#!/usr/bin/env python3
from pathlib import Path
import argparse
import math
import pandas as pd


def close(a,b,tol):
    return abs(float(a)-float(b)) <= tol


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--heatwave-out',required=True)
    ap.add_argument('--tmax-out',required=True)
    args=ap.parse_args()
    hw=Path(args.heatwave_out); tx=Path(args.tmax_out)
    pooled=pd.read_csv(hw/'tables/pooled_metrics.csv')
    det=pd.read_csv(hw/'tables/event_detection_metrics.csv')
    score=pd.read_csv(tx/'tables/daily_scorecard_by_city.csv')
    hot=pd.read_csv(tx/'tables/hot_day_skill.csv')
    wsdi=pd.read_csv(tx/'tables/wsdi_event_day_skill.csv')

    checks=[]
    def grab(period,metric,version,field):
        r=pooled[(pooled.period==period)&(pooled.metric==metric)&(pooled.version==version)&(pooled.centered_by_city==False)].iloc[0]
        return r[field]
    checks += [
        ('annual V1 r heatwave_days', grab('annual','heatwave_days','v1','pearson_r'), 0.167997, 1e-5),
        ('annual V2 r heatwave_days', grab('annual','heatwave_days','v2','pearson_r'), 0.712518, 1e-5),
        ('annual V1 RMSE heatwave_days', grab('annual','heatwave_days','v1','rmse'), 16.203148, 1e-5),
        ('annual V2 RMSE heatwave_days', grab('annual','heatwave_days','v2','rmse'), 12.233279, 1e-5),
        ('monthly V2 r heatwave_days', grab('monthly','heatwave_days','v2','pearson_r'), 0.593038, 1e-5),
    ]
    d=det[(det.period=='annual')&(det.city=='ALL_CITIES')].set_index('version')
    checks += [
        ('annual F1 V1', d.loc['v1','f1'], 0.449, 0.002),
        ('annual F1 V2', d.loc['v2','f1'], 0.686, 0.002),
    ]
    s=score.set_index('city')
    checks += [
        ('Brasilia daily RMSE', s.loc['Brasília','rmse'], 1.328115, 1e-5),
        ('Goiania daily bias', s.loc['Goiânia','bias_era5_minus_station'], -2.918726, 1e-5),
        ('Porto Alegre daily r', s.loc['Porto Alegre','pearson_r'], 0.958833, 1e-5),
    ]
    h=hot.set_index('city'); w=wsdi.set_index('city')
    checks += [
        ('Porto Alegre F1 hot', h.loc['Porto Alegre','f1_hot_day'], 0.756172, 1e-5),
        ('Manaus WSDI recall', w.loc['Manaus','recall_event_day'], 0.817308, 1e-5),
        ('Salvador WSDI F1', w.loc['Salvador','f1_event_day'], 0.176211, 1e-5),
    ]

    failed=[]
    for name,got,exp,tol in checks:
        ok=close(got,exp,tol)
        print(f"{'OK' if ok else 'FAIL'} | {name}: got={got:.6f} expected={exp:.6f} tol={tol}")
        if not ok: failed.append(name)
    if failed:
        raise SystemExit('Reproducibility checks failed: '+', '.join(failed))
    print('\nAll key-result reproducibility checks passed.')

if __name__=='__main__': main()
