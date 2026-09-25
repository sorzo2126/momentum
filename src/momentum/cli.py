"""Train, forecast, and read frozen research artifacts using explicit local CSVs."""
from pathlib import Path
import argparse,json
import pandas as pd
from .features import prepare_panel,build_features,ResearchConfig
from .states import ScenarioConfig
from .scenarios import fit_scenario_research,predict_scenarios
from .deployment import _config,save_deployment,load_deployment,save_live_reading,read_live_reading


def _inputs(directory,cfg,as_of):
    directory=Path(directory)
    def read(name):
        p=directory/f'{name}.csv'
        return pd.read_csv(p) if p.exists() else None
    quotes,sessions=read('quotes'),read('sessions')
    if quotes is None or sessions is None:return None,None,None
    trades=read('trades')
    panel=prepare_panel(quotes,read('rates'),sessions,cfg,trades=trades,context=read('context'),as_of=pd.Timestamp(as_of))
    return panel,build_features(panel,cfg),trades


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    train=commands.add_parser('train');train.add_argument('--data',required=True);train.add_argument('--as-of',required=True)
    train.add_argument('--output',required=True);train.add_argument('--config')
    forecast=commands.add_parser('forecast');forecast.add_argument('--artifact',required=True);forecast.add_argument('--data',required=True)
    forecast.add_argument('--as-of',required=True);forecast.add_argument('--output',required=True)
    show=commands.add_parser('show');show.add_argument('file')
    args=parser.parse_args()
    if args.command=='show':print(json.dumps(read_live_reading(args.file),indent=2));return 0
    if args.command=='train':
        settings=json.loads(Path(args.config).read_text()) if args.config else {}
        cfg=_config(settings.get('research',{'feature_modules':['cgb','us','curve']}))
        scfg=ScenarioConfig(**settings.get('scenario',{}))
        panel,features,trades=_inputs(args.data,cfg,args.as_of)
        result=fit_scenario_research(panel,features,cfg,scfg,trades)
        if result['status'] not in ('ready','partial'):
            print(json.dumps({'status':result['status'],'reason':result.get('reason'),
                              'horizons':{h:{k:v for k,v in e.items() if k in ('status','reason','eligible_sessions')} for h,e in result['horizons'].items()}}))
            return 0 if result['status']=='awaiting_data' else 2
        manifest=save_deployment(result,args.output)
        print(json.dumps({'status':result['status'],'run_id':manifest['run_id'],'output':str(Path(args.output).resolve())}));return 0
    result=load_deployment(args.artifact)
    panel,features,trades=_inputs(args.data,result['config'],args.as_of)
    if panel is None:raise ValueError('Forecast requires real quote and session files.')
    predictions=predict_scenarios(result,panel,features,trades)
    payload=save_live_reading(predictions,result,args.output)
    print(json.dumps(payload,indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
