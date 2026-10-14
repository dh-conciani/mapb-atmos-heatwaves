# Dicionário resumido dos dados

## `data/gee_exports/heatwaves/HW_validation_annual_urban_centroids_1985_2025.csv`

Uma linha por capital x ano (9 x 41 = 369). Campos centrais:

- `station_heatwave_days`, `station_event_count`, `station_max_event_duration`, `station_mean_event_duration`
- equivalentes `v1_*` e `v2_*`
- `centroid_lon`, `centroid_lat`, `year`, `month`, `period_type`
- `-9999` indica duração/dado indefinido; não deve ser convertido para zero.

## `data/gee_exports/heatwaves/HW_validation_monthly_urban_centroids_1985_2025.csv`

Uma linha por capital x ano x mês (9 x 41 x 12 = 4.428).

## `data/stations/tmax/Maximas_capitais.csv`

Série diária 1985-2025. A primeira coluna é `Data`; as demais são Tmax (°C) por capital.

## `data/gee_exports/era5_tmax/ERA5_Tmax_daily_<capital>_1985_2025.csv`

Tmax diária do ERA5-Land no ponto de validação urbano. Campos principais:

- `date`
- `city_id`, `city`
- `centroid_lon`, `centroid_lat`
- `tmax_era5_k`, `tmax_era5_c`

## `data/reference/HW_validation_urban_centroids.csv`

Centroides urbanos fixos usados na validação dos produtos.

## `data/stations/events/*.txt`

Listas de eventos de estação com início, fim, duração e temperatura máxima associada ao evento. São mantidas para rastreabilidade da validação original.
