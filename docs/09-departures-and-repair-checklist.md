# Source fidelity, omissions and proposed repairs

Version note: this guide reviews the source framework and the earlier CGB baseline. The independent redesign that follows this review is derived and implemented in [document 10](10-structural-model-derivation.md). Source fidelity is a comparison tool, not a requirement to copy its numerical choices.

Review date: 2026-09-24. This is an inspection of the supplied source and the current CAD implementation, not a fitted-data study. No market dataset has been supplied and no empirical results were created. This review changes explanations and navigation; it does not silently replace the forecasting model.

Read [the intellectual story and complete source lesson map](08-the-intellectual-story-and-all-lessons.md) for the intuitions. Read [the mathematical walkthrough](07-understanding-the-framework.md) for derivations and examples. This document answers the narrower question: **what did we preserve, change, miss or need to repair?**

## 1. Verdict

We built a separate CGB baseline. We retained causal measurement, an explicit forecast horizon, optional environmental observations, uncertainty reporting and a distinction between prediction and execution. We replaced major components of Karim's architecture: the exposure-basket construction, GAS/FLUIDE blocks, 22-state grammar, structural transition mixture, state-label prediction, Monte Carlo state propagation and Born/Zurek fusion.

Those are consequential changes. They must be stated before describing the notebook as following his model. Several replacements are reasonable for the stated account objective, but reasonableness does not make them source-faithful.

The biggest conceptual omission is an observed bridge from **pressure and constraints to price response**. The existing model can learn persistence in price behavior. It cannot yet establish that a continuing reorganization of exposures is the mechanism behind that persistence.

## 2. How the review was performed

1. Re-read the six core authored PHYSICS essays and the later `09 ummo.md` formalization. Reviewed the opening/selected material from the remaining two PHYSICS files.
2. Enumerated all 38 CYBERNETICS files, including both files numbered 08. Reviewed abstract/opening material and selected discussion passages; used the earlier deeper readings for the eleven original lessons. A lesson map is not a claim to have checked every proof in every collected paper.
3. Revisited the detailed [original source audit](../audits/source-audit.md), which traces the six original notebooks by zero-based cell index and named function. The original notebooks were not executed.
4. Inspected the actual current feature configuration, measurement code, target construction, chronological split, model fit, pooling, diagnostics and execution ledger. Checked the notebook/package relationship separately in the evidence record.
5. Compared purpose, state vocabulary, equations, code paths and operational behavior. Distinguished a component that exists in code from a component enabled by default, and both from one validated on market data.
6. Parsed the new Markdown equations and checked local navigation. Those checks establish document syntax and file consistency, not financial correctness.

The [review evidence record](../audits/lesson-review-evidence.md) lists the inspected files and content hashes. No full-paper reading or link revalidation is claimed merely because a file was hashed. The prior 272-entry arXiv catalog is still a bibliography; this review did not freshly read 272 papers.

## 3. Checklist: conceptual objects and measurements

Status meanings: **present** means implemented; **partial** means a narrower implementation exists; **changed** means a deliberate substitution; **absent** means missing; **unverified** requires observations or an empirical comparison. None means demonstrated trading edge.

| ID | Question checked | Finding | Reasoned response |
|---|---|---|---|
| A01 | Is the traded object explicit? | Present: a specified CGB contract and future midpoint movement. | Keep outright duration, as requested. |
| A02 | Did we copy his basket/reference trade? | Changed: no inverse-volatility regime basket is traded. | Preserve this difference; use contextual references without silently hedging away the user's target. |
| A03 | Are exposure, statistical beta and physical forcing distinct? | Partial: documentation distinguishes them; no forcing estimate exists. | Keep units and roles separate in any added state model. |
| A04 | Does the default model use the full environment? | No: `feature_modules=('cgb',)` in `ResearchConfig`. | Clearly label the default baseline; activate other modules only with valid matched histories. |
| A05 | Do US common movement and Canadian deviation remain visible? | Present as optional features, using lagged covariance/variance estimates. | Keep both; add a reference-validity diagnostic rather than calling the residual purely local causation. |
| A06 | Are curve level and slope separated? | Present as optional 5y level, 2s5s and 5s10s changes. | Do not interpret flattening without the component yield changes. |
| A07 | Are related forwards treated as independent witnesses? | No explicit independence model exists; features can be redundant. | Record construction ancestry and examine incremental information by economic group. |
| A08 | Is the crowd exposure density estimated? | Absent. | Do not rename filtered drift as crowd positioning. Identify feasible proxies before a latent exposure model. |
| A09 | Are forcing, crowding and risk capacity separately estimated? | Absent. | Define competing observational implications; do not make three names for one return statistic. |
| A10 | Is full L2/order-flow processing present? | No: top-of-book size imbalance, microprice and a short average only. | A richer module needs event definitions, additions/cancellations/executions and data semantics. |
| A11 | Is absorption measured? | Absent: no executed-flow versus subsequent response/replenishment model. | Highest-priority conceptual addition when trade and book data support it. |
| A12 | Are failed recovery attempts represented as events? | No: VWAP distance and dispersion are present, not a recovery-event parser. | Define when an attempt begins, when failure becomes observable, and what response is retained. |
| A13 | Are event time and availability separated? | Present in the adapter. | Preserve this contract, including corrections and stale/invalid observations. |
| A14 | Are session/contract boundaries explicit? | Present; rolling state resets by segment. | Preserve causal boundaries; revisit reset choice if overnight state is intentionally introduced. |
| A15 | Is a live event calendar modeled? | Absent as a dedicated forecast module. Session timing alone is not event context. | Add known-in-advance event timing separately from realized surprises, with their actual availability. |

