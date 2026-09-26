"""Run the predeclared E04-E06 laboratory; no S0 files or fitted models change.

Prices and outcomes here belong to a tractable synthetic world, not the full
bond ecosystem. The Kalman observer knows the DGP; the learned comparator is
a deliberately memory-limited ridge model, not the CGB XGBoost implementation.
"""
from pathlib import Path
import hashlib
import json
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / 'protocol.json').read_text())
OUT = ROOT / 'results'
FIG = ROOT / 'figures'


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def generate(n, minutes, seed, phi, q, r, max_delay=30):
    rng = np.random.default_rng(seed)
    innovations = rng.normal(size=(n, minutes + max_delay + 1))
    eps = rng.normal(size=(n, minutes + 1))
    proxy_noise = rng.normal(size=(n, minutes + max_delay + 1))
    pressure = np.empty_like(innovations)
    pressure[:, 0] = innovations[:, 0] * q / np.sqrt(1 - phi**2)
    for k in range(1, pressure.shape[1]):
        pressure[:, k] = phi * pressure[:, k - 1] + q * innovations[:, k]
    returns = np.zeros_like(eps)
    returns[:, 1:] = pressure[:, max_delay:-1] + r * eps[:, 1:]
    return dict(pressure=pressure, returns=returns, proxy_noise=proxy_noise,
                innovations=innovations, return_noise=eps, max_delay=max_delay)


def observations(world, delay, sd):
    r = world['returns']
    start = world['max_delay'] - delay
    proxy = None if sd is None else (world['pressure'][:, start:start+r.shape[1]]
                                      + sd * world['proxy_noise'][:, start:start+r.shape[1]])
    return r, proxy


def kalman(returns, proxy, delay, proxy_sd, phi, q, r):
    """Augmented causal filter; incoming proxy at t measures pressure at t-delay.

    r[t] measures pressure[t-1]. Each update consumes only the observations in
    that time column. Covariance is shared across worlds with the same sensor.
    """
    worlds, steps = returns.shape
    size = max(2, delay + 1)
    age = np.arange(size)
    cov = q*q/(1-phi*phi) * phi**np.abs(age[:, None]-age[None, :])
    m = np.zeros((worlds, size))
    mean, variance = np.empty_like(returns), np.empty(steps)
    transition = np.zeros((size, size)); transition[0, 0] = phi
    transition[1:, :-1] = np.eye(size-1)
    Q = np.zeros((size, size)); Q[0, 0] = q*q
    eye = np.eye(size)
    for t in range(steps):
        if t:
            m = m @ transition.T
            cov = transition @ cov @ transition.T + Q
        # At time zero, only the proxy is observed; returns[0] is an origin.
        indices = ([1] if t else []) + ([delay] if proxy is not None else [])
        if indices:
            H = eye[indices]
            obs = ([returns[:, t]] if t else []) + ([proxy[:, t]] if proxy is not None else [])
            noise = ([r*r] if t else []) + ([proxy_sd*proxy_sd] if proxy is not None else [])
            R = np.diag(noise)
            gain = np.linalg.solve(H @ cov @ H.T + R, H @ cov).T
            m += (np.column_stack(obs) - m @ H.T) @ gain.T
            # Joseph update protects positive semidefiniteness numerically.
            residual = eye - gain @ H
            cov = residual @ cov @ residual.T + gain @ R @ gain.T
            cov = .5 * (cov + cov.T)
        mean[:, t] = m[:, 0]
        variance[t] = cov[0, 0]
    return mean, variance


def loadings(h, phi, q, r):
    a = (1 - phi**h) / (1 - phi)
    j = np.arange(1, h)
    innovation_variance = q*q*np.sum(((1-phi**j)/(1-phi))**2) + h*r*r
    return float(a), float(innovation_variance)


def features(returns, proxy, origins):
    c = np.cumsum(returns, axis=1)
    cols = [(c[:, origins] - c[:, origins-w]) / w for w in (1, 5, 15, 30)]
    if proxy is not None:
        cols.append(proxy[:, origins])
    return np.stack(cols, axis=-1)


def outcome(returns, origins, h):
    c = np.cumsum(returns, axis=1)
    return c[:, origins+h] - c[:, origins]


