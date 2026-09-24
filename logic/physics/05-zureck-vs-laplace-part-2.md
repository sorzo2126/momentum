---
author: Karim Khemiri
organization: Khem Kapital — société de R&D en finance
---

# Zureck vs Laplace - Part 2

We start with Zurek, because it immediately puts the right idea on the table probability is not an opinion.

It is a consequence of a structure that holds under constraint.

In his framework, you take an open system (S) and couple it to an environment (E).

An environment in the physical sense that which couples to you, measures you, and kills your illusions.

The total Hamiltonian is

$$H = H_S + H_E + H_{int}$$

And the evolution is unitary

$$U(t) = \exp(-iHt/\hbar)$$

At first, you might think "Okay, everything is reversible, everything is clean."

Except you don't observe the whole; you observe the system.

So, you trace out the environment and look at what remains

$$\rho_S(t) = \text{Tr}_E[U(t) \rho_{SE}(0) U^\dagger(t)]$$

Then comes the real shock: decoherence.

Not as a mystical word, but as a filter.

E measures S in a basis {|s_i|} and whatever is not compatible practically disappears.

The off-diagonal terms vanish

$$[\rho_S(t)]_{ij} = c_i c_j^* \Gamma_{ij}(t) = \langle \epsilon_j(t) \mid \epsilon_i(t) \rangle \rightarrow 0 \quad (\text{for } i \neq j)$$

you can have plenty of superpositions in your head, but the world forces a readable basis upon you. What "survives" are the pointer states because they are stable under the coupling.

Zurek is very clear here: pointer states are not chosen by the observer. They are selected by the structure einselection.

Essentially, you keep the projectors compatible with the coupling

$$[H_{int}, P_{i_k}] = 0$$

And you add the "predictability sieve" layer those that minimize entropy production.

It's the same idea as in risk lessons as long as the constraint dissipates, you remain readable.

When the constraint saturates, you change the law. Next, objectivity.

Why do multiple observers "see the same thing"?

Because the environment acts as a witness it copies, it redunds, it imprints.

You can measure this via the mutual information between S and a fragment F subset E

$$I(S : F) = H(S) + H(F) - H(S, F)$$

If a small fraction of E is enough to reconstruct almost all information about S, you reach a plateau in I(S:F).

That means redundancy.

It means "readable by multiple readers simultaneously."

As long as that plateau holds, the effective law holds. If it breaks, you don't have a psychological nuance; you have a regime change. And now the point that really interests us: Born's Rule.

Not "postulated," but derived from an invariance envariance.

Take an entangled state

$$|\Psi\rangle = \sum_k a_k |s_k\rangle \otimes |e_k\rangle$$

You use the idea that you can permute the S side and compensate on the E side without changing the global state.

Therefore, when |a_k| = |a_l|, you impose equiprobability.

Refining the general case gives you

$$p_k = |a_k|^2$$

That is the message probability is a physical property of a system under invariances, not an observer's belief.

In our markets, the "environment" isn't Twitter or the narrative.

It is the constraint. It is what reduces the space of possible actions. Exactly like a man at gunpoint: you don't have "all the options"; you have the law that the constraint permits.

So, we manufacture the operational environment: we construct a stationary spread by opposing compatible forces. Simple example: real assets versus duration.

We write

$$S_t = R_t^{(+)} - \beta_t R_t^{(-)}$$

With a local hedge ratio

$$\beta_t = \frac{\text{Cov}(R^{(+)}, R^{(-)})}{\text{Var}(R^{(-)})}$$

What this forces is clear: as long as the regime invariance holds, St oscillates around a center and maintains a bounded variance.

This is your market pointer state.

Not because it is "stable" in the sense of comfort, but stable in the sense of being readable, reproducible, and exploitable

$$\mathbb{E}[S_{t+1} \mid \text{regime}] \approx 0$$

The analogy holds the spread "measures" your position.

It reflects what the structure allows, not what you say.

The effective law here is stationarity as long as the regime constraint is not violated.

But beware this is where people fail: alpha is not hidden in the stationarity.

Stationarity is the reference frame.

Alpha appears when a force becomes visible within that reference frame. Just like in physics: as long as it is absorbed, the resultant is approx to 0.

When it is no longer absorbed, you see a bias. We formalize the macro dynamics properly, in discrete time, because in trading you decide at t and endure at t+1.

No circularity.

Discrete derivative of inflation and acceleration

$$\dot{\pi}_t = \pi_t - \pi_{t-1}$$

$$\ddot{\pi}_t = \pi_t - 2\pi_{t-1} + \pi_{t-2}$$

Available money supply

$$M_t$$

Macro force cause to effect

$$F_{t+1} = M_t \times \ddot{\pi}_t$$

Direct reading: as long as F is small, the invariance absorbs it, and you remain in "centered spread" mode

$$\mathbb{E}[S_{t+1}] \approx 0$$

When F accelerates and crosses a threshold, you don't change your mind you change the law.

The invariance deforms, and a drift appears in the spread.

You write it as

$$\mu_t \approx \gamma_t F_t$$

You calibrate

$$\gamma_t$$

locally on a window where the regime is stable otherwise, you repeat the Laplacian error believing your mean is a fixed reference when it actually moves with the constraint.

There is your complete bridge:

Breakdown of effective law to neutral spread becomes biased spread to measurable surplus.
The force propagates through specific regimes:

Inflationary Boom Activity + prices accelerate, long rates rise, duration is penalized, real assets have the advantage. The "reals vs. duration" spread drifts toward reals.

Disinflationary Boom: Activity holds, cost pressure slows, duration becomes an asset again, long-duration growth stocks catch up. The drift can flip.

Disinflationary Bust: Activity receding, prices cooling, flight to quality, long bonds and defensives lead.

Inflationary Bust / Stagflation: Maximum constraint, compressed margins, scarce liquidity. Only very selective pockets survive. The rest is "constrained." The rule of action remains the same: you look for mu_t is not equal to 0 in an object that was centered.

Once you have this, you follow the logical progression of risk: measure risk within the spread's reference frame, not on the raw price, or you'll mix different laws and tell yourself a story.

## Local Gaussian Risk

$$\text{VaR}_p^{(G)} = \mu + \sigma z_p$$

$$\text{ES}_p^{(G)} = \mu - \sigma \frac{\phi(z_p)}{1 - p}$$

$$z_p = \Phi^{-1}(p)$$

And at the regime edges, where things truly break, you switch to EVT (Peaks Over Threshold):

$$(Y = S - u \mid S > u) \sim \text{GPD}(\xi, \beta)$$
