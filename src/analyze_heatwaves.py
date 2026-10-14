#!/usr/bin/env python3
"""Reproduce the station-event validation of MapBiomas Heatwaves V1 vs V2."""
from pathlib import Path
import argparse
import json
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

from style_mapbiomas import COLORS, MONTHS_PT, apply_style, ensure_dirs

MISSING = -9999
METRICS = ['heatwave_days','event_count','max_event_duration','mean_event_duration']
VERSIONS = ['v1','v2']


def stats_xy(o, p):
    o = pd.Series(o, dtype=float)
    p = pd.Series(p, dtype=float)
    ok = o.notna() & p.notna() & (o != MISSING) & (p != MISSING)
    o, p = o[ok], p[ok]
    n = len(o)
    if n > 1 and o.nunique() > 1 and p.nunique() > 1:
        r = pearsonr(o, p).statistic
        rho = spearmanr(o, p).statistic
    else:
        r = rho = np.nan
    err = p - o
    bias = err.mean() if n else np.nan
    mae = np.abs(err).mean() if n else np.nan
    rmse = np.sqrt(np.mean(err**2)) if n else np.nan
    sst = np.sum((o-o.mean())**2) if n else 0
    r2 = 1 - np.sum(err**2)/sst if sst > 0 else np.nan
    if n > 1:
        cov = np.mean((o-o.mean())*(p-p.mean()))
        den = o.var(ddof=0)+p.var(ddof=0)+(o.mean()-p.mean())**2
        ccc = 2*cov/den if den > 0 else np.nan
    else:
        ccc = np.nan
    return dict(n=n, pearson_r=r, spearman_rho=rho, bias=bias, mae=mae, rmse=rmse, r2=r2, ccc=ccc)


def detection_metrics(df, version):
    obs = df['station_event_count'] > 0
    pred = df[f'{version}_event_count'] > 0
    tp = int((obs & pred).sum())
    tn = int((~obs & ~pred).sum())
    fp = int((~obs & pred).sum())
    fn = int((obs & ~pred).sum())
    precision = tp/(tp+fp) if tp+fp else np.nan
    recall = tp/(tp+fn) if tp+fn else np.nan
    f1 = 2*precision*recall/(precision+recall) if precision+recall else np.nan
    specificity = tn/(tn+fp) if tn+fp else np.nan
    return dict(n=len(df), tp=tp, tn=tn, fp=fp, fn=fn,
                precision=precision, recall=recall, f1=f1,
                accuracy=(tp+tn)/len(df),
                balanced_accuracy=(recall+specificity)/2,
                csi=tp/(tp+fp+fn) if tp+fp+fn else np.nan)


def pooled_stats(df, metric, version, centered=False):
    oc, pc = f'station_{metric}', f'{version}_{metric}'
    d = df[['city', oc, pc]].copy()
    d = d[(d[oc] != MISSING) & (d[pc] != MISSING)].dropna()
    if centered:
        d[oc] = d[oc] - d.groupby('city')[oc].transform('mean')
        d[pc] = d[pc] - d.groupby('city')[pc].transform('mean')
    return stats_xy(d[oc], d[pc])


def safe_name(s):
    return re.sub(r'[^A-Za-z0-9_-]+','_',s.lower()).strip('_')


