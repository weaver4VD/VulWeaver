import json
import os
import datetime
from collections import defaultdict

def calculate_vulinstruct_metrics(file_path):
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return
    results_list = data.get("detailed_results", [])
    if not results_list:
        return
    unique_samples = {}
    

    for item in results_list:
        if item.get("data_source") != "exclude_100":
            continue

        sample_id = item.get("sample_id")
        if not sample_id:
            continue
        if sample_id in unique_samples:
            continue
        cve_id = item.get("cve_id")
        code_type = item.get("code_type")
        label = item.get("true_label")
        stage1 = item.get("stage1_vulnerability_detection", {})
        prediction = stage1.get("vulnerability_prediction")
        if cve_id is None or label is None or prediction is None or code_type is None:
            continue
        label = int(label)
        prediction = int(prediction)
        
        unique_samples[sample_id] = {
            "cve_id": cve_id,
            "code_type": code_type,
            "label": label,
            "prediction": prediction,
            "sample_id": sample_id
        }

    tp, fp, tn, fn = 0, 0, 0, 0
    cve_pairs = defaultdict(dict)
    
    for sample in unique_samples.values():
        cve_id = sample["cve_id"]
        code_type = sample["code_type"]
        label = sample["label"]
        prediction = sample["prediction"]
        
        if label == 1 and prediction == 1:
            tp += 1
        elif label == 0 and prediction == 1:
            fp += 1
        elif label == 1 and prediction == 0:
            fn += 1
        elif label == 0 and prediction == 0:
            tn += 1
        cve_pairs[cve_id][code_type] = sample
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    
    count_pc = 0
    count_pr = 0
    valid_pairs = 0
    incomplete_pairs = 0
    
    for cve_id, pair in cve_pairs.items():
        if "before" not in pair or "after" not in pair:
            incomplete_pairs += 1
            continue
        
        valid_pairs += 1
        
        before = pair["before"]
        after = pair["after"]
        before_correct = (before["prediction"] == before["label"])
        after_correct = (after["prediction"] == after["label"])
        if before_correct and after_correct:
            count_pc += 1
        elif not before_correct and not after_correct:
            count_pr += 1
    p_c = count_pc / valid_pairs if valid_pairs > 0 else 0
    p_r = count_pr / valid_pairs if valid_pairs > 0 else 0
    fp_s = p_c - p_r
    lines = []
    lines.append(f"========== (VulInstruct Metrics) ==========")
    lines.append(f"time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"file: {file_path}")
    lines.append(f"data_source == 'exclude_100'")
    lines.append("-" * 50)
    lines.append(f"[1] (Point-wise)")
    lines.append(f"  Accuracy  : {accuracy:.4f}")
    lines.append(f"  Precision : {precision:.4f}")
    lines.append(f"  Recall    : {recall:.4f}")
    lines.append(f"  F1 Score  : {f1:.4f}")
    lines.append(f"  TP={tp}, FP={fp}, FN={fn}, TN={tn}")
    lines.append("-" * 50)
    lines.append(f"[2] (Pairwise)")
    lines.append(f"  p-c (Pairwise Correctness)  : {p_c:.4f}  ({count_pc}/{valid_pairs} all right)")
    lines.append(f"  p-r (Pairwise Reverse)      : {p_r:.4f}  ({count_pr}/{valid_pairs} all wrong)")
    lines.append(f"  fp-s (Consistency Score)    : {fp_s:.4f}  (p-c - p-r)")
    lines.append("-" * 50)
    lines.append(f"[3] (Detailed Analysis)")
    if valid_pairs > 0:
        partial_correct = valid_pairs - count_pc - count_pr
        lines.append(f"  in all pairs:")
        lines.append(f"    - all right: {count_pc} ({count_pc/valid_pairs*100:.1f}%)")
        lines.append(f"    - only one right: {partial_correct} ({partial_correct/valid_pairs*100:.1f}%)")
        lines.append(f"    - all wrong: {count_pr} ({count_pr/valid_pairs*100:.1f}%)")
    
    lines.append("=" * 50)

    report_content = "\n".join(lines)
    print(report_content)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = f"cal_{timestamp}"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "metric_report.txt")
    
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"\nresult saved to: {save_path}")
    debug_info = {
        "total_cves": len(cve_pairs),
        "valid_pairs": valid_pairs,
        "incomplete_pairs": incomplete_pairs,
        "unique_samples_count": len(unique_samples),
        "sample_ids_first_10": list(unique_samples.keys())[:10]
    }
    
    debug_path = os.path.join(save_dir, "debug_info.json")
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(debug_info, f, indent=2, ensure_ascii=False)
    print(f"debug info saved to: {debug_path}")
if __name__ == "__main__":
    json_file_path = "/path/to/json/file"
    calculate_vulinstruct_metrics(json_file_path)