# RQ4 Simulation Pipeline (PrimeVul)

This directory contains the scripts to reproduce the RQ4 evaluation on the **PrimeVul** dataset (C/C++): clone target projects, run Enhanced UDG construction and holistic context extraction, then run context-aware LLM reasoning.

---

## Prerequisites

Export the required environment variables before running any step:

```bash
# Path to Joern CLI (required for CPG/UDG construction in run_simulation_primevul)
export JOERN_PATH="/path/to/joern-cli"

# DeepSeek API key (required for LLM-based reasoning in run_llm_reasoning)
export DEEPSEEK_API_KEY="YOUR_DEEPSEEK_API_KEY"
```

---

## Steps

Run the following in order from the **project root** (`VulWeaver/`), or from this directory with paths adjusted.

**1. Clone target projects**

Clone the PrimeVul test-set repositories. The script reads `../primevul_dataset/primevul_test_formatted.json`, clones repos into `target_project/.cache`, and prepares per-commit directories under `target_project/`.

```bash
cd VulWeaver/evaluation/RQ4/simulation
python clone_projects.py
```

**2. Enhanced UDG construction and holistic context extraction**

Run the simulation to build enhanced UDGs and extract context (slicing) for each PrimeVul test entry (C language). Output is written under the configured cache directory (e.g. `effectiveness_evaluation_context/`).

```bash
python run_simulation_primevul.py
```

**3. Context-aware LLM reasoning**

Run the LLM reasoning pipeline on the cached entries. Tasks are read from `../primevul_dataset/primevul_test_formatted.json`; only entries with an existing cache under `--cache-dir` are processed. Use `--lang c` for PrimeVul (C/C++). Results are written to the specified output directory.

```bash
python run_llm_reasoning.py \
  --cache-dir ./effectiveness_evaluation_context \
  --lang c \
  --output-dir ./outputs \
  --run-id demo \
  --rounds 3 \
  --workers 32 \
  --resume
```

Set `PYTHONPATH` so that the `prompt` module from `src/Context-Aware_LLM_Reasoning` is importable when running from the repo root:

```bash
cd VulWeaver
PYTHONPATH=src/Context-Aware_LLM_Reasoning python evaluation/RQ4/simulation/run_llm_reasoning.py \
  --cache-dir evaluation/RQ4/simulation/effectiveness_evaluation_context \
  --lang c \
  --output-dir evaluation/RQ4/simulation/outputs \
  --rounds 3 --workers 32 --resume
```

---

## Summary

| Step | Script | Purpose |
|------|--------|---------|
| 1 | `clone_projects.py` | Clone PrimeVul target projects (from `primevul_test_formatted.json`) into `target_project/` |
| 2 | `run_simulation_primevul.py` | Enhanced UDG construction + holistic context extraction (slicing) for C code |
| 3 | `run_llm_reasoning.py` | Context-aware LLM reasoning on cached entries from `primevul_test_formatted.json` |
