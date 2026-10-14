MAPBIOMAS | ATLAS DE ONDAS DE CALOR - V2.2
=======================================

ARQUIVO PRINCIPAL: MapBiomas_Heatwaves_Thumbnails_GEE_v2_2.txt
USO: copiar integralmente para https://code.earthengine.google.com/ e clicar Run.
O script apenas LE assets e solicita visualizacoes; nao cria ou altera exports.

POR QUE ALGUMAS MINIATURAS ESTAVAM QUEBRADAS?
- Os 41 assets V2 podem existir mesmo que os PNGs nao sejam renderizados.
- Na versao antiga, 41 ou ate 123 renderizacoes podiam comecar juntas.
- Pintar limites detalhados e repetir o recorte espacial em todos os pedidos
  aumenta o trabalho dos servidores e pode ocasionar falhas transitorias.
- Sem o erro HTTP especifico do navegador nao e possivel estabelecer a causa
  definitiva para cada miniatura. A revisao reduz causas provaveis e facilita
  a recuperacao individual.

MUDANCAS
1. Fila gradual de miniaturas, padrao 4 segundos entre pedidos.
   Alternativas 2 s ou 6 s no menu. O contador indica SOLICITADAS,
   nao necessariamente renderizadas com sucesso.
2. Os 41 anos permanecem na mesma pagina; nao ha paginacao.
3. Miniaturas passam a usar 180 px para reduzir processamento.
4. O recorte complexo do Brasil foi retirado das imagens de visualizacao,
   pois os produtos finais ja foram exportados recortados no Brasil.
5. Divisas da base FAO GAUL 2015 simplificadas SOMENTE para o atlas.
   Brasil: contorno preto; estados: cinza.
6. Zeros continuam transparentes. Paletas e escalas sao as mesmas.
7. Abaixo de cada miniatura ha dois botoes:
   - Recarregar miniatura: cria um novo pedido com Brasil e estados.
   - Tentar modo leve: mantem o contorno do Brasil, mas nao desenha estados
     apenas na miniatura selecionada. Esse modo e um recurso de diagnostico
     caso a renderizacao detalhada falhe repetidamente.
8. A fila pode ser pausada e retomada. Alterar as selecoes cancela os pedidos
   QUE AINDA ESTAVAM NA FILA; nao cancela trabalhos ja enviados ao Earth Engine.

SE ALGUMA MINIATURA CONTINUAR QUEBRADA
- Aguarde o processamento das miniaturas restantes e tente Recarregar.
- Se falhar outra vez, use Tentar modo leve no proprio cartao.
- Tente velocidade conservadora (6 s) para comparacoes V1 vs V2.
- Se o mesmo ano falhar persistentemente, copie a mensagem exata do console
  do GEE e a resposta/status HTTP do pedido de thumbnail no navegador.
- Nao exclua os assets: a indisponibilidade temporaria do PNG nao implica
  corrupcao do GeoTIFF/asset.

LIMITACOES
- Nao foi possivel executar o codigo contra os assets privados do projeto.
- A interface ui.Thumbnail do Code Editor nao disponibiliza um callback
  documentado de erro de carregamento HTTP; os botoes de recuperacao sao
  manuais. Nao se afirma que um PNG foi carregado so porque foi solicitado.
- Os contornos foram simplificados para a escala de miniatura; a geometria
  de referencia da FAO nao substitui as divisas oficiais do IBGE.
