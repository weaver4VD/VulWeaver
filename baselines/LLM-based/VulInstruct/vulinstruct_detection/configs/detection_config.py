
from pathlib import Path

MODULE_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = MODULE_ROOT.parent
PRIMEVUL_RETRIEVAL_ROOT = PROJECT_ROOT / "primevul_retrieval"
PRIMEVUL_VULSPEC_ROOT = PRIMEVUL_RETRIEVAL_ROOT

DATASET_PATH_MAPPING = {
    "primevul_vulspec_retrieval_results_exclude.json": 
        PRIMEVUL_RETRIEVAL_ROOT / "nvd" / "final_outputs" / "exclude_100" / "final_dataset_v4_complete" / "primevul_vulspec_retrieval_results_exclude_0129.json",
    
    "historical_samples_merged_v4_complete_20250822_203454.json":
        PRIMEVUL_RETRIEVAL_ROOT / "nvd" / "final_outputs" / "exclude_100" / "final_dataset_v4_complete" / "nvd_retrieval_results_nocwe_20260128_162444.json",
    
    "primevul_vulspec_retrieval_results.json":
        PRIMEVUL_RETRIEVAL_ROOT / "nvd" / "final_outputs" / "subset_100" / "final_dataset" / "primevul_vulspec_retrieval_results0119.json",
    
    "historical_samples_top10_20250818_041337.json":
        PRIMEVUL_RETRIEVAL_ROOT / "nvd" / "final_outputs" / "subset_100" / "final_dataset" / "nvd_retrieval_results_nocwe_20260114_162601.json",
    
    "primevul_full_exclude_100.json":
        PRIMEVUL_VULSPEC_ROOT / "data" / "primevul_full_exclude_100.json",
    
    "primevul_subset_100.json":
        PRIMEVUL_VULSPEC_ROOT / "data" / "primevul_subset_100.json"
}

ABLATION_CONFIGS = {
    "full": {
        "vulspec_threshold": 8,
        "nvd_threshold": 8, 
        "spec_threshold": 8,
    },
    "no_nvd": {
        "vulspec_threshold": 8,
        "nvd_threshold": 11,
        "spec_threshold": 8,
    },
    "no_specification": {
        "vulspec_threshold": 8,
        "nvd_threshold": 8,
        "spec_threshold": 11,
    },
    "no_vulspec": {
        "vulspec_threshold": 11,
        "nvd_threshold": 8,
        "spec_threshold": 8,
    },
    "baseline": {
        "vulspec_threshold": 11,
        "nvd_threshold": 11,
        "spec_threshold": 11,
    }
}

MODEL_CONFIGS = {
    "deepseek-v3": {
        "name": "DeepSeek V3",
        "detection_model": "deepseek-v3",
        "evaluation_model": "gpt-5", 
        "scoring_model": "deepseek-v3",
        "description": "detection model configuring"
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "detection_model": "gpt-4o",
        "evaluation_model": "gpt-5",
        "scoring_model": "deepseek-v3",
        "description": "GPT-4o detection configuring"
    }
}

EXPERIMENT_RESULTS = {
    "main_results": {
        "deepseek_v3_full": MODULE_ROOT / "results" / "detection_outputs" / "full_results" / "two_stage_v15_full_dataset_results_20250827_185231.json",
        "cached_detection_full": MODULE_ROOT / "results" / "detection_outputs" / "full_results" / "cached_detection_results_20250905_203223.json"
    },
    
    "ablation_results": {
        "no_nvd": MODULE_ROOT / "results" / "detection_outputs" / "ablation_no_nvd" / "cached_detection_results_20250906_115916.json",
        "no_specification": MODULE_ROOT / "results" / "detection_outputs" / "ablation_no_specification" / "cached_detection_results_20250906_132114.json"
    },
    
    "evaluation_reports": {
        "full_report": MODULE_ROOT / "results" / "evaluation_reports" / "single_file_evaluation_report_cached_detection_results_20250905_203223_20250905_204955.md",
        "no_nvd_report": MODULE_ROOT / "results" / "evaluation_reports" / "single_file_evaluation_report_cached_detection_results_20250906_115916_20250906_120749.md"
    }
}

RUN_CONFIGS = {
    "development": {
        "max_workers": 10,
        "test_samples": 100,
        "use_cache": True
    },
    "production": {
        "max_workers": 20,
        "test_samples": None,
        "use_cache": True
    },
    "quick_test": {
        "max_workers": 5,
        "test_samples": 10,
        "use_cache": True
    }
}

OUTPUT_CONFIGS = {
    "results_dir": MODULE_ROOT / "results",
    "detection_outputs_dir": MODULE_ROOT / "results" / "detection_outputs",
    "evaluation_reports_dir": MODULE_ROOT / "results" / "evaluation_reports",
    "logs_dir": MODULE_ROOT / "logs",
    "cache_dir": MODULE_ROOT / "cache"
}

def get_ablation_config(ablation_name: str) -> dict:
    if ablation_name not in ABLATION_CONFIGS:
        raise ValueError(f"Unknown ablation config: {ablation_name}. Available: {list(ABLATION_CONFIGS.keys())}")
    return ABLATION_CONFIGS[ablation_name]

def get_model_config(model_name: str) -> dict:
    if model_name not in MODEL_CONFIGS:
        raise ValueError(f"Unknown model config: {model_name}. Available: {list(MODEL_CONFIGS.keys())}")
    return MODEL_CONFIGS[model_name]

def get_mapped_path(original_filename: str) -> Path:
    if original_filename not in DATASET_PATH_MAPPING:
        raise ValueError(f"No mapping found for: {original_filename}")
    
    mapped_path = DATASET_PATH_MAPPING[original_filename]
    if not mapped_path.exists():
        raise FileNotFoundError(f"Mapped file does not exist: {mapped_path}")
    
    return mapped_path

def validate_paths() -> bool:
    missing_paths = []
    
    for filename, path in DATASET_PATH_MAPPING.items():
        if not path.exists():
            missing_paths.append(f"{filename} -> {path}")
    
    if missing_paths:
        print("❌ Missing paths:")
        for missing in missing_paths:
            print(f"   {missing}")
        return False
    
    print("✅ All data paths validated successfully!")
    return True

def create_output_directories():
    for config_name, path in OUTPUT_CONFIGS.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {path}")

if __name__ == "__main__":
    print("🔧 VulInstruct Detection Module Configuration")
    print("=" * 60)
    
    print(f"📂 Module Root: {MODULE_ROOT}")
    print(f"📂 PrimeVul Retrieval: {PRIMEVUL_RETRIEVAL_ROOT}")
    print(f"📂 PrimeVul VulSpec: {PRIMEVUL_VULSPEC_ROOT}")
    
    print(f"\n📋 Available Ablation Configs: {list(ABLATION_CONFIGS.keys())}")
    print(f"📋 Available Model Configs: {list(MODEL_CONFIGS.keys())}")
    
    print(f"\n🔍 Validating data paths...")
    validate_paths()
    
    print(f"\n📁 Creating output directories...")
    create_output_directories()
    
    print(f"\n✅ Configuration validation complete!")