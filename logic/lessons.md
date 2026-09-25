# English study notes: from cybernetics and physics to a CAD momentum model

These are independent explanatory study notes for learning and model construction. Authorship of the six PHYSICS essays is recorded in [the source provenance](README.md). The CYBERNETICS papers retain their own authors, credited below. The financial examples and proposed CGB interpretations are our research extensions.

The central question is practical: given the information available now, what distinguishes duration pressure that will continue over the next one, two, or four hours from repricing that has largely finished? The traded object is outright CGB. Canadian rates, US duration, forward rates, trades, and liquidity help describe its environment. They do not automatically determine the answer.

Each lesson connects an idea to mathematics, then asks what we can actually observe, what the code implements, and what remains a hypothesis. References to the original implementation use zero-based notebook cells. The new CAD code is a separate research implementation, not a replication of every original mechanism.

## Source provenance and reading map

| Key | Exact original filename | Authorship and sections consulted |
|---|---|---|
| P1 | `PHYSICS/01 beta.md` | Entire essay, including the opening reference-frame argument and A–C: cointegration, imbalance carry, convexity. |
| P2 | `PHYSICS/02 smart beta.md` | Entire essay: exposure coordinates, crowd density, penalty landscape, regime changes, adaptation interpretation. |
| P3 | `PHYSICS/03 zureck.md` | Entire essay: effective laws, hidden crowd density, observable proxies, interaction kernel, free-energy interpretation. |
| P4 | `PHYSICS/04 zureck vs laplace.md` | Entire essay, especially information timing, quadrant interpretation, sequential test, variety, decision, and benchmark. |
| P5 | `PHYSICS/05 zureck vs laplace part 2.md` | Entire essay: decoherence/pointer-state analogy, Born probabilities, spread reference frame, local Gaussian risk and EVT. |
| P6 | `PHYSICS/06 stationary time series.md` | Entire essay: return baskets, accumulated levels, hedge ratio, ADF/KPSS distinction. |
| C1 | `CYBERNETICS/01 thermodynamics_requisite_variety.md` | Alexander B. Boyd, Dibyendu Mandal, James P. Crutchfield, *Leveraging Environmental Correlations: The Thermodynamics of Requisite Variety*. Abstract; section II, equations 1–3; memory-matching result and section IV opening, extracted pages 3–4 and 10. |
| C3 | `CYBERNETICS/03 multiscale_requisite_variety.md` | Alexander F. Siegenfeld and Yaneer Bar-Yam, *A Formal Definition of Scale-dependent Complexity and the Multi-scale Law of Requisite Variety*. Abstract; matching definitions 1–3, complexity-profile definitions 4–6, section 4.2/Theorem 1, pages 4–6 and 9. |
| C4 | `CYBERNETICS/04 observer_into_system.md` | Chris Fields, *Building the Observer into the System: Toward a Realistic Description of Human Interaction with the World*. Abstract; section 2.2 black-box definition, pages 6–7; observer dependence and surprise, pages 12–13. |
| C5 | `CYBERNETICS/05 adaptation_control_complex_systems.md` | Olivier Del Fabbro and Patrik Christen, *Philosophy-Guided Modelling and Implementation of Adaptation and Control in Complex Systems*. System metamodel and section 3 adaptation formalism, pages 3–4; section 6.2.3 and opening 6.3, page 10. |
| C18 | `CYBERNETICS/18 Performative_Prediction.md` | Juan C. Perdomo, Tijana Zrnic, Celestine Mendler-Dünner, Moritz Hardt, *Performative Prediction*. Sections 2.1–2.2, definitions 2.1/2.3, repeated risk minimization and Theorem 3.5, pages 5–9. |
| C29 | `CYBERNETICS/29 Order_Flow_Filtration_Directional_Association.md` | Aditya Nittur Anantha, Shashi Jain, Prithwish Maiti, *Order-Flow Filtration and Directional Association with Short-Horizon Returns*. Abstract/introduction; section 2 definitions, section 3 lifetime/modification filters, pages 3–6; discussion, page 15. |
| C30 | `CYBERNETICS/30 Performative_Market_Making.md` | Charalampos Kleitsikas, Stefanos Leonardos, Carmine Ventre, *Performative Market Making*. Section 3 price process, optimality and stability, pages 5–7; section 7 conclusions, page 18. |

