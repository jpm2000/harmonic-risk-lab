"""
spec_runner.py — Bridge between Spec Kit specs and Aristotle verification.

This module reads .spec.yaml files from .speckit/specifications/ and
automatically generates the verification prompt for Aristotle.

Why this matters:
  Without this, the verification prompt is an ad-hoc string in each example.
  With this, the SPEC is the single source of truth — the prompt, the
  documentation, and the implementation contract all come from one file.

  Workflow:
    1. Write .speckit/specifications/my_model.spec.yaml
    2. Implement models/my_model.c
    3. Run: spec_runner.run_verification("var_model") to verify automatically
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

import yaml

SPEC_DIR  = Path(__file__).parent.parent / ".speckit" / "specifications"
MODELS_DIR = Path(__file__).parent.parent / "models"


def load_spec(spec_name: str) -> dict:
    """
    Load a .spec.yaml file by its base name (without extension).

    Example:
        spec = load_spec("var_model")
    """
    spec_path = SPEC_DIR / f"{spec_name}.spec.yaml"
    if not spec_path.exists():
        raise FileNotFoundError(
            f"Spec not found: {spec_path}\n"
            f"Available specs: {list_specs()}"
        )
    with open(spec_path) as f:
        return yaml.safe_load(f)


def list_specs() -> list[str]:
    """Return all available spec names."""
    return [p.stem.replace(".spec", "") for p in SPEC_DIR.glob("*.spec.yaml")]


def build_aristotle_prompt(spec: dict, function_filter: Optional[list[str]] = None) -> str:
    """
    Extract all property.aristotle_prompt strings from a spec and combine
    them into a single verification prompt for Aristotle.

    Args:
        spec: Loaded spec dictionary.
        function_filter: If set, only include properties from these functions.

    Returns:
        A multi-line string ready to pass to Project.create_from_directory().
    """
    lines = [
        f"Verify the following properties for {spec['name']}.",
        f"Source: {spec.get('source', {}).get('paper', 'see spec file')}",
        "",
    ]

    prop_count = 0
    for func_name, func_data in spec.get("functions", {}).items():
        if function_filter and func_name not in function_filter:
            continue
        properties = func_data.get("properties", [])
        if not properties:
            continue
        lines.append(f"[{func_name}]")
        for prop in properties:
            prop_count += 1
            # Normalize the prompt — remove leading whitespace from multi-line YAML
            prompt_text = " ".join(prop["aristotle_prompt"].split())
            lines.append(f"  {prop_count}. {prompt_text}")
        lines.append("")

    if prop_count == 0:
        raise ValueError(f"No properties found in spec '{spec['name']}'")

    return "\n".join(lines).strip()


async def run_verification(
    spec_name: str,
    models_dir: Optional[Path] = None,
    function_filter: Optional[list[str]] = None,
    interactive: bool = False,
) -> dict:
    """
    Full pipeline: load spec → build prompt → submit to Aristotle → return result.

    Args:
        spec_name: Base name of the spec file (without extension).
        models_dir: Directory containing C source files. Defaults to models/.
        function_filter: Only verify these functions (None = all).
        interactive: If True, allow Aristotle to ask questions during verification.

    Returns:
        Dict with keys: status, summary, prompt_used, spec_name.

    Example:
        result = await run_verification("var_model")
        print(result["status"])   # e.g. "SUCCESS"
        print(result["summary"])
    """
    import aristotlelib
    api_key = os.getenv("ARISTOTLE_API_KEY")
    if not api_key:
        raise EnvironmentError("ARISTOTLE_API_KEY not found in environment.")
    aristotlelib.set_api_key(api_key)

    from aristotlelib import AgentQuestionsSetting, Project

    spec = load_spec(spec_name)
    prompt = build_aristotle_prompt(spec, function_filter=function_filter)
    target_dir = models_dir or MODELS_DIR

    project = await Project.create_from_directory(
        prompt,
        str(target_dir),
        agent_questions_setting=(
            AgentQuestionsSetting.INTERACTIVE
            if interactive
            else AgentQuestionsSetting.DISABLED
        ),
    )

    tasks, _ = await project.get_tasks(limit=1)
    await tasks[0].wait_for_completion(interactive=interactive)

    return {
        "status":       tasks[0].status.name,
        "summary":      tasks[0].output_summary or "",
        "prompt_used":  prompt,
        "spec_name":    spec_name,
    }


def print_spec_summary(spec_name: str) -> None:
    """Print a human-readable summary of a spec to the terminal."""
    spec = load_spec(spec_name)
    print(f"\n{'='*60}")
    print(f"SPEC: {spec['name']}  (v{spec.get('version', '?')})")
    print(f"Source: {spec.get('source', {}).get('paper', 'N/A')}")
    print(f"{'='*60}")
    for func_name, func_data in spec.get("functions", {}).items():
        desc = func_data.get("description", "").replace("\n", " ").strip()
        print(f"\n  {func_name}:")
        print(f"    {desc[:80]}...")
        for prop in func_data.get("properties", []):
            print(f"    ✓ [{prop['name']}]")
    print()


if __name__ == "__main__":
    # Quick demo: show available specs and their prompts
    print("Available specs:", list_specs())
    for name in list_specs():
        print_spec_summary(name)
        spec = load_spec(name)
        print("Aristotle prompt preview:")
        print(build_aristotle_prompt(spec))
        print()
