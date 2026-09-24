---
author: Karim Khemiri
organization: Khem Kapital — société de R&D en finance
---

# Zureck vs Laplace

Trading remains a game of probability... but if you treat probability as a belief about what you don't know... then you will just import a narrative into your OHLC series... and that narrative moves faster than your models.

From Laplace's point of view, it is simple: probability comes from counting "equally possible" outcomes... decided by the observer.

This framework works... as long as the narrative held by a participant—who has the capacity to turn everything around still holds.

Except that a real market is reflexive: the agent acts... therefore the rule changes.

Zurek's interpretation is much more suitable: probability is not a bet... it is a property of the system... when certain symmetries hold.

And alpha does not emerge from a narrative... alpha emerges from forces... and thresholds.

We position ourselves in discrete time

$$t \in \mathbb{N}$$

on the structure

$$(\Omega, \mathcal{F}, (\mathcal{F}_t)_{t \geq 0}, P)$$

Ft is the observable information at the end of t.

And every decision is Ft predictable... no look-ahead.

Randomness is not "what you don't know"... randomness is what the system allows... under constraints.

The three decisive constraints: maximum leverage before liquidation... executable liquidity (depth / speed)... and signal-price divergence.

They play the role of decoherence they remove unstable... or desynchronized structures.

Therefore, operational probability is backed by an invariance as long as the configuration remains compatible with these constraints, certain regularities remain stable.

As soon as a threshold is crossed... the law changes.

To measure what is truly pushing the system, we measure a macro forcing

$$F_{t+1} = M_t \times \ddot{\pi}_t$$

$$\dot{\pi}_t = \pi_t - \pi_{t-1}$$

$$\ddot{\pi}_t = \pi_t - 2\pi_{t-1} + \pi_{t-2}$$

The calculation is done at t... the action at t+1 (anti-circularity).

Mt represents the money supply; pi_t is the second derivative of inflation.

As long as the structure absorbs the forcing, the resultant remains zero on average; when the absorption yields... the force becomes visible.

The propagation is classified by regimes by crossing the observed real growth g_t and the forcing F_t

$$Q_{t+1} = \begin{cases} 1 & \text{if } g_t > 0 \text{ and } F_t > 0 \\ 2 & \text{if } g_t > 0 \text{ and } F_t \leq 0 \\ 3 & \text{if } g_t \leq 0 \text{ and } F_t \leq 0 \\ 4 & \text{if } g_t \leq 0 \text{ and } F_t > 0 \end{cases}$$

Each quadrant has a margin of coherence,

defined by

$$\delta_g$$

and

$$\delta_F > 0$$

$$\text{sgn}_\delta(x) = \mathbf{1}_{x > \delta} - \mathbf{1}_{x < -\delta}$$

As long as

$$\text{sgn}_{\delta_g}(g_t)$$

and

$$\text{sgn}_{\delta_F}(F_t)$$

remain constant... the internal law holds.

As soon as

$$|g_t| \leq \delta_g$$

or

$$|F_t| \leq \delta_F$$

the system enters a boundary zone... where the law can change.

## Quadrant interpretation

$$(g_t > 0, F_t > 0)$$

👆 Q1: Energized system, real assets rise, duration is punished.

$$(g_t > 0, F_t \leq 0)$$

👆 Q2: Soft dissipation, long-term growth dominates.

$$(g_t \leq 0, F_t \leq 0)$$

👆 Q3: Cold regime, flight to quality.

$$(g_t \leq 0, F_t > 0)$$

👆 Q4: Harshest constraint, costs rise while activity weakens.

Let

$$r_t = (r_t^1, \ldots, r_t^N)^T$$

be the returns of compatible assets, and here the duration leg.

$$r_t^B$$

We define:

$$w_t \in \arg\max_{w \in \Delta^{N-1}} \text{Cov}(w^T r_t, F_t)$$

$$R_t^+ = w_t^T r_t$$

$$R_t^- = r_t^B$$

Resultant of the same regime

$$\beta_t = \frac{\text{Cov}(R_{t-W+1:t}^+, R_{t-W+1:t}^-)}{\text{Var}(R_{t-W+1:t}^-)}$$

$$S_t = R_t^+ - \beta_t \times R_t^-$$

If the quadrant margin is respected and no external constraint saturates, then

$$\mathbb{E}[S_{t+1} \mid F_t, Q_{t+1} = \text{const}] = 0$$

$$\text{Var}(S_{t+1} \mid F_t, Q_{t+1} = \text{const}) = \sigma_t^2 < \infty$$

This defines physical stationarity: two forces from the same regime offset each other... and you obtain an oscillation around a zero mean...

with bounded variance.

Laws emerge just like in physics: stable as long as invariances hold... and they change as soon as thresholds break.

The force becomes apparent when St carries a bias mu is not equal at 0.

## Detection via sequential test

$$H_0 : S_t \sim \mathcal{N}(0, \sigma_t^2)$$

$$H_1 : S_t \sim \mathcal{N}(\mu, \sigma_t^2), \mu \neq 0$$

Cumulative log-likelihood

$$\Lambda_t = \sum_{k=t_0}^{t} \ln\left[\frac{f_{H_1}(S_k)}{f_{H_0}(S_k)}\right]$$

Decision rule

$$\Lambda_t \geq A \rightarrow \text{accept } H_1$$

$$\Lambda_t \leq B \rightarrow \text{accept } H_0$$

Otherwise... we wait, with

$$A = \ln((1 - \beta) / \alpha)$$

$$B = \ln(\beta / (1 - \alpha))$$

which encode the error rates alpha, beta.

The system's variety is measured by the Shannon entropy of the spread

$$V_D(t) = H(S_{t-L+1:t})$$

$$V_R = \ln(3) \quad (\text{long, flat, short})$$

Ashby's law if Vd (t) > Vr... do not act.

## Decision

$$u_t = \mathbf{1}_{\{Q_{t+1} \text{ held}\}} \times \mathbf{1}_{\{\Lambda_t \geq A\}} \times \mathbf{1}_{\{V_D(t) \leq V_R\}} \times \text{sign}(S_t)$$

Profit and loss, accounting for execution

$$\text{PnL}_{t+1} = u_t \times S_{t+1} - c_t$$

$$c_t = c_0 + c_1 \times |u_t - u_{t-1}|$$

And here you return to the central point alpha is not stationarity;

it is the excess when the apparent force is detected... and dissipation remains controllable.

## Regime benchmark

$$B_t = R_t^+$$

$$\alpha_T = \frac{1}{T} \sum_{t=1}^{T} (\text{PnL}_t - B_t)$$

## Forces generating alpha

Macro force

$$F_{t+1} = M_t \times \ddot{\pi}_t$$

👆 creates a directional bias.

Microstructural absorption decides whether the bias becomes movement.

The leverage constraint modulates the speed of propagation.

Liquidity amplifies or dampens the impulse.

Signal-price divergence shows undigested information.

Alpha appears when these forces align in a stable quadrant... and disappears when its margins or its control break down.
