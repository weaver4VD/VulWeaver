import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def clone_and_process_results(primevul_path=os.path.join(_SCRIPT_DIR, "..", "primevul_dataset", "primevul_test_formatted.json"), target_project_dir=os.path.join(_SCRIPT_DIR, "target_project")):
    target_project_dir = os.path.abspath(target_project_dir)
    cache_dir = os.path.join(target_project_dir, ".cache")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    with open(primevul_path, 'r') as f:
        primevul_data = json.load(f)
    project_groups = {}
    for res in primevul_data:
        url = res.get("project_url")
        if url:
            if url not in project_groups:
                project_groups[url] = []
            project_groups[url].append(res)

    def _clone_repo(project_url, cache_repo_path):
        if os.path.exists(cache_repo_path):
            return True
        print(f"Cloning {project_url} to cache...")
        try:
            subprocess.run(
                ["git", "clone", project_url, cache_repo_path],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone {project_url}: {e}")
            return False

    missing_repos = []
    for project_url, entries in project_groups.items():
        project_name = project_url.split("/")[-1].replace(".git", "")
        cache_repo_path = os.path.join(cache_dir, project_name)
        if not os.path.exists(cache_repo_path):
            missing_repos.append((project_url, cache_repo_path))

    failed_repos = set()
    if missing_repos:
        max_workers = min(32, len(missing_repos))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_repo = {
                executor.submit(_clone_repo, project_url, cache_repo_path): project_url
                for project_url, cache_repo_path in missing_repos
            }
            for future in as_completed(future_to_repo):
                project_url = future_to_repo[future]
                if not future.result():
                    failed_repos.add(project_url)

    for project_url, entries in project_groups.items():
        project_name = project_url.split("/")[-1].replace(".git", "")
        cache_repo_path = os.path.join(cache_dir, project_name)

        if project_url in failed_repos or not os.path.exists(cache_repo_path):
            print(f"Skip {project_url} because cache clone failed.")
            continue

        for entry in entries:
            commit_id = entry.get("commit_id").split("#diff")[0]
            target_file_name = entry.get("target_file_name")
            method_name = entry.get("method_name")

            if not commit_id or not target_file_name:
                continue

            unique_project_name = f"{project_name}_{commit_id}"
            local_repo_path = os.path.join(target_project_dir, unique_project_name)

            if not os.path.exists(local_repo_path):
                print(f"Creating unique instance: {unique_project_name}")
                try:
                    subprocess.run(["git", "clone", cache_repo_path, local_repo_path], check=True, capture_output=True)
                except subprocess.CalledProcessError as e:
                    print(f"Failed to create instance {unique_project_name}: {e}")
                    continue
            
            try:
                subprocess.run(["git", "reset", "--hard"], cwd=local_repo_path, capture_output=True)
                subprocess.run(["git", "checkout", commit_id], cwd=local_repo_path, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                subprocess.run(["rm", "-rf", local_repo_path])
                print(f"Failed to checkout {commit_id} in {unique_project_name}: {e.stderr.decode()}")
                continue

def update_method_name_paths(primevul_path=os.path.join(_SCRIPT_DIR, "..", "primevul_dataset", "primevul_test_formatted.json"), target_project_dir=os.path.join(_SCRIPT_DIR, "target_project")):
    target_project_dir = os.path.abspath(target_project_dir)
    processed_list = []
    
    with open(primevul_path, 'r') as f:
        primevul_data = json.load(f)
    for entry in primevul_data:
        project_url = entry.get("project_url")
        commit_id = entry.get("commit_id")
        target_file_name = entry.get("target_file_name")
        method_name = entry.get("method_name")
        if "#" in method_name:
            continue

        if not all([project_url, commit_id, target_file_name, method_name]):
            processed_list.append(entry)
            continue

        project_name = project_url.split("/")[-1].replace(".git", "")
        unique_project_name = f"{project_name}_{commit_id}"
        local_repo_path = os.path.join(target_project_dir, unique_project_name)

        if not os.path.exists(local_repo_path):
            print(f"Warning: Repository path does not exist: {local_repo_path}")
            processed_list.append(entry)
            continue

        try:
            find_res = subprocess.run(
                ["git", "ls-files", f"*{target_file_name}"], 
                cwd=local_repo_path, 
                check=True, 
                capture_output=True, 
                text=True
            )
            raw_files = [f.strip() for f in find_res.stdout.strip().split('\n') if f.strip()]
            files = [f for f in raw_files if os.path.basename(f) == target_file_name]
            if not files:
                files = raw_files

            if files:
                found_path = None
                for fpath in files:
                    full_fpath = os.path.join(local_repo_path, fpath)
                    try:
                        if os.path.exists(full_fpath):
                            with open(full_fpath, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if method_name in content:
                                    found_path = fpath
                                    break
                    except Exception:
                        continue
                
                final_path = found_path if found_path else files[0]
                entry["method_name"] = f"{final_path}#{method_name}"
                
                if found_path:
                    print(f"[{unique_project_name}] Updated (Content Match): {entry['method_name']}")
                else:
                    print(f"[{unique_project_name}] Updated (Fallback to First): {entry['method_name']}")
            else:
                print(f"[{unique_project_name}] Could not find file {target_file_name}")
                
        except subprocess.CalledProcessError:
            print(f"[{unique_project_name}] Error running git ls-files for {target_file_name}")
        
        processed_list.append(entry)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_list, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    primevul_path = os.path.join(_SCRIPT_DIR, "..", "primevul_dataset", "primevul_test_formatted.json")
    target_project_dir = os.path.join(_SCRIPT_DIR, "target_project")
    clone_and_process_results(primevul_path, target_project_dir)
    update_method_name_paths(primevul_path, target_project_dir)