The PHYSICS originals are already written in English. The purpose of these notes is to unpack their claims and their relation to the code, rather than present a translation as new authorship.

## Lesson 1 — Choose the reference frame before choosing the signal

**Lesson.** P1 asks what exposure and environment give a signal meaning. A bond-futures decline can be a broad duration selloff, a Canadian-specific adjustment, or a mixture. The reference frame determines which of those questions we can ask.

**Mathematics.** For a measured CGB move $r_t^C$ and a US-duration move $r_t^U$, a descriptive decomposition is

$$
r_t^C=\beta_t r_t^U+e_t,
\qquad
\beta_t=\frac{\widehat{\operatorname{Cov}}_{t-1}(r^C,r^U)}{\widehat{\operatorname{Var}}_{t-1}(r^U)}.
$$

If CGB is measured in ticks and US movement in log basis points, beta has units of CGB ticks per US log basis point. Keeping units explicit prevents a dimensionless-looking number from becoming misleading. This beta is a local statistical projection, not an identified causal transmission coefficient.

**Market interpretation and observations.** A negative common component with a negative local component means CGB is falling alongside US duration and underperforming that local reference. A negative common component with a positive residual means local resilience during a broad selloff. Neither guarantees the next direction. We observe prices and their timing; we infer the reference relationship from past paired changes.

**Code and unresolved question.** Original notebook 3 separates return residuals from accumulated level spreads. The CAD `us` feature module similarly keeps `common_ticks_1` and `local_ticks_1`. It leaves the traded exposure outright. The question to test is whether either component's persistence improves the next CGB forecast, not whether a residual looks mathematically elegant.

**Questions to ask.** Which movement do I intend to trade? Does the reference relationship remain useful after announcements? Am I measuring simultaneous co-movement, delayed transmission, or both? What observation would make me reject the current reference?

## Lesson 2 — A stationary representation is a measurement choice, not a trading edge

**Lesson.** P6 makes an essential distinction: stationary returns do not imply a stationary price relationship. Equally, subtracting a rolling mean does not prove that the resulting deviation will reverse.

**Mathematics.** Let two basket log-return series accumulate into levels:

$$
L_t^+=\sum_{u\le t}R_u^+,
\qquad L_t^-=\sum_{u\le t}R_u^-.
$$

A constant-coefficient level spread is $S_t=L_t^+-kL_t^-$. Cointegration asks whether a suitable combination of nonstationary levels is stationary. ADF starts with a unit-root null; KPSS starts with a stationarity null, under their respective specifications. Agreement is evidence conditional on sample and assumptions, not a guarantee of profitable convergence.

With a changing $k_t$, even the increment contains an extra term:

$$
\Delta S_t=R_t^+-k_tR_t^--(k_t-k_{t-1})L_{t-1}^-.
$$

That last term is a change in the representation. It is not automatically money earned by a held portfolio.

**Market interpretation and code.** For intraday duration momentum, stationarity is not the objective. We want a stable enough description to distinguish continuing pressure from a completed adjustment. Original notebook 3 centers a level spread and adds stationarity/cointegration diagnostics; it does not thereby establish mean-reversion profits. The CAD model uses observable changes and does not require CGB itself to be stationary.

**Questions to ask.** Is my target a return, a price level, or a deviation? If I change the hedge estimate, how much of the apparent move comes from redefinition? Would an economically identical market receive a different state label merely because the normalization changed?

## Lesson 3 — Your information set is part of the model

