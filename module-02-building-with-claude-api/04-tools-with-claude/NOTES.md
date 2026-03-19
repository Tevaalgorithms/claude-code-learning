# Module 02 — Tools with Claude: Notes

---

## The Core Problem

Claude is a language model — it can only read and write text/JSON.
It **cannot** call Python functions directly.

So "tool use" is actually a **3-step handshake** between your code and Claude:

```
YOUR CODE  ──[1. here are tools that exist]──►  CLAUDE
YOUR CODE  ◄──[2. please call X with args Y]──  CLAUDE
YOUR CODE  ──[3. here is the result of X(Y)]──► CLAUDE
```

Everything below is just machinery to make those three steps work.

---

## Key Vocabulary

### Schema
A JSON object that describes one tool to Claude. Claude reads it to know:
- what the tool is **named** (it uses this name when requesting a call)
- what it **does** (description — Claude reads this to decide *when* to use it)
- what **arguments** to pass (input_schema — property names, types, which are required)

```python
weather_schema = {
    "name": "get_weather",
    "description": "Return the current weather for a given city.",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name, e.g. London or Tokyo."
            }
        },
        "required": ["city"],
    },
}
```

You pass schemas to Claude via `tools=[schema]` in `client.messages.create()`.
**Claude never sees your Python function — only this JSON description.**

---

### tool_use block
When Claude decides to use a tool, its response contains a `tool_use` block:

```python
# response.content might look like:
# [TextBlock(text="Let me check that for you."),
#  ToolUseBlock(name="get_weather", input={"city": "Paris"}, id="toolu_abc123")]

tool_block = next(b for b in response.content if b.type == "tool_use")

tool_block.name   # "get_weather"   — which tool Claude wants
tool_block.input  # {"city": "Paris"} — the arguments Claude chose
tool_block.id     # "toolu_abc123"  — unique ID for this request (needed for the reply)
```

This is Claude saying: *"I want someone to call `get_weather` with `city="Paris"`. My request ID is `toolu_abc123`."*

Claude has not called anything. It is waiting for you.

---

### Dispatcher
Your code that maps the tool **name** Claude gave you to the actual **Python function** to run.

**Simple version (if/elif):**
```python
if tool_block.name == "get_weather":
    result = get_weather(**tool_block.input)
elif tool_block.name == "calculate":
    result = calculate(**tool_block.input)
```

**Cleaner version (dictionary):**
```python
TOOL_REGISTRY = {
    "get_weather": lambda inp: get_weather(inp["city"]),
    "calculate":   lambda inp: calculate(inp["expression"]),
}

result = TOOL_REGISTRY[tool_block.name](tool_block.input)
```

Both do the same thing. The dictionary version scales better when you have many tools.

---

### tool_result
After you call your function, you send the result back to Claude in a `tool_result` block, linked to Claude's original request via the `tool_use_id`:

```python
messages.append({"role": "assistant", "content": response.content})  # echo Claude's turn
messages.append({
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": tool_block.id,   # must match the tool_use block
        "content": result,              # the actual data from your function
    }]
})
```

Now Claude has the data and can write its final answer.

---

### stop_reason
Every Claude response has a `stop_reason` that tells you *why* it stopped generating:

| stop_reason | Meaning | What to do |
|---|---|---|
| `end_turn` | Claude finished — no more tool calls | Read the final text and stop |
| `tool_use` | Claude wants to call one or more tools | Execute tools, send results back, call API again |
| `pause_turn` | Server hit its internal loop limit | Re-send the messages — Claude will resume |
| `max_tokens` | Hit your `max_tokens` limit | Increase `max_tokens` |

In an agentic loop you check `stop_reason` on every response:

```python
while True:
    response = client.messages.create(...)

    if response.stop_reason == "end_turn":
        break                              # done

    if response.stop_reason == "pause_turn":
        messages.append({"role": "assistant", "content": response.content})
        continue                           # re-send, Claude resumes

    if response.stop_reason == "tool_use":
        # ... execute tools, append results, loop again
```

---

## Three Approaches — Summary

### Approach A — Manual (most explicit)
```
You write:   function + JSON schema (by hand) + if/elif dispatcher + 2 API calls
Best for:    learning the protocol, understanding what's happening
```

### Approach B — Dispatcher Dictionary
```
You write:   function + JSON schema (by hand) + dict registry + 2 API calls
Best for:    multiple tools, when you need custom logic between tool calls
```

### Approach C — @beta_tool + Tool Runner (least boilerplate)
```
You write:   decorated function only
SDK handles: schema generation, dispatching, looping, sending results back
Best for:    production code, minimal repetition
```

```python
# Approach C in full:
@beta_tool
def get_weather_tool(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The city name, e.g. London or Tokyo.
    """
    return get_weather(city)    # calls your real function

for message in client.beta.messages.tool_runner(
    model=MODEL,
    max_tokens=256,
    tools=[get_weather_tool],
    messages=[{"role": "user", "content": "Weather in London?"}],
):
    for block in message.content:
        if block.type == "text":
            print(block.text)
```

---

## What `@beta_tool` Does Under the Hood

The decorator inspects your function and auto-generates the schema:

| Source | Becomes |
|---|---|
| Function name `get_weather_tool` | `"name": "get_weather_tool"` |
| Docstring first line | `"description": "..."` |
| `city: str` type hint | `"city": {"type": "string"}` |
| `Args: city: ...` docstring | `"city": {"description": "..."}` |
| Parameters without defaults | added to `"required": [...]` |

You can inspect the generated schema:
```python
import json
print(json.dumps(get_weather_tool.tool_schema, indent=2))
```

---

## Common Mistakes

**1. Forgetting to append the assistant turn before tool results**
```python
# ❌ Wrong — Claude loses context of what it requested
messages.append({"role": "user", "content": [tool_result_block]})

# ✅ Correct — always include the assistant turn first
messages.append({"role": "assistant", "content": response.content})
messages.append({"role": "user", "content": [tool_result_block]})
```

**2. Mismatching tool_use_id**
```python
# ❌ Wrong — Claude can't match result to its request
{"type": "tool_result", "tool_use_id": "made_up_id", "content": result}

# ✅ Correct — use the exact ID from the tool_use block
{"type": "tool_result", "tool_use_id": tool_block.id, "content": result}
```

**3. Only returning the text and not the full content block list**
```python
# ❌ Wrong — loses the tool_use blocks, breaks the conversation
messages.append({"role": "assistant", "content": response.content[0].text})

# ✅ Correct — append the full content list
messages.append({"role": "assistant", "content": response.content})
```

**4. Stopping after the first tool call**
Claude may call tools multiple times before finishing. Always loop until `stop_reason == "end_turn"`.

---

## Notebooks in This Section

| Notebook | What it covers |
|---|---|
| `001_tools.ipynb` | The manual approach step by step (schemas, tool_use, tool_result) |
| `002_agent_loop.ipynb` | Full agent loop, tool runner, error handling, session management, subagents |
| `003_three_approaches_compared.ipynb` | Same tool, all three approaches side by side |
