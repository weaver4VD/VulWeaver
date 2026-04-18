"""
Merge stage1 and stage2 result files from knowledge extraction
Supports merging of train and test data
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)


class DataUtils:
    @staticmethod
    def load_json(path: str) -> Any:
        """Load JSON file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load file {path}: {e}")
            return {}
    
    @staticmethod
    def save_json(path: str, data: Any):
        """Save JSON file"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info(f"File saved successfully: {path}")
        except Exception as e:
            logging.error(f"Failed to save file {path}: {e}")


class StageResultsMerger:
    """Merge stage1 and stage2 results"""
    
    def __init__(self):
        self.base_path = str(Path(__file__).parent / "output")
    
    def merge_stages(self, stage1_path: str, stage2_path: str, output_path: str, 
                    data_type: str = "unknown"):
        """
        Merge stage1 and stage2 results
        
        Args:
            stage1_path: Stage1 result file path
            stage2_path: Stage2 result file path
            output_path: Output file path
            data_type: Data type (train/test)
        """
        logging.info(f"Starting to merge stage1 and stage2 results for {data_type} data...")
        if not Path(stage1_path).exists():
            logging.warning(f"Stage1 file does not exist: {stage1_path}")
            return False
        
        if not Path(stage2_path).exists():
            logging.warning(f"Stage2 file does not exist: {stage2_path}")
            return False
        stage1_data = DataUtils.load_json(stage1_path)
        stage2_data = DataUtils.load_json(stage2_path)
        
        if not stage1_data:
            logging.warning(f"Stage1 data is empty: {stage1_path}")
        
        if not stage2_data:
            logging.warning(f"Stage2 data is empty: {stage2_path}")
        merged_data = self._merge_stage_data(stage1_data, stage2_data)
        DataUtils.save_json(output_path, merged_data)
        stage1_count = len(stage1_data) if isinstance(stage1_data, dict) else 0
        stage2_count = len(stage2_data) if isinstance(stage2_data, dict) else 0
        merged_count = len(merged_data) if isinstance(merged_data, dict) else 0
        
        logging.info(f"{data_type} data merge statistics:")
        logging.info(f"  Stage1 item count: {stage1_count}")
        logging.info(f"  Stage2 item count: {stage2_count}")
        logging.info(f"  Merged item count: {merged_count}")
        
        return True
    
    def _merge_stage_data(self, stage1_data: Dict, stage2_data: Dict) -> Dict:
        """
        Merge stage1 and stage2 data
        
        Args:
            stage1_data: Stage1 data
            stage2_data: Stage2 data
        
        Returns:
            Merged data
        """
        merged_data = {}
        for key, value in stage1_data.items():
            merged_data[key] = value
        for key, value in stage2_data.items():
            if key in merged_data:
                if isinstance(merged_data[key], list) and isinstance(value, list):
                    merged_data[key].extend(value)
                elif isinstance(merged_data[key], dict) and isinstance(value, dict):
                    merged_data[key].update(value)
                else:
                    merged_data[key] = value
                    logging.debug(f"Overwriting key: {key}")
            else:
                merged_data[key] = value
        
        return merged_data
    
    def merge_train_data(self):
        """Merge stage1 and stage2 of training data"""
        stage1_path = os.path.join(self.base_path, "train_stage1_results.json")
        stage2_path = os.path.join(self.base_path, "train_stage2_results.json")
        output_path = os.path.join(self.base_path, "vul_rag_train_knowledge_merged.json")
        
        return self.merge_stages(stage1_path, stage2_path, output_path, "train")
    
    def merge_test_data(self):
        """Merge stage1 and stage2 of test data"""
        stage1_path = os.path.join(self.base_path, "test_stage1_results.json")
        stage2_path = os.path.join(self.base_path, "test_stage2_results.json")
        output_path = os.path.join(self.base_path, "vul_rag_test_knowledge_merged.json")
        
        return self.merge_stages(stage1_path, stage2_path, output_path, "test")
    
    def merge_vulspec_data(self):
        """Merge VulSpec-related stage results"""
        success_count = 0
        train_stage1 = os.path.join(self.base_path, "vul_spec_train_stage1_results.json")
        train_stage2 = os.path.join(self.base_path, "vul_spec_train_stage2_results.json")
        train_output = os.path.join(self.base_path, "vul_spec_train_merged.json")
        
        if Path(train_stage1).exists() and Path(train_stage2).exists():
            logging.info(f"Merging VulSpec training data: {os.path.basename(train_stage1)} + {os.path.basename(train_stage2)}")
            if self.merge_stages(train_stage1, train_stage2, train_output, "vul_spec_train"):
                success_count += 1
        else:
            logging.warning(f"VulSpec training data files incomplete:")
            logging.warning(f"  Stage1 exists: {Path(train_stage1).exists()}")
            logging.warning(f"  Stage2 exists: {Path(train_stage2).exists()}")
        test_stage1 = os.path.join(self.base_path, "vul_spec_test_stage1_results.json")
        test_stage2 = os.path.join(self.base_path, "vul_spec_test_stage2_results.json")
        test_output = os.path.join(self.base_path, "vul_spec_test_merged.json")
        
        if Path(test_stage1).exists() and Path(test_stage2).exists():
            logging.info(f"Merging VulSpec test data: {os.path.basename(test_stage1)} + {os.path.basename(test_stage2)}")
            if self.merge_stages(test_stage1, test_stage2, test_output, "vul_spec_test"):
                success_count += 1
        else:
            logging.warning(f"VulSpec test data files incomplete:")
            logging.warning(f"  Stage1 exists: {Path(test_stage1).exists()}")
            logging.warning(f"  Stage2 exists: {Path(test_stage2).exists()}")
        
        if success_count > 0:
            logging.info(f"Successfully merged {success_count} VulSpec datasets")
            return True
        else:
            logging.warning("Failed to merge any VulSpec data")
            return False
    
    def check_available_files(self):
        """Check available files"""
        logging.info("Checking available stage result files...")
        
        stage_files = []
        for file_path in Path(self.base_path).glob("*stage*.json"):
            stage_files.append(str(file_path))
        
        if not stage_files:
            logging.warning("No stage result files found")
            return []
        stage_files.sort()
        
        logging.info("Found stage files:")
        for file_path in stage_files:
            file_size = Path(file_path).stat().st_size
            logging.info(f"  {os.path.basename(file_path)} ({file_size} bytes)")
        
        return stage_files
    
    def merge_all_available(self):
        """Merge all available stage files"""
        available_files = self.check_available_files()
        
        if not available_files:
            logging.error("No mergeable files found")
            return False
        logging.info("\n=== Merging Training Data ===")
        train_success = self.merge_train_data()
        logging.info("\n=== Merging Test Data ===")
        test_success = self.merge_test_data()
        logging.info("\n=== Merging VulSpec Data ===")
        vulspec_success = self.merge_vulspec_data()
        
        return train_success or test_success or vulspec_success


def main():
    """Main function"""
    print("=== Knowledge Extraction Result Merge Tool ===")
    
    merger = StageResultsMerger()
    available_files = merger.check_available_files()
    
    if not available_files:
        print("Error: No stage result files found")
        return
    
    print(f"\nFound {len(available_files)} stage files")
    success = merger.merge_all_available()
    
    if success:
        print("\n✅ Merge completed!")
        print("Merged files saved in knowledge_extraction/output/ directory")
        output_dir = merger.base_path
        merged_files = list(Path(output_dir).glob("*merged*.json"))
        
        if merged_files:
            print("\nGenerated merged files:")
            for file_path in merged_files:
                file_size = file_path.stat().st_size
                print(f"  📄 {file_path.name} ({file_size} bytes)")
        
    else:
        print("\n❌ Merge failed, please check file paths and formats")


if __name__ == "__main__":
    main()