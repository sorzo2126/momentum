"""Conditional empirical CGB path distributions with learned state transitions.

All predictive components are fitted on TRAIN; distribution mixtures are fitted
on CAL. Exact sums over finite scenarios replace unnecessary Monte Carlo noise.
"""
import hashlib
import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar
from .model import make_targets, split_sessions, _session_weights, _module_coverage, _metrics
from .states import ScenarioConfig, STATE_NAMES, CONTRACT_VERSION, build_state_observations, model_measurements


def _normal(values):
    values=np.asarray(values,dtype=float)
    if not np.isfinite(values).all() or (values<0).any() or values.sum()<=0:
        raise ValueError('A distribution needs finite, nonnegative scores and positive mass.')
    return values/values.sum(axis=-1,keepdims=True)


def fit_head(x,y,weights,scfg,cfg):
    from xgboost import XGBClassifier
    classes=np.unique(np.asarray(y,dtype=int))
    counts=np.bincount(np.searchsorted(classes,np.asarray(y,dtype=int)),weights=weights,minlength=len(classes))
    result={'classes':classes,'prior':_normal(counts),'model':None}
    if len(classes)>1:
        model=XGBClassifier(n_estimators=scfg.trees,max_depth=scfg.tree_depth,learning_rate=scfg.learning_rate,
            min_child_weight=10,reg_lambda=10,subsample=1.,colsample_bytree=1.,tree_method='hist',
            device=cfg.xgb_device,n_jobs=2,random_state=scfg.random_state,
            objective='multi:softprob',num_class=len(classes),eval_metric='mlogloss')
        model.fit(x,np.searchsorted(classes,np.asarray(y,dtype=int)),sample_weight=weights)
        result['model']=model
    return result


def predict_head(head,x,n_classes):
    p=np.zeros((len(x),n_classes))
    predicted=np.tile(head['prior'],(len(x),1)) if head['model'] is None else head['model'].predict_proba(x)
    p[:,head['classes']]=predicted
    return p/p.sum(1,keepdims=True)


def transition_distribution(current,future,weights,prior_count):
    counts=np.zeros((5,5))
    np.add.at(counts,(np.asarray(current,dtype=int),np.asarray(future,dtype=int)),weights)
    prior=_normal(counts.sum(0))
    return (counts+prior_count*prior)/(counts.sum(1,keepdims=True)+prior_count)


def weighted_quantile(values,weights,level):
    order=np.argsort(values,kind='stable')
    return float(np.asarray(values)[order][min(np.searchsorted(np.cumsum(np.asarray(weights)[order]),level,side='left'),len(order)-1)])


def _scale_fit(x):
    median=x.median().fillna(0.)
    spread=(x.quantile(.75)-x.quantile(.25)).where(lambda y:y>1e-9,1.).fillna(1.)
    return median.to_numpy(float),spread.to_numpy(float)


def neighborhood(bank,x):
    """Equal mass per economic group, not per number of correlated columns."""
    current=(np.asarray(x,float)-bank['center'])/bank['scale']
    history=bank['standardized_x']
    group_distances=[];group_present=[]
    for group in dict.fromkeys(bank['groups']):
        ids=np.flatnonzero(np.asarray(bank['groups'])==group)
        valid=np.isfinite(history[:,ids])&np.isfinite(current[ids])
        delta=np.where(valid,history[:,ids]-current[ids],0.)
        n=valid.sum(1)
        distance=np.divide((delta**2).sum(1),n,out=np.zeros(len(history)),where=n>0)
        group_distances.append(distance);group_present.append(n>0)
    present=np.array(group_present);distances=np.array(group_distances)
    shared=present.sum(0)
    d2=np.divide((distances*present).sum(0),shared,out=np.full(len(history),np.inf),where=shared>0)
    if not np.isfinite(d2).any():raise ValueError('No comparable observed feature group.')
    k=min(bank['neighbor_count'],np.isfinite(d2).sum())
    bandwidth=max(float(np.partition(d2,k-1)[k-1]),1e-8)
    scores=np.maximum(np.exp(-.5*d2/bandwidth),bank['kernel_floor'])*bank['session_weights']
    return _normal(scores),float(np.sqrt(np.min(d2))),float(np.isfinite(current).mean())


