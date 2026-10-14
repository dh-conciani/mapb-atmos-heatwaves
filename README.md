# MapBiomas Atmosfera - reproducibilidade da análise de acurácia de ondas de calor

Este repositório compila os dados, scripts e resultados usados na discussão técnica sobre a viabilidade de publicação dos produtos agregados de ondas de calor do MapBiomas Atmosfera.

O pacote reproduz duas linhas de evidência:

1. **Validação do produto final V1 x V2** contra listas de eventos derivadas de estações meteorológicas em 9 capitais, nas escalas anual e mensal.
2. **Validação da variável de entrada**: temperatura máxima diária das estações contra `temperature_2m_max` do ERA5-Land, incluindo bias/RMSE, sazonalidade, extremos, TX90, alinhamento temporal e persistência WSDI.

O objetivo do pacote é reproduzir **as análises estatísticas e o fact-sheet de acurácia**, sem depender de acesso ao Google Earth Engine. Os CSVs exportados do GEE que alimentaram a análise estão incluídos em `data/gee_exports/`.

## Resultado executivo reproduzido

- V2 - dias anuais com onda de calor: **Pearson r ~0,71**, RMSE **~12,2 dias/ano**, bias **~+1,0 dia/ano**.
- V1 - dias anuais: r **~0,17**, RMSE **~16,2 dias/ano**, bias **~-4,6 dias/ano**.
- F1 de ocorrência anual: **V2 ~0,69** versus **V1 ~0,45**.
- Na escala mensal, a V2 mantém vantagem: r **~0,59** versus **~0,27**, F1 **~0,50** versus **~0,28**.
- ERA5-Land acompanha bem a variabilidade diária de Tmax, mas apresenta **bias frio em todas as 9 capitais**: aproximadamente **-0,4 a -2,9 °C**.
- O limiar TX90 calculado no próprio ERA5-Land também é mais baixo. Isso **compensa parcialmente** o offset absoluto na metodologia percentílica da V2.
- A persistência de sequências >=6 dias é mais difícil de reproduzir do que a classificação de um único dia acima de TX90. Manaus é um exemplo importante de alta detecção/recall com comissão elevada.

**Decisão técnica sugerida:** V2 é a versão mais defensável para publicação de `heatwave_days`, `event_count` e ocorrência mensal/anual. Métricas de duração devem ser publicadas com cautela e nota metodológica.

## Estrutura

```text
.
├── data/
│   ├── stations/events/         # listas de eventos por capital
│   ├── stations/tmax/           # Tmax diária das estações
│   ├── gee_exports/heatwaves/   # tabelas de validação V1/V2 exportadas do GEE
│   ├── gee_exports/era5_tmax/   # Tmax diária ERA5-Land por capital
│   └── reference/               # centroides e tabelas auxiliares
├── gee/                         # scripts do Earth Engine e histórico relevante
├── src/                         # scripts Python reproduzíveis
├── outputs/reference/           # resultados pré-gerados incluídos no ZIP
├── outputs/generated/           # criado por ./run_all.sh
├── report/                      # documentação do relatório
├── presentation/                # apresentação técnica integrada
├── setup_wsl.sh
├── run_all.sh
├── requirements.txt
└── Makefile
```

## Execução rápida no WSL Ubuntu

Depois de descompactar:

```bash
cd MapBiomas_Heatwaves_Accuracy_Reproducibility
chmod +x setup_wsl.sh run_all.sh
./setup_wsl.sh
source .venv/bin/activate
./run_all.sh
```

O principal produto será:

```text
outputs/generated/report/MapBiomas_Atmosfera_Heatwaves_Accuracy_Factsheet.pdf
```

Além dele, todas as tabelas intermediárias e figuras ficam em `outputs/generated/heatwaves/` e `outputs/generated/tmax/`.

Veja `docs/WSL_WINDOWS11.md` para instruções desde a instalação do WSL e `docs/METODOLOGIA.md` para a descrição metodológica.

## Reprodutibilidade

`run_all.sh` executa ao final `src/validate_reproduction.py`, que testa numericamente resultados-chave contra os valores obtidos nesta análise. O processo falha caso os resultados excedam as tolerâncias documentadas.

## Observações importantes

- As listas de eventos de estação não carregam toda a documentação do algoritmo original que gerou cada evento. Por isso, a primeira linha é uma comparação/validação de registros de eventos, e não uma reconstrução perfeita do método da estação.
- A estação é pontual e a célula ERA5-Land é espacialmente agregada (~11 km). O ERA5 foi amostrado no mesmo centroide urbano usado na validação do produto, não necessariamente na coordenada física da estação.
- O pacote é uma base técnica para decisão de publicação, não uma validação nacional exaustiva de todos os municípios, biomas ou contextos urbano/rural.
