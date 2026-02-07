
import json
import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import threading

class KnowledgeScoringCache:
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        if cache_dir is None:
            self.cache_dir = Path(__file__).parent / "cache" / "knowledge_scoring"
        else:
            self.cache_dir = Path(cache_dir)
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.vulspec_cache_file = self.cache_dir / "vulspec_scores.json"
        self.nvd_cache_file = self.cache_dir / "nvd_scores.json"
        self.spec_cache_file = self.cache_dir / "spec_scores.json"
        
        self._vulspec_cache = {}
        self._nvd_cache = {}
        self._spec_cache = {}
        
        self._lock = threading.RLock()
        
        self._load_all_caches()
        
        self.logger.info(f"🔄 Knowledge scoring cache system initialized successfully")
        self.logger.info(f"   Cache directory: {self.cache_dir}")
        self.logger.info(f"   VulSpec cache: {len(self._vulspec_cache)} entries")
        self.logger.info(f"   NVD cache: {len(self._nvd_cache)} entries")
        self.logger.info(f"   Spec cache: {len(self._spec_cache)} entries")
    
    def generate_cache_key(self, cve_id: str, code_type: str, data_source: str, 
                          code_snippet: str, knowledge_type: str) -> str:
        
        primary_key = f"{cve_id}_{code_type}_{data_source}"
        
        normalized_code = self._normalize_code_snippet(code_snippet)
        secondary_key = hashlib.md5(normalized_code.encode('utf-8')).hexdigest()[:8]
        
        tertiary_key = knowledge_type
        
        return f"{primary_key}:{secondary_key}:{tertiary_key}"
    
    def _normalize_code_snippet(self, code: str) -> str:
        if not code:
            return ""
        
        lines = code.strip().split('\n')
        normalized_lines = []
        
        for line in lines:
            stripped = line.rstrip()
            if stripped:
                leading_spaces = len(line) - len(line.lstrip())
                indent_units = leading_spaces
                remainder = leading_spaces % 4
                normalized_indent = '    ' * indent_units + ' ' * remainder
                normalized_lines.append(normalized_indent + stripped.lstrip())
        
        return '\n'.join(normalized_lines)
    
    def get_vulspec_evaluation(self, cve_id: str, code_type: str, data_source: str,
                              code_snippet: str, vulspec_cases: List[Dict]) -> Optional[Dict]:
        with self._lock:
            cache_key = self.generate_cache_key(cve_id, code_type, data_source, 
                                              code_snippet, "vulspec")
            
            if cache_key in self._vulspec_cache:
                cached_result = self._vulspec_cache[cache_key]
                
                if len(cached_result["scores"]) == len(vulspec_cases):
                    self.logger.debug(f"📥 VulSpec cache hit: {cache_key}")
                    return self._reconstruct_vulspec_result(cached_result, vulspec_cases)
                else:
                    self.logger.warning(f"⚠️  VulSpec cache case count mismatch: {cache_key}")
                    del self._vulspec_cache[cache_key]
            
            return None
    
    def cache_vulspec_evaluation(self, cve_id: str, code_type: str, data_source: str,
                                code_snippet: str, vulspec_cases: List[Dict], 
                                evaluation_result: Dict) -> None:
        with self._lock:
            cache_key = self.generate_cache_key(cve_id, code_type, data_source,
                                              code_snippet, "vulspec")
            
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "cve_id": cve_id,
                "code_type": code_type,
                "data_source": data_source,
                "knowledge_type": "vulspec",
                "cases_count": len(vulspec_cases),
                "code_hash": hashlib.md5(self._normalize_code_snippet(code_snippet).encode()).hexdigest()[:8],
                "scores": []
            }
            
            for score_item in evaluation_result.get("scores", []):
                cache_data["scores"].append({
                    "score": score_item["score"],
                    "reasoning": score_item["reasoning"],
                    "case_metadata": self._extract_case_metadata(score_item["case"])
                })
            
            self._vulspec_cache[cache_key] = cache_data
            self._save_vulspec_cache()
            
            self.logger.info(f"💾 VulSpec evaluation results cached: {cache_key}")
    
    def get_nvd_evaluation(self, cve_id: str, code_type: str, data_source: str,
                          code_snippet: str, nvd_cases: List[Dict]) -> Optional[Dict]:
        with self._lock:
            cache_key = self.generate_cache_key(cve_id, code_type, data_source,
                                              code_snippet, "nvd")
            
            if cache_key in self._nvd_cache:
                cached_result = self._nvd_cache[cache_key]
                
                if len(cached_result["scores"]) == len(nvd_cases):
                    self.logger.debug(f"📥 NVD cache hit: {cache_key}")
                    return self._reconstruct_nvd_result(cached_result, nvd_cases)
                else:
                    self.logger.warning(f"⚠️  NVD cache case count mismatch: {cache_key}")
                    del self._nvd_cache[cache_key]
            
            return None
    
    def cache_nvd_evaluation(self, cve_id: str, code_type: str, data_source: str,
                            code_snippet: str, nvd_cases: List[Dict],
                            evaluation_result: Dict) -> None:
        with self._lock:
            cache_key = self.generate_cache_key(cve_id, code_type, data_source,
                                              code_snippet, "nvd")
            
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "cve_id": cve_id,
                "code_type": code_type,
                "data_source": data_source,
                "knowledge_type": "nvd", 
                "cases_count": len(nvd_cases),
                "code_hash": hashlib.md5(self._normalize_code_snippet(code_snippet).encode()).hexdigest()[:8],
                "scores": []
            }
            
            for score_item in evaluation_result.get("scores", []):
                cache_data["scores"].append({
                    "score": score_item["score"],
                    "reasoning": score_item["reasoning"],
                    "case_metadata": self._extract_case_metadata(score_item["case"])
                })
            
            self._nvd_cache[cache_key] = cache_data
            self._save_nvd_cache()
            
            self.logger.info(f"💾 NVD evaluation results cached: {cache_key}")
    
    def get_spec_evaluation(self, cve_id: str, code_type: str, data_source: str,
                           code_snippet: str, specifications: List[str]) -> Optional[Dict]:
        with self._lock:
            cache_key = self.generate_cache_key(cve_id, code_type, data_source,
                                              code_snippet, "spec")
            
            if cache_key in self._spec_cache:
                cached_result = self._spec_cache[cache_key]
                
                if len(cached_result["scores"]) == len(specifications):
                    self.logger.debug(f"📥 Spec cache hit: {cache_key}")
                    return self._reconstruct_spec_result(cached_result, specifications)
                else:
                    self.logger.warning(f"⚠️  Spec cache specification count mismatch: {cache_key}")
                    del self._spec_cache[cache_key]
            
            return None
    
    def cache_spec_evaluation(self, cve_id: str, code_type: str, data_source: str,
                             code_snippet: str, specifications: List[str],
                             evaluation_result: Dict) -> None:
        with self._lock:
            cache_key = self.generate_cache_key(cve_id, code_type, data_source,
                                              code_snippet, "spec")
            
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "cve_id": cve_id,
                "code_type": code_type, 
                "data_source": data_source,
                "knowledge_type": "spec",
                "specs_count": len(specifications),
                "code_hash": hashlib.md5(self._normalize_code_snippet(code_snippet).encode()).hexdigest()[:8],
                "scores": []
            }
            
            for i, score_item in enumerate(evaluation_result.get("scores", [])):
                cache_data["scores"].append({
                    "score": score_item["score"], 
                    "reasoning": score_item["reasoning"],
                    "spec_index": i,
                    "spec_preview": score_item["specification"][:100] + "..." if len(score_item["specification"]) > 100 else score_item["specification"]
                })
            
            self._spec_cache[cache_key] = cache_data
            self._save_spec_cache()
            
            self.logger.info(f"💾 Spec evaluation results cached: {cache_key}")
    
    def _extract_case_metadata(self, case: Dict) -> Dict:
        if not case:
            return {}
        
        metadata = {}
        
        if "cve_id" in case:
            metadata["cve_id"] = case["cve_id"]
        elif isinstance(case, dict):
            case_data = case.get("case_data", case)
            if "cve_id" in case_data:
                metadata["cve_id"] = case_data["cve_id"]
        
        for key in ["description", "title", "summary"]:
            if key in case:
                content = str(case[key])[:200]
                metadata[f"{key}_preview"] = content
                break
        
        return metadata
    
    def _reconstruct_vulspec_result(self, cached_data: Dict, vulspec_cases: List[Dict]) -> Dict:
        scores = []
        
        for i, (score_cache, case) in enumerate(zip(cached_data["scores"], vulspec_cases)):
            scores.append({
                "case": case,
                "score": score_cache["score"],
                "reasoning": score_cache["reasoning"]
            })
        
        return {"scores": scores}
    
    def _reconstruct_nvd_result(self, cached_data: Dict, nvd_cases: List[Dict]) -> Dict:
        scores = []
        
        for i, (score_cache, case) in enumerate(zip(cached_data["scores"], nvd_cases)):
            scores.append({
                "case": case,
                "score": score_cache["score"], 
                "reasoning": score_cache["reasoning"]
            })
        
        return {"scores": scores}
    
    def _reconstruct_spec_result(self, cached_data: Dict, specifications: List[str]) -> Dict:
        scores = []
        
        for i, (score_cache, spec) in enumerate(zip(cached_data["scores"], specifications)):
            scores.append({
                "specification": spec,
                "score": score_cache["score"],
                "reasoning": score_cache["reasoning"]
            })
        
        return {"scores": scores}
    
    def _load_all_caches(self) -> None:
        self._load_vulspec_cache()
        self._load_nvd_cache()
        self._load_spec_cache()
    
    def _load_vulspec_cache(self) -> None:
        try:
            if self.vulspec_cache_file.exists():
                with open(self.vulspec_cache_file, 'r', encoding='utf-8') as f:
                    self._vulspec_cache = json.load(f)
        except Exception as e:
            self.logger.error(f"❌ Failed to load VulSpec cache: {e}")
            self._vulspec_cache = {}
    
    def _load_nvd_cache(self) -> None:
        try:
            if self.nvd_cache_file.exists():
                with open(self.nvd_cache_file, 'r', encoding='utf-8') as f:
                    self._nvd_cache = json.load(f)
        except Exception as e:
            self.logger.error(f"❌ Failed to load NVD cache: {e}")
            self._nvd_cache = {}
    
    def _load_spec_cache(self) -> None:
        try:
            if self.spec_cache_file.exists():
                with open(self.spec_cache_file, 'r', encoding='utf-8') as f:
                    self._spec_cache = json.load(f)
        except Exception as e:
            self.logger.error(f"❌ Failed to load Spec cache: {e}")
            self._spec_cache = {}
    
    def _save_vulspec_cache(self) -> None:
        try:
            existing_cache = {}
            if self.vulspec_cache_file.exists():
                try:
                    with open(self.vulspec_cache_file, 'r', encoding='utf-8') as f:
                        existing_cache = json.load(f)
                except:
                    pass
            
            existing_cache.update(self._vulspec_cache)
            
            with open(self.vulspec_cache_file, 'w', encoding='utf-8') as f:
                json.dump(existing_cache, f, ensure_ascii=False, indent=2)
            
            self._vulspec_cache = existing_cache
                
        except Exception as e:
            self.logger.error(f"❌ Failed to save VulSpec cache: {e}")
        
    def _save_nvd_cache(self) -> None:
        try:
            existing_cache = {}
            if self.nvd_cache_file.exists():
                try:
                    with open(self.nvd_cache_file, 'r', encoding='utf-8') as f:
                        existing_cache = json.load(f)
                except:
                    pass
            
            existing_cache.update(self._nvd_cache)
            
            with open(self.nvd_cache_file, 'w', encoding='utf-8') as f:
                json.dump(existing_cache, f, ensure_ascii=False, indent=2)
            
            self._nvd_cache = existing_cache
                
        except Exception as e:
            self.logger.error(f"❌ Failed to save NVD cache: {e}")
    
    def _save_spec_cache(self) -> None:
        try:
            existing_cache = {}
            if self.spec_cache_file.exists():
                with open(self.spec_cache_file, 'r', encoding='utf-8') as f:
                    existing_cache = json.load(f)
            
            existing_cache.update(self._spec_cache)
            
            with open(self.spec_cache_file, 'w', encoding='utf-8') as f:
                json.dump(existing_cache, f, ensure_ascii=False, indent=2)
                
            self._spec_cache = existing_cache
        except Exception as e:
            self.logger.error(f"❌ Failed to save Spec cache: {e}")

    def get_cache_statistics(self) -> Dict:
        with self._lock:
            return {
                "vulspec_cache_size": len(self._vulspec_cache),
                "nvd_cache_size": len(self._nvd_cache),
                "spec_cache_size": len(self._spec_cache),
                "total_cache_entries": len(self._vulspec_cache) + len(self._nvd_cache) + len(self._spec_cache),
                "cache_files": {
                    "vulspec": str(self.vulspec_cache_file),
                    "nvd": str(self.nvd_cache_file),
                    "spec": str(self.spec_cache_file)
                }
            }
    
    def clear_all_caches(self) -> None:
        with self._lock:
            self._vulspec_cache.clear()
            self._nvd_cache.clear()
            self._spec_cache.clear()
            
            for cache_file in [self.vulspec_cache_file, self.nvd_cache_file, self.spec_cache_file]:
                if cache_file.exists():
                    cache_file.unlink()
            
            self.logger.info("🗑️  All caches cleared")