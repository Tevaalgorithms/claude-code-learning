# Module 1 — Claude Code in Action: Fundamentals

---

## What This Module Covers

How Claude Code works as an agentic CLI tool — its tool system, context management,
planning modes, custom commands, MCP integrations, hooks, subagents, and session workflows.

---

## Key Concepts

### 1. What is Claude Code?

Claude Code is a command-line AI assistant that uses language models to perform
development tasks directly in your terminal.

**How it works — the agentic loop:**

```
reads context → decides action → executes tool → evaluates result → repeats
```

It operates through a **tool system** that handles file operations, command execution,
and code analysis. Claude decides which tools to call, runs them, and uses the results
to inform the next step — autonomously, until the task is complete.

---

### 2. Installation & Setup

```bash
npm install -g @anthropic-ai/claude-code
```

- Run `/init` on first use in a project — generates a `CLAUDE.md` configuration file
- Requires an `ANTHROPIC_API_KEY` environment variable
- Can also be configured for **Amazon Bedrock** or **Google Vertex AI**

---

### 3. Core Tools

| Tool | Purpose |
|---|---|
| `Read` | Read file contents |
| `Write` | Create new files |
| `Edit` | Modify existing files with precise replacements |
| `Glob` | Find files by pattern (e.g., `**/*.ts`) |
| `Grep` | Search file contents with regex |
| `Bash` | Execute shell commands |
| `Task` | Launch specialized subagents for parallel work |
| `WebFetch` / `WebSearch` | Retrieve web content |

---

### 4. Key Hotkeys & Commands

| Shortcut | Action |
|---|---|
| `Enter` | Send message |
| `Escape` | Cancel current operation |
| `Ctrl+C` | Interrupt Claude |
| `Ctrl+O` | Toggle verbose mode (shows thinking as gray italic text) |
| `Shift+Tab` | Cycle permission modes: Normal → Auto-Accept → Plan Mode |
| `Option+T` / `Alt+T` | Toggle thinking on/off |
| `Ctrl+G` | Open plan in text editor |

| Command | Action |
|---|---|
| `/help` | Get help |
| `/init` | Initialize project and generate `CLAUDE.md` |
| `/resume` | Resume a previous session |
| `/rename` | Name the current session |
| `/model` | Change model or effort level |
| `/config` | Edit global settings |
| `/context` | View current context usage |
| `/agents` | View / create subagents |

---

### 5. Context Management — CLAUDE.md

`CLAUDE.md` files give Claude persistent, project-aware context. They load automatically
at the start of every session.

**Three-tier hierarchy:**

| Scope | Location | Use For |
|---|---|---|
| Global | `~/.claude/CLAUDE.md` | Personal preferences, coding style |
| Project | `./CLAUDE.md` | Tech stack, build commands, conventions |
| Local | `./.claude/CLAUDE.md` | Directory-specific rules (e.g., component naming) |

Files merge hierarchically: **global → project → local**. More specific files override broader ones.

**Best practices:**
- Write specific, actionable rules — not vague guidance
- Use `#` during a session to quickly save a memory to `CLAUDE.md`
- Include: tech stack, build/test commands, code conventions, project structure
- Keep it concise — large files eat into the context window

**@ Mentions for file references:**

```
@src/utils/auth.js               # Includes full file content in conversation
@src/components                  # Provides directory listing
@github:repos/owner/repo/issues  # Fetches MCP resources
@file1.js and @file2.js          # Multiple files in one message
```

File references automatically load the `CLAUDE.md` from that file's directory.

---

### 6. Plan Mode

Activated with `Shift+Tab` (cycle twice) or `claude --permission-mode plan`.

In Plan Mode, Claude enters a **read-only analysis state** — it explores the codebase
but makes no changes. It uses `AskUserQuestion` to gather requirements and clarify
goals before proposing a plan.

- Press `Ctrl+G` to open and edit the plan in your text editor

**When to use Plan Mode:**
- Multi-step implementations touching many files
- Exploring unfamiliar codebases before making changes
- Complex architectural decisions
- Iterative planning where you want to refine direction before execution

**Set Plan Mode as default:**

```json
// .claude/settings.json
{ "permissions": { "defaultMode": "plan" } }
```

---

### 7. Extended Thinking (Thinking Mode)

Enabled by default — Claude reasons through problems step-by-step before responding.

| Toggle | Action |
|---|---|
| `Ctrl+O` | Show/hide thinking (verbose mode — appears as gray italic text) |
| `Option+T` / `Alt+T` | Turn thinking on/off entirely |

**Model behaviour:**
- **Opus 4.6** — adaptive reasoning: dynamically allocates thinking budget based on
  effort level (`low` / `medium` / `high`)
- **Other models** — fixed budget up to 31,999 tokens

**Limit the thinking budget:**

```bash
export MAX_THINKING_TOKENS=10000
```

> **Note:** Phrases like "think", "think hard", "ultrathink" are just prompt words —
> they don't allocate extra tokens.

**Best for:** Complex architectural decisions, challenging bugs, multi-step planning,
evaluating tradeoffs.

---

### 8. Custom Commands (Slash Commands)

Store commands as Markdown files:

| Location | Scope |
|---|---|
| `.claude/commands/` | Project-level |
| `~/.claude/commands/` | Global |

The filename becomes the command: `review.md` → `/review`

**Key features:**
- **Arguments:** use `$ARGUMENTS` or `$1`, `$2` for positional args
- **File inclusion:** reference other files with `@file` syntax
- **Tool permissions:** declare `allowed-tools:` in frontmatter for pre-execution steps

**Example — code review command:**

```markdown
<!-- .claude/commands/review.md -->
Review the code in $ARGUMENTS for:
- Security vulnerabilities
- Performance issues
- Code style consistency
```

