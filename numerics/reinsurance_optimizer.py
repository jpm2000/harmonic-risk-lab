"""
numerics/reinsurance_optimizer.py — CVaR optimization for reinsurance selection.
────────────────────────────────────────────────────────────────────────────────
SOURCE: Curriculum Module 9 (Risk optimization)

THE PROBLEM (Module 9's formulation):
  Minimize:  CVaR_α(net retained loss)
  Subject to:
    reinsurance cost ≤ B          (budget constraint)
    retention ≥ R_min             (minimum retained risk)

THE APPROACH (two methods):

  Method 1 — Grid search + efficient frontier (scipy)
    For each candidate retention R in a grid:
      - Net loss per scenario: L_i = min(S_i, R)
      - XL reinsurance premium: cost(R) = (1+loading) * mean(max(S_i - R, 0))
      - Total retained cost: TC_i = L_i + cost(R)    [loss + cost of protection]
      - CVaR(TC) = average of worst (1-alpha) scenarios
    Find R* that minimizes CVaR(TC) subject to cost(R) ≤ budget.
    Outputs the "efficient frontier": CVaR vs. reinsurance cost for all R.

  Method 2 — CVXPY linear program (quota share)
    For quota share fraction q ∈ [0,1]:
      - Net loss per scenario: L_i = (1-q)*S_i + q*mean(S)*(1+loading)
      - This IS linear in q → CVaR minimization is a convex LP → CVXPY
    Uses the Rockafellar-Uryasev CVaR formulation:
      CVaR_α = min_{t, z_i≥0} { t + 1/((1-α)·m) · Σᵢ zᵢ }  s.t. zᵢ ≥ Lᵢ(q) - t

WHY TWO METHODS?
  Grid search: works for any reinsurance structure (XL, stop-loss, etc.)
               non-convex in R, so no closed-form solution
  CVXPY:       only works for structures that are LINEAR in the decision variable
               but finds the provably optimal solution (not just a grid approximation)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import numpy as np
import scipy.optimize as opt


# ── Output types ────────────────────────────────────────────────────────────


@dataclass
class EfficientFrontierResult:
    """The tradeoff curve between reinsurance cost and retained CVaR."""
    retentions:           np.ndarray   # R values tested
    reinsurance_costs:    np.ndarray   # cost(R) for each R
    retained_cvar:        np.ndarray   # CVaR of (net loss + cost) for each R
    retained_cvar_gross:  np.ndarray   # CVaR of net loss only (no cost added)
    optimal_retention:    float        # R* minimizing CVaR subject to budget
    optimal_cost:         float
    optimal_cvar:         float
    gross_cvar:           float        # CVaR with NO reinsurance (baseline)
    alpha:                float


@dataclass
class QuotaShareResult:
    """Optimal quota share from CVXPY."""
    optimal_q:           float    # fraction of risk ceded (0 = keep all, 1 = cede all)
    optimal_cvar:        float    # CVaR of total retained cost at optimal q
    reinsurance_cost:    float    # premium paid at optimal q
    gross_cvar:          float    # CVaR with no reinsurance (baseline)
    cvar_reduction_pct:  float    # percentage reduction in CVaR


# ── Method 1: XL reinsurance — efficient frontier ──────────────────────────


def efficient_frontier_xl(
    scenarios: np.ndarray,
    loading: float = 0.25,
    alpha: float = 0.995,
    budget: Optional[float] = None,
    n_retention_points: int = 50,
    r_min_pct: float = 0.50,
    r_max_pct: float = 0.99,
) -> EfficientFrontierResult:
    """
    Compute the efficient frontier for XL (excess-of-loss) reinsurance.

    An XL contract at retention R means:
      - Insurer pays: min(S, R) for each scenario       ← capped at R
      - Reinsurer pays: max(S-R, 0) for each scenario   ← everything above R

    The insurer pays a PREMIUM upfront for this protection:
      cost(R) = (1 + loading) * E[max(S - R, 0)]
              = (1 + loading) * mean(max(S - R, 0) over all scenarios)

    Total retained cost per scenario: TC_i = min(S_i, R) + cost(R)
    We minimize CVaR(TC) subject to cost(R) ≤ budget.

    Parameters:
      scenarios  — loss scenarios from aggregate_simulation.py
      loading    — reinsurance premium loading factor (0.25 = 25% above expected loss)
      alpha      — confidence level for CVaR (0.995 = 99.5%)
      budget     — maximum reinsurance spend (None = unconstrained)
      n_retention_points — how many R values to test (more = finer grid)
      r_min_pct  — lower bound for R as percentile of S (e.g. 0.50 = 50th percentile)
      r_max_pct  — upper bound for R as percentile of S (e.g. 0.99 = 99th percentile)
    """
    S = scenarios
    m = len(S)

    # Range of retentions to test: from median to 99th percentile of losses
    r_low  = np.percentile(S, r_min_pct * 100)
    r_high = np.percentile(S, r_max_pct * 100)
    retentions = np.linspace(r_low, r_high, n_retention_points)

    costs        = np.zeros(n_retention_points)
    cvars        = np.zeros(n_retention_points)
    cvars_gross  = np.zeros(n_retention_points)

    for i, R in enumerate(retentions):
        # Reinsurance recoveries for each scenario
        recovery = np.maximum(S - R, 0.0)
        # XL premium: expected recovery × loading factor
        xl_premium = (1.0 + loading) * recovery.mean()
        # Net retained loss per scenario (insurer pays up to R)
        net_loss = np.minimum(S, R)
        # Total retained cost = net loss + constant premium paid upfront
        total_cost = net_loss + xl_premium

        costs[i]       = xl_premium
        cvars[i]       = _cvar(total_cost, alpha)   # CVaR of total cost
        cvars_gross[i] = _cvar(net_loss, alpha)      # CVaR of net loss only

    gross_cvar = _cvar(S, alpha)

    # Find optimal retention subject to budget
    if budget is not None:
        feasible = costs <= budget
        if feasible.any():
            idx = np.argmin(cvars[feasible])
            feasible_retentions = retentions[feasible]
            opt_retention = float(feasible_retentions[idx])
            opt_cost      = float(costs[feasible][idx])
            opt_cvar      = float(cvars[feasible][idx])
        else:
            # No retention is within budget — recommend lowest cost option
            idx = np.argmin(costs)
            opt_retention = float(retentions[idx])
            opt_cost      = float(costs[idx])
            opt_cvar      = float(cvars[idx])
    else:
        # Unconstrained: minimize CVaR directly
        idx = np.argmin(cvars)
        opt_retention = float(retentions[idx])
        opt_cost      = float(costs[idx])
        opt_cvar      = float(cvars[idx])

    return EfficientFrontierResult(
        retentions=retentions,
        reinsurance_costs=costs,
        retained_cvar=cvars,
        retained_cvar_gross=cvars_gross,
        optimal_retention=opt_retention,
        optimal_cost=opt_cost,
        optimal_cvar=opt_cvar,
        gross_cvar=gross_cvar,
        alpha=alpha,
    )


# ── Method 2: Quota share — CVXPY LP ───────────────────────────────────────


def optimize_quota_share_cvxpy(
    scenarios: np.ndarray,
    loading: float = 0.25,
    alpha: float = 0.995,
    budget: Optional[float] = None,
    q_min: float = 0.0,
    q_max: float = 1.0,
) -> QuotaShareResult:
    """
    Find the optimal quota share fraction using CVXPY (Module 9 formulation).

    A quota share at rate q means:
      - Insurer cedes fraction q of every loss to the reinsurer
      - Reinsurer pays q * S_i for each scenario
      - Insurer pays (1-q) * S_i
      - Premium paid: q * mean(S) * (1 + loading)

    Net retained cost per scenario:
      TC_i(q) = (1-q) * S_i + q * mean(S) * (1+loading)
              = S_i - q * (S_i - mean(S) * (1+loading))
              = S_i - q * D_i      where D_i = S_i - mean(S)*(1+loading)

    TC_i is LINEAR in q → CVaR minimization is a convex LP → CVXPY.

    CVXPY formulation (Rockafellar-Uryasev):
      minimize:  t + 1/((1-α)·m) · Σᵢ zᵢ
      subject to:
        zᵢ ≥ TC_i(q) - t   for all i
        zᵢ ≥ 0              for all i
        q ∈ [q_min, q_max]
        q * mean(S) * (1+loading) ≤ budget   (if budget given)

    Why CVXPY here and scipy for XL?
      Quota share: TC is LINEAR in q → convex → CVXPY optimal
      XL retention: TC is NOT linear in R → non-convex → use grid search
    """
    try:
        import cvxpy as cp
    except ImportError:
        raise ImportError(
            "cvxpy is required for this function. Install it with:\n"
            "  pip install cvxpy"
        )

    S = scenarios
    m = len(S)
    mean_S = float(S.mean())

    # ── CVXPY variables ─────────────────────────────────────────────────
    q = cp.Variable(name="quota_share", nonneg=True)   # fraction ceded
    t = cp.Variable(name="var_threshold")               # VaR threshold (unconstrained)
    z = cp.Variable(m, nonneg=True, name="cvar_excess") # excess above threshold

    # ── Net retained cost per scenario ──────────────────────────────────
    # TC_i = (1-q) * S_i + q * mean_S * (1+loading)
    #      = S_i + q * (mean_S * (1+loading) - S_i)
    # In matrix form: TC = S + q * (mean_S*(1+loading) - S)
    premium_per_unit = mean_S * (1.0 + loading)
    TC = S + q * (premium_per_unit - S)   # shape (m,), linear in q

    # ── CVaR expression (Rockafellar-Uryasev 2000) ──────────────────────
    # CVaR_α = min_{t} { t + 1/((1-α)·m) · Σᵢ max(TC_i - t, 0) }
    # CVXPY represents the max as: z_i ≥ TC_i - t, z_i ≥ 0
    cvar_obj = t + (1.0 / ((1.0 - alpha) * m)) * cp.sum(z)

    # ── Constraints ─────────────────────────────────────────────────────
    constraints = [
        z >= TC - t,                        # CVaR auxiliary constraint
        q >= q_min,
        q <= q_max,
    ]

    if budget is not None:
        xl_cost = q * premium_per_unit      # total reinsurance premium
        constraints.append(xl_cost <= budget)

    # ── Solve ────────────────────────────────────────────────────────────
    problem = cp.Problem(cp.Minimize(cvar_obj), constraints)
    problem.solve(solver=cp.CLARABEL)

    if problem.status not in ["optimal", "optimal_inaccurate"]:
        raise RuntimeError(
            f"CVXPY solver did not converge: {problem.status}\n"
            "Try a different solver: cp.ECOS, cp.SCS, cp.MOSEK"
        )

    q_star    = float(q.value)
    opt_cost  = float(q_star * premium_per_unit)
    opt_cvar  = float(problem.value)
    gross_cvar = _cvar(S, alpha)

    return QuotaShareResult(
        optimal_q=q_star,
        optimal_cvar=opt_cvar,
        reinsurance_cost=opt_cost,
        gross_cvar=gross_cvar,
        cvar_reduction_pct=(gross_cvar - opt_cvar) / gross_cvar * 100,
    )


# ── Comparison: no reinsurance / quota share / XL ──────────────────────────


def compare_structures(
    scenarios: np.ndarray,
    budget: float,
    loading: float = 0.25,
    alpha: float = 0.995,
    xl_retention_options: Optional[list[float]] = None,
) -> None:
    """
    Compare three reinsurance structures for the same budget:
      1. No reinsurance
      2. Quota share (CVXPY-optimized)
      3. XL reinsurance (grid-search-optimized)

    Outputs a side-by-side table: cost, CVaR reduction, retained CVaR.
    """
    S = scenarios
    m = len(S)
    gross_cvar = _cvar(S, alpha)
    gross_mean = float(S.mean())

    print(f"\n{'═'*68}")
    print(f"  REINSURANCE STRUCTURE COMPARISON")
    print(f"  Budget: {budget:,.2f}  │  Loading: {loading*100:.0f}%  │  CVaR level: {alpha*100:.1f}%")
    print(f"  Baseline: Gross CVaR = {gross_cvar:,.2f}  │  E[S] = {gross_mean:,.2f}")
    print(f"{'═'*68}")
    print(f"  {'Structure':28s}  {'Cost':>10}  {'Retained CVaR':>14}  {'Reduction':>9}")
    print(f"  {'─'*62}")

    # 1 — No reinsurance
    print(f"  {'No reinsurance':28s}  {'0':>10}  {gross_cvar:>14,.2f}  {'0.0%':>9}")

    # 2 — Quota share (CVXPY)
    try:
        qs = optimize_quota_share_cvxpy(
            scenarios, loading=loading, alpha=alpha, budget=budget
        )
        print(
            f"  {'Quota share (CVXPY optimal)':28s}  "
            f"{qs.reinsurance_cost:>10,.2f}  "
            f"{qs.optimal_cvar:>14,.2f}  "
            f"{qs.cvar_reduction_pct:>8.1f}%"
        )
    except Exception as e:
        print(f"  {'Quota share':28s}  [CVXPY error: {e}]")

    # 3 — XL reinsurance (grid search)
    frontier = efficient_frontier_xl(
        scenarios, loading=loading, alpha=alpha, budget=budget
    )
    xl_retained = frontier.optimal_cvar
    xl_reduction = (gross_cvar - xl_retained) / gross_cvar * 100
    print(
        f"  {'XL reinsurance (grid search)':28s}  "
        f"{frontier.optimal_cost:>10,.2f}  "
        f"{xl_retained:>14,.2f}  "
        f"{xl_reduction:>8.1f}%"
    )
    print(f"  XL optimal retention: {frontier.optimal_retention:,.2f}")
    print(f"{'═'*68}")
    print(
        "\n  Interpretation:\n"
        "  - Quota share reduces risk proportionally across ALL scenarios\n"
        "  - XL reinsurance only kicks in above the retention — more efficient\n"
        "    for tail risk (the right structure for bluberri's mining clients)\n"
        "  - CVXPY finds the mathematically optimal quota share fraction\n"
        "  - The grid search approximates the optimal XL retention\n"
    )


def print_frontier(result: EfficientFrontierResult) -> None:
    """
    Print the efficient frontier as a text table.
    Shows the tradeoff between reinsurance cost and retained CVaR.
    """
    print(f"\n{'═'*60}")
    print(f"  EFFICIENT FRONTIER — XL Reinsurance")
    print(f"  CVaR level: {result.alpha*100:.1f}%  │  Gross CVaR (no reinsurance): {result.gross_cvar:,.2f}")
    print(f"{'═'*60}")
    print(f"  {'Retention':>12}  {'Cost':>12}  {'CVaR(net+cost)':>14}  {'CVaR reduction':>14}")
    print(f"  {'─'*56}")

    step = max(1, len(result.retentions) // 10)
    for i in range(0, len(result.retentions), step):
        r      = result.retentions[i]
        cost   = result.reinsurance_costs[i]
        cvar   = result.retained_cvar[i]
        red    = (result.gross_cvar - cvar) / result.gross_cvar * 100
        marker = " ← optimal" if abs(r - result.optimal_retention) < 1e-6 else ""
        print(f"  {r:>12,.2f}  {cost:>12,.2f}  {cvar:>14,.2f}  {red:>13.1f}%{marker}")

    print(f"{'═'*60}")
    print(
        f"\n  Optimal retention: {result.optimal_retention:,.2f}\n"
        f"  Reinsurance cost:  {result.optimal_cost:,.2f}\n"
        f"  Retained CVaR:     {result.optimal_cvar:,.2f}\n"
        f"  CVaR reduction:    {(result.gross_cvar - result.optimal_cvar)/result.gross_cvar*100:.1f}%\n"
    )


# ── Helpers ────────────────────────────────────────────────────────────────


def _cvar(S: np.ndarray, alpha: float) -> float:
    threshold = np.percentile(S, alpha * 100)
    tail = S[S >= threshold]
    return float(tail.mean()) if len(tail) > 0 else float(threshold)


# ── Demo ────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__file__.rsplit("/numerics", 1)[0]))
    from numerics.aggregate_simulation import simulate_lognormal, print_summary

    print("=" * 65)
    print("  MODULE 9 DEMO: Optimal Reinsurance for a Mining Portfolio")
    print("=" * 65)
    print("""