def ridge_fit(x, y, penalty):
    x = x.reshape(-1, x.shape[-1]); y = y.ravel()
    center = x.mean(0); scale = x.std(0); scale[scale < 1e-12] = 1.
    design = np.column_stack([np.ones(len(x)), (x-center)/scale])
    reg = np.eye(design.shape[1]) * penalty; reg[0, 0] = 0
    coefficient = np.linalg.solve(design.T @ design + reg, design.T @ y)
    return center, scale, coefficient


def ridge_predict(fit, x):
    center, scale, coef = fit
    return coef[0] + ((x-center)/scale) @ coef[1:]


def evaluate_forecasts():
    phi = P['pressure_phi_per_minute']; q = P['pressure_innovation_sd_ticks_per_minute']; r = P['return_noise_sd_ticks']
    worlds = {}
    for k, (split, count) in enumerate([('train', P['train_worlds']), ('cal', P['calibration_worlds']), ('test', P['test_worlds'])]):
        worlds[split] = generate(count, P['minutes'], np.random.SeedSequence([P['seed'], k]), phi, q, r)
        np.savez_compressed(OUT/f'{split}-worlds.npz', **worlds[split])
    all_rows, summaries, world_rows, paired = [], [], [], []
    invariants = []
    for cfg in P['proxy_configurations']:
        observations_by_split = {s: observations(w, cfg['delay_minutes'], cfg['noise_sd']) for s, w in worlds.items()}
        received_r, received_proxy = observations_by_split['test']
        filter_mean, filter_var = kalman(received_r, received_proxy, cfg['delay_minutes'], cfg['noise_sd'], phi, q, r)
        # Poison messages after a cutoff, then verify the full earlier forecast state is unchanged.
        cutoff = 180
        poisoned_r = received_r.copy(); poisoned_r[:, cutoff+1:] += 1000
        poisoned_p = None if received_proxy is None else received_proxy.copy()
        if poisoned_p is not None: poisoned_p[:, cutoff+1:] -= 1000
        replay_mean, replay_var = kalman(poisoned_r, poisoned_p, cfg['delay_minutes'], cfg['noise_sd'], phi, q, r)
        prefix_gap = float(np.max(np.abs(filter_mean[:, :cutoff+1]-replay_mean[:, :cutoff+1])))
        assert prefix_gap == 0 and np.array_equal(filter_var[:cutoff+1], replay_var[:cutoff+1])
        invariants.append({'configuration': cfg['name'], 'future_message_poison_prefix_gap': prefix_gap,
                           'minimum_filter_variance': float(filter_var.min())})
        assert filter_var.min() >= 0
        for h in P['horizons_minutes']:
            origins = np.arange(P['first_decision_minute'], P['minutes']-h+1, P['decision_step_minutes'])
            x = {s: features(*o, origins) for s, o in observations_by_split.items()}
            y = {s: outcome(o[0], origins, h) for s, o in observations_by_split.items()}
            fit = ridge_fit(x['train'], y['train'], P['ridge_penalty'])
            cal_mean = ridge_predict(fit, x['cal'])
            residual_variance = max(float(np.mean((y['cal']-cal_mean)**2)), 1e-10)
            np.savez_compressed(OUT/f"ridge-{cfg['name']}-{h}.npz", center=fit[0], scale=fit[1], coefficient=fit[2], calibrated_variance=residual_variance)
            a, intrinsic = loadings(h, phi, q, r)
            theta = worlds['test']['pressure'][:, worlds['test']['max_delay']+origins]
            predictions = {
                'hidden_state_oracle': (a*theta, np.full_like(y['test'], intrinsic)),
                'causal_kalman_observer': (a*filter_mean[:, origins], np.broadcast_to(intrinsic+a*a*filter_var[origins], y['test'].shape)),
                'memory_limited_ridge': (ridge_predict(fit, x['test']), np.full_like(y['test'], residual_variance))}
            losses = {}
            for model, (mean, variance) in predictions.items():
                error = y['test']-mean
                loss = .5*(np.log(2*np.pi*variance)+error*error/variance)
                covered = np.abs(error) <= 1.2815515655446004*np.sqrt(variance)
                per_world = loss.mean(1); losses[model] = per_world
                for i, val in enumerate(per_world):
                    world_rows.append(dict(configuration=cfg['name'], horizon_minutes=h, model=model, world=i,
                                           gaussian_nll=float(val), mse=float(np.mean(error[i]**2)), coverage80=float(covered[i].mean())))
                se = per_world.std(ddof=1)/np.sqrt(len(per_world))
                summaries.append(dict(configuration=cfg['name'], horizon_minutes=h, model=model, worlds=len(per_world), origins_per_world=len(origins),
                    gaussian_nll=float(loss.mean()), nll_ci_low=float(loss.mean()-1.96*se), nll_ci_high=float(loss.mean()+1.96*se),
                    endpoint_rmse_ticks=float(np.sqrt(np.mean(error**2))), interval80_coverage=float(covered.mean()),
                    mean_interval80_width_ticks=float((2*1.2815515655446004*np.sqrt(variance)).mean())))
                all_rows.append(pd.DataFrame(dict(configuration=cfg['name'], horizon_minutes=h, model=model,
                    world=np.repeat(np.arange(len(per_world)), len(origins)), decision_minute=np.tile(origins, len(per_world)),
                    mean_ticks=mean.ravel(), variance_ticks2=variance.ravel(), realized_ticks=y['test'].ravel(), gaussian_nll=loss.ravel())))
            for candidate, reference in [('causal_kalman_observer', 'hidden_state_oracle'), ('memory_limited_ridge', 'causal_kalman_observer')]:
                delta = losses[candidate]-losses[reference]; se = delta.std(ddof=1)/np.sqrt(len(delta))
                paired.append(dict(configuration=cfg['name'], horizon_minutes=h, candidate=candidate, reference=reference,
                    mean_loss_gap=float(delta.mean()), ci_low=float(delta.mean()-1.96*se), ci_high=float(delta.mean()+1.96*se),
                    analytic_information_gap=float(.5*np.log((intrinsic+a*a*filter_var[origins])/intrinsic).mean()) if reference=='hidden_state_oracle' else np.nan))
    pd.concat(all_rows, ignore_index=True).to_csv(OUT/'forecast-rows.csv.gz', index=False, compression='gzip')
    pd.DataFrame(world_rows).to_csv(OUT/'per-world-scores.csv', index=False)
    pd.DataFrame(summaries).to_csv(OUT/'forecast-summary.csv', index=False)
    pd.DataFrame(paired).to_csv(OUT/'paired-gaps.csv', index=False)
    return invariants


