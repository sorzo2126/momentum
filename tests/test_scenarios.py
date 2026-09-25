"""Deterministic software exercises, not market data or investment performance."""
from pathlib import Path
from dataclasses import replace
import json,sys,tempfile,unittest,subprocess,os
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from momentum import ResearchConfig,prepare_panel,build_features,ScenarioConfig
from momentum.states import build_state_observations
from momentum.scenarios import (fit_scenario_research,predict_scenarios,matured_feedback,
    redistribute,transition_distribution,_forecast_summary,path_experts)
from momentum.deployment import save_deployment,load_deployment,save_live_reading,read_live_reading


def exercise_inputs(days=10):
    sessions=[];quotes=[];trades=[]
    for dayno,day in enumerate(pd.bdate_range('2025-01-02',periods=days,tz='UTC')):
        start=day+pd.Timedelta(hours=13)
        idx=pd.date_range(start,periods=481,freq='min');j=np.arange(len(idx));sign=(dayno%3)-1
        mid=110+sign*.002*j+.04*np.sin(j*2*np.pi/37)+.02*np.cos(j*2*np.pi/17)
        sessions.append({'session_id':str(day.date()),'open_time':start,'close_time':idx[-1]})
        quotes.append(pd.DataFrame({'instrument':'CGB','contract':'SOFTWARE_EXERCISE','event_time':idx,
                                    'available_at':idx,'bid':mid-.005,'ask':mid+.005,'bid_size':10.,'ask_size':12.}))
        trades.append(pd.DataFrame({'trade_id':[f'{dayno}-{i}' for i in j],'instrument':'CGB','contract':'SOFTWARE_EXERCISE',
            'event_time':idx,'available_at':idx,'price':mid,'size':10.,'aggressor':np.where(np.sin(j/7)>0,1,-1)}))
    return pd.concat(quotes,ignore_index=True),pd.DataFrame(sessions),pd.concat(trades,ignore_index=True)


class ScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=ResearchConfig(min_train_sessions=4,min_cal_sessions=2,min_test_sessions=2)
        cls.scfg=ScenarioConfig(trees=20,neighbor_count=24)
        cls.quotes,cls.sessions,cls.trades=exercise_inputs()
        cls.cutoff=cls.sessions.close_time.iloc[7]
        cls.panel=prepare_panel(cls.quotes,None,cls.sessions,cls.cfg,trades=cls.trades,as_of=cls.cutoff)
        cls.features=build_features(cls.panel,cls.cfg)
        cls.fit=fit_scenario_research(cls.panel,cls.features,cls.cfg,cls.scfg,cls.trades)

    def test_all_horizons_fit_and_are_coherent(self):
        self.assertEqual(self.fit['status'],'ready',{h:(e['status'],e.get('reason')) for h,e in self.fit['horizons'].items()})
        for h,entry in self.fit['horizons'].items():
            bank=entry['bank'];paths=bank['paths'];p=entry['test_predictions']
            self.assertTrue(np.allclose(entry['transition'].sum(1),1))
            self.assertAlmostEqual(entry['mixture_weights'].sum(),1)
            self.assertTrue(np.all(entry['mixture_weights']>=0))
            self.assertTrue(np.allclose(p[['p_down','p_neutral','p_up']].sum(1),1))
            self.assertTrue(np.allclose(paths[:,0],0))
            self.assertTrue(np.all(bank['mae_long']>=np.maximum(-bank['endpoint'],0)))
            self.assertTrue(np.all(bank['mae_short']>=np.maximum(bank['endpoint'],0)))
            self.assertTrue(set(pd.to_datetime(bank['train_times'])).issubset(set(self.fit['splits']['train'])))
            for times in entry['indices'].values():
                self.assertTrue((times+pd.Timedelta(minutes=h)).isin(self.panel.index).all())

    def test_state_and_flow_prefix_invariance(self):
        cutoff=self.sessions.open_time.iloc[1]+pd.Timedelta(minutes=187)
        panel=prepare_panel(self.quotes,None,self.sessions,self.cfg,trades=self.trades,as_of=cutoff)
        features=build_features(panel,self.cfg)
        earlier=build_state_observations(panel,features,self.cfg,self.scfg,self.trades)
        later=build_state_observations(self.panel,self.features,self.cfg,self.scfg,self.trades)
        assert_frame_equal(earlier,later.loc[earlier.index],check_exact=True)

    def test_missing_flow_is_not_zero_absorption(self):
        obs=build_state_observations(self.panel,self.features,self.cfg,self.scfg)
        self.assertFalse(obs.flow_available.any())
        self.assertTrue(obs.absorption.isna().all())

    def test_unclassified_or_delayed_flow_is_unavailable(self):
        tape=self.trades.copy();tape['aggressor']=0
        obs=build_state_observations(self.panel,self.features,self.cfg,self.scfg,tape)
        self.assertFalse(obs.flow_available.any())
        tape=self.trades.copy();tape['available_at']+=pd.Timedelta(seconds=45)
        obs=build_state_observations(self.panel,self.features,self.cfg,self.scfg,tape)
        self.assertFalse(obs.flow_available.any())

    def test_enabled_environment_cannot_silently_disappear(self):
        cfg=replace(self.cfg,feature_modules=('cgb','us','curve'))
        result=fit_scenario_research(self.panel,self.features,cfg,self.scfg,self.trades)
        self.assertEqual(result['status'],'no_eligible_horizons')
        self.assertTrue(all('coverage' in e['reason'] for e in result['horizons'].values()))

    def test_late_session_horizons_are_unavailable(self):
        now=self.sessions.close_time.iloc[8]-pd.Timedelta(minutes=30)
        p=prepare_panel(self.quotes,None,self.sessions,self.cfg,trades=self.trades,as_of=now)
        f=build_features(p,self.cfg)
        prediction=predict_scenarios(self.fit,p,f,self.trades)
        self.assertTrue(prediction.status.eq('unavailable').all())
        self.assertTrue(prediction.reason.str.contains('session').all())

    def test_transition_rows_shrink_to_observed_prior(self):
        result=transition_distribution([1,1,3],[1,2,3],np.ones(3),10.)
        self.assertTrue(np.allclose(result.sum(1),1))
        self.assertTrue(np.allclose(result[0],[0,1/3,1/3,1/3,0]))

    def test_probability_disintegration(self):
        p,unsupported=redistribute(np.array([.1,.2,.7]),[0,0,1],[.8,.2,0])
        self.assertTrue(np.allclose([p[:2].sum(),p[2]],[.8,.2]))
        self.assertEqual(unsupported,0)

    def test_scale_identity(self):
        entry=self.fit['horizons'][60];n=len(entry['bank']['classes'])
        experts=np.tile(np.ones(n)/n,(3,1));state=np.ones(5)/5
        a=_forecast_summary(entry,experts,state,1.,{})
        b=_forecast_summary(entry,experts,state,2.,{})
        for key in ('endpoint_mean_ticks','endpoint_q10_ticks','endpoint_q90_ticks','mae_long_q80_ticks','mae_short_q80_ticks'):
            self.assertAlmostEqual(b[key],2*a[key])
        self.assertEqual(a['p_up'],b['p_up'])

    def test_future_mutation_cannot_change_fit_or_calibration(self):
        quotes=self.quotes.copy();mask=quotes.available_at>self.fit['available_after']
        adjustment=.04*np.cos(np.arange(mask.sum())/5)
        for col in ('bid','ask'):quotes.loc[mask,col]+=adjustment
        p=prepare_panel(quotes,None,self.sessions,self.cfg,trades=self.trades,as_of=self.cutoff)
        f=build_features(p,self.cfg)
        other=fit_scenario_research(p,f,self.cfg,self.scfg,self.trades)
        self.assertEqual(other['input_fingerprint'],self.fit['input_fingerprint'])
        for h,a in self.fit['horizons'].items():
            b=other['horizons'][h]
            self.assertTrue(np.array_equal(a['bank']['paths'],b['bank']['paths']))
            self.assertTrue(np.allclose(a['mixture_weights'],b['mixture_weights'],atol=1e-12))
            self.assertAlmostEqual(a['state_ml_weight'],b['state_ml_weight'])
            for name in ('state_head','price_head'):
                if a[name]['model'] is not None:
                    self.assertEqual(a[name]['model'].get_booster().save_raw(),b[name]['model'].get_booster().save_raw())

    def test_frozen_deployment_feedback_and_tamper_detection(self):
        now=self.sessions.open_time.iloc[8]+pd.Timedelta(minutes=125)
        p=prepare_panel(self.quotes,None,self.sessions,self.cfg,trades=self.trades,as_of=now)
        f=build_features(p,self.cfg)
        expected=predict_scenarios(self.fit,p,f,self.trades)
        self.assertTrue(expected.status.eq('research_forecast').all())
        self.assertTrue(matured_feedback(expected,p,f,self.cfg,now).empty)
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)/'model';manifest=save_deployment(self.fit,directory)
            journal=pd.read_csv(directory/'state_journal.csv')
            self.assertLessEqual(pd.to_datetime(journal.decision_time,utc=True).max(),self.fit['available_after'])
            self.assertIn('60',json.loads((directory/'evaluation.json').read_text()))
            loaded=load_deployment(directory)
            actual=predict_scenarios(loaded,p,f,self.trades)
            assert_frame_equal(expected,actual,check_exact=True)
            live=Path(temp)/'live.json';save_live_reading(actual,loaded,live)
            self.assertEqual(read_live_reading(live)['run_id'],manifest['run_id'])
            with self.assertRaises(ValueError):save_live_reading(actual,loaded,live)
            pp=prepare_panel(self.quotes,None,self.sessions,self.cfg,trades=self.trades,as_of=now+pd.Timedelta(minutes=65))
            ff=build_features(pp,self.cfg)
            feedback=matured_feedback(actual,pp,ff,self.cfg,pp.index[-1])
            self.assertEqual(feedback.horizon_minutes.tolist(),[60])
            target=directory/'deployment.json';target.write_text(target.read_text()+' ')
            with self.assertRaises(ValueError):load_deployment(directory)

    def test_historical_revision_requires_new_fit(self):
        now=self.sessions.open_time.iloc[8]+pd.Timedelta(minutes=125)
        p=prepare_panel(self.quotes,None,self.sessions,self.cfg,trades=self.trades,as_of=now)
        f=build_features(p,self.cfg);p=p.copy();p.iloc[100,p.columns.get_loc('cgb_mid')]+=.01
        with self.assertRaises(ValueError):predict_scenarios(self.fit,p,f,self.trades)

    def test_no_data_is_explicit(self):
        self.assertEqual(fit_scenario_research(None,None,self.cfg,self.scfg)['status'],'awaiting_data')

    def test_cli_no_data_writes_no_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'model'
            run=subprocess.run([sys.executable,'-m','momentum.cli','train','--data',temp,
                '--as-of','2026-09-24T15:00:00Z','--output',str(output)],capture_output=True,text=True,
                env={**os.environ,'PYTHONPATH':str(ROOT/'src')},check=True)
            self.assertEqual(json.loads(run.stdout)['status'],'awaiting_data')
            self.assertFalse(output.exists())


if __name__=='__main__':unittest.main(verbosity=2)
