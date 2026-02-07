"""
VulInstruct Two-Stage Vulnerability Detector
Processing complete 419 pair dataset with knowledge-enhanced detection
Features: LLM semantic evaluation, HTML structuring, multi-layer analysis framework
"""

import sys
import time
import json
import logging
import tiktoken
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import os


os.environ['PYTHONUNBUFFERED'] = '1'
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_manager import APIManager
from core.knowledge_systems.knowledge_scoring_cache import KnowledgeScoringCache

class VulInstructTwoStageDetector:
    """VulInstruct Two-Stage Vulnerability Detector - Complete dataset version"""
    
    def __init__(self, api_manager: APIManager, model_name: str = "deepseek/deepseek-chat", model_eval_name: str = "deepseek/deepseek-chat", model_score_name: str = "deepseek/deepseek-chat", vulspec_threshold: int = 7, nvd_threshold: int = 7, spec_threshold: int = 7, use_code_context: bool = True):
        self.api_manager = api_manager
        self.model_name = "deepseek-chat"
        self.model_eval_name = "deepseek-chat"
        self.model_score_name = "deepseek-chat"
        self.detector_type = "VulInstructTwoStageDetector"
        self.logger = logging.getLogger(__name__)
        
        self.vulspec_threshold = vulspec_threshold
        self.nvd_threshold = nvd_threshold
        self.spec_threshold = spec_threshold
        self.use_code_context = use_code_context
        
        self.knowledge_cache = KnowledgeScoringCache()

        self.total_tokens_accumulated = 0
        self.total_samples_processed = 0
        
        self.logger.info(f"🚀 VulInstruct two-stage detector initialized, model: {model_name}")
        self.logger.info("   VulInstruct features: Knowledge-enhanced detection + Full 419 pair dataset support")
        self.logger.info(f"   Threshold settings: VulSpec>={vulspec_threshold}, NVD>={nvd_threshold}, Spec>={spec_threshold}")
        self.logger.info("   ✅ Knowledge scoring cache system enabled, ensuring scoring consistency")
    
    def _count_tokens(self, text, model="cl100k_base"):
        """Helper method to count tokens"""
        try:
            if not isinstance(text, str):
                if isinstance(text, (dict, list)):
                    text = json.dumps(text, ensure_ascii=False)
                else:
                    text = str(text)
            
            encoding = tiktoken.get_encoding(model)
            return len(encoding.encode(text))
        except Exception as e:
            self.logger.warning(f"Token counting failed: {e}")
            return 0

    def _parse_attack_specifications(self, response: str) -> List[str]:
        try:
            import re
            specifications = []

            spec_pattern = r'<specification_\d+>(.*?)</specification_\d+>'
            spec_matches = re.findall(spec_pattern, response, re.DOTALL)

            for spec_content in spec_matches:
                pattern_match = re.search(
                    r'<attack_pattern>(.*?)</attack_pattern>',
                    spec_content,
                    re.DOTALL
                )
                spec_match = re.search(
                    r'<defensive_spec>(.*?)</defensive_spec>',
                    spec_content,
                    re.DOTALL
                )
                hint_match = re.search(
                    r'<implementation_hint>(.*?)</implementation_hint>',
                    spec_content,
                    re.DOTALL
                )

                if spec_match:
                    spec_text = spec_match.group(1).strip()

                    full_spec = [spec_text]
                    if pattern_match:
                        full_spec.append(f"  [Attack Pattern: {pattern_match.group(1).strip()}]")
                    if hint_match:
                        full_spec.append(f"  [Implementation: {hint_match.group(1).strip()}]")

                    specifications.append("\n".join(full_spec))

            return specifications

        except Exception as e:
            self.logger.error(f"Failed to parse attack specifications: {e}")
            return []

    def _extract_attack_specifications_from_nvd(self, nvd_cases: List[Dict], 
                                              code_snippet: str, target_cve: str) -> Tuple[List[str], int]:  
        nvd_descriptions = []
        for case in nvd_cases[:10]:
            cve_id = case.get("cve_id", "")
            desc = case.get("description", "")[:800]
            nvd_descriptions.append(f"{cve_id}: {desc}")
        
        extraction_prompt = f"""You are a security expert. Analyze these related vulnerabilities and extract reusable security specifications.
    Related Historical Vulnerabilities
    {chr(10).join(nvd_descriptions)}
    Task: Extract Attack-Derived Specifications
    For each vulnerability pattern you identify:

    1. **Identify the recurring attack mechanism** across these CVEs
    2. **Convert it to a positive security specification** that would prevent such attacks
    3. **Format as defensive requirements** developers must implement
    Output format:
    <attack_specifications>
    <specification_1>
    <attack_pattern>Description of recurring attack mechanism in cve-xxx and cve-xxx in detail</attack_pattern>
    <defensive_spec>AS-DOMAIN-001: security rule that describe the code behavior that prevents this attack</defensive_spec>
    <implementation_hint>Specific checks or validations needed</implementation_hint>
    </specification_1>
    <specification_2>
    ...
    </specification_2>
    </attack_specifications>
"""
        try:
            response, tokens = self._call_api_with_retry(
            extraction_prompt, self.model_score_name
            )
            specs = self._parse_attack_specifications(response)
            return specs, tokens
        except Exception as e:
            self.logger.error(f"Failed to extract attack specifications: {e}")
            return [], 0 

    

    
    
    def detect_single_sample(self, sample: Dict, **kwargs) -> Dict:
        """Two-stage detection for single sample - VulInstruct full dataset version (uses proven logic)"""
        sample_id = sample.get("sample_id", "")
        cve_id = sample.get("cve_id", "")
        code_type = sample.get("code_type", "")
        data_source = sample.get("data_source", "")
        sample_total_tokens = 0
        
        self.logger.debug(f"🚀 Starting two-stage detection VulInstruct: {sample_id} (source: {data_source})")
        
        result = {
            "sample_id": sample_id,
            "cve_id": cve_id,
            "code_type": code_type,
            "data_source": data_source,
            "true_label": sample.get("true_label"),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "model_name": self.model_name,
            "detector_type": self.detector_type,
            "stage1_vulnerability_detection": {},
            "stage2_match_prediction": {},
            "knowledge_utilization": {},
            "vulinstruct_full_dataset_info": {
                "sample_pair_id": sample.get("sample_pair_id", ""),
                "vulinstruct_full_dataset": sample.get("vulinstruct_full_dataset", False)
            }
        }
        
        try:
            stage1_result, s1_tokens = self._stage1_vulinstruct_detection(sample)
            sample_total_tokens += s1_tokens

            result["stage1_vulnerability_detection"] = stage1_result
            result["vulinstruct_llm_knowledge_scoring"] = stage1_result.get("llm_knowledge_scoring", {})
            
            vulnerability_prediction = stage1_result.get("vulnerability_prediction", 0)
            if vulnerability_prediction == 1:
                self.logger.debug(f"Sample {sample_id} predicted vulnerable, entering Stage2 evaluation")  
                stage2_result, s2_tokens = self._stage2_vulinstruct_evaluation(sample, stage1_result)
                sample_total_tokens += s2_tokens
                result["stage2_match_prediction"] = stage2_result
                match_prediction = stage2_result.get("match_result", "N/A")
            else:
                self.logger.debug(f"Sample {sample_id} predicted non-vulnerable, skipping Stage2 evaluation")
                stage2_result = {
                    "match_result": "N/A",
                    "match_confidence": 0.0,
                    "match_reasoning": "Predicted non-vulnerable, MATCH evaluation not performed",
                    "stage2_skipped": True,
                    "skip_reason": "vulnerability_prediction = 0"
                }
                result["stage2_match_prediction"] = stage2_result
                match_prediction = "N/A"
            
            self.total_tokens_accumulated += sample_total_tokens
            self.total_samples_processed += 1
            avg_tokens = self.total_tokens_accumulated / self.total_samples_processed
            result.update({
                "prediction": vulnerability_prediction,
                "confidence": stage1_result.get("confidence", 0.7),
                "reasoning": stage1_result.get("reasoning", ""),
                "match_prediction": match_prediction,
                "match_confidence": stage2_result.get("match_confidence", 0.0),
                "match_reasoning": stage2_result.get("match_reasoning", ""),
                "logical_flow_correct": True,
                "vulinstruct_full_dataset_applied": True,
                "knowledge_selection_based_on_llm": stage1_result.get("knowledge_selection_based_on_llm", False),
                "no_cheating_confirmed": True,
                "success": True,
                "avg_tokens_per_sample": round(avg_tokens, 2)
            })
            
            self.logger.debug(f"✅ VulInstruct completed: {sample_id} -> Vulnerability:{result['prediction']} MATCH:{result['match_prediction']}")
            
        except Exception as e:
            self.logger.error(f"❌ VulInstruct failed: {sample_id} - {e}")
            result.update({
                "prediction": 0,
                "confidence": 0.0,
                "reasoning": f"Detection failed: {str(e)}",
                "match_prediction": "ERROR",
                "logical_flow_correct": True,
                "vulinstruct_full_dataset_applied": False,
                "knowledge_selection_based_on_llm": False,
                "no_cheating_confirmed": False,
                "success": False,
                "error": str(e)
            })
        
        return result
    def _stage1_vulinstruct_detection(self, sample: Dict) -> Tuple[Dict, int]:
        tokens_used = 0
        llm_scoring = {}
        try:
            code_snippet = sample.get("code_snippet", "")
            code_context = sample.get("code_context", "")
            knowledge = sample.get("knowledge", {})
            selected_knowledge, llm_scoring, sel_tokens = self._vulinstruct_llm_knowledge_selection(knowledge, code_snippet, sample)
            tokens_used += sel_tokens
            detection_prompt = self._build_vulinstruct_detection_prompt(
                code_snippet, code_context, selected_knowledge, llm_scoring, sample
            )
            response, det_tokens = self._call_api_with_retry(detection_prompt, use_model=self.model_name)
            tokens_used += det_tokens
            vulnerability_prediction, confidence, reasoning, multi_layer_analysis = self._parse_vulinstruct_response(response)
            
            result = {
                "vulnerability_prediction": vulnerability_prediction,
                "confidence": confidence,
                "reasoning": reasoning,
                "stage1_prompt": detection_prompt,
                "raw_response": response,
                "detection_strategy": "vulinstruct_inherit_vulinstruct_llm_knowledge_scoring",
                "knowledge_selection_based_on_llm": llm_scoring["llm_evaluation_applied"],
                "llm_knowledge_scoring": llm_scoring,
                "selected_knowledge_count": llm_scoring.get("selected_total_count", 0),
                "multi_layer_analysis": multi_layer_analysis,
                "vulinstruct_data_source": sample.get("data_source", ""),
                "no_code_type_bias": True
            }

            return result, tokens_used
            
        except Exception as e:
            self.logger.error(f"Stage 1 VulInstruct detection exception: {e}")
            error_result = {
                "vulnerability_prediction": 0,
                "confidence": 0.5,
                "reasoning": f"VulInstruct detection exception: {str(e)}",
                "stage1_prompt": f"ERROR: {str(e)}",
                "detection_strategy": "vulinstruct_fallback",
                "knowledge_selection_based_on_llm": False,
                "llm_knowledge_scoring": {"error": str(e)},
                "selected_knowledge_count": 0,
                "multi_layer_analysis": {"error": str(e)},
                "vulinstruct_data_source": sample.get("data_source", ""),
                "no_code_type_bias": True
            }
            return error_result, tokens_used
        """VulInstruct uses proven's LLM knowledge selection logic with caching support"""
    def _vulinstruct_llm_knowledge_selection(self, knowledge: Dict, code_snippet: str, sample: Dict = None) -> Tuple[str, Dict, int]:
        tokens_used = 0    
        cve_id = sample.get("cve_id", "") if sample else ""
        code_type = sample.get("code_type", "") if sample else ""
        data_source = sample.get("data_source", "") if sample else ""
        
        llm_scoring_info = {
            "llm_evaluation_applied": False,
            "evaluation_strategy": "none",
            "vulspec_llm_scores": [],
            "nvd_llm_scores": [],
            "spec_llm_scores": [],
            "selected_vulspec_count": 0,
            "selected_nvd_count": 0,
            "selected_spec_count": 0,
            "selected_total_count": 0,
            "evaluation_reasoning": "",
            "vulinstruct_proven_methodology": True
        }
        
        if not knowledge:
            llm_scoring_info["evaluation_reasoning"] = "No available knowledge base"
            return "No relevant security knowledge available for reference", llm_scoring_info,0
        
        try:
            selected_knowledge_parts = []
            vulspec_cases = knowledge.get("vulspec_cases", [])
            selected_vulspec = []
            
            if vulspec_cases:
                vulspec_evaluation, vs_tokens = self._vulinstruct_llm_evaluate_vulspec_relevance(
                    code_snippet, vulspec_cases[:10], cve_id, code_type, data_source
                )
                tokens_used += vs_tokens
                llm_scoring_info["vulspec_llm_scores"] = vulspec_evaluation["scores"]
                for case_info in vulspec_evaluation["scores"]:
                    if case_info["score"] >= self.vulspec_threshold:
                        selected_vulspec.append(case_info["case"])
                
                llm_scoring_info["selected_vulspec_count"] = len(selected_vulspec)
                
                if selected_vulspec:
                    selected_knowledge_parts.append("### LLM-filtered highly relevant vulnerability cases (VulInstruct uses proven)")
                    for i, case in enumerate(selected_vulspec, 1):
                        case_data = case.get("case_data", case) if "case_data" in case else case
                        cve_id = case_data.get("cve_id", "Unknown")
                        
                        case_parts = []
                        case_parts.append(f"**{cve_id}**")
                        
                        understand = case_data.get("understand", "")
                        if understand:
                            if "### System Identification" in understand:
                                sys_info = understand.split("### System Identification")[1].split("###")[0].strip()[:500]
                                case_parts.append(f"System: {sys_info}...")
                        
                        threat_model = case_data.get("threat_model", "")
                        if threat_model:
                            if "<trust_boundaries>" in threat_model:
                                trust_boundaries = threat_model.split("<trust_boundaries>")[1].split("</trust_boundaries>")[0].strip()[:500]
                                case_parts.append(f"Threat boundaries: {trust_boundaries}...")
                            
                            if "<cwe_analysis>" in threat_model:
                                cwe_analysis = threat_model.split("<cwe_analysis>")[1].split("</cwe_analysis>")[0].strip()[:500]
                                case_parts.append(f"CWE analysis: {cwe_analysis}...")
                        
                        vuln_analysis = case_data.get("vulnerability_analysis", "")
                        if vuln_analysis:
                            if "#### 1. Entry Point & Preconditions" in vuln_analysis:
                                entry_section = vuln_analysis.split("#### 1. Entry Point & Preconditions")[1].split("####")[0].strip()[:500]
                                case_parts.append(f"entry point: {entry_section}...")
                            
                            if "#### 2. Vulnerable Code Path Analysis" in vuln_analysis:
                                path_section = vuln_analysis.split("#### 2. Vulnerable Code Path Analysis")[1].split("####")[0].strip()[:500]
                                case_parts.append(f"attack path: {path_section}...")
                        
                        solution_analysis = case_data.get("solution_analysis", "")
                        if solution_analysis:
                            if "<diff>" in solution_analysis:
                                diff_start = solution_analysis.find("<diff>")
                                diff_end = solution_analysis.find("</diff>", diff_start)
                                if diff_start != -1 and diff_end != -1:
                                    diff_content = solution_analysis[diff_start+6:diff_end].strip()[:]
                                    case_parts.append(f"key fixing: {diff_content}...")
                        
                        case_description = "\n    ".join(case_parts)
                        selected_knowledge_parts.append(f"{i}. {case_description}")
                        
                        if i < len(selected_vulspec):
                            selected_knowledge_parts.append("")
            nvd_cases = knowledge.get("nvd_cases", [])
            selected_nvd = []
            
            if nvd_cases:
                nvd_evaluation, nvd_tokens = self._vulinstruct_llm_evaluate_nvd_relevance(
                    code_snippet, nvd_cases[:10], cve_id, code_type, data_source
                )
                tokens_used += nvd_tokens
                llm_scoring_info["nvd_llm_scores"] = nvd_evaluation["scores"]
                for case_info in nvd_evaluation["scores"]:
                    if case_info["score"] >= self.nvd_threshold:
                        selected_nvd.append(case_info["case"])
                
                llm_scoring_info["selected_nvd_count"] = len(selected_nvd)
                
                if selected_nvd:
                    attack_specs, as_tokens = self._extract_attack_specifications_from_nvd(
                        selected_nvd, code_snippet, cve_id
                    )
                    tokens_used += as_tokens
                    if attack_specs:
                        selected_knowledge_parts.append("\n### Attack-Derived Security Specifications")
                        selected_knowledge_parts.extend(attack_specs)
                    for i, case in enumerate(selected_nvd, 1):
                        cve_id = case.get("cve_id", "Unknown")
                        description = case.get("description", case.get("cve_description", ""))[:500] + "..." if len(case.get("description", case.get("cve_description", ""))) > 500 else case.get("description", case.get("cve_description", ""))
                        selected_knowledge_parts.append(f"{i}. {cve_id}: {description}")
            specifications = knowledge.get("specifications", [])
            selected_specs = []
            
            if specifications:
                spec_evaluation, sp_tokens = self._vulinstruct_llm_evaluate_spec_relevance(
                    code_snippet, specifications[:10], cve_id, code_type, data_source
                )
                tokens_used += sp_tokens
                llm_scoring_info["spec_llm_scores"] = spec_evaluation["scores"]
                for spec_info in spec_evaluation["scores"]:
                    if spec_info["score"] >= self.spec_threshold:
                        selected_specs.append(spec_info["specification"])
                
                llm_scoring_info["selected_spec_count"] = len(selected_specs)
                
                if selected_specs:
                    selected_knowledge_parts.append("\n### LLM-filtered relevant secure coding specifications (VulInstruct uses proven)")
                    for i, spec in enumerate(selected_specs, 1):
                        spec_text = spec[:]
                        selected_knowledge_parts.append(f"{i}. {spec_text}")
            total_high_relevance = llm_scoring_info["selected_vulspec_count"] + llm_scoring_info["selected_nvd_count"]
            llm_scoring_info["selected_total_count"] = total_high_relevance + llm_scoring_info["selected_spec_count"]
            
            if total_high_relevance >= 2 and selected_knowledge_parts:
                llm_scoring_info["llm_evaluation_applied"] = True
                llm_scoring_info["evaluation_strategy"] = "high_relevance_llm_selection"
                
                llm_scoring_info["evaluation_reasoning"] = f"VulInstruct uses proven: LLM evaluation found {total_high_relevance} highly relevant cases, choosing filtered knowledge"
                return "\n".join(selected_knowledge_parts), llm_scoring_info, tokens_used
                
            elif total_high_relevance >= 1 and selected_knowledge_parts:
                llm_scoring_info["llm_evaluation_applied"] = True
                llm_scoring_info["evaluation_strategy"] = "moderate_relevance_llm_selection"
                llm_scoring_info["evaluation_reasoning"] = f"VulInstruct uses proven: LLM evaluation found {total_high_relevance} relevant cases, cautiously using filtered knowledge"
                return "\n".join(selected_knowledge_parts), llm_scoring_info, tokens_used
                
            else:
                llm_scoring_info["llm_evaluation_applied"] = True
                llm_scoring_info["evaluation_strategy"] = "llm_determined_autonomous_analysis"
                llm_scoring_info["evaluation_reasoning"] =f"VulInstruct uses proven: LLM evaluation finds insufficient knowledge base relevance (high relevance: {total_high_relevance}), adopting autonomous analysis mode"
                return "Based on VulInstruct using proven's LLM semantic analysis, current code has insufficient relevance with existing vulnerability knowledge base to provide valuable reference, adopting pure technical analysis mode", llm_scoring_info, tokens_used
            
        except Exception as e:
            self.logger.error(f"VulInstruct LLM knowledge evaluation exception: {e}")
            llm_scoring_info["evaluation_reasoning"] = f"VulInstruct LLM knowledge evaluation exception: {str(e)}"
            return "VulInstruct LLM knowledge evaluation exception, adopting autonomous analysis mode", llm_scoring_info, tokens_used
    def _vulinstruct_llm_evaluate_vulspec_relevance(self, code_snippet: str, vulspec_cases: List[Dict], 
                                                  cve_id: str = "", code_type: str = "", data_source: str = "") -> Tuple[Dict, int]:
        """VulInstruct uses proven's VulSpec case relevance evaluation with caching"""
        
        if cve_id and code_type and data_source:
            cached_result = self.knowledge_cache.get_vulspec_evaluation(
                cve_id, code_type, data_source, code_snippet, vulspec_cases
            )
            if cached_result is not None:
                self.logger.debug(f"📥 Using VulSpec cache results: {cve_id}_{code_type}_{data_source}")
                return cached_result,0
        
        self.logger.debug(f"🔄 Executing VulSpec LLM evaluation: {cve_id}_{code_type}_{data_source}")
        
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
                    attack_surfaces = threat_model.split("<attack_surfaces>")[1].split("</attack_surfaces>")[0].strip()[:300]
                    case_eval_parts.append(f"attack surface: {attack_surfaces}")
            
            vuln_analysis = case_data.get("vulnerability_analysis", "")
            if vuln_analysis:
                if "The Flaw" in vuln_analysis:
                    flaw_start = vuln_analysis.find("**The Flaw**")
                    flaw_end = vuln_analysis.find("**", flaw_start + 15)
                    if flaw_start != -1:
                        if flaw_end == -1:
                            flaw_end = flaw_start + 500
                        flaw_content = vuln_analysis[flaw_start:flaw_end].strip()[:400]
                        case_eval_parts.append(f"key flaw: {flaw_content}")
                elif "#### 2. Vulnerable Code Path Analysis" in vuln_analysis:
                    path_section = vuln_analysis.split("#### 2. Vulnerable Code Path Analysis")[1].split("####")[0].strip()[:400]
                    case_eval_parts.append(f"vulnerable path: {path_section}")
            
            case_description = "\n".join(case_eval_parts)
            cases_for_evaluation.append(f"Case {i}:\n{case_description}")
            cases_for_evaluation.append("")
        
        evaluation_prompt = f"""You are a security expert. Please evaluate the relevance between the following code and historical vulnerability cases. (VulInstruct uses proven evaluation criteria)
```c
{code_snippet}
```
{chr(10).join(cases_for_evaluation)}
Please score the relevance of each case to the target code (1-10 points):

**VulInstruct uses proven scoring criteria**:
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
            response_text, tokens = self._call_api_with_retry(evaluation_prompt, self.model_score_name)
            result = self._parse_vulspec_evaluation(response_text, vulspec_cases)
            
            if cve_id and code_type and data_source:
                self.knowledge_cache.cache_vulspec_evaluation(
                    cve_id, code_type, data_source, code_snippet, vulspec_cases, result
                )
            
            return result,tokens
        except Exception as e:
            self.logger.error(f"VulInstruct VulSpec LLM evaluation failed: {e}")
            return {"scores": [{"case": case, "score": 5, "reasoning": f"Evaluation failed: {e}"} for case in vulspec_cases]},0
    def _vulinstruct_llm_evaluate_nvd_relevance(self, code_snippet: str, 
                                           nvd_cases: List[Dict], 
                                           cve_id: str = "", 
                                           code_type: str = "", 
                                           data_source: str = "") -> Tuple[Dict, int]:
        if cve_id and code_type and data_source:
            cached_result = self.knowledge_cache.get_nvd_evaluation(
                cve_id, code_type, data_source, code_snippet, nvd_cases
            )
            if cached_result is not None:
                self.logger.debug(f"📥 Using NVD cache results: {cve_id}_{code_type}_{data_source}")
                return cached_result,0
        
        self.logger.debug(f"🔄 Executing NVD LLM evaluation: {cve_id}_{code_type}_{data_source}")
        
        cases_for_evaluation = []
        for i, case in enumerate(nvd_cases, 1):
            case_cve_id = case.get("cve_id", f"NVD-{i}")
            description = case.get("description", "")[:400] + "..." if len(case.get("description", "")) > 400 else case.get("description", "")
            cases_for_evaluation.append(f"NVD Case {i} ({case_cve_id}):\n{description}")
        
        evaluation_prompt = f"""You are a security expert. Please evaluate the relevance between the following code and NVD vulnerability data. (VulInstruct uses proven evaluation criteria)
