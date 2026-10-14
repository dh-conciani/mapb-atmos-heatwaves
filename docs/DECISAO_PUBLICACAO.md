# Síntese para decisão de publicação

## Recomendação

**Publicar a V2 como referência** para:

- `heatwave_days`
- `event_count`
- ocorrência mensal/anual

## Publicar com cautela

- `max_event_duration`
- `mean_event_duration`

A duração só é definida quando há evento detectado; V1/V2/estação não compartilham exatamente o mesmo conjunto de eventos.

## Não recomendado

Não usar a V1 como versão de referência para publicação.

## Base da decisão

1. Na validação anual, a V2 melhora r, CCC, RMSE, bias, F1 e recall simultaneamente.
2. O ganho persiste na escala mensal.
3. A análise diária da Tmax confirma forte covariação estação x ERA5-Land, mas identifica bias frio absoluto.
4. O TX90 do ERA5-Land também é mais baixo, gerando compensação parcial em um índice percentílico.
5. A persistência WSDI é a etapa mais sensível e explica casos de comissão/omissão por cidade.

## Casos de atenção

- **Manaus:** alta correlação anual, mas comissão elevada em dias WSDI; recall alto e precision baixa. O bias frio torna-se menos negativo em anos recentes em relação ao período climatológico, aumentando a frequência relativa de excedência do TX90.
- **Salvador:** menor habilidade de persistência WSDI; o problema não é explicado apenas por bias médio.
- **Belém:** forte mudança temporal do bias estação x ERA5-Land.
- **Goiânia:** maior offset frio absoluto.
- **Porto Alegre/Curitiba:** evidência mais consistente entre associação, magnitude e persistência.