def redistribute(base,groups,probabilities):
    """Law of total probability: p(path)=p(group)*p(path|group)."""
    base=np.asarray(base);groups=np.asarray(groups,dtype=int);p=np.asarray(probabilities,float).copy()
    present=np.bincount(groups,minlength=len(p))>0
    unsupported=float(p[~present].sum());p[~present]=0
    if p.sum()<=0:raise ValueError('Forecast places no mass on observed scenario support.')
    p/=p.sum()
    out=np.zeros_like(base)
    for group in np.flatnonzero(present):
        mask=groups==group
        out[mask]=p[group]*base[mask]/base[mask].sum()
    return _normal(out),unsupported


def path_experts(bank,x,state_probability,price_probability):
    local,distance,coverage=neighborhood(bank,x)
    structural,unsupported=redistribute(local,bank['future_states'],state_probability)
    supervised,_=redistribute(local,bank['classes'],price_probability)
    paths=np.array([local,structural,supervised])
    endpoint=np.array([[p[bank['classes']==j].sum() for j in range(3)] for p in paths])
    return paths,endpoint,{'nearest_distance':distance,'observed_feature_fraction':coverage,
                           'unsupported_future_state_mass':unsupported}


def _state_weight(p_ml,p_transition,truth,weights):
    row=np.arange(len(truth));truth=np.asarray(truth,int)
    objective=lambda w:float(np.average(-np.log(np.maximum((w*p_ml+(1-w)*p_transition)[row,truth],1e-12)),weights=weights))
    result=minimize_scalar(objective,bounds=(0,1),method='bounded')
    if not result.success:raise ValueError('State calibration failed.')
    return float(result.x)


def _mixture_weights(probabilities,truth,weights):
    # probabilities shape: rows x experts x endpoint classes. Convex objective.
    selected=np.array([p[:,int(c)] for p,c in zip(probabilities,truth)])
    objective=lambda w:float(np.average(-np.log(np.maximum(selected@w,1e-12)),weights=weights))
    result=minimize(objective,np.ones(3)/3,method='SLSQP',bounds=[(0,1)]*3,
                    constraints={'type':'eq','fun':lambda w:w.sum()-1},options={'ftol':1e-10,'maxiter':200})
    if not result.success:raise ValueError('Path mixture calibration failed: '+result.message)
    return _normal(np.clip(result.x,0,1))


def input_fingerprint(panel,features,cutoff):
    p=panel.loc[panel.index<=cutoff].copy()
    f=features.reindex(p.index)
    digest=hashlib.sha256()
    for frame in (p,f):
        digest.update('|'.join(map(str,frame.columns)).encode())
        digest.update(pd.util.hash_pandas_object(frame,index=True).to_numpy().tobytes())
    return digest.hexdigest()


def observation_fingerprint(observations,cutoff):
    return hashlib.sha256(pd.util.hash_pandas_object(observations.loc[observations.index<=cutoff],index=True).to_numpy().tobytes()).hexdigest()


def _make_bank(panel,features,x,observations,targets,index,horizon,cfg,scfg,groups):
    n=horizon//cfg.grid_minutes
    positions=panel.index.get_indexer(index)
    mid=panel.cgb_mid.to_numpy(float)
    paths=np.array([(mid[i:i+n+1]-mid[i])/cfg.tick_size/features.loc[t,'sigma_ticks']
                    for i,t in zip(positions,index)],dtype=np.float64)
    future_times=pd.DatetimeIndex(targets.loc[index,'target_end'])
    future=observations.state_id.reindex(future_times).to_numpy(int)
    center,scale=_scale_fit(x.loc[index])
    weights=_session_weights(panel.loc[index,'session_id'])
    return {'paths':paths,'classes':targets.loc[index,'class_id'].to_numpy(int),
        'future_states':future,'current_states':observations.loc[index,'state_id'].to_numpy(int),
        'center':center,'scale':scale,'standardized_x':(x.loc[index].to_numpy(float)-center)/scale,
        'session_weights':weights,'groups':[groups[c] for c in x.columns],
        'feature_columns':list(x.columns),'neighbor_count':scfg.neighbor_count,'kernel_floor':scfg.kernel_floor,
        'train_times':[t.isoformat() for t in index],'horizon_minutes':horizon,
        'endpoint':paths[:,-1],'mae_long':np.maximum(-paths.min(1),0),
        'mae_short':np.maximum(paths.max(1),0)}


