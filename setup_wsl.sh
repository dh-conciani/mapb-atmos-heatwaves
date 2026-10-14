#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/3] Installing Ubuntu system packages (sudo required)..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip unzip

echo "[2/3] Creating Python virtual environment..."
python3 -m venv "$ROOT/.venv"
source "$ROOT/.venv/bin/activate"
python -m pip install --upgrade pip wheel

echo "[3/3] Installing pinned Python dependencies..."
pip install -r "$ROOT/requirements.txt"

echo
echo "Environment ready."
echo "Run: source .venv/bin/activate && ./run_all.sh"
