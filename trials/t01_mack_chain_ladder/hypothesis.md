# Trial 01: Mack Chain Ladder — IBNR Reserve Calculation

## What We're Testing

The **Mack Chain Ladder** is the most widely used actuarial method for estimating
"Incurred But Not Reported" (IBNR) reserves — money an insurer must hold today to
pay claims that have already happened but haven't been fully settled yet.

Every insurance company that writes liability, mining, or long-tail coverage uses this.
It's required by insurance regulators for balance sheet solvency assessment.

**Paper:** Mack, T. (1993). "Distribution-free calculation of the standard error of chain
ladder estimates." ASTIN Bulletin 23(2): 213–225.

Also implemented in Lean 4 by: [verified-reserving](https://github.com/Robby955/verified-reserving)

---

## The Math

Given a claims development triangle (cumulative paid claims by accident year × development year):

```
         Dev 1   Dev 2   Dev 3   Dev 4
AY 2021  1000    1200    1250    1260
AY 2022   900    1080    1125     ???
AY 2023   850    1020     ???     ???
AY 2024   800     ???     ???     ???
```

**Step 1** — Compute development factors (link ratios) for each column:
```
f_k = sum(C_{i,k+1}) / sum(C_{i,k})   for each column k
```
This is a weighted average of how much losses develop from period k to k+1.

**Step 2** — Project ultimate losses:
```
Ultimate_i = C_{i, latest} * f_{latest} * f_{latest+1} * ... * f_{final}
```

**Step 3** — IBNR Reserve:
```
IBNR_i = Ultimate_i - C_{i, latest}   (always >= 0 by construction)
```

---

## Properties We Want Aristotle to Prove

1. **`development_factor(paid_t, paid_t1) > 0`** when `paid_t > 0` and `paid_t1 > 0`
   — Link ratios must be positive; negative paid claims are impossible.

2. **`predict_ultimate >= current_paid`** when all development factors are >= 1.0
   — Ultimate losses can only be >= what's been paid so far (claims don't reverse).
   — Note: factors < 1.0 are theoretically possible (recoveries) but unusual.

3. **`ibnr_reserve(ultimate, current_paid) >= 0`** when `ultimate >= current_paid >= 0`
   — You can't have negative IBNR (can't owe less than you've already paid).

4. **`ibnr_reserve` returns -1.0 for invalid inputs** (ultimate < current_paid, or negative paid)

---

## Why This Matters for bluberri

A bluberri client is a mining company that buys liability insurance.
Their insurer must hold adequate IBNR reserves or face insolvency.
If the chain ladder implementation has a bug that makes IBNR go negative,
the insurer appears solvent when it isn't — a regulatory catastrophe.

Aristotle proves these invariants hold for ALL inputs simultaneously —
no test suite can do that.

---

## Expected Outcome

All 4 properties should be provable. Property 2 requires the assumption
that all factors >= 1.0 — Aristotle will correctly scope the proof to that
precondition.

If Aristotle finds a counterexample, it means the C code has a bug
(e.g., a sign error or incorrect floor operation).
