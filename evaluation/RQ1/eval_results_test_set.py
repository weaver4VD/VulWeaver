import os
import sys
import json
from typing import Dict, List

# Resolve paths relative to this script's directory so the script can be run from anywhere
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    RESULTS_FILE = os.path.join(_SCRIPT_DIR, "simulation", "outputs", "reasoning_results_primevul4j_test.json")
    # REFLECTION_FILE = os.path.join(_SCRIPT_DIR, "simulation", "outputs", "reasoning_reflection_primevul4j_test.json")
    WORK_LIST_FILE = os.path.join(_SCRIPT_DIR, "primevul4j_dataset", "primevul4j_test.json")
    OUTPUT_JSON = os.path.join(_SCRIPT_DIR, "eval_results_primevul4j_test.json")

def _normalize_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in {"true", "yes", "y", "1"}:
            return True
        if s in {"false", "no", "n", "0"}:
            return False
    return False

def vote_result(round_results: List[Dict]) -> Dict:
    if not round_results:
        return {}

    vul = sum(1 for item in round_results if item.get('is_vulnerable'))
    not_vul = len(round_results) - vul
    if vul > not_vul:
        is_vulnerable = True
    elif not_vul > vul:
        is_vulnerable = False
    else:
        is_vulnerable = False

    base_result = next(
        (r for r in round_results if r.get('is_vulnerable', None) == is_vulnerable),
        round_results[0]
    )
    
    final_result = base_result.copy()
    final_result['is_vulnerable'] = is_vulnerable
    final_result['vote_stats'] = {
        'total_rounds': len(round_results),
        'is_vulnerable': is_vulnerable,
        'vul_votes': vul,
        'not_vul_votes': not_vul,
    }
    
    return final_result

def parse_cache_dir_name(cache_dir_name: str) -> Dict[str, str]:
    if cache_dir_name.startswith("cache_"):
        cache_dir_name = cache_dir_name[6:]
    parts = cache_dir_name.split('#')
    return {
        'project_name': parts[0],
        "file_name": parts[1],
        'target_method': parts[2],
        'idx': parts[3],
        'cve_id': parts[4],
        'commit_id': parts[5],
        'label': parts[6]
    }

