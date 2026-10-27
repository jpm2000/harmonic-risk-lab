"""
Trial 05: Business Interruption Multiplier — The 80% Rule.
───────────────────────────────────────────────────────────
Source:  Marsh "Mining Losses Uncovered" (2025). BI = ~80% of total losses.
Context: Pan American Silver 2025 — 2 fatalities triggered multi-site shutdowns,
         illustrating how a safety incident produces months of production loss
         far exceeding the direct incident cost.

HOW TO RUN:
  python trials/t05_bi_multiplier/run_trial.py
  python trials/t05_bi_multiplier/run_trial.py --dry-run         (see prompt only)
  python trials/t05_bi_multiplier/run_trial.py --show-example    (real-world numbers)
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


def show_bi_example() -> None:
    """Print a concrete BI multiplier calculation grounded in Marsh/PAS data."""
    console.print(Rule("[bold]Worked Example: BI Multiplier for a Mining Incident[/bold]"))
    console.print("""
Marsh finding: BI = 80% of total gross losses in mining (2006-2025).
Pan American Silver 2025: 2 fatalities → shutdowns at Jacobina (Brazil)
and Shahuindo (Peru), triggering safety audits and corrective action plans.

──────────────────────────────────────────────────────────────────
Scenario: Fire at a single grinding mill (machinery breakdown = 16.5% of losses)

Property damage (PD):
  Equipment replacement + structural repair = $15M
  That's the physical damage. But the mill is down.

Business interruption (BI):
  Mill daily output:     2,000 tonnes/day
  Silver grade:         350 g/tonne
  Silver price:         $32/oz = ~$1.03/g
  Daily silver value:    2,000 × 350 × $1.03 ≈ $720,000/day
  Recovery time:         90 days (sourcing + installing a replacement mill)

  BI loss = $720,000/day × 90 days = $64.8M

Total insured loss:
  = PD + BI = $15M + $64.8M = $79.8M

BI ratio   = $64.8M / $79.8M = 81.2%  ← matches Marsh average of ~80%
Multiplier = $79.8M / $15.0M = 5.32×  ← total is 5× the physical damage
──────────────────────────────────────────────────────────────────

PROPERTIES BEING PROVED:
  1. total_loss >= pd_loss:             $79.8M >= $15M ✓ (for ALL inputs)
  2. bi_ratio ∈ [0, 1):                 0.812 < 1.0   ✓ (for ALL pd > 0)
  3. total_loss monotone in days:       90 days > 45 days → $79.8M > $47.4M ✓
  4. bi_ratio monotone in days:         longer outage → higher BI share ✓
  5. bi_loss >= 0:                      $64.8M >= 0   ✓ (always)
  6. bi_multiplier >= 1.0:              5.32 >= 1.0   ✓ (for pd > 0)

These properties hold for EVERY possible input combination —
Aristotle proves this across infinite parameter space.
""")

    table = Table(title="BI Multiplier at Different Recovery Times (same $15M PD)")
    table.add_column("Recovery Days", justify="right")
    table.add_column("BI Loss ($M)", justify="right")
    table.add_column("Total Loss ($M)", justify="right")
    table.add_column("BI Ratio", justify="right")
    table.add_column("Multiplier", justify="right")
    for days, bi in [(0, 0), (30, 21.6), (60, 43.2), (90, 64.8), (180, 129.6), (365, 262.8)]:
        total = 15 + bi
        ratio = bi / total if total > 0 else 0
        mult = total / 15
        table.add_row(
            str(days), f"{bi:.1f}", f"{total:.1f}",
            f"{ratio:.1%}", f"{mult:.2f}×"
        )
    console.print(table)
    console.print(
        "\n[dim]As recovery time grows, the BI ratio approaches 1.0 (100%) "
        "and the multiplier grows without bound. Property 4 proves this "
        "monotonicity holds for ALL valid inputs.[/dim]\n"
    )


async def run(dry_run: bool = False) -> None:
    verification_prompt = """\
Verify the following properties for the functions in bi_model.c:

1. bi_loss_amount(daily_revenue, recovery_days): returns a value >= 0
   for all daily_revenue >= 0 and recovery_days >= 0.
   Returns -1.0 for negative inputs.

2. total_insured_loss(pd_loss, daily_revenue, recovery_days): returns a value
   >= pd_loss for all pd_loss >= 0, daily_revenue >= 0, recovery_days >= 0.
   Total insured loss always equals or exceeds the property damage alone —
   business interruption never reduces the total.
   Returns -1.0 for negative inputs.

3. total_insured_loss is monotone increasing in recovery_days: for any fixed
   pd_loss >= 0 and daily_revenue >= 0, if recovery_days_1 >= recovery_days_2
   (both >= 0), then total_insured_loss(..., recovery_days_1) >=
   total_insured_loss(..., recovery_days_2). Longer outage = higher total loss.

4. bi_share(pd_loss, daily_revenue, recovery_days): returns a value in [0, 1)
   for all pd_loss > 0, daily_revenue >= 0, recovery_days >= 0.
   The BI fraction can never reach or exceed 100% of the total when pd > 0.
   Returns -1.0 for negative inputs.

5. bi_share is monotone increasing in recovery_days: for any fixed pd_loss > 0
   and daily_revenue > 0, if recovery_days_1 >= recovery_days_2 (both >= 0),
   then bi_share(pd_loss, daily_revenue, recovery_days_1) >=
   bi_share(pd_loss, daily_revenue, recovery_days_2).
   Longer outage = higher fraction of loss attributable to business interruption.

6. bi_multiplier(pd_loss, daily_revenue, recovery_days): returns a value >= 1.0
   for all pd_loss > 0, daily_revenue >= 0, recovery_days >= 0.
   The multiplier equals total_loss / pd_loss, which is always >= 1.0 since
   total_loss >= pd_loss (property 2).
   Returns -1.0 for pd_loss <= 0 or negative inputs.

Context: These are business interruption insurance formulas for mining operations.
Marsh data (2006-2025) shows BI averages 80% of total gross mining losses.
A single grinding mill failure can halt production for months, meaning the
total insured loss is typically 3-7× the physical equipment damage.
Property 4 (bi_share < 1) and Property 2 (total >= pd) are underwriting invariants:
if either fails, the model would produce nonsensical or fraudulent insurance prices.
"""

    console.print(Panel.fit(
        "[bold cyan]Trial 05 — Business Interruption Multiplier (The 80% Rule)[/bold cyan]\n"
        "[dim]Source:[/dim] Marsh Mining Losses Uncovered (2025)\n"
        "[dim]Context:[/dim] BI = ~80% of $15.3B mining losses (2006-2025)\n"
        "[dim]Code:[/dim]   trials/t05_bi_multiplier/bi_model.c",
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

    _append_result("t05_bi_multiplier", status, summary)
    console.print("\n[dim]Result saved to trials/RESULTS.md[/dim]")
    console.print(
        "\n→ Full pipeline: [cyan]python examples/05_full_pipeline.py --sector mining[/cyan]"
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
    parser.add_argument("--show-example", action="store_true", help="Print BI example first")
    args = parser.parse_args()

    if args.show_example:
        show_bi_example()

    asyncio.run(run(dry_run=args.dry_run))