## 4. Checklist: state, probability and dynamics

| ID | Question checked | Finding | Reasoned response |
|---|---|---|---|
| B01 | GAS/FLUIDE interaction blocks? | Absent. | If added, define financial coupling/dispersion measurements; do not simply rename high/low volatility. |
| B02 | Eleven tags in two blocks? | Changed to seven price-description phases. | Compare a richer economically motivated grammar with the baseline; do not claim equivalence. |
| B03 | State grammar and permitted transitions? | Absent as a predictive structural grammar. | Specify emissions, transitions and exceptions explicitly before fitting. |
| B04 | Seven structural 22-state matrices? | Absent. The current seven-phase transition matrix is diagnostic only. | A structural model must actually enter forward probabilities to count as implemented. |
| B05 | Pointer-state stability? | Unverified. A persistent label is not sufficient. | Check meaningful perturbation stability and distinct future outcome behavior together. |
| B06 | State persistence duration? | Partial: lagged price features and filtered drift carry memory. | Consider state age/episode history only if it distinguishes future outcomes; no semi-Markov model currently exists. |
| B07 | Original Monte Carlo grammar propagation? | Changed to local Gaussian drift and optional path simulation. | Keep the baseline and label the new state-path model separately if developed. |
| B08 | Dynamics parameter uncertainty? | Partial: filtered state variance exists; fitted parameter uncertainty is not propagated. | Avoid presenting conditional filter variance as total model uncertainty. |
| B09 | Jumps and asymmetric tails? | Partial descriptive skew/semivolatility; Gaussian dynamics remain. | Characterize event/tail residuals before choosing a jump or heavy-tail extension. |
| B10 | Original hybrid EVT layer? | Absent; adverse-excursion quantile heads are a different object. | Explain this difference; do not estimate extreme tails from a few swap sessions. |
| B11 | Original Hurst/Lyapunov proxies? | Absent. | Do not import their standard scientific names without their actual definitions. |
| B12 | Future engineered-tag classifier? | Changed to actual future-price direction/mean/path heads. | Retain the economic target; a future-state auxiliary head is a possible separate addition. |
| B13 | Born/Zurek fusion? | Changed to calibrated log pooling. | Disclose the change. A source-faithful experiment would implement the active source path with documented repairs. |
| B14 | Independent evidence in the pool? | No: experts share inputs; code documents dependent forecasts. | Keep disagreement visible and calibrate the combined output. |
| B15 | One coherent endpoint/path distribution? | No: pooled classes, endpoint mean, adverse quantiles and dynamics simulations are separate outputs. | Do not interpret one as the moment or path sample of another. A joint distribution is a possible later design. |
| B16 | Conflict versus insufficient information? | Partial: data status and expert divergence exist. | Add mechanism-level supporting/opposing evidence if the measurements are defined. |
| B17 | Entropy rate or predictive memory? | No: reported entropy is over three forecast outcomes. | Do not call it thermodynamic entropy or sequence entropy rate. Add memory questions at the event level. |
| B18 | Automatic adaptation? | Absent: parameters freeze after training/calibration. | Separate filtering from refitting; any adaptive layer needs mature feedback and an explicit objective. |

## 5. Checklist: account purpose, evidence and operation

