
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "configs"))

from vulinstruct_config import *


class PrimeVulDataLoader:
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("📊 PrimeVul data loader initialized successfully")
    
    def load_test_data(self) -> List[Dict[str, Any]]:
        test_file = TEST_DATA_PATH
        print(f"🧐 Loader is reading from: {test_file}")
        
        if not test_file.exists():
            self.logger.error(f"Testing data file does not exist: {test_file}")
            return []
        
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                samples = data
            elif isinstance(data, dict) and 'samples' in data:
                samples = data['samples']
            else:
                self.logger.error("Unrecognized testing data format")
                return []
            
            self.logger.info(f"✅ Loaded testing data: {len(samples)} samples")
            return samples
            
        except Exception as e:
            self.logger.error(f"Loading testing data failed: {e}")
            return []
    
    def load_train_data(self) -> List[Dict[str, Any]]:
        train_file = TRAIN_DATA_PATH
        
        if not train_file.exists():
            self.logger.error(f"Training data file does not exist: {train_file}")
            return []
        
        try:
            with open(train_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                samples = data
            elif isinstance(data, dict) and 'samples' in data:
                samples = data['samples']
            else:
                self.logger.error("Unrecognized training data format")
                return []
            
            self.logger.info(f"✅ Loaded training data: {len(samples)} samples")
            return samples
            
        except Exception as e:
            self.logger.error(f"Loading training data failed: {e}")
            return []
    
    def load_sample_by_cve_id(self, cve_id: str, data_type: str = "test") -> Optional[Dict[str, Any]]:
        if data_type == "test":
            samples = self.load_test_data()
        elif data_type == "train":
            samples = self.load_train_data()
        else:
            self.logger.error(f"Unsupported data type: {data_type}")
            return None
        
        for sample in samples:
            if sample.get('cve_id') == cve_id:
                return sample
        
        self.logger.warning(f"CVE {cve_id} not found in {data_type} data")
        return None
    
    def get_cwe_distribution(self, data_type: str = "test") -> Dict[str, int]:
        if data_type == "test":
            samples = self.load_test_data()
        elif data_type == "train":
            samples = self.load_train_data()
        else:
            return {}
        
        cwe_distribution = {}
        
        for sample in samples:
            cwe_list = sample.get('cwe_list', [])
            for cwe in cwe_list:
                cwe_distribution[cwe] = cwe_distribution.get(cwe, 0) + 1
        
        return dict(sorted(cwe_distribution.items(), key=lambda x: x[1], reverse=True))
    
    def filter_samples_by_cwe(self, cwe_types: List[str], data_type: str = "test") -> List[Dict[str, Any]]:
        if data_type == "test":
            samples = self.load_test_data()
        elif data_type == "train":
            samples = self.load_train_data()
        else:
            return []
        
        filtered_samples = []
        
        for sample in samples:
            sample_cwes = sample.get('cwe_list', [])
            if any(cwe in sample_cwes for cwe in cwe_types):
                filtered_samples.append(sample)
        
        self.logger.info(f"🔍 CWE filtering: {len(samples)} → {len(filtered_samples)} (CWE: {cwe_types})")
        return filtered_samples
    
    def get_data_statistics(self) -> Dict[str, Any]:
        test_samples = self.load_test_data()
        train_samples = self.load_train_data()
        
        test_cwe_dist = self.get_cwe_distribution("test")
        train_cwe_dist = self.get_cwe_distribution("train")
        
        return {
            'test_data': {
                'total_samples': len(test_samples),
                'cwe_distribution': test_cwe_dist,
                'unique_cwes': len(test_cwe_dist)
            },
            'train_data': {
                'total_samples': len(train_samples),
                'cwe_distribution': train_cwe_dist,
                'unique_cwes': len(train_cwe_dist)
            },
            'overall': {
                'total_samples': len(test_samples) + len(train_samples),
                'test_ratio': len(test_samples) / (len(test_samples) + len(train_samples)) if (len(test_samples) + len(train_samples)) > 0 else 0
            }
        }