def twins():
    cfg = P['twins']; n=cfg['worlds']; T=cfg['duration_minutes']; cut=cfg['change_minute']; delay=5
    rng=np.random.default_rng(np.random.SeedSequence([P['seed'], 10]))
    shocks=rng.normal(size=(n,T+1)); eps=rng.normal(size=(n,T+1)); noise=rng.normal(size=(n,T+1))
    prehistory_noise=rng.normal(size=(n,delay))
    branches={}; rows=[]
    for name,sign in [('continuation',-1),('reversal',1)]:
        pressure=np.empty_like(shocks); pressure[:,0]=-.25
        returns=np.zeros_like(shocks)
        for t in range(T):
            target=-.25 if t<cut else sign*cfg['post_change_target_ticks_per_minute']
            pressure[:,t+1]=cfg['mean_reversion_phi']*pressure[:,t]+(1-cfg['mean_reversion_phi'])*target+.025*shocks[:,t+1]
            returns[:,t+1]=pressure[:,t]+.8*eps[:,t+1]
        # Pre-session observations have distinct source times; never repeat one
        # observation and label it as several newly received measurements.
        history=np.column_stack([np.repeat(pressure[:,[0]],delay,axis=1),pressure])
        observation_noise=np.column_stack([prehistory_noise,noise])
        received_proxy=history[:,:T+1]+.1*observation_noise[:,:T+1]
        mean,var=kalman(returns,received_proxy,delay,.1,P['pressure_phi_per_minute'],P['pressure_innovation_sd_ticks_per_minute'],P['return_noise_sd_ticks'])
        a,intrinsic=loadings(60,P['pressure_phi_per_minute'],P['pressure_innovation_sd_ticks_per_minute'],P['return_noise_sd_ticks'])
        branches[name]=(returns,received_proxy,mean)
        for i in range(n):
            rows.append(pd.DataFrame(dict(branch=name,world=i,minute=np.arange(T+1),
                pressure_truth=pressure[i],received_return=returns[i],received_proxy=received_proxy[i],
                cumulative_price_ticks=np.cumsum(returns[i]),forecast60_mean_ticks=a*mean[i])))
    A=branches['continuation'];B=branches['reversal']
    for left,right in zip(A,B):assert np.array_equal(left[:,:cut+1],right[:,:cut+1])
    first_observable=min(int(np.flatnonzero(np.any(a!=b,axis=0))[0]) for a,b in zip(A[:2],B[:2]))
    first_prediction=int(np.flatnonzero(np.any(A[2]!=B[2],axis=0))[0])
    assert first_prediction>=first_observable
    df=pd.concat(rows,ignore_index=True);df.to_csv(OUT/'twins.csv.gz',index=False,compression='gzip')
    result=dict(prefix_through_minute=cut,prefix_observations_identical=True,prefix_forecasts_identical=True,
        first_different_received_minute=first_observable,first_different_forecast_minute=first_prediction,
        interpretation='Identical histories cannot reveal hidden branch identity; after new evidence arrives, the same observer begins to distinguish them. This is a target-switch toy world, not inventory clearing.')
    dump(OUT/'twins-verification.json',result)
    return result


