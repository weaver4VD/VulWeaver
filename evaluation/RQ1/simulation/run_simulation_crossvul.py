import re
import sys
import os

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
print(_PROJECT_ROOT)
import Constructing_Enhanced_UDG.joern as joern
from Holistic_Context_Extraction.slice_antman import target_slicing
from Constructing_Enhanced_UDG.common import Language
import json
from tqdm import tqdm
import cpu_heater
from datetime import datetime
import random
import gc

JOERN_PATH = os.getenv("JOERN_PATH")
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    joern.set_joern_env(JOERN_PATH)
    with open(os.path.join(_SCRIPT_DIR, "..", "crossvul_dataset", "crossvul_test.json"), "r") as f:
        crossvul_data = json.load(f)
    work_list = []
    
    cache_dir = os.path.join(_SCRIPT_DIR, "effectiveness_evaluation_context")
    worker_ids = set()
    for row in tqdm(crossvul_data, total=len(crossvul_data), desc="Processing CrossVul"):
        commit_id = str(row['commit_id'])
        project_name = row["project_url"].split("/")[-1].replace(".git", "")
        repo_path = os.path.join(_SCRIPT_DIR, "target_project", f"{project_name}_{commit_id}")
        if row["is_vulnerable"] == True:
            label = "vulnerable"
        else:
            label = "fixed"
        target_method = row['target_method']
        if target_method.strip().endswith("#") or "#" not in target_method:
            continue
        file_path = target_method.strip().split("#")[0]
        file_name = file_path.split("/")[-1]
        method_name = target_method.strip().split("#")[-1]

        idx = str(row["idx"])
        line_map = {}
        callee_names = row["target_api_name"]
        for callee_name in callee_names:
            callee_name = callee_name.split(".")[-1]
            line_map[callee_name] = set()
        change_line_map = True

        worker_ids.add(os.path.join(cache_dir, f"cache_{project_name}#{file_name}#{method_name}#{idx}#{row['CVE_id']}#{commit_id}#{label}"))
        work_list.append((os.path.join(cache_dir, f"cache_{project_name}#{file_name}#{method_name}#{idx}#{row['CVE_id']}#{commit_id}#{label}"), method_name, repo_path, os.path.join(cache_dir, f"cache_{project_name}#{file_name}#{method_name}#{idx}#{row['CVE_id']}#{commit_id}#{label}"), [f"{file_path}#{method_name}"], line_map, Language.JAVA, change_line_map))

    results = []
    finished_ids = set()
    current_work_list = work_list
    max_retries = 3

    BATCH_SIZE = 200

    for i in range(max_retries):
        if not current_work_list:
            break
        print(f"Epoch {i + 1}/{max_retries}: Processing {len(current_work_list)} tasks")
        
        batch_finished_ids = set()
        
        for batch_start in range(0, len(current_work_list), BATCH_SIZE):
            batch_items = current_work_list[batch_start:batch_start + BATCH_SIZE]
            print(f"  Processing batch {batch_start
            
            batch_results = cpu_heater.multiprocess(target_slicing, batch_items, max_workers=1, show_progress=True, timeout=18000)
            
            for res in batch_results:
                worker_id = res[1]
                if worker_id not in finished_ids:
                    results.append(res)
                    finished_ids.add(worker_id)
                batch_finished_ids.add(worker_id)
            
            gc.collect()
            print(f"  Batch completed, gc.collect() done")
            
        next_work_list = []
        for item in current_work_list:
            if item[0] not in batch_finished_ids:
                next_work_list.append(item)
        
        current_work_list = next_work_list
        
        if current_work_list:
            print(f"Retrying {len(current_work_list)} failed/timeout tasks...")
            random.shuffle(current_work_list)
