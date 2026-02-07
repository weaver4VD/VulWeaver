# RQ2 Ablation: Without Holistic Context

This directory contains the evaluation setup and results for the **without holistic context** ablation in RQ2. In this setting, the model receives only the raw target method code from the CrossVul dataset (`target_code`), with **no** context from UDG, slicing, or other VulWeaver pipeline stages.

To reproduce the ablation, follow the steps below.

---

## Run the reasoning pipeline

Use the **local** `run_llm_reasoning.py` in this directory (do **not** use `VulWeaver/src/Context-Aware_LLM_Reasoning/run_llm_reasoning.py`). It reads the task list and code snippets from [`crossvul_test.json`](../../RQ1/crossvul_dataset/crossvul_test.json) or [`whole dataset.json`](../../RQ1/crossvul_dataset/crossvul.json) (`target_code` field) and uses the result key format: `{repo}#{file_name}#{method_name}#{cve_id}#{commit_id}#{vulnerable|fixed}`.

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

Set `DEEPSEEK_API_KEY` in the environment. After the run, copy the generated results file (e.g. `outputs_w_o_context/reasoning_results_java_demo.json`) to `results_w_o_context.json` in this directory.


The final metrics of w/o context are in [eval_results_w_o_context.json](./eval_results_w_o_context.json).
