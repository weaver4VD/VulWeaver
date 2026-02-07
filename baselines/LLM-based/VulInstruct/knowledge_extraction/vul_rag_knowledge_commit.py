import json
import logging
import threading
import time
from enum import Enum
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import queue
from query_llm import query_api


class LLMResponseSeparator(Enum):
    DOC_SEP = "####"
    ANSWER_SEP = "###"
    FUN_PURPOSE_SEP = "Function purpose: "
    FUN_FUNCTION_SEP = "The functions of the code snippet are:"


class KnowledgeDocumentName(Enum):
    PRECONDITIONS = "preconditions_for_vulnerability"
    TRIGGER = "trigger_condition"
    CODE_BEHAVIOR = "specific_code_behavior_causing_vulnerability"
    SOLUTION = "solution"
    PURPOSE = "GPT_purpose"
    FUNCTION = "GPT_function"
    CODE_BEFORE = "code_before_change"
    CODE_AFTER = "code_after_change"
    VUL_BEHAVIOR = "vulnerability_behavior"
    CVE_ID = "CVE_id"

    @classmethod
    def get_es_document_values(cls) -> list:
        return [item.value for item in cls][:-2]


class DataUtils:
    @staticmethod
    def save_json(path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def load_json(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data


def extract_LLM_response_by_prefix(response: str, prefix: str) -> str:
    """
    This function extracts the response from the LLM output that is prefixed by a given string.
    """
    if prefix in response:
        return response.split(prefix)[1].strip()
    else:
        return response.strip()


class APIManager:
    """
    Class for managing multiple API keys, supporting concurrent calls and load balancing
    """
    
    def __init__(self, api_keys: List[str], api_base: str, model: str = "gpt-3.5-turbo"):
        self.api_keys = api_keys
        self.api_base = api_base
        self.model = model
        self.api_queue = queue.Queue()
        self.lock = threading.Lock()
        for api_key in api_keys:
            self.api_queue.put(api_key)
    
    def get_api_key(self):
        """Get an available API key"""
        return self.api_queue.get()
    
    def return_api_key(self, api_key: str):
        """Return API key"""
        self.api_queue.put(api_key)
    
    def query_with_retry(self, prompt: str, system_prompt: str = None, max_retries: int = 3) -> str:
        """
        Query with API, supports retry and error handling
        """
        api_key = self.get_api_key()
        
        for attempt in range(max_retries):
            try:
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n{prompt}"
                else:
                    full_prompt = prompt
                
                result = query_api(
                    api_base=self.api_base,
                    model=self.model,
                    api_key=api_key,
                    prompt=full_prompt,
                    enable_reasoning=False
                )
                if result and not result.startswith("API Error") and not result.startswith("Request Error"):
                    self.return_api_key(api_key)
                    return result
                else:
                    logging.warning(f"API call failed on attempt {attempt + 1}: {result}")
                    time.sleep(1)
                    
            except Exception as e:
                logging.error(f"Exception on attempt {attempt + 1}: {str(e)}")
                time.sleep(1)
        
        self.return_api_key(api_key)
        raise Exception(f"All {max_retries} attempts failed for API call")


class ConcurrentLLMQueryInterface:
    """
    Concurrent LLM query interface, using APIManager for API management
    """
    
    def __init__(self, api_manager: APIManager):
        self.api_manager = api_manager
        self.default_system_prompt = "You are a helpful assistant specialized in vulnerability analysis and code security."
    
    def query_llm(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """
        Query LLM
        """
        if system_prompt is None:
            system_prompt = self.default_system_prompt
            
        return self.api_manager.query_with_retry(prompt, system_prompt)


class ExtractionPrompt:
    
    @staticmethod
    def generate_extract_prompt(CVE_id, CVE_description, code_before_change, code_after_change=None, commit_hash=None):
        """
        Generate extraction prompt, adapted to new data format, including commit information
        """
        commit_info = f" (commit: {commit_hash[:8]}...)" if commit_hash else ""
        
        prefix_str = f"""This is a code snippet with a vulnerability {CVE_id}{commit_info}:

'''
{code_before_change}
'''

The vulnerability is described as follows:
{CVE_description}

"""
        purpose_prompt = f"""{prefix_str}
What is the purpose of the function in the above code snippet? \
Please summarize the answer in one sentence with following format: Function purpose: \"\"

"""
        function_prompt = f"""{prefix_str}
Please summarize the functions of the above code snippet in the list format without other \
explanation: \"The functions of the code snippet are: 1. 2. 3.\"

"""
        if code_after_change:
            analysis_prompt = f"""{prefix_str}
The code after modification is as follows:
'''
{code_after_change}
'''

Why is the above modification necessary to fix the vulnerability?"""
        else:
            analysis_prompt = f"""{prefix_str}
Based on the vulnerability description, what would be the necessary modifications to fix this vulnerability?"""

        knowledge_extraction_prompt = """

I want you to act as a vulnerability detection expert and organize vulnerability knowledge based on the above \
vulnerability information. Please summarize the generalizable specific behavior of the code that \
leads to the vulnerability and the specific solution to fix it. Format your findings in JSON.

Here are some examples to guide you on the level of detail expected in your extraction:

Example 1:

{
    "vulnerability_behavior": {
        'preconditions_for_vulnerability': 'Lack of proper handling for asynchronous events during device removal process.',
        'trigger_condition': 'A physically proximate attacker unplugs a device while the removal function is executing, \
leading to a race condition and use-after-free vulnerability.',
        'specific_code_behavior_causing_vulnerability': 'The code does not cancel pending work associated with a specific \
functionality before proceeding with further cleanup during device removal. This can result in a use-after-free scenario if \
the device is unplugged at a critical moment.'
    },
    'solution': 'To mitigate the vulnerability, it is necessary to cancel any pending work related to the specific \
functionality before proceeding with further cleanup during device removal. This ensures that the code handles asynchronous \
events properly and prevents the use-after-free vulnerability. In this case, the solution involves adding a line to cancel the \
pending work associated with the specific functionality before continuing with the cleanup process.'
}

Please be mindful to omit specific resource names in your descriptions to ensure the knowledge remains generalized. \
For example, instead of writing mutex_lock(&dmxdev->mutex), simply use mutex_lock.

"""

        return purpose_prompt, function_prompt, analysis_prompt, knowledge_extraction_prompt


class CommitAwareKnowledgeExtractor:
    
    def __init__(self, api_manager: APIManager):
        """
        Initialize commit-aware knowledge extractor
        
        Args:
            api_manager: API manager instance
        """
        self.api_manager = api_manager
        self.llm_query_interface = ConcurrentLLMQueryInterface(api_manager)
        self.data_lst = []

    def get_unique_key(self, item: Dict[str, Any]) -> str:
        """
        Generate unique key: CVE_ID + commit_hash
        """
        cve_id = item["cve_id"]
        commit_hash = item.get("commit_hash", "")
        return f"{cve_id}_{commit_hash}"

    def get_dict(self, vul_knowledge_output):
        """
        Parse LLM output vulnerability knowledge into dictionary
        """
        try:
            if "\"vulnerability_behavior\"" in vul_knowledge_output:
                vul_knowledge_output = vul_knowledge_output.split("\"vulnerability_behavior\"")[1]
                vul_knowledge_output = "{\"vulnerability_behavior\"" + vul_knowledge_output
            if "\n```" in vul_knowledge_output:
                vul_knowledge_output = vul_knowledge_output.split("\n```")[0]
            return json.loads(vul_knowledge_output)
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error: {e}")
            logging.error(f"Original output: {vul_knowledge_output}")
            return {
                "vulnerability_behavior": {
                    "preconditions_for_vulnerability": "Failed to parse",
                    "trigger_condition": "Failed to parse",
                    "specific_code_behavior_causing_vulnerability": "Failed to parse"
                },
                "solution": "Failed to parse"
            }

    def process_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process single data item
        """
        cve_id = item.get("cve_id", "unknown")
        commit_hash = item.get("commit_hash", "")
        
        try:
            cve_description = item.get("cve_desc", "")
            if not cve_description:
                logging.warning(f"CVE {cve_id} (commit: {commit_hash[:8]}): Missing cve_desc field")
                return None
            code_before_change = ""
            code_after_change = ""
            
            if "vulnerableMethods_before" in item and item["vulnerableMethods_before"]:
                code_before_change = item["vulnerableMethods_before"][0].get("raw_code", "")
            
            if "vulnerableMethods_after" in item and item["vulnerableMethods_after"]:
                code_after_change = item["vulnerableMethods_after"][0].get("raw_code", "")
            if not code_before_change:
                logging.warning(f"CVE {cve_id} (commit: {commit_hash[:8]}): Missing vulnerableMethods_before code")
                return None
            (
                purpose_prompt,
                function_prompt,
                analysis_prompt,
                knowledge_extraction_prompt
            ) = ExtractionPrompt.generate_extract_prompt(
                cve_id,
                cve_description,
                code_before_change,
                code_after_change if code_after_change else None,
                commit_hash
            )
            purpose_output = self.llm_query_interface.query_llm(purpose_prompt)
            if not purpose_output or purpose_output.startswith(("API Error", "Request Error")):
                logging.error(f"CVE {cve_id} (commit: {commit_hash[:8]}): Purpose query failed")
                return None
            function_output = self.llm_query_interface.query_llm(function_prompt)
            if not function_output or function_output.startswith(("API Error", "Request Error")):
                logging.error(f"CVE {cve_id} (commit: {commit_hash[:8]}): Function query failed")
                return None
            analysis_output = self.llm_query_interface.query_llm(analysis_prompt)
            if not analysis_output or analysis_output.startswith(("API Error", "Request Error")):
                logging.error(f"CVE {cve_id} (commit: {commit_hash[:8]}): Analysis query failed")
                return None
            combined_prompt = f"{analysis_prompt}\n\nAssistant: {analysis_output}\n\nHuman: {knowledge_extraction_prompt}"
            vul_knowledge_output = self.llm_query_interface.query_llm(combined_prompt)
            if not vul_knowledge_output or vul_knowledge_output.startswith(("API Error", "Request Error")):
                logging.error(f"CVE {cve_id} (commit: {commit_hash[:8]}): Knowledge extraction query failed")
                return None
            output_dict = self.get_dict(vul_knowledge_output)
            if not output_dict or "vulnerability_behavior" not in output_dict:
                logging.error(f"CVE {cve_id} (commit: {commit_hash[:8]}): Failed to parse vulnerability_behavior")
                return None
            
            output_dict["GPT_analysis"] = analysis_output
            output_dict["GPT_purpose"] = extract_LLM_response_by_prefix(
                purpose_output,
                LLMResponseSeparator.FUN_PURPOSE_SEP.value
            )
            output_dict["GPT_function"] = extract_LLM_response_by_prefix(
                function_output,
                LLMResponseSeparator.FUN_FUNCTION_SEP.value
            )
            output_dict["CVE_id"] = cve_id
            output_dict["commit_hash"] = commit_hash
            output_dict["repository"] = item.get("repository", "")
            output_dict["code_before_change"] = code_before_change
            output_dict["code_after_change"] = code_after_change
            
            logging.debug(f"Successfully processed CVE {cve_id} (commit: {commit_hash[:8]})")
            return output_dict

        except Exception as e:
            logging.error(f"Exception occurred while processing {cve_id} (commit: {commit_hash[:8]}): {e}", exc_info=True)
            return None

    def format_knowledge_file(self, path):
        """
        Format knowledge file - now maintaining commit-level grouping
        """
        try:
            kno_dict = DataUtils.load_json(path)
            answer = {}
            
            for unique_key in kno_dict:
                answer[unique_key] = []
                for item in kno_dict[unique_key]:
                    if KnowledgeDocumentName.VUL_BEHAVIOR.value in item:
                        vul_behavior = item[KnowledgeDocumentName.VUL_BEHAVIOR.value]
                        item[KnowledgeDocumentName.PRECONDITIONS.value] = vul_behavior.get(KnowledgeDocumentName.PRECONDITIONS.value, "")
                        item[KnowledgeDocumentName.TRIGGER.value] = vul_behavior.get(KnowledgeDocumentName.TRIGGER.value, "")
                        item[KnowledgeDocumentName.CODE_BEHAVIOR.value] = vul_behavior.get(KnowledgeDocumentName.CODE_BEHAVIOR.value, "")
                        
                        if KnowledgeDocumentName.SOLUTION.value in vul_behavior:
                            item[KnowledgeDocumentName.SOLUTION.value] = vul_behavior[KnowledgeDocumentName.SOLUTION.value]
                    
                    answer[unique_key].append(item)

            DataUtils.save_json(path, answer)
        except Exception as e:
            logging.error(f"Error formatting knowledge file: {e}")

    def extract_knowledge_concurrent(self, data_list: List[Dict], output_path: str, 
                                   max_workers: int = 10, resume: bool = False):
        """
        Extract knowledge concurrently - using commit-aware processing
        
        Args:
            data_list: Data list
            output_path: Output path
            max_workers: Maximum number of worker threads
            resume: Whether to resume from previous progress
        """
        self.data_lst = data_list
        if resume and self._check_file_exists(output_path):
            try:
                output_dict = DataUtils.load_json(output_path)
                logging.info(f"Resume mode: Loaded {len(output_dict)} processed items")
            except:
                output_dict = {}
        else:
            output_dict = {}
        items_to_process = []
        for item in self.data_lst:
            unique_key = self.get_unique_key(item)
            if unique_key not in output_dict:
                items_to_process.append(item)

        logging.info(f"Total {len(items_to_process)} items to process")
        processed_count = len(output_dict)
        failed_count = 0
        failed_items = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {
                executor.submit(self.process_single_item, item): item 
                for item in items_to_process
            }
            for future in tqdm(as_completed(future_to_item), total=len(items_to_process), desc="Processing progress"):
                item = future_to_item[future]
                unique_key = self.get_unique_key(item)
                
                try:
                    result = future.result()
                    if result:
                        if unique_key not in output_dict:
                            output_dict[unique_key] = []
                        output_dict[unique_key].append(result)
                        processed_count += 1
                        if processed_count % 50 == 0:
                            DataUtils.save_json(output_path, output_dict)
                            self.format_knowledge_file(output_path)
                            logging.info(f"Progress saved, successfully processed {processed_count} items, {failed_count} failed")
                    else:
                        failed_count += 1
                        failed_items.append(unique_key)
                        logging.warning(f"Processing {unique_key} failed, returned empty result")
                            
                except Exception as e:
                    failed_count += 1
                    failed_items.append(unique_key)
                    logging.error(f"Error processing {unique_key}: {e}")
        DataUtils.save_json(output_path, output_dict)
        self.format_knowledge_file(output_path)
        total_input = len(data_list)
        successful_processed = len(output_dict)
        
        logging.info(f"=" * 60)
        logging.info(f"Processing completion statistics report:")
        logging.info(f"Total input: {total_input}")
        logging.info(f"Successfully processed: {successful_processed}")
        logging.info(f"Failed count: {failed_count}")
        logging.info(f"Success rate: {successful_processed/total_input*100:.1f}%")
        
        if failed_items:
            logging.info(f"List of failed items: {failed_items[:10]}...")
            failed_log_path = output_path.replace('.json', '_failed.json')
            DataUtils.save_json(failed_log_path, {
                "failed_unique_keys": failed_items,
                "failed_count": failed_count,
                "total_input": total_input,
                "success_rate": successful_processed/total_input*100
            })
            logging.info(f"Failed list saved to: {failed_log_path}")
        
        logging.info(f"=" * 60)

    def _check_file_exists(self, path):
        """Check if file exists"""
        import os
        return os.path.exists(path)


def migrate_old_results(old_path: str, new_path: str, original_data_path: str):
    """
    Migrate old results to new commit-aware format
    
    Args:
        old_path: Old results file path
        new_path: New results file path
        original_data_path: Original data path (for getting commit information)
    """
    logging.info("Starting migration of old results to commit-aware format...")
    old_results = DataUtils.load_json(old_path)
    original_data = DataUtils.load_json(original_data_path)
    cve_to_commits = {}
    for item in original_data:
        cve_id = item["cve_id"]
        commit_hash = item.get("commit_hash", "")
        if cve_id not in cve_to_commits:
            cve_to_commits[cve_id] = []
        cve_to_commits[cve_id].append({
            "commit_hash": commit_hash,
            "repository": item.get("repository", ""),
            "item": item
        })
    new_results = {}
    
    for cve_id, cve_results in old_results.items():
        commits = cve_to_commits.get(cve_id, [])
        
        if len(commits) == 1:
            commit_hash = commits[0]["commit_hash"]
            unique_key = f"{cve_id}_{commit_hash}"
            for result in cve_results:
                result["commit_hash"] = commit_hash
                result["repository"] = commits[0]["repository"]
            
            new_results[unique_key] = cve_results
            
        else:
            first_commit = commits[0]
            commit_hash = first_commit["commit_hash"]
            unique_key = f"{cve_id}_{commit_hash}"
            for result in cve_results:
                result["commit_hash"] = commit_hash
                result["repository"] = first_commit["repository"]
            
            new_results[unique_key] = cve_results
            logging.info(f"CVE {cve_id} has {len(commits)} commits, migrated first one ({commit_hash[:8]}), others need reprocessing")
    DataUtils.save_json(new_path, new_results)
    total_original_items = len(original_data)
    migrated_items = len(new_results)
    remaining_items = total_original_items - migrated_items
    
    logging.info(f"Migration complete:")
    logging.info(f"Original data: {total_original_items} CVE-commit combinations")
    logging.info(f"Old format: {len(old_results)} CVEs")
    logging.info(f"Migrated: {migrated_items} CVE-commit combinations")
    logging.info(f"Need reprocessing: {remaining_items} CVE-commit combinations")
    
    return new_results


def main():
    """
    Main function, demonstrating how to use commit-aware knowledge extractor
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('commit_aware_extraction.log'),
            logging.StreamHandler()
        ]
    )
    api_keys = [
        os.getenv("DEEPSEEK_API_KEY")
    ]
    
    api_base = "https://api.chatanywhere.tech/v1"
    model = "deepseek-chat"
    
    old_results_path = "KnowledgeRAG4LLMVulD/zh/knowledge_extraction/output/test_knowledge_extraction.json"
    new_results_path = "KnowledgeRAG4LLMVulD/zh/knowledge_extraction/output/vul_rag_test_knowledge.json"
    original_data_path = "KnowledgeRAG4LLMVulD/zh/VulInstruct/knowledge_extraction/CORRECT_database/processed_test_dataset.json"


    try:
        import os
        if os.path.exists(old_results_path):
            migrate_old_results(old_results_path, new_results_path, original_data_path)
        else:
            logging.info("Old results file not found, will start processing from scratch")
    except Exception as e:
        logging.warning(f"Error migrating old results: {e}")
    api_manager = APIManager(api_keys, api_base, model)
    extractor = CommitAwareKnowledgeExtractor(api_manager)
    try:
        data_list = DataUtils.load_json(original_data_path)
        logging.info(f"Loaded {len(data_list)} data items")
        extractor.extract_knowledge_concurrent(
            data_list=data_list,
            output_path=new_results_path,
            max_workers=15,
            resume=True
        )
        
    except Exception as e:
        logging.error(f"Main program execution error: {e}")
        raise


if __name__ == "__main__":
    main()