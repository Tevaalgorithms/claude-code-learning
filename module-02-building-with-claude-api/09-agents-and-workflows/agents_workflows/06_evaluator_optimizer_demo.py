"""
Demo 06 — Evaluator–Optimizer
==============================
Pattern: One Claude generates output. Another Claude evaluates it.
         Loop until quality threshold is met.

Use case: Code quality improvement loop
  Generator → writes Python function
  Evaluator → scores it (1-10) and gives specific feedback
  Loop      → repeats until score ≥ 8 or max iterations hit

Run:
    python module-03-claude-api/agents_workflows/06_evaluator_optimizer_demo.py
"""

import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL  = "claude-sonnet-4-0"


# ── Generator ────────────────────────────────────────────────────────────────

GENERATOR_SYSTEM = """You are a Python developer. Write clean, production-quality code.
When given feedback, revise your code to specifically address each point of criticism.
Always return ONLY the Python code — no explanation, no markdown fences."""


def generate_code(task: str, feedback: str = None) -> str:
    """Generate (or revise) code based on task and optional feedback."""
    if feedback:
        user_prompt = (
            f"Original task: {task}\n\n"
            f"Your previous attempt was rejected. Feedback:\n{feedback}\n\n"
            "Rewrite the code addressing ALL feedback points."
        )
    else:
        user_prompt = f"Write a Python function for: {task}"

    response = client.messages.create(
        model      = MODEL,
        max_tokens = 1024,
        system     = GENERATOR_SYSTEM,
        messages   = [{"role": "user", "content": user_prompt}]
    )
    code = response.content[0].text.strip()
    # Remove markdown fences if Claude added them anyway
    if code.startswith("```"):
        lines = code.split("\n")
        code = "\n".join(lines[1:-1])
    return code


# ── Evaluator ────────────────────────────────────────────────────────────────

EVALUATOR_SYSTEM = """You are a strict code reviewer. Evaluate Python code rigorously.
Score from 1-10 based on:
- Correctness: Does it solve the task?
- Edge cases: Does it handle None, empty input, invalid types?
- Error handling: Does it raise/return meaningful errors?
- Readability: Clear variable names, appropriate comments?
- Efficiency: No unnecessary operations?

Respond with ONLY valid JSON:
{
  "score": <int 1-10>,
  "passed": <bool, true if score >= 8>,
  "issues": ["issue 1", "issue 2"],
  "strengths": ["strength 1"],
  "feedback": "<specific, actionable instructions for improvement>"
}"""


def evaluate_code(task: str, code: str) -> dict:
    """Evaluate code quality and return structured feedback."""
    response = client.messages.create(
        model      = MODEL,
        max_tokens = 512,
        system     = EVALUATOR_SYSTEM,
        messages   = [{
            "role": "user",
            "content": f"Task: {task}\n\nCode to evaluate:\n```python\n{code}\n```"
        }]
    )

    try:
        return json.loads(response.content[0].text.strip())
    except json.JSONDecodeError:
        return {
            "score": 5,
            "passed": False,
            "issues": ["Could not parse evaluation"],
            "strengths": [],
            "feedback": response.content[0].text.strip()
        }


# ── Evaluator–Optimizer loop ─────────────────────────────────────────────────

def run_improvement_loop(task: str, max_iterations: int = 4) -> dict:
    """
    Generates code, evaluates it, and loops until it passes (score >= 8)
    or max iterations is reached.
    """
    print(f"\n{'='*60}")
    print(f"EVALUATOR–OPTIMIZER DEMO")
    print(f"Task: {task}")
    print("="*60)

    feedback     = None
    final_code   = None
    final_eval   = None
    history      = []

    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Iteration {iteration}/{max_iterations} ---")

        # Generate (or revise)
        print("Generator: writing code...")
        code = generate_code(task, feedback)
        print(f"Code preview:\n{code[:300]}{'...' if len(code) > 300 else ''}")

        # Evaluate
        print("\nEvaluator: reviewing code...")
        evaluation = evaluate_code(task, code)

        score    = evaluation.get("score", 0)
        passed   = evaluation.get("passed", False)
        issues   = evaluation.get("issues", [])
        feedback = evaluation.get("feedback", "")

        print(f"Score: {score}/10 | Passed: {passed}")
        if issues:
            print(f"Issues: {', '.join(issues)}")

        history.append({
            "iteration": iteration,
            "score":     score,
            "passed":    passed,
            "issues":    issues
        })

        final_code = code
        final_eval = evaluation

        if passed:
            print(f"\nPASSED on iteration {iteration}!")
            break

        print(f"Feedback for next iteration: {feedback[:150]}...")

    return {
        "task":       task,
        "final_code": final_code,
        "evaluation": final_eval,
        "iterations": len(history),
        "history":    history,
        "passed":     final_eval.get("passed", False) if final_eval else False
    }


# ── Run examples ─────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # Example 1: Simple function with common edge case traps
    result1 = run_improvement_loop(
        task="Write a function that calculates the average of a list of numbers"
    )

    print("\n" + "="*60)
    print("FINAL CODE:")
    print("="*60)
    print(result1["final_code"])

    print("\n" + "="*60)
    print("ITERATION HISTORY:")
    for h in result1["history"]:
        status = "✓ PASS" if h["passed"] else "✗ FAIL"
        print(f"  Iteration {h['iteration']}: {h['score']}/10 {status}")

    print("\n" + "="*60)

    # Example 2: More complex with error handling requirements
    result2 = run_improvement_loop(
        task=(
            "Write a function that safely reads a JSON file "
            "and returns a default value if the file doesn't exist or is malformed"
        )
    )

    print("\nFINAL CODE:")
    print(result2["final_code"])

    print("\n\n--- KEY TAKEAWAYS ---")
    print("The evaluator gives SPECIFIC, ACTIONABLE feedback — not just 'bad'.")
    print("Each iteration the generator sees the previous feedback.")
    print("Set a clear pass threshold (score >= 8) and max iterations.")
    print("Use this pattern for: code review, writing quality, data validation.")
