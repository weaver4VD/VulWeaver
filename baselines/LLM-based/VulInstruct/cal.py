import json
import os
import datetime
from collections import defaultdict

def calculate_vulinstruct_metrics(file_path):
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
    filtered_items = []
    tp, fp, tn, fn = 0, 0, 0, 0
    cve_groups = defaultdict(list)
    
    for item in results_list:
        if item.get("data_source") != "exclude_100":
            continue
        cve_id = item.get("cve_id")
        label = item.get("true_label")
        stage1 = item.get("stage1_vulnerability_detection", {})
        prediction = stage1.get("vulnerability_prediction")
        if cve_id is None or label is None or prediction is None:
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
        cve_groups[cve_id].append({
            "label": label,
            "prediction": prediction,
            "code_type": item.get("code_type")
        })
        
        filtered_items.append(item)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    count_pc = 0
    count_pr = 0
    valid_groups = 0

    for cve_id, group_items in cve_groups.items():
        if len(group_items) < 2:
            continue
            
        valid_groups += 1
        is_correct_list = [(x['prediction'] == x['label']) for x in group_items]
        
        if all(is_correct_list):
            count_pc += 1
        elif not any(is_correct_list):
            count_pr += 1
    p_c = count_pc / valid_groups if valid_groups > 0 else 0
    p_r = count_pr / valid_groups if valid_groups > 0 else 0
    fp_s = p_c - p_r
    lines = []
    lines.append(f"========== (VulInstruct Metrics) ==========")
    lines.append(f"time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"file: {file_path}")
    lines.append(f"data_source == 'exclude_100'")
    lines.append("-" * 40)
    lines.append(f"number of data: {len(filtered_items)}")
    lines.append(f"number of cve: {valid_groups}")
    lines.append("-" * 40)
    lines.append(f"[1] (Global Point-wise)")
    lines.append(f"  Precision : {precision:.4f}")
    lines.append(f"  Recall    : {recall:.4f}")
    lines.append(f"  F1 Score  : {f1:.4f}")
    lines.append(f"  Accuracy  : {accuracy:.4f}")
    lines.append(f"  (TP={tp}, FP={fp}, FN={fn}, TN={tn})")
    lines.append("-" * 40)
    lines.append(f"[2] (Group-wise by CVE)")
    lines.append(f"  p-c (Pairwise Correctness): {p_c:.4f}")
    lines.append(f"  p-r (Pairwise Reverse)    : {p_r:.4f}")
    lines.append(f"  fp-s (Consistency Score)  : {fp_s:.4f}")
    lines.append("====================================================")

    report_content = "\n".join(lines)
    print(report_content)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = f"cal_{timestamp}"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "metric_report.txt")
    
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"\nresult saved to: {save_path}")
if __name__ == "__main__":
    json_file_path = "/path/to/json/file" 
    
    calculate_vulinstruct_metrics(json_file_path)