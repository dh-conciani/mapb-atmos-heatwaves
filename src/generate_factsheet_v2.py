from pathlib import Path
import math, json, os
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import FancyBboxPatch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color, white, black
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth

# Paths are supplied by CLI; no environment-specific /mnt/data paths.

# -----------------------------
# Palette & typography
# -----------------------------
GREEN='#0B6E4F'; TEAL='#4CA6A6'; ORANGE='#F29F32'; YELLOW='#E4D33F'; PURPLE='#8F2AA8';
PINK='#D764A2'; RED='#D34B4B'; TEXT='#222C27'; MID='#5C6861'; LIGHT='#EAF2ED';
PALE='#F7F8F4'; WARM='#FFF5E6'; GRID='#DDE5E0'; GREY='#AAB5AE'; DARKGREY='#6D7A72'

# Register Roboto Condensed from the system; fallback to Helvetica if absent.
FONT_REG='/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Regular.ttf'
FONT_BOLD='/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Bold.ttf'
if Path(FONT_REG).exists():
    pdfmetrics.registerFont(TTFont('RC', FONT_REG))
    pdfmetrics.registerFont(TTFont('RCB', FONT_BOLD))
    FONT='RC'; FONTB='RCB'
else:
    FONT='Helvetica'; FONTB='Helvetica-Bold'

mpl.rcParams.update({
    'font.family':'Roboto Condensed',
    'font.size':12,
    'axes.titlesize':16,
    'axes.titleweight':'bold',
    'axes.labelsize':12,
    'axes.spines.top':False,
    'axes.spines.right':False,
    'axes.edgecolor':'#BFC9C2',
    'axes.labelcolor':TEXT,
    'xtick.color':MID,
    'ytick.color':MID,
    'grid.color':GRID,
    'grid.alpha':0.55,
    'figure.facecolor':'white',
    'axes.facecolor':'white',
    'savefig.facecolor':'white',
})

# -----------------------------
# Load data / CLI
# -----------------------------
import argparse
ap=argparse.ArgumentParser(description="Generate MapBiomas Atmosfera heatwave accuracy factsheet v2")
ap.add_argument('--heatwave-out', required=True)
ap.add_argument('--tmax-out', required=True)
ap.add_argument('--centroids', required=True)
ap.add_argument('--annual-validation', required=True, help='Annual station x V1/V2 validation CSV')
ap.add_argument('--assets-dir', required=True, help='Directory containing mapbiomas_logo.png and locator_map.png')
ap.add_argument('--outfile', required=True)
args=ap.parse_args()

hw=Path(args.heatwave_out); tx=Path(args.tmax_out)
ASSETS=Path(args.assets_dir)
out=Path(args.outfile); out.parent.mkdir(parents=True, exist_ok=True)
BUILD=out.parent/'_factsheet_v2_work'; CHARTS=BUILD/'charts'; CHARTS.mkdir(parents=True, exist_ok=True)
annual_raw=pd.read_csv(args.annual_validation)
pooled=pd.read_csv(hw/'tables/pooled_metrics.csv')
det=pd.read_csv(hw/'tables/event_detection_metrics.csv')
dur=pd.read_csv(hw/'tables/duration_common_support_metrics.csv')
score=pd.read_csv(tx/'tables/daily_scorecard_by_city.csv')
annual_err=pd.read_csv(tx/'tables/annual_error_metrics.csv')
hot=pd.read_csv(tx/'tables/hot_day_skill.csv')
wsdi=pd.read_csv(tx/'tables/wsdi_event_day_skill.csv')
tx90=pd.read_csv(tx/'tables/tx90_thresholds.csv')
ann_summary=pd.read_csv(tx/'tables/annual_bias_city_summary.csv')
cent=pd.read_csv(args.centroids)

CITY_ORDER=['Brasília','Curitiba','Goiânia','Manaus','Porto Alegre','Salvador','São Paulo','Belém','Belo Horizonte']

# -----------------------------
# Assets / diagnostic bias map
# -----------------------------
locator_path=ASSETS/'locator_map.png'
logo_path=ASSETS/'mapbiomas_logo.png'
if not locator_path.exists():
    raise FileNotFoundError(f"Missing locator map asset: {locator_path}")
if not logo_path.exists():
    raise FileNotFoundError(f"Missing MapBiomas logo asset: {logo_path}")

base=Image.open(locator_path).convert('RGBA')
px={
 'Manaus':(278-44,353-205), 'Belém':(453-44,330-205), 'Salvador':(601-44,494-205),
 'Brasília':(462-44,525-205), 'Goiânia':(438-44,550-205), 'Belo Horizonte':(518-44,595-205),
 'São Paulo':(479-44,648-205), 'Curitiba':(439-44,675-205), 'Porto Alegre':(411-44,741-205)
}
cmap=LinearSegmentedColormap.from_list('coldbias',['#DDEB98','#71C7BB','#2B8CBF','#4D55A9','#6C2D8C'])
norm=Normalize(vmin=0.3,vmax=3.2)
draw=ImageDraw.Draw(base,'RGBA')
try:
    font_small=ImageFont.truetype('/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Bold.ttf',16)
