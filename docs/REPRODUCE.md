# Reproduction Guide

## Requirements

- Python 3.10 or later
- LaTeX distribution (for paper compilation): `sudo apt install texlive-full latexmk`
- ~2 GB disk for all data including LightRAG workdir caches

## Quick setup

```bash
git clone https://github.com/jmanoharan/cgmes-graphrag-bench.git
cd cgmes-graphrag-bench
make setup
```

## Environment variables

The G_LLM build step (`make build-g-llm`) requires an LLM API endpoint.
The codebase uses LightRAG 1.5.x with the `llm_func` abstraction;
you can plug in any OpenAI-compatible provider:

```bash
export AZURE_OPENAI_API_KEY=...
export AZURE_OPENAI_ENDPOINT=...   # e.g. https://<resource>.openai.azure.com/
export AZURE_OPENAI_API_VERSION=2024-02-15-preview
export AZURE_OPENAI_DEPLOYMENT=gpt-4o   # or the deployment name for your builder model
```

The published G_LLM was built with Azure OpenAI `gpt-5.1`. Any capable model
(Qwen2.5-72B, GPT-4o, Llama-3.3-70B, etc.) can be substituted via `build_g_llm.py`'s
`llm_func`; results will differ from the paper's G_LLM.

### Skip G_LLM rebuild (recommended for reviewers)

Pre-built graph artefacts and LightRAG KV caches are included in
`data/networks/*/lightrag_workdir/`.
Scoring and evaluation (`make eval-h1 eval-h2 stats`) do **not** require API keys
and will reproduce the paper's numbers from cached data.

## Step-by-step reproduction

### 1. Build G_STD (parse CGMES → standards-native graph)

```bash
make build-g-std
# Wall time: <1 s per network
```

### 2. (Optional) Rebuild G_LLM

```bash
# Requires LLM API keys (see above)
make build-g-llm
# Wall time: ~9 min MicroGrid, ~11 min SmallGrid
# Token cost: ~88k tokens MicroGrid, ~595k tokens SmallGrid
```

### 3. Run H1/H2/H3 evaluation

```bash
make eval-h1 eval-h2 stats
# Wall time: <2 min total per network on CPU
```

### Or run everything

```bash
make all
```

## Version note

The v1 run (2026-06-10) contained several protocol violations documented in
`paper/supplementary/DEVIATIONS.md`. The v2 artefacts in `data/networks/` are the
canonical, protocol-conforming run. v1 artefacts are not released; do not cite v1 numbers.

## Verification checklist

After `make all`:

1. `python -c "import json; d=json.load(open('results/h2_microgrid.json')); print([x for x in d if x['kg']=='std'][0]['det_acc_all'])"` → `0.82`
2. `python -c "import json; d=json.load(open('results/h1_microgrid.json')); print(d['h1_error_rate'])"` → `0.0135`
3. `python -c "import json; d=json.load(open('results/h3_costs.json')); print(d['microgrid']['g_llm']['total_tokens'])"` → `87962`
