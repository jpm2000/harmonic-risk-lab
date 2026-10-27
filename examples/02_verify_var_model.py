"""
Example 02: Verify a VaR (Value at Risk) model.
─────────────────────────────────────────────────
WHAT THIS TEACHES:
  Value at Risk is the most widely-used market risk measure in banking,
  insurance, and investment. The Basel III framework requires banks to
  calculate it daily.

  The problem: bugs in VaR implementations have caused real financial losses.
  A VaR function that returns a NEGATIVE value would mean "you expect to GAIN
  money in a worst-case scenario" — a dangerous lie.

  Aristotle will PROVE that our implementation always returns >= 0, so no
  input — no matter how extreme — can trigger that bug.

  We also verify that Expected Shortfall (CVaR) is always >= VaR, which is
  a mathematical requirement for it to be a "coherent risk measure."

HOW TO RUN:
  python examples/02_verify_var_model.py

WHAT TO LOOK AT:
  Open models/risk_model.c while this runs. Note the "PROPERTY WE WANT TO PROVE"
  comments — those are exactly what we're passing to Aristotle.
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

load_dotenv()
console = Console()

# Point to the models/ directory — Aristotle will see all .c files in it.
MODELS_DIR = Path(__file__).parent.parent / "models"

# Describe the properties we want to formally verify.
# This is plain English — Aristotle understands financial concepts.
VERIFICATION_PROMPT = """\
Verify the following properties for the functions in risk_model.c:

1. portfolio_var(mu, sigma, alpha, horizon) always returns a value >= 0.0
   for any valid inputs (sigma >= 0, alpha in (0.5, 1.0), horizon >= 1).

2. portfolio_es(mu, sigma, alpha, horizon) always returns a value >=
   portfolio_var(mu, sigma, alpha, horizon) for the same valid inputs.
   (ES must be >= VaR — this is the definition of a coherent risk measure.)

3. calculate_rwa(exposure, risk_weight) returns a value in [0, exposure * 1.5]
   for valid inputs (exposure >= 0, risk_weight in [0.0, 1.5]).
   It returns -1.0 for invalid inputs.
"""


async def main() -> None:
    api_key = os.getenv("ARISTOTLE_API_KEY")
    if not api_key:
        console.print("[red bold]Error:[/red bold] ARISTOTLE_API_KEY not set in .env")
        return

    import aristotlelib
    aristotlelib.set_api_key(api_key)

    from aristotlelib import AgentQuestionsSetting, Project

    console.print(Panel.fit(
        "[bold cyan]Example 02 — Verify VaR Risk Model[/bold cyan]\n"
        "Formally proving that VaR ≥ 0 and ES ≥ VaR for all valid inputs.\n\n"
        "[dim]Source file:[/dim] models/risk_model.c",
        title="harmonic-risk-lab",
    ))

    # ── Key insight: we point at the models/ directory ─────────────────────
    # Aristotle reads ALL files in the directory.
    # This is how you'd verify a real project: just point at your source folder.
    console.print(f"\n[dim]Models directory:[/dim] {MODELS_DIR}")
    console.print("\n[dim]Properties to verify:[/dim]")
    for line in VERIFICATION_PROMPT.strip().split("\n"):
        console.print(f"  {line}")

    console.print("\n[yellow]Submitting to Aristotle...[/yellow]")

    project = await Project.create_from_directory(
        VERIFICATION_PROMPT,
        str(MODELS_DIR),
        agent_questions_setting=AgentQuestionsSetting.DISABLED,
    )

    console.print(f"[green]Project created:[/green] {project.status.name}")
    console.print("[yellow]Waiting for verification (this may take a few minutes)...[/yellow]")

    tasks, _ = await project.get_tasks(limit=1)
    await tasks[0].wait_for_completion(interactive=False)

    console.print(Rule())
    status = tasks[0].status.name
    summary = tasks[0].output_summary or "(no summary)"

    status_color = "green" if "SUCCESS" in status.upper() else "red"
    console.print(f"[bold {status_color}]Status:[/{status_color}] {status}")
    console.print(f"\n[bold]Summary:[/bold]\n{summary}")

    console.print(Rule())
    console.print(
        "\n[bold]Business meaning of this result:[/bold]\n"
        "If Aristotle verified these properties, you now have a machine-checkable\n"
        "proof that your VaR model can NEVER return a negative value or violate\n"
        "the ES >= VaR constraint — for ANY possible portfolio input.\n\n"
        "This is stronger than any test suite. Tests check specific inputs.\n"
        "Formal verification checks ALL inputs simultaneously.\n\n"
        "→ Next: run [cyan]examples/03_verify_insurance.py[/cyan]"
    )


if __name__ == "__main__":
    asyncio.run(main())