def parse_result():
    with open(Config.RESULTS_FILE, "r") as f:
        results = json.load(f)
    f.close()
    
    voted_results = {}
    for key, value in results.items():
        if isinstance(value, list):
            voted_result = vote_result(value)

            if voted_result:
                voted_results[key] = voted_result
            else:
                continue
        elif isinstance(value, dict):
            voted_results[key] = value
        else:
            continue
    
    results = voted_results
    
    reflection_results = {}
    if hasattr(Config, 'REFLECTION_FILE') and os.path.exists(Config.REFLECTION_FILE):
        try:
            with open(Config.REFLECTION_FILE, "r") as f:
                reflection_results = json.load(f)
        except Exception:
            pass
            
    for key, ref_val in reflection_results.items():
        if key in results and isinstance(ref_val, dict):
            if 'is_vulnerable' in ref_val:
                results[key]['is_vulnerable'] = _normalize_bool(ref_val['is_vulnerable'])
    
    tp = 0
    fp = 0
    fn = 0
    tn = 0
    
    work_list_file = Config.WORK_LIST_FILE
    need_run = set()
    true_label_mapping = {}
    if os.path.exists(work_list_file):
        try:
            with open(work_list_file, "r", encoding="utf-8") as f:
                work_list_data = json.load(f)
            for row in work_list_data:
                commit_id = str(row.get('commit_id', ''))
                project_name = row.get("project_url", "").split("/")[-1].replace(".git", "")
                target_method = row.get('target_method', '').strip().split("#")[-1] if row.get('target_method') else ''
                
                file_name = row.get("target_file_name", "")
                idx = str(row.get("idx", ""))
                cve_id = row.get('CVE_id', '')
                if row.get("is_vulnerable") == True:
                    label = "vulnerable"
                else:
                    label = "fixed"
                
                dir_name = f"cache_{file_name}#{target_method}#{cve_id}#{commit_id}"
                true_label_mapping[dir_name] = label
        except Exception as e:
            pass
    pair_items = {}
    with open(work_list_file, "r") as f:
        work_list = json.load(f)
    for key, value in results.items():
        dir_name = os.path.basename(key)
        if dir_name.startswith("cache_"):
            dir_name = dir_name[6:]
        parsed_info = parse_cache_dir_name(dir_name)
        idx = parsed_info.get('idx', '')
        cwe_id = ""
        for item in work_list:
            if item.get('idx') == idx:
                file_name = item.get('target_file_name', '')
                cwe_id = item.get('CWE_id', '')
                break
        
        full_dir_name = f'cache_{file_name}#{parsed_info["target_method"]}#{parsed_info["cve_id"]}#{parsed_info["commit_id"]}'
        true_label = true_label_mapping.get(full_dir_name, parsed_info.get('label', ''))
        
        commit_id = parsed_info.get('commit_id', '')
        
        predicted_vulnerable = value.get('is_vulnerable', False)
        if true_label == "vulnerable":
            if predicted_vulnerable:
                tp += 1
            else:
                fn += 1
                need_run.add(key)
        else:
            if predicted_vulnerable:
                fp += 1
                need_run.add(key)
            else:
                tn += 1
        dir_name = os.path.basename(key)
        if dir_name.startswith("cache_"):
            dir_name = dir_name[6:]
        parsed_info = parse_cache_dir_name(dir_name)
        project_name = parsed_info.get('project_name', '')
        target_method = parsed_info.get('target_method', '')
        cve_id = parsed_info.get('cve_id', '')
        idx = parsed_info.get('idx', '')
        commit_hash = parsed_info.get('commit_id', '')
        label = true_label
        
        
        if file_name and target_method and cve_id and commit_hash:
            commit_id = commit_hash[:-1] if commit_hash.endswith("^") else commit_hash
            pair_id = f"{project_name}#{file_name}#{target_method}#{cve_id}#{commit_id}#{cwe_id}"
            if pair_id not in pair_items:
                pair_items[pair_id] = {}
            pair_items[pair_id][label] = 1 if predicted_vulnerable else 0
    
    total_results = tp + fp + fn + tn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = (2 * tp) / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0.0
    
    print(f"Total results: {total_results}")
    print(f"tp: {tp}, fp: {fp}, fn: {fn}, tn: {tn}")
    print(f"precision: {precision}")
    print(f"recall: {recall}")
    print(f"f1-score: {f1_score}")
    
    pair_stats = {"pc": 0, "pv": 0, "pb": 0, "pr": 0}
    pair_count = 0
    for pair_id, item in pair_items.items():
        if "vulnerable" not in item or "fixed" not in item:
            continue
        pair_count += 1
        pair_1_predict = item["vulnerable"]
        pair_2_predict = item["fixed"]
        if pair_1_predict == 1 and pair_2_predict == 0:
            pair_stats["pc"] += 1
        elif pair_1_predict == 1 and pair_2_predict == 1:
            pair_stats["pv"] += 1
        elif pair_1_predict == 0 and pair_2_predict == 0:
            pair_stats["pb"] += 1
        elif pair_1_predict == 0 and pair_2_predict == 1:
            pair_stats["pr"] += 1
    
    p_c = pair_stats["pc"] / pair_count if pair_count > 0 else 0.0
    p_r = pair_stats["pr"] / pair_count if pair_count > 0 else 0.0
    vp_score = p_c - p_r

    print(f"pair_count: {pair_count}")
    print(f"pc: {pair_stats['pc']}, pv: {pair_stats['pv']}, pb: {pair_stats['pb']}, pr: {pair_stats['pr']}")
    print(f"P-C: {p_c}")
    print(f"P-R: {p_r}")
    print(f"VP-Score: {vp_score}")

    # Output final results to JSON file
    output = {
        "total_results": total_results,
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
        },
        "pair_metrics": {
            "P_C": p_c,
            "P_R": p_r,
            "VP_Score": vp_score,
        },
    }
    with open("need_run.json", "w", encoding="utf-8") as f:
        json.dump(list(need_run), f, indent=2, ensure_ascii=False)

    with open(Config.OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to: {Config.OUTPUT_JSON}")

if __name__ == "__main__":
    parse_result()
