# RQ2 Ablation: Without Implicit Data Flow (Getter/Setter)

This directory contains the evaluation setup and results for the **without implicit context** ablation in RQ2. 

To reproduce the ablation, follow the steps below.

---

## Disable implicit context extraction

Edit `VulWeaver/src/Holistic_Context_Extraction/slice_antman.py` and delete lines 616--623:

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

---

The final metrics of w/o implicit are in [eval_results_w_o_implicit.json](./eval_results_w_o_implicit.json).
