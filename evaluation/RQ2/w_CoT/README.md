# RQ2 Ablation: With Chain-of-Thought (CoT)

This directory contains the evaluation setup and results for the **with CoT** ablation in RQ2. In this variant, VulWeaver's structured context-aware prompts are replaced with simple chain-of-thought (CoT) prompts that only receive the raw code snippet.

To reproduce the ablation, follow the steps below.

---

## 1. Modify the reasoning prompts

Edit `VulWeaver/evaluation/RQ1/simulation/run_llm_reasoning.py` and replace the Java prompt branch (lines 241--258) with the simplified CoT templates:

```python
        system_prompt = prompt_snippet_templates.SYSTEM_PROMPT_TEMPLATE_W_O_CoT_JAVA
        user_prompt = prompt_snippet_templates.USER_PROMPT_TEMPLATE_W_O_CoT_JAVA.format(
            code_snippet=code_snippet,
        )
```

The CoT templates are defined in `VulWeaver/src/Context-Aware_LLM_Reasoning/prompt/prompt_snippet_templates.py`.

---

## 2. Run the reasoning pipeline

```bash
cd VulWeaver/evaluation/RQ1/simulation/

python run_llm_reasoning.py \
  --lang java \
  --cache-dir /path/to/cache_dir \
  --output-dir ./outputs_w_CoT \
  --run-id demo \
  --rounds 3 \
  --workers 32 \
  --resume
```

Use the same `--cache-dir` as in the main experiment. After the run, copy the generated results file (e.g. `outputs_w_CoT/reasoning_results_java_demo.json`) to `results_w_CoT.json` in this directory.

---

## Summary

| Step | Action |
|------|--------|
| 1 | Replace the Java prompt branch (lines 264--281) in `run_llm_reasoning.py` with `*_W_O_CoT_JAVA` templates. |
| 2 | Run `run_llm_reasoning.py` with the command above, then copy the results to `results_w_CoT.json`. |

The final metrics of w/ CoT are in [eval_results_w_CoT.json](./eval_results_w_CoT.json).
