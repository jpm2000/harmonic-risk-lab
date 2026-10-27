"""
Example 04: Full Gemini → Aristotle pipeline.
───────────────────────────────────────────────
WHAT THIS TEACHES:
  The end-to-end pipeline for a non-technical user:

    Plain English description
          ↓ Gemini
    C code + verification prompt
          ↓ Aristotle
    Formal proof / counterexample
          ↓ Gemini
    Plain English explanation for stakeholders

  This is the pattern you'd build into bluberri:
    - An underwriter describes a new pricing rule in plain English
    - The system generates C code implementing that rule
    - Aristotle verifies it's mathematically sound
    - The result is explained to the underwriter in plain English

  No formal math required from the user — Gemini handles the translation.

REQUIRES:
  Both ARISTOTLE_API_KEY and GEMINI_API_KEY in .env

HOW TO RUN:
  python examples/04_gemini_pipeline.py

  You can also modify FINANCIAL_CONCEPT at the top of this file to try
  different risk or insurance scenarios.
"""

import asyncio
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax

load_dotenv()
console = Console()

# ── Change this to explore different financial concepts ───────────────────────
# Some ideas to try:
#   "A function that computes the Sharpe ratio of a portfolio"
#   "A function that calculates the loss given default (LGD) for a loan"
#   "A function that prices a catastrophe bond using a Poisson arrival process"
#   "A function that computes the net present value of a mining lease cash flow"
FINANCIAL_CONCEPT = (
    "A function that computes the combined ratio for an insurance portfolio "
    "(combined ratio = (claims paid + operating expenses) / earned premiums). "
    "The function should return -1.0 for invalid inputs where earned premiums <= 0."
)


async def main() -> None:
    # ── Check both keys ───────────────────────────────────────────────────────
    aristotle_key = os.getenv("ARISTOTLE_API_KEY")
    gemini_key    = os.getenv("GEMINI_API_KEY")

    if not aristotle_key:
        console.print("[red bold]Missing:[/red bold] ARISTOTLE_API_KEY in .env")
        return
    if not gemini_key:
        console.print("[red bold]Missing:[/red bold] GEMINI_API_KEY in .env")
        return

    import aristotlelib
    aristotlelib.set_api_key(aristotle_key)

    from aristotlelib import AgentQuestionsSetting, Project

    # Import our Gemini helpers
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.gemini_client import (
        generate_c_model,
        generate_verification_prompt,
        explain_result,
    )

    console.print(Panel.fit(
        "[bold cyan]Example 04 — Gemini → Aristotle Pipeline[/bold cyan]\n"
        "From plain English → C code → formal proof → plain English explanation.\n\n"
        f"[dim]Concept:[/dim] {FINANCIAL_CONCEPT[:80]}...",
        title="harmonic-risk-lab",
    ))

    # ── Step 1: Gemini generates C code ──────────────────────────────────────
    console.print(Rule("[bold]Step 1 — Gemini generates C implementation[/bold]"))
    console.print(f"[dim]Concept:[/dim] {FINANCIAL_CONCEPT}\n")
    console.print("[yellow]Asking Gemini to write C code...[/yellow]")

    c_code = generate_c_model(FINANCIAL_CONCEPT)

    console.print("[green]C code generated:[/green]")
    console.print(Syntax(c_code, "c", theme="monokai", line_numbers=True))

    # ── Step 2: Gemini generates the verification prompt ─────────────────────
    console.print(Rule("[bold]Step 2 — Gemini generates verification prompt[/bold]"))
    console.print("[yellow]Asking Gemini to identify properties to prove...[/yellow]")

    verification_prompt = generate_verification_prompt(FINANCIAL_CONCEPT, c_code)

    console.print("[green]Verification prompt:[/green]")
    console.print(Panel(verification_prompt, border_style="dim"))

    # ── Step 3: Submit to Aristotle ───────────────────────────────────────────
    console.print(Rule("[bold]Step 3 — Aristotle formally verifies the code[/bold]"))
    console.print("[yellow]Submitting to Aristotle...[/yellow]")

    with tempfile.TemporaryDirectory() as tmpdir:
        c_path = Path(tmpdir) / "generated_model.c"
        c_path.write_text(c_code)

        project = await Project.create_from_directory(
            verification_prompt,
            tmpdir,
            agent_questions_setting=AgentQuestionsSetting.DISABLED,
        )

        console.print(f"[green]Project created:[/green] {project.status.name}")
        console.print("[yellow]Waiting for verification...[/yellow]")

        tasks, _ = await project.get_tasks(limit=1)
        await tasks[0].wait_for_completion(interactive=False)

    status  = tasks[0].status.name
    summary = tasks[0].output_summary or "(no summary from Aristotle)"

    status_color = "green" if "SUCCESS" in status.upper() else "red"
    console.print(f"\n[bold {status_color}]Aristotle status:[/{status_color}] {status}")
    console.print(f"[dim]Technical summary:[/dim] {summary}")

    # ── Step 4: Gemini explains the result in plain English ───────────────────
    console.print(Rule("[bold]Step 4 — Gemini explains the result[/bold]"))
    console.print("[yellow]Asking Gemini to explain the result to a stakeholder...[/yellow]\n")

    explanation = explain_result(status, summary, FINANCIAL_CONCEPT)

    console.print(Panel(
        f"[bold white]{explanation}[/bold white]",
        title="[green]Plain-English Result for Stakeholders[/green]",
        border_style="green",
    ))

    console.print(Rule())
    console.print(
        "\n[bold]What you just built:[/bold]\n"
        "A pipeline where anyone on your team can describe a financial model\n"
        "in plain English and receive a formally verified implementation.\n\n"
        "For bluberri's risk platform:\n"
        "  • Underwriters describe pricing rules → system verifies them\n"
        "  • Actuaries define risk bounds → system proves they hold\n"
        "  • Compliance defines regulatory constraints → system certifies them\n\n"
        "Try changing FINANCIAL_CONCEPT at the top of this file to explore more."
    )


if __name__ == "__main__":
    asyncio.run(main())