Portfolio: Mining company, general liability line
  - λ = 8 expected claims per year
  - Lognormal severity: μ = 10 (≈ $22k median), σ = 1.2 (heavy skew)
  - Budget: 20,000 monetary units for reinsurance
  - Goal: minimize CVaR 99.5% of total retained cost
""")

    # Step 1: Simulate aggregate losses
    print("Step 1: Simulating 100,000 aggregate loss scenarios...")
    result = simulate_lognormal(
        lambda_freq=8.0, mu_sev=10.0, sigma_sev=1.2, n_sim=100_000
    )
    print_summary(result, label="Mining Liability Portfolio")

    # Step 2: Efficient frontier for XL reinsurance
    print("\nStep 2: Computing efficient frontier for XL reinsurance...")
    frontier = efficient_frontier_xl(
        result.scenarios,
        loading=0.25,
        alpha=0.995,
        budget=20_000,
    )
    print_frontier(frontier)

    # Step 3: Compare all structures
    print("\nStep 3: Comparing reinsurance structures at budget = 20,000...")
    compare_structures(
        result.scenarios,
        budget=20_000,
        loading=0.25,
        alpha=0.995,
    )

    print(
        "\n[KEY INSIGHT]\n"
        "The efficient frontier shows every possible (cost, CVaR) pair.\n"
        "The optimal point balances premium spend against tail risk reduction.\n"
        "This is the exact calculation in Curriculum Module 9 — but running\n"
        "on 100,000 Monte Carlo scenarios instead of a textbook formula.\n"
    )
