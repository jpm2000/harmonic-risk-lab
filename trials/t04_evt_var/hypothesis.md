# Trial 04: EVT VaR — Extreme Value Theory for Heavy-Tail Mining Losses

## What We're Testing

**Extreme Value Theory (EVT)** is the statistically correct framework for tail risk when
losses follow a power law rather than a normal distribution. Mining losses are the
canonical example: most years have many small claims, but occasionally a single event
($7B+ Brumadinho tailings collapse, multi-month mine fires) dwarfs everything else.

The problem with normal/lognormal VaR in this setting: **it systematically underestimates
the tail**. You'd compute a 99.5% VaR of, say, $200M — but the true 99.5% loss could be
$1B+. The difference is the capital a mining insurer doesn't hold.

**Paper:** McNeil, A.J., Frey, R. & Embrechts, P. (2005). *Quantitative Risk Management:
Concepts, Techniques and Tools.* Princeton University Press. Chapter 7 (Extreme Values).

**Marsh data context:**
- Fire/explosion = 25.7% of $15.3B losses over 20 years
- Geotechnical + tailings = catastrophic individual events (Brumadinho = $7B+ settlement)
- These are NOT normally distributed. No normal model would ever produce a $7B single event.

---

## The Math

### Why Normal VaR Fails for Mining

Normal VaR: `VaR_α = μ + z_α · σ`

For a normal distribution, the tail decays exponentially — events become impossible very
fast. But mining losses have a **power-law tail**: a $7B event is unlikely but not
astronomically unlikely. It happened in 2019.

### Generalized Pareto Distribution (GPD)

The Pickands-Balkema-de Haan theorem says: for any distribution with a heavy tail,
excess losses above a high threshold `u` converge to a GPD regardless of the
underlying loss distribution.

GPD parameters:
- `ξ` (xi) = **shape / tail index**. When `ξ > 0`, the tail is heavy (power-law). The
  bigger `ξ`, the heavier the tail. Mining: `ξ ≈ 0.3–0.7` is typical.
- `σ` (sigma) = scale parameter
- `u` = threshold (only losses above `u` enter the GPD fit)

### VaR Formula (Peaks-over-Threshold)

```
VaR_α = u + (σ/ξ) · [(p_u / (1-α))^ξ − 1]
```

where:
- `p_u` = P(X > u) = empirical exceedance probability = N_u / N (number of exceedances / total)
- `α` = confidence level (e.g., 0.995 for Solvency II)

**Step by step:**
1. Choose threshold `u` (e.g., $10M for a mining portfolio)
2. Fit GPD to all losses above `u` → get `ξ` and `σ`
3. Count `N_u` = how many losses exceeded `u`, compute `p_u = N_u / N`
4. Plug into the formula

### ES (Expected Shortfall) Formula

```
ES_α = (VaR_α + σ − ξ·u) / (1 − ξ)      requires ξ < 1
```

This is the average loss given you're already above VaR. Requires `ξ < 1` for a finite
expected value. If `ξ ≥ 1`, the expected loss above VaR is literally infinite — the
distribution has no finite mean in the tail.

---

## Properties We Want Aristotle to Prove

1. **`gpd_var(u, sigma, xi, p_u, alpha) >= u`**
   VaR must be above the threshold. Below the threshold, the GPD doesn't apply.
   If VaR < u, the model returns a result in a region where it's undefined.

2. **`gpd_es >= gpd_var` (coherence)**
   ES is always ≥ VaR. This is the central property of Expected Shortfall as a
   coherent risk measure (Artzner, Delbaen, Eber & Heath, 1999).
   If this fails, the capital model understates tail risk.

3. **`gpd_var` monotone in `alpha`**
   Higher confidence level → higher VaR. If VaR at 99.5% < VaR at 99%, the model has a bug.

4. **`evt_tail_premium >= 0` when `xi > 0`**
   EVT VaR ≥ Normal VaR when the tail is heavy. This is the mathematical proof that
   mining insurers need *more* capital than a textbook normal model would suggest.

---

## Why This Matters for bluberri

Every bluberri mining client needs to answer: "How much capital should we hold?"
The Solvency II answer is `VaR(99.5%)`. If you compute this with a normal distribution
and the true losses are Pareto-tailed, you are **systematically undercapitalized**.

This trial formally proves that the EVT capital model is always conservative relative
to the normal model — not just for the fitted parameters, but for ALL valid inputs.

That's the guarantee bluberri can offer: "Our capital model never underestimates tail risk."

---

## Expected Outcome

Properties 1–3 should be provable directly from the formula's algebraic structure.
Property 4 is the most interesting: it requires Aristotle to reason about the relationship
between two different VaR formulas across all valid parameter combinations.

If Aristotle finds a counterexample on Property 4, it means there's a parameter region
where normal VaR actually exceeds EVT VaR — worth investigating if so.
