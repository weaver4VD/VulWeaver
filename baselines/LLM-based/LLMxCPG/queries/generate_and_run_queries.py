import json
import os
import sys
import threading
import time
import argparse
import logging
from typing import List, Dict
from Components.model import LLMManager
from Components.joern_manager import JoernManager
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

def gen_query_prompt(code: str):
    instruction = """Your task is to design Precise Joern CPGQL Queries for Vulnerability Analysis.

Objective:
Develop targeted CPGQL Joern queries to:
1. Identify taint flows based on your analysis
2. Capture potential vulnerability paths

Constraints:
- Queries must be executable in Joern/CPGQL
- Use Scala language features for query construction
- Last query must use reachableByFlows to identify vulnerable paths

Output Requirements:
- Provide a JSON object with one field:
  "queries": Sequence of CPGQL queries to detect vulnerability

Expected JSON Output Format:
```json
{
  "queries": ["Query1", "Query2", ..., "Final Reachable Flows Query"]
}
```

Example Output:
```json
{
  "queries": [
    "val freeCallsWithIdentifier = cpg.method.name("(.*_)?free").filter(_.parameter.size == 1).callIn.where(_.argument(1).isIdentifier).l",
    "freeCallsWithIdentifier.flatMap(f => {val freedIdentifierCode = f.argument(1).code; val postDom = f.postDominatedBy.toSetImmutable; val assignedPostDom = postDom.isIdentifier.where(_.inAssignment).codeExact(freedIdentifierCode).flatMap(id => id ++ id.postDominatedBy); postDom.removedAll(assignedPostDom).isIdentifier.codeExact(freedIdentifierCode).reachableByFlows(f.argument(1))}).l"
  ]
}
```
""" 
    prompt = f"{instruction}\nInput:\n{code}"
    return prompt

