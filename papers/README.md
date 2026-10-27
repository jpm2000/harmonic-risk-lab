# Papers Library

Curated reading list for the harmonic-risk-lab. Each paper is a source of
mathematical theorems that can be translated into Aristotle verification trials.

**How to use a paper here:**
1. Read the paper → identify the key invariants (always-true properties)
2. Create a trial: `mkdir trials/t0N_paper_name/`
3. Write the spec: `.speckit/specifications/paper_name.spec.yaml`
4. Write the C model: `trials/t0N_paper_name/model.c`
5. Write the hypothesis: `trials/t0N_paper_name/hypothesis.md`
6. Run it: `python trials/t0N_paper_name/run_trial.py`

---

## Group 1 — Actuarial Reserving (Claims Development)

These papers are directly applicable to insurance brokers and run-off portfolios.

| Paper | Key Theorems | Trial |
|---|---|---|
| Mack (1993). "Distribution-free calculation of the standard error of chain ladder estimates" | Chain ladder factor = weighted average of individual factors; MSEP formula | `t01_mack_chain_ladder/` |
| Bornhuetter & Ferguson (1972). "The actuary and IBNR" | BF reserve = (1-q) * a priori + chain ladder complement | pending |
| Merz & Wüthrich (2008). "Modelling the claims development result for solvency purposes" | One-year CDR is a martingale under Mack assumptions | pending |

**Open-source Lean 4 implementation:** [verified-reserving](https://github.com/Robby955/verified-reserving) — 479 declarations, builds against Mathlib v4.32.2.

---

## Group 2 — Premium Calculation Principles

Core actuarial pricing theory. Directly maps to `models/insurance_model.c`.

| Paper | Key Theorems | Trial |
|---|---|---|
| Kaas et al. (2008). "Modern Actuarial Risk Theory" Ch.2 | EV/SD/Variance principles each satisfy premium ≥ E[L] | `models/insurance_model.c` |
| Bühlmann (1967). "Experience rating and credibility" | Credibility Z ∈ [0,1]; premium is convex combination of data and prior | `t02_buhlmann_credibility/` |
| Bühlmann & Straub (1970). "Credibility for loss ratios" | Weighted credibility; MSEP minimization | pending |

---

## Group 3 — Risk Measures

These are the mathematical foundations for market and credit risk.

| Paper | Key Theorems | Trial |
|---|---|---|
| Artzner et al. (1999). "Coherent Measures of Risk" | 4 axioms (monotonicity, sub-additivity, positive homogeneity, translation invariance); CVaR is coherent, VaR is not | `examples/02_verify_var_model.py` |
| Hardy (2006). "Introduction to Risk Measures for Actuarial Applications" (CAS) | VaR and TVaR definitions; TVaR ≥ VaR always | [PDF](https://www.casact.org/sites/default/files/database/studynotes_hardy4.pdf) |
| Rockafellar & Uryasev (2000). "Optimization of Conditional VaR" | CVaR as minimization over threshold; CVaR is convex in portfolio weights | pending |

**Relevant Lean 4 library:** [A Formally Verified Library of Mathematical Finance](https://arxiv.org/abs/2606.01356) — 330+ theorems covering risk-neutral pricing, stochastic calculus, portfolio theory.

---

## Group 4 — Reinsurance Pricing

Directly applicable to mining and defense (catastrophe exposure).

| Paper | Key Theorems | Trial |
|---|---|---|
| Panjer (1981). "Recursive evaluation of a family of compound distributions" | (a,b,0) class recursion; aggregate loss probabilities sum to 1 | pending |
| McNeil et al. (2005). "Quantitative Risk Management" Ch.7 | EVT GPD VaR formula; VaR increases monotonically in p | pending |
| Daykin et al. (1994). "Practical Risk Theory for Actuaries" | Excess-of-loss layer expected loss ∈ [0, limit] | `models/insurance_model.c` |

---

## Group 5 — Mathematical Finance (Derivatives / Fixed Income)

Longer-term: relevant once bluberri handles structured products or parametric insurance.

| Paper | Key Theorems | Trial |
|---|---|---|
| Black & Scholes (1973) | Option price is always in [0, S] for call, [0, K] for put | pending |
| Hull (2018). "Options, Futures and Other Derivatives" | Put-call parity: C - P = S - K·e^{-rT} | pending |
| Vasicek (1977). "An equilibrium characterization of the term structure" | Short rate stays positive if 2·kappa·theta > sigma² (Feller condition) | pending |

---

## How to Search for New Papers

Use the Gemini pipeline in `examples/04_gemini_pipeline.py` or run:

```bash
python utils/paper_search.py "parametric insurance pricing for mining operations"
```

This will search for relevant papers and generate a spec stub.
