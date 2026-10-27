"""
Trial 03: Aggregate Loss Model — Formula Verification.
────────────────────────────────────────────────────────
This trial is different from t01/t02 in an important way:

  t01, t02 — verify FINANCIAL INVARIANTS (IBNR ≥ 0, credibility ∈ [0,1])
  t03       — verifies a MATHEMATICAL IDENTITY (the compound Poisson formula)

The difference:
  Financial invariants say the output is in a valid range.
  Mathematical identities say two expressions are ALWAYS EQUAL.
  Aristotle can prove both, but the identity proof is deeper.

HOW TO RUN:
  python trials/t03_aggregate_loss/run_trial.py
  python trials/t03_aggregate_loss/run_trial.py --dry-run
  python trials/t03_aggregate_loss/run_trial.py --show-simulation
    (runs the Python Monte Carlo first so you can see what we're verifying)
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
Verify the following properties for the functions in aggregate_model.c.
This implements the compound Poisson aggregate loss model: S = X₁+...+Xₙ
where N ~ Poisson(lambda).

1. aggregate_mean(lambda, mean_x): returns a value >= 0 for all lambda >= 0
   and mean_x >= 0. Returns -1.0 for invalid inputs.

2. aggregate_variance(lambda, var_x, mean_x): returns a value >= 0 for all
   lambda >= 0, var_x >= 0, mean_x >= 0. Returns -1.0 for invalid inputs.

3. Algebraic identity: aggregate_variance(lambda, var_x, mean_x) equals
   lambda * (var_x + mean_x * mean_x) for all valid non-negative inputs.
   This is the compound Poisson variance identity: Var(S) = λ·E[X²].

4. aggregate_std_dev(lambda, var_x, mean_x): returns a value >= 0 for all
   valid inputs. Returns -1.0 when aggregate_variance returns -1.0.

5. aggregate_cv(lambda, var_x, mean_x): returns a value >= 0 when lambda > 0
   and mean_x > 0 and var_x >= 0. Returns -1.0 for invalid inputs.

6. aggregate_var_normal_approx(lambda, var_x, mean_x, z_alpha):
   returns a value >= aggregate_mean(lambda, mean_x) when z_alpha >= 0.
   (VaR >= E[S]: the risk measure is above the mean, always.)

7. aggregate_cvar_normal_approx: returns a value >= aggregate_var_normal_approx
   for the same lambda, var_x, mean_x, z_alpha when phi_z_alpha >= 0 and
   one_minus_alpha > 0. (CVaR >= VaR: coherent risk measure property.)
"""


def show_simulation() -> None:
    """Run the Python Monte Carlo first to show what we're verifying."""
    console.print(Rule("[bold]Python Monte Carlo First (numerics/aggregate_simulation.py)[/bold]"))
    console.print("""
What this does:
  1. Draws N ~ Poisson(8) for each of 100,000 scenarios → how many claims?
  2. For each scenario with N>0 claims, draws N severities from Lognormal
  3. Sums them: S = X₁ + X₂ + ... + Xₙ
  4. The distribution of S across 100k scenarios IS the aggregate loss distribution
""")
    try:
        from numerics.aggregate_simulation import simulate_lognormal, print_summary
        result = simulate_lognormal(
            lambda_freq=8.0,
            mu_sev=10.0,
            sigma_sev=1.2,
            n_sim=100_000,
        )
        print_summary(result, label="Mining Liability (λ=8, Lognormal)")
        console.print(
            "[dim]Notice: 'Simulated E\\[S]' ≈ 'Theoretical E\\[S] = λ·E\\[X]'[/dim]\n"
            "[dim]That's the formula we're now asking Aristotle to PROVE is always correct.[/dim]\n"
        )
    except ImportError as e:
        console.print(f"[yellow]Install scipy to run the simulation: {e}[/yellow]")


async def run(dry_run: bool = False) -> None:
    console.print(Panel.fit(
        "[bold cyan]Trial 03 — Compound Poisson Aggregate Loss[/bold cyan]\n"
        "[dim]Source:[/dim] Curriculum Module 4, Loss Data Analytics Ch. 3\n"
        "[dim]Code:[/dim] trials/t03_aggregate_loss/aggregate_model.c\n\n"
        "Verifying 7 properties including the compound Poisson variance identity.",
        title="harmonic-risk-lab",
    ))

    console.print(Rule("[bold]Key insight: why verify a formula?[/bold]"))
    console.print(
        "\nThe Python simulator shows: 'simulated mean ≈ λ·E[X]' — but that's\n"
        "just an empirical check. What if someone edits the C formula and\n"
        "accidentally writes `lambda + mean_x` instead of `lambda * mean_x`?\n\n"
        "Aristotle will catch that. It checks the algebraic identity holds\n"
        "for ALL possible values of lambda, var_x, and mean_x simultaneously.\n"
    )

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

    _append_result("t03_aggregate_loss", status, summary)
    console.print(f"\n[dim]Result saved to trials/RESULTS.md[/dim]")
    console.print(
        "\n→ Next: run [cyan]python numerics/reinsurance_optimizer.py[/cyan]\n"
        "  to use these scenarios to find the optimal reinsurance structure."
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
    parser.add_argument("--dry-run",         action="store_true")
    parser.add_argument("--show-simulation", action="store_true")
    args = parser.parse_args()

    if args.show_simulation:
        show_simulation()

    asyncio.run(run(dry_run=args.dry_run))
