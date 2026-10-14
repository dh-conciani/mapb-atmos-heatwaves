# Proveniência e linhagem

## Produtos MapBiomas analisados

Validação dos agregados de ondas de calor:

- V1: `projects/mapbiomas-brazil/assets/DEGRADATION/COLLECTION-11/CLIMATIC_WAVES/heatWaves_agg`
- V2: `projects/mapbiomas-brazil/assets/DEGRADATION/COLLECTION-11/CLIMATIC_WAVES/heatWaves_v2_agg`

Período: 1985-2025.

## Dado climático de entrada

- Google Earth Engine: `ECMWF/ERA5_LAND/DAILY_AGGR`
- Banda: `temperature_2m_max`
- Conversão Kelvin -> Celsius: `T_C = T_K - 273.15`

Os nove CSVs em `data/gee_exports/era5_tmax/` foram exportados dos mesmos centroides urbanos usados na validação dos produtos.

## Estações

- `data/stations/events/*.txt`: listas de eventos usadas na validação de ondas de calor.
- `data/stations/tmax/Maximas_capitais.csv`: Tmax diária 1985-2025 usada na segunda linha de validação.

## Pontos de referência

`data/reference/HW_validation_urban_centroids.csv` contém os centroides ponderados pela área urbana MapBiomas 2025 (classe 24) usados como pontos fixos.

## Separação entre aquisição e análise

Os scripts em `gee/` documentam a aquisição/preparação no Earth Engine. Os scripts em `src/` reproduzem localmente as análises a partir dos CSVs exportados. Assim, a reprodução estatística e do fact-sheet no WSL não exige credenciais GEE.