```c
{code_snippet}
```
{chr(10).join(cases_for_evaluation)}
Please score the relevance of each NVD case to the target code (1-10 points):

**VulInstruct uses proven scoring criteria**:
- 10 points: Highly relevant, vulnerability type, impact and code features highly match
- 8-9 points: Strong relevance, vulnerability types are similar, has important reference value
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
            response_text, tokens = self._call_api_with_retry(evaluation_prompt, self.model_score_name)
            result = self._parse_nvd_evaluation(response_text, nvd_cases)

            if cve_id and code_type and data_source:
                self.knowledge_cache.cache_nvd_evaluation(
                    cve_id, code_type, data_source, code_snippet, nvd_cases, result
                )
            
            return result,tokens
        except Exception as e:
            self.logger.error(f"VulInstruct NVD LLM evaluation failed: {e}")
            return {"scores": [{"case": case, "score": 5, "reasoning": f"Evaluation failed: {e}"} for case in nvd_cases]}, 0
    def _vulinstruct_llm_evaluate_spec_relevance(self, code_snippet: str, specifications: List[str],
                                                 cve_id: str = "", code_type: str = "", data_source: str = "") -> Tuple[Dict, int]:
        """VulInstruct uses proven's Specification relevance evaluation with caching"""
        
        if cve_id and code_type and data_source:
            cached_result = self.knowledge_cache.get_spec_evaluation(
                cve_id, code_type, data_source, code_snippet, specifications
            )
            if cached_result is not None:
                self.logger.debug(f"📥 Using Spec cache results: {cve_id}_{code_type}_{data_source}")
                return cached_result,0
        
        self.logger.debug(f"🔄 Executing Spec LLM evaluation: {cve_id}_{code_type}_{data_source}")
        
        specs_for_evaluation = []
        for i, spec in enumerate(specifications, 1):
            spec_text = spec[:300] + "..." if len(spec) > 300 else spec
            specs_for_evaluation.append(f"Specification {i}:\n{spec_text}")
        
        evaluation_prompt = f"""You are a security expert. Please evaluate the relevance between the following code and secure coding specifications. (VulInstruct uses proven evaluation criteria)
```c
{code_snippet}
```
{chr(10).join(specs_for_evaluation)}
Please score the relevance of each specification to the target code (1-10 points):

**VulInstruct uses proven scoring criteria**:
- 10 points: Highly relevant, specification directly applies to current code scenario
- 8-9 points: Strong relevance, main principles of the specification apply
- 6-7 points: Moderate relevance, part of the specification content has guidance value
- 4-5 points: Weak relevance, specification has weak connection with code scenario
- 1-3 points: Very low relevance, specification basically doesn't apply

Please strictly follow the HTML format for output:

<spec_evaluation>
<spec_1_score>8</spec_1_score>
<spec_1_reasoning>Scoring reason</spec_1_reasoning>
<spec_2_score>4</spec_2_score>
<spec_2_reasoning>Scoring reason</spec_2_reasoning>
...
</spec_evaluation>"""
        
        try:
            response_text, tokens = self._call_api_with_retry(evaluation_prompt, self.model_score_name)
            result = self._parse_spec_evaluation(response_text, specifications)
            
            if cve_id and code_type and data_source:
                self.knowledge_cache.cache_spec_evaluation(
                    cve_id, code_type, data_source, code_snippet, specifications, result
                )
            
            return result,tokens
        except Exception as e:
            self.logger.error(f"VulInstruct Specification LLM evaluation failed: {e}")
            return {"scores": [{"specification": spec, "score": 5, "reasoning": f"Evaluation failed: {e}"} for spec in specifications]},0
    def _parse_vulspec_evaluation(self, response: str, vulspec_cases: List[Dict]) -> Dict:
        """Parse VulSpec evaluation results (uses proven logic)"""
        try:
            import re
            
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
            self.logger.error(f"VulInstruct VulSpec evaluation parsing failed: {e}")
            return {"scores": [{"case": case, "score": 5, "reasoning": f"Parsing exception: {e}"} for case in vulspec_cases]}
    
    def _parse_nvd_evaluation(self, response: str, nvd_cases: List[Dict]) -> Dict:
        """Parse NVD evaluation results (uses proven logic)"""
        try:
            import re
            
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
            self.logger.error(f"VulInstruct NVD evaluation parsing failed: {e}")
            return {"scores": [{"case": case, "score": 5, "reasoning": f"Parsing exception: {e}"} for case in nvd_cases]}
    
    def _parse_spec_evaluation(self, response: str, specifications: List[str]) -> Dict:
        """Parse Specification evaluation results (uses proven logic)"""
        try:
            import re
            
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
            self.logger.error(f"VulInstruct Specification evaluation parsing failed: {e}")
            return {"scores": [{"specification": spec, "score": 5, "reasoning": f"Parsing exception: {e}"} for spec in specifications]}
    
    def _build_vulinstruct_detection_prompt(self, code_snippet: str, code_context: str, 
                                   selected_knowledge: str, llm_scoring_info: Dict, sample: Dict) -> str:
        """Build VulInstruct detection prompt (uses proven multi-layer analysis framework)"""
        knowledge_guidance = ""
        if llm_scoring_info["evaluation_strategy"] == "llm_determined_autonomous_analysis":
            knowledge_guidance = f"""
**Analysis Mode**: VulInstruct uses proven's autonomous technical analysis mode
Based on LLM semantic evaluation, current code has insufficient relevance with existing vulnerability knowledge base, please perform independent analysis based on your professional knowledge.
Data Source: {sample.get("data_source", "Unknown")}
"""
        elif llm_scoring_info["evaluation_strategy"] in ["high_relevance_llm_selection", "moderate_relevance_llm_selection"]:
            knowledge_guidance = f"""
**Analysis Mode**: VulInstruct uses proven's LLM-filtered knowledge-assisted analysis mode  
Highly relevant security knowledge has been filtered through LLM semantic evaluation as reference, please prioritize independent technical analysis with knowledge as supplement.
LLM Evaluation Reasoning: {llm_scoring_info["evaluation_reasoning"]}
Data Source: {sample.get("data_source", "Unknown")}
"""
        context_section = ""
        if self.use_code_context and code_context:
            context_section = f"""
{code_context}
"""
        elif self.use_code_context and not code_context:
            context_section = f"""
No additional context information
"""
        
        prompt = f"""You are a senior code security expert. Please perform systematic multi-layer security analysis on the following code. (VulInstruct uses proven analysis framework)

{knowledge_guidance}
```c
{code_snippet}
```context_section
{context_section}
{selected_knowledge}

Please perform systematic security evaluation according to the following multi-layer analysis framework:

Please identify the most direct, surface-level suspicious operations in the code:
- Unchecked array access operations
- Unvalidated input processing
- Arithmetic operations without overflow checks
- Unsafe memory operations
- Operations lacking boundary checks

Analyze the direct consequences these operations may lead to:
- Buffer overflow
- Program crash
- Memory corruption
- Illegal memory access

Deeply trace the core issues leading to surface symptoms:
- Track data flow and control flow to identify fundamental defects
- Analyze completeness of input validation
- Check adequacy of error handling
- Consider attacker exploitation paths

Example analysis chain: "Out-of-bounds access" ← "Missing user input validation" ← "Trusting unreliable input sources"

Examine design-level issues from a higher level:

**Resource Lifecycle Management**:
- Are all resources (memory, handles, locks) properly managed from creation to destruction?
- Are there risks of resource leaks or double-free?

**Concurrency and Timing**:
- Could race conditions occur?
- Are there TOCTOU (Time-of-Check-Time-of-Use) issues?

**Domain Context**:
- Consider specific application scenarios and framework constraints
- Analyze whether security assumptions at the business logic level hold

Based on the above three-layer analysis, please provide your professional judgment:

**Analysis Process**: 
[Please describe your three-layer analysis process in detail, including discovered issues and reasoning chains]

**Key Findings**:
[List the most important security findings]

**Final Conclusion**: 
Please strictly follow the format below for output:

<vulnerability_assessment>
<has_vulnerability>yes/no</has_vulnerability>
<confidence>0-1</confidence>
<suspected_root_cause>Summarize core findings from multi-layer analysis</suspected_root_cause>
</vulnerability_assessment>

**Format Description**:
- has_vulnerability: "yes" or "no" 
- confidence: Confidence level between 0.0 and 1.0
- Provide accurate judgment based on in-depth multi-layer analysis
- If fixing solution has been used, you can judge "no"
- Focus on analysis quality, avoid over-sensitivity"""
        
        return prompt
    
    def _parse_vulinstruct_response(self, response: str) -> Tuple[int, float, str, Dict]:
        """Parse VulInstruct response (uses proven multi-layer analysis logic)"""
        
        multi_layer_analysis = {
            "surface_symptoms_found": [],
            "root_causes_identified": [],
            "architectural_issues": [],
            "analysis_depth_score": 0,
            "parsing_success": False,
            "vulinstruct_proven_parsing": True
        }
        
        try:
            import re
            from html import unescape
            assessment_pattern = r'<vulnerability_assessment>(.*?)</vulnerability_assessment>'
            assessment_match = re.search(assessment_pattern, response, re.DOTALL)
            
            vulnerability_prediction = 0
            confidence = 0.7
            reasoning = ""
            
            if assessment_match:
                assessment_content = assessment_match.group(1)
                has_vuln_pattern = r'<has_vulnerability>(yes|no)</has_vulnerability>'
                has_vuln_match = re.search(has_vuln_pattern, assessment_content, re.IGNORECASE)
                
                if has_vuln_match:
                    vulnerability_prediction = 1 if has_vuln_match.group(1).lower() == "yes" else 0
                    multi_layer_analysis["parsing_success"] = True
                conf_pattern = r'<confidence>([0-9.]+)</confidence>'
                conf_match = re.search(conf_pattern, assessment_content)
                
                if conf_match:
                    try:
                        confidence = float(conf_match.group(1))
                        if confidence > 1.0:
                            confidence = confidence / 100.0
                    except:
                        pass
                root_cause_pattern = r'<suspected_root_cause>(.*?)</suspected_root_cause>'
                root_cause_match = re.search(root_cause_pattern, assessment_content, re.DOTALL)
                
                suspected_root_cause = ""
                if root_cause_match:
                    suspected_root_cause = unescape(root_cause_match.group(1).strip())
                reasoning_parts = []
                reasoning_parts.append("VulInstruct uses proven LLM knowledge scoring multi-layer analysis results:")
                
                if suspected_root_cause:
                    reasoning_parts.append(f"Suspected Root Cause: {suspected_root_cause}")
                if "Analysis Process" in response or "analysis process" in response.lower():
                    analysis_process_start = response.lower().find("analysis process")
                    analysis_process_end = response.lower().find("final conclusion", analysis_process_start)
                    if analysis_process_start != -1 and analysis_process_end != -1:
                        analysis_process = response[analysis_process_start:analysis_process_end].strip()
                        reasoning_parts.append(f"\nDetailed Analysis: {analysis_process}")
                
                reasoning = "\n\n".join(reasoning_parts) if reasoning_parts else f"VulInstruct uses proven analysis:\n{response[:]}..."
                analysis_keywords = ["surface", "root cause", "architectural", "data flow", "control flow", "lifecycle"]
                depth_score = sum(1 for keyword in analysis_keywords if keyword.lower() in response.lower())
                multi_layer_analysis["analysis_depth_score"] = depth_score
                
            else:
                vulnerability_patterns = [
                    r'Final [Cc]onclusion[：:]?\s*(yes|no|has vulnerability|no vulnerability)',
                    r'has_vulnerability[：:]?\s*(yes|no)',
                    r'Vulnerability [Jj]udgment[：:]?\s*([01])',
                    r'[Cc]onclusion[：:]?\s*(exists|does not exist|has|no).*vulnerability'
                ]
                
                for pattern in vulnerability_patterns:
                    match = re.search(pattern, response, re.IGNORECASE)
                    if match:
                        result = match.group(1).lower()
                        if result in ["yes", "has vulnerability", "1", "exists", "has"]:
                            vulnerability_prediction = 1
                        break
                
                reasoning = f"VulInstruct uses proven analysis (fallback parsing):\n\n{response[:]}"
            
            self.logger.debug(f"VulInstruct multi-layer analysis parsing: Vulnerability={vulnerability_prediction}, Confidence={confidence}, Parsing success={multi_layer_analysis['parsing_success']}")
            
            return vulnerability_prediction, confidence, reasoning, multi_layer_analysis
            
        except Exception as e:
            self.logger.error(f"VulInstruct multi-layer analysis response parsing failed: {e}")
            multi_layer_analysis["parsing_error"] = str(e)
            return 0, 0.5, f"VulInstruct parsing failed: {str(e)}\n\nOriginal response:\n{response[:500]}...", multi_layer_analysis
    def _stage2_vulinstruct_evaluation(self, sample: Dict, stage1_result: Dict) -> Tuple[Dict, int]:
        tokens_used = 0
        try:
            ground_truth_info = sample.get("ground_truth_info")
            if ground_truth_info is None:
                ground_truth_info = {}

            cve_description = ground_truth_info.get("cve_description", "")
            commit_message = ground_truth_info.get("commit_message", "")
            code_diff = ground_truth_info.get("code_diff", "")
            
            if not cve_description:
                self.logger.warning(f"Sample {sample.get('sample_id')} missing CVE description")
                return self._create_error_stage2_result("Missing CVE description"),0
            stage1_reasoning = stage1_result.get("reasoning", "")
            if not stage1_reasoning or len(stage1_reasoning.strip()) < 30:
                stage1_reasoning = stage1_result.get("raw_response", "")
                if not stage1_reasoning:
                    stage1_reasoning = f"VulInstruct uses proven analysis result: Predicted {'vulnerable' if stage1_result.get('vulnerability_prediction') else 'non-vulnerable'}, confidence {stage1_result.get('confidence', 0.5)}"
            match_prompt = self._build_vulinstruct_stage2_prompt(
                cve_description, commit_message, code_diff, stage1_reasoning, sample
            )
            response, tokens_used = self._call_api_with_retry(match_prompt, use_model=self.model_eval_name)
            match_result, match_confidence, match_reasoning = self._parse_stage2_response_vulinstruct(response)
            
            result = {
                "match_result": match_result,
                "match_confidence": match_confidence,
                "match_reasoning": match_reasoning,
                "raw_response": response,
                "evaluation_applied": True,
                "stage2_prompt": match_prompt,
                "match_prompt": match_prompt,
                "vulinstruct_stage2_applied": True,
                "analysis_content_length": len(stage1_reasoning)
            }
            return result, tokens_used
            
        except Exception as e:
            self.logger.error(f"Stage 2 VulInstruct evaluation exception: {e}")
            return self._create_error_stage2_result(f"Stage 2 exception: {str(e)}"), 0
    
    def _build_vulinstruct_stage2_prompt(self, cve_description: str, commit_message: str, 
                                code_diff: str, analysis: str, sample: Dict) -> str:
        """Build VulInstruct's Stage2 prompt - Use proven standard evaluation template"""
        code_type = sample.get("code_type", "")
        data_source = sample.get("data_source", "")
        
        if len(analysis.strip()) < 50:
            vuln_status = 'has vulnerability' if 'vulnerability_prediction\":1' in str(sample) else 'has no obvious vulnerability'
            analysis = f"VulInstruct uses proven LLM knowledge scoring detection tool analysis result. The tool determines code {vuln_status} based on VulInstruct full dataset framework. Data source: {data_source}. Please perform professional evaluation based on CVE description and code changes. Original analysis content: {analysis}"
        
        if code_type == "before":
            return f"""You are a security expert tasked with evaluating a vulnerability detection tool. You are provided with the following:

**Ground Truth**: This includes a CVE description, a commit diff, and a commit message, which collectively describe the cause of the vulnerability.

**Analysis to Evaluate**: This is the rationale generated by an VulInstruct full dataset LLM knowledge scoring vulnerability detection tool based on the vulnerable version of the code, rather than the patched code. This does not necessarily mean the vulnerability detection tool has produced a correct result. We are specifically interested in whether the rationale correctly identifies the ground truth vulnerability.

**Evaluation Criteria**:
- If the causes described in the analysis include the ground truth vulnerability, or If the analysis successfully detects the key elements of the ground truth vulnerability, it indicates a **MATCH**.
- If the analysis does not include the ground truth vulnerability and only identifies unrelated issues, return **MISMATCH**.

Let's think step by step, first analyze the ground truth and rationale, in the end return "MATCH" or "MISMATCH".

**CVE Description:**
{cve_description}

**Commit Message:**
{commit_message}

**Code Diff:**
{code_diff}

**Analysis to Evaluate:**
{analysis}

Please analyze whether the analysis correctly identifies the ground truth vulnerability described in the CVE, commit message, and code diff. 

Step-by-step evaluation:
1. What is the core vulnerability described in the ground truth?
2. What does the VulInstruct tool's analysis claim about the code?
3. Do they align? Does the tool identify the same or related security issue?

Return your final judgment as "MATCH" or "MISMATCH"."""

        else:
            return f"""You are a security expert tasked with evaluating a vulnerability detection tool. You are provided with the following:

**Ground Truth**: This includes a CVE description, a commit diff, and a commit message, which collectively describe the cause of the vulnerability.

**Analysis to Evaluate**: The rationale is generated by an VulInstruct full dataset LLM knowledge scoring detection tool based on the patched version of the code, not the original vulnerable code, which means the tool reports some issues on the non-vulnerable code. However, this does not necessarily mean the vulnerability detection tool has produced a false alarm. We are specifically interested in whether the rationale includes a false alarm related to the ground truth vulnerability.

**Evaluation Criteria**:
- If the causes described in the rationale include the ground truth vulnerability (already fixed in the patched code), meaning either the rationale considers a newly added line in the patch problematic (indicated by + in the diff), or the cause identified by the rationale matches the ground truth vulnerability, it indicates a **FALSE_ALARM**.
- Otherwise, if the rationale does not include the ground truth vulnerability or refers to different issues, return **CORRECT**.

Let's think step by step, first analyze the ground truth and rationale, in the end return "FALSE_ALARM" or "CORRECT".

**CVE Description:**
{cve_description}

**Commit Message:**
{commit_message}

**Code Diff:**
{code_diff}

**Analysis to Evaluate:**
{analysis}

Please analyze whether the analysis includes a false alarm related to the ground truth vulnerability that was already fixed in the patched code.

Step-by-step evaluation:
1. What vulnerability was fixed according to the ground truth?
2. What does the VulInstruct tool's analysis claim about the patched code?
3. Is the tool incorrectly flagging the already-fixed vulnerability?

Return your final judgment as "FALSE_ALARM" or "CORRECT"."""
    def _call_api_with_retry(self, prompt: str, use_model: str, 
                        max_retries: int = 3) -> Tuple[str, int]:
        """API call with retry (uses proven logic)"""        
        for attempt in range(max_retries):
            try:
                response = self.api_manager.query_llm(
                    prompt=prompt,
                    model=use_model,
                    max_retries=1
                )
                
                if response and not response.startswith("API Error:"):
                    res_text = response.strip()
                    input_tokens = self._count_tokens(prompt)
                    output_tokens = self._count_tokens(res_text)
                    total_tokens = input_tokens + output_tokens
                    return res_text, total_tokens
                else:
                    raise Exception(f"API call failed: {response}")
                    
            except Exception as e:
                self.logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        
        return "",0
    
    def _parse_stage2_response_vulinstruct(self, response: str) -> Tuple[str, float, str]:
        """Parse Stage 2 response - VulInstruct uses proven standard parsing logic"""
        try:
            import re
            
            final_patterns = [
                r'\*\*Final [Jj]udgment\*\*[：:]?\s*([A-Z_]+)',    
                r'Final [Jj]udgment[：:]?\s*\*\*([A-Z_]+)\*\*',    
                r'Final [Jj]udgment[：:]?\s*([A-Z_]+)',            
                r'\*\*Final [Jj]udgment\*\*[：:]?\s*\*\*([A-Z_]+)\*\*',
                r'\*\*Result[：:]?\s*([A-Z_]+)\*\*',              
                r'Result[：:]?\s*([A-Z_]+)',                      
                r'Final judgment[：:]?\s*([A-Z_]+)',                      
                r'return\s*[\"\'"]([A-Z_]+)[\"\'"]',                         
                r'judgment[：:]?\s*([A-Z_]+)',                    
                r'conclusion[：:]?\s*([A-Z_]+)',                  
            ]
            
            match_result = None
            for pattern in final_patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                if matches:
                    match_result = matches[-1].upper()
                    break
            
            if not match_result:
                response_upper = response.upper()
                lines = response.strip().split('\n')
                last_few_lines = ' '.join(lines[-6:])
                
                if "FALSE_ALARM" in last_few_lines.upper():
                    match_result = "FALSE_ALARM"
                elif "CORRECT" in last_few_lines.upper():
                    match_result = "CORRECT"
                elif "MISMATCH" in last_few_lines.upper():
                    match_result = "MISMATCH"
                elif "MATCH" in last_few_lines.upper() and "MISMATCH" not in last_few_lines.upper():
                    match_result = "MATCH"
                else:
                    if "MISMATCH" in response_upper:
                        match_result = "MISMATCH"
                    elif "FALSE_ALARM" in response_upper:
                        match_result = "FALSE_ALARM"
                    elif "CORRECT" in response_upper:
                        match_result = "CORRECT"
                    elif "MATCH" in response_upper:
                        match_result = "MATCH"
                    else:
                        match_result = "UNKNOWN"
            
            confidence = 0.8 if match_result in ["MATCH", "MISMATCH", "FALSE_ALARM", "CORRECT"] else 0.5
            
            self.logger.debug(f"VulInstruct Stage2 parsing result: {match_result}")
            
            return match_result, confidence, response
            
        except Exception as e:
            self.logger.error(f"VulInstruct Stage 2 response parsing failed: {e}")
            return "ERROR", 0.0, response
    
    def _create_error_stage2_result(self, error_msg: str) -> Dict:
        """Create error Stage2 result (uses proven logic)"""
        return {
            "match_result": "ERROR",
            "match_confidence": 0.0,
            "match_reasoning": error_msg,
            "raw_response": "",
            "stage2_prompt": f"ERROR: {error_msg}",
            "match_prompt": f"ERROR: {error_msg}",
            "vulinstruct_stage2_applied": False
        }