except:
    font_small=ImageFont.load_default()
for _,r in score.iterrows():
    city=r['city']; val=abs(float(r['bias_era5_minus_station']))
    if city not in px: continue
    x,y=px[city]; color=tuple(int(v*255) for v in cmap(norm(val))[:3])+(235,)
    rad=13; draw.ellipse((x-rad,y-rad,x+rad,y+rad),fill=color,outline=(255,255,255,255),width=3)
legend_y=base.height-34
for i,v in enumerate([0.5,1.5,2.5,3.0]):
    color=tuple(int(z*255) for z in cmap(norm(v))[:3])+(255,); xx=18+i*118
    draw.ellipse((xx,legend_y,xx+16,legend_y+16),fill=color,outline=(255,255,255,255),width=2)
    draw.text((xx+21,legend_y-1),f'-{v:.1f}°C',fill=(48,58,53,255),font=font_small)
BIAS_MAP=CHARTS/'bias_map.png'; base.save(BIAS_MAP)

# -----------------------------
# Charts
# -----------------------------
def savefig(path):
    plt.savefig(path, dpi=220, bbox_inches='tight', facecolor='white')
    plt.close()

# 1. Product annual scatter, V1/V2 side-by-side
fig,axs=plt.subplots(1,2,figsize=(10.8,4.1),sharex=True,sharey=True)
for ax,ver,col,title in zip(axs,['v1','v2'],['#AFC0CA',PURPLE],['V1','V2']):
    x=annual_raw['station_heatwave_days'].astype(float)
    y=annual_raw[f'{ver}_heatwave_days'].astype(float)
    ax.scatter(x,y,s=18,alpha=.68,color=col,edgecolor='none')
    mx=max(x.max(),y.max())
    ax.plot([0,mx],[0,mx],ls='--',lw=1.3,color='#303934')
    coef=np.polyfit(x,y,1); xx=np.array([0,mx]); ax.plot(xx,coef[0]*xx+coef[1],lw=2,color=ORANGE)
    ax.set_title(title,fontsize=18,color=GREEN if ver=='v1' else PURPLE)
    ax.grid(True,axis='both')
    ax.set_xlabel('Estação (dias/ano)')
    if ax is axs[0]: ax.set_ylabel('MapBiomas (dias/ano)')
    row=pooled[(pooled.period=='annual')&(pooled.metric=='heatwave_days')&(pooled.version==ver)&(~pooled.centered_by_city)].iloc[0]
    ax.text(.04,.96,f"r = {row.pearson_r:.2f}\nRMSE = {row.rmse:.1f}\nBias = {row.bias:+.1f}",transform=ax.transAxes,va='top',fontsize=12,
            bbox=dict(boxstyle='round,pad=.4',fc='white',ec='#D7DFDA'))
fig.suptitle('Dias anuais com onda de calor: estações x produto',fontsize=18,fontweight='bold',color=GREEN,y=1.02)
fig.tight_layout()
savefig(CHARTS/'annual_scatter.png')

# 2. V2 F1 annual/monthly by city
v2a=det[(det.period=='annual')&(det.version=='v2')&(det.city!='ALL_CITIES')].set_index('city').reindex(CITY_ORDER)
v2m=det[(det.period=='monthly')&(det.version=='v2')&(det.city!='ALL_CITIES')].set_index('city').reindex(CITY_ORDER)
y=np.arange(len(CITY_ORDER)); h=.35
fig,ax=plt.subplots(figsize=(8.3,4.7))
ax.barh(y-h/2,v2a['f1'],height=h,color=GREEN,label='Anual')
ax.barh(y+h/2,v2m['f1'],height=h,color=PURPLE,label='Mensal')
ax.set_yticks(y,CITY_ORDER); ax.invert_yaxis(); ax.set_xlim(0,1); ax.set_xlabel('F1-score')
ax.grid(True,axis='x'); ax.legend(frameon=False,ncol=2,loc='lower right')
ax.set_title('Detecção de ocorrência da V2 por capital',color=GREEN,pad=12)
for i,(a,m) in enumerate(zip(v2a['f1'],v2m['f1'])):
    ax.text(a+.015,i-h/2,f'{a:.2f}',va='center',fontsize=9,color=GREEN)
    ax.text(m+.015,i+h/2,f'{m:.2f}',va='center',fontsize=9,color=PURPLE)
fig.tight_layout(); savefig(CHARTS/'f1_annual_monthly_city.png')

