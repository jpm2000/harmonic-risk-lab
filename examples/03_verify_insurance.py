"""
Example 03: Verify insurance premium models.
──────────────────────────────────────────────
WHAT THIS TEACHES:
  An insurance broker selling policies to mining or defense companies must
  guarantee that every premium charged is AT LEAST the expected loss.
  If not, the insurer is technically insolvent from day one.

  This is not just good practice — it's required by insurance regulators.

  We formally verify three actuarial pricing principles from insurance_model.c:
    1. Expected Value Principle: P = (1+θ)·E[L] > E[L] when θ > 0
    2. Standard Deviation Principle: P = E[L] + k·σ ≥ E[L] when k,σ ≥ 0
    3. Variance Principle: P = E[L] + β·Var[L] ≥ E[L] when β,Var ≥ 0

  We also verify the XL reinsurance layer pricer returns values in [0, limit].

HOW TO RUN:
  python examples/03_verify_insurance.py

WHAT TO LOOK AT:
  Open models/insurance_model.c and read the property comments for each function.
  These translate directly into the verification prompt below.
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

MODELS_DIR = Path(__file__).parent.parent / "models"

VERIFICATION_PROMPT = """\
Verify the following actuarial pricing invariants in insurance_model.c:

1. premium_ev(expected_loss, theta):
   - Returns a value strictly greater than expected_loss when theta > 0 and
     expected_loss >= 0. (The insurer always charges more than expected cost.)
   - Returns -1.0 when expected_loss < 0 or theta <= 0.

2. premium_sd(expected_loss, std_loss, k):
   - Returns a value >= expected_loss for all std_loss >= 0 and k > 0.
   - Returns -1.0 for invalid inputs.

3. premium_variance(expected_loss, variance_loss, beta):
   - Returns a value >= expected_loss for variance_loss >= 0 and beta > 0.
   - Returns -1.0 for invalid inputs.

4. layer_expected_loss(retention, limit, alpha_pareto, x_m):
   - Returns a value in [0.0, limit] for all valid inputs
     (retention >= x_m > 0, limit > 0, alpha_pareto > 1.0).
   - Returns -1.0 for invalid inputs.
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
        "[bold cyan]Example 03 — Verify Insurance Premium Models[/bold cyan]\n"
        "Proving that every premium principle satisfies P ≥ E[L].\n\n"
        "[dim]Source file:[/dim] models/insurance_model.c",
        title="harmonic-risk-lab",
    ))

    console.print("\n[dim]Verifying four actuarial pricing functions...[/dim]\n")

    project = await Project.create_from_directory(
        VERIFICATION_PROMPT,
        str(MODELS_DIR),
        agent_questions_setting=AgentQuestionsSetting.DISABLED,
    )

    console.print(f"[green]Project created:[/green] {project.status.name}")
    console.print("[yellow]Waiting for verification...[/yellow]")

    tasks, _ = await project.get_tasks(limit=1)
    await tasks[0].wait_for_completion(interactive=False)

    console.print(Rule())
    status = tasks[0].status.name
    summary = tasks[0].output_summary or "(no summary)"

    status_color = "green" if "SUCCESS" in status.upper() else "red"
    console.print(f"[bold {status_color}]Status:[/{status_color}] {status}")
    console.print(f"\n[bold]Summary:[/bold]\n{summary}")

    # ── Show per-property results if available ─────────────────────────────
    # The properties() method returns each individually-named property's status.
    # This lets you see which specific invariant passed or failed.
    try:
        props = await project.get_properties()
        if props:
            console.print(Rule())
            console.print("[bold]Per-property results:[/bold]")
            for p in props:
                icon = "✓" if "SUCCESS" in p.status.upper() else "✗"
                console.print(f"  [{icon}] {p.name}: {p.status}")
    except AttributeError:
        pass  # get_properties() may not be available in all API versions

    console.print(Rule())
    console.print(
        "\n[bold]Why this matters for bluberri:[/bold]\n"
        "An insurance broker platform that prices policies for mining or defense\n"
        "companies is operating in a highly regulated space. If a single policy\n"
        "is underpriced due to a code bug, the insurer faces:\n"
        "  - Regulatory intervention\n"
        "  - Solvency risk\n"
        "  - Potential litigation\n\n"
        "Formal verification converts the question 'does this code work?' into\n"
        "a mathematical certificate. Regulators and auditors can inspect the proof.\n\n"
        "→ Next: run [cyan]examples/04_gemini_pipeline.py[/cyan] to build NEW models from scratch."
    )


if __name__ == "__main__":
    asyncio.run(main())
