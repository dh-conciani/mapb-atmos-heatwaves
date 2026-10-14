#!/usr/bin/env python3
"""Generate an 8-page MapBiomas Atmosfera-style accuracy factsheet PDF."""
from pathlib import Path
import argparse
import pandas as pd
import numpy as np

from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth

W, H = 960, 540  # 16:9 points-like canvas
GREEN = HexColor('#0B6E4F'); TEAL=HexColor('#56B6C7'); ORANGE=HexColor('#F2A23A'); PURPLE=HexColor('#8E2CA2')
V1=HexColor('#7FAFC1'); TEXT=HexColor('#26332C'); MID=HexColor('#5B675F'); LIGHT=HexColor('#EFF4EF'); PALE=HexColor('#F6F7F3'); WARM=HexColor('#FFF6E8')


def txt(c, x, y, text, size=10, color=TEXT, font='Helvetica', max_width=None, leading=None, bold=False, align='left'):
    fontname = 'Helvetica-Bold' if bold else font
    c.setFont(fontname, size); c.setFillColor(color)
    leading = leading or size*1.23
    if max_width is None:
        if align=='center': c.drawCentredString(x,y,text)
        elif align=='right': c.drawRightString(x,y,text)
        else: c.drawString(x,y,text)
        return y
    words=text.split(); lines=[]; cur=''
    for w in words:
        trial=(cur+' '+w).strip()
        if stringWidth(trial,fontname,size) <= max_width:
            cur=trial
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    yy=y
    for line in lines:
        if align=='center': c.drawCentredString(x,yy,line)
        elif align=='right': c.drawRightString(x,yy,line)
        else: c.drawString(x,yy,line)
        yy -= leading
    return yy


def header(c, page, section='ANÁLISE DE ACURÁCIA'):
    c.setFillColor(TEAL); c.rect(0,H-6,450,6,stroke=0,fill=1)
    c.setFillColor(ORANGE); c.rect(450,H-6,230,6,stroke=0,fill=1)
    c.setFillColor(GREEN); c.rect(680,H-6,280,6,stroke=0,fill=1)
    txt(c,28,H-25,f'MAPBIOMAS ATMOSFERA | {section}',7.5,GREEN,bold=True)
    txt(c,930,H-25,f'{page:02d}',7.5,HexColor('#9AA59C'),align='right')


def footer(c, text='Fonte: MapBiomas / ERA5-Land / estações meteorológicas | 1985-2025'):
    txt(c,28,18,text,6.5,HexColor('#8B9690'))


def title(c, t, sub=None):
    txt(c,28,H-64,t,24,GREEN,bold=True,max_width=885)
    if sub: txt(c,28,H-88,sub,10.5,MID,max_width=880)


def rounded(c,x,y,w,h,fill=PALE,stroke=HexColor('#DDE5E0'),r=10):
    c.setFillColor(fill); c.setStrokeColor(stroke); c.roundRect(x,y,w,h,r,stroke=1,fill=1)


def metric(c,x,y,w,value,label,accent=GREEN):
    rounded(c,x,y,w,68)
    txt(c,x+w/2,y+41,value,19,accent,bold=True,align='center')
    txt(c,x+w/2,y+18,label,8.2,MID,bold=True,align='center')


def diamond(c,cx,cy,size,color):
    c.saveState(); c.translate(cx,cy); c.rotate(45); c.setFillColor(color); c.setStrokeColor(color); c.rect(-size/2,-size/2,size,size,stroke=0,fill=1); c.restoreState()


def image(c,path,x,y,w,h,preserve=True):
    path=Path(path)
    if not path.exists(): return
    ir=ImageReader(str(path)); iw,ih=ir.getSize()
    if preserve:
        scale=min(w/iw,h/ih); nw=iw*scale; nh=ih*scale; x=x+(w-nw)/2; y=y+(h-nh)/2; w=nw; h=nh
    c.drawImage(ir,x,y,w,h,mask='auto',preserveAspectRatio=True)


