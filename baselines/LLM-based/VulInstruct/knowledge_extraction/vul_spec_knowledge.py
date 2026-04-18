import json
import logging
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import queue
import threading
from prompt_spec import generate_context_model_prompt, generate_threat_model_prompt
from query_llm import query_api


class APIManager:
    def __init__(self, api_keys: List[str], api_base: str, model: str):
        self.api_keys = api_keys
        self.api_base = api_base
        self.model = model
        self.api_queue = queue.Queue()
        self.lock = threading.Lock()
        
        for api_key in api_keys:
            self.api_queue.put(api_key)
    
    def get_api_key(self):
        return self.api_queue.get()
    
    def return_api_key(self, api_key: str):
        self.api_queue.put(api_key)
    
    def query_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        api_key = self.get_api_key()
        
        for attempt in range(max_retries):
            try:
                result = query_api(
                    api_base=self.api_base,
                    model=self.model,
                    api_key=api_key,
                    prompt=prompt
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


class ThreatModelingAnalyzer:

    
    def __init__(self, api_manager: APIManager):
        self.api_manager = api_manager
    
    def _call_api(self, prompt: str) -> str:
        return self.api_manager.query_with_retry(prompt)
    
    def _generate_unique_key(self, item: Dict[str, Any]) -> str:
        cve_id = item["cve_id"]
        commit_hash = item.get("commit_hash", "")
        return f"{cve_id}_{commit_hash}"
    
    def _extract_tagged_content(self, response: str, tag: str) -> str:
        pattern = f"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_all_specifications(self, response: str) -> List[str]:
        pattern = r"<spec>(.*?)</spec>"
        matches = re.findall(pattern, response, re.DOTALL)
        return [match.strip() for match in matches]
    
    def _prepare_code_data(self, item: Dict[str, Any]) -> Tuple[str, str, str]:
        vuln_code = ""
        if "vulnerableMethods_before" in item and item["vulnerableMethods_before"]:
            vuln_code = item["vulnerableMethods_before"][0].get("raw_code", "")
        
        fixed_code = ""
        if "vulnerableMethods_after" in item and item["vulnerableMethods_after"]:
            fixed_code = item["vulnerableMethods_after"][0].get("raw_code", "")
        
        code_context = item.get("code_context", "")
        
        return vuln_code, fixed_code, code_context
    
    def _generate_threat_model_prompt(self, repository: str, commit_message: str, 
                                    cve_description: str, cwe_type: str, 
                                    code_context: str, vuln: str, fixed: str) -> str:
        
        return generate_threat_model_prompt(repository, commit_message, cve_description, cwe_type, code_context, vuln, fixed)

    def _generate_context_model_prompt(self, commit_message: str, cve_description: str,
                                     cwe_type: str, code_context: str, vuln: str, 
                                     fixed: str, understand: str, specification: str) -> str:
        
        return generate_context_model_prompt(commit_message, cve_description, cwe_type, code_context, vuln, fixed, understand, specification)

    
    def stage1_analyze_single(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Stage 1: Analyze single system and generate security specifications
        """
        unique_key = self._generate_unique_key(item)
        
        try:
            repository = item.get("repository", "")
            commit_message = item.get("commit_msg", "")
            cve_description = item.get("cve_desc", "")
            cwe_type = item.get("cwe_list", [""])[0] if item.get("cwe_list") else ""
            
            vuln_code, fixed_code, code_context = self._prepare_code_data(item)
            
            if not cve_description:
                logging.warning(f"CVE description missing: {unique_key}")
                return None
            
            if not vuln_code:
                logging.warning(f"Vulnerable code missing: {unique_key}")
                return None
            
            prompt = self._generate_threat_model_prompt(
                repository=repository,
                commit_message=commit_message,
                cve_description=cve_description,
                cwe_type=cwe_type,
                code_context=code_context,
                vuln=vuln_code,
                fixed=fixed_code
            )
            
            response = self._call_api(prompt)
            
            understand = self._extract_tagged_content(response, "understand")
            classification = self._extract_tagged_content(response, "classification")
            specifications = self._extract_all_specifications(response)
            
            if not understand or not specifications:
                logging.warning(f"Stage 1 analysis result incomplete: {unique_key}")
                return None
            
            return {
                "case_id": unique_key,
                "cve_id": item.get("cve_id", ""),
                "commit_hash": item.get("commit_hash", ""),
                "repository": repository,
                "cwe_type": cwe_type,
                "commit_msg": commit_message,
                "cve_desc": cve_description,
                "stage1_response": response,
                "understand": understand,
                "classification": classification,
                "specifications": specifications,
                "specifications_text": "\n".join(specifications),
                "processed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error during Stage 1 analysis of {unique_key}: {str(e)}")
            return None
    
    def stage2_analyze_single(self, item: Dict[str, Any], stage1_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Stage 2: Perform detailed threat modeling based on Stage 1 results
        """
        unique_key = self._generate_unique_key(item)
        
        try:
            commit_message = item.get("commit_msg", "")
            cve_description = item.get("cve_desc", "")
            cwe_type = item.get("cwe_list", [""])[0] if item.get("cwe_list") else ""
            
            vuln_code, fixed_code, code_context = self._prepare_code_data(item)
            understand = stage1_result["understand"]
            specifications = stage1_result["specifications_text"]
            prompt = self._generate_context_model_prompt(
                commit_message=commit_message,
                cve_description=cve_description,
                cwe_type=cwe_type,
                code_context=code_context,
                vuln=vuln_code,
                fixed=fixed_code,
                understand=understand,
                specification=specifications
            )
            
            response = self._call_api(prompt)
            model = self._extract_tagged_content(response, "model")
            vuln_analysis = self._extract_tagged_content(response, "vuln")
            solution_analysis = self._extract_tagged_content(response, "solution")
            
            if not model:
                logging.warning(f"Stage 2 analysis result incomplete: {unique_key}")
                return None
            
            final_result = stage1_result.copy()
            final_result.update({
                "stage2_response": response,
                "threat_model": model,
                "vulnerability_analysis": vuln_analysis,
                "solution_analysis": solution_analysis,
                "stages_completed": ["stage1", "stage2"],
                "stage2_processed_at": datetime.now().isoformat()
            })
            
            return final_result
            
        except Exception as e:
            logging.error(f"Error during Stage 2 analysis of {unique_key}: {str(e)}")
            return None
    
    def run_stage1_batch(self, data_list: List[Dict[str, Any]], output_path: str, 
                         max_workers: int = 10, resume: bool = True) -> Dict[str, Any]:
        """
        Run Stage 1 analysis in batch
        """
        if resume and os.path.exists(output_path):
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
                processed_keys = set(existing_results.get("cases", {}).keys())
                logging.info(f"Resume mode: {len(processed_keys)} cases already processed")
            except Exception as e:
                logging.warning(f"Failed to load existing results: {e}")
                existing_results = {"cases": {}}
                processed_keys = set()
        else:
            existing_results = {"cases": {}}
            processed_keys = set()
        items_to_process = []
        for item in data_list:
            unique_key = self._generate_unique_key(item)
            if unique_key not in processed_keys:
                items_to_process.append(item)
        
        logging.info(f"Stage 1: Total {len(items_to_process)} cases to process")
        
        if len(items_to_process) == 0:
            logging.info("Stage 1: All cases have been processed")
            return existing_results
        successful_count = len(processed_keys)
        failed_count = 0
        failed_items = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {
                executor.submit(self.stage1_analyze_single, item): item 
                for item in items_to_process
            }
            for future in tqdm(as_completed(future_to_item), total=len(items_to_process), desc="Stage 1 Progress"):
                item = future_to_item[future]
                unique_key = self._generate_unique_key(item)
                
                try:
                    result = future.result()
                    if result:
                        existing_results["cases"][unique_key] = result
                        successful_count += 1
                        if successful_count % 100 == 0:
                            self._save_results(existing_results, output_path)
                            logging.info(f"Stage 1: Progress saved, {successful_count} items successfully processed")
                    else:
                        failed_count += 1
                        failed_items.append(unique_key)
                            
                except Exception as e:
                    failed_count += 1
                    failed_items.append(unique_key)
                    logging.error(f"Error processing {unique_key}: {e}")
        existing_results["metadata"] = {
            "stage": "stage1",
            "total_input": len(data_list),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "success_rate": successful_count / len(data_list) * 100,
            "processed_at": datetime.now().isoformat(),
            "failed_cases": failed_items
        }
        
        self._save_results(existing_results, output_path)
        
        logging.info(f"Stage 1 completed! Success: {successful_count}, Failed: {failed_count}")
        return existing_results
    
    def run_stage2_batch(self, data_list: List[Dict[str, Any]], stage1_results_path: str, 
                         output_path: str, max_workers: int = 10, resume: bool = True) -> Dict[str, Any]:
        """
        Run Stage 2 analysis in batch
        """
        try:
            with open(stage1_results_path, 'r', encoding='utf-8') as f:
                stage1_results = json.load(f)
            stage1_cases = stage1_results.get("cases", {})
            logging.info(f"Loaded {len(stage1_cases)} Stage 1 results")
        except Exception as e:
            logging.error(f"Unable to load Stage 1 results: {e}")
            return {}
        if resume and os.path.exists(output_path):
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
                processed_keys = set(existing_results.get("cases", {}).keys())
                logging.info(f"Resume mode: {len(processed_keys)} cases already completed Stage 2 processing")
            except Exception as e:
                logging.warning(f"Failed to load existing Stage 2 results: {e}")
                existing_results = {"cases": {}}
                processed_keys = set()
        else:
            existing_results = {"cases": {}}
            processed_keys = set()
        data_map = {self._generate_unique_key(item): item for item in data_list}
        items_to_process = []
        for unique_key, stage1_result in stage1_cases.items():
            if unique_key not in processed_keys and unique_key in data_map:
                items_to_process.append((data_map[unique_key], stage1_result))
        
        logging.info(f"Stage 2: Total {len(items_to_process)} cases to process")
        
        if len(items_to_process) == 0:
            logging.info("Stage 2: All cases have been processed")
            return existing_results
        successful_count = len(processed_keys)
        failed_count = 0
        failed_items = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_data = {
                executor.submit(self.stage2_analyze_single, item, stage1_result): (item, stage1_result)
                for item, stage1_result in items_to_process
            }
            for future in tqdm(as_completed(future_to_data), total=len(items_to_process), desc="Stage 2 Progress"):
                item, stage1_result = future_to_data[future]
                unique_key = self._generate_unique_key(item)
                
                try:
                    result = future.result()
                    if result:
                        existing_results["cases"][unique_key] = result
                        successful_count += 1
                        if successful_count % 10 == 0:
                            self._save_results(existing_results, output_path)
                            logging.info(f"Stage 2: Progress saved, {successful_count} items successfully processed")
                    else:
                        failed_count += 1
                        failed_items.append(unique_key)
                            
                except Exception as e:
                    failed_count += 1
                    failed_items.append(unique_key)
                    logging.error(f"Error during Stage 2 processing of {unique_key}: {e}")
        existing_results["metadata"] = {
            "stage": "stage2",
            "total_stage1_cases": len(stage1_cases),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "success_rate": successful_count / len(stage1_cases) * 100 if len(stage1_cases) > 0 else 0,
            "processed_at": datetime.now().isoformat(),
            "failed_cases": failed_items
        }
        
        self._save_results(existing_results, output_path)
        
        logging.info(f"Stage 2 completed! Success: {successful_count}, Failed: {failed_count}")
        return existing_results
    
    def _save_results(self, results: Dict[str, Any], output_path: str):
        """Save results"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving results: {e}")


def main():
    """
    Main function
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('threat_modeling_separated.log'),
            logging.StreamHandler()
        ]
    )
    api_keys = [
        os.getenv("DEEPSEEK_API_KEY")
    ]
    api_base = "https://api.chatanywhere.tech/v1"
    model = "deepseek-chat"

    api_manager = APIManager(api_keys, api_base, model)
    original_data_path = "KnowledgeRAG4LLMVulD/zh/VulInstruct/knowledge_extraction/CORRECT_database/processed_train_dataset.json"
    output_dir = str(Path(__file__).parent / "output")
    
    stage1_output_path = os.path.join(output_dir, "train_stage1_results.json")
    stage2_output_path = os.path.join(output_dir, "train_stage2_results.json")
    analyzer = ThreatModelingAnalyzer(api_manager)
    try:
        with open(original_data_path, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
        logging.info(f"Loaded {len(data_list)} data items")
        data_list = data_list
        logging.info("=" * 60)
        logging.info("Starting Stage 1 analysis: System understanding and security specification generation")
        logging.info("=" * 60)
        
        stage1_results = analyzer.run_stage1_batch(
            data_list=data_list,
            output_path=stage1_output_path,
            max_workers=20,
            resume=True
        )
        logging.info("=" * 60)
        logging.info("Starting Stage 2 analysis: Detailed threat modeling")
        logging.info("=" * 60)
        
        stage2_results = analyzer.run_stage2_batch(
            data_list=data_list,
            stage1_results_path=stage1_output_path,
            output_path=stage2_output_path,
            max_workers=5,
            resume=True
        )
        
        
        logging.info("=" * 60)
        logging.info("All threat modeling analysis completed!")
        logging.info(f"Stage 1 results saved at: {stage1_output_path}")
        logging.info(f"Stage 2 results saved at: {stage2_output_path}")
        logging.info("=" * 60)
        
    except Exception as e:
        logging.error(f"Main program execution error: {e}")
        raise


if __name__ == "__main__":
    main()