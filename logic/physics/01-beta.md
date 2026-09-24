---
author: Karim Khemiri
organization: Khem Kapital — société de R&D en finance
---

# Beta

If in the end J.P. Morgan's alpha comes from the way they wired their entire architecture around their beta... then the only real question becomes: what is your beta?

And there, we return to the strict application of the Zurek framework we laid out before: you take a system, you fix the environment, and you ask the simplest question in the world...

What remains stable as long as no one breaks the system's invariances?

In Zurek's world, these are called pointer states.

Here, in the market, your "pointer state"... is your spread... and your quadrant.

And in our macro version, the environment isn't a vague concept. It is two things, period.

The macro regime: the inflation / growth pair.

Real constraints: what your broker lets you do, your asset universe, your leverage, your cash, your margin rules, your prohibitions.

That is your local Hamiltonian.

Once this environment is fixed, beta can no longer be "stocks go up in the long run" (that's a belief).
The beta becomes: "in this quadrant, under these constraints, here is the structure that must remain neutral if the system dissipates normally."

And concretely, it takes the form of your spread

$$S_t = R_t^+ - \beta_t R_t^-$$

And this spread, you build it in your own universe... with your ETFs, CFDs, or futures.

So if your regime is an inflationary boom... and your broker only offers ETFs...

Your beta isn't "SPX."

Your beta is something like: "long energy / short duration (via a bond ETF)"... or "long commodities / flat the rest."

The trader must be able to say, in black and white: "if inflation accelerates and Mt does not contract, this basket represents the force

$$F = M_t \times \ddot{\pi}_t$$

inside my specific environment

where

$$\ddot{\pi}_t$$

is the discrete acceleration of inflation for example

$$\ddot{\pi}_t = \pi_t - 2\pi_{t-1} + \pi_{t-2}$$

That is the definition of a realistic beta.

And once this foundation is laid, what people call "strategy"... is nothing other than the exploitation of the deformations of this beta.

That's where you stop being passive and start extracting.

Here are three concrete ways to do it.

## A. Intra-sector cointegration (macro pair trading)

If your beta tells you "the energy sector must outperform"... you don't just buy the index and pray.

You look inside. Exxon (XOM) and Chevron (CVX) are driven by the same forces.

If Exxon takes off and Chevron lags... it's not "mystical information"... it's often a flow / liquidity imbalance.

So you keep it simple: you buy the laggard, you short the leader.

You capture the convergence without adding directional risk.

That is pure alpha on top of an already validated beta.

## B. Imbalance carry (spread drift)

Sometimes the force (F) is so violent (like 9% inflation) that the spread doesn't just oscillate... it tilts.

It has a slope. It has a structural drift: mu_t > 0.T

here, your strategy isn't "ping-pong mean reversion."

You build a pyramidal position: you buy the spread, and at each volatility pullback (when your z-score returns to 0), you reload. You exploit the inertia of the system. It's what trend followers do... except you do it on a framed spread, not on a naked price.

## C. Selling convexity (synthetic knock-in)

There we go up a notch.

If you know that your spread is bounded by the regime (invariance), then at the extremes IV is often too expensive.

So instead of paying for protection, you structure: you sell puts on the strong leg (energy) to finance OTM calls... or you sell call spreads on the weak leg (tech/duration).

And you transform your regime reading into a premium harvesting machine. It's the moment where the operator truly intervenes: directional, mean reversion, option selling, carry... it's no longer divination.

It's exploiting a regime shift in a controlled reference frame. And for a small account, the rule is even stricter: instead of inventing an RSI signal out of nowhere, you wait for your "house" macro spread to give you the quadrant, you build the cleanest beta your broker allows, and only then do you choose the compensation mode: convexity, reversion, carry.

From there, talking about alpha finally becomes rigorous

Alpha is the excess generated above a beta built under constraints and consistent with your environment.

Refusing this work is to stay in the initial Laplacian model: 6 isolated assets, no framework, no force, no invariance.

Not "false"... just indefensible as soon as someone asks you two serious questions.

Conversely, if the beta is well-defined (quadrant + broker constraints + stationary spread), the causal chain is clean... In conclusion, a strategy is only reliable if it is first built from real constraints:

capital, account size, type of assets available, legal framework. A retail trader in the US, Europe, or Asia doesn't have the same access to futures, options, CFDs, ETFs, or physical gold; three different environments imply three different local Hamiltonians, therefore three betas to build...

even if the displayed benchmark is the same.

The first step is to define this structural beta in one's own universe, by selecting a basket consistent with one's region, trading hours, and legal limits.

And only then do we apply what we did in the previous lessons: treating the macro forces (Ft) as effective laws, building the spread adapted to this environment, transforming it into a stationary series, and letting the excess emerge inside this stable framework. At that point, alpha is no longer an accidental performance...

it's the surplus that comes out of a structure compatible with the constraints of the system and with the regime in which you operate.