def martingale():
    cfg=P['martingale'];n=cfg['worlds'];T=cfg['minutes'];hold=cfg['minimum_hold_minutes']
    rng=np.random.default_rng(np.random.SeedSequence([P['seed'],20]))
    changes=rng.choice([-1.,1.],size=(n,T))*cfg['independent_step_ticks']
    prices=12000.5+np.column_stack([np.zeros(n),np.cumsum(changes,axis=1)])
    np.savez_compressed(OUT/'martingale-worlds.npz',price_mid_ticks=prices,innovations_ticks=changes)
    ledgers=[];summaries=[];perworld=[]
    roundtrip=2*cfg['one_way_half_spread_ticks']+cfg['roundtrip_extra_slippage_ticks']+cfg['roundtrip_fee_ticks']
    for policy in cfg['policies']:
        gross=np.zeros(n);cost=np.zeros(n);count=np.zeros(n,dtype=int)
        for t in range(30,T-hold+1,hold):
            past=prices[:,t]-prices[:,t-30]
            direction=np.ones(n) if policy=='always_long' else (-np.ones(n) if policy=='always_short' else np.sign(past)*(1 if policy=='past_30min_momentum' else -1))
            active=direction!=0
            pnl=direction*(prices[:,t+hold]-prices[:,t]); charge=active*roundtrip
            entry_touch=prices[:,t]+direction*cfg['one_way_half_spread_ticks']
            exit_touch=prices[:,t+hold]-direction*cfg['one_way_half_spread_ticks']
            net_from_touches=direction*(exit_touch-entry_touch)-active*(cfg['roundtrip_extra_slippage_ticks']+cfg['roundtrip_fee_ticks'])
            assert np.allclose(pnl-charge,net_from_touches,atol=1e-9)
            gross+=pnl;cost+=charge;count+=active
            ledgers.append(pd.DataFrame(dict(policy=policy,world=np.arange(n),decision_minute=t,exit_minute=t+hold,
                direction=direction,past30_return_ticks=past,entry_touch_ticks=entry_touch,exit_touch_ticks=exit_touch,
                gross_ticks=pnl,cost_ticks=charge,net_ticks=pnl-charge)))
        net=gross-cost;se_g=gross.std(ddof=1)/math.sqrt(n);se_n=net.std(ddof=1)/math.sqrt(n)
        summaries.append(dict(policy=policy,worlds=n,mean_gross_ticks=float(gross.mean()),gross_ci_low=float(gross.mean()-1.96*se_g),gross_ci_high=float(gross.mean()+1.96*se_g),
            mean_cost_ticks=float(cost.mean()),mean_net_ticks=float(net.mean()),net_ci_low=float(net.mean()-1.96*se_n),net_ci_high=float(net.mean()+1.96*se_n),
            fraction_profitable_worlds=float((net>0).mean()),mean_roundtrips=float(count.mean())))
        perworld.append(pd.DataFrame(dict(policy=policy,world=np.arange(n),gross_ticks=gross,cost_ticks=cost,net_ticks=net,roundtrips=count)))
    pd.concat(ledgers,ignore_index=True).to_csv(OUT/'martingale-ledger.csv.gz',index=False,compression='gzip')
    pd.concat(perworld,ignore_index=True).to_csv(OUT/'martingale-per-world.csv',index=False)
    pd.DataFrame(summaries).to_csv(OUT/'martingale-summary.csv',index=False)
    return dict(bounded_predictable_positions=True,steps_independent_symmetric=True,touch_accounting_reconciled=True,roundtrip_cost_ticks=roundtrip,
                selection='All four policies retained; none selected or tuned using final outcomes.')