# 3. Daily Tmax scorecard: correlation and RMSE paired as two panels
s=score.set_index('city').reindex(CITY_ORDER)
fig,axs=plt.subplots(1,2,figsize=(10.2,4.5))
ax=axs[0]
y=np.arange(len(CITY_ORDER)); ax.barh(y,s['pearson_r'],color=TEAL)
ax.set_yticks(y,CITY_ORDER); ax.invert_yaxis(); ax.set_xlim(0,1); ax.set_xlabel('Pearson r diário'); ax.grid(True,axis='x')
ax.set_title('Variabilidade diária',color=GREEN)
for i,v in enumerate(s['pearson_r']): ax.text(v+.012,i,f'{v:.2f}',va='center',fontsize=9)
ax=axs[1]
ax.barh(y,s['rmse'],color=ORANGE); ax.set_yticks(y,[]); ax.invert_yaxis(); ax.set_xlim(0,3.6); ax.set_xlabel('RMSE (°C)'); ax.grid(True,axis='x'); ax.set_title('Erro de magnitude',color=GREEN)
for i,v in enumerate(s['rmse']): ax.text(v+.05,i,f'{v:.2f}',va='center',fontsize=9)
fig.suptitle('Tmax estação x ERA5-Land',fontsize=18,fontweight='bold',color=GREEN,y=1.03)
fig.tight_layout(); savefig(CHARTS/'tmax_corr_rmse.png')

# 4. Annual bias trend + recent shift
fig,ax=plt.subplots(figsize=(11.8,4.9))
# climatology band
ax.axvspan(1991,2020,color='#EAF2ED',alpha=.7,zorder=0)
# non-key cities
keycols={'Manaus':ORANGE,'Belém':TEAL,'Salvador':PINK,'Goiânia':PURPLE,'Brasília':GREEN}
for city in CITY_ORDER:
    d=annual_err[annual_err.city==city].sort_values('year')
    if city in keycols:
        ax.plot(d.year,d.bias,lw=2.7,color=keycols[city],label=city,zorder=3)
    else:
        ax.plot(d.year,d.bias,lw=1.0,color='#C4CEC8',alpha=.75,zorder=1)
ax.axhline(0,color='#303934',lw=1.3)
ax.set_xlim(1985,2025); ax.set_ylim(-3.65,.4); ax.set_xlabel('Ano'); ax.set_ylabel('Bias anual (°C)')
ax.grid(True,axis='both'); ax.legend(ncol=5,frameon=False,loc='upper center',bbox_to_anchor=(0.5,1.02),fontsize=9.5)
ax.set_title('Offset anual de Tmax: ERA5-Land - estação',color=GREEN,pad=32,fontsize=19)
ax.text(1992,0.23,'1991-2020 = climatologia do TX90',fontsize=9.5,color=GREEN,va='top')
fig.tight_layout(); savefig(CHARTS/'annual_bias_trend_highlight.png')

# Recent shift bar (2021-25 minus 1991-2020)
rows=[]
for city in CITY_ORDER:
    d=annual_err[annual_err.city==city]
    b=d[d.year.between(1991,2020)].bias.mean(); r=d[d.year.between(2021,2025)].bias.mean(); rows.append((city,r-b,b,r))
shift=pd.DataFrame(rows,columns=['city','shift','baseline','recent']).set_index('city').reindex(CITY_ORDER)
fig,ax=plt.subplots(figsize=(7.4,4.6))
cols=[TEAL if v>0 else PURPLE for v in shift['shift']]
y=np.arange(len(shift)); ax.barh(y,shift['shift'],color=cols)
ax.axvline(0,color='#303934',lw=1.2); ax.set_yticks(y,shift.index); ax.invert_yaxis(); ax.set_xlabel('Mudança do bias (°C)\n2021-25 menos 1991-2020'); ax.grid(True,axis='x')
ax.set_title('O offset mudou depois da climatologia',color=GREEN,pad=10)
for i,v in enumerate(shift['shift']): ax.text(v+(0.03 if v>=0 else -0.03),i,f'{v:+.2f}',ha='left' if v>=0 else 'right',va='center',fontsize=9,fontweight='bold')
fig.tight_layout(); savefig(CHARTS/'recent_bias_shift.png')

# 5. Bias hot days vs other days
hdf=hot.set_index('city').reindex(CITY_ORDER)
y=np.arange(len(CITY_ORDER)); hh=.35
fig,ax=plt.subplots(figsize=(8.4,4.9))
ax.barh(y-hh/2,hdf['bias_on_station_hot_days'],height=hh,color=PURPLE,label='Dias > TX90 na estação')
ax.barh(y+hh/2,hdf['bias_on_other_days'],height=hh,color=TEAL,label='Demais dias')
ax.set_yticks(y,CITY_ORDER); ax.invert_yaxis(); ax.set_xlabel('ERA5 - estação (°C)'); ax.axvline(0,color='#303934',lw=1.1); ax.grid(True,axis='x'); ax.legend(frameon=False,loc='lower right')
ax.set_title('O viés fica mais negativo nos dias quentes',color=GREEN,pad=10)
fig.tight_layout(); savefig(CHARTS/'bias_hot_vs_other.png')

