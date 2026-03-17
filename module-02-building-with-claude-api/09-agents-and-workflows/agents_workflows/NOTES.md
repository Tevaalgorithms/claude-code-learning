# Agents and Workflows — Study Notes

**Course:** Building with the Claude API (Anthropic SkillJar)
**Section:** Agents and Workflows

---

## 1. What is an Agent?

An **agent** is Claude operating in a loop — it can decide to use tools, act on
the results, and keep going until the task is complete. Instead of a single
request → response, an agent does:

```
User request
    ↓
Claude thinks → decides to use a tool
    ↓
Tool runs → result returned to Claude
    ↓
Claude thinks again → use another tool? or respond?
    ↓
Final answer to user
```

The key difference from a regular API call:
- Regular call: **1 input → 1 output**
- Agent: **1 input → many tool calls → 1 final output**

---

## 2. Tool Use — The Foundation of Agents

Tools are functions you define that Claude can choose to call. You describe
each tool in JSON schema, and Claude decides when and how to call them.

### How it works

```
1. You define tools (name, description, input schema)
2. You send user message + tools to Claude
3. Claude responds with a tool_use block (not text)
4. You run the actual function and get the result
5. You send the result back to Claude as tool_result
6. Claude uses the result to form its final answer
```

### Tool definition structure

```python
tools = [
    {
        "name": "get_weather",
        "description": "Get current weather for a city. Use this when the user asks about weather.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name, e.g. 'London'"
                }
            },
            "required": ["city"]
        }
    }
]
```

### Stop reason signals

| `stop_reason` | Meaning |
|---|---|
| `"end_turn"` | Claude finished — no more tool calls needed |
| `"tool_use"` | Claude wants to call a tool — extract and run it |

### Full tool call / result cycle

```python
# Step 1: Claude asks to use a tool
response = client.messages.create(
    model=model, messages=messages, tools=tools
)

if response.stop_reason == "tool_use":
    # Step 2: Find which tool Claude chose
    tool_block = next(b for b in response.content if b.type == "tool_use")

    # Step 3: Run your actual function
    result = my_function(**tool_block.input)

    # Step 4: Add Claude's tool request + your result to messages
    messages.append({"role": "assistant", "content": response.content})
    messages.append({
        "role": "user",
        "content": [{
            "type": "tool_result",
            "tool_use_id": tool_block.id,
            "content": str(result)
        }]
    })

    # Step 5: Send back to Claude for final answer
    final = client.messages.create(model=model, messages=messages, tools=tools)
```

---

## 3. The Agentic Loop

When a task requires multiple tool calls, wrap everything in a while loop:

```python
while response.stop_reason == "tool_use":
    # Process all tool calls in this response
    for block in response.content:
        if block.type == "tool_use":
            result = run_tool(block.name, block.input)
            # append tool_result to messages ...

    # Ask Claude again with the results
    response = client.messages.create(...)

# Loop exits when stop_reason == "end_turn"
print(response.content[0].text)
```

**Important:** Always set a max iteration limit to prevent infinite loops:
```python
max_iterations = 10
iteration = 0
while response.stop_reason == "tool_use" and iteration < max_iterations:
    iteration += 1
    ...
```

---

## 4. The Five Workflow Patterns

Anthropic defines 5 patterns for building reliable agentic systems.
Each pattern solves a different type of problem.

---

### Pattern 1: Prompt Chaining

**What it is:** Break a complex task into sequential steps.
Output of step N feeds into step N+1.

```
Input → [Step 1: Extract] → [Step 2: Analyse] → [Step 3: Format] → Output
```

**When to use:**
- Tasks with clear, ordered stages
- When each step needs to fully complete before the next begins
- When you want to validate/check output between steps

**Example use case:** Blog post pipeline
```
Raw topic
  → Step 1: Research key points
  → Step 2: Write outline
  → Step 3: Write full draft
  → Step 4: Edit for tone
  → Final post
```

**Key insight:** Add a "gate" between steps to check quality before proceeding.
If a step fails the gate, stop early rather than propagating bad output.

---

### Pattern 2: Routing

**What it is:** Classify the input first, then send it to a specialist handler.

```
Input → [Classifier] → route A → [Specialist A]
                     → route B → [Specialist B]
                     → route C → [Specialist C]
```

**When to use:**
- Different input types need very different handling
- You want to use cheaper/faster models for simple cases
- Specialist prompts outperform a single generalist prompt

**Example use case:** Customer support router
```
User message
  → Classify: billing | technical | general
  → billing   → billing specialist (knows refund policies)
  → technical → tech specialist (knows product docs)
  → general   → general assistant
```

**Key insight:** The classifier should output a simple, structured label
(not free text) so routing logic is predictable.

---

### Pattern 3: Parallelization

**What it is:** Run multiple Claude calls simultaneously and combine results.
Two sub-patterns:

**3a. Sectioning** — split a big task into independent chunks, process in parallel:
```
Large document
  → [Chunk 1] [Chunk 2] [Chunk 3]   ← all run at the same time
  → Combine results
```

