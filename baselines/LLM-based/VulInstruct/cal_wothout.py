import json
import os
import datetime
from collections import defaultdict

def calculate_vulinstruct_metrics_filtered_nodedup(file_path):
    
    if not os.path.exists(file_path):
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return
    results_list = data.get("detailed_results", [])
    if not results_list:
        return
    tp, fp, tn, fn = 0, 0, 0, 0
    processed_count = 0
    cve_groups = defaultdict(lambda: {"before": [], "after": []})
    
    for item in results_list:
        if item.get("data_source") != "exclude_100": 
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
        if label == 1 and prediction == 1:
            tp += 1
        elif label == 0 and prediction == 1:
            fp += 1
        elif label == 1 and prediction == 0:
            fn += 1
        elif label == 0 and prediction == 0:
            tn += 1
            
        processed_count += 1
        sample_data = {
            "cve_id": cve_id,
            "code_type": code_type,
            "label": label,
            "prediction": prediction
        }
        cve_groups[cve_id][code_type].append(sample_data)

    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    
    count_pc = 0
    count_pr = 0
    valid_groups = 0
    
    for cve_id, group in cve_groups.items():
        before_list = group["before"]
        after_list = group["after"]
        if not before_list or not after_list:
            continue
        
        valid_groups += 1
        
        all_before_correct = all(x["prediction"] == x["label"] for x in before_list)
        all_after_correct = all(x["prediction"] == x["label"] for x in after_list)
        if all_before_correct and all_after_correct:
            count_pc += 1
        else:
            all_before_wrong = all(x["prediction"] != x["label"] for x in before_list)
            all_after_wrong = all(x["prediction"] != x["label"] for x in after_list)
            
            if all_before_wrong and all_after_wrong:
                count_pr += 1
    p_c = count_pc / valid_groups if valid_groups > 0 else 0
    p_r = count_pr / valid_groups if valid_groups > 0 else 0
    fp_s = p_c - p_r
    lines = []
    lines.append(f"========== (Filtered 'exclude_100') ==========")
    lines.append(f"time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"files: {file_path}")
    lines.append(f" data_source == 'exclude_100'")
    lines.append("-" * 50)
    lines.append(f"[1] (Point-wise)")
    lines.append(f"  Accuracy  : {accuracy:.4f}")
    lines.append(f"  Precision : {precision:.4f}")
    lines.append(f"  Recall    : {recall:.4f}")
    lines.append(f"  F1 Score  : {f1:.4f}")
    lines.append(f" TP={tp}, FP={fp}, FN={fn}, TN={tn}")
    lines.append(f"  (TP+FP+FN+TN): {tp+fp+fn+tn}")
    lines.append("-" * 50)
    lines.append(f"[2] (Pairwise)")
    lines.append(f"  p-c (Correct) : {p_c:.4f} ({count_pc}/{valid_groups})")
    lines.append(f"  p-r (Reverse) : {p_r:.4f} ({count_pr}/{valid_groups})")
    lines.append(f"  fp-s (Score)  : {fp_s:.4f}")
    lines.append("=" * 50)

    report_content = "\n".join(lines)
    print(report_content)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = f"cal_filtered_nodedup_{timestamp}"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "metric_report_filtered.txt")
    
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"\nresult saved to: {save_path}")
if __name__ == "__main__":
    json_file_path = "/path/to/json/file"
    calculate_vulinstruct_metrics_filtered_nodedup(json_file_path)