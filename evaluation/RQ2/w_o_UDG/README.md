# RQ2 Ablation: Without Enhanced UDG

This directory contains the evaluation setup and results for the **without enhanced UDG** ablation in RQ2. In this variant, the UDG is built with `enhanced=False` so the model does not receive the enhanced UDG context.

To reproduce the ablation, follow the steps below.

---

## 1. Disable enhanced UDG

Set the `enhanced` flag to `False` in both places where the call graph is built.

**`VulWeaver/src/Holistic_Context_Extraction/slice_antman.py`** (line 1151):

```python
callgraph = get_call(target_repo, target_proj, cache_dir, max_workers=multithread_max_workers, enhanced=False)
```

**`VulWeaver/src/VulWeaver.py`** (line 278):

```python
callgraph = get_call(target_repo, target_proj, cache_dir, max_workers=max_workers, enhanced=False)
```

---

## 2. Run the pipeline and obtain evaluation metrics

Following the [RQ1 README](../RQ1/README.md), run the corresponding steps (context extraction and reasoning) to produce the results.

The final metrics of w/o UDG are in [eval_results_w_o_enhanced_UDG.json](./eval_results_w_o_enhanced_UDG.json).