# 6. Mean TX90 bias by city
tmean=tx90.groupby('city',as_index=False).tx90_bias.mean().set_index('city').reindex(CITY_ORDER)
fig,ax=plt.subplots(figsize=(7.0,4.8))
y=np.arange(len(CITY_ORDER)); ax.barh(y,tmean.tx90_bias,color=TEAL)
ax.set_yticks(y,CITY_ORDER); ax.invert_yaxis(); ax.axvline(0,color='#303934',lw=1.1); ax.set_xlabel('TX90 ERA5 - estação (°C)'); ax.grid(True,axis='x'); ax.set_title('O TX90 do ERA5 também é mais baixo',color=GREEN,pad=10)
for i,v in enumerate(tmean.tx90_bias): ax.text(v-.06,i,f'{v:.2f}',ha='right',va='center',fontsize=9,color='white',fontweight='bold')
fig.tight_layout(); savefig(CHARTS/'tx90_bias_mean.png')

# 7. F1 hot-day and WSDI by city
wdf=wsdi.set_index('city').reindex(CITY_ORDER)
y=np.arange(len(CITY_ORDER)); hh=.35
fig,ax=plt.subplots(figsize=(8.5,4.9))
ax.barh(y-hh/2,hdf['f1_hot_day'],height=hh,color=TEAL,label='Dia > TX90')
ax.barh(y+hh/2,wdf['f1_event_day'],height=hh,color=PURPLE,label='Dia em sequência ≥6')
ax.set_yticks(y,CITY_ORDER); ax.invert_yaxis(); ax.set_xlim(0,.85); ax.set_xlabel('F1-score'); ax.grid(True,axis='x'); ax.legend(frameon=False,loc='lower right')
ax.set_title('Persistência é mais difícil que detectar um dia quente',color=GREEN,pad=10)
for i,(a,b) in enumerate(zip(hdf['f1_hot_day'],wdf['f1_event_day'])):
    ax.text(a+.01,i-hh/2,f'{a:.2f}',va='center',fontsize=8.7,color=TEAL)
    ax.text(b+.01,i+hh/2,f'{b:.2f}',va='center',fontsize=8.7,color=PURPLE)
fig.tight_layout(); savefig(CHARTS/'f1_hot_wsdi_v2.png')

# 8. WSDI annual correlation vs event-day bias diagnostic
fig,ax=plt.subplots(figsize=(7.0,4.9))
for _,r in wdf.reset_index().iterrows():
    ax.scatter(r.annual_event_days_bias,r.annual_event_days_pearson_r,s=80,color=PURPLE,alpha=.82)
    ax.text(r.annual_event_days_bias+.15,r.annual_event_days_pearson_r+.01,r.city,fontsize=9)
ax.axvline(0,color='#303934',lw=1.1); ax.set_xlabel('Bias anual de dias WSDI (dias/ano)'); ax.set_ylabel('Pearson r anual'); ax.grid(True)
ax.set_title('Correlação alta pode coexistir com comissão',color=GREEN,pad=10)
ax.set_xlim(-3,10.5); ax.set_ylim(0,1.03)
fig.tight_layout(); savefig(CHARTS/'wsdi_corr_bias.png')

# 9. Minimal duration comparison (common support)
dann=dur[dur.period=='annual'].copy()
fig,axs=plt.subplots(1,2,figsize=(7.7,3.6))
for ax,metric,label in zip(axs,['max_event_duration','mean_event_duration'],['Duração máxima','Duração média']):
    d=dann[dann.metric==metric].set_index('version').reindex(['v1','v2'])
    ax.bar(['V1','V2'],d['rmse'],color=['#AFC0CA',PURPLE])
    ax.set_ylabel('RMSE (dias)'); ax.set_title(label,color=GREEN); ax.grid(True,axis='y')
    for i,v in enumerate(d['rmse']): ax.text(i,v+.08,f'{v:.2f}',ha='center',fontsize=10,fontweight='bold')
fig.suptitle('Duração: ganho menos consistente',fontsize=17,fontweight='bold',color=GREEN,y=1.02)
fig.tight_layout(); savefig(CHARTS/'duration_common_support.png')

# -----------------------------
# Report helpers
# -----------------------------
W,H=960,540
C=lambda x: HexColor(x)

def text(c,x,y,s,size=11,color=TEXT,bold=False,maxw=None,leading=None,align='left'):
    font=FONTB if bold else FONT
    c.setFillColor(C(color) if isinstance(color,str) else color); c.setFont(font,size)
    if maxw is None:
        if align=='center': c.drawCentredString(x,y,s)
        elif align=='right': c.drawRightString(x,y,s)
        else: c.drawString(x,y,s)
        return y
    leading=leading or size*1.17
    words=str(s).split(); lines=[]; cur=''
    for w in words:
        t=(cur+' '+w).strip()
        if stringWidth(t,font,size)<=maxw: cur=t
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    yy=y
    for line in lines:
        if align=='center': c.drawCentredString(x,yy,line)
        elif align=='right': c.drawRightString(x,yy,line)
        else: c.drawString(x,yy,line)
        yy-=leading
    return yy

