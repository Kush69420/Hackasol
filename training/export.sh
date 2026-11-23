#!/usr/bin/env bash
# Merge the Qwen3-8B adapter into its unquantized parent, then publish Q5_K_M.
set -euo pipefail

if (( $# != 2 )); then
    echo 'Usage: bash export.sh <adapter-dir> <ollama-model>' >&2
    exit 2
fi

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
adapter=$(cd -- "$1" && pwd)
name=$2
python="$root/venv/bin/python"
llama="$root/llama.cpp-b6500"
exported="$adapter/export"

if ollama show "$name" >/dev/null 2>&1; then
    echo "Refusing to overwrite existing Ollama model: $name" >&2
    exit 1
fi
mkdir -p -- "$exported"
work=$(mktemp -d "$exported/merge.XXXXXXXX")
trap 'rm -rf -- "$work"' EXIT

# The 125 GB host can merge in CPU RAM, with no contention for the training GPU.
OMP_NUM_THREADS=8 "$python" - "$adapter" "$work/merged" <<'PY'
import json
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

adapter, destination = sys.argv[1:]
run = json.loads((Path(adapter) / "run.json").read_text())
if run["base"] != "unsloth/Qwen3-8B-bnb-4bit" or run["revision"] != "1deaf68f694c40dbce295da300851729d759b21a":
    raise ValueError("export expects the pinned Qwen3-8B QLoRA base")
base = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen3-8B",
    revision="b968826d9c46dd6066d109eabc6255188de91218",
    dtype=torch.bfloat16,
    device_map="cpu",
)
model = PeftModel.from_pretrained(base, adapter).merge_and_unload(safe_merge=True)
model.save_pretrained(destination)
AutoTokenizer.from_pretrained(adapter).save_pretrained(destination)
PY

# Use llama.cpp's matching gguf-py rather than a possibly incompatible PyPI release.
PYTHONPATH="$llama/gguf-py" OMP_NUM_THREADS=8 "$python" "$llama/convert_hf_to_gguf.py" \
    "$work/merged" --outfile "$work/merged-bf16.gguf" --outtype bf16
"$llama/build/bin/llama-quantize" "$work/merged-bf16.gguf" "$work/model-q5_k_m.gguf" Q5_K_M 8
mv -- "$work/model-q5_k_m.gguf" "$exported/model-q5_k_m.gguf"

cd -- "$exported"
# Same two input turns and empty thinking block as train.py's generation prefix.
cat > Modelfile <<'MODELFILE'
FROM ./model-q5_k_m.gguf
TEMPLATE """{{ range .Messages }}<|im_start|>{{ .Role }}
{{ .Content }}<|im_end|>
{{ end }}<|im_start|>assistant
<think>

</think>

"""
PARAMETER temperature 0
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
MODELFILE
ollama create "$name" -f Modelfile
