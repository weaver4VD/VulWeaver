#!/bin/bash
# Batch repository cloning script for PrimeVul dataset

set -e  # Exit on error

echo "🚀 Starting PrimeVul dataset repository batch cloning"
echo "Current directory: $(pwd)"
echo "Time: $(date)"
echo

# Check dependencies
command -v git >/dev/null 2>&1 || { echo "❌ Git not installed"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 not installed"; exit 1; }

# Check input file
if [ ! -f "primevul_test_paired.jsonl" ]; then
    echo "❌ Data file does not exist: primevul_test_paired.jsonl"
    exit 1
fi

# Check Python dependencies
python3 -c "import tqdm, json" 2>/dev/null || {
    echo "❌ Python dependencies missing, installing..."
    pip install tqdm
}

# Show disk space
echo "💾 Current disk space:"
df -h .
echo

# First perform dry run analysis
echo "🔍 Analyzing repositories to be cloned..."
python3 batch_cloner.py --dry-run

echo
read -p "🤔 Do you want to continue with cloning? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ User cancelled operation"
    exit 0
fi

# Execute batch cloning
echo "🚀 Starting batch cloning, can interrupt with Ctrl+C at any time..."
python3 batch_cloner.py

# Show results
echo
echo "📊 Cloning completed, viewing status:"
python3 clone_status_viewer.py

echo
echo "💡 Tips:"
echo "  - View failed repositories: python3 clone_status_viewer.py --failed"
echo "  - Retry cloning: python3 batch_cloner.py"
echo "  - Start analysis: python3 primevul_analyzer.py --skip-clone"
echo
echo "✅ Batch cloning process completed!"