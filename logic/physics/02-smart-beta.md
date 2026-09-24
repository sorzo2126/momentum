---
author: Karim Khemiri
organization: Khem Kapital — société de R&D en finance
---

# Smart Beta

Most people want "a signal."

Something to hear in the crowd—an insider tip, a faster feed, a micro-edge. I do the opposite: I don't look at an individual in the stadium... I look at the mass.

Instead of following a single trajectory (wi(t)), I describe the market as a distribution:

$$\rho(w, t) \quad \text{where} \quad \int_\Omega \rho(w, t) \, dw = 1$$

ρ(w,t) is literally a capital heatmap: where the crowd concentrates, where it empties out, where it piles up.

Then, I make a choice that changes everything: I don't define (w) as "weights in 500 stocks."

That is impossible to observe. I define (w) as a small vector of exposures, because that is where constraints actually bite

$$w = (\text{duration}, \beta_{equity}, \beta_{credit}, \beta_{inflation}, \beta_{commod/energy}, \beta_{FX\ carry/EM})$$

This is what makes the model operational: I'm not guessing "which stock." I'm reading "which exposure is currently being selected."

From there, I describe the market as a penalty landscape.

Actors don't "choose" in a moral sense; they slide mechanically under constraint.

The terrain is defined by the Hamiltonian

$$H(w, \rho_t, F_{Z,t}) = -w \cdot F_{Z,t} + \frac{\gamma}{2} |w|^2 + \lambda (K * \rho_t)(w)$$

The first term, − w · F, is the thrust: a macro forcing that makes certain exposures advantageous and others toxic.

The term

$$\frac{\gamma}{2} |w|^2$$

is the structural cost: the further I go, the more I pay. This is where leverage eventually gets punished.

And λ (K * ρ) is the microstructure reality: the crowd compressing into the same zone and manufacturing its own penalty. Crowding, impact, propagation.

The individual dynamics become:

$$dw_t = -\nabla_w H(w_t, \rho_t, F_{Z,t}) \, dt + \sqrt{2D_t} \, dB_t$$

And the crowd dynamics:

$$\partial_t \rho = \nabla_w \cdot \left(\rho \nabla_w H(w, \rho_t, F_{Z,t})\right) + D_t \Delta_w \rho$$

And I do not treat Dt as a decorative parameter. It is the temperature of the system: agitation, internal disorder, dispersion.

When Dt explodes, the structure melts, diffusion dominates, and exits become messy. It is not "psychology."

It is mechanics.

Now I pose a definition that no one says clearly, because it forces one to think: smart beta.

Smart beta is a semi-passive portfolio that does not just follow "the index," but tilts voluntarily toward a premium: value, momentum, quality, low vol, carry.

A premium here is a long-term statistical excess paid for carrying a specific exposure with a specific risk.

In my language, smart beta is a shape in the exposure space.

A template:

$$\rho_{SB}(w, t) \approx \rho_{SB}(w)$$

It works as long as the effective law remains compatible with this shape.

Except the law is not eternal. The dominant constraint can switch. And when it switches, it is not just that "the premium disappears."

It is that the premium becomes incompatible with the new penalty landscape.

That is what "out of play" means.

I treat the four quadrants as a real law, not as a pretty matrix.

It does not tell me "how to comment on macro."

It tells me "which constraint is currently selecting the winners."

I do not need a macro novel.

I need two directions: the acceleration of activity

$$(a_g(t))$$

nd the acceleration of inflation

$$(a_\pi(t))$$

The quadrant is just the sign of these two objects

$$Q(t) = (\text{sign}(a_g(t)), \text{sign}(a_\pi(t)))$$

When the quadrant changes, it is not a nuance: the forcing F{Z,t} changes, sometimes Dt changes, sometimes even the kernel K changes because liquidity no longer has the same geometry.
I take a concrete example: inflationary boom. Activity accelerates and prices accelerate. Everyone says "everything goes up."

I read a dominant constraint: the cost of capital becomes the variable that will bite.

Even if the market can continue for a while, the direction is fixed: inflation pushes nominal yields and discount rates upward, so duration becomes a dangerous exposure. Not moral. Not opinion. Discounting.

So the forcing looks like this: it rewards exposures that absorb inflation and it penalizes duration.

$$F_{Z,t}^{(IB)} : (+\beta_{inflation}, +\beta_{commod}) \text{ and } (-\text{duration})$$

That is exactly why long bonds get crushed in these regimes: no one locks up liquidity for 10 years to pick up 1–2% while inflation accelerates and the cost of capital reprices. It is not "psychological." It is the penalty landscape that makes the position unstable.

And on the other side, stores of value emerge: energy, commodities, gold, real estate, cyclical producers with pricing power. Not because it is "sexy." Because these exposures mechanically absorb the inflation constraint.

And then something almost always happens: the longer the inflationary boom lasts, the more multiples stretch. And as soon as rates and the cost of capital rise enough, the compression starts. The punishment hits everything that is long duration or without pricing power. Once again: no judgment. Penalty.

In the equation, this can be seen in two ways.

First in the term  − w · F the slope turns against duration.

Then in lambda λ (K * ρ) the crowd packs into the same zones (same themes, same trades), the crowding penalty rises, and the slightest shock propagates execution cost.

The constraint does not just select: it makes the transition violent.

And when the regime becomes rate-sensitive, Dt tends to rise: dominant diffusion, melting structure, exits that become cliffs.

So when someone asks me "why didn't smart beta hold?", I do not answer with slogans.

answer with the logic of the model: smart beta carried a premium compatible with an old forcing.

The constraint switched. The template ρ_SB(w)

became a granite block placed on a floor that started to tilt.

Not "wrong." Just out of play. I read the three other quadrants the same, but I do not treat them like forum categories.

I treat them as three other effective laws, three other penalty landscapes. When growth slows but inflation remains high, the system enters a double bind: inflation says "tighten," activity says "do not tighten."

Duration remains penalized, but equity beta gets punished too because growth breaks.

Nominal promises and long-duration valuations are dismantled, and credit starts pricing default.

The dominant penalty becomes a squeeze on real income and funding instability. When growth accelerates and inflation decelerates, it is the opposite world: duration is rewarded, multiples can expand, financing remains soft.

This is where smart beta premiums look "universal."

In reality, it is just a quadrant where the forcing is compatible with many templates, so ρ_SB looks smart.

The trap is that crowding rises in silence and fragility accumulates.

The punishment arrives when the constraint switches.

And when growth slows and inflation decelerates, the constraint becomes survival-by-liquidity: cash, quality sovereign duration, safe haven.

Credit spreads widen, equity beta is punished, cyclicals are crushed.

The penalty is not "I was wrong." The penalty is "I did not have the right to be exposed to that." And I close the loop on the only thing that matters

$$\alpha(t) = -d\mathcal{F}/dt \geq 0$$

For me, alpha is not an eternal property of a factor. It is the speed of adaptation of the system under the current constraint.

So when the constraint switches, my strategy does not "make a mistake." It just becomes out of play.
