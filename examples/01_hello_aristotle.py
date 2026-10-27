"""
Example 01: Hello Aristotle — your first formal verification.
─────────────────────────────────────────────────────────────
WHAT THIS TEACHES:
  The simplest possible verification: a math function that is obviously correct.
  We prove x² + 1 > 0 for all integers — which is trivially true in math,
  but here Aristotle will *formally* prove it from the C code.

  This is your "Hello World" for formal verification. The same workflow
  (write code → describe property → submit → get proof) is what we'll use
  for VaR models and insurance pricing in the next examples.

PREREQUISITE:
  1. Copy .env.example to .env and fill in ARISTOTLE_API_KEY.
  2. Run: pip install -r requirements.txt  (or: uv pip install -r requirements.txt)
  3. If you don't have a key yet: aristotle login

HOW TO RUN:
  python examples/01_hello_aristotle.py
"""

import asyncio
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

load_dotenv()
console = Console()

# The trivial C function we'll verify.
# x*x is always >= 0, so x*x + 1 is always >= 1 — always positive.
SIMPLE_C_CODE = """\
/*
 * hello.c — A trivially correct function for our first Aristotle test.
 */
int always_positive(int x) {
    return x * x + 1;  /* x^2 + 1 >= 1 for all integers */
}
"""

# Plain English description of what Aristotle should verify.
VERIFICATION_PROMPT = (
    "Verify that always_positive(x) returns a strictly positive integer "
    "(greater than 0) for all possible integer inputs x."
)


async def main() -> None:
    # ── 1. Check the API key ──────────────────────────────────────────────
    api_key = os.getenv("ARISTOTLE_API_KEY")
    if not api_key:
        console.print("[red bold]Error:[/red bold] ARISTOTLE_API_KEY not set.")
        console.print("  → Copy .env.example to .env and add your key.")
        console.print("  → Or run: aristotle login")
        return

    import aristotlelib
    aristotlelib.set_api_key(api_key)

    from aristotlelib import AgentQuestionsSetting, Project

    console.print(Panel.fit(
        "[bold cyan]Example 01 — Hello Aristotle[/bold cyan]\n"
        "Formally proving x² + 1 > 0 for all integers.\n\n"
        f"[dim]Property:[/dim] {VERIFICATION_PROMPT}",
        title="harmonic-risk-lab",
    ))

    # ── 2. Write the C code to a temp directory ───────────────────────────
    # Aristotle works on DIRECTORIES (a project), not single strings.
    # We create a temporary directory with one C file inside.
    with tempfile.TemporaryDirectory() as tmpdir:
        c_path = Path(tmpdir) / "hello.c"
        c_path.write_text(SIMPLE_C_CODE)

        console.print(f"\n[dim]Submitting project from:[/dim] {tmpdir}")
        console.print(f"[dim]Prompt:[/dim] {VERIFICATION_PROMPT}\n")

        # ── 3. Create the verification project ───────────────────────────
        # Project.create_from_directory() sends the code + prompt to Aristotle.
        # AgentQuestionsSetting.DISABLED = don't pause to ask us questions.
        project = await Project.create_from_directory(
            VERIFICATION_PROMPT,
            tmpdir,
            agent_questions_setting=AgentQuestionsSetting.DISABLED,
        )

        console.print(f"[green]Project created:[/green] {project.status.name}")

        # ── 4. Wait for the result ─────────────────────────────────────────
        # Aristotle may take seconds to hours depending on complexity.
        # wait_for_completion(interactive=False) blocks until done.
        console.print("[yellow]Waiting for Aristotle to verify...[/yellow]")
        tasks, _ = await project.get_tasks(limit=1)
        await tasks[0].wait_for_completion(interactive=False)

        # ── 5. Print results ───────────────────────────────────────────────
        console.print(Rule())
        status = tasks[0].status.name
        summary = tasks[0].output_summary or "(no summary)"

        status_color = "green" if "SUCCESS" in status.upper() else "red"
        console.print(f"[bold {status_color}]Status:[/{status_color}] {status}")
        console.print(f"\n[bold]Summary:[/bold]\n{summary}")
        console.print(Rule())
        console.print(
            "\n[bold]What just happened:[/bold]\n"
            "Aristotle read the C code, understood the property you described,\n"
            "and constructed a formal mathematical proof (or found a counterexample).\n\n"
            "→ Next: run [cyan]examples/02_verify_var_model.py[/cyan] to verify a real risk model."
        )


if __name__ == "__main__":
    asyncio.run(main())