| ID | Question checked | Finding | Reasoned response |
|---|---|---|---|
| C01 | Are horizons explicit? | Present: 60, 120 and 240 minutes. | Keep the 1–4-hour interpretation provisional because the original reply was "1 and 4." |
| C02 | Does the label preserve path risk? | Present: endpoint plus long/short maximum adverse excursion. | Do not confuse a favorable endpoint with an easily held trade. |
| C03 | Does late-session forecasting roll overnight silently? | No: horizon eligibility respects session close. | Preserve the distinction between no valid horizon and no directional view. |
| C04 | Does warming up consume the target window? | Yes: chained rolling features consume session history. | Publish earliest usable decision time per enabled module; long horizons may have few or no eligible starts. |
| C05 | Can four swap sessions train the full configured model? | No under current coverage gates. | Keep short-history observations visible separately; do not invent a month of swap confirmation. |
| C06 | Are overlapping rows independent evidence? | No; equal-session weights do not remove dependence. | Interpret uncertainty at session/episode scale; one split is only an initial evaluation design. |
| C07 | Are train, calibration and test separated? | Present, with complete target paths and partition eligibility. | Preserve this when adding any state-learning or normalization stage. |
| C08 | Are simple forecasting baselines present? | Present: zero drift, training frequencies, past direction, dynamics and ML separately. | They diagnose what a richer mechanism adds; they are not arbitrary tests. |
| C09 | Are reported probabilities evaluated as probabilities? | Present: log loss, Brier and related reporting paths. | Actual calibration and coverage remain unverified until market data exist. |
| C10 | Do three-class probabilities describe magnitude fully? | No. | Keep expected movement and path information separate; a high directional probability can still imply little economic opportunity. |
| C11 | Are price bid/offer costs handled? | Present as optional futures touch benchmark and dirty-price bond ledger. | Spread is paid in prices. Do not subtract the same spread again as generic slippage. |
| C12 | Are fills, queue priority and size-dependent impact modeled? | Absent. | Do not report touch benchmarks as realized executable performance. |
| C13 | Can the cash-bond ledger substitute for a CGB exposure model? | No: no DV01, CTD/conversion-factor, basis, repo or hedge-ratio engine. | Add those only if comparing/choosing cash and futures exposures; the outright CGB predictor does not require pretending they are identical. |
| C14 | Is the model a controller? | No: no order policy or autonomous risk response. | Keep indicator output distinct from position and execution decisions. |
| C15 | Is deployment-induced market feedback estimated? | Absent. | Use price-taking as an explicit scope where appropriate; revisit at the size/policy stage. |
| C16 | Are monitoring failures attributed to their source? | Partial: input statuses exist; no complete causal monitoring map. | Distinguish feed failure, changed reference, forecast error, higher costs and a different account policy. |
| C17 | Has predictive edge been established? | Unverified; no market fit/backtest supplied. | Software checks and theoretical motivation cannot fill this gap. |

## 6. What I would repair first, and why

These are recommendations inferred from the framework and code, not claims that Karim personally requested them.

### Repair 1: make the observable pressure–response relation explicit

Keep three objects distinct: the action proxy, the market's response, and the conditions under which the response occurs. At event or short-window scale, a descriptive starting point is

![Mathematical expression](../assets/math/display-fc5c19755ad993f0ec02.svg)

![Mathematical expression](../assets/math/inline-a3f4ccef765873ecdd37.svg) must be defined: signed executed quantity is different from resting depth or message count. ![Mathematical expression](../assets/math/inline-e23ffc3ef9a94d8c63e6.svg) is an observational response coefficient unless a stronger causal design is supplied. Units must be stated. Dividing price changes by tiny flow is unstable; a regularized local relation or conditional bins can be preferable to a raw ratio.

Record bid replenishment, cancellation and the survival of recovered price levels when those observations exist. The discriminating question is whether repeated pressure still generates displacement. This directly addresses the user's trading intuition and the source's account of absorption.

The deciding evidence would be incremental future information beyond completed price movement and common duration. A strong contemporaneous association alone does not settle that question.

### Repair 2: expose validity of the reference

The current beta always supplies a projection when sufficient data exist. It does not decide whether the relationship remains economically interpretable. Add a record of freshness, recent residual distribution, reference stability and known event conditions. Avoid using a large residual both to declare the reference broken and to claim powerful local alpha without examining alternatives.

This is where the source's environment-first idea has practical force. A measurement can be numerically defined while its earlier interpretation no longer holds.

### Repair 3: represent formation, persistence and loss of response

Design the state vocabulary around distinguishable events. For example, sustained selling with preserved response and sustained selling with diminishing response should not necessarily share a state merely because both have negative trailing returns.

The state map must be causal. Labeling a recovery "failed" requires a criterion and an observable completion time. State age, number of attempts and changing response are possible measurements. They should not be calculated retrospectively from the final trend-day label.

The existing seven phases can remain a benchmark. A closer source translation would introduce separate environmental blocks and a genuine predictive transition layer. It would document whether a transition is impossible by construction or merely assigned a low prior probability.

### Repair 4: retain the original future-state question without losing the actual outcome

Use a future-state task only alongside actual future CGB movement. Predicting the future grammar can reveal useful transition structure. Predicting the actual price/path gives that structure an external economic check.

