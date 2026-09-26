"""Retrospective grouping of frozen one-hour forecasts and saved trades."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
STUDY=HERE.parents[2]

def main():
    forecasts=[];trades=[];hashes={}
    for seed in (1729,2718,3141):
        root=STUDY/'results'/f'base-{seed}'
        frames={}
        for name,file in [('features','features.csv.gz'),('forecasts','predictions-and-outcomes.csv.gz'),('trades','trade-ledger.csv')]:
            path=root/file;hashes[str(path.relative_to(STUDY))]=hashlib.sha256(path.read_bytes()).hexdigest()
            frame=pd.read_csv(path);frame['decision_time']=pd.to_datetime(frame.decision_time,utc=True)
            frames[name]=frame
        f=frames['forecasts'].query('horizon_minutes == 60').copy()
        f=f.merge(frames['features'][['decision_time','mom_z_30']],on='decision_time',validate='one_to_one')
        f['observed_direction']=np.where(abs(f.mom_z_30)>=.75,np.sign(f.mom_z_30),0).astype(int)
        f['forecast_direction']=np.sign(f.indicator).astype(int)
        f['alignment']=np.select([f.forecast_direction.eq(0),f.observed_direction.eq(0),f.forecast_direction.eq(f.observed_direction)],['zero_forecast','balanced_origin','continuation'],default='opposing')
        p=f[['p_down','p_neutral','p_up']].to_numpy();y=f.class_id.to_numpy(int)
        f['log_loss']=-np.log(np.maximum(p[np.arange(len(y)),y],1e-12))
        f['signed_endpoint_ticks']=f.forecast_direction*f.return_ticks
        f['direction_hit']=f.signed_endpoint_ticks.gt(0)
        f['above_existing_indicator_threshold']=abs(f.indicator)>=.2
        f['seed']=seed;forecasts.append(f)
        t=frames['trades'].query("horizon_minutes == 60 and strategy == 'model'").copy()
        t=t.merge(f[['decision_time','mom_z_30','observed_direction']],on='decision_time',validate='one_to_one')
        t['alignment']=np.select([t.observed_direction.eq(0),t.direction.eq(t.observed_direction)],['balanced_origin','continuation'],default='opposing')
        t['seed']=seed;trades.append(t)
    f=pd.concat(forecasts,ignore_index=True);t=pd.concat(trades,ignore_index=True)
    f.to_csv(HERE/'alignment-forecasts.csv.gz',index=False);t.to_csv(HERE/'alignment-trades.csv',index=False)
    summary=f.groupby(['seed','alignment']).agg(forecasts=('decision_time','size'),
        above_indicator_threshold=('above_existing_indicator_threshold','sum'),log_loss=('log_loss','mean'),
        signed_endpoint_ticks=('signed_endpoint_ticks','mean'),direction_hit=('direction_hit','mean')).reset_index()
    summary.to_csv(HERE/'alignment-forecast-summary.csv',index=False)
    summary=t.groupby(['seed','alignment']).agg(trades=('decision_time','size'),
        net_benchmark_cad=('net_benchmark_cad','sum'),stress_net_cad=('stress_net_cad','sum')).reset_index()
    summary.to_csv(HERE/'alignment-trade-summary.csv',index=False)
    assert all(hashlib.sha256((STUDY/name).read_bytes()).hexdigest()==digest for name,digest in hashes.items())
    (HERE/'alignment-verification.json').write_text(json.dumps({'source_hashes':hashes,'sources_unchanged':True,
        'classification':'Existing absolute 30-minute momentum threshold 0.75; existing forecast sign; no new trades or filter',
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
    print(summary.to_string(index=False))

if __name__=='__main__':main()