Usage: `/review src/auth.js`

**Commands vs Skills:**
- **Commands** = manually triggered with `/command_name`
- **Skills** = activate automatically when their description matches the task context
- Both can coexist: `.claude/commands/review.md` and `.claude/skills/review/SKILL.md` both create `/review`

---

### 9. MCP Server Integration

**Model Context Protocol (MCP)** is an open standard for connecting Claude to external
tools and data sources — databases, APIs, browsers, services.

**Add an MCP server:**

```bash
claude mcp add <name> <command> [args...]

# Example:
claude mcp add playwright npx @playwright/mcp@latest
```

**Common MCP servers:**

| Server | Capability |
|---|---|
| Playwright | Browser automation, UI testing |
| GitHub | Issues, PRs, repos |
| PostgreSQL | Database queries |
| Context7 | Library specifications |
| Slack | Team messaging |

**Important:**
- Each MCP server consumes context window — monitor with `/context`
- MCP servers do **not** inherit Claude's `Read`, `Write`, or `Bash` tools unless explicitly provided
- Use `@server:resource` syntax to reference MCP resources in conversation
- Configure in `.claude/settings.json` or `~/.claude/settings.json`

---

### 10. Hooks — Deterministic Automation

Hooks are shell commands that execute automatically at specific points in Claude's lifecycle.
Configured in `.claude/settings.json`.

**Two modes:**
- **Command** — run shell scripts (fast, predictable)
- **Prompt** — LLM decides what to run (flexible, context-aware)

**Seven event types:**

| Event | When it Fires |
|---|---|
| `PreToolUse` | Before Claude executes a tool |
| `PostToolUse` | After a tool completes |
| `UserPromptSubmit` | When user sends a message |
| `PermissionRequest` | When Claude requests permission |
| `Stop` | When Claude finishes responding |
| `SessionStart` | When a new session begins |
| `SessionEnd` | When a session ends |

**Practical use cases:**
- Auto-format code after every file edit (`PostToolUse` on `Write|Edit`)
- Block dangerous commands like `rm -rf` (`PreToolUse` on `Bash`)
- Run tests when test files change (`PostToolUse`)
- Type-check TypeScript after edits (`PostToolUse`)
- Block edits on `main` branch (`PreToolUse`)

**Example hook configuration:**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "prettier --write $FILE_PATH"
      }
    ]
  }
}
```

---

### 11. GitHub Integration

**Automated PR reviews:**
- Use GitHub Actions to trigger Claude Code on PR events
- Claude analyzes diffs, identifies issues, and posts review comments

**Useful commands:**

```bash
# Resume a session linked to a PR
claude --from-pr <number>

# Use Claude as a linter in CI
claude -p 'you are a linter...'

# Pipe build errors through Claude
cat build-error.txt | claude -p 'explain this error'
```

**Creating PRs:**
- Ask directly: *"create a pr for my changes"*
- Or use: `/commit-push-pr` skill (commits, pushes, and opens PR in one step)
- When `gh pr create` is used, the session is automatically linked to the PR

---

### 12. Subagents

Subagents are specialized AI personalities with **isolated context windows**.
They prevent "context poisoning" of the main session and can run in parallel.

**Configure in `.claude/agents/`:**

```yaml
name: security-auditor
description: Analyzes code for security vulnerabilities
tools: Read, Grep, Bash
model: sonnet  # Can use different models: sonnet, opus, haiku
```

**Benefits:**
- **Isolated context** — each agent has its own conversation, separate from the main session
- **Parallelizable** — multiple subagents can run concurrently
- **Specialized** — each agent has focused expertise and restricted tool access

View and create subagents with `/agents`.

---

### 13. Claude Code SDK — Programmatic Use

Use Claude Code in scripts and pipelines with **headless mode**:

```bash
# Basic headless call
claude -p "your prompt"

# Pipe data through Claude
cat data.txt | claude -p 'summarize this' > output.txt

# Structured JSON output
claude -p 'analyze code' --output-format json > analysis.json
```

**Output formats:** `text` | `json` | `stream-json`

**Use in `package.json` scripts:**

```json
"scripts": {
  "lint:claude": "claude -p 'lint the changes vs main...'"
}
```

---

### 14. Session Management

**Resuming conversations:**

```bash
claude --continue              # Resume most recent conversation in current directory
claude --resume                # Open session picker
claude --resume auth-refactor  # Resume by name
claude --from-pr 123           # Resume session linked to a PR
```

Use `/resume` inside a session to switch to a different conversation.

**Session picker shortcuts:**

| Key | Action |
|---|---|
| `↑` / `↓` | Navigate sessions |
| `→` / `←` | Expand / collapse grouped sessions |
| `Enter` | Select session |
| `P` | Preview session |
| `R` | Rename session |
| `/` | Search sessions |
| `A` | Toggle current dir / all projects |
| `B` | Filter by current git branch |

**Git Worktrees for parallel sessions:**

```bash
git worktree add ../feature-branch feature-branch
```

Run separate Claude Code instances in each worktree — changes in one don't affect others.
Useful for working on multiple features simultaneously without switching branches.

---

## Things to Explore Next

- [ ] Build a custom subagent for a specific domain (e.g., security auditing)
- [ ] Set up a `PostToolUse` hook to auto-run tests on file changes
- [ ] Try Plan Mode on a large refactor to see the analysis before committing
- [ ] Add an MCP server (e.g., Playwright or GitHub) and test `@server:resource` references
- [ ] Create a project-level `/review` slash command and use it in a real PR workflow
- [ ] Experiment with `--output-format stream-json` in a pipeline script

---

## Files

| File | Description |
|---|---|
| `NOTES.md` | This file — concept notes for all Module 1 topics |
