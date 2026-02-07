
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
import concurrent.futures
import tiktoken
from datetime import datetime
import os

os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)
current_dir = Path(__file__).resolve().parent
detection_root = current_dir.parent.parent
project_root = detection_root.parent
retrieval_root = project_root / "primevul_retrieval"
sys.path.append(str(detection_root))
sys.path.append(str(project_root))
sys.path.append(str(retrieval_root))

from utils.api_manager import APIManager
from core.knowledge_systems.knowledge_scoring_cache import KnowledgeScoringCache
from core.data_loaders.vulinstruct_dataset_loader import VulInstructDatasetLoader
from core.detectors.vulinstruct_two_stage_detector import VulInstructTwoStageDetector

class KnowledgeScoringBuilder:
    
    def __init__(self, max_workers: int = 40, model_score_name: str = "deepseek-v3"):
        self.max_workers = max_workers
        self.model_score_name = model_score_name
        self.api_manager = APIManager()
        self.knowledge_cache = KnowledgeScoringCache()
        self.data_loader = VulInstructDatasetLoader()
        
        self.detector = VulInstructTwoStageDetector(
            self.api_manager,
            model_name="deepseek/deepseek-chat",
            model_eval_name="deepseek/deepseek-chat",
            model_score_name=self.model_score_name
        )
        
        self.setup_logging()
        
        self.logger.info(f"🚀 Knowledge scoring cache builder initialized successfully")
        self.logger.info(f"   Concurrent workers: {max_workers}")
        self.logger.info(f"   Scoring model: {model_score_name}")
        self.logger.info(f"   Target: Build complete knowledge scoring cache for 419 pairs dataset")
        
        self.stats = {
            "total_samples": 0,
            "vulspec_scored": 0,
            "nvd_scored": 0, 
            "spec_scored": 0,
            "vulspec_cached": 0,
            "nvd_cached": 0,
            "spec_cached": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
            "total_tokens": 0,
            "total_api_time": 0.0,
            "total_api_calls": 0
        }
    
    def setup_logging(self):
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_filename = f"knowledge_scoring_builder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            file_handler = logging.FileHandler(log_dir / log_filename)
            file_handler.setLevel(logging.INFO)
            
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def _count_tokens(self, text, model="cl100k_base"):
        if not text:
            return 0
        try:
            encoding = tiktoken.get_encoding(model)
            if isinstance(text, (dict, list)):
                text = json.dumps(text, ensure_ascii=False)
            else:
                text = str(text)
            return len(encoding.encode(text))
        except Exception:
            return len(str(text))
    
    def _call_api_with_retry(self, prompt: str, model_name: str, max_retries: int = 3) -> str:
        result = self.detector._call_api_with_retry(prompt, use_model=model_name, max_retries=max_retries)
        if isinstance(result, tuple) and len(result) >= 2:
            response_text, tokens = result[0], result[1]
            return response_text
        elif isinstance(result, tuple):
            return str(result[0])
        else:
            self.logger.warning(f"API returned unexpected type: {type(result)}")
            return str(result)
    
    def _evaluate_vulspec_relevance(self, code_snippet: str, vulspec_cases: List[Dict]) -> Dict:
        if not vulspec_cases:
            return {"scores": []}
        
        cases_for_evaluation = []
        for i, case in enumerate(vulspec_cases, 1):
            case_data = case.get("case_data", case) if "case_data" in case else case
            case_cve_id = case_data.get("cve_id", f"Case-{i}")
            
            case_eval_parts = []
            case_eval_parts.append(f"**{case_cve_id}**")
            
            understand = case_data.get("understand", "")
            if understand:
                understand_summary = understand[:600] + "..." if len(understand) > 600 else understand
                case_eval_parts.append(f"system identification: {understand_summary}")
            
            threat_model = case_data.get("threat_model", "")
            if threat_model:
                if "<cwe_analysis>" in threat_model:
                    cwe_section = threat_model.split("<cwe_analysis>")[1].split("</cwe_analysis>")[0].strip()[:400]
                    case_eval_parts.append(f"CWE analysis: {cwe_section}")
                
                if "<attack_surfaces>" in threat_model:
                    attack_section = threat_model.split("<attack_surfaces>")[1].split("</attack_surfaces>")[0].strip()[:400]
                    case_eval_parts.append(f"attack surfaces: {attack_section}")
            
            code_analysis = case_data.get("code_analysis", "")
            if code_analysis:
                if "<vulnerability_location>" in code_analysis:
                    vuln_location = code_analysis.split("<vulnerability_location>")[1].split("</vulnerability_location>")[0].strip()[:400]
                    case_eval_parts.append(f"vulnerability location: {vuln_location}")
                
                if "<fix_analysis>" in code_analysis:
                    fix_analysis_text = code_analysis.split("<fix_analysis>")[1].split("</fix_analysis>")[0].strip()[:400]
                    case_eval_parts.append(f"fix analysis: {fix_analysis_text}")
            
            cases_for_evaluation.append(f"VulSpec Case {i}:\n" + "\n".join(case_eval_parts))
        
        evaluation_prompt = f"""You are a security expert. Please evaluate the relevance between the following code and VulSpec vulnerability cases.
```c
{code_snippet}
```
{chr(10).join(cases_for_evaluation)}

Please score the relevance of each case to the target code (1-10 points):

**Scoring criteria**:
- 10 points: Highly relevant, vulnerability type, trigger conditions, and code patterns are almost identical
- 8-9 points: Strong relevance, main vulnerability features are similar, can provide valuable reference
- 6-7 points: Moderate relevance, some features are similar, has certain reference value
- 4-5 points: Weak relevance, only few similarities
- 1-3 points: Very low relevance, basically no reference value

Please strictly follow the HTML format for output:

<vulspec_evaluation>
<case_1_score>6</case_1_score>
<case_1_reasoning>Scoring reason</case_1_reasoning>
<case_2_score>8</case_2_score>
<case_2_reasoning>Scoring reason</case_2_reasoning>
...
</vulspec_evaluation>"""
        
        try:
            t_start = time.time()
            input_tokens = self._count_tokens(evaluation_prompt)
            response = self._call_api_with_retry(evaluation_prompt, self.model_score_name)
            if not isinstance(response, str):
                self.logger.error(f"Response is not string after API call: {type(response)}")
                response = str(response)
            duration = time.time() - t_start
            output_tokens = self._count_tokens(response)
            self.stats["total_tokens"] += (input_tokens + output_tokens)
            self.stats["total_api_time"] += duration
            self.stats["total_api_calls"] += 1

            return self._parse_vulspec_evaluation(response, vulspec_cases)
        except Exception as e:
            self.logger.error(f"VulSpec evaluation failed: {e}", exc_info=True)
            return {"scores": [{"case": case, "score": 5, "reasoning": f"Evaluation failed: {e}"} for case in vulspec_cases]}
    
    def _evaluate_nvd_relevance(self, code_snippet: str, nvd_cases: List[Dict]) -> Dict:
        if not nvd_cases:
            return {"scores": []}
        
        cases_for_evaluation = []
        for i, case in enumerate(nvd_cases, 1):
            case_cve_id = case.get("cve_id", f"NVD-{i}")
            description = case.get("description", "")[:400] + "..." if len(case.get("description", "")) > 400 else case.get("description", "")
            cases_for_evaluation.append(f"NVD Case {i} ({case_cve_id}):\n{description}")
        
        evaluation_prompt = f"""You are a security expert. Please evaluate the relevance between the following code and NVD vulnerability data.
```c
{code_snippet}
```
{chr(10).join(cases_for_evaluation)}

Please score the relevance of each case to the target code (1-10 points):

**Scoring criteria**:
- 10 points: Highly relevant, same vulnerability type and similar code context
- 8-9 points: Strong relevance, vulnerability type matches, can provide clear guidance
- 6-7 points: Moderate relevance, partial features match, has certain guidance significance
- 4-5 points: Weak relevance, only vague similarities
- 1-3 points: Very low relevance, basically unrelated

Please strictly follow the HTML format for output:

<nvd_evaluation>
<nvd_1_score>7</nvd_1_score>
<nvd_1_reasoning>Scoring reason</nvd_1_reasoning>
<nvd_2_score>5</nvd_2_score>
<nvd_2_reasoning>Scoring reason</nvd_2_reasoning>
...
</nvd_evaluation>"""
        
        try:
            t_start = time.time()
            input_tokens = self._count_tokens(evaluation_prompt)
            response = self._call_api_with_retry(evaluation_prompt, self.model_score_name)
            if not isinstance(response, str):
                self.logger.error(f"Response is not string after API call: {type(response)}")
                response = str(response)
            duration = time.time() - t_start
            output_tokens = self._count_tokens(response)
            self.stats["total_tokens"] += (input_tokens + output_tokens)
            self.stats["total_api_time"] += duration
            self.stats["total_api_calls"] += 1
            
            return self._parse_nvd_evaluation(response, nvd_cases)
        except Exception as e:
            self.logger.error(f"NVD evaluation failed: {e}", exc_info=True)
            return {"scores": [{"case": case, "score": 5, "reasoning": f"Evaluation failed: {e}"} for case in nvd_cases]}
    
    def _evaluate_spec_relevance(self, code_snippet: str, specifications: List[str]) -> Dict:
        if not specifications:
            return {"scores": []}
        
        specs_for_evaluation = []
        for i, spec in enumerate(specifications, 1):
            spec_text = spec[:300] + "..." if len(spec) > 300 else spec
            specs_for_evaluation.append(f"Specification {i}:\n{spec_text}")
        
        evaluation_prompt = f"""You are a security expert. Please evaluate the relevance between the following code and secure coding specifications.
```c
{code_snippet}
```
{chr(10).join(specs_for_evaluation)}

Please score the relevance of each specification to the target code (1-10 points):

**Scoring criteria**:
- 10 points: Highly relevant, specification directly addresses the code's security issues
- 8-9 points: Strong relevance, specification provides clear security guidance for this code
- 6-7 points: Moderate relevance, specification has some application to this code
- 4-5 points: Weak relevance, specification only loosely related
- 1-3 points: Very low relevance, specification not applicable

Please strictly follow the HTML format for output:

<spec_evaluation>
<spec_1_score>8</spec_1_score>
<spec_1_reasoning>Scoring reason</spec_1_reasoning>
<spec_2_score>4</spec_2_score>
<spec_2_reasoning>Scoring reason</spec_2_reasoning>
...
</spec_evaluation>"""
        
        try:
            t_start = time.time()
            input_tokens = self._count_tokens(evaluation_prompt)
            response = self._call_api_with_retry(evaluation_prompt, self.model_score_name)
            if not isinstance(response, str):
                self.logger.error(f"Response is not string after API call: {type(response)}")
                response = str(response)
            duration = time.time() - t_start
            output_tokens = self._count_tokens(response)
            self.stats["total_tokens"] += (input_tokens + output_tokens)
            self.stats["total_api_time"] += duration
            self.stats["total_api_calls"] += 1
            
            return self._parse_spec_evaluation(response, specifications)
        except Exception as e:
            self.logger.error(f"Specification evaluation failed: {e}", exc_info=True)
            return {"scores": [{"specification": spec, "score": 5, "reasoning": f"Evaluation failed: {e}"} for spec in specifications]}
    
    def _parse_vulspec_evaluation(self, response: str, vulspec_cases: List[Dict]) -> Dict:
        try:
            import re
            if not isinstance(response, str):
                self.logger.warning(f"Response is not a string in parse function, got {type(response)}, converting...")
                response = str(response)
            
            scores = []
            eval_pattern = r'<vulspec_evaluation>(.*?)</vulspec_evaluation>'
            eval_match = re.search(eval_pattern, response, re.DOTALL)
            
            if eval_match:
                eval_content = eval_match.group(1)
                
                for i, case in enumerate(vulspec_cases, 1):
                    score_pattern = f'<case_{i}_score>([0-9]+)</case_{i}_score>'
                    reason_pattern = f'<case_{i}_reasoning>(.*?)</case_{i}_reasoning>'
                    
                    score_match = re.search(score_pattern, eval_content)
                    reason_match = re.search(reason_pattern, eval_content, re.DOTALL)
                    
                    score = int(score_match.group(1)) if score_match else 5
                    reasoning = reason_match.group(1).strip() if reason_match else "No evaluation reason"
                    
                    scores.append({
                        "case": case,
                        "score": score,
                        "reasoning": reasoning
                    })
            else:
                for case in vulspec_cases:
                    scores.append({"case": case, "score": 5, "reasoning": "Parsing failed, default score"})
            
            return {"scores": scores}
        except Exception as e:
            self.logger.error(f"VulSpec evaluation parsing failed: {e}", exc_info=True)
            return {"scores": [{"case": case, "score": 5, "reasoning": f"Parsing exception: {e}"} for case in vulspec_cases]}
    
    def _parse_nvd_evaluation(self, response: str, nvd_cases: List[Dict]) -> Dict:
        try:
            import re
            if not isinstance(response, str):
                self.logger.warning(f"Response is not a string in parse function, got {type(response)}, converting...")
                response = str(response)
            
            scores = []
            eval_pattern = r'<nvd_evaluation>(.*?)</nvd_evaluation>'
            eval_match = re.search(eval_pattern, response, re.DOTALL)
            
            if eval_match:
                eval_content = eval_match.group(1)
                
                for i, case in enumerate(nvd_cases, 1):
                    score_pattern = f'<nvd_{i}_score>([0-9]+)</nvd_{i}_score>'
                    reason_pattern = f'<nvd_{i}_reasoning>(.*?)</nvd_{i}_reasoning>'
                    
                    score_match = re.search(score_pattern, eval_content)
                    reason_match = re.search(reason_pattern, eval_content, re.DOTALL)
                    
                    score = int(score_match.group(1)) if score_match else 5
                    reasoning = reason_match.group(1).strip() if reason_match else "No evaluation reason"
                    
                    scores.append({
                        "case": case,
                        "score": score,
                        "reasoning": reasoning
                    })
            else:
                for case in nvd_cases:
                    scores.append({"case": case, "score": 5, "reasoning": "Parsing failed, default score"})
            
            return {"scores": scores}
        except Exception as e:
            self.logger.error(f"NVD evaluation parsing failed: {e}", exc_info=True)
            return {"scores": [{"case": case, "score": 5, "reasoning": f"Parsing exception: {e}"} for case in nvd_cases]}
    
    def _parse_spec_evaluation(self, response: str, specifications: List[str]) -> Dict:
        try:
            import re
            if not isinstance(response, str):
                self.logger.warning(f"Response is not a string in parse function, got {type(response)}, converting...")
                response = str(response)
            
            scores = []
            eval_pattern = r'<spec_evaluation>(.*?)</spec_evaluation>'
            eval_match = re.search(eval_pattern, response, re.DOTALL)
            
            if eval_match:
                eval_content = eval_match.group(1)
                
                for i, spec in enumerate(specifications, 1):
                    score_pattern = f'<spec_{i}_score>([0-9]+)</spec_{i}_score>'
                    reason_pattern = f'<spec_{i}_reasoning>(.*?)</spec_{i}_reasoning>'
                    
                    score_match = re.search(score_pattern, eval_content)
                    reason_match = re.search(reason_pattern, eval_content, re.DOTALL)
                    
                    score = int(score_match.group(1)) if score_match else 5
                    reasoning = reason_match.group(1).strip() if reason_match else "No evaluation reason"
                    
                    scores.append({
                        "specification": spec,
                        "score": score,
                        "reasoning": reasoning
                    })
            else:
                for spec in specifications:
                    scores.append({"specification": spec, "score": 5, "reasoning": "Parsing failed, default score"})
            
            return {"scores": scores}
        except Exception as e:
            self.logger.error(f"Specification evaluation parsing failed: {e}", exc_info=True)
            return {"scores": [{"specification": spec, "score": 5, "reasoning": f"Parsing exception: {e}"} for spec in specifications]}
    
    def _process_sample_scoring(self, sample: Dict, sample_idx: int) -> Dict:
        sample_id = sample.get("sample_id", "unknown")
        cve_id = sample.get("cve_id", "")
        code_type = sample.get("code_type", "")
        data_source = sample.get("data_source", "")
        code_snippet = sample.get("code_snippet", "")
        knowledge = sample.get("knowledge", {})
        
        result = {
            "sample_id": sample_id,
            "sample_idx": sample_idx,
            "cve_id": cve_id,
            "code_type": code_type,
            "data_source": data_source,
            "vulspec_status": "skipped",
            "nvd_status": "skipped", 
            "spec_status": "skipped",
            "errors": []
        }
        
        try:
            vulspec_cases = knowledge.get("vulspec_cases", [])
            if vulspec_cases:
                cached_vulspec = self.knowledge_cache.get_vulspec_evaluation(
                    cve_id, code_type, data_source, code_snippet, vulspec_cases[:10]
                )
                
                if cached_vulspec is not None:
                    result["vulspec_status"] = "cached"
                    self.stats["vulspec_cached"] += 1
                else:
                    vulspec_result = self._evaluate_vulspec_relevance(code_snippet, vulspec_cases[:10])
                    self.knowledge_cache.cache_vulspec_evaluation(
                        cve_id, code_type, data_source, code_snippet, vulspec_cases[:10], vulspec_result
                    )
                    result["vulspec_status"] = "scored"
                    self.stats["vulspec_scored"] += 1
            
            nvd_cases = knowledge.get("nvd_cases", [])
            if nvd_cases:
                cached_nvd = self.knowledge_cache.get_nvd_evaluation(
                    cve_id, code_type, data_source, code_snippet, nvd_cases[:10]
                )
                
                if cached_nvd is not None:
                    result["nvd_status"] = "cached"
                    self.stats["nvd_cached"] += 1
                else:
                    nvd_result = self._evaluate_nvd_relevance(code_snippet, nvd_cases[:10])
                    self.knowledge_cache.cache_nvd_evaluation(
                        cve_id, code_type, data_source, code_snippet, nvd_cases[:10], nvd_result
                    )
                    result["nvd_status"] = "scored"
                    self.stats["nvd_scored"] += 1
            
            specifications = knowledge.get("specifications", [])
            if specifications:
                cached_spec = self.knowledge_cache.get_spec_evaluation(
                    cve_id, code_type, data_source, code_snippet, specifications[:10]
                )
                
                if cached_spec is not None:
                    result["spec_status"] = "cached"
                    self.stats["spec_cached"] += 1
                else:
                    spec_result = self._evaluate_spec_relevance(code_snippet, specifications[:10])
                    self.knowledge_cache.cache_spec_evaluation(
                        cve_id, code_type, data_source, code_snippet, specifications[:10], spec_result
                    )
                    result["spec_status"] = "scored"
                    self.stats["spec_scored"] += 1
            
        except Exception as e:
            error_msg = f"Sample processing failed: {e}"
            result["errors"].append(error_msg)
            self.stats["errors"] += 1
            self.logger.error(f"❌ {sample_id}: {error_msg}")
        
        return result
    
    def build_knowledge_cache(self, samples_limit: Optional[int] = None) -> Dict:
        self.logger.info("=" * 100)
        self.logger.info("🚀 Starting to build knowledge scoring cache")
        self.logger.info("=" * 100)
        
        self.stats["start_time"] = time.time()
        
        try:
            self.logger.info("📊 Loading V15 complete dataset...")
            samples = self.data_loader.load_full_detection_samples(limit=samples_limit)
            
            if not samples:
                self.logger.error("❌ No valid samples loaded")
                return {"error": "No valid samples loaded"}
            
            self.stats["total_samples"] = len(samples)
            actual_samples = len(samples)
            
            self.logger.info(f"🎯 Starting concurrent knowledge scoring (concurrency: {self.max_workers}, samples: {actual_samples})")
            
            initial_cache_stats = self.knowledge_cache.get_cache_statistics()
            self.logger.info(f"📋 Initial cache status: VulSpec={initial_cache_stats['vulspec_cache_size']}, "
                           f"NVD={initial_cache_stats['nvd_cache_size']}, Spec={initial_cache_stats['spec_cache_size']}")
            
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_sample = {
                    executor.submit(self._process_sample_scoring, sample, i): (sample, i)
                    for i, sample in enumerate(samples)
                }
                
                completed = 0
                for future in concurrent.futures.as_completed(future_to_sample):
                    sample, idx = future_to_sample[future]
                    
                    try:
                        result = future.result()
                        results.append(result)
                        completed += 1
                        
                        if completed % 100 == 0:
                            progress_pct = completed / len(samples) * 100
                            current_time = time.time() - self.stats["start_time"]
                            speed = completed / current_time if current_time > 0 else 0
                            
                            self.logger.info(f"📈 Progress: {completed}/{len(samples)} ({progress_pct:.1f}%) "
                                           f"speed: {speed:.1f} samples/sec")
                            self.logger.info(f"   Current status: VulSpec scoring={self.stats['vulspec_scored']}, "
                                           f"NVD scoring={self.stats['nvd_scored']}, Spec scoring={self.stats['spec_scored']}")
                            self.logger.info(f"   cache hit: VulSpec={self.stats['vulspec_cached']}, "
                                           f"NVD={self.stats['nvd_cached']}, Spec={self.stats['spec_cached']}")
                    
                    except Exception as e:
                        error_result = {
                            "sample_id": sample.get("sample_id", "unknown"),
                            "sample_idx": idx,
                            "errors": [f"Processing exception: {e}"]
                        }
                        results.append(error_result)
                        self.stats["errors"] += 1
                        self.logger.error(f"❌ Sample {idx + 1} processing exception: {e}")
            
            self.stats["end_time"] = time.time()
            
            self._print_final_report(results)
            
            return {
                "success": True,
                "stats": self.stats,
                "results": results,
                "final_cache_stats": self.knowledge_cache.get_cache_statistics()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Knowledge scoring cache build failed: {e}")
            return {"error": str(e), "success": False}
    
    def _print_final_report(self, results: List[Dict]):
        elapsed_time = self.stats["end_time"] - self.stats["start_time"]
        total_tokens = self.stats["total_tokens"]
        total_samples = self.stats["total_samples"]
        api_calls = self.stats["total_api_calls"]
        
        self.logger.info("=" * 100)
        self.logger.info("📊 Knowledge scoring cache build completion report")
        self.logger.info("=" * 100)
        
        self.logger.info(f"📈 Processing statistics:")
        self.logger.info(f"   Total samples: {total_samples}")
        self.logger.info(f"   Processing time elapsed: {elapsed_time:.2f} seconds")
        self.logger.info(f"   Processing speed: {total_samples/elapsed_time:.2f} samples/sec")
        self.logger.info(f"   Error count: {self.stats['errors']}")
        
        self.logger.info(f"\n🎯 Scoring execution statistics:")
        self.logger.info(f"   VulSpec new scoring: {self.stats['vulspec_scored']}")
        self.logger.info(f"   NVD new scoring: {self.stats['nvd_scored']}")
        self.logger.info(f"   Spec new scoring: {self.stats['spec_scored']}")
        self.logger.info(f"   Total new scoring: {self.stats['vulspec_scored'] + self.stats['nvd_scored'] + self.stats['spec_scored']}")
        
        self.logger.info(f"\n💾 Cache hit statistics:")
        self.logger.info(f"   VulSpec cache hit: {self.stats['vulspec_cached']}")
        self.logger.info(f"   NVD cache hit: {self.stats['nvd_cached']}")
        self.logger.info(f"   Spec cache hit: {self.stats['spec_cached']}")
        self.logger.info(f"   Total cache hit: {self.stats['vulspec_cached'] + self.stats['nvd_cached'] + self.stats['spec_cached']}")
        
        success_samples = len([r for r in results if not r.get("errors")])
        success_rate = success_samples / len(results) if results else 0
        self.logger.info(f"\n✅ Success rate: {success_rate:.1%}")
        self.logger.info(f"\n💰 Token & Latency Analysis:")
        self.logger.info(f"   Total Tokens Consumed: {total_tokens:,}")
        
        if api_calls > 0:
            avg_tokens_per_call = total_tokens / api_calls
            avg_time_per_call = self.stats["total_api_time"] / api_calls
            self.logger.info(f"   Avg Tokens/Call: {avg_tokens_per_call:.1f} (Actual LLM requests)")
            self.logger.info(f"   Avg Latency/Call: {avg_time_per_call:.2f}s")
        
        if total_samples > 0:
            avg_tokens_per_sample = total_tokens / total_samples
            self.logger.info(f"   Avg Tokens/Sample: {avg_tokens_per_sample:.1f} (Amortized over all samples)")
        if total_samples > 0 and total_samples < 838:
            estimated_full_tokens = (total_tokens / total_samples) * 838
            self.logger.info(f"   Estimated Full Dataset (838 samples): {estimated_full_tokens:,.0f} tokens")

        self.logger.info("=" * 100)
        self.logger.info("🎉 Knowledge scoring cache build completed!")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Knowledge scoring cache builder")
    parser.add_argument("--workers", type=int, default=20, help="Number of concurrent workers")
    parser.add_argument("--samples", type=int, default=2000, help="Processing samples limit (default all)")
    parser.add_argument("--model-score", type=str, default="deepseek/deepseek-chat", help="Scoring model name")
    
    args = parser.parse_args()
    
    try:
        builder = KnowledgeScoringBuilder(
            max_workers=args.workers,
            model_score_name=args.model_score
        )
        
        result = builder.build_knowledge_cache(samples_limit=args.samples)
        
        if result.get("success"):
            print("\n" + "=" * 100)
            print("🎉 Knowledge scoring cache build successful!")
            print("=" * 100)
            
            stats = result["stats"]
            final_cache = result["final_cache_stats"]
            
            print(f"📊 Final statistics:")
            print(f"   Processed samples: {stats['total_samples']}")
            print(f"   New scoring: VulSpec={stats['vulspec_scored']}, NVD={stats['nvd_scored']}, Spec={stats['spec_scored']}")
            print(f"   cache hit: VulSpec={stats['vulspec_cached']}, NVD={stats['nvd_cached']}, Spec={stats['spec_cached']}")
            print(f"   Final cache: {final_cache['total_cache_entries']} records")
            print(f"   Processing speed: {stats['total_samples']/(stats['end_time'] - stats['start_time']):.1f} samples/sec")
            
            if stats["errors"] == 0:
                print("✅ All samples processed successfully, cache system ready!")
            else:
                print(f"⚠️  {stats['errors']} samples processing failed, but cache is basically available")
        else:
            print(f"❌ Knowledge scoring cache build failed: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Program execution exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()