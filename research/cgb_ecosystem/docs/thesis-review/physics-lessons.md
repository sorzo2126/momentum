# Physics lessons translated into CGB research decisions

These are English analytical notes on all nine supplied PHYSICS Markdown documents. They distinguish the text's construction from the proposed CGB application. Line references refer to the source snapshot recorded in [coverage.json](coverage.json). All source text was read, including the long collected documents; full reading does not imply adopting every physical claim or importing every section into a financial model.

## P01 — 01 beta.md

**Source logic.** Lines 8–24 begin with the environment and actual constraints, then ask which exposure remains coherent under them. Lines 26–55 construct a neutral reference; lines 57–97 distinguish mean-reverting, carrying and convex compensation modes. Lines 101–117 describe alpha relative to a constraint-compatible reference.

**CGB translation.** The account has already selected outright Canadian duration. We should not quietly replace that with a CAD–US residual trade. The useful reference asks whether the current movement is common duration, local deviation or curve redistribution. Each may support the outright position for a different reason. The reference coefficient is an observation device with a validity domain.

**Question that changes the model.** What must remain stable for this relationship to remain informative, and which observable disturbance breaks that condition? A fixed beta can fail because sensitivity changes, a local shock arrives, timing changes or the instrument's delivery economics change. These require different responses.

**Current status.** Common and local coordinates exist. The next extension is a map of reference validity under controlled coupling, basis and timing changes, not compulsory hedging of the target.

## P02 — 02 smart beta.md

**Source logic.** Lines 12–24 place capital in a small exposure space. Lines 26–50 define an interaction-dependent Hamiltonian and stochastic movement; lines 64–98 associate different forms of allocation with forcing, agitation and interactions. Lines 115–149 describe crowding and changing dominant constraints; lines 157–161 connect adjustment to a free-energy derivative.

**CGB translation.** Define a distribution of participant exposures, not a distribution of arbitrary indicator values. An account can have a duration target, funding capacity and adjustment speed. Dealer capacity can change the route and timing of the same target adjustment. Population heterogeneity can matter even at equal aggregate flow.

**Question that changes the model.** Two tapes contain the same net selling. In one, nearly every seller is finished. In the other, a concentrated constrained population has barely begun. Which observation distinguishes the remaining stock of adjustment? A model of flow alone cannot answer by definition.

**Current status.** Persistent pressure and a random absorption switch are explicit simulator variables, but the population that would generate them is absent. E07 builds that population with instrument and cash accounting. The free-energy construction in the main report separates relaxation from continuing external forcing.

## P03 — 03 zureck.md

**Source logic.** Lines 32–42 use equilibrium as a conditional reference; lines 44–75 put the dominant constraint at the centre of the law. Lines 109–137 discuss hidden capital distributions and observable proxies. Lines 143–183 connect the cost landscape, crowding, agitation and reorganisation.

**CGB translation.** Ask what adjustment would remain if fresh shocks stopped now. That counterfactual separates unfinished inventory execution from a market that needs new information to continue. Then vary liquidity, leverage and funding constraints one at a time to see which changes the response law.

**Question that changes the model.** Is selling persistent because the forcing continues, because transmission is slow, because capacity is scarce, or because falling prices induce more selling? The same downward path can occur in all four cases. Forecasting may be possible without identifying the exact cause, but the causes imply different failure conditions.

**Current status.** The experiment includes continuation and liquidity stresses. It lacks a direct remaining-adjustment stock and a mechanism-conditioned observability comparison. E04, E05 and E07 supply those missing distinctions.

## P04 — 04 zureck vs laplace.md

**Source logic.** Lines 20–50 establish observation and subsequent action timing. Lines 32–40 describe constraints as thresholds; lines 56–90 discuss regime boundaries. Lines 110–142 concern reference coherence. Lines 146–168 introduce sequential evidence; lines 170–214 connect response capacity, accounting and the sources of an opportunity.

