"""
gemini_client.py — Gemini helpers for the Harmonic pipeline.

This module uses Gemini to bridge the gap between plain English finance
descriptions and the two artifacts Aristotle needs:
  1. A C implementation of the model.
  2. A natural-language property description for the verification prompt.

Why Gemini here?
  Aristotle understands what to VERIFY but needs CODE to verify.
  Gemini understands English and can write C.
  Together: describe a risk concept → get formally verified code.
"""

import os
from google import genai
from google.genai import types


def _get_client() -> genai.Client:
    """
    Supports two auth methods:
      1. API key:  set GEMINI_API_KEY in .env  (personal/aistudio.google.com)
      2. ADC:      run the ADC setup script, then set GOOGLE_CLOUD_PROJECT in .env
                   bash <(curl -sSL https://storage.googleapis.com/cloud-samples-data/adc/setup_adc.sh)
                   Use this when your org blocks API keys (enterprise Vertex AI).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)

    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project:
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        return genai.Client(vertexai=True, project=project, location=location)

    raise EnvironmentError(
        "No Gemini credentials found. Choose one of:\n"
        "  Option A — API key (aistudio.google.com):\n"
        "    Add GEMINI_API_KEY=your_key to .env\n\n"
        "  Option B — ADC (enterprise / org account):\n"
        "    Run: bash <(curl -sSL https://storage.googleapis.com/cloud-samples-data/adc/setup_adc.sh)\n"
        "    Then add GOOGLE_CLOUD_PROJECT=your-project-id to .env"
    )


def generate_c_model(concept: str) -> str:
    """
    Given a plain-English description of a financial/risk calculation,
    return a self-contained C implementation.

    Example:
        generate_c_model("A function that computes the insurance combined ratio
                          (claims + expenses divided by earned premium)")
    """
    client = _get_client()

    prompt = f"""You are an expert in actuarial science, quantitative finance, and C programming.

A user wants to formally verify this financial/risk model:

"{concept}"

Write a self-contained C implementation (.c file only, no headers needed beyond math.h).
Rules:
- Use only standard C (C11), include <math.h> if needed.
- Every function must have clear parameter preconditions in a comment.
- Return -1.0 for invalid inputs (negative values where not allowed, etc.).
- Keep it simple — no structs, no dynamic allocation.
- Add a comment block at the top explaining what the code models.

Output ONLY the C code, nothing else."""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=2048,
        ),
    )
    code = response.text.strip()
    # Strip markdown fences if Gemini wraps the output
    if code.startswith("```"):
        lines = code.split("\n")
        code = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
    return code


def generate_verification_prompt(concept: str, c_code: str) -> str:
    """
    Given the original concept and its C implementation, generate a
    precise Aristotle verification prompt that describes what properties
    Aristotle should formally prove.

    Returns a string suitable for use as the `prompt` argument to
    Project.create_from_directory().
    """
    client = _get_client()

    prompt = f"""You are an expert in formal verification and financial risk management.

Here is a financial/risk model concept:
"{concept}"

Here is its C implementation:
```c
{c_code}
```

Write a clear, concise verification prompt for Aristotle (a formal verification AI).
The prompt should list the specific mathematical properties to prove, e.g.:
- "Verify that function X always returns a non-negative value for valid inputs"
- "Prove that Y is always greater than Z when parameter W > 0"

Focus on the invariants that matter for financial regulation and safety.
Keep it under 150 words. Be specific about function names and conditions.
Output ONLY the verification prompt, no preamble."""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=512,
        ),
    )
    return response.text.strip()


def explain_result(status: str, summary: str, concept: str) -> str:
    """
    Translates Aristotle's raw output into plain English for a non-technical
    stakeholder (e.g., an underwriter, compliance officer, or operations manager).
    """
    client = _get_client()

    prompt = f"""You are explaining a formal verification result to a finance/insurance professional
who is not a software engineer.

The model being verified: "{concept}"
Verification status: {status}
Aristotle's technical summary: {summary}

Explain in 3-4 sentences what this means for the business:
- What was verified (or not)?
- What does this mean for reliability and risk?
- Is there anything the team should investigate?

Use plain language. No jargon. Be direct."""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=256,
        ),
    )
    return response.text.strip()
