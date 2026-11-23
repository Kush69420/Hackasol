"""Train a Qwen3 QLoRA adapter on the Auditor's JSONL message contract."""

import argparse
import hashlib
import json
import time
from importlib.metadata import version
from pathlib import Path

BASE = "unsloth/Qwen3-8B-bnb-4bit"
BASE_REVISION = "1deaf68f694c40dbce295da300851729d759b21a"
END = "<|im_end|>"
ASSISTANT = "<|im_start|>assistant\n<think>\n\n</think>\n\n"


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--val", type=Path, required=True)
    parser.add_argument("--base", default=BASE)
    parser.add_argument("--revision")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-seq-len", type=int, required=True)
    parser.add_argument("--epochs", type=float, default=2)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--grad-accum", type=int, default=2)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--eval-steps", type=int, default=0, help="Periodic validation and best-adapter selection; 0 validates only at the end")
    parser.add_argument("--patience", type=int, default=2, help="Stop after this many validations without improvement")
    return parser.parse_args()


def encode(path, tokenizer, limit):
    from datasets import Dataset

    records = []
    dropped = 0
    longest = 0
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for number, line in enumerate(stream, start=1):
            digest.update(line)
            try:
                messages = json.loads(line)["messages"]
                if [message["role"] for message in messages] != ["system", "user", "assistant"]:
                    raise ValueError("expected one system, user, and assistant message in order")
                if any(not isinstance(m["content"], str) or not m["content"].strip() for m in messages):
                    raise ValueError("expected nonempty string content")
                if not all(isinstance(json.loads(m["content"]), dict) for m in messages[1:]):
                    raise ValueError("expected JSON objects in user and assistant content")
            except (KeyError, ValueError, TypeError) as error:
                raise ValueError(f"{path}:{number}: {error}") from error

            prefix = tokenizer.apply_chat_template(
                messages[:2], tokenize=False, add_generation_prompt=True, enable_thinking=False
            )
            expected = "".join(f"<|im_start|>{m['role']}\n{m['content']}{END}\n" for m in messages[:2])
            if prefix != expected + ASSISTANT:
                raise ValueError("Qwen3 no-thinking template changed; update training and Ollama together")
            answer = messages[2]["content"] + END
            prefix_ids = tokenizer.encode(prefix, add_special_tokens=False)
            response_ids = tokenizer.encode(answer, add_special_tokens=False)
            length = len(prefix_ids) + len(response_ids)
            longest = max(longest, length)
            if length > limit:
                dropped += 1
                continue
            records.append({
                "input_ids": prefix_ids + response_ids,
                "completion_mask": [0] * len(prefix_ids) + [1] * len(response_ids),
            })
    if not records:
        raise ValueError(f"{path}: no rows fit {limit} tokens (longest: {longest})")
    stats = {
        "sha256": digest.hexdigest(),
        "used": len(records),
        "over_limit": dropped,
        "max_tokens": max(len(row["input_ids"]) for row in records),
        "longest_input_tokens": longest,
    }
    print(f"{path}: {json.dumps(stats)}", flush=True)
    return Dataset.from_list(records), stats


