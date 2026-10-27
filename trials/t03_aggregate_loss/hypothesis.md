# Trial 03: Aggregate Loss Model — Compound Poisson Formulas

## What We're Testing

The **compound Poisson aggregate loss model** is the foundation of Module 4.
It says: total portfolio loss S = X₁ + X₂ + ... + Xₙ where N ~ Poisson(λ).

The key closed-form formulas that hold EXACTLY (not approximately):

```
E[S] = λ · E[X]
Var(S) = λ · E[X²]   (= λ · Var(X) + λ · (E[X])²)
```

The second formula uses the compound Poisson variance identity — a special
property that only holds because N is Poisson (so Var(N) = E[N] = λ).

For a general compound distribution: Var(S) = E[N]·Var(X) + Var(N)·(E[X])²
For Poisson specifically:            Var(S) = λ·Var(X) + λ·(E[X])²  = λ·E[X²]

Source: Curriculum Module 4 + Loss Data Analytics Ch. 3

---

## Properties We Want Aristotle to Prove

1. **`aggregate_mean(lambda, mean_x) ≥ 0`** when `lambda ≥ 0` and `mean_x ≥ 0`
   — Expected aggregate loss can never be negative.

2. **`aggregate_variance(lambda, var_x, mean_x) ≥ 0`** when `lambda ≥ 0`, `var_x ≥ 0`, `mean_x ≥ 0`
   — Variance is always non-negative. (Mathematically obvious, but worth certifying in code.)

3. **`aggregate_variance ≥ aggregate_mean²/lambda`** under the specific Pareto parameterization
   — This is the sub-additivity of risk: diversification reduces variance below
     what you'd get from a single large claim of the same expected magnitude.

4. **`aggregate_variance` equals `lambda * (var_x + mean_x²)`**
   — The compound Poisson variance identity. This is the formula the Python
     `aggregate_simulation.py` uses as a "sanity check" — if Aristotle proves
     this algebraic identity holds in C, the sanity check is formally grounded.

5. **`aggregate_std_dev(lambda, var_x, mean_x) ≥ 0`**
   — sqrt of aggregate variance is always non-negative.

6. **`var_floor_nonneg`** — the floor operation in the VaR function always produces ≥ 0
   — Identical to the property in lean_proofs/BasicRisk.lean, now verified in C.

---

## Why Two Representations (Python + C)?

This is the KEY insight of the whole lab:

```
Python (aggregate_simulation.py)          C (aggregate_model.c)
────────────────────────────────          ──────────────────────
Uses the formula to COMPUTE               Implements the formula
E[S], Var(S) as sanity checks             for Aristotle to VERIFY

Result: "the simulated mean is
close to λ·E[X]" (empirical)             Result: "λ·E[X] ≥ 0 for all
                                          λ≥0, E[X]≥0" (proven)
```

The Python tells you what the answer IS. Aristotle tells you the formula
CAN'T be wrong for any input.

---

## Connection to bluberri

When bluberri's platform computes risk metrics for a mining client:
1. Python runs the simulation to get the distribution (fast, approximate)
2. The C functions compute the analytical risk measures (exact formulas)
3. Aristotle has already proven those C functions are always correct

The combination gives you both speed (Python) and certified correctness (Aristotle).
