# Patch - Fact-sheet de acurácia v2

Esta atualização substitui o layout anterior do relatório por uma versão mais próxima do estilo de factsheets MapBiomas: tipografia maior, menos elementos por página, mapas como elementos focais, números-chave em destaque e mensagens técnicas mais diretas.

## Conteúdo novo

- página de método com mapa das 9 capitais;
- mapa diagnóstico do bias médio diário da Tmax;
- página dedicada ao offset anual de Tmax;
- comparação explícita 1991-2020 versus 2021-2025;
- explicação direta de Manaus, Belém e Salvador;
- página TX90 com o mecanismo de compensação parcial;
- página WSDI com comissão em Manaus e maior incerteza em Salvador;
- fontes e títulos maiores, reduzindo a densidade visual.

## Instalar no repositório existente

A partir da raiz de `MapBiomas_Heatwaves_Accuracy_Reproducibility` copie os arquivos do patch preservando as pastas ou use `unzip -o`.

Depois:

```bash
chmod +x generate_report_v2.sh
source .venv/bin/activate
./generate_report_v2.sh
```

O relatório será criado em:

```text
outputs/generated/report/MapBiomas_Atmosfera_Heatwaves_Accuracy_Factsheet_v2.pdf
```

O script usa os outputs já recalculados por `analyze_heatwaves.py` e `analyze_tmax.py`; portanto, rode as análises primeiro.
