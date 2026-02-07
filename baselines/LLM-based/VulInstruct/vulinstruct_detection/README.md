**Important Notes**: 
- Stage1 is VulInstruct vulnerability detection, Stage2 is our CORRECT evaluation method
- The "subset_100" dataset refers to 100 randomly selected cases specifically chosen for knowledge scoring validation and experimental consistency
- The "exclude_100" dataset contains the remaining 319 cases for comprehensive evaluation


# VulInstruct Detection Module

VulInstruct detection module, a knowledge-enhanced two-stage vulnerability detection system that supports combined use and ablation experiments of three knowledge sources: VulSpec, NVD, and Specification.

## 🎯 Module Overview

VulInstruct Detection is a complete vulnerability detection experimental framework that includes:

- **Two-Stage Detection Architecture**: Stage1 vulnerability detection + Stage2 match prediction
- **Three Knowledge Sources**: Specification + VulSpec (Vulnerability Detailed Cases) + NVD historical vulnerabilities (for dynamically summarizing domain-specific specifications)
- **Ablation Experiment Support**: Elegant disabling of knowledge sources through threshold control
- **Cache Consistency**: Pre-built knowledge scoring cache ensures experimental reproducibility
- **Complete Evaluation System**: End-to-end metric calculation from detection to evaluation

## 🏗️ Architecture Design

### Core Components

```
vulinstruct_detection/
├── core/                          # Core detection engine
│   ├── data_loaders/             # Data loaders
│   │   ├── vulinstruct_dataset_loader.py    # VulInstruct complete dataset loader
│   │   └── path_adapter.py               # Path adapter
│   ├── detectors/                # Detector components
│   │   ├── cached_detection_runner.py    # Cached detection runner
│   │   └── vulinstruct_two_stage_detector.py  # VulInstruct two-stage detector
│   ├── evaluators/               # Evaluators
│   │   └── single_file_evaluator.py      # Single file evaluator
│   └── knowledge_systems/        # Knowledge systems
│       └── knowledge_scoring_builder.py  # Knowledge scoring builder
├── experiments/                  # Experiment scripts
│   ├── main_runners/            # Main runners
│   │   └── vulinstruct_test_runner.py
│   └── evaluation_scripts/      # Evaluation scripts
├── results/                     # Experiment results
│   ├── detection_outputs/       # Detection outputs
│   │   ├── full_results/       # Complete detection results
│   │   ├── ablation_no_nvd/    # No-NVD ablation results
│   │   └── ablation_no_specification/  # No-Specification ablation results
│   └── evaluation_reports/      # Evaluation reports
└── configs/                     # Configuration files
    └── detection_config.py      # Main configuration file
```

## 📊 Baseline Comparison Framework

For comprehensive model performance comparison, see our **Different Model Experimental Framework**:

- **Location**: `different_model/` directory
- **Purpose**: Compare COT baseline vs VulInstruct-enhanced detection across different models
- **Documentation**: See `different_model/README.md` for detailed experimental design and usage

### Data Flow Architecture

```
PrimeVul Dataset → Knowledge Retrieval(VulSpec/NVD/Spec) → Two-Stage Detection → Evaluation Metrics
     ↓              ↓                                       ↓                    ↓
 subset_100/    Retrieval Result Cache                   Stage1+Stage2        Precision/
 exclude_100    (Consistency Guarantee)                  Vuln+Match Prediction  Recall/F1
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Check data path mapping
python configs/detection_config.py

# Verify all dependency files
cd ../primevul_retrieval/nvd && python verify_module.py
```

### 2. Build Knowledge Scoring Cache

```bash
# Build consistency cache (ensure experimental reproducibility)
python core/knowledge_systems/knowledge_scoring_builder.py \
    --workers 20 \
    --model-score deepseek-chat
```

### 3. Run Complete Detection

```bash
# Main detection experiment
python core/detectors/cached_detection_runner.py \
    --workers 10 \
    --model-name "deepseek-chat" \
    --model-eval-name "deepseek-chat" \
    --vulspec-threshold 8 \
    --nvd-threshold 8 \
    --spec-threshold 8
```

### 4. Ablation Experiments

```bash
# Ablate NVD knowledge (set nvd_threshold=11 > 10)
python core/detectors/cached_detection_runner.py \
    --workers 10 --samples 100 \
    --model-name "deepseek-v3" --model-eval-name "gpt-5" \
    --vulspec-threshold 8 --nvd-threshold 11 --spec-threshold 8

# Ablate Specification knowledge (set spec_threshold=11 > 10)
python core/detectors/cached_detection_runner.py \
    --workers 10 --samples 100 \
    --model-name "deepseek-v3" --model-eval-name "gpt-5" \
    --vulspec-threshold 8 --nvd-threshold 8 --spec-threshold 11
```

### 5. Evaluate Results

```bash
# Evaluate detection results
python core/evaluators/single_file_evaluator.py \
    --file "results/detection_outputs/full_results/cached_detection_results_20250905_203223.json"
```

## 🔧 Core Features

### 1. Intelligent Path Mapping

The detection module automatically maps original paths to `primevul_retrieval` structure:

