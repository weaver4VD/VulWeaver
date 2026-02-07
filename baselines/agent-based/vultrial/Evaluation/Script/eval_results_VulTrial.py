import json
from pathlib import Path
import re
import os


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


def load_test_data_single(jsonl_path):
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        json_list = list(f)
    
    test_data = []
    for json_str in json_list:
        result = json.loads(json_str)
        test_data.append({
            "idx": result["idx"],
            "target": result["target"]
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


def evaluate_pairs(jury_folder, pairs, status):
    y_true = []
    y_pred = []
    pair_count = 0
    code_total = 0

    pair_stats = {"pc": 0, "pv": 0, "pb": 0, "pr": 0}
    
    for commit_id, pair_data in pairs.items():
        idx_list = pair_data["idx"]
        target_list = pair_data["target"]
        
        idx_i = 0
        while idx_i + 1 < len(idx_list):
            idx_1 = idx_list[idx_i]
            idx_2 = idx_list[idx_i + 1]
            
            file_1 = Path(jury_folder) / f"{idx_1}.txt"
            file_2 = Path(jury_folder) / f"{idx_2}.txt"
            
            if file_1.exists() and file_2.exists():
                pair_count += 1
                code_total += 2
                
                pair_1_label = target_list[idx_i]
                pair_2_label = target_list[idx_i + 1]
                pair_1_predict = check_vul_label(jury_folder, idx_1, status)
                pair_2_predict = check_vul_label(jury_folder, idx_2, status)

                if pair_1_label == pair_1_predict and pair_2_label == pair_2_predict:
                    pair_stats["pc"] += 1
                elif pair_1_predict == 1 and pair_2_predict == 1:
                    pair_stats["pv"] += 1
                elif pair_1_predict == 0 and pair_2_predict == 0:
                    pair_stats["pb"] += 1
                elif pair_1_predict == 0 and pair_2_predict == 1:
                    pair_stats["pr"] += 1
                
                y_true.extend([pair_1_label, pair_2_label])
                y_pred.extend([pair_1_predict, pair_2_predict])
            
            idx_i += 2
    
    metrics = calculate_metrics(y_true, y_pred)

    p_c = pair_stats["pc"] / pair_count if pair_count > 0 else 0.0
    vp_s = (pair_stats["pv"] - pair_stats["pb"]) / pair_count if pair_count > 0 else 0.0

    pair_metrics = {
        **pair_stats,
        "P-C": p_c,
        "VP-S": vp_s,
    }
    
    return metrics, pair_count, code_total, y_true, y_pred, pair_metrics


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


def calculate_pair_metrics_from_maps(pairs, idx_to_true, idx_to_pred):
    pair_count = 0
    pair_stats = {"pc": 0, "pv": 0, "pb": 0, "pr": 0}
    
    for commit_id, pair_data in pairs.items():
        idx_list = pair_data["idx"]
        target_list = pair_data["target"]
        
        idx_i = 0
        while idx_i + 1 < len(idx_list):
            idx_1 = idx_list[idx_i]
            idx_2 = idx_list[idx_i + 1]
            
            if idx_1 not in idx_to_pred or idx_2 not in idx_to_pred:
                idx_i += 2
                continue
            
            pair_count += 1
            pair_1_label = target_list[idx_i]
            pair_2_label = target_list[idx_i + 1]
            pair_1_predict = idx_to_pred[idx_1]
            pair_2_predict = idx_to_pred[idx_2]
            if pair_1_label == pair_1_predict and pair_2_label == pair_2_predict:
                pair_stats["pc"] += 1
            elif pair_1_predict == 1 and pair_2_predict == 1:
                pair_stats["pv"] += 1
            elif pair_1_predict == 0 and pair_2_predict == 0:
                pair_stats["pb"] += 1
            elif pair_1_predict == 0 and pair_2_predict == 1:
                pair_stats["pr"] += 1
            
            idx_i += 2

    p_c = pair_stats["pc"] / pair_count
    vp_s = (pair_stats["pc"] - pair_stats["pr"]) / pair_count
    return {
        **pair_stats,
        "pair_count": pair_count,
        "P-C": p_c,
        "VP-S": vp_s,
    }

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    jury_folders = [
        os.path.join(_SCRIPT_DIR, "..", "..", "MultiAgents", "VulTrial", "results", "final_record")
    ]
    
    jsonl_path = os.path.join(_SCRIPT_DIR, "primevul_test_paired.jsonl")
    
    status_types = ["only_valid_high"]
    
    evaluation_mode = 'single' 
    
    for jury_folder in jury_folders:
        print(f"\nProcessing folder: {jury_folder}")
        print("=" * 60)
        
        for status in status_types:
            print(f"\nEvaluation condition: {status}")
            print(f"Evaluation mode: {evaluation_mode}")
            print("-" * 60)
            
            if evaluation_mode == 'pair':
                pairs = load_test_data(jsonl_path)
                metrics, pair_count, code_total, y_true, y_pred, pair_metrics = evaluate_pairs(jury_folder, pairs, status)
                
                if code_total == 0:
                    print("Warning: No valid paired results found")
                    continue
                
            else:
                test_data = load_test_data_single(jsonl_path)
                metrics, code_total, y_true, y_pred, idx_to_true, idx_to_pred = evaluate_single(jury_folder, test_data, status)
                
                if code_total == 0:
                    print("Warning: No valid result files found")
                    continue
                

                pairs = load_test_data(jsonl_path)
                pair_metrics = calculate_pair_metrics_from_maps(pairs, idx_to_true, idx_to_pred)

            print("\nClassification metrics:")
            print(f"  Precision: {metrics['Precision']:.4f} ({metrics['Precision']*100:.2f}%)")
            print(f"  Recall:    {metrics['Recall']:.4f} ({metrics['Recall']*100:.2f}%)")
            print(f"  F1 Score:  {metrics['F1']:.4f} ({metrics['F1']*100:.2f}%)")
            print(f"  P-C:       {pair_metrics['P-C']:.4f} ({pair_metrics['P-C']*100:.2f}%)")
            print(f"  VP-S:      {pair_metrics['VP-S']:.4f}")


if __name__ == "__main__":
    main()     