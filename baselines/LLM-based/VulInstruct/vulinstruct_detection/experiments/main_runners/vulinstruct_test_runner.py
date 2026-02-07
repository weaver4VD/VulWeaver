
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
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_manager import APIManager
from core.detectors.vulinstruct_two_stage_detector import VulInstructTwoStageDetector
from core.data_loaders.vulinstruct_dataset_loader import VulInstructDatasetLoader

class VulInstructTestRunner:
    
    def __init__(self, max_workers: int = 30, test_samples: Optional[int] = None, 
                 model_name: str = "gpt-4o", model_eval_name: str = "gpt-5", model_score_name: str = "deepseek-v3",
                 vulspec_threshold: float = 0.7, nvd_threshold: float = 0.7, 
                 spec_threshold: float = 0.7, use_code_context: bool = True):
        self.max_workers = max_workers
        self.test_samples = test_samples
        self.api_manager = APIManager()
        self.model_name = model_name
        self.model_eval_name = model_eval_name
        self.vulspec_threshold = vulspec_threshold
        self.nvd_threshold = nvd_threshold
        self.spec_threshold = spec_threshold
        self.use_code_context = use_code_context
        self.model_score_name = model_score_name
        self.detector = VulInstructTwoStageDetector(
            self.api_manager, 
            model_name=self.model_name, 
            model_eval_name=self.model_eval_name,
            model_score_name = self.model_score_name, 
            vulspec_threshold=self.vulspec_threshold, 
            nvd_threshold=self.nvd_threshold, 
            spec_threshold=self.spec_threshold,
            use_code_context=self.use_code_context
        )
        self.data_loader = VulInstructDatasetLoader()
        
        self.setup_logging()
        
        total_samples_desc = "complete 419-pair dataset" if test_samples is None else f"{test_samples} samples subset"
        
        self.logger.info(f"🚀 VulInstruct two-stage detector complete dataset testing runner initialized successfully")
        self.logger.info(f"   Concurrent workers: {max_workers}")
        self.logger.info(f"   Testing scale: {total_samples_desc}")
        self.logger.info(f"   Main detection model: {self.model_name}")
        self.logger.info(f"   Evaluation model: {self.model_eval_name}")
        self.logger.info(f"   VulSpec threshold: {self.vulspec_threshold}")
        self.logger.info(f"   NVD threshold: {self.nvd_threshold}")
        self.logger.info(f"   Specification threshold: {self.spec_threshold}")
        self.logger.info("   VulInstruct objectives: complete dataset validation + inherited optimizations + system scalability")
    
    def setup_logging(self):
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_filename = f"two_stage_v15_full_dataset_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
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
    
    def run_test(self) -> Dict:
        self.logger.info("=" * 100)
        self.logger.info("🚀 Starting VulInstruct complete dataset vulnerability detection testing")
        self.logger.info("=" * 100)
        
        start_time = time.time()
        
        try:
            self.logger.info("📊 Loading VulInstruct complete dataset...")
            samples = self.data_loader.load_full_detection_samples(limit=self.test_samples)
            
            if not samples:
                self.logger.error("❌ No valid samples loaded")
                return {"error": "No valid samples loaded"}
            
            dataset_stats = self.data_loader.get_dataset_statistics()
            self._print_dataset_statistics(dataset_stats)
            
            actual_samples = len(samples)
            self.logger.info(f"🤖 Starting two-stage detection (concurrency: {self.max_workers}, samples: {actual_samples})")
            
            results = []
            progress_bar = tqdm(
                total=actual_samples, 
                desc="🚀 VulInstruct vulnerability detection progress", 
                unit="samples",
                position=0,
                leave=True,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}"
            )
            
            completed_samples = 0
            intermediate_stats = {"success": 0, "error": 0, "vulnerable_detected": 0}
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_sample = {
                    executor.submit(self._detect_sample_with_retry, sample, i): (sample, i)
                    for i, sample in enumerate(samples)
                }
                
                for future in concurrent.futures.as_completed(future_to_sample):
                    sample, idx = future_to_sample[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        completed_samples += 1
                        if result.get("success", False):
                            intermediate_stats["success"] += 1
                        else:
                            intermediate_stats["error"] += 1
                        if result.get("prediction") == 1:
                            intermediate_stats["vulnerable_detected"] += 1
                        
                        success_rate = intermediate_stats["success"] / completed_samples * 100
                        vuln_rate = intermediate_stats["vulnerable_detected"] / completed_samples * 100
                        progress_bar.set_postfix({
                            "Success rate": f"{success_rate:.1f}%",
                            "Vulnerability detection rate": f"{vuln_rate:.1f}%",
                            "error": intermediate_stats["error"]
                        })
                        progress_bar.update(1)
                        
                        if completed_samples % 100 == 0:
                            current_accuracy = self._calculate_intermediate_accuracy(results)
                            self.logger.info(f"📊 Intermediate evaluation ({completed_samples}/{actual_samples}): "
                                           f"accuracy={current_accuracy:.3f}, "
                                           f"success rate={success_rate:.1f}%, "
                                           f"vulnerability detection rate={vuln_rate:.1f}%")
                            
                    except Exception as e:
                        self.logger.error(f"❌ Detection failed - sample {idx + 1}: {e}")
                        error_result = self._create_error_result(sample, str(e))
                        results.append(error_result)
                        
                        completed_samples += 1
                        intermediate_stats["error"] += 1
                        success_rate = intermediate_stats["success"] / completed_samples * 100
                        vuln_rate = intermediate_stats["vulnerable_detected"] / completed_samples * 100
                        progress_bar.set_postfix({
                            "Success rate": f"{success_rate:.1f}%",
                            "Vulnerability detection rate": f"{vuln_rate:.1f}%",
                            "error": intermediate_stats["error"]
                        })
                        progress_bar.update(1)
            
            progress_bar.close()
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"⏰ VulInstruct complete dataset detection completed, time elapsed: {elapsed_time:.2f} seconds")
            
            metrics = self.calculate_comprehensive_metrics(results)
            self.print_comprehensive_results(results, metrics, elapsed_time, dataset_stats)
            self.analyze_v15_full_dataset_performance(results, metrics)
            
            self.save_comprehensive_results(results, metrics, elapsed_time, dataset_stats)
            
            return {
                "results": results,
                "metrics": metrics,
                "dataset_statistics": dataset_stats,
                "elapsed_time": elapsed_time,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"❌ VulInstruct complete dataset testing execution failed: {e}")
            return {"error": str(e), "success": False}
    
    def _print_dataset_statistics(self, dataset_stats: Dict):
        self.logger.info("📊 VulInstruct complete dataset statistics info:")
        self.logger.info(f"   Dataset version: {dataset_stats['dataset_version']}")
        self.logger.info(f"   Total samples: {dataset_stats['total_samples']}")
        self.logger.info(f"   Unique CVEs: {dataset_stats['unique_cves']}")
        self.logger.info(f"   Before samples: {dataset_stats['before_samples']}")
        self.logger.info(f"   After samples: {dataset_stats['after_samples']}")
        
        source_dist = dataset_stats['data_source_distribution']
        self.logger.info(f"   Data source distribution:")
        self.logger.info(f"     exclude_100: {source_dist['exclude_100']} samples")
        self.logger.info(f"     subset_100: {source_dist['subset_100']} samples")
        
        knowledge_cov = dataset_stats['knowledge_coverage']
        self.logger.info(f"   Knowledge coverage:")
        self.logger.info(f"     VulSpec coverage: {knowledge_cov['vulspec_covered']} samples ({knowledge_cov['vulspec_coverage_rate']:.1%})")
        self.logger.info(f"     NVD coverage: {knowledge_cov['nvd_covered']} samples ({knowledge_cov['nvd_coverage_rate']:.1%})")
        self.logger.info(f"     Ground Truth coverage: {knowledge_cov['ground_truth_covered']} samples ({knowledge_cov['ground_truth_coverage_rate']:.1%})")
    
    def _detect_sample_with_retry(self, sample: Dict, idx: int) -> Dict:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                result = self.detector.detect_single_sample(sample)
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.logger.warning(f"⚠️  Sample {idx + 1} detection failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(1 * attempt)
        
        return self._create_error_result(sample, "Max retries exceeded")
    
    def _calculate_intermediate_accuracy(self, current_results: List[Dict]) -> float:
        if not current_results:
            return 0.0
        
        correct_predictions = sum(
            1 for r in current_results 
            if r.get("true_label") == r.get("prediction")
        )
        return correct_predictions / len(current_results)
    
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
            "detector_type": "VulInstructTwoStageDetector"
        }
    
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
        
        full_dataset_applied = sum(1 for r in results if r.get("v15_full_dataset_applied", False))
        successful_detections = sum(1 for r in results if r.get("success", False))
        
        exclude_100_results = [r for r in results if r.get("data_source") == "exclude_100"]
        subset_100_results = [r for r in results if r.get("data_source") == "subset_100"]
        
        strategy_stats = {}
        selected_knowledge_counts = []
        
        for result in results:
            v14_scoring = result.get("v14_llm_knowledge_scoring", {})
            strategy = v14_scoring.get("evaluation_strategy", "unknown")
            strategy_stats[strategy] = strategy_stats.get(strategy, 0) + 1
            
            selected_count = v14_scoring.get("selected_total_count", 0)
            selected_knowledge_counts.append(selected_count)
        
        avg_selected_knowledge = sum(selected_knowledge_counts) / len(selected_knowledge_counts) if selected_knowledge_counts else 0
        
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
            "v15_full_dataset_statistics": {
                "full_dataset_applied_count": full_dataset_applied,
                "full_dataset_applied_rate": round(full_dataset_applied / total, 4) if total > 0 else 0,
                "successful_detection_count": successful_detections,
                "success_rate": round(successful_detections / total, 4) if total > 0 else 0,
                "avg_selected_knowledge_count": round(avg_selected_knowledge, 2),
                "knowledge_selection_strategies": strategy_stats,
                "data_source_performance": {
                    "exclude_100": {
                        "samples": len(exclude_100_results),
                        "accuracy": sum(1 for r in exclude_100_results if r.get("true_label") == r.get("prediction")) / len(exclude_100_results) if exclude_100_results else 0
                    },
                    "subset_100": {
                        "samples": len(subset_100_results),
                        "accuracy": sum(1 for r in subset_100_results if r.get("true_label") == r.get("prediction")) / len(subset_100_results) if subset_100_results else 0
                    }
                }
            }
        }
    
    def print_comprehensive_results(self, results: List[Dict], metrics: Dict, 
                                   elapsed_time: float, dataset_stats: Dict):
        self.logger.info("=" * 100)
        self.logger.info("📊 VulInstruct complete dataset vulnerability detection testing results")
        self.logger.info("=" * 100)
        
        basic = metrics["basic_performance"]
        self.logger.info(f"📈 Basic performance metrics:")
        self.logger.info(f"   Accuracy: {basic['accuracy']:.4f}")
        self.logger.info(f"   Precision: {basic['precision']:.4f}")
        self.logger.info(f"   Recall: {basic['recall']:.4f}")
        self.logger.info(f"   F1 Score: {basic['f1_score']:.4f}")
        
        cm = metrics["confusion_matrix"]
        self.logger.info(f"\n📋 Confusion Matrix:")
        self.logger.info(f"   True Positive (TP): {cm['true_positive']}")
        self.logger.info(f"   False Positive (FP): {cm['false_positive']}")
        self.logger.info(f"   True Negative (TN): {cm['true_negative']}")
        self.logger.info(f"   False Negative (FN): {cm['false_negative']}")
        self.logger.info(f"   Total samples: {cm['total_samples']}")
        self.logger.info(f"   Total vulnerability samples: {cm['total_vulnerabilities']}")
        
        match = metrics["match_analysis"]
        self.logger.info(f"\n🎯 MATCH analysis (VulInstruct core metrics):")
        self.logger.info(f"   True vulnerability before samples: {match['total_vuln_before_samples']}")
        self.logger.info(f"   Predicted vulnerability before samples: {match['predicted_vuln_before_samples']}")
        self.logger.info(f"   MATCH successful count: {match['before_match_count']}")
        self.logger.info(f"   Correct MATCH rate: {match['correct_match_rate']:.4f} ({match['match_rate_percentage']})")
        
        v15 = metrics["v15_full_dataset_statistics"]
        self.logger.info(f"\n🚀 VulInstruct complete dataset statistics:")
        self.logger.info(f"   Complete dataset applied count: {v15['full_dataset_applied_count']}")
        self.logger.info(f"   Complete dataset applied rate: {v15['full_dataset_applied_rate']:.4f}")
        self.logger.info(f"   Successful detection count: {v15['successful_detection_count']}")
        self.logger.info(f"   Successful detection rate: {v15['success_rate']:.4f}")
        self.logger.info(f"   Average selected knowledge count: {v15['avg_selected_knowledge_count']}")
        
        source_perf = v15["data_source_performance"]
        self.logger.info(f"\n📊 Data source performance comparison:")
        self.logger.info(f"   exclude_100 (319 pairs): {source_perf['exclude_100']['samples']} samples, accuracy {source_perf['exclude_100']['accuracy']:.3f}")
        self.logger.info(f"   subset_100 (100 pairs): {source_perf['subset_100']['samples']} samples, accuracy {source_perf['subset_100']['accuracy']:.3f}")
        
        for strategy, count in v15["knowledge_selection_strategies"].items():
            percentage = (count / cm['total_samples']) * 100 if cm['total_samples'] > 0 else 0
            self.logger.info(f"   {strategy}: {count} samples ({percentage:.1f}%)")
        
       
    def analyze_v15_full_dataset_performance(self, results: List[Dict], metrics: Dict):

        
        for data_source in ["exclude_100", "subset_100"]:
            source_results = [r for r in results if r.get("data_source") == data_source]
            if not source_results:
                continue
            
            source_accuracy = sum(1 for r in source_results if r.get("true_label") == r.get("prediction")) / len(source_results)
            
            source_vuln_before = [r for r in source_results if r.get("code_type") == "before" and r.get("true_label") == 1]
            source_predicted_vuln = [r for r in source_vuln_before if r.get("prediction") == 1]
            source_match = sum(1 for r in source_predicted_vuln if r.get("match_prediction") == "MATCH")
            source_match_rate = source_match / len(source_vuln_before) if source_vuln_before else 0
            
        
        
        strategy_performance = {}
        for strategy, count in metrics["v15_full_dataset_statistics"]["knowledge_selection_strategies"].items():
            strategy_samples = [r for r in results 
                              if r.get("v14_llm_knowledge_scoring", {}).get("evaluation_strategy") == strategy]
            
            if strategy_samples:
                strategy_accuracy = sum(1 for r in strategy_samples if r.get("true_label") == r.get("prediction")) / len(strategy_samples)
                
                strategy_vuln_before = [r for r in strategy_samples 
                                      if r.get("code_type") == "before" and r.get("true_label") == 1]
                strategy_predicted_vuln = [r for r in strategy_vuln_before if r.get("prediction") == 1]
                strategy_match = sum(1 for r in strategy_predicted_vuln if r.get("match_prediction") == "MATCH")
                strategy_match_rate = strategy_match / len(strategy_vuln_before) if strategy_vuln_before else 0
                
                self.logger.info(f"\n   Strategy: {strategy}")
                self.logger.info(f"     Sample count: {len(strategy_samples)}")
                self.logger.info(f"     accuracy: {strategy_accuracy:.3f}")
                self.logger.info(f"     Vulnerability sample count: {len(strategy_vuln_before)}")
                self.logger.info(f"     MATCH rate: {strategy_match_rate:.3f} ({strategy_match_rate*100:.1f}%)")
        
    
    def save_comprehensive_results(self, results: List[Dict], metrics: Dict, 
                                  elapsed_time: float, dataset_stats: Dict):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results_file = f"two_stage_v15_full_dataset_results_{timestamp}.json"
        full_results = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "detector_version": "VulInstructTwoStageDetector", 
                "test_samples": len(results),
                "model_name": self.model_name,
                "model_eval_name": self.model_eval_name,
                "elapsed_time": elapsed_time,
            },
            "dataset_statistics": dataset_stats,
            "metrics": metrics,
            "detailed_results": results
        }
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(full_results, f, ensure_ascii=False, indent=2)
            self.logger.info(f"💾 Results saved: {results_file}")
        except Exception as e:
            self.logger.error(f"❌ Save results failed: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="V15 complete dataset testing")
    parser.add_argument("--workers", type=int, default=25, help="Number of concurrent workers")
    parser.add_argument("--samples", type=int, default=50, help="Testing sample quantity limit (default uses complete dataset)")
    parser.add_argument("--model-name", type=str, default="deepseek-v3", help="Main detection model name")
    parser.add_argument("--model-eval-name", type=str, default="gpt-5", help="Evaluation model name")
    parser.add_argument("--model-score-name", type=str, default="deepseek-v3", help="Scoring model name")
    parser.add_argument("--vulspec-threshold", type=float, default=11, help="VulSpec knowledge threshold value")
    parser.add_argument("--nvd-threshold", type=float, default=7, help="NVD knowledge threshold value")
    parser.add_argument("--spec-threshold", type=float, default=7, help="Specification threshold value")
    parser.add_argument("--no-code-context", action="store_true", help="Disable code context (default enabled)")
    
    args = parser.parse_args()
    
    try:
        runner = VulInstructTestRunner(
            max_workers=args.workers, 
            test_samples=args.samples,
            model_name=args.model_name,
            model_eval_name=args.model_eval_name,
            vulspec_threshold=args.vulspec_threshold,
            nvd_threshold=args.nvd_threshold,
            spec_threshold=args.spec_threshold,
            use_code_context=not args.no_code_context
        )
       
    except Exception as e:
        print(f"❌ V15 complete dataset testing execution error: {e}")

if __name__ == "__main__":
    main()