def plots():
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    df=pd.read_csv(OUT/'paired-gaps.csv');a=df.query("horizon_minutes==60 and reference=='hidden_state_oracle'")
    fig,ax=plt.subplots(figsize=(11,5),layout='constrained')
    x=np.arange(len(a)); y=a.mean_loss_gap.to_numpy()
    ax.errorbar(x,y,yerr=np.vstack([y-a.ci_low.to_numpy(),a.ci_high.to_numpy()-y]),fmt='o',capsize=5,label='Observed paired loss gap ±95% world CI')
    ax.scatter(x,a.analytic_information_gap,marker='x',s=75,color='#d55e00',label='Known-DGP conditional entropy gap')
    ax.axhline(0,color='#777',lw=.8);ax.set_xticks(x,[s.replace('_','\n') for s in a.configuration]);ax.set_ylabel('Observer NLL minus hidden-state oracle NLL')
    ax.set_title('Information lost between hidden pressure and received observations\n60-minute forecast • synthetic linear Gaussian laboratory');ax.legend(fontsize=9)
    fig.savefig(FIG/'01-observability-gap.png',dpi=170);plt.close(fig)
    twin=pd.read_csv(OUT/'twins.csv.gz').groupby(['branch','minute']).mean(numeric_only=True).reset_index()
    fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True,layout='constrained')
    for name,color in [('continuation','#0072b2'),('reversal','#d55e00')]:
        t=twin[twin.branch==name];axes[0].plot(t.minute,t.cumulative_price_ticks,label=name,color=color)
        axes[1].plot(t.minute,t.forecast60_mean_ticks,label=name,color=color)
    for ax in axes:ax.axvline(P['twins']['change_minute'],color='#666',ls='--');ax.legend()
    axes[0].set_title('Identical observed opening; different hidden targets after minute 180\nMeans across 128 paired synthetic worlds; same causal observer');axes[0].set_ylabel('Cumulative midpoint move (ticks)')
    axes[1].set_ylabel('Forecast next 60-minute move (ticks)');axes[1].set_xlabel('Minute')
    fig.savefig(FIG/'02-observable-twins.png',dpi=170);plt.close(fig)
    m=pd.read_csv(OUT/'martingale-per-world.csv');fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
    for ax,(name,g) in zip(axes.ravel(),m.groupby('policy',sort=False)):
        ax.hist(g.net_ticks,bins=30,color='#0072b2',alpha=.85);ax.axvline(0,color='#d55e00',ls='--');ax.set_title(name.replace('_',' '));ax.set_xlabel('Net ticks per 480-minute world');ax.set_ylabel('World count')
    fig.suptitle('Strict martingale price control • 1,024 worlds • explicit crossing costs\nProfitable individual worlds can occur without positive expected gains')
    fig.savefig(FIG/'03-martingale-control.png',dpi=170);plt.close(fig)


def main():
    if (OUT/'COMPLETE.json').exists():
        raise SystemExit('Completed laboratory already exists; preserve it or choose a new version.')
    OUT.mkdir(parents=True,exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
    print('Running causal observation comparisons...',flush=True)
    observer=evaluate_forecasts()
    print('Running identical-prefix twins...',flush=True)
    twins_check=twins()
    print('Running strict martingale control...',flush=True)
    martingale_check=martingale()
    plots()
    result=dict(status='PASS',observer_checks=observer,twins=twins_check,martingale=martingale_check,
                protocol_sha256=hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),
                code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                source_scope='This new standalone world does not modify S0 or fit its CGB model.')
    dump(OUT/'verification.json',result)
    dump(OUT/'COMPLETE.json',{'status':'complete','experiment_groups':['E04','E05','E06'],'protocol_sha256':result['protocol_sha256']})
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