def fit_scenario_research(panel,features,cfg,scfg=None,trades=None):
    scfg=scfg or ScenarioConfig();scfg.validate(cfg)
    result={'status':'awaiting_data','horizons':{},'config':cfg,'scenario_config':scfg,'contract':CONTRACT_VERSION}
    if panel is None or features is None or panel.empty:return result
    splits=split_sessions(panel,cfg);result['splits']=splits
    if splits['metadata']['status']!='ready':
        result.update(status='insufficient_history',reason=splits['metadata']);return result
    observations=build_state_observations(panel,features,cfg,scfg,trades)
    flow_days=observations.loc[observations.index.intersection(splits['train'])].query('flow_available').session_id.nunique()
    use_flow=flow_days>=cfg.min_train_sessions
    use_vwap='vwap' in cfg.feature_modules
    x,groups=model_measurements(features,observations,cfg,use_flow,use_vwap)
    result.update(observations=observations,use_flow=use_flow,use_vwap=use_vwap,feature_columns=list(x.columns),
        history_start=panel.index[0],available_after=splits['cal'].max(),
        input_fingerprint=input_fingerprint(panel,features,splits['cal'].max()),
        observation_fingerprint=observation_fingerprint(observations,splits['cal'].max()))
    targets=make_targets(panel,features,cfg)
    reports=[];predictions=[]
    for horizon,y in targets.items():
        entry={'status':'insufficient_history'};result['horizons'][int(horizon)]=entry
        indices={}
        for part in ('train','cal','test'):
            idx=observations.index.intersection(splits[part]);ends=y.loc[idx,'target_end']
            future=observations.state_id.reindex(pd.DatetimeIndex(ends)).to_numpy()
            good=observations.loc[idx,'valid'].to_numpy() & y.loc[idx,'class_id'].notna().to_numpy()
            good &= ends.isin(splits[part]).to_numpy() & np.isfinite(future) & (future>=0)
            indices[part]=idx[good]
        tr,ca,te=(indices[k] for k in ('train','cal','test'))
        entry['eligible_sessions']={k:int(panel.loc[i,'session_id'].nunique()) for k,i in indices.items()}
        minima={'train':cfg.min_train_sessions,'cal':cfg.min_cal_sessions,'test':cfg.min_test_sessions}
        if any(entry['eligible_sessions'][k]<minima[k] or len(indices[k])<30 for k in indices):
            entry['reason']='Too few complete paths and sessions for TRAIN/CAL/TEST.';continue
        coverage=_module_coverage(panel,features,tr,cfg);entry['module_coverage']=coverage
        if any(v['sessions']<cfg.min_train_sessions or v['rows']<30 for v in coverage.values()):
            entry['reason']='An enabled observation module lacks TRAIN coverage.';continue
        if set(y.loc[tr,'class_id'].astype(int))!={0,1,2}:
            entry['reason']='The empirical path bank must represent all three endpoint classes.';continue
        bank=_make_bank(panel,features,x,observations,y,tr,horizon,cfg,scfg,groups)
        wt=bank['session_weights'];wc=_session_weights(panel.loc[ca,'session_id'])
        transition=transition_distribution(bank['current_states'],bank['future_states'],wt,scfg.transition_prior_count)
        state_head=fit_head(x.loc[tr],bank['future_states'],wt,scfg,cfg)
        price_head=fit_head(x.loc[tr],bank['classes'],wt,scfg,cfg)
        both=ca.append(te)
        state_ml=predict_head(state_head,x.loc[both],5);price_ml=predict_head(price_head,x.loc[both],3)
        state_prior=transition[observations.loc[both,'state_id'].to_numpy(int)]
        future_truth=observations.state_id.reindex(pd.DatetimeIndex(y.loc[both,'target_end'])).to_numpy(int)
        alpha=_state_weight(state_ml[:len(ca)],state_prior[:len(ca)],future_truth[:len(ca)],wc)
        state_p=alpha*state_ml+(1-alpha)*state_prior
        endpoint_cal=[]
        for i,time in enumerate(ca):
            _,p,_=path_experts(bank,x.loc[time],state_p[i],price_ml[i]);endpoint_cal.append(p)
        mixture=_mixture_weights(np.array(endpoint_cal),y.loc[ca,'class_id'].to_numpy(int),wc)
        entry.update(status='ready',bank=bank,state_head=state_head,price_head=price_head,
                     transition=transition,state_ml_weight=alpha,mixture_weights=mixture,indices=indices)
        test_rows=[];individual={name:[] for name in ('local','structural','supervised')}
        individual_means={name:[] for name in individual}
        for offset,time in enumerate(te,start=len(ca)):
            experts,endpoint,diag=path_experts(bank,x.loc[time],state_p[offset],price_ml[offset])
            row=_forecast_summary(entry,experts,state_p[offset],features.loc[time,'sigma_ticks'],diag)
            row.update(decision_time=time,horizon_minutes=horizon,model_use='TEST',
                       observed_state=STATE_NAMES[int(observations.loc[time,'state_id'])])
            test_rows.append(row)
            for j,name in enumerate(individual):
                individual[name].append(endpoint[j])
                individual_means[name].append(float(experts[j]@bank['endpoint']*features.loc[time,'sigma_ticks']))
        frame=pd.DataFrame(test_rows).set_index('decision_time');predictions.extend(test_rows)
        actual=y.loc[te];sessions=panel.loc[te,'session_id']
        prior=np.bincount(bank['classes'],weights=wt,minlength=3);prior/=prior.sum()
        candidates={**{k:np.array(v) for k,v in individual.items()},
                    'mixture':frame[['p_down','p_neutral','p_up']].to_numpy(),
                    'train_frequency':np.tile(prior,(len(te),1))}
        means={**individual_means,'mixture':frame.endpoint_mean_ticks,
               'train_frequency':np.repeat(np.average(y.loc[tr,'return_ticks'],weights=wt),len(te))}
        entry['metrics']={}
        for name,prob in candidates.items():
            metric=_metrics(prob,actual.class_id.astype(int),actual.return_ticks,means[name],sessions)
            entry['metrics'][name]=metric
            reports.append({'horizon_minutes':horizon,'expert':name,'log_loss':metric['log_loss'],'brier':metric['brier'],
                            'endpoint_mae_ticks':metric['endpoint_mae_ticks'],
                            'rows':len(te),'sessions':sessions.nunique()})
        entry['test_predictions']=frame
        risk={}
        for side in ('long','short'):
            truth=actual[f'mae_{side}_ticks'].to_numpy();pred=frame[f'mae_{side}_q80_ticks'].to_numpy()
            residual=truth-pred;w=_session_weights(sessions)
            risk[side]={'coverage_q80':float(np.average(truth<=pred,weights=w)),
                        'pinball_q80':float(np.average(np.maximum(.8*residual,-.2*residual),weights=w))}
        entry['risk_metrics']=risk
    result['report']=pd.DataFrame(reports)
    ready=sum(e['status']=='ready' for e in result['horizons'].values())
    result['status']='ready' if ready==len(result['horizons']) else ('partial' if ready else 'no_eligible_horizons')
    return result


