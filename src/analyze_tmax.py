#!/usr/bin/env python3
"""Reproduce daily station Tmax vs ERA5-Land accuracy diagnostics and TX90/WSDI diagnostics."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr, linregress

from style_mapbiomas import COLORS, MONTHS_PT, apply_style, ensure_dirs

CITY_MAP = {
    'brasilia':'Brasilia', 'curitiba':'Curitiba', 'goiania':'Goiania', 'manaus':'Manaus',
    'porto_alegre':'PortoAlegre', 'salvador':'Salvador', 'sao_paulo':'SaoPaulo',
    'belem':'Belem', 'belo_horizonte':'BeloHorizonte'
}
CITY_LABELS = {
    'brasilia':'Brasília','curitiba':'Curitiba','goiania':'Goiânia','manaus':'Manaus',
    'porto_alegre':'Porto Alegre','salvador':'Salvador','sao_paulo':'São Paulo',
    'belem':'Belém','belo_horizonte':'Belo Horizonte'
}


def ccc(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float)
    mx,my=x.mean(),y.mean(); vx,vy=x.var(),y.var(); cov=np.mean((x-mx)*(y-my))
    den=vx+vy+(mx-my)**2
    return np.nan if den==0 else 2*cov/den


def paired_stats(d):
    d=d.dropna(subset=['station_tmax_c','era5_tmax_c']).copy()
    x=d.station_tmax_c.astype(float); y=d.era5_tmax_c.astype(float); e=y-x
    r=pearsonr(x,y).statistic if len(d)>1 and x.nunique()>1 and y.nunique()>1 else np.nan
    rho=spearmanr(x,y).statistic if len(d)>1 and x.nunique()>1 and y.nunique()>1 else np.nan
    return {'n':len(d),'pearson_r':r,'spearman_rho':rho,'ccc':ccc(x,y),
            'bias_era5_minus_station':e.mean(),'mae':np.abs(e).mean(),
            'rmse':np.sqrt(np.mean(e**2)),'error_p05':e.quantile(.05),'error_p95':e.quantile(.95)}


def load_data(station_file, era5_dir):
    s=pd.read_csv(station_file); s['date']=pd.to_datetime(s['Data'],format='%d-%b-%Y')
    frames=[]
    for cid,col in CITY_MAP.items():
        x=s[['date',col]].copy().rename(columns={col:'station_tmax_c'}); x['city_id']=cid; x['city']=CITY_LABELS[cid]; frames.append(x)
    station=pd.concat(frames,ignore_index=True)
    eframes=[]
    for cid in CITY_MAP:
        path=Path(era5_dir)/f'ERA5_Tmax_daily_{cid}_1985_2025.csv'
        e=pd.read_csv(path); e['date']=pd.to_datetime(e['date'])
        e=e[['date','city_id','centroid_lon','centroid_lat','tmax_era5_c']].rename(columns={'tmax_era5_c':'era5_tmax_c'})
        eframes.append(e)
    era5=pd.concat(eframes,ignore_index=True)
    d=station.merge(era5,on=['date','city_id'],how='left',validate='one_to_one')
    d['delta_t']=d.era5_tmax_c-d.station_tmax_c; d['year']=d.date.dt.year; d['month']=d.date.dt.month
    return d


def build_tx90(d,col):
    clim=d[(d.date>=pd.Timestamp('1991-01-01'))&(d.date<=pd.Timestamp('2020-12-31'))][['date',col]].dropna().copy()
    clim=clim[~((clim.date.dt.month==2)&(clim.date.dt.day==29))]
    by_md={(m,day):g[col].to_numpy() for (m,day),g in clim.groupby([clim.date.dt.month,clim.date.dt.day])}
    template=pd.date_range('2001-01-01','2001-12-31',freq='D'); out={}
    for t in template:
        vals=[]
        for off in [-2,-1,0,1,2]:
            dd=t+pd.Timedelta(days=off); vals.extend(by_md.get((dd.month,dd.day),[]))
        out[(t.month,t.day)]=np.nanpercentile(vals,90) if vals else np.nan
    return out


def event_membership(vals,minrun=6):
    vals=np.asarray(vals); out=np.full(len(vals),np.nan); valid=~pd.isna(vals); out[valid]=0
    start=None
    for i,v in enumerate(vals):
        if pd.isna(v) or not bool(v):
            if start is not None:
                if i-start>=minrun: out[start:i]=1
                start=None
        elif start is None: start=i
    if start is not None and len(vals)-start>=minrun: out[start:]=1
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--station',required=True)
    ap.add_argument('--era5-dir',required=True)
    ap.add_argument('--outdir',required=True)
    args=ap.parse_args()
    apply_style(); out=Path(args.outdir); figs=out/'figures'; tables=out/'tables'; ensure_dirs(figs,tables)
    data=load_data(args.station,args.era5_dir); data.to_csv(tables/'paired_daily_data.csv',index=False)

    # Daily scorecard
    rows=[]
    for cid,d in data.groupby('city_id'):
        rows.append({'city_id':cid,'city':CITY_LABELS[cid],**paired_stats(d),
                     'station_missing_days':int(d.station_tmax_c.isna().sum()),
                     'era5_missing_days':int(d.era5_tmax_c.isna().sum())})
    score=pd.DataFrame(rows).sort_values('rmse'); score.to_csv(tables/'daily_scorecard_by_city.csv',index=False)

    monthly=(data.groupby(['city_id','month'],as_index=False)
             .agg(bias=('delta_t','mean'),mae=('delta_t',lambda s:np.nanmean(np.abs(s))),
                  rmse=('delta_t',lambda s:np.sqrt(np.nanmean(np.square(s)))),n=('delta_t','count')))
    monthly['city']=monthly.city_id.map(CITY_LABELS); monthly.to_csv(tables/'monthly_error_metrics.csv',index=False)
    annual=(data.groupby(['city_id','year'],as_index=False)
            .agg(bias=('delta_t','mean'),mae=('delta_t',lambda s:np.nanmean(np.abs(s))),
                 rmse=('delta_t',lambda s:np.sqrt(np.nanmean(np.square(s)))),n=('delta_t','count')))
    annual['city']=annual.city_id.map(CITY_LABELS); annual.to_csv(tables/'annual_error_metrics.csv',index=False)

    trends=[]
    for cid,d in annual.groupby('city_id'):
        lr=linregress(d.year,d.bias)
        trends.append({'city_id':cid,'city':CITY_LABELS[cid],'bias_trend_c_per_decade':lr.slope*10,'p_value':lr.pvalue,
                       'min_annual_bias':d.bias.min(),'min_bias_year':int(d.loc[d.bias.idxmin(),'year']),
                       'max_annual_bias':d.bias.max(),'max_bias_year':int(d.loc[d.bias.idxmax(),'year'])})
    pd.DataFrame(trends).to_csv(tables/'annual_bias_trends.csv',index=False)

    # Quantile bias
    qrows=[]
    for cid,d in data.groupby('city_id'):
        dd=d.dropna(subset=['station_tmax_c','era5_tmax_c'])
        for q in [.5,.9,.95,.99]:
            st=dd.station_tmax_c.quantile(q); er=dd.era5_tmax_c.quantile(q)
            qrows.append({'city_id':cid,'city':CITY_LABELS[cid],'quantile':q,'station_tmax':st,'era5_tmax':er,'era5_minus_station':er-st})
    qdf=pd.DataFrame(qrows); qdf.to_csv(tables/'quantile_bias.csv',index=False)

    # lag diagnostic
    lags=[]
    for cid,d in data.groupby('city_id'):
        dd=d.sort_values('date').set_index('date'); x=dd.station_tmax_c
        for lag in [-2,-1,0,1,2]:
            y=dd.era5_tmax_c.shift(lag); ok=x.notna()&y.notna()
            lags.append({'city_id':cid,'city':CITY_LABELS[cid],'era5_shift_days':lag,'pearson_r':x[ok].corr(y[ok]),'n':int(ok.sum())})
    lagdf=pd.DataFrame(lags); lagdf.to_csv(tables/'lag_diagnostic.csv',index=False)

    # TX90 / hot-day / WSDI
    txrows=[]; hotrows=[]; eventrows=[]; annual_event=[]
    for cid,d0 in data.groupby('city_id'):
        d=d0.sort_values('date').copy(); stx=build_tx90(d,'station_tmax_c'); etx=build_tx90(d,'era5_tmax_c')
        keys=[(2,28) if (dt.month==2 and dt.day==29) else (dt.month,dt.day) for dt in d.date]
        d['station_tx90']=[stx.get(k,np.nan) for k in keys]; d['era5_tx90']=[etx.get(k,np.nan) for k in keys]
        d['station_hot']=np.where(d.station_tmax_c.notna(),(d.station_tmax_c>d.station_tx90).astype(float),np.nan)
        d['era5_hot']=np.where(d.era5_tmax_c.notna(),(d.era5_tmax_c>d.era5_tx90).astype(float),np.nan)
        for k in stx:
            txrows.append({'city_id':cid,'city':CITY_LABELS[cid],'month_day':f'{k[0]:02d}-{k[1]:02d}',
                           'station_tx90':stx[k],'era5_tx90':etx[k],'tx90_bias':etx[k]-stx[k]})
        v=d.dropna(subset=['station_hot','era5_hot']); obs=v.station_hot.astype(bool); pred=v.era5_hot.astype(bool)
        tp=int((obs&pred).sum()); fp=int((~obs&pred).sum()); fn=int((obs&~pred).sum()); tn=int((~obs&~pred).sum())
        precision=tp/(tp+fp) if tp+fp else np.nan; recall=tp/(tp+fn) if tp+fn else np.nan
        f1=2*precision*recall/(precision+recall) if precision+recall else np.nan
        hotrows.append({'city_id':cid,'city':CITY_LABELS[cid],'n':len(v),'precision_hot_day':precision,'recall_hot_day':recall,'f1_hot_day':f1,
                        'bias_on_station_hot_days':v.loc[obs,'delta_t'].mean(),'bias_on_other_days':v.loc[~obs,'delta_t'].mean(),
                        'tp':tp,'fp':fp,'fn':fn,'tn':tn})
        d['station_event_day']=event_membership(d.station_hot.values,6); d['era5_event_day']=event_membership(d.era5_hot.values,6)
        vv=d.dropna(subset=['station_event_day','era5_event_day']); oe=vv.station_event_day.astype(bool); pe=vv.era5_event_day.astype(bool)
        tp=int((oe&pe).sum()); fp=int((~oe&pe).sum()); fn=int((oe&~pe).sum()); tn=int((~oe&~pe).sum())
        precision=tp/(tp+fp) if tp+fp else np.nan; recall=tp/(tp+fn) if tp+fn else np.nan; f1=2*precision*recall/(precision+recall) if precision+recall else np.nan
        aa=d.groupby(d.date.dt.year)[['station_event_day','era5_event_day']].sum(min_count=1).dropna()
        eventrows.append({'city_id':cid,'city':CITY_LABELS[cid],'precision_event_day':precision,'recall_event_day':recall,'f1_event_day':f1,
                          'station_event_days_total':int(oe.sum()),'era5_event_days_total':int(pe.sum()),
                          'annual_event_days_pearson_r':aa.station_event_day.corr(aa.era5_event_day),
                          'annual_event_days_bias':(aa.era5_event_day-aa.station_event_day).mean(),
                          'annual_event_days_rmse':np.sqrt(np.mean((aa.era5_event_day-aa.station_event_day)**2)),
                          'tp':tp,'fp':fp,'fn':fn,'tn':tn})
        for y,row in aa.iterrows():
            annual_event.append({'city_id':cid,'city':CITY_LABELS[cid],'year':int(y),'station_event_days':row.station_event_day,'era5_event_days':row.era5_event_day})
    txdf=pd.DataFrame(txrows); hotdf=pd.DataFrame(hotrows); eventdf=pd.DataFrame(eventrows)
    txdf.to_csv(tables/'tx90_thresholds.csv',index=False); hotdf.to_csv(tables/'hot_day_skill.csv',index=False); eventdf.to_csv(tables/'wsdi_event_day_skill.csv',index=False)
    pd.DataFrame(annual_event).to_csv(tables/'annual_wsdi_event_days.csv',index=False)

    # Annual bias summary, including recent period
    summaries=[]
    for city,d in annual.groupby('city'):
        recent=d[d.year.between(2021,2025)]
        summaries.append({'city':city,'mean_bias':d.bias.mean(),'min_bias':d.bias.min(),'max_bias':d.bias.max(),'recent_bias_2021_2025':recent.bias.mean()})
    pd.DataFrame(summaries).to_csv(tables/'annual_bias_city_summary.csv',index=False)

    # --- figures
    p=score.sort_values('bias_era5_minus_station')
    plt.figure(figsize=(8.7,5.3)); plt.barh(p.city,p.bias_era5_minus_station,color=COLORS['purple']); plt.axvline(0,color='#444',lw=1)
    plt.xlabel('Bias médio (ERA5-Land - estação), °C'); plt.title('ERA5-Land subestima a Tmax diária em todas as capitais',color=COLORS['green']); plt.grid(axis='x'); plt.tight_layout(); plt.savefig(figs/'01_bias_por_capital.png',dpi=220); plt.close()
    p=score.sort_values('rmse')
    plt.figure(figsize=(8.7,5.3)); plt.barh(p.city,p.rmse,color=COLORS['orange']); plt.xlabel('RMSE diário (°C)'); plt.title('Erro diário de Tmax por capital',color=COLORS['green']); plt.grid(axis='x'); plt.tight_layout(); plt.savefig(figs/'02_rmse_por_capital.png',dpi=220); plt.close()
    p=score.sort_values('pearson_r')
    plt.figure(figsize=(8.7,5.3)); plt.barh(p.city,p.pearson_r,color=COLORS['green']); plt.xlim(0,1); plt.xlabel('Pearson r'); plt.title('Variabilidade diária: estação x ERA5-Land',color=COLORS['green']); plt.grid(axis='x'); plt.tight_layout(); plt.savefig(figs/'03_pearson_por_capital.png',dpi=220); plt.close()

    piv=monthly.pivot(index='city_id',columns='month',values='bias').reindex(CITY_MAP.keys())
    plt.figure(figsize=(11.5,5.5)); im=plt.imshow(piv.values,aspect='auto',cmap='YlGnBu_r',vmin=-3.6,vmax=.2)
    plt.yticks(range(len(piv)),[CITY_LABELS[c] for c in piv.index]); plt.xticks(range(12),MONTHS_PT); plt.title('Bias mensal de Tmax: ERA5-Land - estação (°C)',color=COLORS['green'])
    cb=plt.colorbar(im); cb.set_label('°C')
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            if np.isfinite(piv.iloc[i,j]): plt.text(j,i,f'{piv.iloc[i,j]:+.1f}',ha='center',va='center',fontsize=7.5)
    plt.tight_layout(); plt.savefig(figs/'04_bias_mensal_heatmap.png',dpi=220); plt.close()

    plt.figure(figsize=(10,5.6))
    for city,d in annual.groupby('city'):
        lw=2 if city in ['Manaus','Salvador','Belém'] else 1.2; plt.plot(d.year,d.bias,lw=lw,label=city)
    plt.axhline(0,color='#444',lw=1); plt.xlabel('Ano'); plt.ylabel('Bias anual (°C)'); plt.title('Offset anual de Tmax: ERA5-Land - estação',color=COLORS['green']); plt.grid(); plt.legend(ncol=3,fontsize=7,frameon=False)
    plt.tight_layout(); plt.savefig(figs/'05_bias_anual_series.png',dpi=220); plt.close()

    # quantile bias
    plt.figure(figsize=(9.5,5.5))
    for city,d in qdf.groupby('city'): plt.plot(d['quantile']*100,d['era5_minus_station'],marker='o',label=city)
    plt.axhline(0,color='#444',lw=1); plt.xticks([50,90,95,99]); plt.xlabel('Percentil da Tmax diária'); plt.ylabel('ERA5 - estação (°C)'); plt.title('Diferença nos quantis da Tmax',color=COLORS['green']); plt.grid(); plt.legend(ncol=3,fontsize=7,frameon=False)
    plt.tight_layout(); plt.savefig(figs/'06_bias_por_percentil.png',dpi=220); plt.close()

    # hot vs other
    h=hotdf.sort_values('bias_on_station_hot_days'); x=np.arange(len(h)); w=.37
    plt.figure(figsize=(10.5,5.8)); plt.bar(x-w/2,h.bias_on_station_hot_days,w,label='Dias > TX90 na estação',color=COLORS['purple']); plt.bar(x+w/2,h.bias_on_other_days,w,label='Demais dias',color=COLORS['teal']); plt.axhline(0,color='#444',lw=1)
    plt.xticks(x,h.city,rotation=35,ha='right'); plt.ylabel('ERA5 - estação (°C)'); plt.title('O viés fica mais negativo nos dias quentes',color=COLORS['green']); plt.legend(frameon=False); plt.grid(axis='y'); plt.tight_layout(); plt.savefig(figs/'07_bias_quente_vs_outros.png',dpi=220); plt.close()

    txmean=txdf.groupby('city',as_index=False).tx90_bias.mean().sort_values('tx90_bias')
    plt.figure(figsize=(8.7,5.3)); plt.barh(txmean.city,txmean.tx90_bias,color=COLORS['teal']); plt.axvline(0,color='#444',lw=1); plt.xlabel('ERA5 TX90 - estação TX90 (°C)'); plt.title('O limiar TX90 do ERA5-Land também é mais baixo',color=COLORS['green']); plt.grid(axis='x'); plt.tight_layout(); plt.savefig(figs/'08_bias_tx90_por_capital.png',dpi=220); plt.close()

    merged=hotdf[['city','f1_hot_day']].merge(eventdf[['city','f1_event_day']],on='city').sort_values('f1_event_day')
    x=np.arange(len(merged)); w=.37
    plt.figure(figsize=(10.5,5.8)); plt.bar(x-w/2,merged.f1_hot_day,w,label='Dia > TX90',color=COLORS['teal']); plt.bar(x+w/2,merged.f1_event_day,w,label='Dia em sequência >=6',color=COLORS['purple']); plt.xticks(x,merged.city,rotation=35,ha='right'); plt.ylim(0,1); plt.ylabel('F1-score'); plt.title('Da temperatura extrema à persistência WSDI',color=COLORS['green']); plt.legend(frameon=False); plt.grid(axis='y'); plt.tight_layout(); plt.savefig(figs/'09_f1_hot_wsdi.png',dpi=220); plt.close()

    # lag
    plt.figure(figsize=(9.5,5.5))
    for city,d in lagdf.groupby('city'): plt.plot(d.era5_shift_days,d.pearson_r,marker='o',label=city)
    plt.xticks([-2,-1,0,1,2]); plt.xlabel('Deslocamento aplicado ao ERA5 (dias)'); plt.ylabel('Pearson r'); plt.title('Diagnóstico de alinhamento temporal',color=COLORS['green']); plt.legend(ncol=3,fontsize=7,frameon=False); plt.grid(); plt.tight_layout(); plt.savefig(figs/'10_lag_diagnostic.png',dpi=220); plt.close()

    # city scatter panels
    fig,axes=plt.subplots(3,3,figsize=(12,11))
    for ax,cid in zip(axes.ravel(),CITY_MAP):
        d=data[data.city_id==cid].dropna(subset=['station_tmax_c','era5_tmax_c']); s=paired_stats(d); lo=min(d.station_tmax_c.min(),d.era5_tmax_c.min()); hi=max(d.station_tmax_c.max(),d.era5_tmax_c.max())
        ax.hexbin(d.station_tmax_c,d.era5_tmax_c,gridsize=35,mincnt=1,cmap='viridis'); ax.plot([lo,hi],[lo,hi],'--',color='#333',lw=1); ax.set_title(f"{CITY_LABELS[cid]} | r={s['pearson_r']:.2f} | bias={s['bias_era5_minus_station']:+.2f}",fontsize=9); ax.grid(alpha=.15)
    fig.supxlabel('Estação Tmax (°C)'); fig.supylabel('ERA5-Land Tmax (°C)'); fig.suptitle('Temperatura máxima diária: estação x ERA5-Land',color=COLORS['green'],fontweight='bold')
    fig.tight_layout(rect=[.02,.02,1,.96]); fig.savefig(figs/'11_scatter_9_capitais.png',dpi=220); plt.close(fig)

    # summary
    b=score.loc[score.rmse.idxmin()]; w=score.loc[score.rmse.idxmax()]; hs=hotdf.loc[hotdf.f1_hot_day.idxmax()]; hw=eventdf.loc[eventdf.f1_event_day.idxmax()]
    text=f"""TMAX VALIDATION SUMMARY\n\nDaily Pearson r range: {score.pearson_r.min():.3f} to {score.pearson_r.max():.3f}\nMean bias range: {score.bias_era5_minus_station.max():+.2f} to {score.bias_era5_minus_station.min():+.2f} °C\nRMSE range: {score.rmse.min():.2f} to {score.rmse.max():.2f} °C\nLowest RMSE: {b.city} ({b.rmse:.2f} °C)\nHighest RMSE: {w.city} ({w.rmse:.2f} °C)\nBest F1 hot day: {hs.city} ({hs.f1_hot_day:.3f})\nBest F1 WSDI-event day: {hw.city} ({hw.f1_event_day:.3f})\n"""
    (out/'summary.txt').write_text(text,encoding='utf-8'); print(text)

if __name__=='__main__': main()