If those tasks disagree, investigate the representation instead of automatically forcing the price forecast to obey the tag. A state called persistent must earn that interpretation through future conditional behavior.

### Repair 5: give contradictory evidence its own explanation

A single indicator can hide several situations: weak evidence, strong conflicting evidence, missing data, a broken reference, or a robust neutral forecast. Retain the distinct inputs to that judgment. The later formalization's four-valued intuition is useful here as an evidence ledger, even though its speculative physical claims need not be adopted.

### Repair 6: define adaptation before switching it on

Specify what may change, at what clock, using which matured outcome. Keep a record of frozen predictions so later refitting does not rewrite what the model knew. Consider whether the feedback is forecast error, state-recognition error, execution error or account-level loss. These are different learning signals.

With only a few sessions, responding aggressively to each apparent failure can create the redundant-solution loop highlighted in the cybernetics collection. Repeatedly tuning on the same events is not new evidence.

## 7. Source details that should be corrected, not copied

Faithfulness means understanding the construction, including its errors and limits. The following points are traceable in the source and do not depend on disliking its philosophy.

| Source point | Issue | Correct handling |
|---|---|---|
| P05 reduced density matrix | The environmental overlap is equated to the full matrix element, dropping amplitude factors. | Write ![Mathematical expression](../assets/math/inline-6ee7b178a944a9f5a024.svg) with ![Mathematical expression](../assets/math/inline-fbeedb3700bae90001bd.svg). |
| P05 Gaussian expected shortfall | With ![Mathematical expression](../assets/math/inline-0bdc61b9600979078cef.svg) for a lower-tail return quantile, the printed denominator is inconsistent. | Lower-tail ![Mathematical expression](../assets/math/inline-cd5ff5998049138168f8.svg). State tail and loss/return convention explicitly. |
| P02/P03 free-energy decrease | The stated dissipation identity requires fixed landscape parameters and boundary assumptions. | Include explicit forcing/temperature-change terms when the functional depends on time. |
| P04 entropy/action comparison | Continuous differential entropy and ![Mathematical expression](../assets/math/inline-8e47e154ebcee0ab717f.svg) are not directly comparable. | Define a common discrete task representation or a properly justified information-theoretic condition. |
| P04/P05 probability philosophy | Ordinary Bayesian/conditional probability does not assume a static non-reflexive market. | Treat the contrast as a modeling motivation; classical state/action-dependent probability remains available. |
| P09 coupled expansion formulas | ![Mathematical expression](../assets/math/inline-9dee74ee6143790a1be5.svg) implies equal squares, contradicting negative squares except at zero for real values. | Repair the domain and equations; do not map a negative square to a bearish financial state. |
| Original Hurst/Lyapunov functions | Their names suggest estimators the functions do not implement. | Use the actual proxy definitions and avoid standard exponent interpretations. |
| Original independently calibrated tag/state outputs | Nonlinear temperature transforms need not preserve the tag marginal of the 22-state distribution. | Calibrate one joint distribution and derive its marginal coherently. |
| Original notebook 5 backtest timing | Cell 76 sizes an already realized close-to-close return with the current posterior; cell 146 passes it without the necessary shift. | Use forecasts available before the evaluated return and price execution at the chosen later entry time. |
| Original adaptive/governor labels | Some code paths change training weights; other named adaptation methods only record diagnostics. | Trace active effects rather than infer operation from a class or method name. |

The existing source audit records additional estimator, timing and calibration nuances. These are reasons to implement the underlying ideas carefully, not reasons to ignore their useful questions.

## 8. Cognitive checklist before calling the CGB model complete

- [ ] I can name the traded outcome without referring to a feature or a state label.
- [ ] I can explain why each contextual market belongs in the system.
- [ ] I can distinguish observed pressure, price response and an inferred motive.
- [ ] I know which modules are actually enabled and which have sufficient history.
- [ ] I can describe when the reference relationship should stop being trusted.
- [ ] I can explain each state through observations available at that moment.
- [ ] I know whether a probability forecasts a future tag, price direction or path event.
- [ ] I can identify what changed because of physics-inspired structure and what was introduced independently.
- [ ] I can distinguish missing evidence, conflicting evidence and a neutral forecast.
- [ ] I know which uncertainty is represented and which is omitted.
- [ ] I understand why a proposed comparison addresses a specific mechanism.
- [ ] I can show which simpler forecast the extra complexity improves upon.
- [ ] I can separate price prediction, execution costs and position policy.
- [ ] I know what feedback has matured and what is still in the future.
- [ ] I can state what observation would weaken the model's explanation.
- [ ] I have empirical evidence for the intended claim, rather than only working code and plausible theory.

These boxes remain open research acceptance criteria. Creating this document does not check them on behalf of data that do not yet exist.
