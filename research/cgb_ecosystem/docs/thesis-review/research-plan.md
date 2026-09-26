# Research plan before real data

This is a prospective plan written after examining the saved S0 experiment. None of the experiments below is represented as already run. The existing published simulations, fitted models and results remain the baseline. See the [review](REPORT.md) for the derivations and the lesson files for the source arguments.

The objective is to identify **which observable structure supports useful CGB continuation over one to four hours**, and how the answer changes with adjustment, liquidity, memory and information quality. The objective is not to maximise a synthetic profit number by making the world easier or repeatedly changing the decision rule.

## The experiment contract

Every new experiment records a question, a competing explanation, a controlled intervention, what remains fixed, the available observation set, an evaluation criterion, and the decision made from the result. Separate three namespaces: latent world state, received observations, and evaluation outcomes. Nothing in the first or third namespace enters the observer accidentally.

Keep TRAIN, CAL and TEST roles explicit. A new random seed of an unchanged mechanism tests sampling variability. A new parameter setting tests local robustness. A held-out generator family tests whether a construction transfers to a different mechanism. Report those three types separately.

Use common random numbers for paired interventions where the noise retains the same interpretation. Draw independent worlds for final replication. Average dependent forecast losses within sessions or world episodes before uncertainty calculations; thousands of overlapping forecast origins are not thousands of independent experiments. Rare transitions need enough independently generated episodes, not just many adjacent bars.

Select a primary criterion before the run. Keep probability loss, endpoint distribution scores, adverse-path scores and executable accounts visible separately. State a practically meaningful improvement threshold before any architecture selection. The threshold should reflect the intended use and uncertainty, not be chosen after looking at results. Keep a bounded candidate list and an untouched family-level evaluation set.

## Phase A — understand the existing result

### E01. Component attribution and the objective's blind spot

**Question:** Does structure improve direction, within-class path risk, or neither?

**Construction:** Compare the saved local, state-conditioned and price-conditioned experts. Reproduce the 60-minute supervised/mixture equality directly. In a new CAL-only comparison, fit endpoint-only and path-aware objectives to the same candidate distributions. Hold the generator, features, TEST observations and action rule fixed.

**Readouts:** Endpoint log loss and Brier score; continuous endpoint CRPS or interval score; long and short adverse-excursion pinball losses; selected first-passage probabilities; trading outcomes under one frozen adapter. Report each expert separately before its mixture.

**Decision:** If structural information helps only path risk, assign it that job. If it adds neither predictive nor decision value across the held-out comparisons, keep the smaller baseline. Do not force positive weights. An endpoint-only objective cannot identify differences that preserve endpoint-class masses.

### E02. Clock dependence and matched horizons

**Question:** Is the apparent one-hour advantage about adjustment dynamics, a repeatable event clock, or the subset of the session eligible for that horizon?

**Construction:** Compare a clock-only baseline, price-only baseline and full observer. Generate fixed, jittered and irregular event schedules, preserving event magnitudes and marginal counts. When an event is scheduled, provide only the schedule known at the decision time; when it is unscheduled, do not reveal its arrival. Compare 60/120/240-minute outcomes at the same eligible decision origins as well as on their original full samples.

**Readouts:** Paired predictive skill, event-relative performance, lead/lag of entries, matched-origin horizon comparisons, and activity by time of day.

**Decision:** Retain genuine schedule information as a named context channel. Revise any claim about persistent adjustment if most skill depends on a fixed simulator clock. A horizon difference that disappears on matched origins is an eligibility effect worth separating from memory.

### E03. Independent information versus alternate coordinates

**Question:** Which extra observations contribute independent information?

**Construction:** Add a deterministic duplicate, a noisy duplicate, and an independent measurement with matched marginal correlation. Split or merge redundant feature groups. Add independent CAD basis/funding and swap-curve innovations while retaining valuation consistency. Keep source identities visible.

**Readouts:** Conditional forecast improvement, sensitivity to group partition, effective scenario concentration, and probability changes caused purely by duplicated measurements.