class DatasetProcessor:
    """
    Processes each datapoint, generates the Joern queries for this specific sample, and finally executes the joern queries
    to extract the potentially vulnerable execution paths.
    Each instance runs in its own thread.
    """
    def __init__(self,
                 port: int,
                 dataset_slice: List[Dict],
                 output_file: str,
                 logs_file: str,
                 compose_file: str,
                 llm_model_type: str,
                 llm_endpoint: str,
                 llm_port: int,
                 joern_recreate_interval: int):
        """
        Initialize a dataset processor for a specific port and dataset slice.

        Args:
            port: Joern server port number for this processor.
            dataset_slice: Subset of the dataset to process.
            output_file: Path to the unique output file for this thread's results.
            logs_file: Path to the file to store detailed logs/errors for this thread.
            compose_file: Path to the Docker compose file for Joern.
            llm_model_type: Identifier string for the LLM model type (e.g., "DeepSeek").
            llm_endpoint: URL/path for the LLM service.
            llm_port: Port for the LLM service.
            joern_recreate_interval: Number of samples to process before recreating Joern server.
        """
        self.port = port
        self.dataset_slice = dataset_slice
        self.output_file = output_file
        self.logs_file = logs_file
        self.compose_file = compose_file
        self.joern_recreate_interval = joern_recreate_interval
        self.llm_model_type = llm_model_type
        self.llm_endpoint = llm_endpoint
        self.llm_port = llm_port

        self.current_sample_uuid = ""
        self.sample_log_buffer = []
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.logs_file), exist_ok=True)

    def _log_sample_message(self, level: int, message: str, **kwargs):
        """Logs a message and adds it to the sample buffer."""
        log_msg = f"[Port {self.port} | Sample {self.current_sample_uuid}] {message}"
        logging.log(level, log_msg, **kwargs)
        self.sample_log_buffer.append(f"[{logging.getLevelName(level)}] {message}")

    def process_dataset(self):
        """
        Process the assigned slice of the dataset. Handles Joern server recreation.
        """
        import nest_asyncio
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        nest_asyncio.apply(loop)
        self.joern_manager = JoernManager(self.port, self.compose_file)
        self.llm_manager = LLMManager(self.llm_model_type, self.llm_endpoint, port=self.llm_port)

        active_joern_project = None
        try:
            num_samples = len(self.dataset_slice)
            for i, sample in enumerate(self.dataset_slice):
                self.current_sample_uuid = sample.get("uuid", "N/A")
                self.sample_log_buffer = []
                active_joern_project = None
                if i > 0 and i % self.joern_recreate_interval == 0:
                    if active_joern_project:
                         try:
                             self._log_sample_message(logging.DEBUG, f"Cleaning up project '{active_joern_project}' before Joern recreate.")
                             self.joern_manager.delete_project(active_joern_project)
                         except Exception as cleanup_e:
                             self._log_sample_message(logging.WARNING, f"Failed to cleanup Joern project {active_joern_project} before recreate: {cleanup_e}")
                         finally:
                            active_joern_project = None

                    self._log_sample_message(logging.INFO, f"Processed {self.joern_recreate_interval} samples. Recreating Joern server.")

                    is_healthy = self.joern_manager.recreate_server()
                    if not is_healthy:
                        self._log_sample_message(logging.ERROR, "Joern server unhealthy after recreation. Exiting thread.")
                        self._write_error_logs()
                        return
                    self._log_sample_message(logging.INFO, "Joern server recreated successfully.")

                try:
                    self._log_sample_message(logging.INFO, f"Starting processing.")
                    file_name = sample.get("file_name", "").split("/")[-1]
                    if not file_name:
                         raise ValueError("Could not extract a valid file_name from sample['file_name']")
                    result = self._process_single_sample(sample, file_name)
                    if result:
                        active_joern_project = file_name
                        self._write_processed_sample(result)
                        self._log_sample_message(logging.INFO, f"Successfully processed and saved.")
                    else:
                        self._log_sample_message(logging.WARNING, f"Processing failed. Check logs.")
                        self._write_error_logs()
                        active_joern_project = file_name

                except Exception as e:
                    self._log_sample_message(logging.ERROR, f"Unhandled error processing sample: {e}", exc_info=True)
                    self._write_error_logs()
                    if 'file_name' in locals() and file_name:
                         active_joern_project = file_name

                finally:
                    if active_joern_project:
                         try:
                             self._log_sample_message(logging.DEBUG, f"Cleaning up Joern project: {active_joern_project}")
                             self.joern_manager.delete_project(active_joern_project)
                         except Exception as cleanup_e:
                             self._log_sample_message(logging.WARNING, f"Failed to cleanup Joern project {active_joern_project}: {cleanup_e}")
                         finally:
                             active_joern_project = None


        except Exception as e:
            logging.error(f"[Port {self.port}] Critical error in thread execution: {e}", exc_info=True)
            self.sample_log_buffer.append(f"[CRITICAL] Thread execution error: {e}")
            self._write_error_logs()
        finally:
            loop.close()


    def _process_single_sample(self, sample: Dict, file_name: str) -> Dict | None:
        """
        Process a single sample using Joern and LLM.

        Args:
            sample: The sample dictionary to process.
            file_name: The extracted filename for Joern operations.

        Returns:
            The processed sample result as a dictionary, or None if processing failed.
        """
        try:
            required_keys = ["file_name", "code", "label"]
            if not all(key in sample for key in required_keys):
                 missing = [key for key in required_keys if key not in sample]
                 raise ValueError(f"Sample missing required keys: {missing}")
            code_content = sample["code"]
            self._log_sample_message(logging.DEBUG, f"Loading project '{file_name}' into Joern.")
            stdout = self.joern_manager.load_project(file_name)
            if "io.joern.console.ConsoleException" in stdout:
                 self._log_sample_message(logging.ERROR, f"Joern ConsoleException loading project '{file_name}': {stdout}")
                 raise Exception(f"Joern ConsoleException loading project: {stdout}")
            elif "fail" in stdout.lower() or "error" in stdout.lower():
                 self._log_sample_message(logging.WARNING, f"Potential issue loading project '{file_name}' in Joern: {stdout}")
            self._log_sample_message(logging.DEBUG, "Generating CPGQL queries using LLM.")
            prompt = gen_query_prompt(code_content)
            message_history = [{"role": "user", "content": prompt}]

            llm_response = self.llm_manager.send_messages(message_history)
            if not llm_response:
                raise Exception("LLM response was empty or invalid.")

            completion_text = self.llm_manager.get_completion_text(llm_response)
            if not completion_text:
                 raise Exception("Failed to extract completion text from LLM response.")

            llm_answer = self.llm_manager.extract_queries(completion_text)
            if not llm_answer or "queries" not in llm_answer or not isinstance(llm_answer["queries"], list):
                 self._log_sample_message(logging.WARNING, f"Failed to extract valid list of queries from LLM response. Response text: {completion_text}")
                 raise Exception("Failed to extract valid queries list from LLM response.")

            generated_queries = llm_answer["queries"]
            self._log_sample_message(logging.INFO, f"LLM generated {len(generated_queries)} queries.")
            self._log_sample_message(logging.DEBUG, f"Generated Queries: {generated_queries}")
            self._log_sample_message(logging.DEBUG, "Running generated queries in Joern.")
            successful, paths = self.joern_manager.run_queries(generated_queries, code_content)

            self._log_sample_message(logging.INFO, f"Joern query validation: successful={successful}")
            self._log_sample_message(logging.DEBUG, f"Extracted paths: {paths}")
            sample_result = {
                "file_name": sample["file_name"],
                "llm_model_type": self.llm_model_type,
                "llm_queries": generated_queries,
                "label": sample["label"],
                "joern_results": {
                     "all_paths": paths,
                     "successful_query_validation": successful
                },
                "processing_status": "success",
                "details": sample
            }

            return sample_result

        except Exception as e:
            self._log_sample_message(logging.ERROR, f"Error processing sample: {e}", exc_info=True)
            return None

    def _write_processed_sample(self, processed_sample: Dict):
        """Appends a processed sample to the thread-specific JSON output file."""
        try:
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    self._log_sample_message(logging.WARNING, f"Output file {self.output_file} does not contain a JSON list. Overwriting.")
                    existing_data = []
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []
            existing_data.append(processed_sample)
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4)

            logging.info(f"[Port {self.port}] Appended result for sample {self.current_sample_uuid} to {self.output_file}")

        except Exception as e:
             logging.error(f"[Port {self.port} | Sample {self.current_sample_uuid}] Error writing processed sample to {self.output_file}: {e}", exc_info=True)
             self.sample_log_buffer.append(f"[ERROR] Failed to write result to output file: {e}")
             self._write_error_logs()


    def _write_error_logs(self):
        """Appends the buffered logs for the current sample to the thread's log file."""
        if not self.sample_log_buffer:
            return

        try:
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "port": self.port,
                "sample_uuid": self.current_sample_uuid,
                "log_messages": self.sample_log_buffer
            }
            try:
                with open(self.logs_file, 'r', encoding='utf-8') as f:
                    existing_logs = json.load(f)
                if not isinstance(existing_logs, list):
                     logging.warning(f"Log file {self.logs_file} corrupt. Starting new list.")
                     existing_logs = []
            except (FileNotFoundError, json.JSONDecodeError):
                existing_logs = []
            existing_logs.append(log_entry)
            with open(self.logs_file, 'w', encoding='utf-8') as f:
                json.dump(existing_logs, f, indent=4)

            logging.info(f"[Port {self.port}] Appended logs for sample {self.current_sample_uuid} to {self.logs_file}")

        except Exception as e:
            logging.critical(f"[Port {self.port} | Sample {self.current_sample_uuid}] CRITICAL ERROR: Failed to write to error log file {self.logs_file}: {e}", exc_info=True)
        finally:
             self.sample_log_buffer = []


