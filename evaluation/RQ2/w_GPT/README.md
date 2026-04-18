# RQ2 Ablation: With Qwen

This directory contains the evaluation setup and results for the Qwen ablation in RQ2.

---

## 1. Obtain ablation evaluation results

From this directory (or with paths adjusted so the script finds `results_w_qwen.json` and the test list), run:

```bash
cd VulWeaver/evaluation/RQ2/w_Qwen
python eval_results_w_qwen.py
```

This script loads the reasoning results, applies voting over rounds, and computes precision, recall, F1, etc. The printed metrics are the **ablation results** reported for this setting in RQ2.

The final results of w/ CoT is in [eval_results_w_qwen.json](./eval_results_w_qwen.json)