**Decision:** If duplicating a witness creates a stronger belief without new information, repair the fusion or grouping rule. If a forward is useful solely as a coordinate transformation, keep it for that purpose without counting it as independent corroboration.

## Phase B — establish what can be known

### E04. Oracle, observation filter and learner

**Question:** Where is information lost?

**Construction:** Begin with a small state-space world whose conditional laws can be computed or closely approximated. Evaluate three tracks: hidden-state/DGP access; all causally received observations; and the actual compressed features with the deployed learner. Give the latter two identical timing rules. Validate a numerical oracle against an analytically tractable special case.

**Readouts:** Probability and path-loss gaps, uncertainty as an observation channel is removed, and achievable decision value at the same costs. Separate a known-DGP oracle from an oracle given future shocks; the latter is only a perfect-information ceiling, not a deployable forecasting benchmark.

**Decision:** An oracle advantage lost by the observation filter identifies a measurement problem. A filter advantage lost by the learner identifies a representation or estimation problem. No cost-adjusted opportunity even for the causal hidden-state oracle rejects that world's opportunity hypothesis for the stated use.

### E05. Observable twins

**Question:** Can the same opening selloff imply different futures, and when can we tell?

**Construction:** Create paired worlds with the same received history up to a declared decision time. Change only a hidden remaining-inventory stock, capacity limit or future forcing law after that common prefix. Include unfinished selling, completed repricing with temporary displacement, and curve/basis rotation. Use an exact equality audit on the common observation prefix.

**Readouts:** First time any received observation can distinguish the worlds; forecast divergence relative to that time; error before and after information arrives; value of a candidate extra measurement.

**Decision:** A forecast divergence before the common prefix ends indicates an information-boundary error. Persistent ambiguity after the split may justify a mixture of futures, a shorter holding window or a new observation requirement. It does not justify assigning a story with false certainty.

### E06. A strict traded-price martingale control

**Question:** Does the research pipeline invent apparent opportunity when none is available under its information set?

**Construction:** Generate the traded gains process as a martingale conditional on all admissible observations. Use bounded predictable positions and nonnegative explicit costs. If a full curve is reconstructed from the price, verify the martingale property survives the construction at the traded instrument; do not assume a martingale yield has a martingale price. Keep a separate predictable-world positive control.

**Readouts:** Mean net gains across independent worlds; confidence/calibration; false opportunity declarations; apparent benefits from adaptive selection; sensitivity to repeated candidate searches.

**Decision:** Repeated positive expected gains beyond simulation uncertainty require investigation of filtration, accounting, selection or generator semantics. Isolated profitable runs are expected. Passing this control does not require abstention at every origin.

## Phase C — generate the mechanism instead of prescribing its appearance

### E07. Inventory and capacity as causes

**Question:** Can unfinished constrained adjustment produce the continuation we intend to recognise?

**Construction:** Use a small population of target-adjusting accounts, constrained dealers and trend responders. Track instrument quantities, risk sensitivities, cash, fills and outside-sector transfers. Compare two populations with the same net initial order flow but different remaining inventories and capacity distributions. Reuse the existing curve/bond valuation layer.

**Readouts:** Inventory conservation, settlement/cash reconciliation, remaining target distance, capacity utilisation, price response per unit flow, and future continuation conditional on equal initial tape. Evaluate the observer without hidden inventory columns.

**Decision:** Keep population heterogeneity only if it creates an economically relevant distinction that aggregate pressure misses. If it generates a distinction no proposed observation can reveal in time, record that measurement gap rather than hiding it behind a larger model.

### E08. Memory, age and hysteresis

**Question:** Which memory must the observer retain?

**Construction:** Match one-step marginals and broad volatility while varying episode durations: exponential, bounded execution schedule, heavy-tailed renewal, interrupted execution and capacity-triggered reversal. Compare session resets with continuous overnight latent state. Include up-and-down sweeps of capacity to test path dependence. Preserve the existing age feature and ablate it explicitly.