def main():
    """
    Main function to parse arguments, set up, and run dataset processing threads.
    """
    parser = argparse.ArgumentParser(description="Process a dataset of code samples using Joern and an LLM in parallel.")
    parser.add_argument("-d", "--dataset-file", type=str, required=True,
                        help="Path to the input dataset JSON file.")
    parser.add_argument("-o", "--output-base-dir", type=str, required=True,
                        help="Base directory for output files. 'results' and 'logs' subdirectories will be created here.")
    parser.add_argument("-c", "--compose-file", type=str, default="docker-compose.yml",
                        help="Path to the Docker Compose file for Joern servers.")
    parser.add_argument("-n", "--num-workers", type=int, default=1,
                        help="Number of parallel threads/workers (and Joern instances) to use.")
    parser.add_argument("--base-joern-port", type=int, default=16240,
                        help="Starting port number for Joern servers.")
    parser.add_argument("--joern-recreate-interval", type=int, default=5,
                        help="Number of samples to process before recreating a Joern server instance.")
    parser.add_argument("--llm-model-type", type=str, choices=["vLLM", "DeepSeek"], default="vLLM",
                        help="Identifier string for the type of LLM model to use (e.g., 'vLLM', 'DeepSeek'). Passed to LLMManager.")
    parser.add_argument("--llm-endpoint", type=str, required=True,
                        help="Endpoint URL or path for the LLM service (e.g., '/path/to/model' or 'http://host:port').")
    parser.add_argument("--llm-port", type=int, default=9001,
                        help="Port number for the LLM service.")

    args = parser.parse_args()
    if not os.path.isfile(args.dataset_file):
        logging.error(f"Dataset file not found: {args.dataset_file}")
        sys.exit(1)
    if args.num_workers <= 0:
        logging.error("--num-workers must be positive.")
        sys.exit(1)
    results_dir = os.path.join(args.output_base_dir, "results")
    logs_dir = os.path.join(args.output_base_dir, "logs")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    logging.info(f"Outputs will be saved under: {args.output_base_dir}")
    logging.info(f"Number of workers: {args.num_workers}")
    try:
        with open(args.dataset_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        if not isinstance(dataset, list):
             raise TypeError("Dataset file does not contain a valid JSON list.")
        logging.info(f"Loaded dataset with {len(dataset)} samples from {args.dataset_file}")
    except (json.JSONDecodeError, TypeError, FileNotFoundError, OSError) as e:
        logging.error(f"Failed to load or parse dataset file {args.dataset_file}: {e}")
        sys.exit(1)


    if not dataset:
        logging.warning("Dataset is empty. Exiting.")
        sys.exit(0)


    dataset = dataset[:50]
    slice_size = len(dataset)
    remainder = len(dataset) % args.num_workers
    threads = []
    start_idx = 0
    logging.info("Starting worker threads...")
    for i in range(args.num_workers):
        current_slice_size = slice_size + (1 if i < remainder else 0)
        end_idx = start_idx + current_slice_size

        if start_idx >= len(dataset):
            logging.warning(f"Worker {i+1} has no data assigned, reducing effective worker count.")
            continue

        dataset_slice = dataset[start_idx:end_idx]

        output_file = os.path.join(results_dir, f'thread_{i+1}_results.json')
        logs_file = os.path.join(logs_dir, f'thread_{i+1}_logs.json')
        port = args.base_joern_port + i
        processor = DatasetProcessor(
            port=port,
            dataset_slice=dataset_slice,
            output_file=output_file,
            logs_file=logs_file,
            compose_file=args.compose_file,
            llm_model_type=args.llm_model_type,
            llm_endpoint=args.llm_endpoint,
            llm_port=args.llm_port,
            joern_recreate_interval=args.joern_recreate_interval
        )

        thread = threading.Thread(target=processor.process_dataset, name=f"Worker-{i+1}")
        thread.start()
        threads.append(thread)
        logging.info(f"Started Worker-{i+1} (Port {port}) processing {len(dataset_slice)} samples. Output: {output_file}, Logs: {logs_file}")

        start_idx = end_idx
    for thread in threads:
        thread.join()

    logging.info("All worker threads have completed processing.")


if __name__ == "__main__":
    main()
