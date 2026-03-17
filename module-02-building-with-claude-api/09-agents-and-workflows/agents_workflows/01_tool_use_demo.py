"""
Demo 01 — Tool Use (Foundation of Agents)
==========================================
Shows the full tool call cycle:
  1. Define a tool
  2. Send to Claude
  3. Claude responds with tool_use (stop_reason = "tool_use")
  4. Run your actual function
  5. Return tool_result to Claude
  6. Claude gives final answer

Run:
    cd ~/github-profile/claude-code-learning
    source ~/Anthrophic/.venv/bin/activate
    python module-03-claude-api/agents_workflows/01_tool_use_demo.py
"""

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL  = "claude-sonnet-4-0"

# ── 1. Define your tools ────────────────────────────────────────────────────

tools = [
    {
        "name": "get_weather",
        "description": (
            "Get the current weather for a given city. "
            "Use this when the user asks about weather conditions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name, e.g. 'London' or 'Toronto'"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit. Defaults to celsius."
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_time",
        "description": "Get the current local time for a given city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city to get the time for"
                }
            },
            "required": ["city"]
        }
    }
]


# ── 2. Fake implementations (in real life, call an API) ─────────────────────

def get_weather(city: str, unit: str = "celsius") -> dict:
    """Simulated weather data."""
    fake_data = {
        "london":  {"temp": 12, "condition": "Cloudy",  "humidity": 78},
        "toronto": {"temp": -2, "condition": "Snowing",  "humidity": 90},
        "sydney":  {"temp": 25, "condition": "Sunny",    "humidity": 55},
    }
    data = fake_data.get(city.lower(), {"temp": 20, "condition": "Clear", "humidity": 60})
    temp = data["temp"]
    if unit == "fahrenheit":
        temp = round(temp * 9/5 + 32, 1)
    return {"city": city, "temperature": temp, "unit": unit,
            "condition": data["condition"], "humidity": data["humidity"]}


def get_time(city: str) -> dict:
    """Simulated time data."""
    fake_times = {
        "london":  "14:30 GMT",
        "toronto": "09:30 EST",
        "sydney":  "01:30 AEDT",
    }
    return {"city": city, "time": fake_times.get(city.lower(), "12:00 UTC")}


def run_tool(name: str, inputs: dict) -> str:
    """Dispatcher — maps tool name to actual function."""
    if name == "get_weather":
        result = get_weather(**inputs)
    elif name == "get_time":
        result = get_time(**inputs)
    else:
        result = {"error": f"Unknown tool: {name}"}
    return str(result)


# ── 3. The agent function ────────────────────────────────────────────────────

def run_agent(user_message: str) -> str:
    """
    Runs the tool-use loop:
    - Sends the message to Claude with tools available
    - If Claude calls a tool, runs it and sends back the result
    - Repeats until Claude gives a final text answer
    """
    print(f"\nUser: {user_message}")
    print("-" * 50)

    messages = [{"role": "user", "content": user_message}]

    max_iterations = 5
    for i in range(max_iterations):
        response = client.messages.create(
            model      = MODEL,
            max_tokens = 1024,
            tools      = tools,
            messages   = messages
        )

        print(f"[Iteration {i+1}] stop_reason = {response.stop_reason}")

        # Claude is done — return the final text
        if response.stop_reason == "end_turn":
            final_text = next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            )
            return final_text

        # Claude wants to call tools
        if response.stop_reason == "tool_use":
            # Add Claude's response (with tool_use blocks) to history
            messages.append({"role": "assistant", "content": response.content})

            # Process every tool call in this response
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → Tool call : {block.name}({block.input})")
                    result = run_tool(block.name, block.input)
                    print(f"  ← Tool result: {result}")
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     result
                    })

            # Send all results back to Claude
            messages.append({"role": "user", "content": tool_results})

    return "Max iterations reached."


# ── 4. Run examples ──────────────────────────────────────────────────────────

if __name__ == "__main__":

    # Single tool call
    answer = run_agent("What's the weather like in London right now?")
    print(f"\nFinal answer:\n{answer}")

    print("\n" + "=" * 60)

    # Multiple tool calls in one request
    answer = run_agent("What's the weather and current time in Sydney?")
    print(f"\nFinal answer:\n{answer}")

    print("\n" + "=" * 60)

    # No tool needed — Claude answers directly
    answer = run_agent("What is the capital of France?")
    print(f"\nFinal answer:\n{answer}")
