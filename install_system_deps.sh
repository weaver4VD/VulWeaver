#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"

if ! command -v apt-get >/dev/null 2>&1; then
    echo "This script currently supports Debian/Ubuntu systems with apt-get."
    echo "Please install Graphviz development headers manually on your platform."
    exit 1
fi

if ! command -v python >/dev/null 2>&1; then
    echo "python was not found in PATH."
    echo "Please activate your Python/conda environment first, then rerun this script."
    exit 1
fi

if [[ ! -f "${REQUIREMENTS_FILE}" ]]; then
    echo "requirements.txt was not found at: ${REQUIREMENTS_FILE}"
    exit 1
fi

echo "Installing system packages required by scubatrace/pygraphviz..."
sudo apt-get update
sudo apt-get install -y graphviz libgraphviz-dev pkg-config

echo "Installing Python dependencies from requirements.txt..."
python -m pip install --upgrade pip
python -m pip install -r "${REQUIREMENTS_FILE}"

echo "System and Python dependencies installed successfully."
