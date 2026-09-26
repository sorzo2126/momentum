"""Versioned, hash-checked empirical-path artifacts. No pickle deserialization."""
from pathlib import Path
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib,json,uuid
import numpy as np
import pandas as pd
from .features import ResearchConfig
from .states import ScenarioConfig,CONTRACT_VERSION


def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _json(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def _config(values):
    values=values.copy()
    for field in ('horizons_minutes','momentum_windows','feature_modules'):
        if field in values:values[field]=tuple(values[field])
    return ResearchConfig(**values)


def save_deployment(research,directory):
    if research.get('status') not in ('ready','partial'):raise ValueError('No fitted model to save.')
    directory=Path(directory)
    if directory.exists() and any(directory.iterdir()):raise ValueError('Use an empty directory for an immutable deployment.')
    directory.mkdir(parents=True,exist_ok=True)
    run_id=str(uuid.uuid4())
    state_hash=research['observation_fingerprint']
    meta={'run_id':run_id,'code_contract_version':CONTRACT_VERSION,'state_series_hash':state_hash,
          'created_at':datetime.now(timezone.utc).isoformat(),'status':research['status'],
          'config':asdict(research['config']),'scenario_config':asdict(research['scenario_config']),
          'use_flow':research['use_flow'],'use_vwap':research['use_vwap'],'feature_columns':research['feature_columns'],
          'history_start':str(research['history_start']),'available_after':str(research['available_after']),
          'input_fingerprint':research['input_fingerprint'],'observation_fingerprint':state_hash,'horizons':{}}
    for horizon,entry in research['horizons'].items():
        item={'status':entry['status']}
        meta['horizons'][str(horizon)]=item
        if entry['status']!='ready':item['reason']=entry.get('reason','unavailable');continue
        bank=entry['bank'];arrays={k:v for k,v in bank.items() if isinstance(v,np.ndarray)}
        np.savez_compressed(directory/f'bank-{horizon}.npz',**arrays,transition=entry['transition'],mixture_weights=entry['mixture_weights'])
        item.update(bank={k:v for k,v in bank.items() if not isinstance(v,np.ndarray)},state_ml_weight=entry['state_ml_weight'],heads={})
        for name in ('state_head','price_head'):
            head=entry[name];detail={'classes':head['classes'].tolist(),'prior':head['prior'].tolist(),'file':None}
            if head['model'] is not None:
                detail['file']=f'{name}-{horizon}.json';head['model'].save_model(directory/detail['file'])
            item['heads'][name]=detail
    _json(directory/'deployment.json',meta)
    research['report'].to_csv(directory/'test_metrics.csv',index=False)
    research['observations'].loc[:research['available_after']].to_csv(directory/'state_journal.csv',index_label='decision_time')
    evaluation={}
    for horizon,entry in research['horizons'].items():
        if entry['status']!='ready':continue
        evaluation[str(horizon)]={'risk_metrics':entry['risk_metrics'],'experts':{}}
        for name,metrics in entry['metrics'].items():
            evaluation[str(horizon)]['experts'][name]={k:v for k,v in metrics.items() if not isinstance(v,pd.DataFrame)}
            for table in ('per_session','pointwise_losses','reliability'):
                metrics[table].to_csv(directory/f'{table}-{horizon}-{name}.csv',index=True)
        entry['test_predictions'].to_csv(directory/f'test-predictions-{horizon}.csv',index_label='decision_time')
    _json(directory/'evaluation.json',evaluation)
    import numpy,pandas,scipy,xgboost
    code_dir=Path(__file__).parent
    manifest={'run_id':run_id,'code_contract_version':CONTRACT_VERSION,'state_series_hash':state_hash,
              'dependencies':{p.__name__:p.__version__ for p in (numpy,pandas,scipy,xgboost)},
              'code_sha256':{p.name:_sha(p) for p in sorted(code_dir.glob('*.py'))},
              'files':{p.name:_sha(p) for p in sorted(directory.iterdir()) if p.is_file()}}
    _json(directory/'manifest.json',manifest)
    return manifest


def load_deployment(directory,verify_code=True):
    from xgboost import XGBClassifier
    directory=Path(directory).resolve();manifest=json.loads((directory/'manifest.json').read_text())
    if manifest['code_contract_version']!=CONTRACT_VERSION:raise ValueError('Unsupported code contract.')
    for name,digest in manifest['files'].items():
        target=(directory/name).resolve()
        if target.parent!=directory or not target.is_file() or _sha(target)!=digest:
            raise ValueError('Artifact integrity check failed: '+name)
    if verify_code:
        for name,digest in manifest['code_sha256'].items():
            target=Path(__file__).parent/name
            if not target.is_file() or _sha(target)!=digest:raise ValueError('Deployment code changed: '+name)
    meta=json.loads((directory/'deployment.json').read_text())
    for key in ('run_id','code_contract_version','state_series_hash'):
        if meta[key]!=manifest[key]:raise ValueError('Artifact lineage mismatch.')
    result={k:v for k,v in meta.items() if k not in ('config','scenario_config','horizons')}
    result.update(config=_config(meta['config']),scenario_config=ScenarioConfig(**meta['scenario_config']),
                  contract=CONTRACT_VERSION,horizons={})
    for name,item in meta['horizons'].items():
        horizon=int(name);entry={'status':item['status']};result['horizons'][horizon]=entry
        if item['status']!='ready':entry['reason']=item['reason'];continue
        with np.load(directory/f'bank-{horizon}.npz',allow_pickle=False) as archive:
            entry['bank']={**item['bank'],**{k:archive[k] for k in archive.files if k not in ('transition','mixture_weights')}}
            entry['transition']=archive['transition'];entry['mixture_weights']=archive['mixture_weights']
        entry['state_ml_weight']=item['state_ml_weight']
        for head_name,detail in item['heads'].items():
            model=None
            if detail['file']:
                target=(directory/detail['file']).resolve()
                if target.parent!=directory or detail['file'] not in manifest['files']:raise ValueError('Invalid head path.')
                model=XGBClassifier();model.load_model(target)
            entry[head_name]={'model':model,'classes':np.array(detail['classes'],dtype=int),'prior':np.array(detail['prior'])}
    return result


def save_live_reading(predictions,research,path):
    if 'run_id' not in research:raise ValueError('Load a saved deployment before publishing a reading.')
    records=json.loads(predictions.to_json(orient='records',date_format='iso'))
    payload={'run_id':research['run_id'],'code_contract_version':CONTRACT_VERSION,
             'state_series_hash':research['state_series_hash'],'execution_status':'indicator_only_no_orders',
             'predictions':records}
    path=Path(path)
    if path.exists():raise ValueError('Preserve historical predictions; choose a new output filename.')
    path.parent.mkdir(parents=True,exist_ok=True);_json(path,payload)
    return payload


def read_live_reading(path):
    """Read-only consumer: no state recalculation, training or market-data access."""
    payload=json.loads(Path(path).read_text(encoding='utf-8'))
    if payload.get('code_contract_version')!=CONTRACT_VERSION:raise ValueError('Unexpected live-reading contract.')
    return payload
