# Knowledge Extraction Module

This module implements the core knowledge extraction pipelines for VulInstruct, constructing specification knowledge bases from historical vulnerability data.

## Overview

VulInstruct leverages two complementary knowledge extraction approaches to build a comprehensive understanding of security specifications:

1. **VulSpec Knowledge Extraction**: Our novel specification extraction method
2. **VUL-RAG Knowledge Extraction**: Baseline implementation for comparison

## Preprocessed Database

We provide preprocessed vulnerability data in the `CORRECT_database/` directory:

- `processed_train_dataset.json`: Training set containing historical CVE data with vulnerability and patch information
- `processed_test_dataset.json`: Test set for evaluation

Each entry in the database contains:
- CVE identification (CVE ID, CWE type)
- Repository and commit information
- Vulnerable code before the fix
- Patched code after the fix
- Code context and related functions
- Commit messages and CVE descriptions

## VulSpec Knowledge Extraction

### Implementation: `vul_spec_knowledge.py`

This script implements our specification extraction pipeline with two-stage processing:

#### Stage 1: Threat Modeling Analysis
Extracts three types of specifications from vulnerability-patch pairs:
- **HS-MEM**: Memory safety specifications
- **HS-STATE**: State consistency specifications  
- **HS-IO**: Input/Output validation specifications

#### Stage 2: Context-Aware Refinement
Enhances specifications with:
- Domain-specific context
- Code pattern recognition
- Security boundary analysis

### Usage

```bash
python vul_spec_knowledge.py \
    --input CORRECT_database/processed_train_dataset.json \
    --output output/vul_spec/ \
    --model gpt-4 \
    --api-keys path/to/api_keys.json \
    --batch-size 10 \
    --max-workers 5
```

### Output Format

The script generates structured specification knowledge in `output/vul_spec/`:

```json
{
  "CVE-2007-6761_0b29669c065f60501e7289e1950fa2a618962358": {
    "cve_id": "CVE-2007-6761",
    "repository": "torvalds/linux",
    "cwe_type": "CWE-119",
    "understand": "System identification and functional analysis",
    "classification": "Memory safety violation category",
    "specifications": [
      "HS-MEM-001: Memory allocation operations must ensure complete initialization",
      "HS-STATE-002: Reference counting mechanisms must maintain consistent state",
      "HS-IO-003: Video buffer management must enforce proper lifecycle tracking"
    ]
  }
}
```

## VUL-RAG Knowledge Extraction

### Implementation: `vul_rag_knowledge_commit.py`

This script extracts knowledge following the VUL-RAG methodology for baseline comparison. We maintain full compatibility with the official VUL-RAG implementation, including:
- Identical prompt templates
- Same knowledge document structure
- Consistent field naming conventions

### Usage

```bash
python vul_rag_knowledge_commit.py \
    --input CORRECT_database/processed_train_dataset.json \
    --output output/vul_rag/ \
    --model gpt-3.5-turbo \
    --api-keys path/to/api_keys.json
```

### Output Format

Generates VUL-RAG compatible knowledge in `output/vul_rag/`:

```json
{
  "CVE-2007-6761_0b29669c065f60501e7289e1950fa2a618962358": [
    {
      "vulnerability_behavior": {
        "preconditions_for_vulnerability": "...",
        "trigger_condition": "...",
        "specific_code_behavior_causing_vulnerability": "..."
      },
      "solution": {
        "general_fix_approach": "...",
        "specific_code_changes": [...],
        "defensive_measures": [...]
      },
      "GPT_purpose": "Code purpose description",
      "GPT_function": "Code functionality description",
      "code_before_change": "...",
      "code_after_change": "..."
    }
  ]
}
```

## Configuration

### API Configuration

Both extraction scripts support multiple LLM providers:

```python
# Example configuration in query_llm.py
API_CONFIG = {
    "openai": {
        "base_url": "https://api.openai.com/v1/",
        "models": ["gpt-4", "gpt-3.5-turbo"]
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1/",
        "models": ["deepseek-coder", "deepseek-reasoner"]
    },
    "claude": {
        "base_url": "https://api.anthropic.com/v1/",
        "models": ["claude-3-sonnet", "claude-3-opus"]
    }
}
```

### Parallel Processing

Both scripts support parallel processing for efficiency:

```bash
# Configure parallel workers
--max-workers 10  # Number of parallel API calls
--batch-size 50   # Batch size for processing
```

## Output Examples

### VulSpec Specification Example

```
HS-MEM-001: Memory allocation operations must ensure complete initialization of all critical fields
- Reasoning: Uninitialized count field → random values → resource leaks → mandatory initialization

HS-STATE-002: Reference counting mechanisms must maintain consistent state through initialization
- Reasoning: Reference counting corrupted by uninitialized values → requires atomic init-increment sequence
```

### VUL-RAG Knowledge Example

```json
{
  "preconditions_for_vulnerability": "Memory structure containing reference count is not properly initialized before use.",
  "trigger_condition": "An attacker with local access can exploit uninitialized memory to manipulate reference counting mechanisms.",
  "specific_code_behavior_causing_vulnerability": "The code increments a reference count field in a memory structure that was not properly initialized."
}
```

## Performance Optimization

### API Rate Limiting

The scripts implement intelligent rate limiting:
- Automatic retry with exponential backoff
- API key rotation for load balancing
- Request queuing and throttling

### Caching

Results are cached to avoid redundant API calls:
- Intermediate results saved after each batch
- Resume capability from checkpoints
- Deduplication of similar code patterns

## Extending the Pipeline

### Adding New Specification Types

To add custom specification categories:

1. Modify the classification taxonomy in `prompt_spec.py`
2. Update the extraction prompts
3. Add validation rules for the new specifications

### Custom Knowledge Formats

To implement alternative knowledge representations:

1. Inherit from the base extractor class
2. Override the `extract()` and `format_output()` methods
3. Register the new format in the output handler

## Troubleshooting

### Common Issues

1. **API Rate Limits**: Reduce `--max-workers` or add more API keys
2. **Memory Issues**: Reduce `--batch-size` for large datasets
3. **Incomplete Extraction**: Check `--resume` flag to continue from checkpoint

### Validation

Validate extracted knowledge quality:

```bash
python validate_knowledge.py \
    --knowledge-base output/vul_spec/ \
    --validation-set CORRECT_database/processed_test_dataset.json
```
