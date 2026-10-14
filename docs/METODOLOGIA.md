# Metodologia da análise de acurácia

## 1. Produto V2 de ondas de calor

A lógica avaliada é baseada em WSDI/TX90:

1. Tmax diária do ERA5-Land (`temperature_2m_max`).
2. Climatologia de referência 1991-2020.
3. Para cada dia-calendário, percentil 90 calculado em janela centrada de 5 dias.
4. Dia quente quando `Tmax > TX90`.
5. Dia de onda de calor quando pertence a uma sequência de **>=6 dias quentes consecutivos**.
6. 29/fev é excluído da climatologia; em anos bissextos, usa-se o limiar de 28/fev.

## 2. Agregações mensal e anual

Convenção adotada na validação:

- `heatwave_days`: os dias são atribuídos às datas em que efetivamente ocorreram.
- `event_count`: evento completo contado uma única vez no período em que termina.
- `max_event_duration`: duração máxima entre eventos completos que terminam no período.
- `mean_event_duration`: média das durações dos eventos completos que terminam no período.
- Eventos não são quebrados na virada de mês/ano.
- Sem evento completo: duração é indefinida, não zero.

## 3. Validação dos agregados V1 x V2

Dados de referência: listas de eventos de estações meteorológicas em Brasília, Curitiba, Goiânia, Manaus, Porto Alegre, Salvador, São Paulo, Belém e Belo Horizonte.

Referência espacial: centroide ponderado pela área urbana MapBiomas 2025 (classe 24), fixo por cidade durante 1985-2025.

Métricas:

- Pearson r: associação temporal.
- Spearman rho: associação monotônica.
- CCC de Lin: concordância entre associação e magnitude.
- Bias = MapBiomas - estação.
- MAE e RMSE.
- Precision, Recall, F1 e CSI para ocorrência de evento.

Para duração, a comparação V1 x V2 também é feita em **common support**, isto é, apenas onde estação, V1 e V2 têm duração definida.

## 4. Validação da Tmax diária ERA5-Land

A série `Maximas_capitais.csv` é pareada por data com o ERA5-Land amostrado no mesmo centroide urbano da validação dos agregados.

Convenção:

```text
DeltaT = Tmax_ERA5 - Tmax_estação
```

- DeltaT < 0: ERA5-Land mais frio.
- DeltaT > 0: ERA5-Land mais quente.

São calculados:

- Pearson, Spearman, CCC, bias, MAE, RMSE.
- Erro por mês e por ano.
- Tendência do bias anual.
- Diferenças nos percentis P50, P90, P95 e P99.
- Diagnóstico de lag em -2, -1, 0, +1 e +2 dias.

## 5. Diagnóstico TX90 e persistência

O TX90 é recalculado **separadamente** nas estações e no ERA5-Land, mantendo a mesma regra conceitual da V2: 1991-2020, janela de 5 dias e P90.

Dois níveis de habilidade são medidos:

1. Concordância diária de `Tmax > TX90`.
2. Concordância de dias pertencentes a sequências de >=6 dias acima de TX90.

Isso permite separar:

- erro absoluto de temperatura;
- erro no limiar climatológico;
- erro na classificação de dia extremo;
- erro na persistência que transforma dias extremos em evento WSDI.

## 6. Interpretação dos resultados

O ERA5-Land apresenta bias frio absoluto nas nove capitais. Entretanto, o TX90 do próprio ERA5-Land também é mais baixo. Por isso, a metodologia percentílica possui uma **compensação interna parcial** e pode reproduzir ocorrência relativa melhor do que o bias absoluto de Tmax sugeriria.

A compensação não é completa. Diferenças em variabilidade, ordenamento e persistência diária explicam divergências como:

- **Manaus:** alto recall, mas baixa precisão de dias WSDI; detecta muitos dias extras. O bias frio fica menos negativo em anos recentes em relação ao período climatológico, contribuindo para maior frequência relativa de excedência do TX90 ERA5.
- **Salvador:** baixa concordância de persistência WSDI; o problema não é explicado apenas pelo bias médio da Tmax.
- **Porto Alegre/Curitiba:** melhor combinação de associação diária e persistência.

## 7. Limitações

- Estação meteorológica = observação pontual; ERA5-Land = célula espacial ~11 km.
- O ponto ERA5 é o centroide urbano de validação, não necessariamente a coordenada da estação.
- Mudanças de instrumentação, relocação e ambiente urbano das estações não foram modeladas.
- As listas de eventos não carregam toda a documentação do método que as originou.
- Nove capitais não representam todos os biomas, municípios ou contextos rurais/urbanos do Brasil.

## 8. Uso recomendado

A evidência atual sustenta a V2 para publicação de `heatwave_days`, `event_count` e ocorrência mensal/anual. Métricas de duração devem ser acompanhadas por ressalva e análise de sensibilidade.
