#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export MPLBACKEND=Agg
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

if [[ -f "$ROOT/.venv/bin/activate" ]]; then
  source "$ROOT/.venv/bin/activate"
fi

python -u "$ROOT/src/generate_factsheet_v2.py" \
  --heatwave-out "$ROOT/outputs/generated/heatwaves" \
  --tmax-out "$ROOT/outputs/generated/tmax" \
  --centroids "$ROOT/data/reference/HW_validation_urban_centroids.csv" \
  --annual-validation "$ROOT/data/gee_exports/heatwaves/HW_validation_annual_urban_centroids_1985_2025.csv" \
  --assets-dir "$ROOT/assets/report_v2" \
  --outfile "$ROOT/outputs/generated/report/MapBiomas_Atmosfera_Heatwaves_Accuracy_Factsheet_v2.pdf"

echo
echo "Generated:"
stat "$ROOT/outputs/generated/report/MapBiomas_Atmosfera_Heatwaves_Accuracy_Factsheet_v2.pdf"
