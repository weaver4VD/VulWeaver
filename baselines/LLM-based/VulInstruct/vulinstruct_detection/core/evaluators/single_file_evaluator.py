
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import argparse

class SingleFileEvaluator:
    def __init__(self, vulinstruct_file):
        self.vulinstruct_file = vulinstruct_file
        
    def process_vulinstruct_data(self):
        print(f"🔍 Loading VulInstruct file: {self.vulinstruct_file}")
        
        try:
            with open(self.vulinstruct_file, 'r', encoding='utf-8') as f:
                vulinstruct_data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load VulInstruct data: {e}")
            return []
        
        samples = []
        processed_count = 0
        
        for result in vulinstruct_data.get('detailed_results', []):
            try:
                stage1_result = result.get("stage1_vulnerability_detection", {})
                stage2_result = result.get("stage2_match_prediction", {})
                
                sample_id = result.get("sample_id", "")
                cve_id = result.get("cve_id", "")
                code_type = result.get("code_type", "")
                true_label = 1 if code_type == "before" else 0
                
                prediction = stage1_result.get("vulnerability_prediction", 0)
                if isinstance(prediction, str):
                    prediction = 1 if prediction.upper() in ["TRUE", "YES"] else 0
                elif isinstance(prediction, bool):
                    prediction = 1 if prediction else 0
                
                original_stage2_result = stage2_result.get("match_result", "")
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
                    "stage2_evaluation_success": True,
                    "original_result": result
                }
                samples.append(sample)
                processed_count += 1
                
            except Exception as e:
                print(f"⚠️ Error processing sample: {e}")
                continue
        
        print(f"✅ Successfully processed {processed_count} samples")
        return samples
    
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
    
    def _calculate_basic_metrics(self, samples):
        tp = fp = tn = fn = 0
        
        for sample in samples:
            true_label = sample["true_label"]
            prediction = sample["prediction"]
            
            if true_label == 1 and prediction == 1:
                tp += 1
            elif true_label == 0 and prediction == 1:
                fp += 1
            elif true_label == 0 and prediction == 0:
                tn += 1
            elif true_label == 1 and prediction == 0:
                fn += 1
        
        total = tp + fp + tn + fn
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "total": total},
            "metrics": {
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4), 
                "f1_score": round(f1_score, 4)
            }
        }
    
    def _calculate_correct_based_metrics(self, samples):
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
            "confusion_matrix": {"tp": new_tp, "fp": new_fp, "tn": new_tn, "fn": new_fn, "total": total},
            "metrics": {
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1_score, 4)
            }
        }
    
    def _analyze_cve_pairs(self, samples):
        cve_groups = defaultdict(list)
        for sample in samples:
            cve_id = sample["cve_id"]
            if cve_id:
                cve_groups[cve_id].append(sample)
        
        valid_pairs = []
        for cve_id, group_samples in cve_groups.items():
            before_sample = next((s for s in group_samples if s["code_type"] == "before"), None)
            after_sample = next((s for s in group_samples if s["code_type"] == "after"), None)
            
            if before_sample and after_sample:
                valid_pairs.append((cve_id, before_sample, after_sample))
        
        total_pairs = len(valid_pairs)
        
        stage1_patterns = {
            "p-c": 0,
            "p-v": 0,
            "p-b": 0,
            "p-r": 0
        }
        
        correct_patterns = {
            "both_correct": 0,
            "before_correct_after_wrong": 0,
            "before_wrong_after_correct": 0,
            "both_wrong": 0
        }
        
        for cve_id, before_sample, after_sample in valid_pairs:
            before_pred = before_sample["prediction"] 
            after_pred = after_sample["prediction"]
            
            if before_pred == 1 and after_pred == 0:
                stage1_patterns["p-c"] += 1
            elif before_pred == 1 and after_pred == 1:
                stage1_patterns["p-v"] += 1
            elif before_pred == 0 and after_pred == 0:
                stage1_patterns["p-b"] += 1
            else:
                stage1_patterns["p-r"] += 1
            
            if before_pred == 1 and before_sample["stage2_match_result"] == "MATCH":
                before_class = "TP"
            else:
                before_class = "FN"
            
            if after_pred == 0:
                after_class = "TN"
            elif after_pred == 1 and after_sample["stage2_match_result"] == "FALSE_ALARM":
                after_class = "FP"
            else:
                after_class = "TN"
            
            if before_class == "TP" and after_class == "TN":
                correct_patterns["both_correct"] += 1
            elif before_class == "TP" and after_class == "FP":
                correct_patterns["before_correct_after_wrong"] += 1
            elif before_class == "FN" and after_class == "TN":
                correct_patterns["before_wrong_after_correct"] += 1
            else:
                correct_patterns["both_wrong"] += 1
        
        return {
            "total_pairs": total_pairs,
            "stage1_patterns": stage1_patterns,
            "stage1_percentages": {k: round(v/total_pairs*100, 1) if total_pairs > 0 else 0 for k, v in stage1_patterns.items()},
            "correct_patterns": correct_patterns,
            "correct_percentages": {k: round(v/total_pairs*100, 1) if total_pairs > 0 else 0 for k, v in correct_patterns.items()}
        }
    
    def run_single_file_evaluation(self):
        print("🚀 Starting single file VulInstruct evaluation...")
        print(f"📂 Target file: {Path(self.vulinstruct_file).name}")
        
        vulinstruct_samples = self.process_vulinstruct_data()
        if not vulinstruct_samples:
            print("❌ No valid sample data")
            return {}
        
        print(f"📊 Total samples: {len(vulinstruct_samples)}")
        
        print("\n🔍 Calculating evaluation metrics...")
        
        basic_metrics = self._calculate_basic_metrics(vulinstruct_samples)
        
        correct_metrics = self._calculate_correct_based_metrics(vulinstruct_samples)
        
        pair_analysis = self._analyze_cve_pairs(vulinstruct_samples)
        
        stage2_counts = defaultdict(int)
        for sample in vulinstruct_samples:
            stage2_result = sample.get("stage2_match_result", "N/A")
            stage2_counts[stage2_result] += 1
        
        evaluation_results = {
            "method_info": {
                "total_samples": len(vulinstruct_samples),
                "before_samples": len([s for s in vulinstruct_samples if s["code_type"] == "before"]),
                "after_samples": len([s for s in vulinstruct_samples if s["code_type"] == "after"]),
                "cve_pairs": pair_analysis["total_pairs"]
            },
            "basic_metrics": basic_metrics,
            "correct_metrics": correct_metrics,
            "pair_analysis": pair_analysis,
            "stage2_statistics": dict(stage2_counts),
            "source_file": self.vulinstruct_file
        }
        
        self._generate_single_file_report(evaluation_results)
        
        self._save_single_file_results(evaluation_results, vulinstruct_samples)
        
        return evaluation_results
    
    def _generate_single_file_report(self, result):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_filename = Path(self.vulinstruct_file).stem
        report_file = f"single_file_evaluation_report_{source_filename}_{timestamp}.md"
        
        info = result["method_info"]
        basic = result["basic_metrics"]["metrics"]
        correct = result["correct_metrics"]["metrics"]
        stage2 = result["stage2_statistics"]
        pairs = result["pair_analysis"]
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"**Generation Time**: {datetime.now().isoformat()}  \n")
            f.write(f"**Source File**: {Path(self.vulinstruct_file).name}  \n")
            f.write(f"**Evaluation Logic**: Strict evaluation framework based on CORRECT paper  \n")
            f.write("**Calculation Method**: Strictly consistent with complete evaluator\n\n")
            
            f.write(f"- **Total Samples**: {info['total_samples']}\n")
            f.write(f"- **Before Samples**: {info['before_samples']}\n")
            f.write(f"- **After Samples**: {info['after_samples']}\n")
            f.write(f"- **CVE Pairs**: {info['cve_pairs']}\n\n")
            
            stage2_str = ", ".join([f"{k}={v}" for k, v in stage2.items() if v > 0])
            f.write(f"- **Stage2 Statistics**: {stage2_str}\n\n")
            
            f.write(f"- **Accuracy**: {basic['accuracy']:.1%}\n")
            f.write(f"- **Precision**: {basic['precision']:.1%}\n")
            f.write(f"- **Recall**: {basic['recall']:.1%}\n")
            f.write(f"- **F1 Score**: {basic['f1_score']:.1%}\n\n")
            
            f.write(f"- **Accuracy**: {correct['accuracy']:.1%}\n")
            f.write(f"- **Precision**: {correct['precision']:.1%}\n")
            f.write(f"- **Recall**: {correct['recall']:.1%}\n")
            f.write(f"- **F1 Score**: {correct['f1_score']:.1%}\n\n")
            
            basic_cm = result["basic_metrics"]["confusion_matrix"]
            correct_cm = result["correct_metrics"]["confusion_matrix"]
            
            f.write(f"- **TP (True Positive)**: {basic_cm['tp']}\n")
            f.write(f"- **FP (False Positive)**: {basic_cm['fp']}\n")
            f.write(f"- **TN (True Negative)**: {basic_cm['tn']}\n")
            f.write(f"- **FN (False Negative)**: {basic_cm['fn']}\n\n")
            
            f.write(f"- **TP (True Positive)**: {correct_cm['tp']}\n")
            f.write(f"- **FP (False Positive)**: {correct_cm['fp']}\n")
            f.write(f"- **TN (True Negative)**: {correct_cm['tn']}\n")
            f.write(f"- **FN (False Negative)**: {correct_cm['fn']}\n\n")
            
            f.write(f"- **p-c (Ideal)**: {pairs['stage1_patterns']['p-c']} pairs ({pairs['stage1_percentages']['p-c']}%)\n")
            f.write(f"- **p-v (Both Vulnerable)**: {pairs['stage1_patterns']['p-v']} pairs ({pairs['stage1_percentages']['p-v']}%)\n")
            f.write(f"- **p-b (Both Benign)**: {pairs['stage1_patterns']['p-b']} pairs ({pairs['stage1_percentages']['p-b']}%)\n")
            f.write(f"- **p-r (Reversed)**: {pairs['stage1_patterns']['p-r']} pairs ({pairs['stage1_percentages']['p-r']}%)\n\n")
            
            cp = pairs["correct_patterns"]
            cpp = pairs["correct_percentages"]
            f.write(f"- **Perfect Case (Before=TP, After=TN)**: {cp['both_correct']} pairs ({cpp['both_correct']}%)\n")
            f.write(f"- **Before Correct After Wrong (Before=TP, After=FP)**: {cp['before_correct_after_wrong']} pairs ({cpp['before_correct_after_wrong']}%)\n")
            f.write(f"- **Before Wrong After Correct (Before=FN, After=TN)**: {cp['before_wrong_after_correct']} pairs ({cpp['before_wrong_after_correct']}%)\n")
            f.write(f"- **Both Wrong (Before=FN, After=FP)**: {cp['both_wrong']} pairs ({cpp['both_wrong']}%)\n\n")
            
            f.write(f"\n---\n*Single file evaluation report generated at: {datetime.now().isoformat()}*\n")
        
        print(f"\n📋 Evaluation report generated: {report_file}")
        
    def _save_single_file_results(self, evaluation_results, samples):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_filename = Path(self.vulinstruct_file).stem
        results_file = f"single_file_evaluation_results_{source_filename}_{timestamp}.json"
        
        output_data = {
            "metadata": {
                "generation_time": datetime.now().isoformat(),
                "description": "Single file VulInstruct evaluation results",
                "evaluation_method": "single_file_vulinstruct",
                "source_file": self.vulinstruct_file,
                "total_samples": len(samples),
                "total_pairs": evaluation_results["method_info"]["cve_pairs"]
            },
            "evaluation_results": evaluation_results,
            "detailed_samples": samples
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Evaluation results saved: {results_file}")


def main():
    parser = argparse.ArgumentParser(description="Single file VulInstruct evaluator")
    parser.add_argument("--file", type=str, required=True, help="VulInstruct results file path")
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"❌ File does not exist: {args.file}")
        return
    
    evaluator = SingleFileEvaluator(args.file)
    results = evaluator.run_single_file_evaluation()
    
    if results:
        print("\n🎉 Single file evaluation completed!")
        print(f"✅ Processed {results['method_info']['total_samples']} samples")
        print(f"✅ Contains {results['method_info']['cve_pairs']} CVE pairs")
        print("✅ Calculation logic strictly consistent with complete evaluator")
    else:
        print("❌ Evaluation failed")
    
    return results


if __name__ == "__main__":
    main()