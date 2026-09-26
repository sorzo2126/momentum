"""Verify causality, separation, data structure and cash accounting of a saved run."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from .structured_simulation import OUT,dump_json
from momentum import prepare_panel,build_features
from momentum.deployment import load_deployment
from momentum.scenarios import predict_scenarios


def run_checks():
    checks=[]
    def checked(name,detail):checks.append(dict(check=name,status='PASS',detail=detail));print('PASS',name,flush=True)
    base=OUT/'results/base-1729'
    quotes=pd.read_csv(base/'inputs/quotes.csv.gz',float_precision='round_trip');trades=pd.read_csv(base/'inputs/trades.csv.gz',float_precision='round_trip');rates=pd.read_csv(base/'inputs/rates.csv.gz',float_precision='round_trip');sessions=pd.read_csv(base/'inputs/sessions.csv.gz')
    for frame in (quotes,trades,rates):
        for c in ('event_time','available_at'):frame[c]=pd.to_datetime(frame[c],utc=True,format='mixed')
        assert (frame.available_at>=frame.event_time).all()
    for c in ('open_time','close_time'):sessions[c]=pd.to_datetime(sessions[c],utc=True)
    cgb=quotes[quotes.instrument=='CGB']
    assert np.allclose(cgb.bid/.01,np.round(cgb.bid/.01)) and np.allclose(cgb.ask/.01,np.round(cgb.ask/.01))
    assert (quotes.ask>=quotes.bid).all() and (quotes.bid>0).all() and (quotes[['bid_size','ask_size']]>0).all().all()
    checked('quote_units_and_clocks','Positive uncrossed prices; CGB bid/ask on 0.01 lattice; positive depth; event <= arrival.')
    curve=pd.read_csv(base/'inputs/curve_truth.csv.gz')
    assert np.allclose(curve.fwd1y1y_bp,(curve.discount1/curve.discount2-1)*1e4)
    assert np.allclose(curve.fwd2y1y_bp,(curve.discount2/curve.discount3-1)*1e4)
    assert rates[rates.instrument.str.startswith('SWAP')].event_time.dt.date.nunique()==4
    assert rates[rates.instrument.str.startswith('SWAP')].event_time.min()>sessions.close_time.iloc[31]
    checked('curve_identities_and_short_history','Annual effective forwards satisfy discount-ratio identities; swaps exist only in last four TEST sessions.')
    from .bond_ecosystem import TENORS,bond_values,carry_future,zero_curve,schedule
    curves=pd.read_csv(base/'inputs/curves.csv.gz');cash=pd.read_csv(base/'inputs/cash_bonds.csv.gz');fv=pd.read_csv(base/'inputs/futures_valuation.csv.gz')
    for country in ('CAD','US','OIS'):
        ds=curves[[f'{country}_discount_{t:g}y' for t in TENORS]].to_numpy()
        assert (ds>0).all() and (np.diff(ds,axis=1)<0).all()
    assert np.allclose(cash.dirty,cash.clean+cash.accrued)
    assert (cash.dv01_per_100k>0).all()
    for name in ('CAD2','CAD5','CAD10'):
        b=cash[cash.instrument==name]
        assert np.max(abs(b[['krd2_per_100k','krd5_per_100k','krd10_per_100k']].sum(1)-b.dv01_per_100k))<1e-4
    for name in ('CGB','CGF','CGZ','US10'):
        f=fv[fv.instrument==name]
        cols=[c for c in curves if c.startswith(name+'_') and c.endswith('_delivery_cost')]
        assert np.allclose(f.fair.to_numpy(),curves[cols].min(axis=1).to_numpy())
    # Reprice an exact cash-flow bond and its carry identity independently.
    pars=curves.iloc[0];params=tuple(np.array([pars[c]]) for c in ('gov_level','gov_slope','gov_curvature'))
    dirty,clean,accrued,pv,tau,cf,remaining=bond_values(*params,np.array([0.]),8.25,.03)
    cash0=cash[cash.instrument=='CGB_A'].iloc[0]
    assert abs(dirty[0]-cash0.dirty)<1e-10
    y=cash0.yield_bp/1e4
    assert abs(np.sum(cf*(1+y/2)**(-2*tau[0]))-dirty[0])<1e-9
    future,conversion,aid,income=carry_future(dirty,np.array([pars.repo_rate-.0003]),np.array([0.]),8.25,.03,120/365)
    assert np.allclose(future*conversion+aid+income,dirty*np.exp((pars.repo_rate-.0003)*120/365))
    checked('cashflow_curve_and_futures_identities','Positive decreasing discount factors; dirty = clean + accrued; positive DV01; key-rate sum within C$0.0001 per 100k; YTM inversion; coupon-aware repo carry and cheapest delivery selection.')
    model=load_deployment(base/'frozen-model');cutoff=sessions.open_time.iloc[32]+pd.Timedelta(minutes=190)
    assert not any('latent' in c or 'target' in c or 'pressure_cad' in c for c in model['feature_columns'])
    for h,e in model['horizons'].items():
        assert max(pd.to_datetime(e['bank']['train_times'],utc=True))<sessions.open_time.iloc[24]
        assert np.allclose(e['transition'].sum(1),1) and np.isclose(e['mixture_weights'].sum(),1)
        assert np.allclose(e['bank']['paths'][:,0],0)
        assert (e['bank']['mae_long']>=np.maximum(-e['bank']['endpoint'],0)-1e-9).all()
        assert (e['bank']['mae_short']>=np.maximum(e['bank']['endpoint'],0)-1e-9).all()
    checked('model_and_path_integrity','Frozen deployment hashes verified; TRAIN-only scenario dates; stochastic matrices; coherent scenario excursions; no hidden truth columns selected.')
    for folder in (OUT/'results').iterdir():
        if not folder.is_dir():continue
        p=pd.read_csv(folder/'predictions-and-outcomes.csv.gz')
        assert np.allclose(p[['p_down','p_neutral','p_up']].sum(1),1)
        assert (p[['p_down','p_neutral','p_up']]>=0).all().all()
        assert np.allclose(p.indicator,p.p_up-p.p_down)
        assert (p.endpoint_q90_ticks>=p.endpoint_q10_ticks).all()
        ledger=pd.read_csv(folder/'trade-ledger.csv');mark=pd.read_csv(folder/'marked-pnl.csv.gz')
        for col in ('decision_time','entry_time','exit_time'):ledger[col]=pd.to_datetime(ledger[col],utc=True)
        assert ((ledger.entry_time-ledger.decision_time)==pd.Timedelta(minutes=1)).all()
        assert np.allclose(ledger.net_benchmark_cad,ledger.midpoint_change_cad-ledger.spread_crossing_cad-ledger.additional_slippage_cad-ledger.fees_cad)
        assert np.allclose(ledger.stress_net_cad,ledger.net_benchmark_cad-30)
        for (h,s),g in ledger.groupby(['horizon_minutes','strategy']):
            assert (g.entry_time.iloc[1:].to_numpy()>g.exit_time.iloc[:-1].to_numpy()).all()
            z=mark[(mark.horizon_minutes==h)&(mark.strategy==s)]
            assert abs(z.pnl_cad.iloc[-1]-g.net_benchmark_cad.sum())<1e-7
        inp=folder/'inputs'
        if inp.exists() and folder.name not in ('base-1729','null-1729','base-2718','null-2718','base-3141','null-3141'):
            sq=pd.read_csv(inp/'quotes.csv.gz',float_precision='round_trip')
            for col in ('event_time','available_at'):sq[col]=pd.to_datetime(sq[col],utc=True,format='mixed')
            old=quotes[quotes.available_at<=sessions.close_time.iloc[31]].reset_index(drop=True)
            new=sq[sq.available_at<=sessions.close_time.iloc[31]].reset_index(drop=True)
            assert_frame_equal(old,new)
    summary=pd.read_csv(OUT/'execution-summary.csv')
    incomplete=summary.unpriced_trades>0
    assert incomplete.any() and summary.loc[incomplete,['net_cad','stress_net_cad','max_drawdown_cad']].isna().all().all()
    checked('all_forecast_and_cash_ledgers','Every run: probabilities, indicator identity, quantile order, one-minute delay, no overlap per book, spread counted once, priced-subset mark reconciliation, frozen stress prefix. Aggregate book P&L/drawdown withheld whenever an open trade remains unpriced.')
    gap=pd.read_csv(OUT/'results/feed_gaps-1729/predictions-and-outcomes.csv.gz')
    assert (~gap.outcome_available).sum()>0
    assert (gap.observed_feature_fraction<1).any()
    checked('missing_targets_remain_visible',f'{int((~gap.outcome_available).sum())} published forecasts retained with unavailable future outcomes, excluded explicitly from scoring only.')
    # Reconstruct a historical live decision from raw messages. The supplied raw
    # tables contain later messages: as_of must prevent any effect on the reading.
    context=pd.read_csv(base/'inputs/context.csv.gz',float_precision='round_trip')
    for col in ('event_time','available_at'):context[col]=pd.to_datetime(context[col],utc=True,format='mixed')
    panel=prepare_panel(quotes,rates,sessions,model['config'],trades=trades,context=context,as_of=cutoff)
    features=build_features(panel,model['config'])
    live=predict_scenarios(model,panel,features,trades)
    saved=pd.read_csv(base/'predictions-and-outcomes.csv.gz');saved['decision_time']=pd.to_datetime(saved.decision_time,utc=True)
    expected=saved[saved.decision_time==cutoff].set_index('horizon_minutes')
    fields=['p_down','p_neutral','p_up','indicator','endpoint_mean_ticks','endpoint_q10_ticks','endpoint_q90_ticks','mae_long_q80_ticks','mae_short_q80_ticks']
    for row in live.to_dict('records'):
        assert row['status']=='research_forecast'
        assert np.allclose([row[k] for k in fields],expected.loc[row['horizon_minutes'],fields].to_numpy(float),rtol=1e-9,atol=1e-9)
    checked('historical_live_replay_matches_batch','Raw receiver-time replay at first TEST session minute 190 exactly reproduces saved batch probabilities, endpoints and adverse-excursion bounds for all three horizons.')
    saved_features=pd.read_csv(base/'features.csv.gz',index_col=0);saved_features.index=pd.to_datetime(saved_features.index,utc=True)
    assert_frame_equal(features,saved_features.loc[features.index],check_dtype=False,check_names=False,rtol=1e-9,atol=1e-9,check_freq=False)
    checked('feature_prefix_invariance','Recomputed truncated receiver-time history matches full-run features through the cutoff.')
    ref=json.loads((OUT/'example-audit/rerun.json').read_text())
    p=OUT/'reference/provided-example.ipynb';assert hashlib.sha256(p.read_bytes()).hexdigest()==ref['source_sha256']
    assert abs(ref['variants'][0]['net_pnl_pct']-26.113004252244)<1e-9
    assert ref['variants'][0]['net_pnl_pct']==ref['variants'][1]['net_pnl_pct']
    checked('provided_notebook_preserved_and_reproduced','Original notebook SHA unchanged; both normal-scenario variants reproduce identical P&L; only reported ES convention differs.')
    dump_json(OUT/'verification.json',dict(checks=checks,scope='Structural/accounting checks on synthetic inputs, not evidence of market alpha.'))
    return checks


if __name__=='__main__':run_checks()
