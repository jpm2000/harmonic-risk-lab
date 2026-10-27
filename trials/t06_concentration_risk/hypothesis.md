# Trial 06: Concentration Risk — Single Point of Failure

## What We're Testing

The second biggest operational insight in the Marsh report (after BI = 80%):

> "The industry's shift toward single, high-capacity machines has aggravated this
> exposure; a single grinding mill can process thousands of tons of ore a day,
> so a failure can trigger multi-month outages."
> — Marsh, *Mining Losses Uncovered* (2025)

This is **concentration risk**: when one machine, one road, or one facility handles
a large fraction `f` of total production capacity, a single failure causes BI losses
proportional to `f`. The more concentrated the operation, the larger the BI loss
from any single incident.

Pan American Silver operates this reality across 10 mines in 8 countries — each mine
is itself a concentration point. Their Jacobina (Brazil) and Shahuindo (Peru) fatalities
in 2025 triggered immediate shutdowns of entire sites, not just the affected area.

**Source:** Marsh (2025). *Mining Losses Uncovered.* Patrick Walker, Rio Tinto,
on machinery breakdown (16.5% of $15.3B losses, BI share > 82%).

---

## The Math

### Concentration Fraction Model

Let `f ∈ (0, 1]` be the fraction of total daily production handled by a single asset.

```
bi_loss_concentrated = f × daily_revenue × recovery_days
```

For a fully concentrated operation (single machine does everything, `f = 1.0`):
```
bi_loss_max = 1.0 × daily_revenue × recovery_days
```

For `n` identical machines sharing the load equally (`f = 1/n`):
```
bi_loss_single_failure = (1/n) × daily_revenue × recovery_days
```

### Diversification Benefit

If there are `n` machines and one fails, the loss is `1/n` of what it would be
with a single machine. The diversification factor:

```
diversification_ratio = bi_loss_single_failure(n) / bi_loss_max
                      = (1/n × rev × days) / (1.0 × rev × days)
                      = 1/n
```

As `n` grows (more machines, each smaller), the loss from one failure shrinks.
This is why diversification of production assets reduces insurance premiums.

### Capital Implications

A mining company choosing between:
1. **One large mill** handling 100% of ore: single failure = full BI loss
2. **Two mills** each handling 50%: single failure = 50% BI loss
3. **Four mills** each handling 25%: single failure = 25% BI loss

The premium reduction from diversification is linear in `1/n`.

---

## Properties We Want Aristotle to Prove

1. **`concentrated_bi_loss >= 0`** for valid inputs (`f ∈ (0,1]`, `daily_revenue >= 0`,
   `recovery_days >= 0`)

2. **`concentrated_bi_loss` monotone in `f`**
   Higher concentration fraction → larger BI loss. If `f1 >= f2`, then
   `concentrated_bi_loss(f1) >= concentrated_bi_loss(f2)`. This is the
   mathematical statement of "concentration risk increases exposure."

3. **`concentrated_bi_loss` monotone in `recovery_days`**
   Longer outage → larger loss. Proved in t05 for the general case;
   here it applies specifically to the concentration fraction model.

4. **`diversified_bi_loss(n) <= concentrated_bi_loss(1.0)`**
   Distributing production across `n >= 1` machines always reduces the BI loss
   from a single machine failure. Formally: `bi_loss(1/n) <= bi_loss(1.0)`.

5. **`diversified_bi_loss` monotone decreasing in `n_machines`**
   More machines → smaller individual loss. `n1 >= n2` implies
   `bi_loss(1/n1) <= bi_loss(1/n2)`. Adding machines always helps, never hurts.

6. **`concentration_premium(f) >= 0`**
   The extra premium required for concentration vs. a fully diversified operation.
   `premium = bi_loss(f) - bi_loss(1/n_equivalent)`. This is always non-negative.

---

## Why This Matters for bluberri

An insurance broker (bluberri's target client) must correctly price the concentration
structure of each mining client. Two mines with the same total production value but
different machine configurations have different BI exposure:

- Mine A: 1 SAG mill at 10,000 t/day → single failure = 100% BI
- Mine B: 2 SAG mills at 5,000 t/day each → single failure = 50% BI

Mine B should pay ~50% less for BI coverage, or equivalently, bluberri recommends
Mine A buy redundancy to reduce their premium. These invariants prove that the
concentration model behaves correctly for every possible configuration.

---

## Expected Outcome

Properties 1–3 are straightforward from the linear structure of the formula.
Properties 4 and 5 require Aristotle to reason about the relationship between
`bi_loss(1/n)` and `bi_loss(1.0)` — essentially that `1/n <= 1.0` for `n >= 1`.
Property 6 builds on that comparison.
