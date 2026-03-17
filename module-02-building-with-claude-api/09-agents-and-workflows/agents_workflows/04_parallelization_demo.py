"""
Demo 04 — Parallelization
==========================
Pattern A — Sectioning: Split a large task into chunks, run simultaneously.
Pattern B — Voting: Run same task multiple times, take majority answer.

Run:
    python module-03-claude-api/agents_workflows/04_parallelization_demo.py
"""

import anthropic
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL  = "claude-sonnet-4-0"


def call_claude(system: str, user: str, max_tokens: int = 512) -> str:
    response = client.messages.create(
        model      = MODEL,
        max_tokens = max_tokens,
        system     = system,
        messages   = [{"role": "user", "content": user}]
    )
    return response.content[0].text.strip()


# ════════════════════════════════════════════════════════════════
# PATTERN A: Sectioning — analyse each section in parallel
# ════════════════════════════════════════════════════════════════

# Simulated long document split into sections
DOCUMENT_SECTIONS = {
    "Executive Summary": """
    TechCorp Q4 2025 results exceeded expectations with 23% revenue growth YoY.
    The company launched 3 new products and expanded into 5 new markets.
    Operating margin improved from 18% to 22% driven by cost optimisation.
    """,
    "Financial Performance": """
    Revenue: $4.2B (up 23% YoY). Net income: $924M (up 31% YoY).
    Gross margin: 68%. R&D spend increased 15% to $630M.
    Cash position: $2.1B. Debt reduced by $400M ahead of schedule.
    """,
    "Product Updates": """
    Launched CloudSync Pro (B2B), MobileFirst 3.0 (consumer), and DataBridge API.
    CloudSync Pro acquired 12,000 enterprise customers in 60 days.
    MobileFirst 3.0 has 4.8/5 rating with 2M downloads in Q4.
    """,
    "Market Expansion": """
    Entered Brazil, India, South Korea, Germany, and Australia.
    APAC now represents 18% of total revenue (up from 11%).
    Partnership with Deutsche Telekom announced for European distribution.
    """,
    "Risks and Challenges": """
    Supply chain disruptions impacting hardware division margins.
    Regulatory scrutiny in EU around data privacy practices.
    Talent competition intensifying, attrition rate rose from 8% to 11%.
    """
}


def analyse_section(section_name: str, section_text: str) -> dict:
    """Analyse one document section — runs in parallel with others."""
    result = call_claude(
        system = "You are a business analyst. Provide concise, structured analysis.",
        user   = (
            f"Analyse this section of a quarterly report:\n\n"
            f"Section: {section_name}\n{section_text}\n\n"
            "Return JSON with keys: key_insight (1 sentence), sentiment (positive/neutral/negative), "
            "action_required (true/false), summary (2 sentences)"
        )
    )
    try:
        return {"section": section_name, **json.loads(result)}
    except json.JSONDecodeError:
        return {"section": section_name, "summary": result}


def run_sectioning_demo():
    print("\n" + "="*60)
    print("PATTERN A: Sectioning (Parallel Document Analysis)")
    print("="*60)

    start = time.time()

    # Run all section analyses in parallel
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(analyse_section, name, text): name
            for name, text in DOCUMENT_SECTIONS.items()
        }
        for future in as_completed(futures):
            section_name = futures[future]
            result = future.result()
            results.append(result)
            print(f"  ✓ Completed: {section_name}")

    elapsed = time.time() - start
    print(f"\nAll {len(results)} sections analysed in {elapsed:.1f}s (parallel)")
    print(f"Sequential would take ~{len(results) * 2}s+ estimated\n")

    # Print summaries
    for r in sorted(results, key=lambda x: x['section']):
        sentiment = r.get('sentiment', 'N/A')
        print(f"[{sentiment.upper():8}] {r['section']}: {r.get('key_insight', r.get('summary',''))}")

    # Aggregate summary
    print("\n--- Aggregate Summary ---")
    all_insights = "\n".join(
        f"- {r['section']}: {r.get('key_insight', r.get('summary',''))}"
        for r in results
    )
    summary = call_claude(
        system = "You are a senior analyst. Synthesise findings into an executive summary.",
        user   = f"Synthesise these section analyses into a 3-sentence executive summary:\n{all_insights}"
    )
    print(summary)


# ════════════════════════════════════════════════════════════════
# PATTERN B: Voting — same question, multiple runs, majority wins
# ════════════════════════════════════════════════════════════════

def single_classification(text: str, run_id: int) -> str:
    """One classification run — used N times in parallel for voting."""
    result = call_claude(
        system = (
            "You are a content moderator. Classify text as exactly one of: "
            "SAFE, SPAM, HARMFUL. Respond with ONLY the label."
        ),
        user = f"Classify: {text}"
    )
    label = result.strip().upper()
    # Normalise to valid labels
    if label not in {"SAFE", "SPAM", "HARMFUL"}:
        label = "SAFE"
    print(f"  Run {run_id}: {label}")
    return label


def classify_with_voting(text: str, num_votes: int = 3) -> str:
    """
    Run the same classification N times in parallel.
    Return the majority vote — reduces variance from stochastic outputs.
    """
    with ThreadPoolExecutor(max_workers=num_votes) as executor:
        futures = [executor.submit(single_classification, text, i+1)
                   for i in range(num_votes)]
        votes = [f.result() for f in futures]

    from collections import Counter
    tally = Counter(votes)
    winner = tally.most_common(1)[0][0]
    return winner, dict(tally)


def run_voting_demo():
    print("\n" + "="*60)
    print("PATTERN B: Voting (Majority Wins)")
    print("="*60)

    test_cases = [
        "Buy cheap meds online! Click here now!!",
        "The weather forecast shows rain tomorrow",
        "I will find where you live and make you regret this",
        "Great tutorial, really helped me understand the concept"
    ]

    for text in test_cases:
        print(f"\nText: \"{text[:60]}\"")
        decision, tally = classify_with_voting(text, num_votes=3)
        print(f"  Votes: {tally}  →  Final decision: {decision}")


# ── Run both patterns ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_sectioning_demo()
    run_voting_demo()

    print("\n\n--- KEY TAKEAWAYS ---")
    print("Sectioning: Independent tasks run simultaneously → major speed gains.")
    print("Voting:     Same task N times → more reliable than single run.")
    print("Both use ThreadPoolExecutor — simple and effective for I/O-bound tasks.")
