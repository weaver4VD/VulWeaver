# RQ1 Simulation Pipeline

This directory contains the scripts to reproduce the RQ1 effectiveness evaluation on the CrossVul dataset: clone target projects, run Enhanced UDG construction and holistic context extraction, then run context-aware LLM reasoning.

---

## Prerequisites

Export the required environment variables before running any step:

```bash
# Path to Joern CLI (required for CPG/UDG construction in run_simulation_crossvul)
export JOERN_PATH="/path/to/joern-cli"

# DeepSeek API key (required for LLM-based reasoning in run_llm_reasoning)
export DEEPSEEK_API_KEY="YOUR_DEEPSEEK_API_KEY"
```

---

## Steps

Run the following in order from the **project root** (`VulWeaver/`), or from this directory with paths adjusted.

**1. Clone target projects**

Clone the CrossVul test-set repositories into `target_project/`:

```bash
cd VulWeaver/evaluation/RQ1/simulation
python clone_projects.py
```

**2. Enhanced UDG construction and holistic context extraction**

Run the simulation to build enhanced UDGs and extract context (slicing) for each CrossVul test entry. Output is written under the configured cache directory (e.g. `effectiveness_evaluation_context/`).

```bash
python run_simulation_crossvul.py
```

**3. Context-aware LLM reasoning**

Run the LLM reasoning pipeline on the cached entries. Tasks are read from `../crossvul_dataset/crossvul_test.json`; only entries with an existing cache under `--cache-dir` are processed. Results are written to the specified output directory.

```bash
python run_llm_reasoning.py \
  --cache-dir ./effectiveness_evaluation_context \
  --lang java \
  --output-dir ./outputs \
  --run-id demo \
  --rounds 3 \
  --workers 32 \
  --resume
```

Set `PYTHONPATH` so that the `prompt` module from `src/Context-Aware_LLM_Reasoning` is importable when running from the repo root:

```bash
cd VulWeaver
PYTHONPATH=src/Context-Aware_LLM_Reasoning python evaluation/RQ1/simulation/run_llm_reasoning.py \
  --cache-dir evaluation/RQ1/simulation/effectiveness_evaluation_context \
  --output-dir evaluation/RQ1/simulation/outputs \
  --rounds 3 --workers 32 --resume
```

---

## Summary

| Step | Script | Purpose |
|------|--------|---------|
| 1 | `clone_projects.py` | Clone CrossVul target projects into `target_project/` |
| 2 | `run_simulation_crossvul.py` | Enhanced UDG construction + holistic context extraction (slicing) |
| 3 | `run_llm_reasoning.py` | Context-aware LLM reasoning on cached entries from `crossvul_test.json` |
