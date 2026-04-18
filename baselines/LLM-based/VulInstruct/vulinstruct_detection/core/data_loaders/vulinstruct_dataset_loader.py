"""
VulInstruct Dataset Loader
Merges 319+100=419 pair dataset, uses unified ground truth data
Provides unified data access interface for VulInstruct detection system
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict
sys.path.append(str(Path(__file__).parent))
from path_adapter import adapt_path
sys.path.append(str(Path(__file__).parent.parent.parent / "configs"))
from detection_config import get_mapped_path

class VulInstructDatasetLoader:
    """VulInstruct Dataset Loader - handles 419 pair complete dataset"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            self.exclude_100_path = get_mapped_path("primevul_full_exclude_100.json")
            self.subset_100_path = get_mapped_path("primevul_subset_100.json")
            self.vulspec_results_path = get_mapped_path("primevul_vulspec_retrieval_results_exclude.json")
            self.nvd_results_path = get_mapped_path("historical_samples_merged_v4_complete_20250822_203454.json")
            self.vulspec_results_100_path = get_mapped_path("primevul_vulspec_retrieval_results.json")
            self.nvd_results_100_path = get_mapped_path("historical_samples_top10_20250818_041337.json")
            self.base_path = Path(__file__).parent.parent.parent.parent.parent / "primevul_vulspec"
            self.ground_truth_file = Path("/path/to/json/file")
            self.logger.info("✅ VulInstruct data paths successfully mapped to primevul_retrieval structure")
            
        except Exception as e:
            self.logger.error(f"❌ Path mapping failed: {e}")
            self.base_path = Path("/path/to/base/directory")
            self.exclude_100_path = self.base_path / "data" / "primevul_full_exclude_100.json" 
            self.subset_100_path = self.base_path / "data" / "primevul_subset_100.json"
            self.vulspec_results_path = self.base_path / "results" / "final_dataset_v4_complete" / "primevul_vulspec_retrieval_results_exclude.json"
            self.nvd_results_path = self.base_path / "results" / "final_dataset_v4_complete" / "historical_samples_merged_v4_complete_20250822_203454.json"
            self.vulspec_results_100_path = self.base_path / "results" / "embedding_data" / "primevul_vulspec_retrieval_results.json"
            self.nvd_results_100_path = self.base_path / "results" / "final_dataset" / "historical_samples_top10_20250818_041337.json"
            self.ground_truth_file = self.project_root / "data" / "fixed_merged_matched_detection_results.json"
        self._exclude_100_data = None
        self._subset_100_data = None
        self._vulspec_results_319 = None
        self._vulspec_results_100 = None
        self._nvd_results_319 = None
        self._nvd_results_100 = None
        self._ground_truth_data = None
        self._full_dataset_cache = None
        
        self.logger.info("🚀 VulInstruct dataset loader initialization completed")
        self.logger.info(f"   Target dataset: 319 + 100 = 419 pair data")
        self.logger.info(f"   Unified ground truth: {self.ground_truth_file.name}")
    
    def load_full_detection_samples(self, limit: Optional[int] = None) -> List[Dict]:
        """Load complete 419 pair detection samples"""
        if self._full_dataset_cache is not None and (limit is None or len(self._full_dataset_cache) >= limit):
            return self._full_dataset_cache[:limit] if limit else self._full_dataset_cache
        
        self.logger.info("📊 Starting to load VulInstruct complete dataset...")
        
        exclude_100_data = self._load_exclude_100_data()
        subset_100_data = self._load_subset_100_data()
        vulspec_results_319 = self._load_vulspec_results_319()
        vulspec_results_100 = self._load_vulspec_results_100()
        nvd_results_319 = self._load_nvd_results_319()
        nvd_results_100 = self._load_nvd_results_100()
        ground_truth_data = self._load_ground_truth_data()
        
        self.logger.info(f"✅ Data sources loaded successfully:")
        self.logger.info(f"   exclude_100: {len(exclude_100_data)} items")
        self.logger.info(f"   subset_100: {len(subset_100_data)} items")
        self.logger.info(f"   ground_truth: {len(ground_truth_data)} items")
        
        samples = []
        missing_vulspec = 0
        missing_nvd = 0
        missing_ground_truth = 0
        
        for cve_data in exclude_100_data:
            cve_id = cve_data.get("cve_id", "")
            if not cve_id:
                continue
            
            processed_samples = self._process_cve_data(
                cve_data, "exclude_100", 
                vulspec_results_319, nvd_results_319, ground_truth_data
            )
            
            if processed_samples:
                samples.extend(processed_samples)
                for sample in processed_samples:
                    if not sample.get("knowledge", {}).get("vulspec_cases"):
                        missing_vulspec += 1
                    if not sample.get("knowledge", {}).get("nvd_cases"):
                        missing_nvd += 1
                    if not sample.get("ground_truth_info"):
                        missing_ground_truth += 1
        
        for cve_data in subset_100_data:
            cve_id = cve_data.get("cve_id", "")
            if not cve_id:
                continue
            
            processed_samples = self._process_cve_data(
                cve_data, "subset_100",
                vulspec_results_100, nvd_results_100, ground_truth_data
            )
            
            if processed_samples:
                samples.extend(processed_samples)
                for sample in processed_samples:
                    if not sample.get("knowledge", {}).get("vulspec_cases"):
                        missing_vulspec += 1
                    if not sample.get("knowledge", {}).get("nvd_cases"):
                        missing_nvd += 1
                    if not sample.get("ground_truth_info"):
                        missing_ground_truth += 1
        
        self._full_dataset_cache = samples
        
        unique_cve_ids = len(set(sample.get("cve_id") for sample in samples))
        before_samples = len([s for s in samples if s.get("code_type") == "before"])
        after_samples = len([s for s in samples if s.get("code_type") == "after"])
        
        self.logger.info(f"🎯 VulInstruct complete dataset loaded successfully:")
        self.logger.info(f"   Total samples: {len(samples)}")
        self.logger.info(f"   Unique CVEs: {unique_cve_ids}")
        self.logger.info(f"   Before samples: {before_samples}")
        self.logger.info(f"   After samples: {after_samples}")
        self.logger.info(f"   Missing VulSpec: {missing_vulspec}")
        self.logger.info(f"   Missing NVD: {missing_nvd}")
        self.logger.info(f"   Missing Ground Truth: {missing_ground_truth}")
        
        return samples[:limit] if limit else samples
    
    def _process_cve_data(self, cve_data: Dict, data_source: str, 
                         vulspec_results: Dict, nvd_results: Dict, 
                         ground_truth_data: List[Dict]) -> List[Dict]:
        
        cve_id = cve_data.get("cve_id", "")
        repository = cve_data.get("repository", "")
        cwe_list = cve_data.get("cwe_list", [])
        commit_hash = cve_data.get("commit_hash", "")
        
        before_methods = cve_data.get("vulnerableMethods_before", [])
        after_methods = cve_data.get("vulnerableMethods_after", [])
        
        if not before_methods:
            return []
        
        before_code = before_methods[0].get("raw_code", "") if before_methods else ""
        after_code = after_methods[0].get("raw_code", "") if after_methods else ""
        code_context = cve_data.get("code_context", "")
        
        if not before_code:
            return []
        
        vulspec_knowledge = self._get_vulspec_knowledge(cve_id, vulspec_results)
        nvd_knowledge = self._get_nvd_knowledge(cve_id, nvd_results)
        
        ground_truth_info = self._get_ground_truth_info(cve_id, ground_truth_data)
        
        samples = []
        
        before_sample_id = self._generate_sample_id(cve_id, "before", data_source)
        after_sample_id = self._generate_sample_id(cve_id, "after", data_source)
        
        before_sample = {
            "sample_id": before_sample_id,
            "cve_id": cve_id,
            "repository": repository,
            "cwe_list": cwe_list,
            "commit_hash": commit_hash,
            "code_type": "before",
            "data_source": data_source,
            "code_snippet": before_code,
            "code_context": code_context,
            "true_label": 1,
            "knowledge": self._merge_knowledge(vulspec_knowledge, nvd_knowledge),
            "ground_truth_info": ground_truth_info,
            "vulinstruct_dataset": True,
            "sample_pair_id": f"{cve_id}_{data_source}"
        }
        samples.append(before_sample)
        
        if after_code:
            after_sample = {
                "sample_id": after_sample_id,
                "cve_id": cve_id,
                "repository": repository,
                "cwe_list": cwe_list,
                "commit_hash": commit_hash,
                "code_type": "after",
                "data_source": data_source,
                "code_snippet": after_code,
                "code_context": code_context,
                "true_label": 0,
                "knowledge": self._merge_knowledge(vulspec_knowledge, nvd_knowledge),
                "ground_truth_info": ground_truth_info,
                "vulinstruct_dataset": True,
                "sample_pair_id": f"{cve_id}_{data_source}"
            }
            samples.append(after_sample)
        
        return samples
    
    def _load_exclude_100_data(self) -> List[Dict]:
        if self._exclude_100_data is not None:
            return self._exclude_100_data
        
        try:
            with open(self.exclude_100_path, 'r', encoding='utf-8') as f:
                self._exclude_100_data = json.load(f)
            self.logger.info(f"✅ Loaded exclude_100 data: {len(self._exclude_100_data)} items")
            return self._exclude_100_data
        except Exception as e:
            self.logger.error(f"❌ Failed to load exclude_100 data: {e}")
            return []
    
    def _load_subset_100_data(self) -> List[Dict]:
        if self._subset_100_data is not None:
            return self._subset_100_data
        
        try:
            with open(self.subset_100_path, 'r', encoding='utf-8') as f:
                self._subset_100_data = json.load(f)
            self.logger.info(f"✅ Loaded subset_100 data: {len(self._subset_100_data)} items")
            return self._subset_100_data
        except Exception as e:
            self.logger.error(f"❌ Failed to load subset_100 data: {e}")
            return []
    
    def _load_vulspec_results_319(self) -> Dict:
        if self._vulspec_results_319 is not None:
            return self._vulspec_results_319
        
        try:
            with open(self.vulspec_results_path, 'r', encoding='utf-8') as f:
                self._vulspec_results_319 = json.load(f)
            self.logger.info(f"✅ Loaded VulSpec results (319): {len(self._vulspec_results_319)} items")
            return self._vulspec_results_319
        except Exception as e:
            self.logger.error(f"❌ Failed to load VulSpec results (319): {e}")
            return {}
    
    def _load_vulspec_results_100(self) -> Dict:
        if self._vulspec_results_100 is not None:
            return self._vulspec_results_100
        
        try:
            with open(self.vulspec_results_100_path, 'r', encoding='utf-8') as f:
                self._vulspec_results_100 = json.load(f)
            self.logger.info(f"✅ Loaded VulSpec results (100): {len(self._vulspec_results_100)} items")
            return self._vulspec_results_100
        except Exception as e:
            self.logger.error(f"❌ Failed to load VulSpec results (100): {e}")
            return {}
    
    def _load_nvd_results_319(self) -> Dict:
        if self._nvd_results_319 is not None:
            return self._nvd_results_319
        
        try:
            with open(self.nvd_results_path, 'r', encoding='utf-8') as f:
                self._nvd_results_319 = json.load(f)
            self.logger.info(f"✅ Loaded NVD results (319): {len(self._nvd_results_319)} items")
            return self._nvd_results_319
        except Exception as e:
            self.logger.error(f"❌ Failed to load NVD results (319): {e}")
            return {}
    
    def _load_nvd_results_100(self) -> Dict:
        if self._nvd_results_100 is not None:
            return self._nvd_results_100
        
        try:
            with open(self.nvd_results_100_path, 'r', encoding='utf-8') as f:
                self._nvd_results_100 = json.load(f)
            self.logger.info(f"✅ Loaded NVD results (100): {len(self._nvd_results_100)} items")
            return self._nvd_results_100
        except Exception as e:
            self.logger.error(f"❌ Failed to load NVD results (100): {e}")
            return {}
    
    def _load_ground_truth_data(self) -> List[Dict]:
        if self._ground_truth_data is not None:
            return self._ground_truth_data
        
        try:
            with open(self.ground_truth_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._ground_truth_data = data.get("results", [])
            self.logger.info(f"✅ Loaded unified Ground Truth data: {len(self._ground_truth_data)} items")
            return self._ground_truth_data
        except Exception as e:
            self.logger.error(f"❌ Failed to load Ground Truth data: {e}")
            return []
    
    def _get_vulspec_knowledge(self, cve_id: str, vulspec_results: Dict) -> Dict:
        if not vulspec_results:
            return {"vulspec_cases": []}
        
        retrieval_results = vulspec_results.get("retrieval_results", {})
        
        for sample_id, result in retrieval_results.items():
            if isinstance(result, dict):
                sample_info = result.get("sample_info", {})
                if sample_info.get("cve_id") == cve_id:
                    cases = result.get("retrieval_results", [])[:10]
                    return {"vulspec_cases": cases}
        
        return {"vulspec_cases": []}
    
    def _get_nvd_knowledge(self, cve_id: str, nvd_results: Dict) -> Dict:
        if cve_id in nvd_results:
            nvd_data = nvd_results[cve_id]
            if isinstance(nvd_data, list):
                cases = nvd_data[:10]
                return {"nvd_cases": cases}
        return {"nvd_cases": []}
    
    def _get_ground_truth_info(self, cve_id: str, ground_truth_data: List[Dict]) -> Optional[Dict]:
        for item in ground_truth_data:
            if item.get("cve_id") == cve_id and item.get("code_type") == "before":
                gt_info = item.get("ground_truth_info", {})
                if gt_info:
                    return {
                        "cve_description": gt_info.get("cve_description", ""),
                        "commit_message": gt_info.get("commit_message", ""),
                        "commit_hash": gt_info.get("commit_hash", ""),
                        "code_diff": gt_info.get("code_diff", ""),
                        "filename": gt_info.get("filename", ""),
                        "diff_lines": gt_info.get("diff_lines", [])
                    }
        return None
    
    def _merge_knowledge(self, vulspec_knowledge: Dict, nvd_knowledge: Dict) -> Dict:
        specifications = []
        vulspec_cases = vulspec_knowledge.get("vulspec_cases", [])
        for case in vulspec_cases[:5]:
            case_data = case.get("case_data", case) if "case_data" in case else case
            specs = case_data.get("specifications", [])
            if isinstance(specs, list):
                specifications.extend(specs[:3])
        
        unique_specs = []
        seen = set()
        for spec in specifications:
            if spec not in seen and len(unique_specs) < 8:
                unique_specs.append(spec)
                seen.add(spec)
        
        merged = {
            "vulspec_cases": vulspec_cases,
            "nvd_cases": nvd_knowledge.get("nvd_cases", []),
            "specifications": unique_specs
        }
        return merged
    
    def _generate_sample_id(self, cve_id: str, code_type: str, data_source: str) -> str:
        return f"{cve_id}_{code_type}_{data_source}_vulinstruct"
    
    def get_dataset_statistics(self) -> Dict:
        if self._full_dataset_cache is None:
            self.load_full_detection_samples()
        
        samples = self._full_dataset_cache
        
        total_samples = len(samples)
        unique_cves = len(set(sample.get("cve_id") for sample in samples))
        before_samples = len([s for s in samples if s.get("code_type") == "before"])
        after_samples = len([s for s in samples if s.get("code_type") == "after"])
        
        exclude_100_samples = len([s for s in samples if s.get("data_source") == "exclude_100"])
        subset_100_samples = len([s for s in samples if s.get("data_source") == "subset_100"])
        
        vulspec_covered = len([s for s in samples if s.get("knowledge", {}).get("vulspec_cases")])
        nvd_covered = len([s for s in samples if s.get("knowledge", {}).get("nvd_cases")])
        ground_truth_covered = len([s for s in samples if s.get("ground_truth_info")])
        
        return {
            "dataset_version": "VulInstruct_dataset",
            "total_samples": total_samples,
            "unique_cves": unique_cves,
            "before_samples": before_samples,
            "after_samples": after_samples,
            "data_source_distribution": {
                "exclude_100": exclude_100_samples,
                "subset_100": subset_100_samples
            },
            "knowledge_coverage": {
                "vulspec_covered": vulspec_covered,
                "vulspec_coverage_rate": vulspec_covered / total_samples if total_samples > 0 else 0,
                "nvd_covered": nvd_covered,
                "nvd_coverage_rate": nvd_covered / total_samples if total_samples > 0 else 0,
                "ground_truth_covered": ground_truth_covered,
                "ground_truth_coverage_rate": ground_truth_covered / total_samples if total_samples > 0 else 0
            }
        }