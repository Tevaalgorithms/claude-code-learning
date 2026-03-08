# Module 3 — Accessing Claude with the API

**Notebook:** `module03_accessing_claude_with_api.ipynb`

---

## What This Module Covers

How to call the Claude API directly using the Python SDK — setting up the client,
managing conversation history manually, using system prompts, controlling temperature,
and working with streaming responses.

---

## Key Concepts

### 1. Client Setup

```python
from anthropic import Anthropic
client = Anthropic()  # Reads ANTHROPIC_API_KEY from environment automatically
model = "claude-sonnet-4-0"
```

Always load your API key from an `.env` file — never hardcode it.
The `python-dotenv` library handles this with a single `load_dotenv()` call.

---

### 2. The Messages List — How Claude Tracks Context

Claude has no memory between API calls. Every request must include the **full
conversation history** in the `messages` list. Each message is a dict with a
`role` (`"user"` or `"assistant"`) and `content`.

```python
messages = [
    {"role": "user",      "content": "What is the capital of France?"},
    {"role": "assistant", "content": "The capital of France is Paris."},
    {"role": "user",      "content": "What are the top 3 landmarks there?"},
]
```

The helper functions `add_user_message()` and `add_assistant_message()` simply
append to this list — keeping the conversation thread alive across multiple turns.

**Key insight:** If you start a new `messages = []`, Claude has zero memory of
the previous conversation. The list IS the memory.

---

### 3. Multi-Turn Conversation

The France example in the notebook demonstrates this well. Three questions build
on each other:

1. "What is the capital of France?" → Paris
2. "What are the top 3 famous landmarks there?" → Claude knows "there" means Paris because the history is in the list
3. "Who is the current president of the country?" → Claude knows "the country" means France

Without passing the history each time, question 2 and 3 would have no context to
work from.

---

### 4. System Prompts

A system prompt sets Claude's persona and behaviour for the entire conversation.
It sits outside the `messages` list as a separate `system` parameter.

```python
system_prompt = "You are a patient math instructor. You explain math concepts
in a simple and easy to understand way."

client.messages.create(
    model=model,
    messages=messages,
    system=system_prompt,   # <-- separate from messages
    max_tokens=1000,
)
```

The math instructor example shows how a system prompt shapes every response —
Claude stays in character for all three math questions without needing to be
reminded each time.

**Use system prompts to define:** tone, persona, constraints, output format,
domain expertise.

---

### 5. Temperature

Temperature controls how creative vs predictable Claude's responses are.

| Value | Behaviour | Good For |
|---|---|---|
| `0.0` | Highly deterministic, same answer every time | Code generation, factual Q&A |
| `0.7` | Balanced | General conversation |
| `1.0` (default) | More varied and creative | Brainstorming, creative writing |

The movie idea cell uses `temperature=0.7` — enough creativity for a fun one-liner
without going completely off the rails.

---

### 6. Pre-filling the Assistant Response

One of the more interesting API features — you can put words in Claude's mouth
by adding an `assistant` message at the end of the list *before* calling the API:

```python
messages = []
add_user_message(messages, "Is tea or coffee better at breakfast?")
add_assistant_message(messages, "Coffee is better because")  # Pre-fill
answer = create_message(messages)
```

Claude will continue from where you left off — it *must* complete that sentence.
This is useful for controlling output format, forcing a specific starting point,
or extracting structured data.

---

### 7. Streaming

Instead of waiting for the full response, streaming lets you display tokens as
they arrive — same as how Claude.ai shows text being "typed out".

**Raw streaming (event-by-event):**
```python
stream = client.messages.create(model=model, messages=messages, stream=True)
for event in stream:
    print(event)  # Prints raw event objects including metadata
```

**Text-only streaming (cleaner):**
```python
with client.messages.stream(model=model, messages=messages) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)  # Prints tokens as they arrive
final = stream.get_final_message()  # Get the complete message object after
```

Use `stream=True` when you want low-level control over events.
Use `client.messages.stream()` (context manager) when you just want the text.

---

### 8. Interactive Chatbot Loop

```python
messages = []
while True:
    user_input = input("User: ")
    add_user_message(messages, user_input)
    response = create_message(messages)
    print(f"Assistant: {response}")
    add_assistant_message(messages, response)
```

This is the simplest possible chatbot. The `messages` list grows with each turn,
giving Claude full context of the conversation. In production you'd want a max
context limit and a way to exit the loop.

---

## Things to Explore Next

- [ ] `max_tokens` — what happens when a response hits the limit?
- [ ] Stop sequences — how to tell Claude to stop at a specific word or pattern
- [ ] Token counting — `client.messages.count_tokens()` before sending a request
- [ ] Vision — passing images alongside text in the `content` field
- [ ] Tool use — letting Claude call functions in your code

---

## Files

| File | Description |
|---|---|
| `module03_accessing_claude_with_api.ipynb` | Notebook with all demos |
| `NOTES.md` | This file — concept notes and explanations |