def line(c,x1,y1,x2,y2,color='#D7DFDA',width=1):
    c.setStrokeColor(C(color)); c.setLineWidth(width); c.line(x1,y1,x2,y2)

def img(c,path,x,y,w,h,preserve=True):
    path=Path(path)
    if not path.exists(): return
    ir=ImageReader(str(path)); iw,ih=ir.getSize()
    if preserve:
        sc=min(w/iw,h/ih); nw=iw*sc; nh=ih*sc; x+=(w-nw)/2; y+=(h-nh)/2; w=nw; h=nh
    c.drawImage(ir,x,y,w,h,mask='auto',preserveAspectRatio=True)

def roundbox(c,x,y,w,h,fill='#F7F8F4',stroke='#DDE5E0',rad=10):
    c.setFillColor(C(fill)); c.setStrokeColor(C(stroke)); c.setLineWidth(1); c.roundRect(x,y,w,h,rad,fill=1,stroke=1)

def page_header(c,title,page,section='MAPBIOMAS ATMOSFERA | ANÁLISE DE ACURÁCIA'):
    # logo + page title inspired by official factsheets
    if (ASSETS/'mapbiomas_logo.png').exists():
        img(c,ASSETS/'mapbiomas_logo.png',26,H-53,155,34)
    else:
        text(c,28,H-31,'MAPBIOMAS',13,TEAL,bold=True)
    text(c,166,H-31,title,18,TEXT,bold=True,maxw=690)
    # multicolor rule under header
    y=H-58
    c.setFillColor(C(ORANGE)); c.rect(0,y,235,4,stroke=0,fill=1)
    c.setFillColor(C('#7DBA49')); c.rect(235,y,240,4,stroke=0,fill=1)
    c.setFillColor(C(YELLOW)); c.rect(475,y,250,4,stroke=0,fill=1)
    c.setFillColor(C('#40B8B1')); c.rect(725,y,235,4,stroke=0,fill=1)
    # page badge
    c.setFillColor(C('#7DBA49')); c.circle(920,H-31,18,stroke=0,fill=1)
    c.setFillColor(C(YELLOW)); c.circle(934,H-42,8,stroke=0,fill=1)
    text(c,920,H-36,str(page),10,white,bold=True,align='center')

def footer(c):
    text(c,28,16,'Fonte: MapBiomas / ERA5-Land / estações meteorológicas | 1985-2025',6.8,'#8A958E')
    text(c,930,16,'versão técnica | 14/10/2026',6.8,'#9AA59C',align='right')

def big_num(c,x,y,value,label,color=TEAL,unit=None):
    text(c,x,y,value,30,color,bold=True)
    if unit: text(c,x+stringWidth(value,FONTB,30)+4,y+1,unit,16,color)
    text(c,x,y-24,label,10,MID,maxw=180,leading=11)

def callout(c,x,y,w,h,head,body,accent=GREEN,fill='#F7F8F4'):
    roundbox(c,x,y,w,h,fill,stroke='#D9E2DC',rad=8)
    c.setFillColor(C(accent)); c.rect(x,y+h-5,w,5,stroke=0,fill=1)
    text(c,x+14,y+h-27,head,11.2,accent,bold=True,maxw=w-28)
    text(c,x+14,y+h-49,body,9.5,TEXT,maxw=w-28,leading=11)

# -----------------------------
# Build 9-page PDF
# -----------------------------
c=canvas.Canvas(str(out),pagesize=(W,H)); c.setTitle('MapBiomas Atmosfera - Analise de acuracia de ondas de calor v2')

# PAGE 1 executive
page_header(c,'Validação integrada das ondas de calor',1)
text(c,35,438,'SUMÁRIO EXECUTIVO',11,GREEN,bold=True)
text(c,35,395,'V2 é tecnicamente viável',30,GREEN,bold=True)
text(c,35,360,'para publicação de dias e ocorrência',30,GREEN,bold=True)
text(c,35,326,'A evidência combina validação do produto final e da Tmax diária usada no ERA5-Land.',12,MID,maxw=690)
# large summary numbers, more MapBiomas-like and less card-based
big_num(c,35,250,'0,71','Pearson r anual | V2',PURPLE)
big_num(c,225,250,'12,2','RMSE anual | V2',ORANGE,'dias')
big_num(c,425,250,'0,69','F1 ocorrência anual',PURPLE)
big_num(c,615,250,'-0,4 a -2,9','bias Tmax diário',TEAL,'°C')
big_num(c,805,250,'0,40-0,76','F1 dias > TX90',GREEN)
line(c,35,190,925,190,'#DDE5E0',1)
callout(c,35,85,570,85,'Mensagem central','ERA5-Land é sistematicamente mais frio em temperatura absoluta. Como o TX90 é calculado no próprio ERA5, o limiar também fica mais baixo e parte do offset se compensa. O restante da incerteza está na variabilidade diária e, sobretudo, na persistência.',GREEN,'#EEF5F0')
callout(c,630,85,295,85,'Decisão sugerida','Publicar V2 para heatwave_days, event_count e ocorrência mensal/anual. Duração permanece em amarelo: publicar com nota metodológica e cautela.',ORANGE,'#FFF7EA')
footer(c); c.showPage()