def main():
    args = arguments()
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit(f"Refusing to overwrite nonempty {args.out}")

    # Unsloth must initialize before Transformers, PEFT or TRL.
    from unsloth import FastLanguageModel
    from huggingface_hub import snapshot_download
    import torch
    from transformers import EarlyStoppingCallback
    from trl import SFTConfig, SFTTrainer

    started = time.perf_counter()
    if not torch.cuda.is_available():
        raise SystemExit("QLoRA requires CUDA")
    torch.cuda.reset_peak_memory_stats()
    bf16 = torch.cuda.is_bf16_supported()
    revision = args.revision or (BASE_REVISION if args.base == BASE else None)
    # The Hub cache already contains the pinned checkpoint; Unsloth's remote
    # repository discovery does not work offline even when weights are cached.
    model_path = args.base if Path(args.base).is_dir() else snapshot_download(
        args.base, revision=revision, local_files_only=True
    )
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_path,
        max_seq_length=args.max_seq_len,
        dtype=torch.bfloat16 if bf16 else torch.float16,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.rank,
        lora_alpha=2 * args.rank,
        lora_dropout=0,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )
    train, train_stats = encode(args.data, tokenizer, args.max_seq_len)
    val, val_stats = encode(args.val, tokenizer, args.max_seq_len)
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train,
        eval_dataset=val,
        args=SFTConfig(
            output_dir=str(args.out),
            per_device_train_batch_size=1,
            per_device_eval_batch_size=1,
            gradient_accumulation_steps=args.grad_accum,
            num_train_epochs=args.epochs,
            max_steps=args.max_steps,
            learning_rate=args.lr,
            optim="adamw_8bit",
            bf16=bf16,
            fp16=not bf16,
            completion_only_loss=True,
            dataset_kwargs={"skip_prepare_dataset": True},
            remove_unused_columns=False,
            max_length=args.max_seq_len,
            packing=False,
            eval_strategy="steps" if args.eval_steps else "no",
            eval_steps=args.eval_steps or None,
            save_strategy="steps" if args.eval_steps else "no",
            save_steps=args.eval_steps or 500,
            save_total_limit=1,
            save_only_model=True,
            load_best_model_at_end=bool(args.eval_steps),
            metric_for_best_model="eval_loss" if args.eval_steps else None,
            greater_is_better=False,
            logging_steps=5,
            report_to="none",
            prediction_loss_only=True,
        ),
        callbacks=[EarlyStoppingCallback(early_stopping_patience=args.patience)] if args.eval_steps else [],
    )
    # Confirm the installed TRL collator actually suppresses all prompt loss.
    example = train[0]
    expected_labels = [token if mask else -100 for token, mask in zip(example["input_ids"], example["completion_mask"])]
    if trainer.data_collator([example])["labels"][0].tolist() != expected_labels:
        raise RuntimeError("TRL collator did not preserve the assistant-only loss mask")

    torch.cuda.synchronize()
    train_started = time.perf_counter()
    result = trainer.train()
    torch.cuda.synchronize()
    train_seconds = time.perf_counter() - train_started
    mib = 1024 * 1024
    record = {
        "base": args.base,
        "revision": revision,
        "max_seq_len": args.max_seq_len,
        "epochs": args.epochs,
        "learning_rate": args.lr,
        "rank": args.rank,
        "grad_accum": args.grad_accum,
        "eval_steps": args.eval_steps,
        "early_stopping_patience": args.patience if args.eval_steps else None,
        "best_eval_loss": trainer.state.best_metric,
        "best_step": trainer.state.best_global_step,
        "val_loss_curve": [
            {key: point[key] for key in ("step", "epoch", "eval_loss")}
            for point in trainer.state.log_history if "eval_loss" in point
        ],
        "train": train_stats,
        "val": val_stats,
        "gpu": torch.cuda.get_device_name(),
        "cuda": torch.version.cuda,
        "packages": {name: version(name) for name in ("torch", "unsloth", "trl", "peft", "bitsandbytes", "datasets", "accelerate")},
        "optimizer_steps": result.global_step,
        "train_seconds": train_seconds,
        "seconds_per_step": train_seconds / result.global_step,
        "training_peak_allocated_mib": torch.cuda.max_memory_allocated() / mib,
        "training_peak_reserved_mib": torch.cuda.max_memory_reserved() / mib,
    }
    print(json.dumps(record), flush=True)
    record["validation"] = trainer.evaluate()
    record["run_peak_allocated_mib"] = torch.cuda.max_memory_allocated() / mib
    record["run_peak_reserved_mib"] = torch.cuda.max_memory_reserved() / mib
    model.save_pretrained(args.out)
    tokenizer.save_pretrained(args.out)
    record["wall_seconds"] = time.perf_counter() - started
    (args.out / "run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
