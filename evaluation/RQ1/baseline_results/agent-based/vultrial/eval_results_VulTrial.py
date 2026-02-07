import json
import os
from pathlib import Path
import re

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JSON = os.path.join(_SCRIPT_DIR, "eval_results_VulTrial.json")


def parse_result_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, "r") as f:
            content = f.read()
    
    if "</think>" in content:
        content = content.split("</think>")[-1]

    json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        
        json_str = content.strip()
        
        json_str = json_str.replace('```json\n', '').replace('```json', '').replace('\n```', '').replace('```', '')
    
    try:
        jury_results = json.loads(json_str)

        if isinstance(jury_results, dict):
            if "verdicts" in jury_results:
                jury_results = jury_results["verdicts"]
            else:
                jury_results = [jury_results]
        elif not isinstance(jury_results, list):
            jury_results = []
            
        return jury_results
    except json.JSONDecodeError as e:
        if "mitigate" in content.split("\n")[-1]:
            return [{"decision": "valid", "severity": "high", "recommended_action": "fix immediately"}]
        return []


def check_condition(vul_item, status):
    if not isinstance(vul_item, dict):
        return 0
        
    if status == "only_valid_high":
        if vul_item.get("decision") == "valid" and vul_item.get("severity") == "high":
            return 1
    elif status == "action_and_valid_high":
        if (vul_item.get("recommended_action") == "fix immediately" and
            vul_item.get("decision") == "valid" and
            vul_item.get("severity") == "high"):
            return 1
    return 0


def check_vul_label(jury_folder, idx, status):
    file_path = Path(jury_folder) / f"{idx}.txt"
    if not file_path.exists():
        return 0
    jury_results = parse_result_file(file_path)
    for vul_item in jury_results:
        if check_condition(vul_item, status):
            return 1
    return 0


def load_test_data(jsonl_path):
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        json_list = list(f)
    
    pairs = {}
    for json_str in json_list:
        result = json.loads(json_str)
        commit_id = result["commit_id"]
        
        if commit_id not in pairs:
            pairs[commit_id] = {"target": [], "idx": []}
        
        pairs[commit_id]["target"].append(result["target"])
        pairs[commit_id]["idx"].append(result["idx"])
    
    return pairs


def load_test_data_from_mapping(json_path):
    filename_mapping = json.load(open(json_path, 'r', encoding='utf-8'))
    raw_groups = {}
    for k, v in filename_mapping.items():
        k_idx = int(k)
        parts = v.split("#")
        if len(parts) >= 3:
            target_method = parts[-3]
            file_name = parts[-2]
            commit_id = parts[1].replace("^", "")

            label = parts[-1]
            if label == "vulnerable":
                label = 1
            else:
                label = 0
            base_key = f"{commit_id}#{target_method}#{file_name}"
            if base_key not in raw_groups:
                raw_groups[base_key] = {0: [], 1: []}
            raw_groups[base_key][label].append(k_idx)
    pairs = {}
    for base_key, label_to_idxs in raw_groups.items():
        vuln_idxs = label_to_idxs.get(1, [])
        nonvuln_idxs = label_to_idxs.get(0, [])
        pair_num = min(len(vuln_idxs), len(nonvuln_idxs))
        for i in range(pair_num):
            pair_key = f"{base_key}#pair{i}"
            pairs[pair_key] = {
                "target": [1, 0],
                "idx": [vuln_idxs[i], nonvuln_idxs[i]],
            }

    return pairs


def load_test_data_single(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        json_list = list(f)
    filename_mapping = json.load(open(json_path, 'r', encoding='utf-8'))
    test_data = []
    for k, v in filename_mapping.items():
        k_idx = int(k)
        v_label = v.split("#")[-1]
        if v_label == "vulnerable":
            v_label = 1
        else:
            v_label = 0
        test_data.append({
            "idx": k_idx,
            "target": v_label
        })
    
    return test_data


def calculate_metrics(y_true, y_pred):
    tp = 0  
    fp = 0  
    tn = 0  
    fn = 0  
    
    for true_label, pred_label in zip(y_true, y_pred):
        if true_label == 1 and pred_label == 1:
            tp += 1
        elif true_label == 0 and pred_label == 1:
            fp += 1
        elif true_label == 0 and pred_label == 0:
            tn += 1
        elif true_label == 1 and pred_label == 0:
            fn += 1
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "Precision": precision,
        "Recall": recall,
        "F1": f1_score
    }