def _forecast_summary(entry,experts,state_probability,sigma,diagnostics):
    bank=entry['bank'];weights=_normal(entry['mixture_weights']@experts)
    probabilities=np.array([weights[bank['classes']==j].sum() for j in range(3)])
    endpoints=bank['endpoint']*sigma
    expert_classes=np.array([[w[bank['classes']==j].sum() for j in range(3)] for w in experts])
    mean=expert_classes.mean(0)
    divergence=float(np.mean(np.sum(expert_classes*np.log(np.maximum(expert_classes,1e-12)/np.maximum(mean,1e-12)),axis=1)))
    return {'p_down':probabilities[0],'p_neutral':probabilities[1],'p_up':probabilities[2],
        'indicator':probabilities[2]-probabilities[0],'endpoint_mean_ticks':float(weights@endpoints),
        'endpoint_q10_ticks':weighted_quantile(endpoints,weights,.1),'endpoint_q90_ticks':weighted_quantile(endpoints,weights,.9),
        'mae_long_q80_ticks':weighted_quantile(bank['mae_long']*sigma,weights,.8),
        'mae_short_q80_ticks':weighted_quantile(bank['mae_short']*sigma,weights,.8),
        'effective_scenarios':float(1/(weights@weights)),
        'predictive_entropy':float(-np.sum(probabilities*np.log(np.maximum(probabilities,1e-12)))/np.log(3)),
        'expert_disagreement':divergence,'future_state_probabilities':state_probability.tolist(),**diagnostics}