**CGB translation.** A boundary is where a previously adequate description becomes unreliable, not simply a large return. Useful boundary events include capacity exhaustion, a changed reference relationship, or an order-flow response that no longer resembles the previous regime. A sequential observer should accumulate genuinely new evidence and retain its delay.

**Question that changes the model.** Can the system identify a changed response before enough trading opportunity is lost, without repeatedly sounding alarms during normal variation? Repeated overlapping bars should not be treated as independent likelihood evidence. Use conditional innovations or an explicitly dependent sequential model.

**Current status.** Receiver-time causality and frozen evaluation are implemented. A live sequential boundary detector and a tested response/re-entry policy remain proposed. E15 evaluates their false alarms, delay and recovery, not just their number of interventions.

## P05 — 05 zureck vs laplace part 2.md

**Source logic.** Lines 12–50 build a coupled system/environment description and a stable pointer basis. Lines 56–70 discuss multiple environmental records. Lines 74–86 construct probabilities from amplitudes. Lines 92–122 return to reference and forcing; lines 138–183 concern local calibration and behaviour near boundaries.

**CGB translation.** Ask which state distinctions survive relevant disturbance and remain useful for future paths. Price direction alone can combine fundamentally different remaining-adjustment conditions. Likewise, several forwards from one curve can be multiple records of one measurement rather than independent evidence.

**Question that changes the model.** If a purported state mixes histories with very different future laws, should we change its coordinates or split it? If several witnesses agree only because the simulator gave them the same hidden driver and noise, how much confirmation survives an independent measurement channel?

**Current status.** The observer has five price-derived states and explicitly grouped features. E03 tests redundant versus independent evidence. E10 compares those states with continuous economic and predictive representations. Amplitude-based fusion is a possible composition, but its measurement inputs and calibration must be specified; there is no need to preserve a numerical transformation solely because the source uses it.

## P06 — 06 stationary time series.md

**Source logic.** Line 22 explicitly distinguishes stationary returns from stationary spread levels. Lines 24–58 discuss risk-weighted construction and alignment; lines 60–72 use stationarity diagnostics to examine a reference.

**CGB translation.** The traded price need not be stationary for an intraday momentum model. A conditional reference can nevertheless have a stable residual distribution within a valid environment. The question is which object is assumed stable: level, increment, scale, transition law or response relationship.

**Question that changes the model.** Does normalisation expose a stable relationship, or merely conceal a changing one? Compare residual behaviour when exposure sensitivities and coupling change. Preserve the unnormalised movement alongside the normalised coordinate.

**Current status.** Causal volatility estimates and reference residuals exist. E08 and E09 vary memory and coupling rather than presuming that one scaling choice solves both.

## P07 — 07 trou noir.md

**Source character.** This long French document collects an argument about gravitational models, coordinates, boundaries and alternative physical constructions. It contains repeated material and equations with extraction issues. It is not a single financial lesson, and its historical or cosmological claims need not become assumptions of the CGB system.

**Useful reasoning.** Lines 36–95 distinguish coordinate transformations and their domains. Lines 221–337 examine an interior boundary condition and critical pressure. Lines 578–748 and 2037–2167 discuss multiple branches and time coordinates. Lines 2651–2943 concern variational construction, integrals and topology. Lines 3379–3513 raise the problem of comparing observations against a restricted model family.

**CGB translation.** A chart of the system can fail without the economic system ceasing to exist. A yield coordinate, a futures price coordinate and a volatility-normalised coordinate can describe one event differently. A stale measurement, an invalid reference frame and a true capacity boundary must be distinguishable. Non-injective summaries can place different economic states at the same apparent coordinate.

**Question that changes the model.** Have we allowed only one explanation to compete, then congratulated it for fitting observations it was constructed to explain? Observable twins and held-out mechanism families are a direct answer. Can the model cross a boundary that the equations or accounting actually forbid? Inventory reconciliation and declared feasibility conditions are another answer.