def make_scatter_composite(annual, out):
    fig, axes = plt.subplots(1,2,figsize=(11,5.1), sharex=True, sharey=True)
    for ax, version in zip(axes, ['v1','v2']):
        x = annual['station_heatwave_days'].astype(float)
        y = annual[f'{version}_heatwave_days'].astype(float)
        ok = (x != MISSING) & (y != MISSING)
        x,y=x[ok],y[ok]
        s=stats_xy(x,y)
        lo=min(x.min(),y.min()); hi=max(x.max(),y.max())
        ax.scatter(x,y,s=18,alpha=.55,color=COLORS[version],edgecolors='none')
        ax.plot([lo,hi],[lo,hi],'--',color='#333333',lw=1.1,label='1:1')
        if len(x)>1:
            coef=np.polyfit(x,y,1); xx=np.linspace(lo,hi,100)
            ax.plot(xx,coef[0]*xx+coef[1],color=COLORS['orange'],lw=1.5,label='regressão')
        ax.set_title(version.upper(), color=COLORS[version])
        ax.set_xlabel('Estação (dias/ano)')
        ax.grid(True)
        ax.text(.04,.96,f"r={s['pearson_r']:.2f}\nCCC={s['ccc']:.2f}\nRMSE={s['rmse']:.1f}\nBias={s['bias']:+.1f}\nn={s['n']}",
                transform=ax.transAxes,ha='left',va='top',fontsize=9,
                bbox=dict(boxstyle='round,pad=.35',facecolor='white',edgecolor='#DADFDA',alpha=.9))
    axes[0].set_ylabel('MapBiomas (dias/ano)')
    axes[1].legend(frameon=False,loc='lower right')
    fig.suptitle('Dias anuais com onda de calor: comparação direta com estações',color=COLORS['green'],fontweight='bold')
    fig.tight_layout(rect=[0,0,1,.94])
    fig.savefig(out,dpi=220,bbox_inches='tight'); plt.close(fig)


def make_city_pearson_rmse(enhanced, out):
    d=enhanced[(enhanced.period=='annual')&(enhanced.metric=='heatwave_days')]
    pr=d.pivot(index='city',columns='version',values='pearson_r')
    rm=d.pivot(index='city',columns='version',values='rmse')
    order=list(pr.index)
    x=np.arange(len(order)); w=.36
    fig,axes=plt.subplots(1,2,figsize=(12,5.5))
    axes[0].bar(x-w/2,pr['v1'],w,label='V1',color=COLORS['v1'])
    axes[0].bar(x+w/2,pr['v2'],w,label='V2',color=COLORS['v2'])
    axes[0].set_xticks(x); axes[0].set_xticklabels(order,rotation=40,ha='right')
    axes[0].set_ylim(-.2,1); axes[0].set_ylabel('Pearson r'); axes[0].set_title('Correlação temporal anual')
    axes[0].grid(axis='y'); axes[0].legend(frameon=False)
    axes[1].bar(x-w/2,rm['v1'],w,label='V1',color=COLORS['v1'])
    axes[1].bar(x+w/2,rm['v2'],w,label='V2',color=COLORS['v2'])
    axes[1].set_xticks(x); axes[1].set_xticklabels(order,rotation=40,ha='right')
    axes[1].set_ylabel('RMSE (dias/ano)'); axes[1].set_title('Erro de magnitude anual')
    axes[1].grid(axis='y')
    fig.suptitle('Desempenho por capital: dias anuais com onda de calor',color=COLORS['green'],fontweight='bold')
    fig.tight_layout(rect=[0,0,1,.94]); fig.savefig(out,dpi=220,bbox_inches='tight'); plt.close(fig)


def make_detection_plot(det, out):
    fig,axes=plt.subplots(1,2,figsize=(11.5,5.2))
    for ax,period,title in zip(axes,['annual','monthly'],['Anual','Mensal']):
        d=det[(det.period==period)&(det.city!='ALL_CITIES')]
        p=d.pivot(index='city',columns='version',values='f1')
        x=np.arange(len(p)); w=.36
        ax.bar(x-w/2,p['v1'],w,label='V1',color=COLORS['v1'])
        ax.bar(x+w/2,p['v2'],w,label='V2',color=COLORS['v2'])
        ax.set_xticks(x); ax.set_xticklabels(p.index,rotation=40,ha='right')
        ax.set_ylim(0,1); ax.set_ylabel('F1-score'); ax.set_title(title); ax.grid(axis='y')
    axes[0].legend(frameon=False)
    fig.suptitle('Habilidade de detecção de ocorrência de eventos',color=COLORS['green'],fontweight='bold')
    fig.tight_layout(rect=[0,0,1,.93]); fig.savefig(out,dpi=220,bbox_inches='tight'); plt.close(fig)


