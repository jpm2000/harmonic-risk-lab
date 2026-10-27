"""
Trial 04: EVT VaR — Heavy-Tail Mining Losses (Peaks-over-Threshold).
──────────────────────────────────────────────────────────────────────
Source:  McNeil, Frey & Embrechts (2005). Quantitative Risk Management. Ch. 7.
Context: Marsh mining loss database ($15.3B, 2006-2025). Fire/explosion (25.7%),
         geotechnical/tailings (10.4%+) follow power-law tails, not normal.

HOW TO RUN:
  python trials/t04_evt_var/run_trial.py
  python trials/t04_evt_var/run_trial.py --dry-run         (see prompt only)
  python trials/t04_evt_var/run_trial.py --show-example    (calibrated example)
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

load_dotenv()
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

console = Console()
TRIAL_DIR = Path(__file__).parent


def show_calibration_example() -> None:
    """Print a concrete EVT calibration to make the math tangible."""
    console.print(Rule("[bold]Worked Example: EVT VaR for a Mining Portfolio[/bold]"))
    console.print("""
Marsh data context:
  - $15.3B insured mining losses, 2006–2025
  - Fire/explosion: 25.7%  |  Flood: 22.5%  |  Geotechnical: 10.4%
  - Single events: Brumadinho tailings (2019) = $7B+ settlement

Hypothetical calibration for a copper mining portfolio:
  N = 200 loss events over 10 years
  Threshold u = $10M (only large losses enter GPD fit)
  N_u = 40 exceedances above $10M  →  p_u = 40/200 = 0.20

GPD fit on exceedances (typical mining parameters):
  ξ (tail index) = 0.50  [heavy tail — consistent with fire/geotechnical]
  σ (scale)      = $15M

Normal approximation (same portfolio, for comparison):
  μ = $8M/event × 20 events/year = $160M/year
  σ_n = $120M/year
  z_99.5% = 2.576

─────────────────────────────────────────────────────
  VaR (99.5%) comparison:

  Normal VaR  = μ + z · σ_n
              = 160 + 2.576 × 120
              = $469M

  EVT VaR     = u + (σ/ξ) · [(p_u / (1-α))^ξ - 1]
              = 10 + (15/0.5) · [(0.20 / 0.005)^0.50 - 1]
              = 10 + 30 · [40^0.50 - 1]
              = 10 + 30 · [6.32 - 1]
              = 10 + 30 · 5.32
              = 10 + 159.7
              = $169.7M  (as excess above threshold)
              → Absolute VaR ≈ $170M + base

  EVT ES (CVaR, 99.5%) = (VaR + σ - ξ·u) / (1 - ξ)
                       = (170 + 15 - 0.5·10) / (1 - 0.5)
                       = (170 + 15 - 5) / 0.5
                       = 180 / 0.5
                       = $360M beyond threshold

PROPERTY BEING PROVED:
  gpd_es >= gpd_var for ALL valid (u, sigma, xi, p_u, alpha) inputs.
  Not just for these numbers — for every mining portfolio ever.
""")

    table = Table(title="Tail Risk Comparison: Normal vs. EVT (99.5% confidence)")
    table.add_column("Model", style="bold")
    table.add_column("VaR 99.5%")
    table.add_column("ES 99.5%")
    table.add_column("Capital Required")
    table.add_row("Normal (Gaussian)", "$469M", "~$530M", "$469M - E[S]")
    table.add_row(
        "EVT (GPD, ξ=0.50)", "$170M+ threshold", "$360M+ threshold",
        "Higher at extreme quantiles"
    )
    table.add_row("Brumadinho actual", "$7,000M+", "—", "Destroyed normal models")
    console.print(table)
    console.print(
        "\n[dim]Takeaway: EVT captures the Brumadinho-scale tail. Normal models "
        "would have predicted this as essentially impossible.[/dim]\n"
    )


async def run(dry_run: bool = False) -> None:
    verification_prompt = """\
Verify the following properties for the functions in evt_model.c:

1. gpd_var(u, sigma, xi, p_u, alpha): returns a value >= u (the threshold)
   for all valid inputs where u >= 0, sigma > 0, 0 < xi < 2, 0 < p_u <= 1,
   0 < alpha < 1. Returns -1.0 for invalid inputs.

