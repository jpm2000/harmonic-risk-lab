"""
Trial 06: Concentration Risk — Single Point of Failure.
────────────────────────────────────────────────────────
Source:  Marsh "Mining Losses Uncovered" (2025). Patrick Walker, Rio Tinto.
         Machinery breakdown = 16.5% of $15.3B losses; BI share > 82%.
Context: "Dependence on single, high-capacity machines amplifies single-point failures."

HOW TO RUN:
  python3 trials/t06_concentration_risk/run_trial.py
  python3 trials/t06_concentration_risk/run_trial.py --dry-run
  python3 trials/t06_concentration_risk/run_trial.py --show-example
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


def show_concentration_example() -> None:
    """Print a worked example of concentration risk using real mining numbers."""
    console.print(Rule("[bold]Worked Example: Concentration Risk in a Silver Mine[/bold]"))
    console.print("""
Scenario: Pan American Silver — La Colorada (Mexico)
  Total daily silver production: 5,000 oz/day
  Silver price: $32/oz
  Daily revenue: $160,000/day

Option A: ONE large SAG mill (f = 1.0)
  Single machine handles 100% of ore processing.
  One failure = 100% production loss.

Option B: TWO equal mills (n = 2, f = 0.50 each)
  Each mill handles 50% of ore.
  One failure = 50% production loss.

Option C: FOUR equal mills (n = 4, f = 0.25 each)
  Each mill handles 25% of ore.
  One failure = 25% production loss.

Recovery time (replace/repair SAG mill): 90 days
""")

    table = Table(title="BI Loss vs. Machine Configuration (90-day recovery)")
    table.add_column("Configuration", style="bold")
    table.add_column("f", justify="right")
    table.add_column("BI Loss ($)", justify="right")
    table.add_column("vs. Option A", justify="right")
    table.add_column("Insurance premium")

    base_bi = 160_000 * 90
    configs = [
        ("1 large mill (Option A)", 1.0),
        ("2 equal mills (Option B)", 0.50),
        ("4 equal mills (Option C)", 0.25),
        ("10 small units", 0.10),
    ]
    for label, f in configs:
        bi = f * base_bi
        ratio = bi / base_bi
        table.add_row(
            label, f"{f:.2f}", f"${bi:,.0f}",
            f"{ratio:.0%}", "↓" if f < 1.0 else "baseline"
        )
    console.print(table)

    console.print("""
PROPERTIES BEING PROVED:
  Property 2: BI loss(f=1.0) >= BI loss(f=0.5) >= BI loss(f=0.25)
              → concentration always costs more than diversification
  Property 4: diversified_bi_loss(n=4) <= concentrated_bi_loss(f=1.0)
              → any diversification is better than full concentration
  Property 5: BI(n=2) >= BI(n=4) >= BI(n=10)
              → adding machines always reduces single-failure exposure
  Property 6: concentration_premium(f=1.0, n=4) = BI(1.0) - BI(0.25) >= 0
              → the price of concentration is always non-negative

These hold for ALL valid inputs — not just these 4 configurations.
""")


async def run(dry_run: bool = False) -> None:
    verification_prompt = """\
Verify the following properties for the functions in concentration_model.c:

1. concentrated_bi_loss(f, daily_revenue, recovery_days): returns a value >= 0
   for all 0 < f <= 1.0, daily_revenue >= 0, recovery_days >= 0.
   Returns -1.0 for invalid inputs (f <= 0 or f > 1 or negative inputs).

2. concentrated_bi_loss is monotone in f: for fixed daily_revenue >= 0 and
   recovery_days >= 0, if f1 >= f2 > 0, then
   concentrated_bi_loss(f1,...) >= concentrated_bi_loss(f2,...).
   Higher concentration fraction always produces at least as large a BI loss.

3. concentrated_bi_loss is monotone in recovery_days: for fixed f and
   daily_revenue >= 0, if days1 >= days2 >= 0, then
   concentrated_bi_loss(f, daily_revenue, days1) >=
   concentrated_bi_loss(f, daily_revenue, days2).

4. diversified_bi_loss(n_machines, daily_revenue, recovery_days): returns a
   value <= concentrated_bi_loss(1.0, daily_revenue, recovery_days) for all
   n_machines >= 1, daily_revenue >= 0, recovery_days >= 0.
   Splitting production across n machines always reduces single-failure BI loss.
   Returns -1.0 for n_machines < 1 or negative inputs.

5. diversified_bi_loss is monotone decreasing in n_machines: for fixed
   daily_revenue >= 0 and recovery_days >= 0, if n1 >= n2 >= 1, then
   diversified_bi_loss(n1,...) <= diversified_bi_loss(n2,...).
   More machines always means less exposure per failure.

6. concentration_premium(f, n_equivalent, daily_revenue, recovery_days): returns
   a value >= 0 when f >= 1/n_equivalent, daily_revenue >= 0, recovery_days >= 0.
   The extra BI exposure from concentration is always non-negative.
   Returns -1.0 for invalid inputs.

7. diversification_ratio(n_machines): returns a value in (0, 1] for n_machines >= 1.
   Ratio = 1.0 for n=1 (no diversification benefit), approaches 0 as n grows.
   Returns -1.0 for n_machines < 1.

Context: These functions model production concentration risk in mining operations.
Marsh data (2006-2025) shows machinery breakdown causes BI shares above 82% of
total losses. A single large SAG mill handling 100% of ore processing creates
full exposure to any mechanical failure, while splitting production across multiple
machines reduces single-failure BI loss proportionally.
"""

    console.print(Panel.fit(
        "[bold cyan]Trial 06 — Concentration Risk: Single Point of Failure[/bold cyan]\n"
        "[dim]Source:[/dim]  Marsh (2025) + Patrick Walker (Rio Tinto)\n"
        "[dim]Context:[/dim] Machinery breakdown = 16.5% of $15.3B losses; BI share > 82%\n"
        "[dim]Code:[/dim]    trials/t06_concentration_risk/concentration_model.c",
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
    console.print("[yellow]Waiting for result...[/yellow]")

    tasks, _ = await project.get_tasks(limit=1)
    await tasks[0].wait_for_completion(interactive=False)

    status  = tasks[0].status.name
    summary = tasks[0].output_summary or ""

    console.print(Rule())
    status_color = "green" if "SUCCESS" in status.upper() else "red"
    console.print(f"[bold {status_color}]Status:[/{status_color}] {status}")
    if summary:
        console.print(f"\n[bold]Summary:[/bold]\n{summary}")

    _append_result("t06_concentration_risk", status, summary)
    console.print("\n[dim]Result saved to trials/RESULTS.md[/dim]")
    console.print(
        "\n→ Next trial: [cyan]python3 trials/t07_tailings_pml/run_trial.py[/cyan]"
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
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--show-example", action="store_true")
    args = parser.parse_args()

    if args.show_example:
        show_concentration_example()

    asyncio.run(run(dry_run=args.dry_run))
