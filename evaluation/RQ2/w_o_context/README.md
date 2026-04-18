# RQ2 Ablation: Without Holistic Context

This directory contains the evaluation setup and results for the **without holistic context** ablation in RQ2. In this setting, the model receives only the raw target method code from the PrimeVul4J dataset (`target_code`), with **no** context from UDG, slicing, or other VulWeaver pipeline stages.

To obtain the reported metrics and reproduce the ablation, follow the steps below.

---

## 1. Obtain ablation evaluation results

From this directory (or with paths adjusted so the script finds `results_w_o_context.json` and the test list), run:

```bash
cd VulWeaver/evaluation/RQ2/w_o_context
python eval_results_w_o_context.py
```

This script loads the reasoning results, applies voting over rounds, and computes precision, recall, F1, etc. The printed metrics are the **ablation results** reported for this setting in RQ2.

---

## 2. Produce results (without-context variant)

This ablation uses the **local** `run_llm_reasoning.py` in this directory, which:

- Reads the task list and **code snippets** directly from [RQ1 `primevul4j_test.json`](../../RQ1/primevul4j_dataset/primevul4j_test.json) (`target_code` field).
- Uses the result key format: `{repo}#{file_name}#{method_name}#{cve_id}#{commit_id}#{vulnerable|fixed}`.

Do **not** use `VulWeaver/src/Context-Aware_LLM_Reasoning/run_llm_reasoning.py`; use this directory’s script so that code comes from PrimeVul4J and keys match the evaluator.

**Run reasoning (from repo root or this directory):**

```bash
cd VulWeaver/evaluation/RQ2/w_o_context

python run_llm_reasoning.py \
  --lang java \
  --sensitive-api-map ../../../src/Context-Aware_LLM_Reasoning/sensitive_api/sensitive_api.json \
  --output-dir ./outputs_w_o_context \
  --run-id demo \
  --rounds 3 \
  --workers 32 \
  --resume
```

Set `DEEPSEEK_API_KEY` in the environment. After the run, copy or link the generated results file (e.g. `outputs_w_o_context/reasoning_results_java_demo.json`) to `results_w_o_context.json` in this directory, then run step 1 to obtain the ablation metrics.

## Summary

| Step | Action |
|------|--------|
| 1 | Run `python eval_results_w_o_context.py` in this directory to get the ablation metrics. |
| 2 | Use **this directory’s** `run_llm_reasoning.py` (not `src/Context-Aware_LLM_Reasoning/`) so code comes from PrimeVul4J `target_code` and keys match. |
| 3 | Run `run_llm_reasoning.py` with the command above, then copy the results to `results_w_o_context.json` and re-run step 1 if needed. |


The final results of w/ CoT is in [eval_results_w_o_context.json](./eval_results_w_o_context.json)