**Lesson.** C4 describes an observer who has access to finite input-output records, not the interior of the whole system. P4's decision timing makes this operational: an action must use information available before the resulting outcome. A correct timestamp is therefore part of the mathematics.

**Mathematics.** Let $a_i$ be when observation version $i$ became available. The usable information is

$$
\mathcal F_t=\sigma\{x_i:a_i\le t\}.
$$

A feature $X_t$ must be measurable with respect to $\mathcal F_t$. A forecast $p_t$ may depend on $X_t$; a future target $Y_{t,h}$ may not enter it. Event time and availability time differ when updates arrive late or historical observations are revised.

**Market interpretation.** A swap quote timestamped 10:00 but received at 10:03 cannot explain a decision made at 10:01. A stale quote does not mean that rate pressure is zero. A corrected old observation must not rewrite what a past decision knew. Likewise, market depth shows displayed willingness at a location and instant, not all hidden interest or all dealer inventory.

**Code and unresolved question.** The CAD snapshot adapter tracks `event_time` and `available_at`, retains invalid newest observations rather than silently returning to an older valid one, and uses explicit sessions and contracts. Its value depends on honest upstream timestamps and feed semantics. It cannot reconstruct information that the vendor never retained.

**Questions to ask.** What could the receiver know then? Is a missing value unknown, stale, or truly zero? Are bid and ask atomic snapshots? Can I append later observations without changing previously available features? Where does my observation boundary hide important activity?

## Lesson 4 — Entropy measures uncertainty under a description, not tradability

**Lesson.** C1 distinguishes single-symbol entropy from entropy rate. A sequence can contain equal numbers of up and down signs while being highly predictable in order. P4's comparison with three trading actions is an intuition that needs additional definitions before becoming a rule.

**Mathematics.** For discrete $Z$, using natural logarithms,

$$
H(Z)=-\sum_zp(z)\log p(z),
\qquad
h=\lim_{n\to\infty}H(Z_n\mid Z_{1:n-1}).
$$

For a stationary process, $h\le H(Z_1)$. A random initial sign followed by exact alternation has marginal entropy $\log 2$ but entropy rate zero. Independent fair signs have both equal to $\log 2$. Counting signs alone misses the distinction.

C1 derives a physical work bound for its finite information-ratchet setting, using entropy rates in bits:

$$
\langle W\rangle\le k_BT\log 2\,(h_{\rm out}-h_{\rm in}).
$$

This is not a bound on trading PnL. It depends on a thermodynamic engine, reservoir, and work definition absent from a financial return series.

**Market interpretation and observability.** Memory can help when temporal structure exists. More memory is not automatically better. Discrete entropy depends on the selected categories. Differential entropy of continuous returns changes under rescaling: $h(aX)=h(X)+\log|a|$. It cannot be compared directly with the discrete action bound $\log 3$.

**Code and unresolved question.** Original notebook 2 constructs a body/tail differential-entropy estimate; notebook 5 constructs separate discretized variety. The CAD indicator reports entropy of its three predicted outcome probabilities. That measures model uncertainty over those outcomes, not a proof that the market is controllable or safe to trade.

**Questions to ask.** Entropy of what variable, in what units and bins? Is order information being discarded? Does lower entropy correspond to reliable predictions, or merely excessive confidence?

## Lesson 5 — Match the model to the scale of the decision

**Lesson.** C3's requisite-variety result concerns distinctions requiring different responses. A regulator does not need to reproduce every microscopic detail. It must distinguish the environmental situations that matter for its task, at the relevant scales.

**Mathematics.** In a simplified matching condition, environmental states $Y$ requiring distinct responses must be distinguishable through system states $X$:

$$
H(Y\mid X)=0\quad\Longrightarrow\quad H(X)\ge H(Y).
$$

The paper strengthens this with appropriately corresponding partitions and complexity profiles across scales. These are necessary matching conditions, not sufficient conditions for choosing the correct response. The theorem's scale is a coarse-graining structure; interpreting it as time horizon in markets is an extension, not a literal restatement.