# PAGE 2 method + locator map
page_header(c,'Como a acurácia foi avaliada',2)
text(c,35,448,'Duas linhas de evidência independentes',25,GREEN,bold=True)
text(c,35,422,'A recomendação não depende de uma única comparação.',11,MID)
# locator map
img(c,ASSETS/'locator_map.png',35,88,390,310)
text(c,45,80,'9 capitais | centroides urbanos MapBiomas 2025 (classe 24)',8.2,MID)
# workflow on right
text(c,465,382,'1',18,white,bold=True,align='center'); c.setFillColor(C(GREEN)); c.circle(465,388,19,stroke=0,fill=1); text(c,465,382,'1',14,white,bold=True,align='center')
text(c,498,392,'Produto final V1 x V2',17,GREEN,bold=True)
text(c,498,366,'Listas de eventos de estações x agregados anuais e mensais.',10.5,TEXT,maxw=400)
text(c,498,332,'Indicadores',10,GREEN,bold=True); text(c,498,311,'heatwave_days | event_count | duração',10,TEXT)
text(c,498,282,'Métricas',10,GREEN,bold=True); text(c,498,261,'Pearson | CCC | RMSE | Bias | F1 | Recall',10,TEXT)
line(c,465,235,915,235,'#DDE5E0',1)
c.setFillColor(C(PURPLE)); c.circle(465,203,19,stroke=0,fill=1); text(c,465,197,'2',14,white,bold=True,align='center')
text(c,498,207,'Dado de entrada: Tmax diária',17,PURPLE,bold=True)
text(c,498,181,'Estação x ERA5-Land no mesmo centroide urbano, 1985-2025.',10.5,TEXT,maxw=400)
text(c,498,147,'Diagnósticos',10,PURPLE,bold=True); text(c,498,126,'bias/RMSE | sazonalidade | extremos | TX90 | lag | persistência ≥6 dias',10,TEXT,maxw=400)
# footer stats
text(c,465,79,'14.975',24,ORANGE,bold=True); text(c,552,79,'dias/capital',10,MID)
text(c,640,79,'~99,5%',24,TEAL,bold=True); text(c,739,79,'cobertura estação',10,MID)
footer(c); c.showPage()

# PAGE 3 annual product validation
page_header(c,'Validação do produto | escala anual',3)
text(c,35,448,'V2 melhora associação, erro, viés e detecção',25,GREEN,bold=True)
# key metrics as large numerals
# helper pooled
getp=lambda ver: pooled[(pooled.period=='annual')&(pooled.metric=='heatwave_days')&(pooled.version==ver)&(~pooled.centered_by_city)].iloc[0]
a1=getp('v1'); a2=getp('v2')
da=det[(det.period=='annual')&(det.city=='ALL_CITIES')].set_index('version')
# left numbers
text(c,35,387,'V1',12,'#7FAFC1',bold=True); text(c,90,387,'V2',12,PURPLE,bold=True)
# metric lines
metrics=[('Pearson r',a1.pearson_r,a2.pearson_r,'higher'),('CCC',a1.ccc,a2.ccc,'higher'),('RMSE',a1.rmse,a2.rmse,'lower'),('Bias',a1.bias,a2.bias,'zero'),('F1 ocorrência',da.loc['v1','f1'],da.loc['v2','f1'],'higher'),('Recall',da.loc['v1','recall'],da.loc['v2','recall'],'higher')]
y=354
for lab,v1,v2,typ in metrics:
    text(c,35,y,lab,10.5,TEXT,bold=True)
    text(c,148,y,f'{v1:.2f}' if abs(v1)<10 else f'{v1:.1f}',13,'#7FAFC1',bold=True,align='right')
    text(c,208,y,f'{v2:.2f}' if abs(v2)<10 else f'{v2:.1f}',13,PURPLE,bold=True,align='right')
    line(c,35,y-9,220,y-9,'#E3E9E5',.7); y-=42
img(c,CHARTS/'annual_scatter.png',260,132,660,290)
callout(c,35,76,375,72,'Leitura','A V2 não ganha apenas em correlação: reduz RMSE, deixa o bias anual próximo de zero e aumenta fortemente a detecção de anos com evento.',GREEN,'#EEF5F0')
callout(c,430,76,490,72,'Decisão','A V1 não é uma referência defensável para publicação. A V2 é a versão operacional para dias e ocorrência.',PURPLE,'#F7F1F9')
footer(c); c.showPage()

