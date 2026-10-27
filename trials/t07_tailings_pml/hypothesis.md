# Trial 07: Tailings Dam PML — Probable Maximum Loss via Return Period

## What We're Testing

From the Marsh report:

> "The 2015 Fundão tailings-dam collapse at Samarco's Mariana mine and the
> 2019 Brumadinho dam disaster in Brazil illustrate the potential scale of such
> losses. The latter resulted in many casualties and prompted a settlement with
> Brazilian authorities for over US$7 billion."

Tailings facilities represent only ~0.7% of loss frequency in the Marsh database,
yet they produce the largest single losses ever recorded in mining insurance history.
This is a classic **rare + catastrophic** risk profile — the kind that breaks every
model calibrated to "average" years.

**Probable Maximum Loss (PML)** is the actuarial concept for this: the largest loss
expected to occur within a given return period `T` years. `PML(T = 100)` means
"the worst loss we expect to see once every 100 years."

**Source:** McNeil, Frey & Embrechts (2005). *Quantitative Risk Management.* Ch. 7.
Pickands (1975) for generalized extreme value distributions. Brumadinho (2019) as
the canonical real-world calibration point.

---

## The Math

### Return Period and Exceedance Probability

For a loss distribution, the **annual exceedance probability** for loss level `x` is:
```
p(x) = P(annual loss > x) = 1 - F(x)
```

The **return period** `T` for loss `x` is:
```
T = 1 / p(x)  years
```

So a 1-in-100-year event has `T = 100` and `p = 0.01 = 1%` annual probability.

### PML via Pareto Severity

For tailings events, the severity distribution follows a Pareto (power-law) shape.
Given Pareto parameters `(alpha, x_m)` where `x_m` is the minimum loss:

```
P(X > x) = (x_m / x)^alpha    for x >= x_m
```

Inverting for the `T`-year PML:
```
PML(T) = x_m × T^(1/alpha)
```

This grows as a power of `T`, meaning tail events are much larger than the
annual average suggests. At `alpha = 1.5` (typical for catastrophic events):
- 10-year PML = x_m × 10^(0.67) = x_m × 4.6×
- 100-year PML = x_m × 100^(0.67) = x_m × 21.5×
- 1000-year PML = x_m × 1000^(0.67) = x_m × 100×

For Brumadinho ($7B settlement, return period estimated ~200 years in Brazilian mining):
- `x_m ≈ $50M` (minimum tailings event)
- PML(200) ≈ $7B → implies `alpha ≈ 1.3`

### Annual Exceedance Probability

Given the Pareto model:
```
aep(x, x_m, alpha) = (x_m / x)^alpha    for x >= x_m
```

The probability of exceeding $7B in any given year is:
```
p = (50 / 7000)^1.3 ≈ 0.003 = 0.3% per year
```

---

## Properties We Want Aristotle to Prove

1. **`pml_pareto >= x_m`** for all valid `(x_m, alpha, T)` with `T >= 1`
   PML is always at least the minimum loss. No return-period calculation can
   produce a result below the smallest observed event.

2. **`pml_pareto` monotone in `T`** (longer return period = larger event)
   If `T1 >= T2 >= 1`, then `pml_pareto(x_m, alpha, T1) >= pml_pareto(x_m, alpha, T2)`.
   A 200-year event is always at least as large as a 100-year event.

3. **`aep` monotone decreasing in `x`** (larger losses are rarer)
   If `x1 >= x2 >= x_m`, then `aep(x1) <= aep(x2)`.
   The bigger the loss, the lower its annual probability.

4. **`aep` in `(0, 1]` for valid inputs** (`x >= x_m > 0`, `alpha > 0`)
   Annual exceedance probability is always a valid probability.

5. **`pml_pareto` and `aep` are consistent inverses**
   `aep(pml_pareto(x_m, alpha, T)) = 1/T` — the AEP of the T-year PML is
   exactly 1/T. This is the definitional consistency property.

6. **`pml_pareto` monotone decreasing in `alpha`**
   Higher tail index `alpha` = lighter tail = smaller T-year PML.
   `alpha1 >= alpha2 > 0` implies `pml_pareto(x_m, alpha1, T) <= pml_pareto(x_m, alpha2, T)`.

---

## Why This Matters for bluberri

A mining client asking "what should our maximum foreseeable loss be?" needs PML.
The Solvency II framework requires insurers to hold capital for a 1-in-200-year event.

For tailings facilities specifically: if a mine has a tailings dam, the PML is often
the largest single number in their entire risk profile — larger than all other perils
combined. A bluberri risk report must correctly compute and display this.

This trial formally proves that the PML model is internally consistent — that
100-year losses are always smaller than 200-year losses, and that the relationship
between exceedance probability and return period is mathematically coherent.

---

## Expected Outcome

Properties 1–4 are provable from the monotonicity of power functions.
Property 5 (consistency of PML and AEP as inverses) requires Aristotle to reason
about the composition of two functions — the most interesting property in this trial.
Property 6 requires reasoning about `alpha` as an exponent, which involves
logarithms and may be the hardest property here.
