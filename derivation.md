# Biological transport and constraint geometry in Canadian and US bond futures

## Abstract

We formulate a cross-domain inverse problem connecting biological transport and constraint geometry to the coupled dynamics of Canadian government bond futures and US Treasury futures. The financial system is represented by a causal response operator whose coefficients depend on latent inventory, funding, liquidity, and contract states. A relative price displacement is an observation of this system rather than a complete description of its state.

Coupled moisture transport and elastic deformation provide a first-principles construction of distributed internal states, anisotropic response, and incompatible preferred geometry. Organized elastic microstructures provide a complementary construction of selective disturbance transmission. Eliminating internal variables produces memory operators that can be compared with reduced financial dynamics through explicitly defined state, input, and observation mappings. We derive conditions under which common forcing generates transient relative displacement, equal observed displacement admits different subsequent responses, and stable directed coupling permits temporary amplification.

The analysis focuses on CGB and standard ZN futures, with Ultra 10-year TN as a maturity control. Intraday transmission is conditioned on slower economic and contract states. Operator correspondence, observability, stochastic consistency, and execution constraints define the limits of the proposed framework. The mathematical results are supported by synthetic verification; empirical presence and predictive value in CGB–ZN markets remain hypotheses requiring market-data identification.

## 1 Introduction and modeling principles

Cross-market price formation involves more than the movement of two quoted prices. Participants hold heterogeneous exposures, revise them under funding and risk constraints, and interact through markets whose replenishment and adjustment rates vary over time. A price displacement can therefore reflect several distinct conditions: a change in the economically justified target, incomplete information assimilation, accumulated inventory pressure, a binding financing constraint, or a change in the contract's observation geometry. Distinguishing these conditions requires a model of the states and mechanisms that generate the observed displacement.

Biological systems suggest a constructive approach to this problem. Their macroscopic response emerges from organized microscopic constraints, transport pathways, and internal states. The relevant cross-domain question is whether specified mathematical properties of these mechanisms survive reduction into an effective market model. A resemblance between shapes or time series is insufficient; the correspondence must preserve named operators, causal inputs, observable outputs, and constraints within a stated regime.

The framework combines distributions over exposures, constrained stochastic adjustment, anisotropic interaction, internal-state memory, and feedback from deployed decisions. These ingredients are treated as explicit modeling assumptions. The biological constitutive laws and the proposed financial dynamics have different evidential status: established physical mechanisms motivate operator classes, while financial interpretation requires identification and independent prediction.

Seven distinctions govern the construction:

1. **Return neutralization and level stability.** Covariance neutralization establishes a fitted orthogonality condition, not a restoring drift. A return residual, a level displacement, a residual obtained by subtracting a rolling center, and a self-financing gain process are different mathematical objects. Their stability and economic interpretation must be assessed separately.
2. **Dissipation and financial return.** A gradient flow can reduce an energy or penalty functional without generating cash profits for an investor. Changing forcing, interaction kernels, diffusion, and actions contribute terms of either sign to its derivative. A trading objective therefore requires a separate cash-flow and execution model.
3. **Physical laws and formal correspondences.** A transported symmetry must remain algebraically and dimensionally consistent. Opposite real rates have equal squares, not opposite squares. A coordinate boundary is not automatically a physical boundary, and a proposed latent field requires an observation mechanism. Physical terminology alone establishes neither a financial conservation law nor a constitutive relation.
4. **Classical probability and quantum structure.** Representing a classical probability by its square root does not establish quantum dynamics. Amplitudes proportional to exp(score/(2 temperature)), followed by squaring and normalization, yield ordinary softmax weights. Complex phase, interference, and a measurement structure would require additional mathematical and empirical justification.
5. **Predictive features and dynamical invariants.** A bounded persistence score is not automatically a Hurst exponent, and a propagation score is not automatically a Lyapunov exponent. A feature can be useful without possessing the stronger interpretation suggested by its name. That interpretation must follow from its definition, estimator, and validation.
6. **State architecture and empirical transition laws.** A selected state topology or transition matrix is a prior unless derived from identified mechanisms and observations. State dimension, persistence, and admissible transitions must be supported at the relevant sampling scale. A persistence probability cannot be transported unchanged between daily and intraday observations.
7. **Causal models and causal estimation.** Every decision, initialization, normalization, and parameter fallback must use information available before action. A volatility estimate from the complete evaluation series introduces future information into an earlier observation. Initial uncertainty must instead use a training-only prior or a past-only estimate.

The resulting program is to construct a feasible state space, define the observation map, derive candidate transition mechanisms, and identify which effective law is supported by the data. Regime labels summarize conditions; they do not replace governing equations.

## 2 Contract structure and financial coordinates

Let C denote CGB, U denote standard CME ZN, and T denote Ultra 10-year TN. Use actual expiry contracts and exchange event times, not an unqualified back-adjusted continuous ticker.

| Object | CGB | Standard ZN |
| --- | --- | --- |
| Contract face amount | CAD 100,000 | USD 100,000 |
| Price-point cash multiplier | CAD 1,000 | USD 1,000 |
| Outright minimum increment | 0.01 point, CAD 10 | 1/64 point, USD 15.625 |
| Deliverable maturity range under published rules | 8 to 10.5 years, with specified rounding | At least 6.5 and less than 8 years, with specified rounding |