# PAGE 4 monthly + duration
page_header(c,'Validação do produto | escala mensal e duração',4)
text(c,35,448,'A vantagem da V2 permanece na escala mensal',25,GREEN,bold=True)
text(c,35,421,'A escala mensal é mais exigente: o produto precisa detectar o evento e posicioná-lo no mês correto.',11,MID)
# metrics strip
m2=pooled[(pooled.period=='monthly')&(pooled.metric=='heatwave_days')&(pooled.version=='v2')&(~pooled.centered_by_city)].iloc[0]
dm=det[(det.period=='monthly')&(det.city=='ALL_CITIES')].set_index('version')
big_num(c,35,355,f'{m2.pearson_r:.2f}','Pearson mensal V2',PURPLE)
big_num(c,205,355,f'{m2.rmse:.2f}','RMSE mensal',ORANGE,'dias')
big_num(c,365,355,f'{m2.bias:+.2f}','Bias mensal',GREEN,'dias')
big_num(c,530,355,f"{dm.loc['v2','f1']:.2f}",'F1 ocorrência mensal',PURPLE)
big_num(c,710,355,f"{dm.loc['v2','recall']:.2f}",'Recall mensal',TEAL)
img(c,CHARTS/'f1_annual_monthly_city.png',35,92,560,235)
img(c,CHARTS/'duration_common_support.png',615,150,300,150)
callout(c,615,80,300,62,'Duração = cautela','Na comparação em common support, a V2 melhora a duração média, mas o ganho não é consistente para duração máxima e a amostra é pequena.',ORANGE,'#FFF7EA')
footer(c); c.showPage()

# PAGE 5 absolute Tmax + maps
page_header(c,'Acurácia da Tmax | estação x ERA5-Land',5)
text(c,35,448,'Boa covariação diária, mas viés frio sistemático',25,GREEN,bold=True)
text(c,35,421,'Erro absoluto e capacidade de acompanhar oscilações são dimensões diferentes.',11,MID)
img(c,BIAS_MAP,35,96,355,290)
text(c,35,82,'Mapa diagnóstico do bias médio diário (ERA5 - estação).',8.8,MID)
img(c,CHARTS/'tmax_corr_rmse.png',420,172,500,225)
# key city messages bottom right
callout(c,420,78,158,75,'Brasília','Menor RMSE diário: 1,33 °C; bias médio -0,39 °C.',GREEN,'#EEF5F0')
callout(c,590,78,158,75,'Goiânia','Maior offset frio: bias médio -2,92 °C; RMSE 3,25 °C.',PURPLE,'#F7F1F9')
callout(c,760,78,160,75,'Porto Alegre','Maior r diário: 0,96; forte acompanhamento da variabilidade.',TEAL,'#EEF8F7')
footer(c); c.showPage()

# PAGE 6 annual offset and key mechanisms
page_header(c,'Acurácia da Tmax | offset anual e não-estacionariedade',6)
text(c,35,448,'O offset anual não é constante ao longo da série',25,GREEN,bold=True)
text(c,35,421,'Isso importa porque o TX90 da V2 é fixado pela climatologia 1991-2020.',11,MID)
img(c,CHARTS/'annual_bias_trend_highlight.png',35,178,630,230)
img(c,CHARTS/'recent_bias_shift.png',685,178,240,230)
# messages
callout(c,35,78,280,78,'Manaus | comissão recente','Bias continua frio, mas fica menos negativo: -2,62 °C em 1991-2020 para -1,99 °C em 2021-25. Com TX90 ancorado em 1991-2020, a Tmax recente fica relativamente mais alta frente ao próprio limiar.',ORANGE,'#FFF7EA')
callout(c,335,78,280,78,'Belém | tendência oposta','O bias fica mais negativo no fim da série: -1,67 °C em 1991-2020 para -2,36 °C em 2021-25. É o caso mais forte de não-estacionariedade da comparação.',TEAL,'#EEF8F7')
callout(c,635,78,290,78,'Salvador | não é só offset','O bias frio persiste e se torna um pouco mais negativo, mas o baixo skill WSDI aponta também divergência na persistência/ordenação dos extremos.',PURPLE,'#F7F1F9')
footer(c); c.showPage()

# PAGE 7 TX90 compensation
page_header(c,'Extremos e TX90 | por que a V2 ainda funciona',7)
text(c,35,448,'O limiar relativo compensa parte do bias absoluto',25,GREEN,bold=True)
text(c,35,421,'O ERA5 é mais frio, mas seu TX90 também é mais baixo. O que importa para a V2 é Tmax > TX90 e a persistência.',11,MID)
# mechanism diagram top-left
roundbox(c,35,292,235,92,'#EEF5F0','#DDE7E1',10)
text(c,55,355,'ESTAÇÃO',10,GREEN,bold=True); text(c,55,330,'Tmax',17,TEXT,bold=True); text(c,142,330,'>',17,GREEN,bold=True); text(c,175,330,'TX90',17,TEXT,bold=True)
roundbox(c,35,185,235,92,'#F7F1F9','#E9DCEC',10)
text(c,55,248,'ERA5-LAND',10,PURPLE,bold=True); text(c,55,223,'Tmax mais fria',15,PURPLE,bold=True); text(c,165,223,'>',17,PURPLE,bold=True); text(c,194,223,'TX90',15,PURPLE,bold=True)
text(c,55,201,'limiar também mais baixo',9.5,MID)
text(c,152,160,'COMPENSAÇÃO PARCIAL',11,GREEN,bold=True,align='center')
img(c,CHARTS/'bias_hot_vs_other.png',300,180,305,215)
img(c,CHARTS/'tx90_bias_mean.png',620,180,305,215)
callout(c,35,78,890,65,'Leitura técnica','Em todas as capitais, o bias é mais negativo nos dias que a estação classifica como quentes. Mesmo assim, o TX90 do ERA5 também é deslocado para baixo. Portanto, bias absoluto frio não implica necessariamente subdetecção do índice percentílico.',GREEN,'#EEF5F0')
footer(c); c.showPage()