Add separate equal-initial-pressure and equal-integrated-expected-pressure comparisons. The existing fast-decay stress moves the one-minute pressure coefficient from 0.985 to 0.65, shortening the half-life from 45.86 to 1.61 minutes and reducing the remaining expected contribution. An amplitude-adjusted duration comparison answers a different question; do not claim that all these controls preserve every marginal simultaneously.

**Readouts:** Skill by episode age; termination hazard; prediction improvement from older history beyond the current state; continuation versus excursion; different responses at the same instantaneous capacity reached by different paths.

**Decision:** Add memory only where held-out prediction improves. If instantaneous state is insufficient but age resolves the problem, prefer a semi-Markov extension over a large recurrent model. If histories remain indistinguishable to the observer, return to E04/E05.

### E09. Propagation versus measurement delay

**Question:** What does “US-led” actually mean in the simulated mechanism?

**Construction:** Independently vary economic CAD–US transmission delays, feed delays, common shocks and local disturbances. Include simultaneous common responses and genuine delayed transmission. Use a directed response kernel where required, rather than assuming every coupling derives from one potential.

**Readouts:** Identified lag versus true lag; predictive improvement after correcting receipt delays; false leader classification; CAD-local residual behaviour when the reference relationship changes.

**Decision:** Keep lead/lag claims only to the level the experiment distinguishes. A receiver-order effect should become a feed-quality finding. An economic delay should persist under corrected availability and be evaluated against a contemporaneous common-factor alternative.

## Phase D — earn the mathematical representation

### E10. Price states versus predictive states

**Question:** Are the current five states the distinctions the future needs?

**Construction:** Compare the current observer, continuous economic coordinates, and a small learned predictive partition using the same information. Test state counts and transition restrictions on TRAIN/CAL only. Hold out complete mechanism families. Examine rare changes separately from persistent regimes.

**Readouts:** Conditional future-law differences within each state; value of older history after conditioning on state; transition detection delay and false alarms; complexity, stability and prediction quality on unseen families.

**Decision:** Split a state when it hides a reproducible predictive distinction. Merge states that create names without decision-relevant differences. Keep unresolved mechanism uncertainty separate from balanced directional predictions.

### E11. Geometry of sensitivity

**Question:** Does a geometric description identify fragility beyond simple local response measurements?

**Construction:** Define a metric over risk-normalised economic states or conditional path distributions. Compare paired-perturbation response, a local Jacobian and coarse transition curvature. Change measurement units and duplicate derived coordinates without changing the economic world. Repeat around binding constraints and away from them.

**Readouts:** Forecast instability under small perturbations, detection of cascade-prone regions, invariance under legitimate coordinate changes, and out-of-family improvement beyond the simpler diagnostic.

**Decision:** Use geometry only for the role it improves: uncertainty, capacity, state partition or forecast. A coordinate-dependent artefact requires a metric repair. A simpler equally effective sensitivity diagnostic wins on interpretability and estimation burden.

### E12. A coherent future across horizons

**Question:** Can one path law serve the holding-window decision?

**Construction:** Compare the existing independent horizon banks with one shared-prefix path model. Score on matched decision origins and identical observation sets. Preserve late-session restrictions. Evaluate memory/continuation hazards where they generate paths, rather than forcing endpoint probabilities to be monotone.

**Readouts:** Endpoint and path scores at every horizon, joint first-passage events, adverse-excursion ordering, sample support, calibration and duration decisions under a frozen adapter.

**Decision:** Keep the joint model only if coherence and usable path estimates compensate for the loss of long-path sample support. If separate models remain preferable, publish their inconsistency diagnostics and avoid treating them as one joint scenario tree.

## Phase E — test decisions and feedback separately

### E13. Forecast quality versus decision quality

**Question:** Which errors matter for a duration account?

**Construction:** Keep marginal forecast error approximately matched while changing error persistence, clustering and alignment with turning points. Feed a frozen forecast into the current threshold adapter, a simple receding-horizon duration adapter and a flat comparator. Include identical trade-opportunity and exposure-matched summaries, while also reporting each policy's natural activity.