**Market interpretation.** Millisecond queue changes, five-minute pressure, and a four-hour duration move are related but distinct objects. A microprice imbalance may be useful for immediate execution while adding little to a four-hour direction forecast. A slow macro constraint may define the background without timing the next five minutes.

**Code and unresolved question.** The original pipeline uses multiple windows but mostly daily conventions. The CAD notebook expresses feature windows and targets in explicit minutes and keeps the one-, two-, and four-hour targets separate. This makes scale choices visible; it does not validate them. Thousands of overlapping minute rows still may represent only a few independent market episodes.

**Questions to ask.** Which distinctions would actually change the forecast? Is a detailed state useful at this horizon? Does a faster input arrive early enough to matter? Am I adding informative resolution or simply adding fitted parameters?

## Lesson 6 — Hidden pressure is a hypothesis; filtered drift is an estimate

**Lesson.** P2–P3 describe crowd exposure as a hidden density $\rho(w,t)$ inferred through proxies. The valuable move is acknowledging partial observation. The dangerous move is relabeling a convenient price statistic as if it directly measured everyone's positioning.

**Mathematics.** A general state-space description separates hidden state and observation:

$$
z_{t+1}=f(z_t)+\eta_{t+1},
\qquad x_t=g(z_t)+\epsilon_t.
$$

The CAD dynamics expert uses the narrower model

$$
d_{t+1}=\phi d_t+\eta_{t+1},
\qquad r_t=d_t+\epsilon_t,
$$

with Gaussian noises of variances $Q$ and $R$. Here $d_t$ is latent local drift in ticks per grid step. Given filtered mean $m_t$, the expected next-$n$-step cumulative move is $m_t\sum_{j=1}^n\phi^j$. No claim about dealer inventory follows from that equation.

**Market interpretation and observability.** Negative drift may summarize persistent price pressure. The same observed path could result from aggressive selling, bids withdrawing, common macro information, or a combination. Identifying a cause requires observations that distinguish those explanations. High offer depth alone cannot determine whether it represents resilient supply or a transient quote.

**Code and unresolved question.** Original Hurst and Lyapunov functions are engineered shock-memory and propagation proxies, not conventional estimators of those named exponents. The CAD filter instead has explicit observation and state equations, estimates parameters on training data, and filters forward without a smoother. Its Gaussian form remains an approximation that may miss jumps, asymmetric tails, and changing liquidity.

**Questions to ask.** What hidden quantity am I claiming to estimate? What measurements identify it? Could another mechanism generate the same observations? Does the uncertainty increase when evidence is missing or contradictory?

## Lesson 7 — Observation, prediction, action, and adaptation are different operations

**Lesson.** C5 distinguishes a state-update function from an adaptation function that changes the update rules. A changing displayed state is not necessarily an adapting model. A forecast is also not a controller: control needs an action and a way that action affects outcomes.

**Mathematics.** A useful separation is

$$
x_{t+1}=f_{\theta_k}(x_t,o_{t+1}),
\qquad
\theta_{k+1}=A(\theta_k,\mathcal D_k,L).
$$

The first equation updates the state using observations. The second updates parameters using an adaptation dataset and loss. An execution policy would add $u_t=\pi(x_t)$ and an objective involving future PnL, risk, and costs. These need not operate on the same clock.

**Market interpretation.** A Kalman estimate can react every minute while its parameters remain frozen. Retraining on each losing trade would be parameter adaptation, but possibly adaptation to noise. A trader can change position without changing either model. Clear separation lets us diagnose which part failed.

**Code and unresolved question.** Original notebook 5 genuinely adapts some training weights from errors, while certain governor methods merely record diagnostics. The CAD implementation fits on TRAIN, chooses opinion-pool parameters on CAL, and reports on TEST. It does not send orders or automatically retrain. Its pooling weight reflects comparative conditional forecasting performance, not an independent causal law.

