# Trials

Each trial is a self-contained experiment: a math paper → C model → Aristotle verification.

**The trial format:**
```
trials/t0N_model_name/
├── hypothesis.md    ← Read this first: the math, the paper, what we're testing and why
├── model.c          ← The C implementation with property comments
└── run_trial.py     ← Submit to Aristotle and save results
```

---

## Running Trials

```bash
# Dry run — see the prompt without submitting (good for reviewing first)
python trials/t01_mack_chain_ladder/run_trial.py --dry-run

# Full run — submit to Aristotle
python trials/t01_mack_chain_ladder/run_trial.py

# With a worked example for context
python trials/t01_mack_chain_ladder/run_trial.py --show-triangle
python trials/t02_buhlmann_credibility/run_trial.py --show-example
```

Results are automatically saved to `trials/RESULTS.md`.

---

## Available Trials

| Trial | Topic | Source | Key Properties | Python companion |
|---|---|---|---|---|
| `t01_mack_chain_ladder/` | IBNR reserve estimation | Mack (1993) | IBNR ≥ 0, factors > 0 | — |
| `t02_buhlmann_credibility/` | Personalized insurance pricing | Bühlmann (1967) | Z ∈ [0,1], convex blend | — |
| `t03_aggregate_loss/` | Compound Poisson formulas | Module 4 / Loss Data Analytics | Var(S) = λ·E[X²] identity | `numerics/aggregate_simulation.py` |
| `t04_evt_var/` | Heavy-tail VaR (mining/cat) | McNeil et al. (2005) + Marsh (2025) | VaR ≥ u, ES ≥ VaR, EVT ≥ Normal | — |
| `t05_bi_multiplier/` | Business interruption multiplier | Marsh (2025) + PAS (2025) | total ≥ PD, BI ratio ∈ [0,1), mult ≥ 1 | — |
| `t06_concentration_risk/` | Single point of failure | Marsh (2025) / Rio Tinto | conc ≥ divr, ratio ∈ (0,1], monotone in n | — |
| `t07_tailings_pml/` | Tailings dam PML / return period | McNeil et al. (2005) / Brumadinho | PML ≥ x_m, monotone in T, AEP ∈ (0,1] | — |

## The Python–Aristotle relationship (t03 onwards)

Starting from t03, each trial has a **Python companion** in `numerics/`:
- Python computes the answers (Monte Carlo, optimization)
- C implements the closed-form formulas
- Aristotle proves the C formulas are always correct
- This certifies that the Python results rest on proven foundations

## Planned Trials

| Trial | Topic | Paper | Status |
|---|---|---|---|
| `t08_bornhuetter_ferguson/` | BF reserves (long-tail mining claims) | Bornhuetter & Ferguson (1972) | TODO |
| `t09_panjer_recursion/` | Aggregate loss distribution | Panjer (1981) | TODO |
| `t10_ruin_probability/` | Cramér-Lundberg ruin bound | Grandell (1991) | TODO |

---

## Adding a New Trial

1. Read a paper in `papers/README.md`
2. Copy `trials/trial_template/` to `trials/t0N_paper_name/`
3. Fill in `hypothesis.md` with the paper, math, and properties
4. Write `model.c` implementing the functions
5. Write `run_trial.py` (copy from an existing trial and edit the prompt)
6. Run with `--dry-run` first, then for real
7. Check `RESULTS.md` for the outcome

---

## Interpreting Results

| Status | Meaning | What to do |
|---|---|---|
| `SUCCESS` | All properties proved for all inputs | Ship with confidence |
| `COUNTEREXAMPLE_FOUND` | Aristotle found an input that breaks a property | That's a bug — fix `model.c` |
| `TIMEOUT` | Proof took too long | Simplify the property or split into smaller ones |
| `ERROR` | API or code error | Check the C code compiles, fix syntax |
