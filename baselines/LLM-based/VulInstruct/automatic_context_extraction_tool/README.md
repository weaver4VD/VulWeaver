# PrimeVul Automatic Context Extraction Tool

> **Note**: The `downloaded_repos/` directory is not uploaded to this repository due to its large size. We have uploaded the successfully extracted context files in `VulInstruct/automatic_context_extraction_tool/primevul_with_context`.

An automatic context extraction toolchain for PrimeVul vulnerability data based on improvements to the CORRECT framework, designed to automatically extract code context information for vulnerability fixes from Git repositories.

## 📁 Directory Structure

```
automatic_context_extraction_tool/
├── README.md                          # This file: tool documentation
├── scripts/                           # Core scripts
│   ├── url_parser.py                 # URL parser
│   ├── batch_cloner.py               # Batch repository cloner
│   ├── run_batch_clone.sh            # Batch clone script
│   ├── bfs.scala                     # BFS code analysis based on CORRECT
│   ├── get_methods.scala             # Method extraction tool based on CORRECT
│   ├── primevul_context_generator.py # PrimeVul context generator
│   ├── create_complete_dataset.py    # Complete dataset creation tool
│   └── batch_process_correct.py      # Batch processing tool
├── primevul_with_context/             # PrimeVul data with context
│   └── primevul_zh_format_complete.json  # Final complete dataset
└── downloaded_repos/                  # Repository download directory (placeholder)
    ├── github.com/                   # GitHub repositories
    ├── git.kernel.org/               # Kernel repositories
    └── other_repos/                  # Other repositories
```

## 🎯 Toolchain Overview

We developed a complete PrimeVul context extraction toolchain based on the CORRECT framework, which includes:

1. **URL Parsing and Conversion**: Support for various Git hosting platform URL formats
2. **Batch Repository Download**: Automatic download and management of Git repositories
3. **Code Context Analysis**: BFS and method extraction based on CORRECT
4. **Dataset Generation**: Generate complete PrimeVul dataset with context

## 🔧 Core Components

### 1. URL Parser (`url_parser.py`)

**Functionality**: Parse and standardize various Git repository URL formats

**Supported URL Formats**:

```python
# GitHub format
https://github.com/torvalds/linux/commit/abc123def456

# GitWeb format
https://git.kernel.org/?p=linux/kernel/git/torvalds/linux.git;a=commit;h=abc123def456

# CGit format
https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=abc123def456

# GitLab format
https://gitlab.com/user/repo/-/commit/abc123def456

# GNOME format
https://browse.gnome.org/repo/commit/?id=abc123def456
```

**Core Logic**:
```python
def parse_url(commit_url):
    """
    Parse commit URL and extract repository information
    
    Returns:
        {
            'host': 'github.com',
            'user': 'torvalds', 
            'repo': 'linux',
            'commit': 'abc123def456',
            'clone_url': 'https://github.com/torvalds/linux.git'
        }
    """
```

### 2. Batch Repository Cloner (`batch_cloner.py`)

**Functionality**: Batch clone Git repositories based on parsed URL information

**Workflow**:
1. Read commit URLs from PrimeVul data
2. Parse URLs using `url_parser.py`
3. Organize download directory by domain and user
4. Batch clone repositories locally
5. Record clone status and statistics

**Key Features**:
- ✅ **Resume Support**: Continue downloading after interruption
- ✅ **Progress Display**: Real-time clone progress
- ✅ **Status Recording**: Record success/failure status
- ✅ **Disk Management**: Check disk space to avoid insufficient space

**Example Usage**:
```bash
cd scripts/
# Dry run to analyze repositories to download
python batch_cloner.py --input primevul_data.json --dry-run

# Actual download
python batch_cloner.py --input primevul_data.json --output ../downloaded_repos/
```

### 3. Code Analysis Tools

Scala tools modified based on the CORRECT framework:

#### **Breadth-First Search** (`bfs.scala`)
- Improved BFS algorithm based on CORRECT
- Analyzes code dependencies and call chains
- Supports cross-function and cross-file context analysis

#### **Method Extraction Tool** (`get_methods.scala`)
- Method extraction logic based on CORRECT
- Identifies and extracts relevant function definitions
- Analyzes function call relationships and data flow

### 4. Context Generator (`primevul_context_generator.py`)

**Functionality**: Integrate all tools to generate PrimeVul data with code context

**Processing Flow**:
1. Read original PrimeVul data
2. For each CVE sample:
   - Parse commit URL
   - Locate locally cloned repository
   - Execute Scala analysis tools to extract context
   - Generate enhanced data entry
3. Output complete context dataset

## 🚀 Complete Workflow

### Step 1: URL Parsing and Repository Download

```bash
cd scripts/

# 1. Parse all URLs from PrimeVul data
python url_parser.py --input ../primevul_with_context/primevul_original.json --output parsed_urls.json

# 2. Batch clone repositories (placeholder, will download during actual use)
# Current version uses directory placeholder, doesn't actually download
./run_batch_clone.sh --input parsed_urls.json --output ../downloaded_repos/
```

### Step 2: Code Context Analysis

```bash
# 3. Run CORRECT-improved analysis tools
# Analyze vulnerability code in each repository
scala bfs.scala --repo-path ../downloaded_repos/github.com/user/repo --commit abc123

# 4. Extract related methods and functions
scala get_methods.scala --repo-path ../downloaded_repos/github.com/user/repo --commit abc123
```

### Step 3: Generate Complete Dataset

```bash
# 5. Integrate all analysis results to generate final dataset
python primevul_context_generator.py \
    --input ../primevul_with_context/primevul_original.json \
    --repos ../downloaded_repos/ \
    --output ../primevul_with_context/primevul_zh_format_complete.json
```

## 📊 Data Format Description

### Input Format (Original PrimeVul)
```json
{
    "cve_id": "CVE-2021-1234",
    "commit_url": "https://github.com/torvalds/linux/commit/abc123def456",
    "before_code": "...",
    "after_code": "...",
    "cwe_id": "CWE-119"
}
```

### Output Format (Enhanced Version)
```json
{
    "cve_id": "CVE-2021-1234", 
    "commit_url": "https://github.com/torvalds/linux/commit/abc123def456",
    "before_code": "...",
    "after_code": "...",
    "cwe_id": "CWE-119",
    "context": {
        "related_functions": ["func1", "func2"],
        "call_chain": ["caller -> target -> callee"],
        "data_dependencies": ["var1", "var2"],
        "file_context": "surrounding code context",
        "extracted_by": "CORRECT-based BFS + method extraction"
    },
    "repository_info": {
        "host": "github.com",
        "user": "torvalds",
        "repo": "linux", 
        "commit": "abc123def456",
        "local_path": "downloaded_repos/github.com/torvalds/linux"
    }
}
```