**3b. Voting** — run the same task N times, take majority answer:
```
Question
  → [Claude call 1] [Claude call 2] [Claude call 3]
  → Most common answer wins
```

**When to use:**
- Independent subtasks (sectioning)
- Need high confidence / reduce variance (voting)
- Speed matters and tasks don't depend on each other

**Implementation:** Use `asyncio` or `ThreadPoolExecutor` in Python:
```python
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(analyze_chunk, chunk) for chunk in chunks]
    results = [f.result() for f in futures]
```

---

### Pattern 4: Orchestrator–Subagents

**What it is:** One Claude (the orchestrator) plans and delegates tasks.
Other Claude instances (subagents) execute the individual tasks.

```
User goal → [Orchestrator: plans & delegates]
                → [Subagent A: web search]
                → [Subagent B: code execution]
                → [Subagent C: file writing]
            Orchestrator combines results → Final answer
```

**When to use:**
- Complex tasks that require different specializations
- Tasks where you don't know upfront how many steps are needed
- When subtasks can run independently

**Key insight:** The orchestrator doesn't do the actual work — it just decides
WHAT to do and WHO should do it. Each subagent has its own focused tools and
system prompt.

**This is exactly the Amazon Bedrock multi-agent pattern** from the e-commerce project:
- Supervisor Agent = Orchestrator
- ProductSearchAgent, OrderAgent, etc. = Subagents

---

### Pattern 5: Evaluator–Optimizer

**What it is:** One Claude generates output. Another Claude evaluates it.
Loop until quality threshold is met.

```
Task → [Generator] → draft
            ↑            ↓
       (revise)    [Evaluator] → PASS → Final output
                        ↓
                      FAIL + feedback
```

**When to use:**
- Output quality is measurable/verifiable
- You have clear criteria for "good enough"
- Tasks where iterative improvement is natural (writing, code, etc.)

**Example use case:** Code review loop
```
Write a function
  → Evaluator: does it handle edge cases? is it efficient?
  → FAIL: "missing null check"
  → Generator revises with feedback
  → Evaluator: now checks out ✓
  → Return final code
```

**Key insight:** The evaluator's feedback must be specific and actionable,
not just "try again." Include what's wrong AND what would make it pass.

---

## 5. Choosing the Right Pattern

| Situation | Pattern to use |
|---|---|
| Task has ordered, dependent steps | Prompt Chaining |
| Different inputs need different handling | Routing |
| Tasks are independent and can run together | Parallelization |
| Complex goal needs planning + specialised execution | Orchestrator–Subagents |
| Output quality needs to meet a bar | Evaluator–Optimizer |
| Really complex task | Combine patterns |

---

## 6. Key Principles for Reliable Agents

### Give Claude enough context
The system prompt must clearly define:
- What the agent's job is
- What tools are available and when to use each
- What to do when uncertain

### Minimal footprint
Only request permissions the agent actually needs.
Prefer reversible actions over irreversible ones.
When in doubt, pause and ask the human.

### Human in the loop
For high-stakes actions (deleting data, sending emails, spending money),
add a confirmation step before executing.

```python
# Before irreversible action
if action.is_irreversible:
    confirm = input(f"About to {action}. Confirm? (y/n): ")
    if confirm != 'y':
        return "Action cancelled."
```

### Inject fresh context
Agents can drift over long tasks. Remind them of the goal
periodically in long agentic loops.

---

## 7. Tool Design Best Practices

| Do | Don't |
|---|---|
| Write clear, specific descriptions | Use vague names like `do_thing` |
| Explain WHEN to use the tool | Assume Claude knows from the name |
| Mark truly required params as required | Mark everything required |
| Return structured data (JSON) | Return unstructured text blobs |
| Include error info in the result | Return empty strings on failure |

---

## 8. Quick Reference

```python
# Check if Claude wants to use a tool
if response.stop_reason == "tool_use":
    ...

# Find the tool_use block
tool_block = next(b for b in response.content if b.type == "tool_use")
tool_name  = tool_block.name    # e.g. "get_weather"
tool_input = tool_block.input   # e.g. {"city": "London"}
tool_id    = tool_block.id      # needed for tool_result

# Return the result back to Claude
{
    "type": "tool_result",
    "tool_use_id": tool_id,      # must match the tool_use block id
    "content": str(result)       # your function's return value as string
}
```

---

## Demo Files in This Folder

| File | Pattern | What it shows |
|---|---|---|
| `01_tool_use_demo.py` | Tool Use | Basic single tool call cycle |
| `02_prompt_chaining_demo.py` | Prompt Chaining | 3-step blog post pipeline |
| `03_routing_demo.py` | Routing | Customer support router |
| `04_parallelization_demo.py` | Parallelization | Parallel document analysis |
| `05_orchestrator_subagent_demo.py` | Orchestrator–Subagents | Research assistant with specialist agents |
| `06_evaluator_optimizer_demo.py` | Evaluator–Optimizer | Code quality improvement loop |