def make_raw_annual(annual, out):
    cities=annual['city'].drop_duplicates().tolist()
    fig,axes=plt.subplots(3,3,figsize=(13,9),sharex=True)
    for ax,city in zip(axes.ravel(),cities):
        d=annual[annual.city==city].sort_values('year')
        x=np.arange(len(d)); w=.34
        ax.bar(x-w/2,d['v1_heatwave_days'],w,color=COLORS['v1'],alpha=.75,label='V1')
        ax.bar(x+w/2,d['v2_heatwave_days'],w,color=COLORS['v2'],alpha=.75,label='V2')
        ax.plot(x,d['station_heatwave_days'],color=COLORS['station'],lw=1.3,label='Estação')
        ax.set_title(city,loc='left',fontsize=10)
        ticks=[i for i,y in enumerate(d.year) if y in [1985,1995,2005,2015,2025]]
        ax.set_xticks(ticks); ax.set_xticklabels([str(d.iloc[i].year) for i in ticks],rotation=45,ha='right',fontsize=7)
        ax.grid(axis='y',alpha=.35)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,ncol=3,loc='upper center',frameon=False)
    fig.suptitle('Dias anuais com onda de calor por capital (1985-2025)',color=COLORS['green'],fontweight='bold',y=.99)
    fig.tight_layout(rect=[0,.01,1,.95]); fig.savefig(out,dpi=220,bbox_inches='tight'); plt.close(fig)


