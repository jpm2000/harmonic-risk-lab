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

| Trial | Topic | Paper | Key Properties |
|---|---|---|---|
| `t01_mack_chain_ladder/` | IBNR reserve estimation | Mack (1993) | IBNR ≥ 0, factors > 0 |
| `t02_buhlmann_credibility/` | Personalized insurance pricing | Bühlmann (1967) | Z ∈ [0,1], premium is convex combination |

## Planned Trials

| Trial | Topic | Paper | Status |
|---|---|---|---|
| `t03_panjer_recursion/` | Aggregate loss distribution | Panjer (1981) | TODO |
| `t04_evt_var/` | Heavy-tail VaR (mining/cat) | McNeil et al. (2005) | TODO |
| `t05_bornhuetter_ferguson/` | BF reserves | Bornhuetter & Ferguson (1972) | TODO |
| `t06_black_scholes_bounds/` | Option pricing bounds | Black & Scholes (1973) | TODO |

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