**Questions to ask.** What is being changed—state, parameters, representation, or position? Which loss defines improvement? Has the feedback outcome actually matured? What stops repeated adaptation from learning the same small sample again?

## Lesson 8 — Predictions can change the world they predict

**Lesson.** C18 studies performativity: deploying a model may change the data distribution. C30 gives a market-making example. This is stronger than ordinary nonstationarity because part of the change is caused by model-driven actions.

**Mathematics.** If deploying parameter $\theta$ induces distribution $D(\theta)$, performative risk is

$$
\operatorname{PR}(\theta)=\mathbb E_{Z\sim D(\theta)}[\ell(Z;\theta)].
$$

A performative optimum minimizes this full expression. A stable point instead satisfies

$$
\theta^*\in\arg\min_\theta\mathbb E_{Z\sim D(\theta^*)}[\ell(Z;\theta)].
$$

Stability and optimality are not identical. C18 proves retraining convergence under particular smoothness, strong-convexity, and weak distribution-response assumptions. It does not say arbitrary adaptive trading systems converge.

C30 proposes $ds_t=\varepsilon(r_t-s_t)dt+\sigma dW_t$, where $r_t$ is a strategy-generated reference valuation. With constant known $r$, this is an ordinary mean-reverting conditional model. With a random future reference, its uncertainty must also enter the forecast: one cannot generally use the deterministic-reference Gaussian mean/variance merely because the reference is adapted.

**Market interpretation and code.** A small CGB trader may have little direct impact, yet many similar momentum accounts can create collective feedback. The CAD model currently observes the resulting market; it does not identify a deployment-response map, impact kernel, or performative equilibrium. Original structural fusion likewise does not estimate all those objects.

**Questions to ask.** Would this pattern exist if participants stopped responding to it? Can our actions alter quotes or fills? Is apparent model decay caused by external conditions, our own impact, or competitors adapting? What evidence distinguishes them?

## Lesson 9 — Order flow describes an interaction, not an institution's intention

**Lesson.** C29 is particularly relevant to L2, but its actual claim is narrower than “filtered flow predicts momentum.” It studies association between imbalance and returns over the same backward-looking window, using BankNifty futures and a small set of trading days.

**Mathematics.** The paper's count-based convention is

$$
I_t=\frac{N_t^{\rm sell}-N_t^{\rm buy}}{N_t^{\rm sell}+N_t^{\rm buy}}.
$$

The CAD top-of-book feature instead uses displayed sizes:

$$
B_t=\frac{q_t^{\rm bid}-q_t^{\rm ask}}{q_t^{\rm bid}+q_t^{\rm ask}}.
$$

These differ in primitive data, sign, and interpretation. Neither is interchangeable with signed executed volume. The paper's stronger association for filtered executed-trade parent orders motivates research, not a demonstrated CGB trading strategy.

Its lifetime filter uses $T_j=t_j^{\rm exit}-t_j^{\rm entry}$. At a decision before exit, the eventual $T_j$ is unknown. A live feature can use current age $a_j(t)=t-t_j^{\rm entry}$, observed modifications so far, or already completed order histories. It cannot retroactively classify all earlier events using their future lifetimes. Event-time “filtration” in the paper means selecting events; it should not be confused with automatically satisfying a probabilistic information-filtration condition.

**Market interpretation and observability.** A sell imbalance with little downward movement suggests possible absorption. It could also reflect measurement gaps or simultaneous buying elsewhere. A small imbalance with a large fall could indicate thin liquidity. Test the joint behavior of flow, depth changes, and subsequent price response instead of inferring intent from a large visible order.

**Code and unresolved question.** The CAD book module computes current size imbalance and microprice displacement. It does not reconstruct order lifetimes, Hawkes intensities, hidden inventories, or institutional identities. C29 itself says it does not observe trader identities and does not specify a forecasting/execution strategy. Hawkes cross-excitation can describe temporal dependence; without additional identification, it does not establish intervention-level causality.