def predict_scenarios(research,panel,features,trades=None,verify_history=True):
    if research.get('status') not in ('ready','partial'):return pd.DataFrame()
    cfg,scfg=research['config'],research['scenario_config']
    if panel.index[0]!=pd.Timestamp(research['history_start']):raise ValueError('Replay must start at the saved history origin.')
    if panel.index[-1]<=pd.Timestamp(research['available_after']):raise ValueError('Live inference must follow calibration.')
    if verify_history and input_fingerprint(panel,features,pd.Timestamp(research['available_after']))!=research['input_fingerprint']:
        raise ValueError('Historical measurements changed; create a new versioned fit.')
    observations=build_state_observations(panel,features,cfg,scfg,trades)
    if verify_history and observation_fingerprint(observations,pd.Timestamp(research['available_after']))!=research['observation_fingerprint']:
        raise ValueError('Historical state/flow observations changed; create a new versioned fit.')
    x,_=model_measurements(features,observations,cfg,research['use_flow'],research['use_vwap'])
    if list(x.columns)!=research['feature_columns']:raise ValueError('Feature contract changed.')
    time=observations.index[-1];state=observations.iloc[-1];rows=[]
    for horizon,entry in research['horizons'].items():
        row={'decision_time':time,'horizon_minutes':horizon,'status':'unavailable','contract':CONTRACT_VERSION}
        if entry['status']!='ready':row['reason']=entry.get('reason',entry['status'])
        elif not state.valid:row['reason']='Current measurement or warm-up is invalid.'
        elif time+pd.Timedelta(minutes=horizon)>panel.loc[time,'session_close']:row['reason']='Horizon extends beyond the current session.'
        else:
            p_ml=predict_head(entry['state_head'],x.loc[[time]],5)[0]
            p_state=entry['state_ml_weight']*p_ml+(1-entry['state_ml_weight'])*entry['transition'][int(state.state_id)]
            p_price=predict_head(entry['price_head'],x.loc[[time]],3)[0]
            experts,_,diag=path_experts(entry['bank'],x.loc[time],p_state,p_price)
            row.update(_forecast_summary(entry,experts,p_state,features.loc[time,'sigma_ticks'],diag))
            row.update(status='research_forecast',observed_state=STATE_NAMES[int(state.state_id)],
                flow_status='observed' if state.flow_available else 'unavailable',
                reference_status='observed' if state.reference_available else 'unavailable',
                data_status='complete_selected_features' if diag['observed_feature_fraction']==1 else 'partial_selected_features')
        rows.append(row)
    return pd.DataFrame(rows)


def matured_feedback(predictions,panel,features,cfg,as_of):
    """Only completed outcomes; no fitting or alteration of historical forecasts."""
    cutoff=pd.Timestamp(as_of)
    if cutoff.tzinfo is None:raise ValueError('Feedback cutoff must be timezone-aware.')
    p=panel.loc[panel.index<=cutoff];f=features.reindex(p.index);targets=make_targets(p,f,cfg);out=[]
    for row in predictions.to_dict('records'):
        time=pd.Timestamp(row['decision_time']);h=int(row['horizon_minutes'])
        if row.get('status','research_forecast')!='research_forecast' or time not in targets[h].index:continue
        target=targets[h].loc[time]
        if pd.isna(target.class_id) or target.target_end>cutoff:continue
        probs=np.array([row['p_down'],row['p_neutral'],row['p_up']])
        out.append({'decision_time':time,'horizon_minutes':h,'target_end':target.target_end,
                    'return_ticks':target.return_ticks,'log_loss':float(-np.log(max(probs[int(target.class_id)],1e-12)))})
    return pd.DataFrame(out)