Contract sizes, delivery, and CGB eligibility come from [Montréal Exchange CGB specifications](https://www.m-x.ca/en/markets/interest-rate-derivatives/cgb); ZN delivery eligibility, conversion factors, point value, and tick are defined in [CBOT Chapter 19](https://www.cmegroup.com/rulebook/CBOT/II/19.pdf). The name “10-year” therefore does not give matched maturity exposure. TN's narrower exposure near ten years makes it a useful control, as described in [CME's Ultra 10-year introduction](https://investor.cmegroup.com/news-releases/news-release-details/cme-group-announces-successful-launch-ultra-10-year-futures).

Define these observed or inferred objects:

- F_i(t): futures midpoint in decimal price points, with bid, ask, and age stored separately.
- k_i(t): cheapest-to-deliver bond identity, and c_i(t): its conversion factor.
- y_i(t,T): cash zero curve; r_i(t,T): financing curve, including bond-specific repo where available.
- d_i(t): positive futures DV01 in native currency per basis point, evaluated using information available at t.
- v_i(t): vector of key-rate DV01s in native currency per basis point.
- X_t: CAD per USD; one USD of current variation-margin P&L converts to X_t CAD.
- Q_i(t,p): displayed depth; replenishment, cancellations, trade signs, open interest, and roll state are separate observables.
- theta_t: inferred country-specific relative valuation target, conditional on policy expectations, term premia, supply, financing, and the contract state.

For a simplified bond with a parallel continuously compounded yield y and cash flows C_j at times T_j,

$$
B(y)=\sum_j C_j e^{-yT_j},\qquad
-\frac{\partial B}{\partial y}=\sum_j T_jC_j e^{-yT_j}>0.
$$

If B is currency value for the deliverable nominal amount, the frozen-CTD approximation is

$$
d_i\approx \frac{10^{-4}}{c_i}\left(-\frac{\partial B_i}{\partial y}\right).
\tag{1}
$$

Carry, financing, delivery-option sensitivities, and CTD switching modify this approximation. In a production inverse problem, use the full observation function

$$
F_i=\Phi_i[y_i(\cdot),r_i(\cdot),\text{basket}_i,\text{delivery rights}_i,\text{basis}_i]
+\ell_i+\epsilon_i.
\tag{2}
$$

Here ell_i is a transient microstructure displacement and epsilon_i is observation noise. Cross-country policy and term-premium differences belong in the slow state; they are not assumed to disappear by arbitrage. A fixed-bond forward calculation and an explicit delivery option must use consistent conventions so that the quality option is not counted twice.

Locally define a yield-equivalent increment

$$
dx_i(t)=-\frac{m_i}{d_i(t^-)}\,dF_i(t),\qquad m_C=m_U=1000.
\tag{3}
$$

The units are basis points. Its integral is a risk-normalized coordinate, not an exact cash yield. Use left-limit risk coefficients for trading calculations. At CTD changes, equation (2), its Jacobian, and its uncertainty change; the latent economic state need not jump just because the observation chart changes.

A long n_C CGB and short n_U ZN position neutralizes a shared parallel basis-point shift when

$$
n_U=n_C\frac{d_C}{X_td_U}.
\tag{4}
$$

If the factor produces dx_C=beta dx_U, factor neutrality instead requires n_U=n_C beta d_C/(X_t d_U). Scalar duration neutrality does not also neutralize every curve factor. Two instruments can remove one common factor while retaining a nonzero position; they generally cannot remove two independent factors simultaneously. TN and additional tenors improve identification even when only CGB and ZN are traded.

Currency conversion of futures P&L is not multiplication of the futures price by spot FX as if it were an owned foreign cash bond. Account balances and collateral can introduce separate FX exposure; that requires its own ledger.

## 3 Pinecone transport and incompatible preferred strain

The ordinary bilayer description is incomplete. Research on pinecone scales reports differential tissue deformation and a porosity gradient; another study identifies spring-like and square microtubular structures in vascular bundles, with water retention in surrounding tissue contributing to slow movement. These mechanisms motivate studying transport, spatially varying stiffness, and internal states together. They are established findings for the studied specimens, not a claim that one ideal bilayer represents every species. See [Quan et al. on hydration-induced deformation](https://www.sciencedirect.com/science/article/pii/S1742706121002956) and [Zhang et al. on slow hygroscopic movement](https://www.nature.com/articles/s41563-022-01391-2).

### 3.1 Constitutive objects and conservation

Take a bounded tissue domain Omega in three-dimensional space. Let c(x,t) be water content per reference volume, u(x,t) displacement, a(x) a local fiber director, C(x) an elastic stiffness tensor, and B(x) the tensor mapping water-content change into preferred strain. In a small-strain approximation,

$$
\varepsilon(u)=\tfrac12(\nabla u+\nabla u^\top),\qquad
\varepsilon^*(c,x)=B(x)[c-c_0(x)].
$$

For transversely anisotropic swelling,

$$
B=b_\parallel a\otimes a+b_\perp(I-a\otimes a).
$$

The director field, permeability, and stiffness are microscopic architectural information. Their spatial organization determines which moisture perturbations generate bending, rather than merely changing volume.

Consider the coupled functional

$$
\mathcal E[c,u]=\int_\Omega\left[
f(c,x)+\tfrac12\nabla c\cdot K_c(x)\nabla c
+\tfrac12(\varepsilon(u)-\varepsilon^*):C:(\varepsilon(u)-\varepsilon^*)
\right]dx.
\tag{5}
$$

Assume positive stiffness on symmetric strain tensors and positive moisture mobility. With C independent of c for this derivation,

$$
\sigma=C:(\varepsilon-\varepsilon^*),\qquad
\mu=\frac{\delta\mathcal E}{\delta c}=f_c-\nabla\cdot(K_c\nabla c)-B:\sigma.
\tag{6}
$$

Mechanical stress therefore feeds back into moisture chemical potential. If C depends on hydration, its derivative contributes another term to mu. Dropping this contribution while fitting humidity-dependent stiffness would be inconsistent.

Water conservation and quasistatic mechanical balance give

$$
\partial_t c+\nabla\cdot J=0,\qquad J=-M_c\nabla\mu,
\qquad -\nabla\cdot\sigma=0.
\tag{7}
$$

Specify initial c; fixed supports or tractions for u; and either impermeable boundaries or an exchange law J dot n = k(mu-mu_ext). If equation (5) includes a moisture-gradient term, supply its natural or prescribed concentration boundary condition as well. On a closed domain with no mechanical work,

$$
\frac{d\mathcal E}{dt}=-\int_\Omega\nabla\mu\cdot M_c\nabla\mu\,dx\leq0.
\tag{8}
$$

For exchange with a reservoir, the energy derivative includes boundary chemical work. Dissipation remains nonnegative after that external work is accounted for. Equation (8) is conditional on the constitutive model and boundary conditions; it is not a generic assertion about open systems.

### 3.2 Derive macroscopic curvature

In a slender scale, take longitudinal strain epsilon_0+z kappa across thickness z. Let E(z)>0 be longitudinal modulus and e_star(z) preferred strain. Per unit beam length and width,

$$
E_b=\tfrac12\int E(z)[\epsilon_0+z\kappa-e^*(z)]^2dz.
$$

Define

$$
A=\int E dz,\quad B_1=\int Ez dz,\quad D=\int Ez^2dz,
\quad N^*=\int Ee^*dz,\quad M^*=\int Eze^*dz.
$$

Force and moment balance, or minimization with respect to epsilon_0 and kappa, gives

$$
\begin{pmatrix}A&B_1\\B_1&D\end{pmatrix}
\begin{pmatrix}\epsilon_0\\\kappa\end{pmatrix}
=\begin{pmatrix}N^*\\M^*\end{pmatrix},\qquad
\boxed{\kappa=\frac{AM^*-B_1N^*}{AD-B_1^2}}.
\tag{9}
$$

Weighted Cauchy–Schwarz gives AD-B_1^2>0 for a nondegenerate thickness distribution. For equal-modulus, equal-thickness layers of total thickness h, the chosen strain sign convention gives

$$
\kappa=\frac{3}{2h}(e^*_{\rm top}-e^*_{\rm bottom}).
\tag{10}
$$

Equation (9) shows exactly how architecture becomes response: a stiffness-weighted first moment of incompatible preferred strain produces curvature, divided by effective bending stiffness. Uniform swelling can change extension without generating curvature. After extension is eliminated, bending stiffness is D-B_1^2/A, and there can still be residual elastic energy because a general preferred-strain profile is not affine in z.

### 3.3 Geometry rather than shape copying

For large rotations, use a shell embedding r:S to R^3. Its induced first and second fundamental forms are a_alpha_beta=partial_alpha r dot partial_beta r and b_alpha_beta=n dot partial_alpha partial_beta r. Hydration assigns preferred forms a_bar(c), b_bar(c). A shell energy has stretching and bending terms proportional to h and h^3, respectively, in their differences from these preferred forms.

Not every proposed pair of forms is realizable. A smooth Euclidean surface must satisfy Gauss and Codazzi compatibility, including

$$
K(a)=\frac{\det b}{\det a},\qquad
\nabla_\alpha b_{\beta\gamma}=\nabla_\beta b_{\alpha\gamma}.
\tag{11}
$$

Incompatible preferred geometry creates residual stress even without external mechanical loads. This is the relevant organizing principle: locally preferred responses may not be jointly realizable. The physical geometry and its derivation are developed in [Efrati, Sharon, and Kupferman's non-Euclidean plate theory](https://arxiv.org/abs/0810.2411).

Financial markets have no demonstrated Gauss–Codazzi law. The transferable question is whether a family of locally preferred adjustments lies in the image of a global constraint operator. That finite-dimensional problem is derived in Section 9.

### 3.4 Architecture creates a relaxation spectrum

Near a stable reference state, eliminating quasistatic displacement gives an effective moisture Hessian H_c. The linearized dynamics can be written

$$
\dot c=-\mathscr L c+\mathscr B h(t),\qquad
\kappa(t)=\mathscr C c(t),\qquad
G_B(s)=\mathscr C(sI+\mathscr L)^{-1}\mathscr B.
\tag{12}
$$

Here h is a small humidity or reservoir-potential perturbation. The natural moisture state space is L^2(Omega), with a suitable Sobolev operator domain and boundary conditions. A uniformly elliptic diffusion specialization on a bounded regular domain has a discrete relaxation spectrum. More general coupled gradients require the energy-weighted operator, rather than assuming self-adjointness in an arbitrary L^2 metric.

For modes with rates lambda_n>0 that are excited and observed,

$$
G_B(s)=\sum_n\frac{r_n}{s+\lambda_n},\qquad
K_B(t)=\sum_n r_ne^{-\lambda_nt}.
\tag{13}
$$

Architecture determines rates and residues. Boundary water retention changes the slow modes; anisotropic transport changes which regions respond first; curvature observation can give residues of opposite signs. Thus a differential output need not be monotone even when the underlying transport dissipates energy.

A broad spectrum with density g(lambda) proportional to lambda^(alpha-1) on a finite range gives, over the corresponding intermediate time range,

$$
\int_0^\infty e^{-\lambda t}\lambda^{\alpha-1}d\lambda
=\Gamma(\alpha)t^{-\alpha},\qquad 0<\alpha<1.
\tag{14}
$$

A fractional-memory representation may approximate such a spectrum. A fitted power law is not proof of literal fractal geometry or an infinite-memory law. Completely monotone positive kernels require positive modal weights; curvature differences and cross-market responses may have signed weights.

Humidity cycling can produce **rate-dependent loops** because moisture states lag the input. A linear diffusive bilayer does not, by itself, establish **rate-independent hysteresis**. The latter requires additional switching, multistability, sorption branches, or another constitutive mechanism.

### 3.5 Microscopic coefficients and operator domains

The tensors in equation (5) need an architectural derivation or measurement. In a periodic, scale-separated linear-elastic idealization with microscopic cell Y of unit volume, define a periodic displacement corrector chi with zero mean. For imposed macroscopic strain E_0,

$$
W_{\rm eff}(E_0,c)=\min_{\chi}\tfrac12\int_Y
[E_0+\varepsilon_y(\chi)-\varepsilon^*(y,c)]:C(y):
[E_0+\varepsilon_y(\chi)-\varepsilon^*(y,c)]dy.
\tag{14a}
$$

Its stationarity condition is local force balance in Y. Differentiating the minimized energy with respect to E_0 defines effective stress; its second derivative defines C_eff. Preferred strain and internal corrector fields determine the effective swelling tensor and any remaining stress. This is a conditional homogenization calculation: actual heterogeneous pinecone tissue need not be periodic, have a clean separation of scales, or obey linear elasticity over an entire opening cycle.

An analogous transport cell problem defines an effective positive tensor D_eff:

$$
\xi^\top D_{\rm eff}\xi=\min_{\phi\ {
\rm periodic}}\int_Y(\xi+\nabla_y\phi)^\top D(y)
(\xi+\nabla_y\phi)dy.
\tag{14b}
$$

For flat layers with fractions v_j and scalar transport coefficients D_j, transport along the layers has coefficient sum v_j D_j, while transport across layers has coefficient (sum v_j/D_j)^(-1). This gives a direct first-principles mechanism for anisotropy from constituents that are individually isotropic. Elastic and transport architectures can therefore have different principal directions. A single scalar response curve cannot recover both microscopic organizations uniquely.

For equation (7), the quasistatic displacement is mathematically defined by its weak form. On a bounded regular domain with supports removing rigid motions, the bilinear form

$$
a_u(u,v)=\int_\Omega\varepsilon(u):C:\varepsilon(v)dx
$$

is bounded and coercive on the admissible H^1 displacement space by uniform stiffness positivity and Korn's inequality. Lax–Milgram then gives a unique displacement for a prescribed moisture field and admissible loads. Eliminating it is not merely a metaphor: the quadratic effective moisture Hessian is a Schur complement,

$$
H_{\rm eff}=H_{cc}-H_{cu}H_{uu}^{-1}H_{uc}.
\tag{14c}
$$

Its positivity requires stability of the full coupled energy after the constrained modes are removed. A nonconvex energy can lose that property and permit multiple branches.

For the simpler Fickian linear specialization, a symmetric uniformly positive D(x) and Robin exchange define the closed form

$$
a_c(v,w)=\int_\Omega\nabla v^\top D\nabla w\,dx+
\int_{\partial\Omega}k vw\,dS,\quad k\geq0.
\tag{14d}
$$

It generates a nonnegative self-adjoint operator on L^2(Omega). On a bounded regular domain the resolvent is compact, justifying the discrete-mode expansion used in equation (13). Pure no-flux conditions retain a zero constant mode; exclude that conserved mode or model exchange before claiming strictly positive relaxation rates. Coupled higher-order moisture models have different form domains and boundary requirements and cannot inherit this particular operator theorem without checking them.

These calculations also limit the financial inverse problem: if several architectures produce the same effective Hessian and observable spectral residues, macroscopic futures responses cannot identify which microscopic architecture generated them. Additional ports or independent internal measurements are necessary.

## 4 Mantis shrimp architecture and selective transmission

The transferable mechanism is selective propagation through organized anisotropy. Helicoidal and herringbone microstructures redistribute stress and support toughness. A 2025 study combined ultrasonic experiments and simulations to identify phononic behavior and selective shear-wave filtering in the periodic region. The claims are about particular wave modes, specimens, and modeling conditions; reduced transmitted energy must not automatically be described as absorption. See [Yaraghi et al. on herringbone architecture](https://arxiv.org/abs/1604.07798) and [Alderete et al. on phononic shielding](https://bpb-us-e1.wpmucdn.com/sites.northwestern.edu/dist/b/5461/files/2025/02/Does-the-mantis-shrimp-pack-a-phononic-shield-1.pdf).

### 4.1 Derive the operator

Let an orthotropic stiffness tensor C_0 be rotated through a depth-dependent fiber angle theta(z):

$$
C_{ijkl}(z)=R_{ia}R_{jb}R_{kc}R_{ld}(\theta(z))(C_0)_{abcd}.
$$

Momentum conservation gives the small-amplitude elastodynamic model

$$
\rho_m\partial_t^2u=\nabla\cdot[C(z):\varepsilon(u)]-\mathscr D\partial_tu+f,
\tag{15}
$$

where rho_m is material density and D is a positive damping operator when damping is included. With suitable boundary conditions,

$$
\frac{d}{dt}\left[\tfrac12\int\rho_m|\dot u|^2dx+
\tfrac12\int\varepsilon:C:\varepsilon\,dx\right]
=\text{input power}-\langle\dot u,\mathscr D\dot u\rangle.
\tag{16}
$$

For a periodically rotated idealization, insert a Bloch field u=e^(iq dot x-i omega t)v_q(x), where v_q is periodic. A discretization gives

$$
K(q)v_q=\omega^2M v_q.
\tag{17}
$$

A bandgap is an interval with no propagating mode of the specified polarization and direction. Graded pitch is not globally periodic; local periodic approximations or direct transfer/scattering computations are needed. Reflection, localized storage, scattering into other modes, and damping are distinct mechanisms.

### 4.2 What survives in finance

A financial analogue can preserve frequency-dependent transmission, mixed modes, directional sensitivity, and several internal relaxation times. It does not inherit mass density, momentum conservation, physical pitch, elastic wave speed, or a phononic bandgap.

In a linear financial realization,

$$
\dot z=Az+Bf,\qquad y=Cz+Df,\qquad
G_F(s)=C(sI-A)^{-1}B+D.
\tag{18}
$$

A small singular value of G_F(i omega) in one input/output direction describes weak transmission at that frequency. Calling it a biological bandgap would require additional evidence of the relevant periodic mechanism. A lag filter or a transfer zero is already standard systems theory. The new research opportunity is to identify which changing market constraints organize that filter and whether the identification predicts responses to new shocks.

## 5 Specify what cross-domain equivalence means

An analogy is rigorous only relative to named structures. Let biology have state space X_B, market dynamics X_F, input maps, output maps, and evolution semigroups S_B(t), S_F(t). Seek a bounded reduction Pi and positive time scale a such that

$$
\Pi S_B(t)\approx S_F(at)\Pi,\qquad
\Pi A_B\approx aA_F\Pi,
\tag{19}
$$

on specified operator domains and an experimentally relevant subspace. Inputs and observations must also map: Pi B_B approximately equals a B_F U, and C_F Pi approximately equals R C_B. U and R convert explicitly defined input and output units. Arbitrary gains cannot be adjusted separately for every observation after testing.

Exact invertible bounded similarity preserves the generator spectrum; unitary equivalence additionally preserves the chosen inner product. A noninvertible reduction preserves only the retained invariant modes. Exact deterministic lumping needs the discarded kernel to remain invariant; otherwise eliminating it generates memory or noise.

For nonlinear deterministic fields, a differentiable state map T requires

$$
DT(x)f_B(x)=a f_F(Tx).
\tag{20}
$$

For Itô diffusions with covariance Q_B, the pushforward drift also contains the Hessian correction:

$$
DT f_B+\tfrac12 Q_B:\nabla^2T=a f_F\circ T,\qquad
DT Q_B DT^\top=a Q_F\circ T.
\tag{21}
$$

Equivalently, their generators satisfy L_B(phi composed with T)=a(L_F phi) composed with T. Matching deterministic drift while ignoring covariance and the Itô correction is not stochastic equivalence. In partially observed systems, matching outputs is weaker still.

| Property | Candidate preservation | Necessary qualification |
| --- | --- | --- |
| Hidden distributed states | Moisture modes to inventory and funding modes | Only observable combinations can be identified |
| Anisotropy | Stiffness or transport tensor to direction-dependent adjustment or uncertainty tensor | Economic coordinates and risk metric must be fixed |
| Internal compatibility | Strain constraints to global feasibility or graph consistency | Financial constraints must be derived, not declared physical laws |
| Elimination of internal variables | Both produce a causal memory operator | This is a general dynamical property, not uniquely biological |
| Relaxation spectrum | Matched poles or approximate modal measures | Only within identifiable frequency and time ranges |
| Passivity | A common storage inequality for specified ports | Must be tested in finance; information and strategic activity can invalidate it |
| Hysteresis | Same reduced output at different histories can imply different future response | Separate finite-rate lag, switching, and true persistent branches |
| Conservation | Probability mass and trade bookkeeping | No conservation of price, liquidity, capital value, or “financial energy” |
| Quantum probability | None required | Classical normalized weights are sufficient here |

Local changes of coordinates can make many unrelated nonzero vector fields look similar. Consequently, unconstrained fitting of T is nearly vacuous. A useful mapping must preserve named constraints, causal ports, units, observable predictions, and behavior outside the fitted trajectories. The proposed claim is **approximate operator correspondence after reduction**, not an isomorphism of entire organisms and markets.

## 6 A kinetic model of constrained exposure adjustment

Let w=(w_C,w_U,w_T,b,c,...) be a low-dimensional vector of duration exposures, basis exposure b, and capacity c. Let rho(w,t) be a probability density of modeled agents or exposure states. This distribution describes the heterogeneous population whose adjustments contribute to observable market dynamics. It is not automatically capital density: a capital-weighted distribution needs a separate mass and source equation.

Normalize exposure coordinates by fixed reference scales. The logarithm in the entropy term is understood relative to a fixed reference density in those coordinates; writing log rho below suppresses an additive constant. Changing coordinates or reference measures requires transforming the density and reference together. Differential entropy alone is not a coordinate-independent physical measure of financial disorder.

Suppose agents revise exposures through small stochastic adjustments and face a potential

$$
U(w,t)=\tfrac12w^\top Q_tw-w^\top f_t+\psi_t(w),
$$

where Q_t is an assumed risk/capital penalty, f_t expected marginal benefit, and psi_t represents smooth costs or feasible-set restrictions. Add a symmetric interaction kernel K(w,v) only for the component of interaction that is genuinely reciprocal. Define

$$
\mathcal F_t[\rho]=\int U\rho\,dw+
\tfrac12\iint K(w,v)\rho(w)\rho(v)dw\,dv+
\varepsilon_t\int\rho\log\rho\,dw.
\tag{22}
$$

Its variational derivative is

$$
\mu_\rho=U+K\rho+\varepsilon_t(1+\log\rho).
$$

Assume a positive mobility M(w,t). A particular stochastic micro-model yielding a gradient-form density equation is

$$
dw=\left[-M\nabla(U+K\rho)+\varepsilon_t\nabla\cdot M+v_{\rm act}\right]dt
+\sqrt{2\varepsilon_tM}\,dB+dL_{\rm reflect},
\tag{23}
$$

with an inward reflection term on a fixed feasible boundary. The divergence correction is necessary for spatially varying mobility in this Itô convention. The relation between diffusion covariance and M is a **model assumption**; finance supplies no thermodynamic Einstein relation requiring it. General financial models should estimate an independent covariance tensor and need not have the gradient form.

For the assumed equation (23),

$$
\partial_t\rho=\nabla\cdot(\rho M\nabla\mu_\rho)
-\nabla\cdot(\rho v_{\rm act}).
\tag{24}
$$

For a fixed domain and zero boundary flux, integral rho=1 is conserved. Summing microscopic inventory trades gives a separate clearing identity: total long and short futures positions balance across the entire market. Net inventory in a selected dealer subsystem can change because its counterparties are outside that subsystem. Open interest, marked wealth, depth, and financing capacity can all change.

If active drift vanishes and coefficients are fixed, integration by parts yields

$$
\frac{d\mathcal F}{dt}=-\int\rho\nabla\mu_\rho^\top M\nabla\mu_\rho\,dw\leq0.
\tag{25}
$$

With time-dependent inputs and strategic drift,

$$
\frac{d\mathcal F_t}{dt}=-\mathcal D_t+
\int\rho\,\partial_tU\,dw+
\tfrac12\iint\rho(w)\partial_tK(w,v)\rho(v)dw\,dv+
\dot\varepsilon_t\int\rho\log\rho\,dw+
\int\rho\nabla\mu_\rho\cdot v_{\rm act}\,dw.
\tag{26}
$$

Moving constraints and nonzero boundary flux add further terms. A forcing U=U_0-w dot f_t contributes -E[w] dot f_dot_t, whose sign is unrestricted. Consequently, negative free-energy change is not an unconditionally nonnegative quantity in the driven system. Even equation (25) has units of penalty per time, not necessarily account currency per time.

Asymmetric cross-market propagation generally cannot be hidden inside a symmetric scalar interaction energy. Place it in active drift, a directed operator, delayed controls, or an explicitly non-gradient interaction. The Gibbs expression rho proportional to exp(-H/epsilon) is an equilibrium condition under these restrictive assumptions, not a measured universal distribution of investor exposures.

### 6.1 Moments and closure

For a fixed no-flux domain, integrate (24) against w. Its mean q obeys

$$
\dot q=-\mathbb E[M\nabla(U+K\rho)]+\varepsilon_t\mathbb E[\nabla\cdot M]
+\mathbb E[v_{\rm act}].
\tag{27}
$$

Reflection/boundary forces contribute when present. Nonlinear terms depend on higher moments, so q alone is not closed. The covariance equation depends on drift-exposure cross moments and the diffusion tensor. A Gaussian, finite-mixture, Galerkin, or particle closure is an additional approximation to test against observed responses.

Common news noise shared by agents does not disappear with large population size. Conditional on that common noise, the population density remains stochastic. A deterministic mean-field PDE should not be presented as exact merely because there are many participants.

Prices then arise through the observation function (2), order-flow impact, and market clearing. Defining rho and solving a PDE does not determine futures prices without this coupling. This is the point at which economic mechanisms enter the otherwise general mathematics.

## 7 Eliminate hidden states to obtain the effective market operator

Let x collect observable risk coordinates, and h internal inventory, replenishment, financing, and expectation states. Locally, condition on a slow state eta and write

$$
\dot x=A_{xx}x+A_{xh}h+B_xf,\qquad
\dot h=A_{hx}x+A_{hh}h+B_hf.
$$

Variation of constants gives

$$
h(t)=e^{A_{hh}t}h(0)+\int_0^te^{A_{hh}(t-s)}[A_{hx}x(s)+B_hf(s)]ds.
$$

Substitution yields the exact reduced equation

$$
\boxed{\dot x(t)=A_{xx}x(t)+\int_0^tK_\eta(t-s)x(s)ds+
\widetilde B_\eta*f(t)+r_\eta(t)},
\quad K_\eta(t)=A_{xh}e^{A_{hh}t}A_{hx}.
\tag{28}
$$

The initial-state term r_eta=A_xh exp(A_hh t)h(0) matters. Eliminated stochastic noise becomes colored forcing; it is not generally independent white noise. In Laplace form,

$$
K_\eta(s)=A_{xh}(sI-A_{hh})^{-1}A_{hx}.
\tag{29}
$$

This is the precise cross-domain bridge: moisture transport and financial internal adjustment can both lead to a Schur-complement memory operator. A price-only Markov model can fail because it discards variables needed to predict the future. Equation (28) is already general systems theory; biological architecture suggests restricted realizations and informative experiments, rather than establishing a new identity.

If eta changes appreciably during the response, replace exp(A_hh(t-s)) by the nonautonomous evolution operator U_h(t,s). The kernel becomes A_xh(t)U_h(t,s)A_hx(s), which depends on both times rather than their difference. A convolution kernel estimated across such changes mixes different constitutive states. This is one precise way a conditional effective law can fail without any mysterious violation of stationarity.

### 7.1 A sharply falsifiable differential-response model

Suppose, as a local hypothesis, both markets eventually assimilate a shared input f but with different relaxation times:

$$
\tau_C\dot x_C+x_C=a_Cf,\qquad
\tau_U\dot x_U+x_U=a_Uf.
$$

Use beta=a_C/a_U and e=x_C-beta x_U. Then

$$
\boxed{\frac{E(s)}{F(s)}=
\frac{a_Cs(\tau_U-\tau_C)}{(1+s\tau_C)(1+s\tau_U)}}.
\tag{30}
$$

The shared static response cancels while the transient survives. For a step f_0 from a zero reference,

$$
e(t)=a_Cf_0\left(e^{-t/\tau_U}-e^{-t/\tau_C}\right).
\tag{31}
$$

The displacement first opens and then closes without requiring different long-run valuations. A scalar contemporaneous correlation cannot identify this response. If tau_C exceeds tau_U, a positive yield-like input initially makes e negative in these coordinates. This is a conditional calculation, not an assertion that CGB is systematically slower.

Different final country targets add a nonzero static component. Economically justified divergence must not be forced into the transient model. Estimate shock loadings and time scales on training events, then predict the response curve on unseen events with quotes that were actually executable after observation.

### 7.2 Passive memory as one candidate restriction

A finite internal-state realization with displacement e and memory modes m_j can be derived from

$$
V=\tfrac12k e^2+\tfrac12\sum_j a_j(e-m_j)^2,
\quad \dot e=-M_e\partial_eV+u,
\quad \dot m_j=(e-m_j)/\tau_j,
\tag{32}
$$

where k,a_j,M_e,tau_j are positive. It obeys

$$
\dot V=-M_e(\partial_eV)^2-\sum_j\frac{a_j}{\tau_j}(e-m_j)^2+u\partial_eV.
\tag{33}
$$

Eliminating m_j gives a structured relaxation memory. This is genuinely equivalent to a dissipative internal-variable material model at the level of the equations. Its financial meaning is only a hypothesis about reciprocal restoring adjustments. Whether its gradient is related to price and its input to actual trading flow must be specified before translating the storage inequality into an impact-cost restriction.

### 7.3 Active feedback can reverse the conclusion

An alternative reduced model is

$$
de=[-\lambda(\ell)(e-\theta)+b m+d_f f]dt+\sigma_e dW_e,
$$
$$
dm=[-m/\tau+c(e-\theta)+r_f f+G_a a_t]dt+\sigma_m dW_m,
$$
$$
d\log\ell=[\alpha(\log\ell_0-\log\ell)-\chi m^2-\zeta a_t^2]dt
+\sigma_\ell dW_\ell.
\tag{34}
$$

Here ell>0 represents capacity for correcting the relative displacement, not necessarily displayed book depth. Monotonicity of lambda(ell) is a hypothesis to estimate. m is a signed internal pressure, theta the moving target, and a_t the researcher's executed action. All coefficients have units fixed by these state definitions. Keep this three-state proposal separate from the passive construction (32).

Freeze ell and theta. The e,m Jacobian is

$$
A=\begin{pmatrix}-\lambda&b\\c&-1/\tau\end{pmatrix}.
$$

Since trace A<0, local stability requires

$$
\boxed{\lambda/\tau-bc>0.}
\tag{35}
$$

Positive bc weakens stability: restoring behavior can disappear while a regression still reports a familiar spread. Negative bc can create damped oscillatory responses. Define dimensionless loop strength R=bc tau/lambda. For positive feedback, R approaching one is a candidate fragility indicator, with parameter uncertainty carried into the estimate. This follows from the proposed dynamics; it is not an established CGB–ZN threshold.

At equal observed e and theta, opposite m produce opposite instantaneous expected changes through b m. This is the clean experimental discriminator for hidden state. The economic mechanisms attributed to m require additional observations; otherwise m is only a predictive latent coordinate.

### 7.4 Stable spectra can still allow temporary amplification

Take, in a fixed standardized risk metric,

$$
A=\begin{pmatrix}-a&k\\0&-b\end{pmatrix},\quad a,b>0.
$$

Its eigenvalues are negative, yet the off-diagonal response is

$$
[e^{At}]_{12}=k\frac{e^{-bt}-e^{-at}}{a-b},\quad a\ne b.
\tag{36}
$$

A sufficiently large directed coupling produces transient norm growth. Test

$$
\mathcal A_\eta(t)=\|e^{A_\eta t}\|_{Q\to Q},\qquad
\mathcal R_\eta(\omega)=\|(i\omega I-A_\eta)^{-1}\|_{Q\to Q},
\tag{37}
$$

with Q chosen before fitting from meaningful risk or observation units. Arbitrary rescaling can manufacture Euclidean amplification. Every finite-dimensional Hurwitz A admits some Lyapunov metric in which the unforced flow contracts; the relevant empirical claim is amplification in the independently chosen market-risk metric.

### 7.5 Distinguish lag from persistent hysteresis

For an explicit bistable hypothesis, let

$$
V(e;f)=e^4/4-a e^2/2-f e,\qquad \dot e=-\partial_eV,\quad a>0.
$$

Stationary points satisfy e^3-a e-f=0; fold points satisfy 3e^2-a=0. Thus

$$
|f_{\rm fold}|=\frac{2a^{3/2}}{3\sqrt3}.
\tag{38}
$$

Slow input cycling can follow different stable branches. This is a mathematical switching mechanism, not evidence of market bistability. A varying target, finite-rate linear response, CTD switching, or omitted news can also produce apparent loops. Hysteresis depends on the state representation, switching mechanism, forcing protocol, and noise. Markovian evolution in the complete state does not exclude history-dependent response in a reduced observation, nor does an observed loop identify its underlying mechanism.

## 8 Adaptive hedges and nonintegrable observations

Even before introducing latent states, a changing hedge creates a geometric issue. For normalized level coordinates x_C,x_U and state-dependent beta,

$$
s=x_C-\beta x_U,\qquad
ds=dx_C-\beta dx_U-x_Ud\beta.
\tag{39}
$$

The differential hedge gain alpha_form=dx_C-beta dx_U differs from ds. Its exterior derivative is

$$
d\alpha_{\rm form}=-d\beta\wedge dx_U.
\tag{40}
$$

When nonzero, the gain integral depends on the path; there is no scalar spread potential whose change equals that integral on the entire state space. On a closed deterministic loop,

$$
\oint(dx_C-\beta dx_U)=\oint x_Ud\beta.
\tag{41}
$$

This can resemble hysteresis even when the economic state has no hysteretic mechanism. It represents adaptive exposure and rebalancing, not free profit. In a stochastic product formula, beta and x_U can also contribute quadratic covariation. Predictable holdings and a cash/collateral ledger define self-financing gains; subtracting a rolling center or recomputing a hedge does not manufacture tradable mean reversion.

For actual futures, use native-currency cash multipliers and equation (4), not the normalized coordinate integral alone. Record each rebalance and variation-margin cash flow. Test a frozen hedge within each event window as an identification control.

## 9 Incompatible local constraints on an extended market graph

The closest financial version of incompatible geometry requires more than a single two-node edge. Build a connected graph containing CGB, ZN, TN, cash duration factors, and selected financing or policy coordinates. First express all proposed edge displacements in consistent units and remove explicitly modeled country and curve components. These are statistical/economic compatibility targets, not universal no-arbitrage identities between sovereigns.

Let B_G be an edge-by-node incidence matrix; p node coordinates; d desired edge differences inferred from local models; and W a positive precision matrix. A globally compatible configuration minimizes

$$
\mathcal E_G(p)=\tfrac12(B_Gp-d)^\top W(B_Gp-d).
$$

After fixing the constant-coordinate gauge,

$$
B_G^\top W B_Gp^*=B_G^\top Wd,\qquad
r=d-B_Gp^*,\qquad B_G^\top Wr=0.
\tag{42}
$$

The incompatible component is

$$
r=\left[I-B_G(B_G^\top W B_G)^\dagger B_G^\top W\right]d.
\tag{43}
$$

For a cycle c with B_G^top c=0, c^top d must vanish if d is exactly compatible. Nonzero cycle sums detect inconsistent desired differences. Observed synchronous price differences themselves always telescope around a cycle; computing a cycle sum of those differences cannot discover alpha. The informative object is a set of independently inferred, forward-looking adjustment targets, with uncertainty and nuisance terms included.

This projection problem preserves the algebra of frustrated constraints. It does not preserve physical Gaussian curvature. A graph with two nodes and a single undirected edge has no independent cycle space, so CGB and ZN prices alone cannot identify this spatial incompatibility. Parallel edges representing distinct mechanisms require separate observable definitions to carry information.

Possible residual sources include inconsistent estimates, curve mismatch, repo specialness, delivery options, or real intermediate funding constraints. Only the latter mechanisms support a structural interpretation after the other explanations have been tested.

## 10 Formulate the cross-domain inverse problem

Let observations at irregular times t_k be

$$
o_k=h_{\gamma_k}(z_{t_k},\eta_{t_k})+\epsilon_k,
\qquad dz=f_\Theta(z,\eta,a_t)dt+\Sigma_\Theta(z,\eta)dW_t+dJ_t.
\tag{44}
$$

gamma is the contract/CTD observation chart; eta contains slow targets and external conditions; J contains specified jump events. Inputs include timestamped news surprises and observed flow, but a news surprise is not automatically a valid instrument for direct cross-impact. It can affect both markets through a common pathway.

Infer jointly, within a restricted model class:

- the state trajectory or filtering distribution;
- modal rates, loadings, coupling, capacity response, and target evolution;
- the observation Jacobian and CTD/basis uncertainty;
- the reduction and port maps, if a biological operator class is being compared;
- whether reciprocal/passive restrictions survive the data or an active directed extension is required.

One schematic objective, with terms standardized so their units are compatible, is

$$
\min_{\Theta,\Pi,z}\left\{
-\log p_\Theta(o_{1:n}\mid f,a,\gamma)
+\lambda_s\mathcal P_{\rm smooth}(\Theta)
+\lambda_r\mathcal P_{\rm complexity}(\Theta)
+\lambda_I\|\Pi A_B-aA_F\Pi\|_{\rm test}^2
\right\},
\tag{45}
$$

subject to positivity, causality, stated feasible-set conditions, correctly modeled measurement times, and whichever physical restrictions are actually under test. A passivity penalty should compare a passive subclass against an unrestricted active subclass, rather than forcing a financial conclusion. The operator norm is evaluated on explicitly chosen modes or trajectories; unbounded generators cannot be compared by a naive unrestricted matrix norm.

### 10.1 Identifiability is part of the answer

For a linear realization, the observability Gramian is

$$
W_o(T)=\int_0^Te^{A^\top t}C^\top R^{-1}Ce^{At}dt.
\tag{46}
$$

Its rank gives observable state directions; small eigenvalues give unstable inference even when rank is full. Input excitation and a controllability Gramian determine which modes can be probed. Singular values of the block Hankel response suggest a minimal observable realization. State dimension should follow from these identification properties rather than an a priori correspondence with another system.

Hidden-state realizations are usually identifiable only up to similarity:

$$
(A,B,C)\sim(SAS^{-1},SB,CS^{-1}).
\tag{47}
$$

Consequently, a fitted latent variable cannot be called dealer inventory or funding capacity without anchoring measurements. Price-only equivalence does not identify microscopic causation. Inverse diffusion spectra and relaxation measures are also ill-conditioned Laplace inversions: finite noisy observations cannot reliably distinguish arbitrarily many nearby modes.

For parameters, examine sensitivity J_Theta=partial E[o]/partial Theta and a Fisher/weighted sensitivity matrix. Project out target, CTD, and common-news nuisance directions before interpreting coupling sensitivity. A zero or nearly zero residual sensitivity means the claimed structural parameter is not identified by the selected experiment.

No observation-only method can generally separate direct U-to-C transmission from correlated common shocks without exclusions, event design, or other identifying restrictions. Estimate a common driver explicitly and test whether directional coupling survives. A Kalman smoother uses future observations; tradable state estimates require a filter and as-of timestamps.

### 10.2 Identify predictive state before naming a mechanism

Define two histories H and H' as equivalent at the chosen horizon if they imply the same conditional law of future observations under every admissible future action sequence. Their equivalence classes define the minimal predictive state, when such a representation exists.

An operational target for an approximate state encoder m_t is

$$
\min I(m_t;H_t)\quad\text{subject to}\quad
I(o_{t+1:t+h};H_t\mid m_t,\eta_t,\gamma_t)\leq\delta.
\tag{48}
$$

Equation (48) expresses memory selection as a prediction problem: retain the aspects of history needed to distinguish future responses at the chosen horizon. Information-ratchet theory relates effective use of temporal correlations to a matching internal memory, while multiscale requisite variety distinguishes response capacity at different resolutions. See [Boyd, Mandal, and Crutchfield](https://arxiv.org/abs/1609.05353) and [Siegenfeld and Bar-Yam](https://arxiv.org/abs/2206.04896). These principles motivate the representation criterion; they do not guarantee profitable financial control. A daily memory bank may be incapable of distinguishing relevant subsecond states, while a detailed order-book representation may be irrelevant to a multi-day target. Resolution is therefore selected by the future behavior to be distinguished.

### 10.3 Separate statistical lead–lag from causal transmission

Estimate the conditional impulse-response matrix and its frequency representation using timestamp-correct observations. Partial conditioning must include common surprises, quote age, liquidity state, and contract state. Conditional mutual information or transfer entropy can reveal incremental predictive content; neither proves a causal market-to-market link without additional assumptions.

Order lifetimes that are only known when an order later cancels cannot enter an earlier decision. Use age-so-far or a survival estimate, and distinguish it from full realized lifetime. A persistence filter must be defined relative to the observable order history at the decision time. Hawkes excitation describes conditional event intensities; a stable fitted excitation kernel and a shared-news control are necessary before interpreting directional propagation.

## 11 Predictive hypotheses and discriminating experiments

| Hypothesis | Derivation | Discriminating test | Reason to reject |
| --- | --- | --- | --- |
| Differential assimilation times | Equations (30)–(31) | Predict unseen event response shapes using loadings and liquidity-conditioned time scales | Quote-age correction or common news removes the effect |
| Internal state changes response sign | Equation (34) | Match events on e, target, volatility, chart, and news; test incremental history/flow-state prediction | A simple history baseline explains it equally well, or only smoothed states predict |
| Capacity loss changes restoring behavior | Equation (35) | Estimate conditional restoring derivative with uncertainty; test its relation to independent capacity proxies | Parameter is unidentifiable or CTD/target shifts explain it |
| Directed stable coupling amplifies shocks temporarily | Equations (36)–(37) | Compare multi-output responses in a risk metric fixed in advance | Amplification disappears with proper units or common-factor conditioning |
| Broad internal relaxation spectrum | Equations (13)–(14), (28) | Compare a small modal mixture, a power-law approximation, and flexible lag baselines across sampling scales | Only a narrow sampling window supports the power law |
| Incompatible preferred adjustments | Equations (42)–(43) | Use an extended instrument graph and independently inferred edge targets | Residuals arise from estimation error or deterministic contract/currency mismatch |
| Direction differs after loading and unloading | Sections 7.5 and 8 | Freeze the hedge, control target changes, vary cycle speed, and infer an internal branch/state | Adaptive hedge geometry or finite-rate lag accounts for the loop |

The clearest first candidate is the differential response model enriched with a small number of anchored internal modes. It is interpretable, falsifiable, and can fail decisively. More elaborate geometry should earn its place through additional identified predictive content.

Structural novelty would require an architectural restriction that predicts independent responses and survives comparison with models of comparable flexibility. Exponential kernels, latent-state models, fractional approximations, nonnormal operators, graph projections, and performative feedback already have extensive literatures. Their combination here is a proposed research synthesis, not a demonstrated new theorem about these markets.

## 12 Execution and performative feedback

Let n_t be signed integer contract holdings. At a short horizon with CAD as account currency,

$$
\Delta\Pi\approx n_Cm_C\Delta F_C+X_tn_Um_U\Delta F_U
-\text{fees}-\text{spread}-\text{slippage}-\text{impact},
\tag{49}
$$

with a separate exact cash ledger for currency conversion timing and collateral. If n_U is negative, it is a short position. An expected fall in a yield-equivalent coordinate corresponds to an expected rise in the futures price, so trading direction must respect equation (3).

Use the inferred state to forecast executable cash gains g_t and covariance Sigma_t, not merely an abstract decrease in a potential. A local decision problem is

$$
\max_{n\in\mathcal A_t}\left\{n^\top g_t-\tfrac\gamma2n^\top\Sigma_tn
-\mathcal C_t(n,n_{t-1})\right\},
\tag{50}
$$

where A_t imposes margin, participation, inventory, currency, and factor constraints. With no costs or integer restriction and one neutrality constraint r^top n=0,

$$
n^*=\frac1\gamma\left[\Sigma^{-1}g-
\Sigma^{-1}r\frac{r^\top\Sigma^{-1}g}{r^\top\Sigma^{-1}r}\right].
\tag{51}
$$

This formula translates a conditional forecast into risk-constrained exposure. It does not establish that g is nonzero. An entry requires expected executable gain to survive costs and inference uncertainty; a visually large displacement alone is insufficient.

If actions influence the tape or capacity, the model is closed loop:

$$
z_{t+1}=F_\Theta(z_t,a_t,\xi_{t+1}),\quad
a_t=\pi_{\vartheta_t}(o_{\leq t}),\quad
\vartheta_{t+1}=\mathcal U(\vartheta_t,o_{\leq t+1},a_{\leq t}).
\tag{52}
$$

This formulation includes the distribution shift created by deployed predictions and the evolving state of the population responding to them. [Perdomo et al.](https://proceedings.mlr.press/v119/perdomo20a.html) formalize performative prediction, and [Brown et al.](https://arxiv.org/abs/2011.03885) explicitly include population state. Their convergence results depend on specified assumptions and do not imply trading stability.

For small trades, action-independent price forecasts may be an acceptable approximation if participation has negligible influence on the modeled response. At larger participation, dynamics and uncertainty must be conditioned on action size and direction. A simplified feedback a=-Kz changes the local Jacobian to A-BK; delays, saturation, target uncertainty, and the covariance of other agents' actions must also be considered. Repeated tightening of controls can reduce capacity and worsen the displacement being corrected. This possibility is a testable feedback mechanism whose sign and magnitude require financial identification.

Direct statistical cross-response and tradable impact are different ports. In a linear impact model with trading-rate input u and impacted price output,

$$
\mathbb E[C[u]]=\int u(t)^\top\left[\int_0^tG(t-s)u(s)ds\right]dt
+C_{\rm spread}[u].
\tag{53}
$$

Test nonnegative expected cost for admissible round trips in the model. Under particular bounded-kernel assumptions, cross-impact theory derives linearity and reciprocity restrictions; observed asymmetric responses do not automatically violate them because statistical response includes information and bid–ask costs matter. See [Schneider and Lillo](https://arxiv.org/abs/1612.07742) and [Gatheral](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1292353). Do not declare the full financial response operator passive merely because a biological material is passive.

## 13 Empirical research design and computational architecture

### 13.1 Data required for the proposed identification

Use actual CGB and ZN expiry contracts, ideally TN and cash tenors as controls. Store exchange time, receive time, sequence numbers, contract identifiers, bid/ask, quote age, trade price/size/sign, book updates, replenishment, cancellations, open interest, volume, session interruptions, and roll dates. Market-by-order data supports stronger order-lifecycle claims than aggregated depth.

Add deliverable-basket histories, conversion factors, cash bond quotes, risk vectors, repo and financing proxies, USD/CAD, OIS curves, policy expectations, and scheduled macro releases with their actual publication times and vintages. Independent inventory/capacity observations are valuable but may be unavailable; in that case retain predictive latent-state labels.

Estimate the behavior on multiple horizons rather than assuming a single scale: event-time response, short clock-time transmission, and slower recovery. The horizons are experimental choices to be set using data quality and execution latency, not claims that the effect exists at a particular duration.

### 13.2 Model ladder

Compare a common-input model without direct cross-coupling; a simple fixed duration hedge and lag model; a conditional linear state-space/VAR model; the constrained two-relaxation response; a few internal modes; an active capacity/feedback extension; and only then a broad relaxation measure or extended graph. Conventional models are controls that can falsify the value of the structural proposal.

Fit contract observation and common-shock components first, while carrying their uncertainty into the dynamic estimation. Avoid fitting a drifting target so freely that it can explain every residual, or forcing it to be fixed so that genuine country-specific drift is falsely attributed to liquidity memory. Evaluate profile likelihood and sensitivity across alternative target restrictions.

Split by whole chronological event windows and contract regimes. Purge observations whose feature, state-initialization, or target windows overlap across splits. Learn feature scaling, modal count, relaxation priors, and threshold selection on training data. Filtering initialization must use past data only. Never use realized future quote updates, completed order lifetimes, future CTD labels, or a full-sample volatility fallback in an earlier feature.

Assess held-out likelihood, calibrated response intervals, sign and magnitude of executable cash gains, and incremental value relative to the model ladder. Evaluate robustness to timestamp aggregation, quote-age controls, stale-price exclusion, factor neutrality, frozen versus adaptive hedges, CGB–TN maturity controls, CTD/roll exclusions, and different macro-release families. Trading evaluation must cross the actual bid–ask, model partial fills and legging, and include delayed reaction and capacity.

No number of ADF/KPSS tests alone verifies a latent response operator. Repeated selection of a hedge to make a series look stationary changes the distribution of subsequent test statistics. Economic cointegration, causal demeaning, and a tradable self-financing gain process must be assessed separately.

### 13.3 Computational architecture

The computational realization separates observation, representation, exposure accounting, transition dynamics, inference, and execution. This separation keeps a change in the measurement model from being mistaken for a change in the economic state and makes the resulting predictions reproducible.

| Component | Role | Required specification |
| --- | --- | --- |
| Market observations | Traded pair with wider identification controls | Contract-aware data, decimal ticks, as-of deliverables, DV01, FX, exchange times, and receive times |
| Multiscale representation | Observation and memory features | Separate flow and depth recovery from return features; define proxy metrics accurately; estimate response scales using past information |
| Exposure accounting | Risk observation chart and executable hedge | CTD and key-rate sensitivities, rebalancing, collateral, and a cash-gains ledger; separate displacement, filtered residual, and P&L |
| Transition dynamics | Mode switching and hybrid contract dynamics | Conditional transitions, empirical holding times, uncertainty, and sampling-interval consistency |
| State inference | Filtered state, response operator, target uncertainty, and action feedback | A small observable realization, identifiable parameters, explicit probability models, and comparisons between restricted and unrestricted dynamics |
| Decision and execution | Executable forecasts and constrained allocation | Native-currency P&L, costs, integer contract ratios, partial fills, risk, and capacity; joint reporting of forecast and model validity |

Reproducibility requires versioned records of data, parameters, model updates, and inference outputs, together with their dependency lineage. A latest-successful-run selector is not an as-of data-vintage rule: availability timestamps, release vintages, contract charts, and model versions must remain explicit. Generated transition and observation artifacts should retain the definitions and data versions from which they were produced.

For a continuous-time Markov approximation, estimate a valid rate generator Q with nonnegative off-diagonal entries and zero row sums, then use P_delta=exp(delta Q) for a new observation interval. An arbitrary discrete transition matrix need not be embeddable in such a generator. If empirical holding times are not exponential, use a semi-Markov or duration-augmented state model. Reusing a daily persistence probability at an intraday frequency changes the implied relaxation time and cannot preserve the operator.

This architecture defines the empirical realization of the inverse problem. Its specification does not by itself establish calibrated CGB–ZN dynamics or executable trading performance; those conclusions require the identification and evaluation procedures described above.

## 14 Numerical verification and reproducibility

Eleven synthetic checks verify the algebra and counterexamples underlying the framework. They cover beam force and moment balance, differential step-response shape, equality of a hidden-state realization and its reduced transfer function, the storage inequality in equation (32), external forcing in the energy balance, stable transient amplification, different responses at equal observed displacement, the feedback stability boundary, graph compatibility projection, similarity nonidentifiability, and adaptive-hedge gain geometry. All eleven checks pass; the numerical results are recorded in the [supplementary verification results](verification_results.md).

The [differential response figure](differential_response.png) illustrates static cancellation with transient relative displacement. The [internal-state and amplification figure](hidden_state_and_amplification.png) shows how different internal states produce opposite responses from the same observed displacement, and how a stable directed realization produces a peak amplification of approximately 2.08 in its fixed standardized metric.

All numerical coefficients and trajectories are synthetic and dimensionless except the stated beam dimensions. They verify mathematical identities and illustrate possible behavior. They do not estimate CGB–ZN parameters, demonstrate market causality, establish trading performance, or validate a biological specimen.

The [verification script](verify_derivations.py) reproduces the calculations using NumPy, SciPy, and Matplotlib. Running `python verify_derivations.py` produces the numerical results and standalone figures.

## 15 Discussion and research implications

At a given contract chart and slowly varying economic target, the response of CGB and ZN to new information may depend on a low-dimensional set of internal relaxation and capacity states. These states may be identified from prices plus independent flow, replenishment, funding, and contract observations. If the inferred states predict different executable future responses at otherwise similar observed displacement, and the prediction survives common-news controls and stronger conventional baselines, the response operator contains economically useful structure.

The biological contribution is a method of constructing and restricting that operator: derive the distributed dynamics, enforce genuine conservation and feasibility conditions, eliminate internal variables without discarding memory, and identify which global responses cannot satisfy all local preferences simultaneously. The financial contribution must be established by identification and new-event prediction. A successful theory would connect measured architecture to a transferable response law; a failed theory would identify exactly which proposed conservation, reciprocity, memory, or compatibility property the markets do not preserve.
