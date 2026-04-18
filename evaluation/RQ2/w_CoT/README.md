# RQ2 Ablation: With Chain-of-Thought (CoT)

This directory contains the evaluation setup and results for the CoT ablation in RQ2. To obtain the reported metrics and reproduce the ablation, follow the steps below.

---

## 1. Obtain ablation evaluation results

From this directory (or with paths adjusted so the script finds `results_w_CoT.json` and the test list), run:

```bash
cd VulWeaver/evaluation/RQ2/w_CoT
python eval_results_w_CoT.py
```

This script loads the reasoning results, applies voting over rounds, and computes precision, recall, F1, etc. The printed metrics are the **ablation results** reported for this setting in RQ2.

---

## 2. Produce reasoning results (with CoT variant)

To get the **without CoT** ablation variant, modify the prompt in the LLM reasoning script so that it uses the no–chain-of-thought templates.

**File:** `VulWeaver/evaluation/RQ1/simulation/run_llm_reasoning.py`

**Change:** Replace the Java branch (lines 266-283) with:

```python
        system_prompt = prompt_snippet_templates.SYSTEM_PROMPT_TEMPLATE_W_O_CoT_JAVA
        user_prompt = prompt_snippet_templates.USER_PROMPT_TEMPLATE_W_O_CoT_JAVA.format(
            code_snippet=code_snippet,
        )
```

Then run the reasoning pipeline:

```bash
cd VulWeaver/evaluation/RQ1/simulation/

python run_llm_reasoning.py \
  --lang java \
  --cache-dir /path/to/cache_dir \
  --output-dir ./outputs_w_o_CoT \
  --run-id demo \
  --rounds 3 \
  --workers 32 \
  --resume
```

Use the same `--cache-dir` and dataset as in the main experiment. Copy or link the generated results (e.g. `reasoning_vulnerabilities_java_demo.json`) into this directory or point the evaluation script to that output.

---

## Summary

| Step | Action |
|------|--------|
| 1 | Edit `run_llm_reasoning.py` to use `*_W_O_CoT_JAVA` prompts (lines 241–258). |
| 2 | Run `run_llm_reasoning.py` with the command above to produce reasoning outputs. |
| 3 | Run `python eval_results_w_CoT.py` in this directory to get the ablation metrics. |

The final results of w/ CoT is in [eval_results_w_CoT.json](./eval_results_w_CoT.json)
