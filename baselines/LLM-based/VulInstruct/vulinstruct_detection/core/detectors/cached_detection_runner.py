
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import concurrent.futures
from datetime import datetime
import os
from tqdm import tqdm
import threading
from collections import defaultdict
import re

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
from core.detectors.vulinstruct_two_stage_detector import VulInstructTwoStageDetector
from core.data_loaders.vulinstruct_dataset_loader import VulInstructDatasetLoader

class CachedDetectionRunner:
    
    def __init__(self, max_workers: int = 30, test_samples: Optional[int] = None,
                 model_name: str = "deepseek/deepseek-chat", model_eval_name: str = "deepseek/deepseek-chat", 
                 model_score_name: str = "deepseek/deepseek-chat",
                 vulspec_threshold: float = 8, nvd_threshold: float = 8, 
                 spec_threshold: float = 8, use_code_context: bool = True):
        
        self.max_workers = max_workers
        self.test_samples = test_samples
        self.model_name = model_name
        self.model_eval_name = model_eval_name
        self.model_score_name = model_score_name
        self.vulspec_threshold = vulspec_threshold
        self.nvd_threshold = nvd_threshold
        self.spec_threshold = spec_threshold
        self.use_code_context = use_code_context
        
        self.api_manager = APIManager()
        self.detector = VulInstructTwoStageDetector(
            self.api_manager,
            model_name=self.model_name,
            model_eval_name=self.model_eval_name,
            model_score_name=self.model_score_name,
            vulspec_threshold=self.vulspec_threshold,
            nvd_threshold=self.nvd_threshold,
            spec_threshold=self.spec_threshold,
            use_code_context=self.use_code_context
        )
        self.data_loader = VulInstructDatasetLoader()
        
        self.results_lock = threading.Lock()
        self.completed_results = []
        self.realtime_metrics_interval = 20

        self.token_stats = {
            "total_tokens": 0,
            "total_samples": 0,
             "sample_tokens": []
        }
        
        self.setup_logging()
        

    
    def setup_logging(self):
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_filename = f"cached_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
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
    
    def run_cached_detection(self) -> Dict:

        
        start_time = time.time()
        
        try:
            self.logger.info("📊 Loading dataset...")
            samples = self.data_loader.load_full_detection_samples(limit=self.test_samples)
            
            if not samples:
                self.logger.error("❌ Failed to load valid samples")
                return {"error": "No valid samples loaded"}
            
            dataset_stats = self.data_loader.get_dataset_statistics()
            
            cache_stats = self.detector.knowledge_cache.get_cache_statistics()

            actual_samples = len(samples)

            
            results = []
            cache_hits = {"vulspec": 0, "nvd": 0, "spec": 0}

            with self.results_lock:
                self.token_stats = {
                    "total_tokens": 0,
                    "total_samples": 0,
                    "sample_tokens": []
                } 
            
            with tqdm(total=actual_samples, desc="🔍 Vulnerability detection progress", 
                     bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]") as pbar:
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_sample = {
                        executor.submit(self._detect_sample_with_cache_tracking, sample, i): (sample, i)
                        for i, sample in enumerate(samples)
                    }
                    
                    for future in concurrent.futures.as_completed(future_to_sample):
                        sample, idx = future_to_sample[future]
                        try:
                            result, sample_cache_hits = future.result()
                            
                            with self.results_lock:
                                results.append(result)
                                self.completed_results.append(result)

                                sample_tokens = result.get('avg_tokens_per_sample', 0)
                                if sample_tokens > 0:
                                    self.token_stats["total_tokens"] += sample_tokens
                                    self.token_stats["total_samples"] += 1
                                    self.token_stats["sample_tokens"].append(sample_tokens)

                                current_count = len(self.completed_results)
                            
                            for cache_type, hits in sample_cache_hits.items():
                                cache_hits[cache_type] += hits
                            
                            pbar.update(1)
                            
                            if current_count % self.realtime_metrics_interval == 0:
                                with self.results_lock:
                                    current_results_copy = self.completed_results.copy()
                                    current_token_stats = self.token_stats.copy() 
                                
                                realtime_metrics = self._calculate_realtime_correct_metrics(current_results_copy)
                                self._display_realtime_metrics(current_count, realtime_metrics, cache_hits, current_token_stats)
                                
                        except Exception as e:
                            self.logger.error(f"❌ Detection failed - sample {idx + 1}: {e}")
                            error_result = self._create_error_result(sample, str(e))
                            
                            with self.results_lock:
                                results.append(error_result)
                                self.completed_results.append(error_result)
                            
                            pbar.update(1)
            
            elapsed_time = time.time() - start_time
            
            metrics = self.calculate_comprehensive_metrics(results)
            self.print_comprehensive_results(results, metrics, elapsed_time, dataset_stats, cache_hits, self.token_stats)
            self.save_comprehensive_results(results, metrics, elapsed_time, dataset_stats, cache_hits, self.token_stats) 
            
            return {
                "results": results,
                "metrics": metrics,
                "dataset_statistics": dataset_stats,
                "cache_statistics": cache_hits,
                "elapsed_time": elapsed_time,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"❌ Cache-based detection execution failed: {e}")
            return {"error": str(e), "success": False}
    
    
    def _detect_sample_with_cache_tracking(self, sample: Dict, idx: int):
        max_retries = 2
        for attempt in range(max_retries):
            try:
                initial_cache = self.detector.knowledge_cache.get_cache_statistics()
                
                result = self.detector.detect_single_sample(sample)
                
                final_cache = self.detector.knowledge_cache.get_cache_statistics()
                
                cache_hits = {
                    "vulspec": 0 if final_cache['vulspec_cache_size'] > initial_cache['vulspec_cache_size'] else 1,
                    "nvd": 0 if final_cache['nvd_cache_size'] > initial_cache['nvd_cache_size'] else 1,
                    "spec": 0 if final_cache['spec_cache_size'] > initial_cache['spec_cache_size'] else 1
                }
                
                return result, cache_hits
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.logger.warning(f"⚠️  Sample {idx + 1} detection failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(1 * attempt)
        
        return self._create_error_result(sample, "Max retries exceeded"), {"vulspec": 0, "nvd": 0, "spec": 0}
    
    def _create_error_result(self, sample: Dict, error: str) -> Dict:
        return {
            "sample_id": sample.get("sample_id", "unknown"),
            "cve_id": sample.get("cve_id", ""),
            "true_label": sample.get("true_label", 0),
            "code_type": sample.get("code_type", ""),
            "data_source": sample.get("data_source", ""),
            "prediction": 0,
            "confidence": 0.0,
            "reasoning": f"Detection failed: {error}",
            "match_prediction": "ERROR",
            "success": False,
            "error": error,
            "detector_type": "VulInstructTwoStageDetector",
            "stage1_vulnerability_detection": {
                "vulnerability_prediction": 0,
                "confidence": 0.0,
                "reasoning": f"Detection failed: {error}"
            },
            "stage2_match_prediction": {
                "match_result": "ERROR",
                "match_confidence": 0.0,
                "match_reasoning": f"Detection failed: {error}"
            }
        }
    
    def _calculate_realtime_correct_metrics(self, results: List[Dict]) -> Dict:
        processed_samples = []
        
        for result in results:
            try:
                stage1_result = result.get("stage1_vulnerability_detection", {})
                stage2_result = result.get("stage2_match_prediction", {})
                
                sample_id = result.get("sample_id", "")
                cve_id = result.get("cve_id", "")
                code_type = result.get("code_type", "")
                true_label = 1 if code_type == "before" else 0
                
                prediction = stage1_result.get("vulnerability_prediction", result.get("prediction", 0))
                if isinstance(prediction, str):
                    prediction = 1 if prediction.upper() in ["TRUE", "YES"] else 0
                elif isinstance(prediction, bool):
                    prediction = 1 if prediction else 0
                
                original_stage2_result = stage2_result.get("match_result", result.get("match_prediction", ""))
                reasoning = stage2_result.get("match_reasoning", "") or stage2_result.get("raw_response", "")
                fixed_stage2_result = self._extract_stage2_conclusion_from_reasoning(
                    reasoning, original_stage2_result, code_type, prediction
                )
                
                sample = {
                    "sample_id": sample_id,
                    "cve_id": cve_id,
                    "code_type": code_type,
                    "true_label": true_label,
                    "prediction": prediction,
                    "confidence": stage1_result.get("confidence", 0.0),
                    "reasoning": stage1_result.get("reasoning", ""),
                    "stage2_match_result": fixed_stage2_result,
                    "stage2_match_confidence": stage2_result.get("match_confidence", 0.0),
                    "stage2_match_reasoning": reasoning,
                    "stage2_evaluation_success": True
                }
                processed_samples.append(sample)
                
            except Exception as e:
                continue
        
        if not processed_samples:
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0}
        
        return self._calculate_correct_based_metrics_core(processed_samples)
    
    def _extract_stage2_conclusion_from_reasoning(self, reasoning_text, original_result, code_type, stage1_prediction):
        if original_result in ['MATCH', 'MISMATCH', 'CORRECT', 'FALSE_ALARM']:
            return original_result
        
        if original_result == 'N/A':
            if code_type == "before":
                return 'MISMATCH' if stage1_prediction == 0 else 'N/A'
            else:
                return 'CORRECT' if stage1_prediction == 0 else 'N/A'
        
        if original_result not in ['THE', 'WHILE', 'IS']:
            return original_result
        
        if not reasoning_text:
            return 'MISMATCH' if code_type == "before" else 'CORRECT'
        
        reasoning_upper = reasoning_text.upper()
        
        if code_type == "before":
            priority_order = ['MISMATCH', 'MATCH']
        else:
            priority_order = ['FALSE_ALARM', 'CORRECT']
        
        for keyword in priority_order:
            if keyword in reasoning_upper:
                return keyword
        
        return 'MISMATCH' if code_type == "before" else 'CORRECT'
    
    def _calculate_correct_based_metrics_core(self, samples: List[Dict]) -> Dict:
        new_tp = new_fp = new_tn = new_fn = 0
        
        for sample in samples:
            true_label = sample["true_label"]
            prediction = sample["prediction"]
            stage2_result = sample["stage2_match_result"]
            
            if true_label == 1:
                if prediction == 1:
                    if stage2_result == "MATCH":
                        new_tp += 1
                    else:
                        new_fn += 1
                else:
                    new_fn += 1
            else:
                if prediction == 0:
                    new_tn += 1
                else:
                    if stage2_result == "FALSE_ALARM":
                        new_fp += 1
                    else:
                        new_tn += 1
        
        total = new_tp + new_fp + new_tn + new_fn
        accuracy = (new_tp + new_tn) / total if total > 0 else 0
        precision = new_tp / (new_tp + new_fp) if (new_tp + new_fp) > 0 else 0
        recall = new_tp / (new_tp + new_fn) if (new_tp + new_fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1_score, 4),
            "confusion_matrix": {"tp": new_tp, "fp": new_fp, "tn": new_tn, "fn": new_fn, "total": total}
        }
    
    def _display_realtime_metrics(self, current_count: int, metrics: Dict, cache_hits: Dict):
        self.logger.info("\n" + "="*80)
        self.logger.info(f"📊 Real-time CORRECT-based metrics ({current_count} samples)")
        self.logger.info("="*80)
        self.logger.info(f"   accuracy (Accuracy): {metrics['accuracy']:.1%}")
        self.logger.info(f"   precision (Precision): {metrics['precision']:.1%}")
        self.logger.info(f"   recall (Recall): {metrics['recall']:.1%}")
        self.logger.info(f"   F1 score (F1-Score): {metrics['f1_score']:.1%}")
        
        cm = metrics.get('confusion_matrix', {})
        if cm:
            self.logger.info(f"  TP={cm.get('tp', 0)}, FP={cm.get('fp', 0)}, TN={cm.get('tn', 0)}, FN={cm.get('fn', 0)}")
        
        total_cache_hits = sum(cache_hits.values())
        total_cache_opportunities = current_count * 3
        cache_hit_rate = total_cache_hits / total_cache_opportunities if total_cache_opportunities > 0 else 0
        self.logger.info(f"   cache hit: {cache_hit_rate:.1%} ({total_cache_hits}/{total_cache_opportunities})")
        if token_stats["total_samples"] > 0:
            avg_tokens = token_stats["total_tokens"] / token_stats["total_samples"]
            self.logger.info(f"\n💰 Token Usage (current):")
            self.logger.info(f"   Total Tokens: {token_stats['total_tokens']:,.0f}")
            self.logger.info(f"   Avg Tokens/Sample: {avg_tokens:.1f}")
            self.logger.info(f"   Samples Counted: {token_stats['total_samples']}")
        self.logger.info("="*80 + "\n")
    
    def calculate_comprehensive_metrics(self, results: List[Dict]) -> Dict:
        true_pos = sum(1 for r in results if r.get("true_label") == 1 and r.get("prediction") == 1)
        false_pos = sum(1 for r in results if r.get("true_label") == 0 and r.get("prediction") == 1)
        true_neg = sum(1 for r in results if r.get("true_label") == 0 and r.get("prediction") == 0)
        false_neg = sum(1 for r in results if r.get("true_label") == 1 and r.get("prediction") == 0)
        
        total = len(results)
        total_vulnerabilities = true_pos + false_neg
        predicted_vulnerabilities = true_pos + false_pos
        
        accuracy = (true_pos + true_neg) / total if total > 0 else 0
        precision = true_pos / predicted_vulnerabilities if predicted_vulnerabilities > 0 else 0
        recall = true_pos / total_vulnerabilities if total_vulnerabilities > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        before_vuln_samples = [r for r in results if r.get("code_type") == "before" and r.get("true_label") == 1]
        before_predicted_vuln = [r for r in before_vuln_samples if r.get("prediction") == 1]
        before_match = sum(1 for r in before_predicted_vuln if r.get("match_prediction") == "MATCH")
        
        total_vuln_before = len(before_vuln_samples)
        correct_match_rate = before_match / total_vuln_before if total_vuln_before > 0 else 0
        
        successful_detections = sum(1 for r in results if r.get("success", False))
        
        return {
            "basic_performance": {
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1_score, 4)
            },
            "confusion_matrix": {
                "true_positive": true_pos,
                "false_positive": false_pos,
                "true_negative": true_neg,
                "false_negative": false_neg,
                "total_samples": total,
                "total_vulnerabilities": total_vulnerabilities,
                "predicted_vulnerabilities": predicted_vulnerabilities
            },
            "match_analysis": {
                "total_vuln_before_samples": total_vuln_before,
                "predicted_vuln_before_samples": len(before_predicted_vuln),
                "before_match_count": before_match,
                "correct_match_rate": round(correct_match_rate, 4),
                "match_rate_percentage": f"{correct_match_rate * 100:.1f}%"
            },
            "detection_statistics": {
                "successful_detection_count": successful_detections,
                "success_rate": round(successful_detections / total, 4) if total > 0 else 0
            }
        }
    def print_comprehensive_results(self, results: List[Dict], metrics: Dict, 
                               elapsed_time: float, dataset_stats: Dict, cache_hits: Dict, token_stats: Dict):
        self.logger.info("=" * 100)
        self.logger.info("📊 Cache-based vulnerability detection results")
        self.logger.info("=" * 100)
        
        basic = metrics["basic_performance"]
        self.logger.info(f"📈:")
        self.logger.info(f"   accuracy (Accuracy): {basic['accuracy']:.4f}")
        self.logger.info(f"   precision (Precision): {basic['precision']:.4f}")
        self.logger.info(f"   recall (Recall): {basic['recall']:.4f}")
        self.logger.info(f"   F1 score (F1-Score): {basic['f1_score']:.4f}")
        
        match = metrics["match_analysis"]
        self.logger.info(f"\n🎯 MATCH analysis:")
        self.logger.info(f"   vulnerability before samples: {match['total_vuln_before_samples']}")
        self.logger.info(f"   MATCH: {match['correct_match_rate']:.4f} ({match['match_rate_percentage']})")
        
        total_samples = len(results)
        total_cache_opportunities = total_samples * 3
        total_cache_hits = sum(cache_hits.values())
        cache_hit_rate = total_cache_hits / total_cache_opportunities if total_cache_opportunities > 0 else 0
        
        self.logger.info(f"\n💾 Cache effectiveness analysis:")
        self.logger.info(f"   VulSpec cache hits: {cache_hits['vulspec']} times")
        self.logger.info(f"   NVD cache hits: {cache_hits['nvd']} times")
        self.logger.info(f"   Spec cache hits: {cache_hits['spec']} times")
        self.logger.info(f"   Total cache hits: {total_cache_hits} times")
        self.logger.info(f"   Cache hit rate: {cache_hit_rate:.1%}")

        self.logger.info("\n" + "="*100)
        self.logger.info("💰 Token Usage Statistics (Final)")
        self.logger.info("="*100)

        if token_stats["total_samples"] > 0:
            avg_tokens = token_stats["total_tokens"] / token_stats["total_samples"]
            sample_tokens = token_stats["sample_tokens"]
    
        self.logger.info(f"   Total Tokens Consumed: {token_stats['total_tokens']:,.0f}")
        self.logger.info(f"   Total Samples Processed: {token_stats['total_samples']}")
        self.logger.info(f"   Average Tokens per Sample: {avg_tokens:.1f}")
    
        if sample_tokens:
            import numpy as np
            self.logger.info(f"   Min Tokens/Sample: {min(sample_tokens):.0f}")
            self.logger.info(f"   Max Tokens/Sample: {max(sample_tokens):.0f}")
            self.logger.info(f"   Median Tokens/Sample: {np.median(sample_tokens):.1f}")
            self.logger.info(f"   Std Dev: {np.std(sample_tokens):.1f}")
        else:
             self.logger.info("   ⚠️  No token statistics available")
        self.logger.info("="*100 + "\n")
        
     

    
    def save_comprehensive_results(
        self,
        results: List[Dict],
        metrics: Dict,
        elapsed_time: float,
        dataset_stats: Dict,
        cache_hits: Dict,
        token_stats: Dict
    ):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"cached_detection_results_{timestamp}.json"

        token_summary = {}

        if token_stats.get("total_samples", 0) > 0:
            total_tokens = token_stats["total_tokens"]
            total_samples = token_stats["total_samples"]
            sample_tokens = token_stats.get("sample_tokens", [])

            avg_tokens = total_tokens / total_samples

            token_summary = {
                "total_tokens": total_tokens,
                "total_samples_with_token_data": total_samples,
                "avg_tokens_per_sample": round(avg_tokens, 2),
                "min_tokens": min(sample_tokens) if sample_tokens else 0,
                "max_tokens": max(sample_tokens) if sample_tokens else 0,
            }
        full_results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "detector_version": "VulInstructTwoStageDetector_Cached",
            "test_samples": len(results),
            "model_name": self.model_name,
            "model_eval_name": self.model_eval_name,
            "model_score_name": f"{self.model_score_name} (cached)",
            "elapsed_time": elapsed_time,
        },
        "dataset_statistics": dataset_stats,
        "cache_statistics": cache_hits,
        "token_statistics": token_summary,
        "metrics": metrics,
        "detailed_results": results
        }
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(full_results, f, ensure_ascii=False, indent=2)
            self.logger.info(f"💾 Results saved: {results_file}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save results: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Cache-based detection runner")
    parser.add_argument("--workers", type=int, default=20, help="Number of concurrent workers")
    parser.add_argument("--samples", type=int, default=900, help="Limit on number of test samples (default uses full dataset)")
    parser.add_argument("--model-name", type=str, default="gpt-4o", help="Main detection model name")
    parser.add_argument("--model-eval-name", type=str, default="gpt-5", help="Evaluation model name")
    parser.add_argument("--model-score-name", type=str, default="deepseek-v3", help="Scoring model name (uses cache)")
    parser.add_argument("--vulspec-threshold", type=float, default=6, help="VulSpec knowledge threshold value")
    parser.add_argument("--nvd-threshold", type=float, default=6, help="NVD knowledge threshold value")
    parser.add_argument("--spec-threshold", type=float, default=6, help="Spec threshold value")
    parser.add_argument("--no-code-context", action="store_true", help="Disable code context (default enabled)")
    

    args = parser.parse_args()
    
    try:
        runner = CachedDetectionRunner(
            max_workers=args.workers,
            test_samples=args.samples,
            model_name=args.model_name,
            model_eval_name=args.model_eval_name,
            model_score_name=args.model_score_name,
            vulspec_threshold=args.vulspec_threshold,
            nvd_threshold=args.nvd_threshold,
            spec_threshold=args.spec_threshold,
            use_code_context=not args.no_code_context
        )
        
        runner.run_cached_detection()
    
    
    except Exception as e:
        print(f"❌ {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()