2. gpd_es(u, sigma, xi, p_u, alpha): returns a value >= gpd_var(u, sigma, xi, p_u, alpha)
   for all valid inputs where 0 < xi < 1. This is the coherence property:
   Expected Shortfall is always >= Value-at-Risk at the same confidence level.
   Returns -1.0 for invalid inputs or when xi >= 1.

3. gpd_var is monotone increasing in alpha: for any fixed (u, sigma, xi, p_u),
   if alpha1 >= alpha2 (both valid), then gpd_var(..., alpha1) >= gpd_var(..., alpha2).
   Higher confidence level must always produce a higher or equal VaR.

4. normal_var(mu, sigma_n, z_alpha): returns a value >= mu >= 0 for valid inputs
   where mu >= 0, sigma_n > 0, z_alpha >= 0. Returns -1.0 for invalid inputs.

5. evt_tail_premium(u, sigma, xi, p_u, alpha, mu, sigma_n, z_alpha): returns
   a finite value (not -1.0) when both gpd_var and normal_var are valid.
   Returns -1.0 if either component is invalid.

Context: These are EVT/GPD functions for quantifying extreme mining losses.
Mining loss data (Marsh, 2006-2025) shows fire/explosion and geotechnical events
follow power-law tails (xi > 0), meaning normal VaR systematically underestimates
capital requirements. Property 2 (ES >= VaR) is the key coherence invariant —
a violation would mean the capital model underestimates tail losses.
"""

    console.print(Panel.fit(
        "[bold cyan]Trial 04 — EVT VaR for Heavy-Tail Mining Losses[/bold cyan]\n"
        "[dim]Source:[/dim] McNeil, Frey & Embrechts (2005), QRM Chapter 7\n"
        "[dim]Context:[/dim] Marsh $15.3B mining loss database (2006-2025)\n"
        "[dim]Code:[/dim]   trials/t04_evt_var/evt_model.c",
        title="harmonic-risk-lab",
    ))

    console.print(Rule("[bold]Verification Prompt[/bold]"))
    console.print(Panel(verification_prompt, border_style="dim"))

    if dry_run:
        console.print("[yellow]--dry-run: stopping before submission.[/yellow]")
        return

    api_key = os.getenv("ARISTOTLE_API_KEY")
    if not api_key:
        console.print("[red bold]Error:[/red bold] ARISTOTLE_API_KEY not set in .env")
        return

    import aristotlelib
    aristotlelib.set_api_key(api_key)

    from aristotlelib import AgentQuestionsSetting, Project

    console.print("\n[yellow]Submitting to Aristotle...[/yellow]")
    project = await Project.create_from_directory(
        verification_prompt,
        str(TRIAL_DIR),
        agent_questions_setting=AgentQuestionsSetting.DISABLED,
    )
    console.print(f"[green]Project created:[/green] {project.status.name}")
    console.print("[yellow]Waiting for result (EVT proofs can take a few minutes)...[/yellow]")

    tasks, _ = await project.get_tasks(limit=1)
    await tasks[0].wait_for_completion(interactive=False)

    status  = tasks[0].status.name
    summary = tasks[0].output_summary or ""

    console.print(Rule())
    status_color = "green" if "SUCCESS" in status.upper() else "red"
    console.print(f"[bold {status_color}]Status:[/{status_color}] {status}")
    if summary:
        console.print(f"\n[bold]Summary:[/bold]\n{summary}")

    _append_result("t04_evt_var", status, summary)
    console.print("\n[dim]Result saved to trials/RESULTS.md[/dim]")
    console.print(
        "\n→ Next trial: [cyan]python trials/t05_bi_multiplier/run_trial.py[/cyan]"
    )


def _append_result(trial_id: str, status: str, summary: str) -> None:
    results_path = REPO_ROOT / "trials" / "RESULTS.md"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    icon = "✓" if "SUCCESS" in status.upper() else "✗"
    entry = (
        f"\n## {icon} {trial_id} — {timestamp}\n"
        f"**Status:** {status}\n"
        f"**Summary:** {summary or '(none)'}\n"
    )
    with open(results_path, "a") as f:
        f.write(entry)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print prompt only, don't submit")
    parser.add_argument("--show-example", action="store_true", help="Print calibration example first")
    args = parser.parse_args()

    if args.show_example:
        show_calibration_example()

    asyncio.run(run(dry_run=args.dry_run))
