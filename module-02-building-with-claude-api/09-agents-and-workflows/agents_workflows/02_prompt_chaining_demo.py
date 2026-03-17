"""
Demo 02 — Prompt Chaining
==========================
Pattern: Break a complex task into sequential steps.
         Output of each step feeds into the next.

Pipeline: Topic → [Step 1: Key Points] → [Step 2: Outline] → [Step 3: Draft] → Blog Post

Run:
    python module-03-claude-api/agents_workflows/02_prompt_chaining_demo.py
"""

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL  = "claude-sonnet-4-0"


def call_claude(system: str, user: str) -> str:
    """Simple single-turn call — returns the text response."""
    response = client.messages.create(
        model      = MODEL,
        max_tokens = 1024,
        system     = system,
        messages   = [{"role": "user", "content": user}]
    )
    return response.content[0].text.strip()


def gate_check(content: str, minimum_words: int = 20) -> bool:
    """
    Quality gate between steps.
    Returns False if output looks too short or empty.
    In production, use Claude itself to evaluate quality.
    """
    word_count = len(content.split())
    if word_count < minimum_words:
        print(f"  [GATE FAILED] Output too short: {word_count} words (min {minimum_words})")
        return False
    print(f"  [GATE PASSED] {word_count} words")
    return True


# ── The 3-step blog post pipeline ───────────────────────────────────────────

def step1_research(topic: str) -> str:
    """Extract 5 key points about the topic."""
    print("\n[Step 1] Researching key points...")
    result = call_claude(
        system = "You are a research assistant. Extract clear, factual key points.",
        user   = f"List exactly 5 key points about: {topic}\nFormat: numbered list, one sentence each."
    )
    print(result)
    return result


def step2_outline(topic: str, key_points: str) -> str:
    """Turn key points into a structured blog outline."""
    print("\n[Step 2] Creating outline...")
    result = call_claude(
        system = "You are a content strategist. Create clear blog outlines.",
        user   = (
            f"Topic: {topic}\n\n"
            f"Key points:\n{key_points}\n\n"
            "Create a blog post outline with: title, intro, 3 sections (with subheadings), conclusion."
        )
    )
    print(result)
    return result


def step3_draft(topic: str, outline: str) -> str:
    """Write the full blog post from the outline."""
    print("\n[Step 3] Writing full draft...")
    result = call_claude(
        system = (
            "You are a skilled blog writer. Write engaging, clear content. "
            "Use a friendly but informative tone."
        ),
        user   = (
            f"Write a complete blog post based on this outline:\n\n{outline}\n\n"
            "Keep it to 400-500 words. Use markdown formatting."
        )
    )
    return result


def run_pipeline(topic: str) -> str:
    """
    Runs the full chaining pipeline with gates between each step.
    Stops early if any step produces low-quality output.
    """
    print(f"\n{'='*60}")
    print(f"PROMPT CHAINING DEMO — Topic: {topic}")
    print('='*60)

    # Step 1 — Research
    key_points = step1_research(topic)
    if not gate_check(key_points, minimum_words=30):
        return "Pipeline stopped at Step 1 — poor quality output."

    # Step 2 — Outline
    outline = step2_outline(topic, key_points)
    if not gate_check(outline, minimum_words=50):
        return "Pipeline stopped at Step 2 — poor quality outline."

    # Step 3 — Draft
    draft = step3_draft(topic, outline)
    if not gate_check(draft, minimum_words=200):
        return "Pipeline stopped at Step 3 — draft too short."

    return draft


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    final_post = run_pipeline("The benefits of learning to code as an adult")

    print("\n" + "="*60)
    print("FINAL BLOG POST:")
    print("="*60)
    print(final_post)

    # Key learning: each step's output is the next step's input
    # The chain is only as strong as its weakest step
    print("\n\n--- KEY TAKEAWAY ---")
    print("Each step output → next step input.")
    print("Gates catch bad output before it propagates through the chain.")
