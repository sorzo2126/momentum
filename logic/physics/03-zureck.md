---
author: Karim Khemiri
organization: Khem Kapital — société de R&D en finance
---

# Zureck

Imagine I throw you into a stadium full of people... everyone is screaming at the same time.

And your job is to find a BUY or SELL signal... by listening to one random guy in the crowd.

That is the obsession with the "micro-signal": you take two or three trajectories, two or three "smart actors," two or three fast flows... and you act as if that were the market.

In econophysics, we do the opposite. We stop following an individual... and we follow the mass.

So instead of worshipping a single path, we describe the market with a single object

$$\rho(w, t)$$

Read this as: "at time (t), how much capital is sitting near a position (w)." It's a heatmap of capital.

Cold zones = empty.

Hot zones = crowding.

And yes:

$$\int_\Omega \rho(w, t) \, dw = 1$$

And here, there is something that flips the critics on their heads.

People will tell you: "your physics metaphor has its limits. Markets are not ergodic. They can stay stuck in bubbles."

Perfect.

That's not a flaw. That's exactly the point.

$$\rho_{eq}(w) \propto \exp\left(-\frac{H(w, F, \rho_{eq})}{D}\right)$$

is not a promise that the market reaches equilibrium like a gas in a box. It's a frame of reference: "if the forcing froze, toward what shape would the mass relax?"

Except a market does not relax gently. It's not a closed lab system. It's a survival machine under constraint. It can stay in a metastable state (a bubble) until a constraint snaps... and then the "relaxation" isn't a slope, it's a cliff.

So the model doesn't need ergodicity to be useful. It needs something else:

Effective laws.

And an effective law is not eternal.

That's the central idea: the framework remains... but the dominant constraint can switch.

Sometimes the constraint is macro. Sometimes it's liquidity. Sometimes it's leverage tolerance. Sometimes it's latency. Sometimes it's chains of forced liquidations.

So

$$F = M \cdot \ddot{\pi}$$

👆 is not "THE law."

It is an example of forcing within a larger rule:

The dominant constraint defines the effective law.

And in practice, you write it zone by zone:

$$F_{Z,t} = M_{Z,t} \cdot \ddot{\pi}_{Z,t}$$

with

$$Z \in \{US, UK, EZ\}$$

And tomorrow, your forcing might become another (F'_{Z,t}) because a different constraint has become dominant.
That's what makes the thing robust: you aren't married to an equation.

You are modeling selection under constraint.

Now, the penalty landscape.

You don't say "people choose." You say "people slide."

The terrain is

$$H(w, \rho_t, F_{Z,t}) = -w \cdot F_{Z,t} + \frac{\gamma}{2} |w|^2 + \lambda (K * \rho_t)(w)$$

And again, critics will say: "your temperature (D) is not constant.

In a crisis, it explodes." Exactly.

D is not a decorative parameter. It is the internal agitation of the system, its disorder.

So you don't treat it as a constant.

You treat it as part of the effective law D → Dt (regime-dependent).

Then the movement becomes:

$$dw_t = -\nabla_w H(w_t, \rho_t, F_{Z,t}) \, dt + \sqrt{2D_t} \, dB_t$$

and the transport of the crowd becomes

$$\partial_t \rho = \nabla_w \cdot \left(\rho \nabla_w H(w, \rho_t, F_{Z,t})\right) + D_t \Delta_w \rho$$

when Dt explodes, the crowd doesn't become "irrational" in a moral sense.

The temperature rises. Diffusion dominates. The structure melts. The exits get messy.

It's Ashby law, not psychology: without noise, no variety; without variety, no adaptation.

And now, the big operational attack: Okay, but how do you measure ρ(w,t)?

You don't know everyone's portfolios."

Yes.

And it's still not a flaw.

In physics, you don't track every molecule. You infer a distribution from observables.

Same here: ρ is a hidden state. You estimate it by what leaks into the tape: flows, open interest, positioning proxies, order flow pressure, liquidity maps.

And above all: you don't need ρ in full of Rd and you choose the right coordinates for (w).

If w = weight of every asset, you're dead.

If w = "factor exposures" (duration, energy, credit beta, equity beta, inflation beta), it becomes manageable.

So the practical move is: you redefine w as a low-dimensional exposure vector, then you infer ρ (w,t) using proxies.

Next, they'll say: "your kernel (K) is arbitrary." No. K is not decoration.

K is the microstructure transfer function: how crowding in one spot creates cost pressure elsewhere.

And yes, choosing K matters... because liquidity is precisely the constraint that makes the market "physical." So you don't choose K "to taste."

You choose K to match observed propagation: local crowding, sector crowding, factor crowding. You impose K ≥ 0 and a shape consistent with how execution costs diffuse.

And the clean point: K can also change with the regime.

It stays perfectly aligned with the thesis:

Effective laws can change.

Now, the alpha.

They'll say:

$$\alpha(t) = -d\mathcal{F}/dt$$

s brilliant but abstract. You can't observe it."

Yes.

And that's exactly why it's powerful: it's not a magic formula. It's a target function.

It tells you what "being right" means in this world: you win when you are ahead of the reorganization path the crowd must follow under penalty.

You define a free energy:

$$\mathcal{F}[\rho] = \int_\Omega \rho(w) U(w, F) \, dw + \frac{\lambda}{2} \iint K(w-u) \rho(w) \rho(u) \, dw \, du + D_t \int_\Omega \rho(w) \log \rho(w) \, dw$$

with

$$U(w, F) = -w \cdot F + \frac{\gamma}{2} |w|^2$$

And you set

$$\alpha(t) = -\frac{d\mathcal{F}}{dt} \geq 0$$

So "physical" alpha is the speed of the system's adaptation.

So how do you trade this without pretending to observe it directly?

You trade the cause of the dissipation: the penalty gradient and the crowding constraint.

You build rules faithful to the story:

You align with the current forcing F{Z,t} (zone-specific).

You avoid concentration where λ(K*ρ_t) is already high (crowding).

You size down when Dt is high (temperature regime).

You accept that in a metastable state, the trend can last until the constraint switches: you don't try to "call the top," you monitor for the change in the dominant constraint.

And the contrarian punchline that kills the classic critique: You don't say "the market is a gas at equilibrium.

"You say: "the market is a survival system selected by constraints."

And the only edge is right there: You don't guess the direction.

You identify which constraint is currently selecting the winners... and you position yourself before the crowd is forced to move.

That is khem kapital version of econophysics: selection, not prediction.