**Readouts:** Probability/path scores alongside net gains, adverse excursions, first-passage accuracy, turnover, time exposed and missed opportunities. Charge price spread once, then fees and additional slippage; keep missing fills and exits visible.

**Decision:** A policy improvement with unchanged forecasts is an action-adapter result. A forecast improvement that does not help the intended decision may still improve another product, but should not justify this adapter by itself.

### E14. Five separate feedback switches

**Question:** Which deployment loop destabilises or improves the system?

**Construction:** Independently enable selected fill labels, action-distorted observations, action-caused future liquidity, changed opportunity sets and model-generated training labels. Start with zero own market impact. Keep public shadow observations where available. Only test recursive synthetic training when that loop is deliberately enabled.

**Readouts:** Passive forecast quality, decision-system utility, observational support, rare-state retention, parameter drift and action drift. Keep untouched external generator lineages for evaluation of recursive training.

**Decision:** Repair the failing loop directly. Weighting selected samples is not a generic cure for a changed world; monitoring public outcomes is not enough when actions change those outcomes. A fixed point is not automatically low risk or high utility.

### E15. Bounded governor and recovery

**Question:** Can adaptation protect the account without oscillating or withdrawing permanently?

**Construction:** Use a small action set, delayed matured evidence, a cooldown and a defined re-entry rule. Compare frozen operation, monitoring without action and bounded intervention. Vary gain and feedback delay. Add feed failure and genuine economic change as separate causes of similar observed drift.

**Readouts:** False alarm rate under independent null worlds, detection delay, tail loss, false withdrawals, opportunity retained, switching costs, recovery time and whether the response addresses the actual cause.

**Decision:** Reject a controller whose apparent safety comes chiefly from ceasing activity or whose switching consumes the advantage. Increase adaptation complexity only after a simpler governor demonstrably fails a specified challenge.

### E16. Crowding and strategic response

**Question:** What changes when others share or respond to the signal?

**Construction:** Sweep crowd fraction, signal-error correlation, position overlap, impact strength and response costs. Include correlated models without correlated positions, common fundamentals without imitation, and heterogeneous controllers. Compare stale fallback behaviour with a continuously updated shadow baseline. Run increasing and decreasing crowding sweeps to expose hysteresis.

**Readouts:** Loop stability in action space, liquidity recovery, tail losses, crowd-induced continuation and reversal, impact-adjusted capacity, and performance under altered observable behaviour.

**Decision:** Preserve the zero-impact baseline and identify where it stops approximating the intended deployment. If the signal changes its own measurement channel, learn or bound that response before increasing capacity. Do not infer crowd behaviour from signal correlation alone.

## The space these experiments cover

The plan deliberately crosses the following axes: continued versus completed forcing; ample versus constrained capacity; memoryless versus age-dependent episodes; gradient versus directed coupling; local versus common disturbances; exact versus delayed observations; independent versus redundant witnesses; passive versus action-dependent environments; stable versus changing delivery/basis relationships; and fixed versus adaptive decision policies.

It is a structured set of discriminating cases, not a claim to enumerate every possible financial world. Expand it when an observed failure exposes a missing axis. Avoid expanding it merely because another technical method is available.

## What the next implementation should contain

Add a separate research version with a world interface, an observation interface, an evaluator with privileged truth access, and adapters for forecasters and policies. Every run should save its mechanism family, parameters, random streams, timing rules, world-state schema, received-data schema, model version, selection history and result status. Preserve S0 byte-for-byte as a reference.

The first delivery should implement E01–E06 with a tractable world before the inventory population becomes elaborate. Its output should be an attribution table, clock-dependence table, oracle-gap plot, observable-twin comparison, and martingale-control distribution. Those five results decide what complexity is justified next.

The resulting real-data specification should say what each field resolves: independent swap/basis observations, receipt timestamps, actual event-level order identities if lifecycle features are intended, traded cash-bond price quotes, futures contract/roll metadata, and enough sessions to observe the targeted transitions. Four swap sessions remain four swap sessions; synthetic history can develop a method but cannot turn them into a validated long-history observation channel.