**Current status.** The valuation layer supports coordinate-consistency checks. E05 and E11 test distinct hidden states, chart choice and perturbation sensitivity. Astronomical parameters, contested historical claims and mirrored-universe assertions are not used as financial inputs; their sections were read but have no derived role in this CGB design.

## P08 — 08 kinetic_theory_galaxies.md

**Source character.** This is a collected paper by Petit, D'Agostini and Monnet. Lines 20–103 start from a distributional construction and a field that must be consistent with it. Lines 127–175 introduce material transport and moment quantities. Lines 231–394 use an ellipsoidal distributional form; lines 398–521 apply symmetry and closure choices. Lines 541–563 explicitly defer the full numerical potential/density solution.

**CGB translation.** Mean transport and fluctuations around it are different objects. A duration repricing can have a persistent mean flow while residual noise differs sharply across curve and basis directions. A scalar volatility parameter may miss that anisotropy. More importantly, a chosen population distribution and a market response should be reconciled, not specified independently in ways that contradict one another.

**Question that changes the model.** If the simulator keeps only mean flow and covariance, do different populations with those same moments still produce different tail or continuation behaviour? That tests the closure, rather than simply assuming the retained moments are sufficient.

**Current status.** The present world uses pressure factors and scalar volatility/depth drivers. E07 can introduce a small heterogeneous population; E08 and E11 test whether extra moments or directional sensitivity improve the observer. Keep the distinction between a tractable ansatz, a solved self-consistent world and an empirically estimated population.

## P09 — 09 ummo.md

**Source character.** This formalisation ranges across paired structures, collective memory, probability, logic and speculative physical/biological material. It is not necessary to force every passage into a trading feature. The useful CGB applications below are explicitly our derived constructions.

**Useful reasoning.** Lines 21–68 introduce paired structures and coupling. Lines 171–213 and 287–311 discuss collective fields and memory. Lines 517–531 discuss structural transition roles. Lines 718–734 and 774–793 introduce a four-valued logical motif. Lines 839–923 describe a modulation rule as something whose form still needs determination.

**CGB translation.** Buying and selling pressures can coexist, and a conflict between information channels should remain visible. A four-part evidence status—support, opposition, both, neither—distinguishes contradictory observations from missing observations. A collective field can be implemented as a summary of interacting positions or signals, with declared feedback into future actions.

**Question that changes the model.** Does averaging contradictory observations erase a useful signal of local pressure or reference failure? Does a shared model population produce correlated errors or actual position overlap, and which one changes market response? Those are distinct mechanisms.

**Current status.** Missingness and expert disagreement have existing diagnostics. E14–E16 test specific feedback channels and crowding. The proposed evidence ledger extends those diagnostics without conflating unknown, balanced and contradictory. Sections on unrelated physical or biological constants have no justified role in the present financial construction.

## What the actual source notebook adds

The review also inspected the source model contract and targeted implementation cells in `5 algo fractal x.ipynb`; this is not a claim to have executed or exhaustively audited every notebook line in this pass.

Cell 81, `train_xgb_by_horizon`, uses direct future graph-tag heads for horizons one through five. Cell 145, `born_bayes_posterior_by_horizon`, combines structural rows, a remembered/current-state distribution, sequential leg or Monte Carlo projections, frontier factors, disagreement-dependent temperature and amplitude normalisation. Its late branches condition transition-state contributions differently from persistent states. Cell 102, `cyber_diagnose`, explicitly labels several Ashby outputs as diagnostics rather than action gates. The source contains both active computational factors and audit-only quantities; the comments and names are not enough to tell them apart.

Our CGB adaptation instead has a five-state price observer, an empirical transition prior, a future-state head, a direct price-class head and calibrated path-expert mixtures. At one hour, the price-conditioned expert wins the saved mixture. That makes direct component attribution essential. Source fidelity should mean preserving the questions—environment, observation, memory, transition, constraint, response—and deriving the CGB answers. It should not mean preserving a specific state count, coefficient, hardware requirement or mathematical decoration without a demonstrated role.
