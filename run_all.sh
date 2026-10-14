#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export MPLBACKEND=Agg
mkdir -p "$ROOT/outputs/generated/heatwaves" "$ROOT/outputs/generated/tmax" "$ROOT/outputs/generated/report"

python "$ROOT/src/analyze_heatwaves.py" \
  --annual "$ROOT/data/gee_exports/heatwaves/HW_validation_annual_urban_centroids_1985_2025.csv" \
  --monthly "$ROOT/data/gee_exports/heatwaves/HW_validation_monthly_urban_centroids_1985_2025.csv" \
  --centroids "$ROOT/data/reference/HW_validation_urban_centroids.csv" \
  --outdir "$ROOT/outputs/generated/heatwaves"

python "$ROOT/src/analyze_tmax.py" \
  --station "$ROOT/data/stations/tmax/Maximas_capitais.csv" \
  --era5-dir "$ROOT/data/gee_exports/era5_tmax" \
  --outdir "$ROOT/outputs/generated/tmax"

python "$ROOT/src/validate_reproduction.py" \
  --heatwave-out "$ROOT/outputs/generated/heatwaves" \
  --tmax-out "$ROOT/outputs/generated/tmax"

python "$ROOT/src/generate_factsheet.py" \
  --heatwave-out "$ROOT/outputs/generated/heatwaves" \
  --tmax-out "$ROOT/outputs/generated/tmax" \
  --centroids "$ROOT/data/reference/HW_validation_urban_centroids.csv" \
  --outfile "$ROOT/outputs/generated/report/MapBiomas_Atmosfera_Heatwaves_Accuracy_Factsheet.pdf"

echo
echo "DONE"
echo "Factsheet: $ROOT/outputs/generated/report/MapBiomas_Atmosfera_Heatwaves_Accuracy_Factsheet.pdf"
echo "Tables/figures: $ROOT/outputs/generated/heatwaves and $ROOT/outputs/generated/tmax"
