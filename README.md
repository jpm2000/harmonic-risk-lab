# harmonic-risk-lab

Learning [Harmonic's Aristotle API](https://aristotle.harmonic.fun) for finance, risk, and insurance applications.

**Goal:** Understand how formal verification can make risk models and insurance pricing functions *mathematically provably correct* — not just "tested", but proven for all possible inputs.

**Use case:** bluberri's risk management platform for insurance brokers and critical infrastructure (mining, defense).

---

## Aristotle vs OpenAI's Math Model — Are They the Same?

**No. They solve different problems and are complementary.**

| | OpenAI math model (o3, preprints) | Harmonic Aristotle |
|---|---|---|
| **What it does** | Discovers/solves hard open math problems | Certifies code is correct for ALL inputs |
| **Input** | "Prove Hadwiger's conjecture for k=6" | C code + "this function is always ≥ 0" |
| **Output** | New mathematical proof or counterexample | Machine-verifiable proof or exact failing input |
| **Strength** | Creative reasoning, research-level insight | Exhaustive certainty over all possible inputs |
| **For bluberri** | Derive new risk/insurance formulas | Prove your C implementation of those formulas is correct |

OpenAI's [preprints](https://github.com/openai/math/tree/main/preprints) (180+ papers solving open conjectures in algebra, topology, combinatorics) show an AI *discovering* new mathematics. That's a research tool.

Aristotle is an *engineering* tool — once you have a formula (from any source: papers, OpenAI, regulators), it proves your code implements it correctly for every possible input.

**The research pipeline:**
```
Math paper
    ↓ Gemini/OpenAI (translate formulas to C)
C implementation
    ↓ Aristotle (formally verify)
Certified model — safe to deploy
```

---

## What is Aristotle?

Aristotle is **not** a math chatbot. It is a **formal verification AI**.

| Regular testing | Formal verification |
|---|---|
| Runs the function with 100 sample inputs | Proves the function works for ALL inputs simultaneously |
| Can miss edge cases | Covers all possible inputs — including ones you never thought of |
| Output: "passed N tests" | Output: a machine-checkable mathematical proof |
| Can't find the exact bug input | Produces a counterexample showing exactly where it breaks |

**For risk management:** Instead of testing that your VaR model *seems* non-negative, Aristotle *proves* it is — or shows you the exact input that breaks it.

---

## Setup

**Requirements:** Python 3.10+, an Aristotle API key, a Gemini API key (for Example 04).

```bash
# 1. Clone and enter the repo
cd harmonic-risk-lab

# 2. Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your API keys
cp .env.example .env
# Edit .env and fill in:
#   ARISTOTLE_API_KEY — get from https://aristotle.harmonic.fun → Dashboard → API Keys
#   GEMINI_API_KEY    — get from https://aistudio.google.com/apikey
```

---

## Examples (run in order)

### Example 01 — Hello Aristotle
```bash
python examples/01_hello_aristotle.py
```
Proves that `x² + 1 > 0` for all integers. Your first formal verification. Confirms the API works.

### Example 02 — Verify VaR Model
```bash
python examples/02_verify_var_model.py
```
Formally verifies `models/risk_model.c`:
- `portfolio_var()` always returns ≥ 0
- `portfolio_es()` always returns ≥ `portfolio_var()` (coherent risk measure)
- `calculate_rwa()` stays within bounds

### Example 03 — Verify Insurance Models
```bash
python examples/03_verify_insurance.py
```
Formally verifies `models/insurance_model.c`:
- All three premium principles return ≥ expected loss
- XL reinsurance layer pricer stays in `[0, limit]`

### Example 04 — Gemini → Aristotle Pipeline
```bash
python examples/04_gemini_pipeline.py
```
Full pipeline: you describe any financial concept in plain English → Gemini writes C code → Aristotle verifies it → Gemini explains the result to stakeholders. Edit `FINANCIAL_CONCEPT` in the file to explore different models.

---

## Spec-Driven Workflow (Spec Kit)

This repo uses [GitHub Spec Kit](https://starlog.is/articles/ai-dev-tools/github-spec-kit) conventions.
The spec is the source of truth — code and verification prompts are derived from it.

```
.speckit/constitution.yaml          ← project-wide principles (read this first)
.speckit/specifications/
├── var_model.spec.yaml             ← defines properties for risk_model.c
└── insurance_model.spec.yaml       ← defines properties for insurance_model.c
```

**To generate an Aristotle prompt directly from a spec:**
```python
from utils.spec_runner import build_aristotle_prompt, load_spec

spec   = load_spec("var_model")
prompt = build_aristotle_prompt(spec)
print(prompt)   # ready to pass to Project.create_from_directory()
```

**To run a full spec-driven verification:**
```python
from utils.spec_runner import run_verification
result = await run_verification("var_model")
print(result["status"])  # SUCCESS / COUNTEREXAMPLE_FOUND
```

---

## Trials (Experiments from Papers)

Trials are self-contained experiments translating math papers into verified C code.

```bash
# See what the trial will verify (no API call)
python trials/t01_mack_chain_ladder/run_trial.py --dry-run

# Run the full verification
python trials/t01_mack_chain_ladder/run_trial.py

# See a worked example of the math first
python trials/t02_buhlmann_credibility/run_trial.py --show-example
```

Results are saved to `trials/RESULTS.md`. See `trials/README.md` for the full list.

---

## Repository Structure

```
harmonic-risk-lab/
├── .speckit/
│   ├── constitution.yaml              # Project principles (machine-readable contract)
│   └── specifications/
│       ├── var_model.spec.yaml        # Formal spec for risk_model.c
│       └── insurance_model.spec.yaml  # Formal spec for insurance_model.c
│
├── examples/                          # Run these in order (basics)
│   ├── 01_hello_aristotle.py          # First verification, confirms setup
│   ├── 02_verify_var_model.py         # Market risk (VaR, ES, RWA)
│   ├── 03_verify_insurance.py         # Actuarial pricing invariants
│   └── 04_gemini_pipeline.py          # Full NL → C → proof → NL pipeline
│
├── models/                            # Shared C models (verified by examples/)
│   ├── risk_model.c                   # VaR, Expected Shortfall, RWA
│   └── insurance_model.c              # Premium principles, XL reinsurance
│
├── trials/                            # Paper-driven experiments
│   ├── README.md                      # How to run trials
│   ├── RESULTS.md                     # Append-only result log
│   ├── t01_mack_chain_ladder/         # Mack (1993) IBNR reserving
│   └── t02_buhlmann_credibility/      # Bühlmann (1967) pricing credibility
│
├── papers/
│   └── README.md                      # Curated reading list with trial roadmap
│
├── utils/
│   ├── gemini_client.py               # Gemini: generate code + explain results
│   └── spec_runner.py                 # Read spec.yaml → Aristotle prompt
│
├── lean_proofs/                       # Lean 4 proofs (bonus, aristotlelib < 3)
│   └── BasicRisk.lean
│
├── .env.example
├── requirements.txt
└── pyproject.toml
```

---

## How the API Works

```python
import aristotlelib
aristotlelib.set_api_key("your-key")

from aristotlelib import AgentQuestionsSetting, Project

# 1. Create a project from a directory of C code
project = await Project.create_from_directory(
    "Verify that calculate_var always returns a non-negative value",
    "./models",                                     # directory with your .c files
    agent_questions_setting=AgentQuestionsSetting.DISABLED,
)

# 2. Wait for the result
tasks, _ = await project.get_tasks(limit=1)
await tasks[0].wait_for_completion(interactive=False)

# 3. Read the result
print(tasks[0].status.name)       # e.g. "SUCCESS" or "COUNTEREXAMPLE_FOUND"
print(tasks[0].output_summary)    # what Aristotle found
```

---

## Application to bluberri

| Risk domain | What to verify | Invariant |
|---|---|---|
| Insurance pricing | Premium calculation | `premium ≥ expected_loss` always |
| Market risk | VaR model | `var ≥ 0` always |
| Credit risk | LGD / PD calculation | `0 ≤ LGD ≤ 1`, `0 ≤ PD ≤ 1` |
| Mining operations | Equipment risk score | Monotone in exposure, bounded |
| Reinsurance | XL layer pricing | `0 ≤ layer_EL ≤ limit` |
| Regulatory capital | RWA calculation | `rwa ≥ 0`, within regulatory bounds |

---

## CLI Reference (aristotlelib)

```bash
aristotle login                          # authenticate via browser
aristotle submit "property" --project-dir ./models --wait
aristotle list                           # list recent projects
aristotle show <project>                 # view project status
aristotle properties <project>           # per-property results
aristotle download <project>             # save result archive
aristotle cancel <project>               # cancel in-progress run
```

---

## Sources

- [Harmonic Aristotle API overview (eco.com)](https://eco.com/support/en/articles/14114345-what-is-the-harmonic-aristotle-api-formal-verification-ai-for-developers)
- [aristotlelib on PyPI](https://pypi.org/project/aristotlelib/)
- [Harmonic raises $120M at $1.45B valuation](https://entrepreneurloop.com/harmonic-ai-startup-valuation-mathematical-reasoning/)
- [Formally verified mathematical finance in Lean 4 (arxiv)](https://arxiv.org/pdf/2606.01356)
- [Lean-agent-protocol: verified guardrails for trading agents](https://github.com/arkanemystic/lean-agent-protocol)
