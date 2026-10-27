"""
Trial 02: Bühlmann Credibility — Insurance Pricing Verification.
─────────────────────────────────────────────────────────────────
HOW TO RUN:
  python trials/t02_buhlmann_credibility/run_trial.py
  python trials/t02_buhlmann_credibility/run_trial.py --dry-run
  python trials/t02_buhlmann_credibility/run_trial.py --show-example
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

load_dotenv()
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

console = Console()
TRIAL_DIR = Path(__file__).parent

VERIFICATION_PROMPT = """\
Verify the following properties for functions in credibility.c:

1. credibility_z(n, k): returns a value in [0.0, 1.0] for all n >= 0 and k > 0.
   Returns -1.0 for invalid inputs (k <= 0 or n < 0).

2. credibility_z is monotone non-decreasing in n:
   For any n1 >= n2 >= 0 and fixed k > 0,
   credibility_z(n1, k) >= credibility_z(n2, k).

3. credibility_premium(z, x_bar, mu_prior): returns a value in
   [min(x_bar, mu_prior), max(x_bar, mu_prior)] for z in [0,1],
   x_bar >= 0, mu_prior >= 0.
   (It is a convex combination, so it never exceeds either input.)

4. credibility_premium returns a value >= 0 when z in [0,1],
   x_bar >= 0, mu_prior >= 0.

5. credibility_param_k(process_var, structural_var): returns a value >= 0
   when process_var >= 0 and structural_var > 0. Returns -1.0 otherwise.

6. full_credibility_n(z_alpha2, r, cv): returns a value >= 0
   for z_alpha2 > 0, r in (0,1), cv >= 0. Returns -1.0 for invalid inputs.

Context: These are Bühlmann credibility functions for personalizing insurance
premiums. Z must be in [0,1] for the blended premium to make actuarial sense.
"""


def show_example() -> None:
    console.print("""
[bold]Worked Example: Bühlmann Credibility for a Mining Client[/bold]

Client:  Cerrejón Mining Co. — coal mining in Cesar department (Colombia)
Product: General liability + workers comp

Data:
  - 3 years of claims history: average loss ratio X̄ = 0.65 (65 cents claims per $1 premium)
  - Industry prior: μ = 0.58 (58 cents average for all mining companies)
  - Process variance estimate: σ²_e = 0.04
  - Structural variance estimate: σ²_u = 0.02

Credibility parameter:
  k = σ²_e / σ²_u = 0.04 / 0.02 = 2.0

Credibility factor:
  Z = n / (n + k) = 3 / (3 + 2.0) = 3/5 = 0.60

Credibility premium:
  P = 0.60 × 0.65 + 0.40 × 0.58 = 0.39 + 0.232 = 0.622

Meaning: The broker charges a 62.2% loss ratio — blending the client's
high own experience (65%) with the industry average (58%).

KEY: P = 0.622 is between 0.58 and 0.65. This is Property 3 — the convex
combination property. Aristotle will prove this ALWAYS holds, not just here.
""")


async def run(dry_run: bool = False) -> None:
    console.print(Panel.fit(
        "[bold cyan]Trial 02 — Bühlmann Credibility Verification[/bold cyan]\n"
        "[dim]Source:[/dim] Bühlmann (1967), ASTIN Bulletin 4(3)\n"
        "[dim]Code:[/dim] trials/t02_buhlmann_credibility/credibility.c",
        title="harmonic-risk-lab",
    ))

    console.print(Rule("[bold]Verification Prompt[/bold]"))
    console.print(Panel(VERIFICATION_PROMPT, border_style="dim"))

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
        VERIFICATION_PROMPT,
        str(TRIAL_DIR),
        agent_questions_setting=AgentQuestionsSetting.DISABLED,
    )
    console.print(f"[green]Project created:[/green] {project.status.name}")
    console.print("[yellow]Waiting...[/yellow]")

    tasks, _ = await project.get_tasks(limit=1)
    await tasks[0].wait_for_completion(interactive=False)

    status  = tasks[0].status.name
    summary = tasks[0].output_summary or ""

    console.print(Rule())
    status_color = "green" if "SUCCESS" in status.upper() else "red"
    console.print(f"[bold {status_color}]Status:[/{status_color}] {status}")
    if summary:
        console.print(f"\n[bold]Summary:[/bold]\n{summary}")

    _append_result("t02_buhlmann_credibility", status, summary)
    console.print(f"\n[dim]Result saved to trials/RESULTS.md[/dim]")


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
    parser.add_argument("--dry-run",       action="store_true")
    parser.add_argument("--show-example",  action="store_true")
    args = parser.parse_args()

    if args.show_example:
        show_example()

    asyncio.run(run(dry_run=args.dry_run))
