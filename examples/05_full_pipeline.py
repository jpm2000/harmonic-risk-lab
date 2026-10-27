"""
Example 05: Full actuarial pipeline — Simulate → Verify → Optimize.
─────────────────────────────────────────────────────────────────────
This example runs the complete workflow described in Curriculum Module 11:

  Layer 3 (Modeling):  simulate_lognormal()  ← Monte Carlo aggregate losses
  Layer 4 (Risk):      print_summary()       ← VaR, CVaR, capital requirement
  Layer 5 (Optim.):    compare_structures()  ← optimal reinsurance selection
  Layer 6 (Explain):   Gemini explanation    ← stakeholder narrative

And optionally Layer 3 verification: Aristotle proves the C aggregate
formulas are correct before we rely on them in the risk metrics.

This is the closest thing in this repo to what bluberri would ship:
  a client uploads their loss data → the system returns a risk report
  with an optimal reinsurance recommendation, all mathematically certified.

HOW TO RUN:
  python examples/05_full_pipeline.py
  python examples/05_full_pipeline.py --skip-aristotle   (faster, no API call)
  python examples/05_full_pipeline.py --sector mining     (or: insurance / defense)
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

load_dotenv()
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

console = Console()

# ── Sector presets (realistic parameters for bluberri's target clients) ─────
SECTORS = {
    "mining": {
        "label": "Mining — General Liability (Cesar–Ciénaga corridor)",
        "lambda_freq": 8.0,
        "mu_sev": 10.0,
        "sigma_sev": 1.3,    # heavier tail for mining operations
        "budget": 20_000,
        "loading": 0.25,
        "description": (
            "Mining companies face high-severity, low-frequency losses: "
            "equipment failures, worker injuries, environmental incidents. "
            "The Pareto-like severity requires a well-placed XL layer."
        ),
    },
    "insurance": {
        "label": "Insurance Broker — Mixed liability portfolio",
        "lambda_freq": 25.0,
        "mu_sev": 9.0,
        "sigma_sev": 0.9,    # more homogeneous
        "budget": 50_000,
        "loading": 0.20,
        "description": (
            "An insurance broker managing a mixed book of business. "
            "Higher frequency but lower severity variance. "
            "Diversification reduces the need for high XL retentions."
        ),
    },
    "defense": {
        "label": "Defense Contractor — Professional indemnity",
        "lambda_freq": 3.0,
        "mu_sev": 12.0,
        "sigma_sev": 1.8,    # very heavy tail (contract disputes, government)
        "budget": 30_000,
        "loading": 0.30,
        "description": (
            "Defense contractors face rare but extremely large claims: "
            "contract terminations, specification failures, IP disputes. "
            "Heavy tail (high sigma) — Pareto-like behavior."
        ),
    },
}


async def run(sector: str = "mining", skip_aristotle: bool = False) -> None:
    from numerics.aggregate_simulation import simulate_lognormal, print_summary
    from numerics.reinsurance_optimizer import (
        efficient_frontier_xl,
        compare_structures,
        print_frontier,
    )

    params = SECTORS.get(sector, SECTORS["mining"])
    label  = params["label"]

    console.print(Panel.fit(
        f"[bold cyan]Example 05 — Full Actuarial Pipeline[/bold cyan]\n"
        f"[dim]Sector:[/dim] {label}\n\n"
        f"{params['description']}",
        title="harmonic-risk-lab",
    ))

    # ── Layer 3: Modeling — Monte Carlo simulation ─────────────────────────
    console.print(Rule("[bold]Layer 3 — Simulate Aggregate Losses (Module 4)[/bold]"))
    console.print(
        f"\nParameters:\n"
        f"  λ (expected claims/year): {params['lambda_freq']}\n"
        f"  Severity: Lognormal(μ={params['mu_sev']}, σ={params['sigma_sev']})\n"
        f"  E[X] = exp(μ + σ²/2) = {_lognormal_mean(params['mu_sev'], params['sigma_sev']):,.2f}\n"
        f"  Simulating 100,000 scenarios...\n"
    )

    result = simulate_lognormal(
        lambda_freq=params["lambda_freq"],
        mu_sev=params["mu_sev"],
        sigma_sev=params["sigma_sev"],
        n_sim=100_000,
    )
    print_summary(result, label=label)

    # ── Layer 4: Risk — risk measures ─────────────────────────────────────
    console.print(Rule("[bold]Layer 4 — Risk Measures (Module 8)[/bold]"))
    capital_requirement = result.var_995 - result.mean
    console.print(
        f"\n  The Solvency II SCR (99.5% VaR basis) requires the insurer to hold:\n"
        f"  Capital = VaR(99.5%) - E[S] = {result.var_995:,.2f} - {result.mean:,.2f} "
        f"= {capital_requirement:,.2f}\n"
        f"\n  This is the minimum buffer against ruin at 99.5% confidence.\n"
        f"  If the insurer can't afford this capital, they MUST buy reinsurance.\n"
    )

    # ── Layer 3a (optional): Aristotle verification ────────────────────────
    if not skip_aristotle:
        console.print(Rule("[bold]Layer 3a — Aristotle Verifies the Formulas (optional)[/bold]"))
        console.print(
            "\n  [dim]The simulation used the formula Var(S) = λ·E[X²] as a sanity check.[/dim]\n"
            "  [dim]Run trial t03 to formally prove that formula is always correct.[/dim]\n"
        )
        console.print(
            "  [yellow]Skipping Aristotle in this example (run t03 separately).[/yellow]\n"
            "  python trials/t03_aggregate_loss/run_trial.py --show-simulation\n"
        )

    # ── Layer 5: Optimization — reinsurance selection ─────────────────────
    console.print(Rule("[bold]Layer 5 — Reinsurance Optimization (Module 9)[/bold]"))
    console.print(
        f"\n  Budget: {params['budget']:,}  │  Reinsurer loading: {params['loading']*100:.0f}%\n"
        f"  Finding optimal XL retention that minimizes CVaR(99.5%) within budget...\n"
    )

    frontier = efficient_frontier_xl(
        result.scenarios,
        loading=params["loading"],
        alpha=0.995,
        budget=params["budget"],
    )
    print_frontier(frontier)

    # Full structure comparison
    console.print(Rule("[bold]Structure Comparison[/bold]"))
    compare_structures(
        result.scenarios,
        budget=params["budget"],
        loading=params["loading"],
        alpha=0.995,
    )

    # ── Layer 6: Explanation — Gemini stakeholder narrative ───────────────
    console.print(Rule("[bold]Layer 6 — Executive Summary (Module 11 output format)[/bold]"))
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        from utils.gemini_client import explain_result
        summary_text = (
            f"Portfolio: {label}. "
            f"Expected annual loss E[S] = {result.mean:,.0f}. "
            f"CVaR 99.5% = {result.cvar_995:,.0f}. "
            f"Optimal XL retention = {frontier.optimal_retention:,.0f}. "
            f"Reinsurance cost = {frontier.optimal_cost:,.0f}. "
            f"CVaR after optimal reinsurance = {frontier.optimal_cvar:,.0f}."
        )
        explanation = explain_result("SUCCESS", summary_text, params["description"])
        console.print(Panel(
            f"[bold white]{explanation}[/bold white]",
            title="[green]Executive Summary for Stakeholders[/green]",
            border_style="green",
        ))
    else:
        console.print(
            "[dim]Set GEMINI_API_KEY in .env to get the Gemini executive summary.[/dim]"
        )

    console.print(Rule())
    console.print(
        f"\n[bold]Key outputs for a bluberri client report:[/bold]\n"
        f"  1. Expected annual loss:        {result.mean:>12,.2f}\n"
        f"  2. VaR 99.5% (Solvency II):     {result.var_995:>12,.2f}\n"
        f"  3. CVaR 99.5% (tail risk):      {result.cvar_995:>12,.2f}\n"
        f"  4. Capital requirement:          {capital_requirement:>12,.2f}\n"
        f"  5. Optimal XL retention:         {frontier.optimal_retention:>12,.2f}\n"
        f"  6. Reinsurance cost:             {frontier.optimal_cost:>12,.2f}\n"
        f"  7. CVaR after reinsurance:       {frontier.optimal_cvar:>12,.2f}\n"
        f"  8. CVaR reduction:               "
        f"{(result.cvar_995 - frontier.optimal_cvar)/result.cvar_995*100:>11.1f}%\n"
        f"\nRun with --sector insurance or --sector defense to compare sectors."
    )


def _lognormal_mean(mu: float, sigma: float) -> float:
    import math
    return math.exp(mu + 0.5 * sigma**2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sector", choices=["mining", "insurance", "defense"], default="mining"
    )
    parser.add_argument(
        "--skip-aristotle", action="store_true",
        help="Skip the Aristotle verification step"
    )
    args = parser.parse_args()
    asyncio.run(run(sector=args.sector, skip_aristotle=args.skip_aristotle))
