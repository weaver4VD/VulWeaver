
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "configs"))
from detection_config import DATASET_PATH_MAPPING, get_mapped_path

class PathAdapter:
    
    def __init__(self):
        self.path_mapping = DATASET_PATH_MAPPING
    
    def adapt_vulspec_path(self, original_path: str) -> Path:
        if "primevul_vulspec_retrieval_results_319.json" in original_path:
            return get_mapped_path("primevul_vulspec_retrieval_results_exclude.json")
        elif "primevul_vulspec_retrieval_results.json" in original_path:
            return get_mapped_path("primevul_vulspec_retrieval_results.json")
        else:
            filename = Path(original_path).name
            if filename in self.path_mapping:
                return get_mapped_path(filename)
            else:
                return Path(original_path)
    
    def adapt_nvd_path(self, original_path: str) -> Path:
        if "historical_samples_merged_v4_complete_20250822_203454.json" in original_path:
            return get_mapped_path("historical_samples_merged_v4_complete_20250822_203454.json")
        elif "historical_samples_top10_20250818_041337.json" in original_path:
            return get_mapped_path("historical_samples_top10_20250818_041337.json")
        else:
            filename = Path(original_path).name
            if filename in self.path_mapping:
                return get_mapped_path(filename)
            else:
                return Path(original_path)
    
    def adapt_base_data_path(self, original_path: str) -> Path:
        if "primevul_full_exclude_100.json" in original_path:
            return get_mapped_path("primevul_full_exclude_100.json")
        elif "primevul_subset_100.json" in original_path:
            return get_mapped_path("primevul_subset_100.json")
        else:
            return Path(original_path)
    
    def adapt_any_path(self, original_path: str) -> Path:
        original_path_obj = Path(original_path)
        filename = original_path_obj.name
        
        if filename in self.path_mapping:
            return get_mapped_path(filename)
        
        if "319" in filename:
            new_filename = filename.replace("319", "exclude")
            if new_filename in self.path_mapping:
                return get_mapped_path(new_filename)
        
        return original_path_obj

path_adapter = PathAdapter()

def adapt_path(original_path: str) -> Path:
    return path_adapter.adapt_any_path(original_path)

def patch_v15_loader_paths():
    pass

if __name__ == "__main__":
    test_paths = [
        "/old/path/primevul_vulspec_retrieval_results_319.json",
        "/old/path/historical_samples_merged_v4_complete_20250822_203454.json",
        "/old/path/primevul_full_exclude_100.json"
    ]
    
    print("🔧 Path Adapter Test")
    print("=" * 50)
    
    for original in test_paths:
        adapted = adapt_path(original)
        print(f"Original: {original}")
        print(f"Adapted:  {adapted}")
        print(f"Exists:   {adapted.exists()}")
        print()