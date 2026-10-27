# Trial 05: Business Interruption Multiplier — The 80% Rule

## What We're Testing

The single most important finding in the Marsh "Mining Losses Uncovered" (2025) report:

> **Business interruption (BI) accounts for ~80% of total gross losses in mining.**

This is not a small correction to physical damage estimates — it is the dominant
component of every major mining claim. The months of lost production after a fire,
flood, or equipment failure routinely cost 4× more than the physical damage itself.

Pan American Silver (2025 Sustainability Report) confirms this reality with two
fatal accidents in 2025 (Shahuindo, Peru and Jacobina, Brazil) — each triggering
operational shutdowns and safety audits that extend well beyond the incident itself.

This trial formalizes and verifies the mathematical model underlying the BI multiplier:
the invariants that must hold for every mining insurance calculation involving BI.

**Source:** Marsh (2025). *Mining Losses Uncovered: The Cost of Disruption and the
Path to Resilience.* Marsh Risk. Data: 2006–2025, $15.3B insured losses.

---

## The Math

### The BI Loss Structure

```
PD loss  = direct physical damage to equipment, structures
BI loss  = daily_revenue × recovery_days
Total    = pd_loss + bi_loss
BI ratio = bi_loss / total_loss
```

### The Multiplier

```
BI multiplier = total_loss / pd_loss = 1 + (daily_revenue × recovery_days) / pd_loss
```

When `BI ratio = 0.80` (Marsh average):
- `bi_loss / total_loss = 0.80`
- `pd_loss / total_loss = 0.20`
- `bi_loss / pd_loss = 4.0`
- So the total loss is **5× the physical damage** (multiplier = 5)

### The Connection to Single Points of Failure (Marsh)

Patrick Walker (Rio Tinto): "A single grinding mill can process thousands of tons
of ore per day." If that mill handles fraction `f` of output:
- `daily_revenue_at_risk = f × total_daily_revenue`
- `bi_loss = f × total_daily_revenue × recovery_days`

The higher the concentration (large `f`), the larger the BI loss for the same
recovery time. This is the mathematical reason why machine breakdown (16.5% of
Marsh losses) produces BI shares above 82% — even small physical damage to a
critical machine causes enormous production shutdowns.

### Why the Model Must Be Verified

If a bluberri pricing model has a bug where:
- `bi_ratio > 1.0` (BI exceeds total loss) — the model is wrong
- `total_loss < pd_loss` — BI is negative, impossible
- `bi_multiplier < 1.0` when recovery_days > 0 — the model undersells coverage

All of these are provable algebraic invariants. Aristotle verifies them hold for
ALL inputs simultaneously, not just a test suite.

---

## Properties We Want Aristotle to Prove

1. **`total_loss >= pd_loss`**
   BI adds to PD — you can't have negative BI. The total is always at least the
   physical damage. If this fails, the model would price policies below actual PD.

2. **`bi_ratio ∈ [0, 1)` when `pd_loss > 0`**
   BI can't exceed 100% of the total loss (that would mean PD is negative).
   The upper bound is strictly less than 1 because `pd_loss > 0`.

3. **`total_loss` monotone in `recovery_days`**
   A longer outage always costs more. If `d1 >= d2`, then `total_loss(d1) >= total_loss(d2)`.

4. **`bi_ratio` monotone in `recovery_days`**
   The longer the outage, the higher the BI share. This is the mathematical basis
   for the observation that "months of lost production inflict the deepest wounds."

5. **`bi_multiplier >= 1.0` when `pd_loss > 0` and `recovery_days >= 0`**
   The total insured value is always at least the PD alone. An insurer that only
   prices PD and ignores BI is always underinsuring.

6. **`bi_loss >= 0`**
   BI loss is non-negative by construction.

---

## The Pan American Silver Connection

From PAS's 2025 Sustainability Report:
- 2 fatal accidents → immediate site shutdowns at Jacobina (Brazil) and Shahuindo (Peru)
- Multiple safety audits triggered → additional recovery delay beyond the incident
- ESG-linked revolving credit ($750M) includes sustainability performance pricing

This means for a PAS-style operation, BI loss has two components:
1. Direct production shutdown (recovery_days × daily_revenue)
2. Indirect costs from audits, corrective actions, regulatory review

A bluberri product for PAS-type clients must correctly model both. This trial
verifies the structural invariants of the direct production component.

---

## Expected Outcome

Properties 1, 3, 5, and 6 are straightforward algebra — Aristotle should prove
these quickly. Properties 2 and 4 require slightly more reasoning about ratios.

The most interesting case: Property 4 (monotonicity of BI ratio). As recovery_days
increases, both numerator (bi_loss) and denominator (total_loss) grow — but the
ratio should still increase because bi_loss grows faster. Aristotle will verify this
formally.