def make_monthly_seasonality(monthly, out):
    cities=monthly['city'].drop_duplicates().tolist()
    fig,axes=plt.subplots(3,3,figsize=(13,9),sharex=True)
    for ax,city in zip(axes.ravel(),cities):
        d=monthly[monthly.city==city].groupby('month')[['station_heatwave_days','v1_heatwave_days','v2_heatwave_days']].mean().reindex(range(1,13))
        ax.plot(d.index,d.station_heatwave_days,color=COLORS['station'],lw=1.4,label='Estação')
        ax.plot(d.index,d.v1_heatwave_days,color=COLORS['v1'],lw=1.2,label='V1')
        ax.plot(d.index,d.v2_heatwave_days,color=COLORS['v2'],lw=1.4,label='V2')
        ax.fill_between(d.index,0,d.v2_heatwave_days,color=COLORS['v2'],alpha=.08)
        ax.set_title(city,loc='left',fontsize=10); ax.grid(alpha=.3)
        ax.set_xticks([1,3,5,7,9,11]); ax.set_xticklabels([MONTHS_PT[i-1] for i in [1,3,5,7,9,11]],fontsize=7)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,ncol=3,loc='upper center',frameon=False)
    fig.suptitle('Sazonalidade média dos dias com onda de calor (1985-2025)',color=COLORS['green'],fontweight='bold')
    fig.tight_layout(rect=[0,.01,1,.95]); fig.savefig(out,dpi=220,bbox_inches='tight'); plt.close(fig)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--annual',required=True)
    ap.add_argument('--monthly',required=True)
    ap.add_argument('--centroids',required=False)
    ap.add_argument('--outdir',required=True)
    args=ap.parse_args()
    apply_style()
    out=Path(args.outdir); figs=out/'figures'; tables=out/'tables'; ensure_dirs(figs,tables)
    annual=pd.read_csv(args.annual); monthly=pd.read_csv(args.monthly)

    enhanced=[]
    for period,df in [('annual',annual),('monthly',monthly)]:
        for city in df.city.drop_duplicates():
            dc=df[df.city==city]
            for metric in METRICS:
                for version in VERSIONS:
                    enhanced.append({'period':period,'city':city,'metric':metric,'version':version,
                                     **stats_xy(dc[f'station_{metric}'],dc[f'{version}_{metric}'])})
    enhanced=pd.DataFrame(enhanced); enhanced.to_csv(tables/'enhanced_metrics_by_city.csv',index=False)

    pooled=[]
    for period,df in [('annual',annual),('monthly',monthly)]:
        for metric in METRICS:
            for version in VERSIONS:
                for centered in [False,True]:
                    pooled.append({'period':period,'metric':metric,'version':version,'centered_by_city':centered,
                                   **pooled_stats(df,metric,version,centered)})
    pooled=pd.DataFrame(pooled); pooled.to_csv(tables/'pooled_metrics.csv',index=False)

    det=[]
    for period,df in [('annual',annual),('monthly',monthly)]:
        for city in list(df.city.drop_duplicates())+['ALL_CITIES']:
            dd=df if city=='ALL_CITIES' else df[df.city==city]
            for version in VERSIONS:
                det.append({'period':period,'city':city,'version':version,**detection_metrics(dd,version)})
    det=pd.DataFrame(det); det.to_csv(tables/'event_detection_metrics.csv',index=False)

    common=[]
    for period,df in [('annual',annual),('monthly',monthly)]:
        for metric in ['max_event_duration','mean_event_duration']:
            mask=(df[f'station_{metric}']!=MISSING)&(df[f'v1_{metric}']!=MISSING)&(df[f'v2_{metric}']!=MISSING)
            dd=df[mask]
            for version in VERSIONS:
                s=stats_xy(dd[f'station_{metric}'],dd[f'{version}_{metric}'])
                common.append({'period':period,'metric':metric,'version':version,'n_common':len(dd),'cities_in_common':dd.city.nunique(),**s})
    pd.DataFrame(common).to_csv(tables/'duration_common_support_metrics.csv',index=False)

    # concise scorecards
    annual_score=pooled[(pooled.period=='annual')&(pooled.centered_by_city==False)&(pooled.metric.isin(['heatwave_days','event_count']))]
    annual_score.to_csv(tables/'annual_pooled_scorecard.csv',index=False)
    monthly_score=pooled[(pooled.period=='monthly')&(pooled.centered_by_city==False)&(pooled.metric=='heatwave_days')]
    monthly_score.to_csv(tables/'monthly_heatwave_days_scorecard.csv',index=False)

    make_scatter_composite(annual,figs/'01_scatter_v1_v2_heatwave_days.png')
    make_raw_annual(annual,figs/'02_raw_annual_days_by_city.png')
    make_city_pearson_rmse(enhanced,figs/'03_by_city_pearson_rmse.png')
    make_detection_plot(det,figs/'04_f1_detection_annual_monthly.png')
    make_monthly_seasonality(monthly,figs/'05_monthly_seasonality.png')

    # summary text
    def row(period,metric,version,centered=False):
        return pooled[(pooled.period==period)&(pooled.metric==metric)&(pooled.version==version)&(pooled.centered_by_city==centered)].iloc[0]
    a1=row('annual','heatwave_days','v1'); a2=row('annual','heatwave_days','v2')
    m1=row('monthly','heatwave_days','v1'); m2=row('monthly','heatwave_days','v2')
    da=det[(det.period=='annual')&(det.city=='ALL_CITIES')].set_index('version')
    dm=det[(det.period=='monthly')&(det.city=='ALL_CITIES')].set_index('version')
    txt=f"""HEATWAVE PRODUCT VALIDATION SUMMARY\n\nAnnual heatwave_days:\nV1 r={a1.pearson_r:.3f}, RMSE={a1.rmse:.2f}, bias={a1.bias:+.2f}\nV2 r={a2.pearson_r:.3f}, RMSE={a2.rmse:.2f}, bias={a2.bias:+.2f}\nAnnual occurrence F1: V1={da.loc['v1','f1']:.3f}, V2={da.loc['v2','f1']:.3f}\nAnnual occurrence recall: V1={da.loc['v1','recall']:.3f}, V2={da.loc['v2','recall']:.3f}\n\nMonthly heatwave_days:\nV1 r={m1.pearson_r:.3f}, RMSE={m1.rmse:.2f}, bias={m1.bias:+.2f}\nV2 r={m2.pearson_r:.3f}, RMSE={m2.rmse:.2f}, bias={m2.bias:+.2f}\nMonthly occurrence F1: V1={dm.loc['v1','f1']:.3f}, V2={dm.loc['v2','f1']:.3f}\nMonthly occurrence recall: V1={dm.loc['v1','recall']:.3f}, V2={dm.loc['v2','recall']:.3f}\n"""
    (out/'summary.txt').write_text(txt,encoding='utf-8')
    print(txt)

if __name__=='__main__':
    main()