```python
# Automatic path mapping
"primevul_vulspec_retrieval_results_exclude.json" 
  → "../primevul_retrieval/nvd/final_outputs/exclude_100/final_dataset_v4_complete/"

"historical_samples_merged_v4_complete_20250822_203454.json"
  → "../primevul_retrieval/nvd/final_outputs/exclude_100/final_dataset_v4_complete/"
```

### 2. Ablation Experiment Mechanism

Elegant disabling of knowledge sources through threshold control:

```python
# Ablation experiment configuration
ABLATION_CONFIGS = {
    "full": {"vulspec_threshold": 8, "nvd_threshold": 8, "spec_threshold": 8},
    "no_nvd": {"vulspec_threshold": 8, "nvd_threshold": 11, "spec_threshold": 8},
    "no_specification": {"vulspec_threshold": 8, "nvd_threshold": 8, "spec_threshold": 11}
}
```

### 3. Cache Consistency Guarantee

- **Knowledge Scoring Cache**: Pre-built scoring ensures 100% consistency
- **Experimental Reproducibility**: Same input produces same results
- **Concurrency Safety**: Supports multi-worker parallel processing

### 4. Two-Stage Detection Architecture

```python
# Stage 1: Vulnerability Detection
vulnerability_prediction: 0/1 (whether vulnerability exists)
confidence: float (confidence score)

# Stage 2: Match Prediction  
match_result: MATCH/MISMATCH/CORRECT/FALSE_ALARM
match_confidence: float (match confidence)
```

## 📊 Experimental Results

### Main Detection Results

| Model | Configuration | File | Description |
|------|------|------|------|
| DeepSeek-V3 | Full Knowledge | `cached_detection_results_20250905_203223.json` | Main detection results |
| DeepSeek-V3 | No NVD (Domain-specific) | `cached_detection_results_20250906_115916.json` | NVD ablation experiment |
| DeepSeek-V3 | No Specification (General) | `cached_detection_results_20250906_132114.json` | Specification ablation experiment |

### Evaluation Reports

- **Full Detection Report**: `single_file_evaluation_report_cached_detection_results_20250905_203223_20250905_204955.md`
- **NVD Ablation Report**: `single_file_evaluation_report_cached_detection_results_20250906_115916_20250906_120749.md`

## ⚙️ Configuration

### Main Parameters

```python
# Model Configuration
--model-name "deepseek-v3"      # Main detection model
--model-eval-name "gpt-5"       # Evaluation model
--model-score-name "deepseek-v3" # Knowledge scoring model

# Knowledge Thresholds (Key for ablation experiments)
--vulspec-threshold 8           # VulSpec knowledge threshold
--nvd-threshold 8              # NVD knowledge threshold  
--spec-threshold 8             # Specification knowledge threshold

# Runtime Configuration
--workers 10                   # Number of concurrent workers
--samples 100                  # Number of test samples (None=full dataset)
```

### Threshold Ablation Mechanism

- **Normal Usage**: Threshold = 8 (standard knowledge filtering)
- **Ablation Disable**: Threshold = 11 (much greater than 10, effectively disables the knowledge source)
- **Baseline Mode**: All thresholds = 11 (no knowledge enhancement)

## 🔬 Experimental Workflow

### Complete Experimental Process

1. **Data Preparation**: Ensure `primevul_retrieval` data is complete
2. **Cache Building**: Build knowledge scoring cache
3. **Main Experiment**: Run full knowledge-enhanced detection
4. **Ablation Experiments**: Disable each knowledge source separately
5. **Results Evaluation**: Calculate various metrics
6. **Comparative Analysis**: Analyze ablation effects

### Batch Experiment Script

```bash
# Create batch experiment script
cat > run_all_experiments.sh << 'EOF'
#!/bin/bash

# 1. Build cache
python core/knowledge_systems/knowledge_scoring_builder.py --workers 30 --samples 200 --model-score deepseek-v3

# 2. Full detection
python core/detectors/cached_detection_runner.py --workers 10 --samples 100 --model-name "deepseek-v3" --model-eval-name "gpt-5" --vulspec-threshold 8 --nvd-threshold 8 --spec-threshold 8

# 3. NVD ablation
python core/detectors/cached_detection_runner.py --workers 10 --samples 100 --model-name "deepseek-v3" --model-eval-name "gpt-5" --vulspec-threshold 8 --nvd-threshold 11 --spec-threshold 8

# 4. Specification ablation  
python core/detectors/cached_detection_runner.py --workers 10 --samples 100 --model-name "deepseek-v3" --model-eval-name "gpt-5" --vulspec-threshold 8 --nvd-threshold 8 --spec-threshold 11

echo "✅ All experiments completed!"
EOF

chmod +x run_all_experiments.sh
./run_all_experiments.sh
```

## 🐛 Troubleshooting

### Common Issues

1. **Path Mapping Failure**
   ```bash
   # Check path mapping
   python configs/detection_config.py
   ```

2. **Missing Data Files**
   ```bash
   # Verify data integrity
   cd ../primevul_retrieval/nvd && python verify_module.py
   ```

3. **API Rate Limiting**
   ```bash
   # Reduce concurrency
   --workers 5
   ```

4. **Insufficient Memory**
   ```bash
   # Reduce sample count
   --samples 50
   ```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Small-scale testing
python core/detectors/cached_detection_runner.py --workers 2 --samples 5 --model-name "deepseek-v3"
```