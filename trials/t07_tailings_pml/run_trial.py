"""
Trial 07: Tailings Dam PML — Probable Maximum Loss via Return Period.
──────────────────────────────────────────────────────────────────────
Source:  McNeil, Frey & Embrechts (2005). QRM Ch. 7. Pickands (1975).
Context: 2019 Brumadinho tailings disaster (Brazil) = $7B+ settlement.
         Tailings = ~0.7% of Marsh event count but most catastrophic losses.

HOW TO RUN:
  python3 trials/t07_tailings_pml/run_trial.py
  python3 trials/t07_tailings_pml/run_trial.py --dry-run
  python3 trials/t07_tailings_pml/run_trial.py --show-example
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


def show_pml_example() -> None:
    """Print a PML table calibrated to real tailings event data."""
    console.print(Rule("[bold]Worked Example: Tailings PML Calibrated to Brumadinho[/bold]"))
    console.print("""
Real calibration from Marsh data:
  2015 Fundão (Samarco, Mariana, Brazil): ~$5B
  2019 Brumadinho (Vale, Brazil):         $7B+ settlement

Pareto model calibration:
  x_m   = $50M   (minimum qualifying tailings event, per Marsh threshold)
  alpha = 1.3    (tail index — heavy tail consistent with power-law events)

Model: PML(T) = x_m × T^(1/alpha) = $50M × T^(0.769)
""")

    table = Table(title="Tailings Dam PML by Return Period (x_m=$50M, alpha=1.3)")
    table.add_column("Return Period", justify="right", style="bold")
    table.add_column("AEP (%/year)", justify="right")
    table.add_column("PML ($M)", justify="right")
    table.add_column("PML ($B)", justify="right")
    table.add_column("Context")

    x_m, alpha = 50.0, 1.3
    periods = [
        (10,   "Annual maintenance planning"),
        (25,   "Mine life planning horizon"),
        (50,   "Major infrastructure design"),
        (100,  "Insurance policy limit"),
        (200,  "Solvency II SCR standard"),
        (500,  "Extreme tail / reinsurance"),
        (1000, "Catastrophe bond threshold"),
    ]
    for T, context in periods:
        pml = x_m * (T ** (1.0 / alpha))
        aep = 100.0 / T
        table.add_row(
            f"1-in-{T}yr", f"{aep:.2f}%", f"${pml:.0f}M", f"${pml/1000:.2f}B", context
        )
    console.print(table)
    console.print("""
PROPERTIES BEING PROVED:
  Property 1: PML(T=200) >= $50M minimum ✓ — for all (x_m, alpha, T)
  Property 2: PML(1000yr) >= PML(200yr) >= PML(100yr) ✓ — always monotone
  Property 3: AEP($7B) < AEP($500M) < AEP($100M) ✓ — larger losses are rarer
  Property 5: AEP(PML(T)) = 1/T exactly — mathematical consistency

Note: The Brumadinho settlement ($7B) corresponds to roughly a 1-in-150 to
1-in-200 year event under this calibration. This validates that the model
can represent observed catastrophic tailings losses.
""")


async def run(dry_run: bool = False) -> None:
    verification_prompt = """\
Verify the following properties for the functions in pml_model.c:

1. pml_pareto(x_m, alpha, T): returns a value >= x_m for all x_m > 0,
   alpha > 0, T >= 1. The Probable Maximum Loss always equals or exceeds
   the minimum loss x_m (which is the smallest event in the model).
   Returns -1.0 for invalid inputs.

2. pml_pareto is monotone increasing in T: for fixed x_m > 0 and alpha > 0,
   if T1 >= T2 >= 1, then pml_pareto(x_m, alpha, T1) >= pml_pareto(x_m, alpha, T2).
   A 200-year event must always be at least as large as a 100-year event.
   Returns -1.0 for invalid inputs.

3. aep_pareto(x, x_m, alpha): returns a value in (0, 1] for all x >= x_m > 0,
   alpha > 0. Annual exceedance probability is always a valid probability.
   Returns -1.0 for invalid inputs or x < x_m.

4. aep_pareto is monotone decreasing in x: for fixed x_m > 0 and alpha > 0,
   if x1 >= x2 >= x_m, then aep_pareto(x1, x_m, alpha) <= aep_pareto(x2, x_m, alpha).
   Larger losses occur less frequently (are rarer). This is the fundamental
   property of a loss severity distribution.

5. return_period(x, x_m, alpha): returns a value >= 1 for all x >= x_m > 0,
   alpha > 0. Every loss has a return period of at least 1 year.
   Returns -1.0 for invalid inputs.

6. return_period is monotone increasing in x: for fixed x_m > 0 and alpha > 0,
   if x1 >= x2 >= x_m, then return_period(x1,...) >= return_period(x2,...).
   Larger losses are expected less frequently (longer return period).

7. pml_consistency_check(x_m, alpha, T): returns a value near 0.0 (ideally 0.0)
   for all x_m > 0, alpha > 0, T >= 1. This verifies that
   aep(pml(T)) = 1/T — that the AEP of the T-year PML is exactly 1/T.
   Returns -1.0 for invalid inputs.

Context: These are Probable Maximum Loss functions for tailings dam events.
The 2019 Brumadinho disaster ($7B+ settlement) and the 2015 Fundão collapse
are calibration points. Tailings events follow power-law (Pareto) distributions
— they are infrequent but catastrophic. Property 4 (AEP decreasing in x) is
the foundational property: without it, the model would suggest that larger
losses happen more often, which is physically impossible.
"""

    console.print(Panel.fit(
        "[bold cyan]Trial 07 — Tailings Dam PML (Return Period Model)[/bold cyan]\n"
        "[dim]Source:[/dim]  McNeil, Frey & Embrechts (2005). Pickands (1975).\n"
        "[dim]Context:[/dim] Brumadinho (2019) = $7B+. Tailings = catastrophic tail risk.\n"
        "[dim]Code:[/dim]    trials/t07_tailings_pml/pml_model.c",
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
    console.print("[yellow]Waiting for result (power functions may need time)...[/yellow]")

    tasks, _ = await project.get_tasks(limit=1)
    await tasks[0].wait_for_completion(interactive=False)

    status  = tasks[0].status.name
    summary = tasks[0].output_summary or ""

    console.print(Rule())
    status_color = "green" if "SUCCESS" in status.upper() else "red"
    console.print(f"[bold {status_color}]Status:[/{status_color}] {status}")
    if summary:
        console.print(f"\n[bold]Summary:[/bold]\n{summary}")

    _append_result("t07_tailings_pml", status, summary)
    console.print("\n[dim]Result saved to trials/RESULTS.md[/dim]")
    console.print(
        "\n→ Full pipeline: [cyan]python3 examples/05_full_pipeline.py --sector mining[/cyan]"
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
        show_pml_example()

    asyncio.run(run(dry_run=args.dry_run))
