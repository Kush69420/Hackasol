# Local QLoRA training

Use the RTX A4000 host. Run these commands there from `~/dpdp-ft`; place
`train.py`, `export.sh`, `requirements.txt`, and the JSONL splits from `training/data/`
there first. Check `nvidia-smi` and `ollama ps` before training. Do not stop
Ollama or evict other jobs. Training is single-GPU; the export merge and
quantization run on CPU.

## One-time setup

```bash
mkdir -p ~/dpdp-ft
cd ~/dpdp-ft
python3.10 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m pip check
venv/bin/python -c 'import unsloth, torch; print(torch.__version__, torch.version.cuda); assert torch.cuda.is_available()'
venv/bin/hf download unsloth/Qwen3-8B-bnb-4bit --revision 1deaf68f694c40dbce295da300851729d759b21a --exclude README.md .gitattributes
venv/bin/hf download Qwen/Qwen3-8B --revision b968826d9c46dd6066d109eabc6255188de91218 --exclude README.md .gitattributes
ollama pull qwen3:8b
curl -fL https://codeload.github.com/ggml-org/llama.cpp/tar.gz/refs/tags/b6500 -o llama-b6500.tar.gz
tar -xzf llama-b6500.tar.gz
cmake -S llama.cpp-b6500 -B llama.cpp-b6500/build -G Ninja -DGGML_CUDA=OFF -DLLAMA_CURL=OFF
cmake --build llama.cpp-b6500/build --target llama-quantize -j 8
```

The pinned 4-bit Qwen3-8B checkpoint seeds training. The stock Ollama
`qwen3:8b` tag is the corresponding zero-shot reference; send `"think": false`
alongside `"format": "json"` for that tag. Training uses the native Qwen3 chat
template with `enable_thinking=False`; the assistant header ends with an empty
thinking block, so only the JSON completion and its end marker contribute to
loss. The exported Modelfile renders the same continuation even if the client
omits `think`, and uses `temperature 0`.

## Train and publish

From the host, with `data/train.jsonl` and `data/val.jsonl` already staged:

```bash
cd ~/dpdp-ft
nohup bash -c 'set +e; (
  set -e
  venv/bin/python -u train.py --data data/train.jsonl --val data/val.jsonl --out runs/run-01 --max-seq-len 4096 --epochs 2 --eval-steps 238 --patience 2
  bash export.sh runs/run-01 dpdp-auditor:run-01
); rc=$?; printf "%s\n" "$rc" > run-01.done; exit "$rc"' > run-01.log 2>&1 < /dev/null &
```

Use a fresh output directory and Ollama tag each run. Use a 4,096-token cap
for mixed classification and retrieval-grounded triage if its splits fit.
The collator uses actual input lengths with a microbatch size of 1; short
classification rows do not pay 4,096-token compute or padding cost.
The trainer counts and excludes rows exceeding the cap rather than cutting
the JSON in half.
`run.json` records those counts, the split digests, package versions, optimizer
updates, validation loss, elapsed time, and PyTorch's peak allocated and
reserved memory. PyTorch peaks do not include other GPU processes or driver
allocations. The exporter merges the adapter into the pinned unquantized Qwen3
parent on CPU, converts to BF16 GGUF, and quantizes once to Q5_K_M before
registering the model. It leaves the GGUF and Modelfile in the run's `export/`
directory and removes its temporary intermediate weights.

A dialogue with the exact Auditor contract has three messages: the role's
system prompt, the JSON user payload containing `evidence` and `context`, and
the JSON answer as the assistant content. Keep training and validation splits
separate and never train on the Report Targets.

## Reproduce the smoke run

From the project environment in the worktree, build 64 synthetic rows at each
length (60 training and 4 validation). The repeated text stresses sequence
memory; the labels do not measure classification quality.

```bash
mkdir -p training/data
PYTHONPATH=. python - <<'PY'
import json
from pathlib import Path
from auditor.llm.prompts import system_prompt

for length in (2048, 4096):
    system = {"role": "system", "content": system_prompt("classification")}
    answer = {"role": "assistant", "content": json.dumps({
        "data_category": "Contact", "reason": "The named field stores an email address.",
    })}
    rows = []
    for i in range(64):
        evidence = f"// Dummy row {i}: contactEmail" + " z" * (length - 119)
        user = {"role": "user", "content": json.dumps({"evidence": evidence, "context": {}})}
        rows.append(json.dumps({"messages": [system, user, answer],
                                "role": "classification", "source": "synthetic-smoke"}) + "\n")
    for split, data in (("train", rows[:60]), ("val", rows[60:])):
        Path(f"training/data/smoke-{length}-{split}.jsonl").write_text("".join(data))
PY
```

After copying the four files to `~/dpdp-ft/data/` on the host:

```bash
cd ~/dpdp-ft
for length in 2048 4096; do
  venv/bin/python -u train.py --data "data/smoke-$length-train.jsonl" --val "data/smoke-$length-val.jsonl" \
    --out "runs/smoke-$length" --max-seq-len "$length" --epochs 1 --max-steps 30
done
bash export.sh runs/smoke-2048 dpdp-smoke
curl --fail-with-body -sS http://127.0.0.1:11434/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"model":"dpdp-smoke","format":"json","stream":false,"keep_alive":0,"options":{"num_predict":128},"messages":[{"role":"system","content":"Assess the supplied Evidence for classification. Return only a JSON object in this shape: {\"data_category\": \"Government Identifier|Biometric|Financial|Health|Child Data|Authentication Secret|Contact|Profile\", \"reason\": \"nonempty explanation\"}."},{"role":"user","content":"{\"evidence\":\"const contactEmail = input.email;\", \"context\":{}}"}]}' |
  venv/bin/python -c 'import json, sys; r = json.load(sys.stdin); value = json.loads(r["message"]["content"]); assert r["done_reason"] == "stop" and isinstance(value, dict) and not r["message"].get("thinking"); print(value)'
ollama rm dpdp-smoke
```

### Measured on the A4000

At startup the GPU was at 0% utilization and 282 of 16,376 MiB were in use
(Xorg and GNOME Shell); `ollama ps` listed no loaded model. PyTorch
reported `2.8.0+cu128`, CUDA `12.8`, and CUDA availability `True`.

| Cap | Longest input | Updates | Training s/update | Training peak allocated / reserved MiB | Full run peak allocated / reserved MiB | Full wall time |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2,048 | 2,037 | 30 | 4.91 | 7,683 / 7,710 | 8,806 / 9,090 | 167.5 s |
| 4,096 | 4,085 | 30 | 9.92 | 8,963 / 8,998 | 11,462 / 11,758 | 312.1 s |

One GPU, microbatch 1 and gradient accumulation 2 give
`(1,500 × 2) / 2 = 1,500` optimizer updates. At measured near-cap lengths,
that is about **4 h 8 min** of training with the 4,096 cap or **2 h 3 min**
with the 2,048 cap, plus loading, validation and export. These are
extrapolations from synthetic rows, not real-data measurements. The
mixed-role run should be faster than the 4,096 near-cap estimate because
its classification rows are shorter.

The 2,048-token smoke adapter exported to Q5_K_M and registered as
`dpdp-smoke`. Ollama returned a parseable `Contact` classification with
`format: json` and no thinking trace. The temporary tag was removed.