**Questions to ask.** Is this resting depth, an update count, or executed flow? Is the filter available now? Does the relationship lead future prices after controlling for the price move already completed? Does it survive other days and instruments?

## Lesson 10 — A physical analogy becomes a financial model only through measurement

**Lesson.** P2–P5 use force, temperature, free energy, pointer states, and Born amplitudes to organize intuition. A charitable reading is that constraints shape which configurations persist. To construct a model, each term still needs a financial definition and a test.

**Mathematics.** The essays propose a penalty landscape

$$
H(w,\rho,F)=-w\cdot F+\frac{\gamma}{2}\lVert w\rVert^2+\lambda(K*\rho)(w).
$$

This can motivate exposure incentives, concentration costs, and interaction effects. It does not determine their units or coefficients from price data alone. Likewise, a free-energy decrease $-d\mathcal F/dt\ge0$ requires the relevant gradient-flow assumptions and boundary conditions. Changing the forcing or the landscape adds terms; the inequality is not a financial PnL guarantee.

Original notebook 5 maps positive scores to probabilities by $p_j=A_j^2/\sum_kA_k^2$, then performs additional structural/classifier fusion. Squaring positive scores guarantees neither a correct state ontology nor calibrated probabilities. There are no financial quantum phases whose interference is measured by that operation.

**Market interpretation and code.** The CAD notebook chooses explicit conditional experts: a drift model and supervised future-outcome heads. Their convex log pool is

$$
p_j\propto\exp\!\left(\frac{w\log p_j^{\rm ML}+(1-w)\log p_j^{\rm dyn}}{T}\right).
$$

Its purpose is practical forecast combination, with weights estimated on calibration data. The experts share information, so it is not multiplication of independent likelihoods. Neither theory nor normalization replaces held-out calibration and economic evaluation.

**Questions to ask.** Which part is an analogy, a definition, an estimate, or an empirical result? Are the units compatible? Can new evidence overturn the structural story? Would a simpler model express the same useful assumption more clearly?

## Lesson 11 — Turn the trading story into competing, observable explanations

Consider the example: CGB opens lower, repeatedly fails to recover VWAP, and a reported account pays five-year swaps. The observation is interesting because several channels appear aligned. The research task is to separate what each channel adds.

**Mathematics and interpretation.** Define the future midpoint outcome at horizon $h$ as

$$
Y_{t,h}=\frac{m_{t+h}-m_t}{\text{tick size}}.
$$

Then compare conditional predictions using price history alone, price plus US duration/curve changes, and price plus timely swaps or book data. The incremental question is whether the added observations improve out-of-sample forecasts of $Y_{t,h}$ or its path risk. Describing the same completed selloff several ways is not additional predictive evidence.

A 2s5s flattening has multiple constructions. With $s_{25}=y_5-y_2$, flattening means $\Delta s_{25}<0$. This can occur because five-year yields fall faster, two-year yields rise faster, or both yields rise with the two-year rising more. Those cases have different implications for duration. The slope sign alone cannot prove that a rally is coming.

**What is observable and implemented.** Timely prices, yield changes, received swap quotes, displayed book sizes, and observed trades are measurements. An account's motive, total hedge, and future execution schedule usually are not. The CAD code constructs price, common/local, curve, optional book, and optional VWAP features. It does not assert that a named institution caused or foresaw a trend.

**Questions to ask before advancing.** What was already priced? Which new observation would distinguish persistence from exhaustion? Is the signal available before the next move? Does each horizon have a complete target? Are the labels independent of the feature story? Can the model say uncertain without pretending the market is balanced? Which simple baseline must the new explanation beat?

The intended learning outcome is the ability to move from a compelling market account to a precisely timed, measurable, revisable research hypothesis—and to recognize exactly where observation ends and interpretation begins.
