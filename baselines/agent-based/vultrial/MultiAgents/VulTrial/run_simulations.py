import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def _process_single_file(args):
    idx, filename, folder_path, total_files, conf = args

    target_file = f"agentverse/tasks/simulation/vultrial/{conf}/config.yaml"
    command = ["python", "agentverse_command/main_simulation_cli.py", "--task", f"simulation/vultrial/{conf}/"]

    file_path = os.path.join(folder_path, filename)
    print(f"[{idx}/{total_files}] Processing file: {file_path}")

    start_time = time.time()

    shutil.copy(file_path, target_file)
    Path("results/final_record/").mkdir(parents=True, exist_ok=True)

    if not os.path.isfile("results/final_record/" + filename.split("/")[-1].split("-")[0] + ".txt"):
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Command failed for file {file_path}. Error: {e}")
            raise
    else:
        print("SKIP")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken: {elapsed_time:.2f} seconds")

    return elapsed_time


def main(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: Folder {folder_path} does not exist.")
        sys.exit(1)

    all_config_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    total_files = len(all_config_files)
    config_files = all_config_files

    print(f"Found {total_files} config file(s) in {folder_path}")
    print(f"Will process all {total_files} file(s)")
    print("-" * 60)

    if not config_files:
        print("No config files found, nothing to do.")
        return

    task_args = []
    for idx, filename in enumerate(config_files, 1):
        result_file = "results/final_record/" + filename.split("/")[-1].split("-")[0] + ".txt"
        if os.path.isfile(result_file):
            print(f"[{idx}/{total_files}] {filename} already has result file, skip.")
            continue
        task_args.append((idx, filename, folder_path, total_files, conf))

    if not task_args:
        print("All files already have results, nothing to run.")
        return

    processing_times = []

    max_workers = min(64, len(task_args))

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(_process_single_file, args): args for args in task_args
            }
            with tqdm(total=len(task_args), desc="Processing configs") as pbar:
                for future in as_completed(future_to_task):
                    try:
                        elapsed_time = future.result()
                        processing_times.append(elapsed_time)
                    except Exception as e:
                        print(f"Thread error: {e}")
                        sys.exit(1)
                    finally:
                        pbar.update(1)
    except Exception as e:
        print(f"Multiprocessing error: {e}")
        sys.exit(1)
    
    if processing_times:
        average_time = sum(processing_times) / len(processing_times)
        total_time = sum(processing_times)
        print("-" * 60)
        print(f"All files processed successfully.")
        print(f"Total processing time: {total_time:.2f} seconds")
        print(f"Average processing time per file: {average_time:.2f} seconds")
    else:
        print("All files processed successfully.")

if __name__ == "__main__":
    conf = "vultrial_deepseek"
    if len(sys.argv) == 2:
        if sys.argv[1] in ["vultrial_base", "vultrial_gpt35", "vultrial_moderator_tuned", "vultrial_deepseek"]:
            conf = str(sys.argv[1])
            folder_path = "agentverse/tasks/simulation/vultrial/"+conf+"/configs"
            main(folder_path)
        else:
            print("Choose the VulTrial setting:")
            print("1. vultrial_base")
            print("2. vultrial_gpt35")
            print("3. vultrial_moderator_tuned")
            print("4. vultrial_deepseek")