# PAGE 8 persistence + city cases
page_header(c,'Persistência WSDI | onde a comissão aparece',8)
text(c,35,448,'Persistência é o componente mais difícil',25,GREEN,bold=True)
text(c,35,421,'Detectar um dia acima do TX90 é mais fácil que reproduzir uma sequência de 6 ou mais dias.',11,MID)
img(c,CHARTS/'f1_hot_wsdi_v2.png',35,170,500,235)
img(c,CHARTS/'wsdi_corr_bias.png',555,170,370,235)
# city callouts
callout(c,35,78,280,72,'Porto Alegre | referência','F1 WSDI 0,72; bias anual de dias de evento ~0,20 dia/ano. Melhor equilíbrio entre detecção e magnitude.',GREEN,'#EEF5F0')
callout(c,335,78,280,72,'Manaus | alta comissão','Recall WSDI 0,82, precision 0,32 e bias +8,15 dias/ano. Identifica anos extremos, mas adiciona muitos dias extras.',ORANGE,'#FFF7EA')
callout(c,635,78,290,72,'Salvador | maior incerteza','F1 WSDI 0,18 e r anual 0,32. A divergência envolve persistência e ordenamento dos extremos, não apenas o bias médio.',PURPLE,'#F7F1F9')
footer(c); c.showPage()

# PAGE 9 decision
page_header(c,'Decisão de publicação',9)
text(c,35,448,'Viabilidade de publicação: recomendação técnica',25,GREEN,bold=True)
text(c,35,421,'A V2 é a versão mais defensável, desde que a incerteza seja comunicada explicitamente.',11,MID)
# three columns with large symbols/numbers
c.setFillColor(C('#7DBA49')); c.circle(155,345,42,stroke=0,fill=1); text(c,155,333,'✓',30,white,bold=True,align='center')
text(c,65,275,'PUBLICAR',17,GREEN,bold=True); text(c,65,245,'heatwave_days\nevent_count\nocorrência mensal/anual',11,TEXT,maxw=220,leading=16)
line(c,320,175,320,390,'#E0E7E2',1)
c.setFillColor(C(YELLOW)); c.circle(480,345,42,stroke=0,fill=1); text(c,480,333,'!',30,TEXT,bold=True,align='center')
text(c,390,275,'CAUTELA',17,ORANGE,bold=True); text(c,390,245,'max_event_duration\nmean_event_duration\n+ nota metodológica',11,TEXT,maxw=220,leading=16)
line(c,640,175,640,390,'#E0E7E2',1)
c.setFillColor(C(PURPLE)); c.circle(805,345,42,stroke=0,fill=1); text(c,805,334,'×',31,white,bold=True,align='center')
text(c,715,275,'NÃO USAR COMO REFERÊNCIA',15,PURPLE,bold=True,maxw=190); text(c,715,235,'V1 para publicação operacional.',11,TEXT,maxw=180)
text(c,35,150,'O que deve acompanhar o release',12,GREEN,bold=True)
bul=[
 'Definição WSDI/TX90: 1991-2020, janela de 5 dias, Tmax > P90, sequência ≥6 dias e regra de 29/fev.',
 'Regra de agregação: dias pela data de ocorrência; eventos e duração atribuídos ao período em que terminam.',
 'Representatividade espacial: estação pontual x célula ERA5-Land ~11 km no centroide urbano.',
 'Reportar o bias frio absoluto e a não-estacionariedade observada em algumas capitais; o índice relativo reduz, mas não elimina, a discrepância.',
 'Próxima etapa: ampliar estações, biomas e testes nas coordenadas exatas das estações.'
]
y=126
for b in bul:
    c.setFillColor(C(GREEN)); c.circle(42,y+3,2.2,stroke=0,fill=1)
    y=text(c,54,y,b,9.7,TEXT,maxw=860,leading=11.2)-5
roundbox(c,205,34,550,33,GREEN,GREEN,8); text(c,480,45,'DECISÃO SUGERIDA: PUBLICAR A V2 PARA DIAS E OCORRÊNCIA, COM RESSALVAS DOCUMENTADAS.',10.2,white,bold=True,align='center')
footer(c); c.save()
print(out)
