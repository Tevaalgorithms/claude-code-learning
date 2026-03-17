"""
Demo 03 — Routing
==================
Pattern: Classify the input first, then send to the right specialist.

Use case: Customer support router
  - billing   → knows refund policies, subscription plans
  - technical → knows product troubleshooting
  - general   → friendly general assistant

Run:
    python module-03-claude-api/agents_workflows/03_routing_demo.py
"""

import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL  = "claude-sonnet-4-0"


# ── Specialist system prompts ────────────────────────────────────────────────

SPECIALISTS = {
    "billing": """You are a billing support specialist for TechCorp.
You help customers with invoices, refunds, subscription changes, and payment issues.
Key policies:
- Refunds available within 30 days of purchase
- Subscription can be cancelled anytime, takes effect end of billing cycle
- Failed payments get a 3-day grace period before account suspension
Be professional and empathetic.""",

    "technical": """You are a technical support specialist for TechCorp.
You help customers troubleshoot software bugs, connectivity issues, and account access problems.
Common fixes:
- Login issues: clear cache, reset password
- Slow performance: check system requirements, clear app cache
- Sync errors: sign out and back in, check internet connection
Be clear and give step-by-step instructions.""",

    "general": """You are a friendly general support assistant for TechCorp.
You help with general questions about products, features, and company information.
If a question is clearly about billing or technical issues, let the user know
you can connect them with the right specialist.
Be warm, concise, and helpful."""
}


def classify_message(message: str) -> str:
    """
    Step 1: Classify the incoming message.
    Returns one of: "billing", "technical", "general"

    Note: The classifier prompt asks for JSON output so routing
    logic is predictable — no string parsing needed.
    """
    response = client.messages.create(
        model      = MODEL,
        max_tokens = 100,
        system     = """Classify customer support messages into exactly one category.
Respond with ONLY valid JSON: {"category": "<category>", "reason": "<one sentence why>"}
Categories:
- billing: payment, invoice, refund, subscription, charge, plan, price
- technical: bug, error, broken, not working, slow, crash, login, password, sync
- general: everything else""",
        messages   = [{"role": "user", "content": f"Classify: {message}"}]
    )

    try:
        data = json.loads(response.content[0].text)
        return data.get("category", "general"), data.get("reason", "")
    except json.JSONDecodeError:
        return "general", "Could not classify"


def handle_with_specialist(category: str, message: str) -> str:
    """
    Step 2: Route to the right specialist and get a response.
    """
    system_prompt = SPECIALISTS.get(category, SPECIALISTS["general"])

    response = client.messages.create(
        model      = MODEL,
        max_tokens = 512,
        system     = system_prompt,
        messages   = [{"role": "user", "content": message}]
    )
    return response.content[0].text.strip()


def route_and_respond(message: str) -> dict:
    """
    Full routing pipeline:
    1. Classify → get category
    2. Route to specialist → get response
    """
    print(f"\nUser: {message}")
    print("-" * 50)

    # Step 1: Classify
    category, reason = classify_message(message)
    print(f"Classified as: [{category.upper()}] — {reason}")

    # Step 2: Handle with specialist
    response = handle_with_specialist(category, message)
    print(f"Specialist [{category}]: {response}")

    return {"category": category, "response": response}


# ── Run examples ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_messages = [
        "I was charged twice this month, can I get a refund?",
        "The app keeps crashing when I try to upload a file",
        "What are your business hours?",
        "My subscription auto-renewed but I cancelled it last week",
        "I can't log in — it says my password is wrong but I just reset it",
        "Do you have a mobile app?"
    ]

    print("=" * 60)
    print("ROUTING DEMO — Customer Support Router")
    print("=" * 60)

    for msg in test_messages:
        route_and_respond(msg)
        print()

    print("\n--- KEY TAKEAWAY ---")
    print("Classify FIRST with structured output (JSON).")
    print("Each specialist has a focused system prompt — better than one generic prompt.")
    print("Routing makes the system cheaper: simple questions hit the same small model.")
