# RQ2 Ablation: Without Implicit Data Flow (Getter/Setter)

This directory contains the evaluation setup and results for the implicit data-flow ablation in RQ2. To obtain the reported metrics and reproduce the ablation, follow the steps below.

---

## 1. Obtain ablation evaluation results

From this directory (or with paths adjusted so the script finds `results_w_o_implicit.json` and the test list), run:

```bash
cd VulWeaver/evaluation/RQ2/w_o_implicit
python eval_results_w_o_implicit.py
```

This script loads the reasoning results, applies voting over rounds, and computes precision, recall, F1, etc. The printed metrics are the **ablation results** reported for this setting in RQ2.

---

## 2. Produce results (without implicit variant)

To reproduce the **without implicit** (no getter/setter) ablation variant, disable the getter/setter processing in the context extraction code.

**File:** `VulWeaver/src/Holistic_Context_Extraction/slice.py`

**Change:** Delete lines 638–645 (the block that runs getter/setter processing):

```python
    if setter_method_names or getter_method_names:
        getter_setter_time_start = time.time()
        print(f"Processing getter_setter: setter={len(setter_method_names)}, getter={len(getter_method_names)}")
        getter_setter(setter_method_names, method_signature_dict, points, edges, project, 0, cache_dir, max_workers)
        setter_getter(getter_method_names, method_signature_dict, points, edges, project, 0, cache_dir, max_workers)
        getter_setter_time_end = time.time()
        print(f"Getter_setter processing done")
        gc.collect()
```

Then, following the [RQ1 README](../RQ1/README.md), run the corresponding steps (e.g. simulation / context extraction and reasoning) to produce the results. Save or copy the generated results to `results_w_o_implicit.json` in this directory so that step 1 can be run to obtain the ablation metrics.

---

## Summary

| Step | Action |
|------|--------|
| 1 | Run `python eval_results_w_o_implicit.py` in this directory to get the ablation metrics. |
| 2 | Delete the getter/setter block (lines 638–645) in `slice.py` to reproduce the without-implicit setup. |
| 3 | Follow the [RQ1 README](../RQ1/README.md) and run the corresponding steps to produce `results_w_o_implicit.json`, then re-run step 1 if needed. |


The final results of w/ CoT is in [eval_results_w_o_implicit.json](./eval_results_w_o_implicit.json)

