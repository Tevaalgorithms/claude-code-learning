"""
Demo 05 — Orchestrator–Subagents
==================================
Pattern: One Claude (orchestrator) plans and delegates.
         Other Claude instances (subagents) are specialists with focused tools.

Use case: Research assistant
  Orchestrator → decides which subagents to call
  Subagents    → web_researcher, data_analyst, report_writer

This mirrors the Amazon Bedrock multi-agent pattern from the e-commerce project:
  Supervisor Agent = Orchestrator
  ProductAgent, OrderAgent etc. = Subagents

Run:
    python module-03-claude-api/agents_workflows/05_orchestrator_subagent_demo.py
"""

import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL  = "claude-sonnet-4-0"


# ── Subagent definitions ─────────────────────────────────────────────────────
# Each subagent has a specialized system prompt and a set of tools.
# In production these could be separate Lambda functions or API endpoints.

SUBAGENTS = {
    "web_researcher": {
        "system": (
            "You are a web research specialist. You find factual information "
            "on any topic and return well-structured findings with key statistics."
        ),
        "description": "Finds facts, statistics, and background information on any topic"
    },
    "data_analyst": {
        "system": (
            "You are a data analyst. You interpret data and trends, identify "
            "patterns, and provide quantitative insights. Format numbers clearly."
        ),
        "description": "Analyses data, identifies trends, provides quantitative insights"
    },
    "report_writer": {
        "system": (
            "You are a professional report writer. You synthesise information "
            "from multiple sources into clear, well-structured reports. "
            "Use headers, bullet points, and a professional tone."
        ),
        "description": "Synthesises research into professional, structured reports"
    }
}


def call_subagent(agent_name: str, task: str) -> str:
    """Invoke a named subagent with a specific task."""
    agent = SUBAGENTS.get(agent_name)
    if not agent:
        return f"Error: Unknown subagent '{agent_name}'"

    print(f"    [Subagent: {agent_name}] Task: {task[:80]}...")

    response = client.messages.create(
        model      = MODEL,
        max_tokens = 1024,
        system     = agent["system"],
        messages   = [{"role": "user", "content": task}]
    )
    result = response.content[0].text.strip()
    print(f"    [Subagent: {agent_name}] Done ✓")
    return result


# ── Orchestrator tools ───────────────────────────────────────────────────────
# The orchestrator has one tool per subagent — it decides which to call and when.

orchestrator_tools = [
    {
        "name": "delegate_to_web_researcher",
        "description": SUBAGENTS["web_researcher"]["description"],
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The research task to perform"
                }
            },
            "required": ["task"]
        }
    },
    {
        "name": "delegate_to_data_analyst",
        "description": SUBAGENTS["data_analyst"]["description"],
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The data analysis task to perform"
                },
                "data": {
                    "type": "string",
                    "description": "The data or findings to analyse"
                }
            },
            "required": ["task"]
        }
    },
    {
        "name": "delegate_to_report_writer",
        "description": SUBAGENTS["report_writer"]["description"],
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The writing task to perform"
                },
                "content": {
                    "type": "string",
                    "description": "All gathered content to include in the report"
                }
            },
            "required": ["task", "content"]
        }
    }
]


def run_tool(tool_name: str, tool_input: dict) -> str:
    """Map orchestrator tool names to subagent calls."""
    mapping = {
        "delegate_to_web_researcher": "web_researcher",
        "delegate_to_data_analyst":   "data_analyst",
        "delegate_to_report_writer":  "report_writer"
    }
    agent_name = mapping.get(tool_name)
    if not agent_name:
        return f"Unknown tool: {tool_name}"

    task = tool_input.get("task", "")
    data = tool_input.get("data", "")
    content = tool_input.get("content", "")
    full_task = task
    if data:
        full_task += f"\n\nData to analyse:\n{data}"
    if content:
        full_task += f"\n\nContent to include:\n{content}"

    return call_subagent(agent_name, full_task)


# ── Orchestrator loop ────────────────────────────────────────────────────────

ORCHESTRATOR_SYSTEM = """You are a research orchestration agent.

You have access to three specialist subagents:
1. delegate_to_web_researcher — for finding facts and background information
2. delegate_to_data_analyst   — for interpreting and analysing data
3. delegate_to_report_writer  — for writing the final structured report

For any research request:
1. First delegate to web_researcher to gather facts
2. Then delegate to data_analyst to interpret the findings
3. Finally delegate to report_writer to produce the polished output

Always delegate — do not answer research questions yourself."""


def run_orchestrator(user_request: str) -> str:
    """
    Runs the full orchestrator–subagent loop.
    The orchestrator decides which subagents to call and in what order.
    """
    print(f"\n{'='*60}")
    print(f"ORCHESTRATOR–SUBAGENT DEMO")
    print(f"Request: {user_request}")
    print("="*60)

    messages = [{"role": "user", "content": user_request}]

    max_iterations = 10
    for i in range(max_iterations):
        print(f"\n[Orchestrator turn {i+1}]")

        response = client.messages.create(
            model      = MODEL,
            max_tokens = 2048,
            system     = ORCHESTRATOR_SYSTEM,
            tools      = orchestrator_tools,
            messages   = messages
        )

        print(f"  stop_reason = {response.stop_reason}")

        # Orchestrator finished
        if response.stop_reason == "end_turn":
            final = next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            )
            return final

        # Orchestrator is delegating
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → Delegating to: {block.name}")
                    result = run_tool(block.name, block.input)
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     result
                    })

            messages.append({"role": "user", "content": tool_results})

    return "Max iterations reached."


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    final_report = run_orchestrator(
        "Research the current state of electric vehicle adoption globally. "
        "Include key statistics, trends, and produce a professional summary report."
    )

    print("\n" + "="*60)
    print("FINAL REPORT:")
    print("="*60)
    print(final_report)

    print("\n\n--- KEY TAKEAWAYS ---")
    print("Orchestrator does NOT do the work — it plans and delegates.")
    print("Each subagent has a focused system prompt → specialist quality.")
    print("This is exactly how AWS Bedrock multi-agent systems work.")
