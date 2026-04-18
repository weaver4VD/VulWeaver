# RQ2 Ablation: Without Enhanced UDG

This directory contains the evaluation setup and results for the enhanced-UDG ablation in RQ2. To obtain the reported metrics and reproduce the ablation, follow the steps below.

---

## 1. Obtain ablation evaluation results

From this directory (or with paths adjusted so the script finds `results_w_o_enhanced_UDG.json` and the test list), run:

```bash
cd VulWeaver/evaluation/RQ2/w_o_UDG
python eval_results_w_o_enhanced_UDG.py
```

This script loads the reasoning results, applies voting over rounds, and computes precision, recall, F1, etc. The printed metrics are the **ablation results** reported for this setting in RQ2.

---

## 2. Produce results (without enhanced UDG variant)

To reproduce the **without enhanced UDG** ablation variant, set the `enhanced` flag to `False` in both places where the call graph is built.

**File 1:** `VulWeaver/src/Holistic_Context_Extraction/slice.py`  
**Line:** 1151  

Set the call to use `enhanced=False`:

```python
callgraph = get_call(target_repo, target_proj, cache_dir, max_workers=multithread_max_workers, enhanced=False)
```

**File 2:** `VulWeaver/src/VulWeaver.py`  
**Line:** 278  

Set the call to use `enhanced=False`:

```python
callgraph = get_call(target_repo, target_proj, cache_dir, max_workers=max_workers, enhanced=False)
```

Then, following the [RQ1 README](../RQ1/README.md), run the corresponding steps (e.g. simulation / context extraction and reasoning) to produce the results. Save or copy the generated results to `results_w_o_enhanced_UDG.json` in this directory so that step 1 can be run to obtain the ablation metrics.

---

## Summary

| Step | Action |
|------|--------|
| 1 | Run `python eval_results_w_o_enhanced_UDG.py` in this directory to get the ablation metrics. |
| 2 | Set `enhanced=False` in `slice.py` (line 1151) and in `VulWeaver.py` (line 278) to reproduce the without–enhanced-UDG setup. |
| 3 | Follow the [RQ1 README](../RQ1/README.md) and run the corresponding steps to produce `results_w_o_enhanced_UDG.json`, then re-run step 1 if needed. |

The final results of w/ CoT is in [eval_results_w_o_enhanced_UDG.json](./eval_results_w_o_enhanced_UDG.json)