def table(c, x, y_top, widths, rows, row_h=23, header_fill=GREEN, font_size=8.5, highlights=None):
    y=y_top
    for i,row in enumerate(rows):
        fill = header_fill if i==0 else (HexColor('#F7FAF7') if i%2 else HexColor('#EDF3EE'))
        xx=x
        for j,(val,w) in enumerate(zip(row,widths)):
            c.setFillColor(fill); c.setStrokeColor(white); c.rect(xx,y-row_h,w,row_h,stroke=1,fill=1)
            col=white if i==0 else TEXT
            bold=i==0 or (highlights and (i,j) in highlights)
            txt(c,xx+(6 if j==0 else w/2),y-row_h+7,str(val),font_size,col,bold=bold,align=('left' if j==0 else 'center'))
            xx+=w
        y-=row_h
    return y


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--heatwave-out',required=True)
    ap.add_argument('--tmax-out',required=True)
    ap.add_argument('--centroids',required=True)
    ap.add_argument('--outfile',required=True)
    args=ap.parse_args()
    hw=Path(args.heatwave_out); tx=Path(args.tmax_out); out=Path(args.outfile); out.parent.mkdir(parents=True,exist_ok=True)
    pooled=pd.read_csv(hw/'tables/pooled_metrics.csv')
    det=pd.read_csv(hw/'tables/event_detection_metrics.csv')
    dur=pd.read_csv(hw/'tables/duration_common_support_metrics.csv')
    score=pd.read_csv(tx/'tables/daily_scorecard_by_city.csv')
    hot=pd.read_csv(tx/'tables/hot_day_skill.csv')
    wsdi=pd.read_csv(tx/'tables/wsdi_event_day_skill.csv')
    tx90=pd.read_csv(tx/'tables/tx90_thresholds.csv')
    annual_bias=pd.read_csv(tx/'tables/annual_bias_city_summary.csv')
    cent=pd.read_csv(args.centroids)

    def prow(period,metric,version,center=False):
        return pooled[(pooled.period==period)&(pooled.metric==metric)&(pooled.version==version)&(pooled.centered_by_city==center)].iloc[0]
    a1=prow('annual','heatwave_days','v1'); a2=prow('annual','heatwave_days','v2')
    m1=prow('monthly','heatwave_days','v1'); m2=prow('monthly','heatwave_days','v2')
    da=det[(det.period=='annual')&(det.city=='ALL_CITIES')].set_index('version')
    dm=det[(det.period=='monthly')&(det.city=='ALL_CITIES')].set_index('version')

    c=canvas.Canvas(str(out),pagesize=(W,H))
    c.setTitle('MapBiomas Atmosfera - Analise de acuracia de ondas de calor')

    # PAGE 1 — executive summary
    header(c,1,'ANÁLISE DE ACURÁCIA | SUMÁRIO EXECUTIVO')
    txt(c,38,460,'VALIDAÇÃO INTEGRADA DAS',24,GREEN,bold=True)
    txt(c,38,427,'ONDAS DE CALOR',36,GREEN,bold=True)
    txt(c,38,398,'V1 x V2 + acurácia da Tmax diária ERA5-Land',13,MID)
    # diamonds
    diamond(c,760,380,95,HexColor('#E1E27D')); diamond(c,835,300,95,TEAL); diamond(c,905,385,65,ORANGE)
    rounded(c,38,248,885,118,LIGHT,HexColor('#DDE8E0'),14)
    txt(c,62,335,'DECISÃO SUGERIDA',10,GREEN,bold=True)
    txt(c,62,303,'V2 é tecnicamente viável para publicação',22,GREEN,bold=True)
    txt(c,62,278,'Priorizar heatwave_days, event_count e ocorrência mensal/anual. Duração deve ser publicada com cautela e nota metodológica.',11,TEXT,max_width=825)
    metric(c,38,140,160,'0,71','Pearson r anual | V2',PURPLE)
    metric(c,215,140,160,'12,2 dias','RMSE anual | V2',ORANGE)
    metric(c,392,140,160,'0,69','F1 ocorrência anual',PURPLE)
    metric(c,569,140,160,'-0,4 a -2,9 °C','bias Tmax diário',TEAL)
    metric(c,746,140,177,'0,40-0,76','F1 dias > TX90',GREEN)
    txt(c,38,102,'Mensagem central',10,GREEN,bold=True)
    txt(c,38,80,'A V2 melhora simultaneamente associação temporal, erro e detecção. O ERA5-Land tem bias frio absoluto, mas o TX90 calculado no próprio ERA5 também é mais baixo, compensando parte desse offset.',10,TEXT,max_width=880)
    footer(c); c.showPage()

    # PAGE 2 — methods and data
    header(c,2,'ANÁLISE DE ACURÁCIA | MÉTODO')
    title(c,'Duas linhas de evidência complementares','A recomendação não depende de uma única comparação.')
    rounded(c,35,215,410,245,LIGHT); rounded(c,515,215,410,245,HexColor('#F7F3FA'))
    txt(c,58,425,'1 | Produto final V1 x V2',16,GREEN,bold=True)
    txt(c,58,393,'Listas de eventos de estações comparadas aos agregados mensais e anuais.',10,TEXT,max_width=350)
    txt(c,58,350,'Indicadores',9,GREEN,bold=True); txt(c,58,330,'heatwave_days | event_count | max/mean duration',9.3,TEXT,max_width=350)
    txt(c,58,292,'Métricas',9,GREEN,bold=True); txt(c,58,272,'Pearson | CCC | RMSE | Bias | F1 | Recall',9.3,TEXT)
    txt(c,538,425,'2 | Dado de entrada: Tmax',16,PURPLE,bold=True)
    txt(c,538,393,'Tmax diária das estações comparada ao ERA5-Land no mesmo centroide urbano.',10,TEXT,max_width=350)
    txt(c,538,350,'Diagnósticos',9,PURPLE,bold=True); txt(c,538,330,'bias/RMSE | sazonalidade | extremos | TX90 | lag | persistência ≥6 dias',9.3,TEXT,max_width=350)
    metric(c,35,125,170,'9','capitais',GREEN); metric(c,220,125,170,'41 anos','1985-2025',TEAL); metric(c,405,125,170,'14.975','dias/capital',ORANGE); metric(c,590,125,170,'~99,5%','cobertura estação',PURPLE); metric(c,775,125,150,'~11 km','escala ERA5',GREEN)
    txt(c,35,88,'Referência espacial: centroide ponderado pela área urbana MapBiomas 2025 (classe 24), fixo no tempo. A estação é pontual; ERA5-Land representa uma célula.',9.2,MID,max_width=880)
    footer(c); c.showPage()

    # PAGE 3 — product validation
    header(c,3,'VALIDAÇÃO DO PRODUTO | V1 x V2')
    title(c,'V2 é claramente superior para dias e ocorrência','O ganho aparece simultaneamente em associação, erro, viés e detecção.')
    rows=[['Métrica','V1','V2','Leitura'],
          ['Pearson r anual',f'{a1.pearson_r:.2f}',f'{a2.pearson_r:.2f}','V2 melhor'],
          ['CCC anual',f'{a1.ccc:.2f}',f'{a2.ccc:.2f}','V2 melhor'],
          ['RMSE anual',f'{a1.rmse:.1f}',f'{a2.rmse:.1f}','V2 menor erro'],
          ['Bias anual',f'{a1.bias:+.1f}',f'{a2.bias:+.1f}','V2 ~ zero'],
          ['F1 ocorrência anual',f"{da.loc['v1','f1']:.2f}",f"{da.loc['v2','f1']:.2f}",'V2 melhor'],
          ['Recall anual',f"{da.loc['v1','recall']:.2f}",f"{da.loc['v2','recall']:.2f}",'V2 melhor']]
    table(c,45,430,[170,75,75,130],rows,row_h=29,highlights={(i,2) for i in range(1,len(rows))})
    image(c,hw/'figures/01_scatter_v1_v2_heatwave_days.png',505,208,420,250)
    rounded(c,45,102,420,78,WARM,HexColor('#F3D8AA'))
    txt(c,65,155,'Leitura',10,ORANGE,bold=True)
    txt(c,65,132,'A superioridade da V2 não é apenas correlação: ela também reduz RMSE e bias e aumenta a detecção de eventos verdadeiros.',9.5,TEXT,max_width=380)
    rounded(c,505,102,420,78,LIGHT,HexColor('#DDE8E0'))
    txt(c,525,155,'Recomendação',10,GREEN,bold=True)
    txt(c,525,132,'Usar a V2 como referência de publicação para dias e ocorrência; não usar a V1 como produto de referência.',9.5,TEXT,max_width=380)
    footer(c); c.showPage()

    # PAGE 4 — monthly, raw, duration
    header(c,4,'VALIDAÇÃO DO PRODUTO | ESCALA MENSAL E DURAÇÃO')
    title(c,'O ganho da V2 se mantém na escala mensal','A escala mensal é mais exigente porque o produto precisa acertar também o momento do evento.')
    metric(c,35,400,160,f'{m2.pearson_r:.2f}','Pearson mensal V2',PURPLE); metric(c,210,400,160,f'{m2.rmse:.2f}','RMSE mensal (dias)',ORANGE); metric(c,385,400,160,f'{m2.bias:+.2f}','Bias mensal (dias)',GREEN); metric(c,560,400,160,f"{dm.loc['v2','f1']:.2f}",'F1 mensal',PURPLE); metric(c,735,400,190,f"{dm.loc['v2','recall']:.2f}",'Recall mensal',TEAL)
    image(c,hw/'figures/02_raw_annual_days_by_city.png',35,105,565,270)
    image(c,hw/'figures/04_f1_detection_annual_monthly.png',615,190,310,185)
    rounded(c,615,105,310,72,WARM,HexColor('#F3D8AA'))
    txt(c,635,154,'Duração: maior cautela',9.5,ORANGE,bold=True)
    txt(c,635,134,'Max/mean duration só existem quando um evento é detectado. V1 e V2 detectam conjuntos diferentes; a comparação justa usa common support.',8.6,TEXT,max_width=275)
    footer(c); c.showPage()

    # PAGE 5 — Tmax scorecard
    header(c,5,'ACURÁCIA DA TMAX | ESTAÇÃO x ERA5-LAND')
    title(c,'Tmax diária: boa covariação, com viés frio sistemático','Bias absoluto e capacidade de acompanhar as oscilações são dimensões diferentes.')
    score2=score.set_index('city').loc[['Brasília','Curitiba','Goiânia','Manaus','Porto Alegre','Salvador','São Paulo','Belém','Belo Horizonte']].reset_index()
    rows=[['Capital','r','Bias °C','RMSE °C']]+[[r.city,f'{r.pearson_r:.2f}',f'{r.bias_era5_minus_station:.2f}',f'{r.rmse:.2f}'] for _,r in score2.iterrows()]
    table(c,35,430,[160,65,85,85],rows,row_h=24)
    image(c,tx/'figures/04_bias_mensal_heatmap.png',455,205,470,255)
    rounded(c,455,104,470,75,LIGHT,HexColor('#DDE8E0'))
    txt(c,475,156,'Leitura direta',9.7,GREEN,bold=True)
    txt(c,475,136,'Brasília tem o menor erro absoluto. Goiânia e Manaus têm os maiores desvios. Porto Alegre, Curitiba e São Paulo acompanham muito bem a variabilidade diária.',8.9,TEXT,max_width=430)
    footer(c); c.showPage()

    # PAGE 6 — extremes & TX90
    header(c,6,'ACURÁCIA DA TMAX | EXTREMOS E TX90')
    title(c,'Extremos: viés frio maior; TX90 ERA5 também mais baixo','Essa compensação parcial é central para entender por que a V2 funciona melhor que a temperatura absoluta sugeriria.')
    image(c,tx/'figures/07_bias_quente_vs_outros.png',35,205,430,215)
    image(c,tx/'figures/08_bias_tx90_por_capital.png',495,205,430,215)
    image(c,tx/'figures/09_f1_hot_wsdi.png',160,55,640,145)
    txt(c,35,42,'Interpretação: índice percentílico é autoconsistente ao dataset. O offset absoluto não desaparece, mas parte dele é absorvida pelo deslocamento do limiar TX90.',8.6,MID,max_width=880)
    footer(c); c.showPage()

    # PAGE 7 — city diagnostics
    header(c,7,'DIAGNÓSTICO POR CAPITAL')
    title(c,'Casos-chave para a discussão técnica','O desempenho não é homogêneo; cada cidade ajuda a entender um mecanismo diferente.')
    cards=[
        ('Porto Alegre',GREEN,'Caso mais consistente','r diário 0,96 | F1 TX90 0,76 | F1 WSDI 0,72 | bias anual de dias de evento ~0.'),
        ('Brasília',TEAL,'Menor erro absoluto','RMSE diário 1,33 °C | bias médio -0,39 °C. Boa referência de concordância de magnitude.'),
        ('Goiânia',ORANGE,'Maior offset frio','bias médio -2,92 °C; ainda assim F1 TX90 ~0,63. Mostra a compensação parcial do limiar percentílico.'),
        ('Manaus',PURPLE,'Alta comissão em persistência','bias frio, mas menos negativo recentemente; recall WSDI ~0,82 e precision ~0,32. Detecta muitos dias extras.'),
        ('Salvador',PURPLE,'Maior incerteza WSDI','F1 WSDI ~0,18. O problema não é só temperatura média: persistência/ordenamento dos extremos divergem.'),
        ('Belém',ORANGE,'Mudança temporal do bias','bias anual varia fortemente ao longo da série; exige cautela com não-estacionariedade da comparação.')]
    xs=[35,335,635,35,335,635]; ys=[320,320,320,120,120,120]
    for (name,col,head,desc),x,y in zip(cards,xs,ys):
        rounded(c,x,y,280,160,PALE,HexColor('#E1E9E3'))
        c.setFillColor(col); c.rect(x,y+148,280,12,stroke=0,fill=1)
        txt(c,x+16,y+122,name,13,col,bold=True)
        txt(c,x+16,y+95,head,9.5,TEXT,bold=True,max_width=248)
        txt(c,x+16,y+68,desc,8.6,MID,max_width=248,leading=10.5)
    footer(c); c.showPage()

    # PAGE 8 — decision
    header(c,8,'DECISÃO DE PUBLICAÇÃO')
    title(c,'Viabilidade de publicação: recomendação técnica','A V2 é a versão mais defensável, desde que as incertezas sejam comunicadas de forma explícita.')
    rounded(c,35,300,270,135,LIGHT,HexColor('#DDE8E0')); rounded(c,345,300,270,135,WARM,HexColor('#F3D8AA')); rounded(c,655,300,270,135,HexColor('#F7F3FA'),HexColor('#E8DDEE'))
    txt(c,55,403,'VERDE | PUBLICAR',13,GREEN,bold=True); txt(c,55,375,'heatwave_days\nevent_count\nocorrência mensal/anual',10,TEXT,max_width=220,leading=15)
    txt(c,365,403,'AMARELO | CAUTELA',13,ORANGE,bold=True); txt(c,365,375,'max_event_duration\nmean_event_duration\n+ nota metodológica',10,TEXT,max_width=220,leading=15)
    txt(c,675,403,'NÃO RECOMENDADO',13,PURPLE,bold=True); txt(c,675,375,'V1 como versão de referência\npara publicação',10,TEXT,max_width=220,leading=15)
    txt(c,35,260,'O que deve acompanhar o release',11,GREEN,bold=True)
    bullets=[
        'Definição WSDI/TX90: 1991-2020, janela de 5 dias, Tmax > P90, sequência >=6 dias; regra de 29/fev documentada.',
        'Regra de agregação: dias pela data de ocorrência; eventos/duração atribuídos ao período em que o evento termina.',
        'Limitação espacial: estação pontual versus pixel ERA5-Land ~11 km no centroide urbano.',
        'Bias frio absoluto do ERA5-Land e menor TX90 devem ser reportados; índice relativo reduz, mas não elimina, a discrepância.',
        'Expandir a validação para mais estações, biomas e coordenadas exatas de estação como próxima etapa.'
    ]
    yy=232
    for b in bullets:
        c.setFillColor(GREEN); c.circle(47,yy+3,2.3,stroke=0,fill=1)
        yy=txt(c,60,yy,b,9.4,TEXT,max_width=835,leading=12.2)-7
    rounded(c,120,50,720,46,GREEN,GREEN,12)
    txt(c,480,67,'DECISÃO SUGERIDA: PUBLICAR A V2 PARA DIAS E OCORRÊNCIA, COM RESSALVAS DOCUMENTADAS.',10.5,white,bold=True,align='center')
    footer(c); c.save()
    print(out)

if __name__=='__main__': main()
