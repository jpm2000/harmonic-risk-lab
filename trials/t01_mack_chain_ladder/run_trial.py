"""
Trial 01: Mack Chain Ladder — IBNR Reserve Verification.
──────────────────────────────────────────────────────────
Reads the spec → generates the Aristotle prompt → submits chain_ladder.c
for formal verification → appends result to trials/RESULTS.md.

HOW TO RUN:
  python trials/t01_mack_chain_ladder/run_trial.py

  Add --dry-run to see the Aristotle prompt without submitting.
  Add --show-triangle to print a worked example first.
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
from rich.syntax import Syntax
from rich.table import Table

load_dotenv()
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

console = Console()
TRIAL_DIR = Path(__file__).parent


def show_worked_example() -> None:
    """Print a concrete chain ladder calculation so the math is tangible."""
    console.print(Rule("[bold]Worked Example: Chain Ladder Development Triangle[/bold]"))
    console.print("""
Paid claims triangle (cumulative, $000s):

         Dev 1   Dev 2   Dev 3   Dev 4 (ultimate)
AY 2021  1,000   1,200   1,250   1,260  ← fully developed
AY 2022    900   1,080   1,125    ???   ← needs one more factor
AY 2023    850   1,020    ???     ???   ← needs two more factors
AY 2024    800    ???     ???     ???   ← needs three more factors

Development factors (column sums weighted):
  f_1 = (1200+1080+1020) / (1000+900+850) = 3300 / 2750 ≈ 1.200
  f_2 = (1250+1125)      / (1200+1080)    = 2375 / 2280 ≈ 1.042
  f_3 = 1260             / 1250           = 1260 / 1250 ≈ 1.008

Projected ultimates:
  AY 2022: 1,125 × 1.008 ≈ 1,134
  AY 2023: 1,020 × 1.042 × 1.008 ≈ 1,070
  AY 2024:   800 × 1.200 × 1.042 × 1.008 ≈ 1,007

IBNR reserves (ultimate − current paid):
  AY 2022: 1,134 − 1,125 =   9
  AY 2023: 1,070 − 1,020 =  50
  AY 2024: 1,007 −   800 = 207
  ─────────────────────────────
  Total IBNR:               266  ← this must be on the balance sheet

PROPERTY WE'RE PROVING:
  ibnr_reserve ≥ 0 for all accident years, ALWAYS.
  Not just for this example — for any valid inputs to the function.
""")


async def run(dry_run: bool = False) -> None:
    # ── Build the verification prompt manually (not from spec file) ────────
    # This trial uses a standalone spec — no shared spec file.
    # We define the properties inline so the trial is self-contained.
    verification_prompt = """\
Verify the following properties for the functions in chain_ladder.c:

1. development_factor(paid_t, paid_t1): returns a strictly positive value when
   both paid_t > 0 and paid_t1 > 0. Returns -1.0 when either input <= 0.

2. weighted_factor(numerator, denominator): returns a strictly positive value
   when both inputs > 0. Returns -1.0 otherwise.

3. predict_ultimate(current_paid, tail_factor): returns a value >= current_paid
   when tail_factor >= 1.0 and current_paid > 0. Returns -1.0 for invalid inputs.

4. ibnr_reserve(ultimate, current_paid): returns a value >= 0 when
   ultimate >= current_paid >= 0. Returns -1.0 when ultimate < current_paid
   or any input is negative.

5. total_ibnr(reserves, n): returns a value >= 0 when all reserves[i] >= 0
   and n >= 1. Returns -1.0 if any element is negative or n < 1.

Context: These are Mack Chain Ladder functions for actuarial IBNR reserve
calculation. Negative reserves are impossible in practice and would indicate
a regulatory compliance failure.
"""

    console.print(Panel.fit(
        "[bold cyan]Trial 01 — Mack Chain Ladder IBNR Verification[/bold cyan]\n"
        "[dim]Source:[/dim] Mack (1993), ASTIN Bulletin 23(2)\n"
        "[dim]Code:[/dim] trials/t01_mack_chain_ladder/chain_ladder.c",
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

    # ── Print result ────────────────────────────────────────────────────────
    console.print(Rule())
    status_color = "green" if "SUCCESS" in status.upper() else "red"
    console.print(f"[bold {status_color}]Status:[/{status_color}] {status}")
    if summary:
        console.print(f"\n[bold]Summary:[/bold]\n{summary}")

    # ── Append to RESULTS.md ────────────────────────────────────────────────
    _append_result("t01_mack_chain_ladder", status, summary)
    console.print(f"\n[dim]Result saved to trials/RESULTS.md[/dim]")
    console.print(
        "\n→ Next trial: [cyan]python trials/t02_buhlmann_credibility/run_trial.py[/cyan]"
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
    parser.add_argument("--show-triangle", action="store_true", help="Print worked example first")
    args = parser.parse_args()

    if args.show_triangle:
        show_worked_example()

    asyncio.run(run(dry_run=args.dry_run))
