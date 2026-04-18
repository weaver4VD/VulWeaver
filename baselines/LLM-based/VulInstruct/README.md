## Framework Overview

VulInstruct is a large and complex framework that systematically extracts reusable security specifications from historical vulnerabilities to guide the detection of new ones. Due to the scope and modularity of our approach, we have organized our code and implementations across different directories, each focusing on specific components of the framework.

## Repository Structure

Our repository has been restructured to provide clear separation of concerns and ease of navigation. Below is the current organization:

```
VulInstruct/
├── vulinstruct_detection/          # Main VulInstruct detection implementation
├── baseline/                       # Baseline method implementations
│   ├── agent-based/               # Multi-agent methods (GPTLens, VulTrial)
│   ├── vul-rag/                   # VUL-RAG baseline implementation
│   └── revd/                      # REVD baseline implementation
├── knowledge_extraction/           # Knowledge extraction pipelines
├── primevul_retrieval/            # PrimeVul dataset retrieval system
├── automatic_context_extraction_tool/  # Context extraction utilities
└── requirement.txt                # Project dependencies
```


## Component Documentation

Each major component of our framework includes detailed documentation and implementation guides. You can access specific information by visiting the README files in the corresponding directories:

### Core VulInstruct Implementation
- **VulInstruct Detection**: [`vulinstruct_detection/README.md`](vulinstruct_detection/README.md) - Main detection system with two-stage architecture and knowledge enhancement

### Knowledge Systems  
- **Knowledge Extraction**: [`knowledge_extraction/README.md`](knowledge_extraction/README.md) - general and domain-specific knowledge extraction pipelines
- **PrimeVul Retrieval**: [`primevul_retrieval/README.md`](primevul_retrieval/README.md) - Comprehensive retrieval system for vulnerability knowledge

### Baseline Methods
- **Agent-Based Methods**: [`baseline/agent-based/README.md`](baseline/agent-based/README.md) - GPTLens and VulTrial implementations
- **VUL-RAG Baseline**: [`baseline/vul-rag/README.md`](baseline/vul-rag/README.md) - Knowledge-enhanced RAG comparison method
- **REVD Baseline**: [`baseline/revd/README.md`](baseline/revd/README.md) - Representation learning baseline

### Utilities
- **Context Extraction**: [`automatic_context_extraction_tool/README.md`](automatic_context_extraction_tool/README.md) - Automated code context extraction tools

## Requirements

The framework requires Python 3.8+ and various dependencies. For detailed requirements, please refer to [`requirement.txt`](requirement.txt).

### Additional Tools for Context Extraction
- **Joern**: Version 4.0.332
- **cflow**: Version 1.6

### API Access Requirements
- LLM API access (OpenAI GPT-4/GPT-5, Claude, DeepSeek, or Qwen)
- API configuration in [`vulinstruct_detection/configs/vulinstruct_config.py`](vulinstruct_detection/configs/vulinstruct_config.py):
  - Update `OPENAI_API_KEYS` with your API keys
  - Configure `OPENAI_API_BASE` for your API endpoint  
  - Set `OPENAI_MODEL` to your preferred model
  - Ensure configuration supports OpenAI-compatible API calls
- Alternatively, specify models at runtime while ensuring config has valid `api_base` and `api_keys`


## Getting Started

**Getting Started**: Begin by exploring the [`vulinstruct_detection/README.md`](vulinstruct_detection/README.md) for the main VulInstruct implementation, then navigate to specific component directories based on your research interests.