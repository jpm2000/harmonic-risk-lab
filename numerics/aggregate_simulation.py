"""
numerics/aggregate_simulation.py — Compound Poisson aggregate loss simulator.
──────────────────────────────────────────────────────────────────────────────
SOURCE: Curriculum Module 4 (Collective risk model) + Module 8 (Risk measures)

THE MODEL (S = ΣXᵢ, collective risk model):
  - N ~ Poisson(λ)  →  how many claims happen in a year
  - Xᵢ ~ F_severity  →  how costly each claim is
  - S = X₁ + X₂ + ... + Xₙ  →  total portfolio loss

CLOSED-FORM PROPERTIES (will be verified in C by Aristotle, trial t03):
  E[S] = λ · E[X]
  Var(S) = λ · E[X²]   (since Var(N) = λ for Poisson)
         = λ · (Var(X) + (E[X])²)

WHY Monte Carlo instead of just the formulas?
  The formulas give E[S] and Var(S), but NOT the full distribution.
  To compute VaR and CVaR — the risk measures regulators care about —
  you need the full shape of the tail. That requires simulation.
  The formulas serve as a "sanity check" on the simulated mean/variance.

SUPPORTED SEVERITY DISTRIBUTIONS:
  - Lognormal (standard for most liability lines)
  - Pareto (heavy tails — mining liability, cat exposures)
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy import stats


@dataclass
class AggregateResult:
    """Output of a simulation run. All monetary values in same currency units."""

    # Simulated summary statistics
    mean: float
    std: float

    # Risk measures — the numbers regulators and capital models use
    var_95: float    # VaR at 95% — common for internal models
    var_99: float    # VaR at 99% — Solvency II standard
    var_995: float   # VaR at 99.5% — Solvency II SCR threshold
    cvar_95: float   # CVaR at 95% (also called TVaR, ES)
    cvar_99: float
    cvar_995: float

    # Theoretical closed-form values (sanity check)
    theoretical_mean: float
    theoretical_var: float

    # The raw scenarios — passed downstream to the optimizer
    scenarios: np.ndarray
    n_simulations: int
    severity_dist: str


# ── Core simulation functions ──────────────────────────────────────────────


def simulate_lognormal(
    lambda_freq: float,
    mu_sev: float,
    sigma_sev: float,
    n_sim: int = 100_000,
    seed: int = 42,
) -> AggregateResult:
    """
    Compound Poisson aggregate loss with Lognormal severity.

    Why Lognormal?
      - Right-skewed: most claims are small, a few are very large
      - Multiplicative: losses often grow proportionally (medical inflation, legal costs)
      - Standard for: workers comp, general liability, motor, professional indemnity

    Parameters:
      lambda_freq — expected number of claims per year (Poisson λ)
      mu_sev      — Lognormal mean parameter (in log scale, not dollar scale)
      sigma_sev   — Lognormal std deviation in log scale (σ)

    Key formulas:
      E[X]    = exp(mu + σ²/2)
      Var(X)  = (exp(σ²) - 1) · exp(2μ + σ²)
      E[X²]   = exp(2μ + 2σ²)
      E[S]    = λ · E[X]
      Var(S)  = λ · E[X²]
    """
    rng = np.random.default_rng(seed)

    # ── Step 1: How many claims per scenario? ──────────────────────────────
    # n_sim independent draws from Poisson(λ)
    # Each entry N[i] = number of claims in scenario i
    N = rng.poisson(lam=lambda_freq, size=n_sim)
    total_claims = int(N.sum())

    # ── Step 2: Draw all individual claim amounts at once ──────────────────
    # More efficient than drawing per-scenario inside a loop
    all_X = rng.lognormal(mean=mu_sev, sigma=sigma_sev, size=total_claims)

    # ── Step 3: Assign claims to scenarios and sum ─────────────────────────
    # np.add.reduceat sums array segments defined by index positions.
    # We use this to sum the claims belonging to each scenario efficiently.
    S = np.zeros(n_sim)
    mask = N > 0
    if mask.any():
        n_nonzero = N[mask]
        # Start index of each scenario's claims in the flattened all_X array
        start_indices = np.concatenate([[0], np.cumsum(n_nonzero[:-1])])
        S[mask] = np.add.reduceat(all_X, start_indices)
    # Scenarios with N[i] = 0 stay at 0 (no claims = no loss)

    # ── Closed-form theoretical values ────────────────────────────────────
    mean_X = np.exp(mu_sev + 0.5 * sigma_sev**2)
    ex2    = np.exp(2 * mu_sev + 2 * sigma_sev**2)   # E[X²]

    theoretical_mean = lambda_freq * mean_X
    theoretical_var  = lambda_freq * ex2               # λ · E[X²]

    return AggregateResult(
        mean=float(S.mean()),
        std=float(S.std()),
        var_95=_var(S, 0.95),
        var_99=_var(S, 0.99),
        var_995=_var(S, 0.995),
        cvar_95=_cvar(S, 0.95),
        cvar_99=_cvar(S, 0.99),
        cvar_995=_cvar(S, 0.995),
        theoretical_mean=theoretical_mean,
        theoretical_var=theoretical_var,
        scenarios=S,
        n_simulations=n_sim,
        severity_dist="lognormal",
    )


def simulate_pareto(
    lambda_freq: float,
    alpha_pareto: float,
    x_m: float,
    n_sim: int = 100_000,
    seed: int = 42,
) -> AggregateResult:
    """
    Compound Poisson aggregate loss with Pareto severity.

    Why Pareto?
      - Extremely heavy tail: P(X > x) = (x_m/x)^α decays as a power law
      - Standard for: mining liability, construction, marine cargo, catastrophe
      - The tail behaviour dominates the risk for large portfolios

    Requires alpha > 2 for finite variance.

    Parameters:
      lambda_freq  — expected claims per year
      alpha_pareto — tail index (shape). Higher α = lighter tail. Typical: 2–4.
      x_m          — minimum claim size (scale). All claims ≥ x_m.

    Key formulas:
      E[X]   = α · x_m / (α - 1)
      Var(X) = α · x_m² / ((α-1)² · (α-2))
      E[X²]  = 2 · x_m² · α / ((α-1)(α-2))
    """
    if alpha_pareto <= 2:
        raise ValueError(
            f"alpha_pareto must be > 2 for finite variance (got {alpha_pareto})"
        )

    rng = np.random.default_rng(seed)

    N = rng.poisson(lam=lambda_freq, size=n_sim)
    total_claims = int(N.sum())

    # scipy.stats.pareto uses the convention: P(X > x) = (scale/(x))^b
    # where b=alpha and scale=x_m. We need to shift: X = x_m * (1 + U)
    # where U ~ pareto(b=alpha_pareto).
    # Simpler: use inverse CDF directly.
    U = rng.uniform(size=total_claims)
    # Inverse CDF of Pareto: F^{-1}(u) = x_m / (1-u)^{1/alpha}
    all_X = x_m / (1 - U) ** (1.0 / alpha_pareto)

    S = np.zeros(n_sim)
    mask = N > 0
    if mask.any():
        n_nonzero = N[mask]
        start_indices = np.concatenate([[0], np.cumsum(n_nonzero[:-1])])
        S[mask] = np.add.reduceat(all_X, start_indices)

    a = alpha_pareto
    mean_X = a * x_m / (a - 1)
    ex2    = 2 * x_m**2 * a / ((a - 1) * (a - 2))

    theoretical_mean = lambda_freq * mean_X
    theoretical_var  = lambda_freq * ex2

    return AggregateResult(
        mean=float(S.mean()),
        std=float(S.std()),
        var_95=_var(S, 0.95),
        var_99=_var(S, 0.99),
        var_995=_var(S, 0.995),
        cvar_95=_cvar(S, 0.95),
        cvar_99=_cvar(S, 0.99),
        cvar_995=_cvar(S, 0.995),
        theoretical_mean=theoretical_mean,
        theoretical_var=theoretical_var,
        scenarios=S,
        n_simulations=n_sim,
        severity_dist="pareto",
    )


# ── Risk measure helpers ────────────────────────────────────────────────────


def _var(S: np.ndarray, alpha: float) -> float:
    """VaR at confidence level alpha = alpha-th percentile of S."""
    return float(np.percentile(S, alpha * 100))


def _cvar(S: np.ndarray, alpha: float) -> float:
    """
    CVaR (Expected Shortfall) at confidence level alpha.
    = average loss in the worst (1-alpha) fraction of scenarios.

    CVaR is always >= VaR at the same level (Property 2 from risk_model.c).
    This is verified formally by Aristotle in examples/02_verify_var_model.py.
    """
    threshold = np.percentile(S, alpha * 100)
    tail = S[S >= threshold]
    return float(tail.mean()) if len(tail) > 0 else threshold


# ── Reporting ──────────────────────────────────────────────────────────────


def print_summary(result: AggregateResult, label: str = "Portfolio") -> None:
    """
    Print a formatted actuarial report for a simulation result.

    The table format mirrors the output structure from Curriculum Module 11
    (Section 4: Actuarial Results + Section 5: Risk Metrics).
    """
    print(f"\n{'═'*58}")
    print(f"  AGGREGATE LOSS REPORT — {label}")
    print(f"  {result.n_simulations:,} Monte Carlo scenarios  │  {result.severity_dist} severity")
    print(f"{'═'*58}")
    print(f"  {'SECTION 1 — Simulated vs Theoretical':}")
    print(f"  {'─'*54}")
    print(f"  {'Simulated E[S]:':35s}  {result.mean:>12,.2f}")
    print(f"  {'Theoretical E[S] = λ·E[X]:':35s}  {result.theoretical_mean:>12,.2f}")
    pct_err = abs(result.mean - result.theoretical_mean) / result.theoretical_mean * 100
    print(f"  {'Error (should be < 1% at 100k sims):':35s}  {pct_err:>11.2f}%")
    print(f"  {'Simulated std dev:':35s}  {result.std:>12,.2f}")
    print(f"  {'Theoretical √Var(S) = √(λ·E[X²]):':35s}  {result.theoretical_var**0.5:>12,.2f}")
    print(f"\n  {'SECTION 2 — Risk Measures':}")
    print(f"  {'─'*54}")
    print(f"  {'VaR  95.0%':35s}  {result.var_95:>12,.2f}")
    print(f"  {'VaR  99.0%  (Solvency II standard)':35s}  {result.var_99:>12,.2f}")
    print(f"  {'VaR  99.5%  (Solvency II SCR)':35s}  {result.var_995:>12,.2f}")
    print(f"  {'─'*54}")
    print(f"  {'CVaR 95.0%':35s}  {result.cvar_95:>12,.2f}")
    print(f"  {'CVaR 99.0%':35s}  {result.cvar_99:>12,.2f}")
    print(f"  {'CVaR 99.5%':35s}  {result.cvar_995:>12,.2f}")
    print(f"\n  {'SECTION 3 — Capital Requirement (simple)':}")
    print(f"  {'─'*54}")
    capital_995 = result.var_995 - result.mean
    print(f"  {'Capital = VaR(99.5%) − E[S]:':35s}  {capital_995:>12,.2f}")
    print(f"  {'(minimum buffer to stay solvent)':}")
    print(f"{'═'*58}\n")


if __name__ == "__main__":
    # ── Quick demo: mining liability portfolio ──────────────────────────────
    # Parameters for a typical mining company general liability portfolio:
    #   - Expected 8 claims per year
    #   - Log-mean = 10.0 → median severity ~$22k (exp(10) ≈ 22,026)
    #   - Log-sigma = 1.2 → heavy right skew (some claims reach millions)
    print("Demo: Mining liability portfolio (Lognormal severity)")
    r_ln = simulate_lognormal(
        lambda_freq=8.0,
        mu_sev=10.0,
        sigma_sev=1.2,
        n_sim=100_000,
    )
    print_summary(r_ln, label="Mining — Lognormal")

    # Same portfolio but with Pareto severity (heavy tail assumption)
    # Pareto α=3, x_m=5000 → E[X] = 3*5000/(3-1) = 7500
    print("Demo: Same portfolio, Pareto severity (heavier tail)")
    r_pa = simulate_pareto(
        lambda_freq=8.0,
        alpha_pareto=3.0,
        x_m=5_000,
        n_sim=100_000,
    )
    print_summary(r_pa, label="Mining — Pareto")

    # Key observation: Pareto will show much higher CVaR than Lognormal
    # even if the means are similar. That's the tail risk difference.
    print("CVaR 99.5% comparison:")
    print(f"  Lognormal: {r_ln.cvar_995:,.2f}")
    print(f"  Pareto:    {r_pa.cvar_995:,.2f}")
    print("\nThe Pareto tail risk is higher — use this for cat-exposed lines.")
