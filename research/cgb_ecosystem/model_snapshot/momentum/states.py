"""Observable CGB states and pressure/response diagnostics, derived for this task.

State count is balance plus two directions times maintaining/losing response.
These describe past observations. They are not physical causes or trade commands.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .features import FEATURE_MODULES, _utc_column

STATE_NAMES=('balanced','up-responsive','up-weakening','down-responsive','down-weakening')
CONTRACT_VERSION='cad-conditional-paths-v1'


@dataclass(frozen=True)
class ScenarioConfig:
    decision_step_minutes: int = 5
    transition_prior_count: float = 10.0
    neighbor_count: int = 64
    kernel_floor: float = 1e-6
    max_flow_delay_seconds: float = 30.
    minimum_classified_fraction: float = .8
    recovery_retrace_sigma: float = .75
    recovery_timeout_minutes: int = 20
    trees: int = 100
    tree_depth: int = 2
    learning_rate: float = .03
    random_state: int = 20260924

    def validate(self, cfg):
        if self.decision_step_minutes % cfg.grid_minutes or self.decision_step_minutes<=0:
            raise ValueError('Decision step must be a positive multiple of the quote grid.')
        if any(h % self.decision_step_minutes for h in cfg.horizons_minutes):
            raise ValueError('Horizons must be multiples of the state decision step.')
        if self.neighbor_count<2 or self.trees<1 or self.tree_depth<1:
            raise ValueError('Invalid neighborhood or tree size.')
        if not 0<self.kernel_floor<1 or not 0<self.minimum_classified_fraction<=1:
            raise ValueError('Invalid probability floor or classified fraction.')
        numbers=(self.transition_prior_count,self.max_flow_delay_seconds,
                 self.recovery_retrace_sigma,self.recovery_timeout_minutes,self.learning_rate)
        if not all(np.isfinite(x) and x>0 for x in numbers):
            raise ValueError('Configuration values must be finite and positive.')


def signed_flow_grid(panel, trades, cfg, scfg):
    """Receiver-time flow; aggressor: +1 buy, -1 sell, 0 unknown.

    A missing feed is unknown. With a supplied complete tape, an empty bin is zero.
    Trade corrections must be resolved upstream; duplicate IDs are rejected.
    """
    out=pd.DataFrame(np.nan,index=panel.index,columns=['flow_volume','classified_volume','signed_volume'])
    if trades is None or trades.empty or 'aggressor' not in trades:
        return out
    required={'trade_id','instrument','contract','event_time','available_at','size','aggressor'}
    if not required.issubset(trades):raise ValueError(f'Missing signed-flow fields: {required-set(trades)}')
    t=trades.copy()
    for field in ('event_time','available_at'):t[field]=_utc_column(t,field)
    t=t[t.available_at<=panel.index.max()].copy()
    if t.trade_id.isna().any() or t.trade_id.duplicated().any():raise ValueError('Signed trades need unique IDs.')
    if not t.instrument.eq('CGB').all() or not t.aggressor.isin([-1,0,1]).all():
        raise ValueError('Only identified CGB trades and explicit aggressor codes are accepted.')
    if not np.isfinite(t['size']).all() or (t['size']<=0).any() or (t.event_time>t.available_at).any():
        raise ValueError('Invalid trade size or timing.')
    t['late']=(t.available_at-t.event_time).dt.total_seconds()>scfg.max_flow_delay_seconds
    for _, p in panel.groupby('segment_id',sort=False):
        idx=p.index
        rows=t[t.contract.eq(p.contract.iloc[0]) & t.event_time.between(idx[0],idx[-1]) &
               t.available_at.between(idx[0],idx[-1])].copy()
        out.loc[idx]=0.
        if rows.empty:continue
        positions=np.searchsorted(idx.asi8,rows.available_at.astype('int64').to_numpy())
        rows['decision_time']=idx[positions]
        rows['signed_volume']=rows['size']*rows.aggressor
        rows['classified_volume']=rows['size']*rows.aggressor.ne(0)
        sums=rows.groupby('decision_time')[['size','classified_volume','signed_volume']].sum()
        out.loc[sums.index]=sums.rename(columns={'size':'flow_volume'}).to_numpy()
        out.loc[rows.loc[rows.late,'decision_time'].unique()]=np.nan
    return out


def build_state_observations(panel, features, cfg, scfg, trades=None):
    scfg.validate(cfg)
    if panel is None or panel.empty:return pd.DataFrame()
    flow=signed_flow_grid(panel,trades,cfg,scfg)
    rows=[]
    for _, p in panel.groupby('segment_id',sort=False):
        f=features.loc[p.index]
        step=scfg.decision_step_minutes//cfg.grid_minutes
        five=5//cfg.grid_minutes
        sums=flow.loc[p.index].rolling(five,min_periods=five).sum()
        pressure=sums.signed_volume/sums.classified_volume.where(sums.classified_volume>0)
        coverage=sums.classified_volume/sums.flow_volume.where(sums.flow_volume>0)
        available=(coverage>=scfg.minimum_classified_fraction)&sums.classified_volume.gt(0)
        scale=f.sigma_ticks*np.sqrt(five)
        response=f.mom_ticks_5/scale
        absorption=(pressure.abs()*np.exp(-np.maximum(np.sign(pressure)*response,0))).where(available)
        state=-1;age=0;previous=None;attempt=False;peak=np.nan;began=None;failures=0
        for time in p.index[::step]:
            x=f.loc[time]; q=p.loc[time]
            valid=bool(q.cgb_valid and np.isfinite(x[FEATURE_MODULES['cgb'][:11]].to_numpy(dtype=float)).all())
            consecutive=previous is not None and time-previous==pd.Timedelta(minutes=scfg.decision_step_minutes)
            if not valid:
                state=-1;age=0;attempt=False;failures=0
            else:
                direction=int(np.sign(x.mom_z_30)) if abs(x.mom_z_30)>=cfg.phase_threshold else 0
                weakening=direction*(x.mom_ticks_5/5)<.5*direction*(x.mom_ticks_30/30)
                new_state=0 if direction==0 else (1 if direction>0 else 3)+int(weakening)
                age=age+scfg.decision_step_minutes if consecutive and state==new_state else scfg.decision_step_minutes
                state=new_state
            failed=False
            vwap_ok=valid and pd.notna(q.vwap) and q.vwap_status=='observed_tape'
            if not vwap_ok:attempt=False
            elif attempt:
                peak=max(peak,float(q.cgb_mid))
                if q.cgb_mid>=q.vwap or time-began>pd.Timedelta(minutes=scfg.recovery_timeout_minutes):
                    attempt=False
                elif (peak-q.cgb_mid)/cfg.tick_size>=scfg.recovery_retrace_sigma*scale.loc[time]:
                    failed=True;failures+=1;attempt=False
            elif q.cgb_mid<q.vwap and x.mom_ticks_5>0 and x.mom_z_30<-cfg.phase_threshold:
                attempt=True;peak=float(q.cgb_mid);began=time
            common=x.get('common_ticks_1',np.nan);local=x.get('local_ticks_1',np.nan)
            record={'decision_time':time,'session_id':q.session_id,'segment_id':q.segment_id,
                    'valid':valid,'state_id':state,'state_age_minutes':age,
                    'flow_available':bool(available.loc[time]),'flow_pressure':pressure.loc[time] if available.loc[time] else np.nan,
                    'absorption':absorption.loc[time],'response_z5':response.loc[time],
                    'vwap_available':bool(vwap_ok),'recovery_active':int(attempt),
                    'recovery_failed_now':int(failed),'recovery_failures':failures,
                    'reference_available':bool(np.isfinite(common) and np.isfinite(local)),
                    'reference_residual_z':local/x.sigma_ticks if valid and np.isfinite(local) else np.nan,
                    'minutes_remaining':(q.session_close-time).total_seconds()/60}
            record['minutes_from_segment_open']=(time-p.index[0]).total_seconds()/60
            for j in range(5):record[f'state_{j}']=float(state==j) if valid else np.nan
            rows.append(record);previous=time if valid else None
    return pd.DataFrame(rows).set_index('decision_time').sort_index()


def model_measurements(features, observations, cfg, use_flow=False, use_vwap=False):
    """Explicit feature provenance; no target, posterior or future column is selected."""
    columns=[];groups={}
    for module in cfg.feature_modules:
        for column in FEATURE_MODULES[module]:
            if column.startswith('phase_'):continue
            columns.append(column);groups[column]=module
    x=features.loc[observations.index,columns].copy()
    added=['state_age_minutes','response_z5','minutes_remaining','minutes_from_segment_open']
    added += [f'state_{j}' for j in range(5)]
    if use_flow:added+=['flow_pressure','absorption','flow_available']
    if use_vwap:added+=['recovery_active','recovery_failed_now','recovery_failures','vwap_available']
    for name in added:
        x[name]=observations[name].astype(float)
        groups[name]='flow' if name in ('flow_pressure','absorption','flow_available') else ('recovery' if name.startswith('recovery') or name=='vwap_available' else 'state')
    return x.replace([np.inf,-np.inf],np.nan),groups
