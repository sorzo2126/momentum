# Deployment, feedback, and duration: a source-grounded research review

Read-only review, 26 September 2026. Assigned corpus: the 12 Markdown files at zero-based sorted CYBERNETICS indices 26–37, confirmed by filename. This report translates their mechanisms into experiments for the CGB synthetic duration research. It does not certify their proofs, reproduce their results, or infer the private intentions of their authors or the repository owner. Any proposed connection to the owner's architecture is a reconstruction.

The named authors below are the source-paper authors, not the author of the CGB implementation. “Current” refers to `C:/Users/mn262/OneDrive/Desktop/momentum/research/cgb_ecosystem`. All line references refer to the provided Markdown/code, not PDF page numbers. Full-text reading includes the appendices present in these Markdown files; external supplements and figure pixels were not inspected. OCR/layout loss, particularly equations, prevents treating this as verification of mathematical transcription.

## Main finding

The current model is a useful experiment on inference from a finite bank of synthetic paths. It is not yet an experiment on the market's response to deployment. That distinction creates an unusually clean research opportunity: retain the present action-independent world as a control, then add mechanisms one at a time. Stronger language about feedback should follow those interventions.

The most valuable next question is: **does the model estimate the lifetime of a tradable opportunity, or merely its direction at a chosen endpoint?** The three base runs select essentially pure supervised direction weights at 60 minutes. Local weighting still determines paths within a class, including adverse-excursion estimates; it has not disappeared from the model. This means endpoint classification can be successful while the path geometry used for sizing, waiting, and exiting is weak. The fast-decay stress already supplies a useful counterexample: modest improvement over the direction-frequency baseline coexists with a losing trade book.

This is a constructive use of mathematical objects. A scenario measure can mean probabilities over admissible future paths; a projection can mean the map from those paths to a duration decision; a governor can mean a bounded controller over size, thresholds, or adaptation rate. Each object earns its role by an observable intervention and a decision criterion. Whether it resembles its original physical setting is secondary to whether its operational meaning is coherent and useful here.

## What was cross-checked in CGB

The [report](<../../REPORT.md>), [hypotheses](<../hypotheses.md>), [structured simulation](<../../simulation/structured_simulation.py>), and [scenario model](<../../model_snapshot/momentum/scenarios.py>) were read in full. Other implementation files were not independently audited by this reviewer. Reported checks were inspected as claims; no simulation or test suite was rerun.

The report describes 11 runs: three base, three pressure-removal controls, one CGB-only fit, and four stress replays. Each world has 40 sessions split 24 TRAIN / 8 CAL / 8 TEST; the horizons are **60, 120, and 240 minutes**. Three base seeds are useful replication within one generator family, not broad replication across possible market mechanisms. Overlapping forecasts do not create independent episodes. Session bootstraps over eight TEST sessions should remain descriptive (REPORT §§15–17, lines 321–447).

The generator pre-draws innovations and has no action or strategy argument; prices are generated before model fitting. Current “impact” is an exogenous displacement state driven by synthetic flow, and the ledger adds execution costs without feeding actions back into prices (`structured_simulation.py` lines 43–161, 249–317, 354–402). Therefore the current evidence concerns a passive price taker. Pressure removal is not a strict martingale null: other mean reversion, nonlinear pricing, carry, and rounding remain (REPORT §5, lines 90–118).

The model's split discipline, frozen stress replay, explicit missingness, and distinction between accounting identities and economic realism are strengths. The saved path distribution produces direction, endpoints, and MAE coherently for each horizon. However, separate horizon models do not define a joint 60/120/240-minute process; finite stored paths cannot generate an unseen tail. Effective scenario count is not a count of independent market episodes (REPORT §§13–14 and 20, lines 250–313, 616–630).

At 60 minutes the reported mixture puts all weight on the supervised expert in all three base runs (REPORT lines 276–295). In code, `path_experts` builds local weights first and redistributes class/state mass over those local conditional weights (`scenarios.py` lines 61–122); `_forecast_summary` then uses the same resulting path weights for class probabilities and MAE (lines 253–267). A zero mixture coefficient on the local expert is consequently not proof that local geometry adds nothing. CAL currently selects direction log loss, not path calibration or decision value. A separate test of within-class path weighting is essential.