def calculate_pair_metrics_from_maps(pairs, idx_to_true, idx_to_pred):
    pair_count = 0  
    pair_stats = {"pc": 0, "pv": 0, "pb": 0, "pr": 0}
    skipped = {
        "bad_len": 0,          
        "not_01_pair": 0,      
        "missing_pred": 0,     
    }
    
    for pair_key, pair_data in pairs.items():
        idx_list = pair_data["idx"]
        target_list = pair_data["target"]
        
        if len(idx_list) != 2 or len(target_list) != 2:
            skipped["bad_len"] += 1
            continue

        
        if set(target_list) != {0, 1}:
            skipped["not_01_pair"] += 1
            continue

        
        vuln_pos = target_list.index(1)
        nonvuln_pos = target_list.index(0)
        vuln_idx = idx_list[vuln_pos]
        nonvuln_idx = idx_list[nonvuln_pos]

        vuln_pred = idx_to_pred.get(vuln_idx)
        nonvuln_pred = idx_to_pred.get(nonvuln_idx)
        if vuln_pred is None or nonvuln_pred is None:
            skipped["missing_pred"] += 1
            continue

        pair_count += 1

        if vuln_pred == 1 and nonvuln_pred == 0:
            pair_stats["pc"] += 1
        elif vuln_pred == 0 and nonvuln_pred == 1:
            pair_stats["pr"] += 1
        elif vuln_pred == 1 and nonvuln_pred == 1:
            pair_stats["pv"] += 1
        elif vuln_pred == 0 and nonvuln_pred == 0:
            pair_stats["pb"] += 1

    p_c = pair_stats["pc"] / pair_count if pair_count > 0 else 0.0
    vp_s = (pair_stats["pc"] - pair_stats["pr"]) / pair_count if pair_count > 0 else 0.0
    return {
        **pair_stats,
        **skipped,
        "pair_count": pair_count,
        "P-C": p_c,
        "VP-S": vp_s,
    }


def evaluate_single(jury_folder, test_data, status):
    y_true = []
    y_pred = []
    code_total = 0
    idx_to_true = {}
    idx_to_pred = {}
    
    for item in test_data:
        idx = item["idx"]
        true_label = item["target"]
        file_path = Path(jury_folder) / f"{idx}.txt"
        if file_path.exists():
            code_total += 1
            pred_label = check_vul_label(jury_folder, idx, status)
            y_true.append(true_label)
            y_pred.append(pred_label)
            idx_to_true[idx] = true_label
            idx_to_pred[idx] = pred_label
    metrics = calculate_metrics(y_true, y_pred)
    
    return metrics, code_total, y_true, y_pred, idx_to_true, idx_to_pred


def main():
    
    jury_folders = [
        "./vultrial_results"
    ]
    json_path = "./vultrial_results/filename_mapping.json"
    
    
    status_types = ["only_valid_high"]
    
    
    evaluation_mode = 'single'
    all_results = []

    for jury_folder in jury_folders:
        print(f"\nProcessing folder: {jury_folder}")
        print("=" * 60)

        for status in status_types:
            print(f"\nEvaluation condition: {status}")
            print(f"Evaluation mode: {evaluation_mode}")
            print("-" * 60)

            test_data = load_test_data_single(json_path)
            metrics, code_total, y_true, y_pred, idx_to_true, idx_to_pred = evaluate_single(jury_folder, test_data, status)

            if code_total == 0:
                print("Warning: No valid result files found")
                continue

            pair_metrics = None
            if json_path and os.path.exists(json_path):
                pairs = load_test_data_from_mapping(json_path)
                pair_metrics = calculate_pair_metrics_from_maps(pairs, idx_to_true, idx_to_pred)

            print("\nClassification metrics:")
            print(f"  Precision: {metrics['Precision']:.4f} ({metrics['Precision']*100:.2f}%)")
            print(f"  Recall:    {metrics['Recall']:.4f} ({metrics['Recall']*100:.2f}%)")
            print(f"  F1 Score:  {metrics['F1']:.4f} ({metrics['F1']*100:.2f}%)")

            if pair_metrics:
                print("\nPair metrics:")
                print(f"  P-C:       {pair_metrics['P-C']:.4f} ({pair_metrics['P-C']*100:.2f}%)")
                print(f"  VP-S:      {pair_metrics['VP-S']:.4f}")
            result_entry = {
                "jury_folder": jury_folder,
                "status": status,
                "evaluation_mode": evaluation_mode,
                "code_total": code_total,
                "metrics": metrics,
                "pair_metrics": pair_metrics,
            }
            all_results.append(result_entry)
    if all_results:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump({"results": all_results}, f, indent=2, ensure_ascii=False)
        print(f"\nResults written to: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()     