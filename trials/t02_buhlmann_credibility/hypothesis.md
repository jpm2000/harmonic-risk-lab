# Trial 02: Bühlmann Credibility — Insurance Pricing Personalization

## What We're Testing

**Bühlmann Credibility** is how insurance companies personalize premiums.
Instead of charging every mining company the same rate, the insurer blends:
- The **company's own claims history** (experience rate)
- The **industry-wide average** (prior / collective rate)

The blend factor Z is called the "credibility" — how much weight to give
the individual's experience versus the market average.

**Paper:** Bühlmann, H. (1967). "Experience rating and credibility."
ASTIN Bulletin 4(3): 199–207.

Also partially formalized in: [verified-reserving](https://github.com/Robby955/verified-reserving)
(`BuhlmannStraubStochastic.lean`)

---

## The Math

The **Bühlmann credibility factor:**
```
Z = n / (n + k)
```
where:
- `n` = number of observation periods (years of claims data)
- `k` = credibility parameter = process_variance / structural_variance
  (the ratio of within-risk volatility to between-risk volatility)

The **credibility-weighted premium:**
```
P_cred = Z * X_bar + (1 - Z) * mu_prior
```
where:
- `X_bar` = the insured's average observed loss ratio
- `mu_prior` = the market-wide expected loss ratio

---

## Properties We Want Aristotle to Prove

1. **`credibility_z(n, k) ∈ [0, 1]`** for n ≥ 0 and k > 0
   — Credibility is always a valid mixing weight.

2. **`credibility_z` is monotone increasing in n**
   — More data → higher credibility → more weight on own experience.

3. **`credibility_z` approaches 1 as n → ∞**
   — With infinite data, Z → 1: we trust the company's own experience fully.
   — In code: credibility_z(n, k) increases as n increases for fixed k > 0.

4. **`credibility_premium` is bounded between min and max of its inputs**
   — P_cred is a convex combination of X_bar and mu_prior.
   — So: min(X_bar, mu_prior) ≤ P_cred ≤ max(X_bar, mu_prior).
   — The blended premium can never be more extreme than either component.

5. **`credibility_premium` is non-negative when both X_bar ≥ 0 and mu_prior ≥ 0**

---

## Why This Matters for bluberri

bluberri is building a risk platform for insurance brokers.
The brokers use it to price policies for individual clients.

The credibility model is the mathematical engine behind personalized pricing:
- New mining client (n=1): mostly use market rates (Z is small)
- Established client with 5 years of claims data (n=5): use their own history (Z is larger)

If the credibility formula has a bug where Z > 1, the broker would extrapolate
BEYOND the client's experience — which is mathematically incoherent and
produces premiums that no actuary would sign off on.

Aristotle proves Z ∈ [0,1] for all inputs — no test can cover all n and k.

---

## Connection to OpenAI's Math Model

OpenAI's math preprints solve hard open problems in pure math.
This trial illustrates the DIFFERENT role Aristotle plays:

- OpenAI's model might discover a NEW credibility formula for correlated risks
- Aristotle would then VERIFY that any C implementation of that formula
  is correct — no bugs, no edge cases, provably sound

The research pipeline: Papers → OpenAI/Gemini (translate) → C code → Aristotle (certify)