The trade rule is explicit and reviewable, but its forecast and execution clocks differ: a 60-minute forecast enters next minute and exits at the original maturity, giving approximately 59 minutes of exposure. Feed-gap handling is candid: unavailable forecasts and incomplete pricing are retained, while last-price marks during a gap can understate intra-gap risk (REPORT §18, lines 449–461; `structured_simulation.py` lines 249–351). These are experimental dimensions, not cosmetic details.

## Twelve paper-to-experiment translations

### 26. FAIRNESS FEEDBACK LOOPS: TRAINING ON SYNTHETIC DATA AMPLIFIES BIAS

Anonymous authors in the provided ICLR submission. [Source](coverage.md#c27). Mechanisms: §2.1, lines 106–146; §3, lines 169–261; §4, lines 262–335 and 469–583; Appendix G, lines 1582–1596 and 1727–1734.

The paper separates contamination through model-generated training examples from changes in who remains represented. Sequential classifiers and sequential generators can lose minority support through different channels. Improving a metric relative to the preceding generation can conceal worsening performance relative to the original population. Resampling does not universally repair the problem, particularly when rare examples inherit wrong labels.

The present CGB generator is fixed and independently specified: it is not recursively trained on its own forecasts, so this paper does not demonstrate collapse in the present experiment. Its useful warning concerns a future research loop in which successful generated scenarios, inferred regimes, or traded observations become the training distribution.

**Experiment:** run a generation chain with four isolated mechanisms: independent fresh data; classifier pseudolabels only; generator replacement only; and policy-selected observations. Hold a frozen evaluation bank from the original world and a second bank containing rare reversals. Vary fresh-data fraction and rare-event replenishment. Record path-support loss, rare-state calibration, first-passage error, and conditional net utility against both the original bank and each preceding generation.

**Decision rule:** claim a feedback-specific degradation only if the recursive arm deteriorates relative to equal-size independent retraining, with uncertainty assessed across complete chains. A fair alternative is ordinary finite-sample tail loss or model approximation error. Market regimes are not demographic groups; transferring the support-loss mechanism does not transfer the paper's fairness conclusions.

### 27. Practical Performative Policy Learning with Strategic Agents

Qianyi Chen, Ying Chen, and Bo Li. [Source](coverage.md#c28). Functional-policy mechanism: introduction, lines 65–95; §2.1–2.2, lines 260–339; §3.2–3.3, lines 385–534; assumptions/guarantees, §4–5, lines 535–775.

The central move is to model how agents respond to the deployed policy's output, rather than requiring response to every internal parameter. The gradient includes both the direct policy effect and the distribution's response. This is attractive for a complex forecasting system with a small external interface. But its own-output response assumption explicitly excludes interference between agents, and the text identifies an intermediate response mapping that cannot always be identified.

CGB has a natural low-dimensional interface: signed size, participation rate, displayed aggressiveness, or a governor's risk allowance. It currently has no samples from a policy-induced response map, so adding a “performative gradient” to today's generated data would give it an unidentified meaning.

**Experiment:** add bounded randomized TRAIN probes of signed participation around a frozen forecast. First let response depend only on that output; then introduce crowd participation and latent inventory. Estimate a response Jacobian using observable state and announced actions. Separate the data used to fit response from the data used to choose the controller; evaluate on held-out action magnitudes and crowd regimes.

**Decision rule:** require response prediction and policy ranking to transfer within a declared action-support region, and require uncertainty or abstention outside it. Test both direct reward and induced future-state effects. A competing explanation is that the policy merely tracks latent pressure: random probes, rather than observational regressions alone, distinguish that case. Historical-gradient momentum also deserves a response-delay test because a stale gradient may point the wrong way after the crowd changes.

### 28. From Tea Leaves to System Maps: A Survey and Framework on Context-aware Machine Learning Monitoring

Joran Leest, Claudia Raibulet, Patricia Lago, and Ilias Gerostathopoulos. [Source](coverage.md#c29). Diagnosis/impact distinction: §II, lines 202–312; C-SAR framework: §V, lines 825–1009; confounding: §VI, lines 2053–2072; limitations: §VII, lines 2445–2488.

Identical measured drift can arise from a changed world, a broken data path, or the system's own interventions. The framework maps monitored systems, aspects, and representations; it is a descriptive organizing framework, not demonstrated evidence that a particular monitor improves outcomes. The distinction between detecting change, identifying its cause, and deciding its practical impact is especially relevant here.

CGB already records useful symptoms: data availability, entropy, expert disagreement, nearest-scenario distances, and effective scenario count. These do not yet identify causes or calibrate a halt decision. High confidence may coexist with an incorrect clock or a new response mechanism.

**Experiment:** construct matched worlds with nearly identical feature-drift statistics but different causes: delayed packets, genuine latent-pressure decay, contract/basis changes, own impact, and synchronized crowd trading. Give the monitor only information available at the decision time. Let it output a cause distribution, uncertainty, and a bounded action such as reduce size, wait, or reinitialize a measurement.

**Decision rule:** evaluate cause discrimination, unnecessary halts, time to useful recovery, and risk-adjusted utility against a simple missing-data rule and a generic drift threshold. Include pairs deliberately observationally indistinguishable; correct behavior there is uncertainty. A competing explanation is recognition of artificial injection fingerprints. Match timings, marginal magnitudes, and missingness patterns, and hide generator labels from the monitor.

### 29. Order-Flow Filtration and Directional Association with Short-Horizon Returns

Aditya Nittur Anantha, Shashi Jain, and Prithwish Maiti. [Source](coverage.md#c30). Diagnostic scope: lines 87–120; full-lifetime filters: §3.1–3.2, lines 266–329; association analysis: §3.4, lines 384–428; window alignment: §5, lines 668–677, and appendix, lines 999–1000; limitations: §7, lines 859–887.

This paper tests whether filtering order-flow records changes directional association. It is explicitly diagnostic, and some filters use full order lifetime, eventual modification counts, or the last modifications before exit. Those are legitimate retrospective descriptions but unavailable for a live decision about an order still resting. The displayed forward/backward window descriptions also require careful reconstruction before any predictive reuse; the text alone does not establish one unambiguous executable chronology.

CGB's event/arrival separation is a strength. Its synthetic tape, however, has aggregate trades rather than order lifetimes, cancellation messages, queue position, and modification histories. It cannot yet test the paper's main filtration mechanism.

**Experiment:** generate an order-message layer with event, arrival, decision, submission, fill, and outcome-maturity timestamps. Compare a retrospective lifetime oracle, causal age-so-far filtering, observed cancellation/modification filtering, and intensity-matched random thinning. Recompute every feature on packets actually received, including reordering and delayed arrival.

**Decision rule:** any claimed filtration benefit must survive causal construction and equal-information or equal-intensity controls, improve out-of-family decision utility, and beat simple aggregation at matched latency. An apparent benefit may instead arise from fewer noisy messages, overlapping feature/return windows, or a common latent driver. This is an excellent deliberate “cheating oracle versus deployable filter” test because the size of the gap is itself informative.

### 30. Performative Market Making

Charalampos Kleitsikas, Stefanos Leonardos, and Carmine Ventre. [Source](coverage.md#c31). Model: §3.1–3.3, lines 235–359; endogenous martingale mechanism: §4, lines 396–615; inventory control: §5, lines 616–877; open multi-agent convergence question: §7, lines 1026–1035.

The price responds toward a strategic reference. In a restricted directional-belief world, performative stability can make the reference coincide with the current price and eliminate predictable drift. Inventory motives produce a different equilibrium structure and potentially exploitable effects from other makers. Existence of a fixed point does not establish convergence of repeated deployment; the paper leaves important multi-agent convergence questions open.

The provocative CGB hypothesis is that **a successful signal can erase the opportunity it describes**. A falling out-of-sample edge after deployment may therefore be a consequence of effective coordination, not necessarily forecast deterioration. Conversely, predicting inventory-driven drift is different from predicting fundamental information.

**Experiment:** construct four worlds with matched volatility, depth, and transaction costs: strict observable-filtration martingale; exogenous information drift; crowd inventory/reference feedback; own-action feedback. Cross these with informed and uninformed maker populations. Perturb controller gain or initial inventory and measure return toward an equilibrium, oscillation, and basin dependence.

**Decision rule:** attribute value separately to fundamental information, inventory compensation, and impact externalities using simulator interventions. Do not infer a stable closed loop from a fixed-point equation. Competing explanations are an implanted drift or privileged access to simulated inventory. Those channels must be hidden or ablated. The scope of the paper's martingale result is a model-specific mechanism, not a universal explanation of market efficiency.

### 31. Nonlinear Performative Prediction

Guangzheng Zhong, Yang Liu, and Jiming Liu. [Source](coverage.md#c32). Sensitivity and contraction: §2.2–2.4, lines 222–619; adaptive regularization: §2.5, lines 620–704; neural parameter similarity: §3.1.3, lines 764–825; stability/accuracy tradeoff: §3.4, lines 1217–1221; stateful extension left open: lines 1233–1236.

The paper relates response sensitivity, regularization strength, and contraction of repeated optimization. Its task-specific sensitivity measure is a useful alternative to treating every distributional change as equally relevant. The theoretical conditions are specific; an observed local sensitivity estimate is not a global certificate, and raw neural-parameter cosine similarity can miss rescaling or representation symmetries.

The operational reconstruction for CGB is a governor with a measurable gain. Its output could change allocation, threshold, or adaptation speed while the official forecast remains fixed. Today there is no policy-to-market response loop with which to measure that gain.

**Experiment:** sweep governor adaptation rate, response delay, and latent-state persistence. Estimate local responses with paired step and impulse probes. Compare fixed, slower, regularized, and gain-adaptive controllers, with identical feasible exposure bounds. Observe action trajectories, response Jacobians, recovery times, oscillation amplitude, and utility.

**Decision rule:** require stability with a nontrivial utility/exposure floor and a confidence bound on local response gain in the tested region; explicitly report failed regions and delay sensitivity. A zero-action controller is trivially quiet and should not win the research question by definition. A second alternative is a metric artifact: stable parameters need not mean stable actions, and stable average actions can conceal alternating extreme positions. Judge the behavior in economically meaningful coordinates.

### 32. Robust Reinforcement Learning in Finance: Modeling Market Impact with Elliptic Uncertainty Sets

Shaocong Ma and Heng Huang. [Source](coverage.md#c33). Uncertainty geometry and robust Bellman formulation: §3, lines 194–487; finance evaluation: §4, lines 495–569; environment: Appendix C.3, lines 2428–2451; limitations: Appendix D, lines 2491–2501; toy transition construction: Appendix E.3, lines 2621–2715.

The proposed uncertainty sets encode directional structure that a symmetric uncertainty set may discard. The benefit is meaningful only when the true response is covered. In the finance environment, much of the market history is action independent and impact is represented through execution prices; the paper itself notes omitted reactions by other traders. That is a narrower intervention than an endogenous market simulation.

CGB currently stresses slippage through one or four extra ticks and uses synthetic depth. This is a good reproducible starting point, but it does not expose size-, direction-, and state-dependent uncertainty or capacity limits.

**Experiment:** fit uncertainty sets for execution cost conditional on signed size, participation, depth, delay, and volatility. Compare symmetric and directional sets at matched empirical coverage and comparable volume. Evaluate both a cost-only historical replay and a separate dynamic-response world. Include deliberately misspecified shocks outside the chosen geometry.

**Decision rule:** report worst conditional net utility, tail-cost coverage, attainable capacity, and activity-adjusted results. Require an advantage over simple shrinkage at matched exposure. A competing explanation is merely trading less. Also distinguish transition uncertainty from execution-cost uncertainty: improving robustness to the latter does not demonstrate robustness to crowding or feedback. The supplied mathematical extraction has layout loss, so no proof certification is implied.

### 33. Dissecting Performative Prediction: A Comprehensive Survey

Thomas Kehrenberg, Javier Sanguino Bautiste, Jose A. Lozano, and Novi Quadrianto. [Source](coverage.md#c34). Stability versus optimality: §2.2, lines 189–245; deployment/equilibration clocks: §2.4, lines 336–469; stateful maps: §2.5, lines 470–524; delayed cohorts: §3.2.4, lines 795–821; access/identification: §3.3, lines 833–987; calibration versus risk: §6.2.4, lines 1803–1815.

This survey supplies the most useful experimental taxonomy. A policy can be best for the distribution it currently induces without being the policy that induces the best distribution. Repeated retraining can operate on a faster clock than the world equilibrates. Simulation access ranges from expensive deployment samples through cheap black-box sampling to full structural knowledge, and results depend strongly on that privilege.

CGB's frozen TRAIN/CAL/TEST protocol cleanly measures passive inference. A performative extension should preserve that baseline and explicitly declare what the learner knows about the generator. Merely having the simulator source available to the researcher can create an unfair oracle if hidden parameters enter controller design.

**Experiment:** construct observationally equivalent worlds under the baseline policy with opposite responses to larger participation. Run an oracle controller, a black-box learner with a fixed probe budget, and a no-probe learner. Hold out whole response families, not just random seeds. Separately vary response memory and delayed participant cohorts.

**Decision rule:** measure response-map error, policy-ranking error, regret against the appropriate oracle, and abstention outside identified support. A learner with no action diversity should acknowledge nonidentifiability in the equivalent-world pair. If the oracle also fails, the issue may be optimization or the objective rather than information. Perfect endpoint calibration cannot by itself certify a good deployment policy.

### 34. The Stability of Online Algorithms in Performative Prediction

Gabriele Farina and Juan Carlos Perdomo. [Source](coverage.md#c35). Definitions and cycles: §2, lines 254–341; no-regret mixture result: §3, lines 382–450; algorithms: §4, lines 481–644; limitations: §5, lines 655–671.

The paper obtains a stability result for a randomized mixture over online iterates under its bounded-loss and sampling conditions. It does not show that the final iterate is stable, that averaging neural parameters is equivalent, or that every stable policy has low performative risk. Stateful and multiplayer settings remain material limitations for market transfer.

The productive CGB interpretation is to keep a finite library of bounded governor policies and adapt a distribution over that library using only matured feedback. This would be a controller experiment, not a new claim about the Born/posterior interpretation of predictive weights.

**Experiment:** compare last-policy deployment, deterministic averaging of policy outputs, and randomized selection of historical policies once per independent episode. Feed online updates only outcomes whose horizons have matured. Repeat with delayed/stateful crowd response to expose the boundary of the theorem's assumptions.

**Decision rule:** report external regret, counterfactual policy performance, controller oscillations, tail exposure, and recovery after regime shifts at matched mean exposure. The theory concerns a particular mixture and expectation; evaluate those quantities explicitly. A competing explanation is risk reduction through random size shrinkage or averaging that masks adverse episode-level behavior. Stable average loss is not a controller safety certificate.

### 35. Realistic Market Impact Modeling for Reinforcement Learning Trading Environments

Lucas Riera Abbade and Anna Helena Reali Costa. [Source](coverage.md#c36). Impact models: §II, lines 125–190; environment/reward: §III, lines 205–271; empirical design: §IV, lines 279–308; results: §V, lines 331–457; limitations: §VI, lines 458–481.

Changing impact and transaction-cost models changes learned trading behavior and algorithm rankings. The important mechanism is not simply subtracting a larger fee: a policy trained with a cost reacts to it. Reduced-form square-root impact, temporary/permanent impact, and transient resilience embody different assumptions about schedule and state.

CGB's explicit ledger supports a clean first comparison, but one-contract independent books cannot establish a scalable strategy's capacity. Costs, execution delay, participation, and opportunity decay should be examined jointly. A policy that waits to reduce impact may lose the signal before it trades.

**Experiment:** cross cost kernel, capital scale, participation cap, execution delay, and whether the policy was trained with that cost. First keep the market path fixed to isolate accounting and behavioral effects; then activate dynamic impact in a separate arm. Include zero-signal round trips and repeated buy/sell cycles to detect a simulator that rewards mechanical price manipulation.

**Decision rule:** compare complete utility-capacity curves and matched-turnover policies, including drawdown and tail cost. Freeze selection before the final evaluation. The source's wording about per-epoch out-of-sample objectives needs care: it should not be copied as permission to select on the final test. A ranking reversal can be driven by different activity, not improved forecasting.

### 36. Artificial Intelligence and Systemic Risk: A Unified Model of Performative Prediction, Algorithmic Herding, and Cognitive Dependency in Financial Markets

Shuchen Meng and Xupeng Chen. [Source](coverage.md#c37). Coupled mechanisms: §3.1–3.4, lines 326–564; dependency: §3.6, lines 818–906; hysteresis: §3.7, lines 911–997; time-scale/identification cautions: §4, lines 1123–1197 and 1490–1506; ABM interventions: §5, lines 1507–1648; limitations: §8, lines 1873–1894. External appendices are explicitly referenced at lines 2045–2046 but absent from the provided Markdown.

The model couples correlated forecasts, price feedback, and deteriorating independent fallback capability. Its interesting implication is a system that looks increasingly competent during calm periods while becoming less able to recover from a common error. Speed limits can even worsen tails in some modeled liquidity regimes. These are hypotheses to test, not universal regulatory conclusions.

For CGB, “cognitive dependency” can receive a precise software meaning: a fallback estimator that receives less refresh data as reliance on the primary model rises. No claim about human psychology is needed. Correlated model error must also be separated from legitimate common exposure to fundamentals.

**Experiment:** populate the world with CGB replicas. Factor crowd fraction, error correlation, own/crowd impact, leverage, and fallback-refresh rate. Sweep adoption upward and downward, then inject an unannounced forecast outage. Compare refreshed shadow estimators with stale fallbacks; test staggered updates and speed limits on both sides of a liquidity transition.

**Decision rule:** measure amplification, recovery time, tail concentration, and hysteresis loop area under matched capital and average exposure. Knock out fallback decay while preserving inventory/liquidity memory: persistent hysteresis would support an alternative mechanism. The text's depth/impact notation is internally awkward in places, so implement explicit units and measured responses rather than copying a dimensionless gain uncritically. Proofs delegated to missing appendices were not read or certified.

### 37. Plan Before You Trade: Inference-Time Optimization for RL Trading Agents

Eun Go, Rohan Deb, and Arindam Banerjee. [Source](coverage.md#c38). Price-taker setting: §2, lines 147–171; forecast-controlled optimization: §3, lines 173–335; reward: lines 336–363; experiments: §4, lines 378–502; normalization: Appendix B, lines 774–775; ablations: Appendix E, lines 1024–1047; limitations: Appendix F, lines 1096–1101.

The paper separates a frozen forecaster from inference-time action optimization over imagined futures. Its controlled oracle interpolation makes forecast quality adjustable, but contains future truth and is a diagnostic device rather than a deployable forecaster. Equal average forecast error need not imply equal action value; error timing and path structure matter.

This is the closest transfer to the current CGB architecture. Its weighted paths could support a small receding-horizon duration planner without adding an RL agent or changing the official predictive distribution. Compare a fixed holding horizon, a causal replanner, a simple bounded action-sequence optimizer, and a forecast-free policy at matched exposure.

**Experiment:** preserve endpoint MAE or directional log loss while changing error persistence, turning-point timing, and tail dependence. Evaluate cost-recovery time, first adverse-barrier passage, useful holding time, and net utility. Compare frozen local conditional path weights with uniform-within-class weights and true conditional paths used only as an oracle. Estimate noise from CAL residuals with temporal dependence rather than assuming forecast-value variance is forecast-error variance.

**Decision rule:** require planner gains beyond simple threshold tuning, allocation changes, and exposure differences. Two implementation lessons need explicit falsification: the described cached future states and detached terminal critic make that bootstrap term constant with respect to the actor update, so turning it off should not change that gradient; independently normalizing on the full validation/test period, if implemented literally as the appendix says, would use future statistics and must be replaced with causal normalization. These observations narrow the transferable mechanism rather than dismissing the planning idea.

## A concrete research sequence before real data

Every stage should freeze its intervention definitions and selection rule before its final evaluation. Retain the present 11 runs as exploratory provenance, then use new complete sessions, new seeds, and held-out generator families. Evaluate uncertainty at the level of independent worlds or sessions, not individual overlapping forecasts. Keep all outcome-based adaptation behind a maturity gate. A useful universal artifact is an immutable row recording the information set, forecast version, chosen action, arrival clock, fill assumptions, outcome maturity, and any later update.

| Stage | Intervention and control | Primary observable and pass/fail interpretation |
|---|---|---|
| 1. Duration meaning | Match endpoint classes while changing decay, reversal time, and intra-path tails. Compare local conditional, uniform conditional, shuffled-time, and oracle path weights. | Direction and endpoint calibration alongside first-passage/MAE calibration and cost-recovery survival. If endpoint scores stay fixed while duration utility collapses, the model needs decision-relevant path validation. |
| 2. Honest clock | Event/arrival jitter, reordering, publication delays, stale packets, and delayed fills; retrospective versus causal flow filters. | Benefit after causal construction and matched thinning. Every forecast must be reproducible from the available prefix. A gain confined to lifetime-oracle filtering fails the deployability test. |
| 3. Strict null and source attribution | Observable-filtration martingale, exogenous drift, crowd inventory feedback, own impact; match volatility and cost scales. | Positive-cost bounded trading should have no positive expected gain in the strict martingale world. Report simulation uncertainty and search-adjusted false discoveries; identify which intervention creates any edge. |
| 4. Response identification | Randomized bounded participation probes; observationally equivalent response worlds; oracle versus budgeted learner. | Response coverage and correct policy ranking on unseen actions/families. No-probe identification in indistinguishable worlds should fail honestly. |
| 5. Capacity and planning | Cost kernel × participation × delay × opportunity half-life, with frozen and cost-trained policies. | Utility-capacity frontier, tail-cost coverage, and duration opportunity lost while executing. Gains must survive matched turnover and exposure. |
| 6. Governor stability | Gain × delay × persistence, with fixed, slow, regularized, adaptive-gain, and randomized-library governors. | Recovery and oscillation at a nonzero utility floor; distinguish local empirical stability from a global theorem. |
| 7. Crowded success and failure | Replica adoption × common error × feedback × fallback refresh; upward/downward sweeps and outages. | Edge erosion, synchronized tail exposure, hysteresis, and recovery. Separate rational common signals, error correlation, leverage, and fallback decay by knockout interventions. |

Stage 1 should come first. It needs the smallest extension and addresses a live ambiguity in the current evidence. For each long/short action define, on each stored path, a cost-recovery time, an adverse-barrier time, and a remaining-opportunity event. The model can report the weighted probability that recovery occurs before the adverse barrier and before a proposed exit. Thresholds and costs must be fixed using TRAIN/CAL. Compare that rule with the present endpoint threshold under the same fills and risk budget. These are operational definitions of duration; they do not require borrowing a physical interpretation.

A particularly demanding variant is a **matched-endpoint adversary**: two synthetic families with the same terminal direction distribution and similar endpoint losses, one giving a smooth recoverable move and the other giving a large adverse excursion before recovery. If the path bank cannot distinguish them from available information, it should widen uncertainty or abstain; it should not be credited with identifying duration merely because its endpoint score remains good.

A second demanding variant is **success-induced edge extinction**: increase deployment by identical well-calibrated models until their collective trading moves the price earlier. The useful duration can shrink even as a delayed-horizon directional forecast stays calibrated. A correct controller should recognize that forecast quality and executable opportunity have separated. A naive “more confidence means more size” governor may worsen precisely when the prediction looks strongest.

A third is **benign-drift versus dangerous-confidence twins**: match a conventional drift statistic across a harmless rescaling and a hidden feedback increase. A monitor that halts both indiscriminately is conservative but diagnostically weak. A monitor that never halts because entropy is low is exposed to common-error amplification. Test its decision value and its honest inability to distinguish certain twins.

## Architectural interpretation and limits

The source repository's `0.1 AGENTS.md`, `0 README_MODEL.md`, `0.2 README_THESES.md`, `requirements.txt`, and relevant `agents` guidance were read. The review follows the separate thesis-reading and constructive-critique roles requested by the parent. It does not import the source project's daily horizons or hardware requirements into CGB's minute-horizon experiment.

One compatible reconstruction of the owner's architecture is: structural objects define useful state or path constraints; the supervised head supplies likelihood-related information; the official posterior produces predictions; a separate governor adjusts bounded behavior and records its interventions. This reconstruction should be tested through ablations and auditable interfaces. Governor weights must not quietly become a second untracked predictive selector. Likewise, a randomized controller mixture from paper 34 is not automatically the same object as a mixture over forecast scenarios.

The ambitious thesis worth testing is that **one probability measure over paths can support coherent direction, adverse-excursion, and opportunity-duration decisions, while a separate bounded controller preserves useful behavior when information and deployment response change**. The current experiment establishes pieces of the first clause under a deliberately favorable synthetic structure. It has not yet established cross-horizon coherence, decision-relevant path calibration, identifiable deployment response, or governor stability. The experiments above turn each missing claim into a tractable synthetic question.

## Full-text coverage ledger

All ranges below are inclusive and were read sequentially: 12 files and 21,599 physical newline-delimited lines. References follow PowerShell `Get-Content`; embedded OCR form-feed characters are not extra lines. Python `splitlines()` would produce different counts for papers 27, 31, 33, and 36; the JSON records both conventions. Reading is not proof certification. A small initial output truncation in paper 26 was repaired by rereading lines 239–245. No other assigned-paper range remains unread. Paper 36's separately hosted online appendices are outside the provided file and remain unread.

| Index / file prefix | Line count | Read chunks | Repair / limitation |
|---|---:|---|---|
| 26 Fairness_Feedback_Loops_OpenReview | 2506 | 1–600; 601–1100; 1101–1800; 1801–2506 | 239–245 reread after a small output truncation |
| 27 Practical_Performative_Policy_Learning_Strategic_Agents | 2138 | 1–350; 351–700; 701–1050; 1051–1400; 1401–1775; 1776–2138 | Provided appendices included |
| 28 From_Tea_Leaves_to_System_Maps_ML_Monitoring | 3371 | 1–400; 401–850; 851–1250; 1251–1700; 1701–2150; 2151–2550; 2551–2925; 2926–3371 | Provided appendices included |
| 29 Order_Flow_Filtration_Directional_Association | 1191 | 1–350; 351–750; 751–1191 | Provided appendix included |
| 30 Performative_Market_Making | 1497 | 1–375; 376–750; 751–1150; 1151–1497 | Provided appendices included |
| 31 Nonlinear_Performative_Prediction | 1386 | 1–450; 451–850; 851–1386 | Entire provided text |
| 32 Robust_RL_in_Finance_Market_Impact | 2716 | 1–450; 451–850; 851–1300; 1301–1800; 1801–2250; 2251–2716 | Provided appendices/checklist included |
| 33 Dissecting_Performative_Prediction_Survey | 2278 | 1–400; 401–800; 801–1200; 1201–1600; 1601–2000; 2001–2278 | Entire provided text |
| 34 Stability_Online_Algorithms_Performative_Prediction | 787 | 1–420; 421–787 | Entire provided text |
| 35 Realistic_Market_Impact_RL_Trading_Environments | 580 | 1–330; 331–580 | Entire provided text |
| 36 AI_Systemic_Risk_Financial_Markets | 2047 | 1–400; 401–800; 801–1200; 1201–1630; 1631–2047 | External Online Appendices A–G not present/read |
| 37 FinPILOT_Inference_Time_Optimization_RL_Trading | 1102 | 1–380; 381–760; 761–1102 | Provided appendices included |

The companion `deployment-coverage.json` records exact source paths, byte hashes, counts, ranges, and scope. For CGB cross-checking, REPORT.md lines 1–726 were read in full, with lines 177–650 reread after a large initial output truncation; hypotheses.md lines 1–79, structured_simulation.py lines 1–411, and scenarios.py lines 1–315 were read in full. Embedded report image/SVG contents and external supplements were not independently inspected. No existing source file was modified.
