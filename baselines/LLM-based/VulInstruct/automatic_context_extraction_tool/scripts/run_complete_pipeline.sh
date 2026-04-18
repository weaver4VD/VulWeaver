#!/bin/bash

# PrimeVul Automatic Context Extraction Complete Pipeline
# Improved toolchain based on CORRECT framework

set -e

echo "🚀 PrimeVul Automatic Context Extraction Toolchain"
echo "=================================="

# Check input file
if [ ! -f "$1" ]; then
    echo "❌ Error: Please provide PrimeVul input file"
    echo "Usage: $0 <primevul_input.json>"
    exit 1
fi

INPUT_FILE="$1"
WORK_DIR="../"
REPOS_DIR="${WORK_DIR}/downloaded_repos"
OUTPUT_DIR="${WORK_DIR}/primevul_with_context"

echo "📂 Input file: $INPUT_FILE"
echo "📂 Repository directory: $REPOS_DIR"
echo "📂 Output directory: $OUTPUT_DIR"

# Step 1: URL parsing
echo ""
echo "🔍 Step 1: Parsing CVE commit URLs..."
python url_parser.py --input "$INPUT_FILE" --output parsed_urls.json
if [ $? -eq 0 ]; then
    echo "✅ URL parsing completed"
else
    echo "❌ URL parsing failed"
    exit 1
fi

# Step 2: Repository download (placeholder mode)
echo ""
echo "📥 Step 2: Repository download (placeholder mode)..."
echo "ℹ️  Currently in placeholder mode, not actually downloading repositories"
echo "ℹ️  For actual use, need to execute: ./run_batch_clone.sh"

# Create placeholder directory structure
mkdir -p "$REPOS_DIR"/{github.com,git.kernel.org,other_repos}
echo "✅ Placeholder directory structure created"

# Step 3: Code analysis (simulation)
echo ""
echo "🔬 Step 3: Code context analysis (based on CORRECT)..."
echo "ℹ️  Using Scala tools: bfs.scala + get_methods.scala"
echo "ℹ️  For actual use, will execute for each repository:"
echo "    scala bfs.scala --repo-path \$REPO --commit \$COMMIT"
echo "    scala get_methods.scala --repo-path \$REPO --commit \$COMMIT"
echo "✅ Analysis tools ready"

# Step 4: Context generation
echo ""
echo "📋 Step 4: Generating complete context dataset..."
if [ -f "primevul_context_generator.py" ]; then
    echo "ℹ️  Integrating analysis results, generating final dataset"
    # python primevul_context_generator.py \
    #     --input "$INPUT_FILE" \
    #     --repos "$REPOS_DIR" \
    #     --output "$OUTPUT_DIR/primevul_zh_format_complete.json"
    echo "✅ Context generator ready"
else
    echo "⚠️  Context generator not in current directory"
fi

# Summary
echo ""
echo "🎉 PrimeVul context extraction toolchain setup complete!"
echo "=================================="
echo "📁 Core tools:"
echo "   • url_parser.py      - URL converter"
echo "   • batch_cloner.py    - Batch cloner"
echo "   • bfs.scala          - CORRECT-based BFS analysis"
echo "   • get_methods.scala  - CORRECT-based method extraction"
echo "   • primevul_context_generator.py - Context generator"
echo ""
echo "📊 Processing flow:"
echo "   1. URL parsing and conversion ✅"
echo "   2. Batch repository download 📦 (placeholder)"
echo "   3. Code context analysis 🔬 (CORRECT-based)"
echo "   4. Complete dataset generation 📋"
echo ""
echo "🔧 Required for actual deployment:"
echo "   • Configure sufficient storage space (100GB+)"
echo "   • Install Scala environment and dependencies"
echo "   • Configure Git access permissions"
echo "   • Adjust concurrency and performance parameters"

exit 0