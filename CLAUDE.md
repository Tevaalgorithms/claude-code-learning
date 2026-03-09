# Claude Code Learning — Project Context

This repo tracks my hands-on learning journey through the Anthropic Claude Code course.
It contains notebooks, notes, and experiments for each module.

## Project Structure

```
claude-code-learning/
├── module-03-claude-api/       # Module 3: Accessing Claude with the API
├── module-04-*/                # Add as course progresses
└── README.md
```

## Conventions

- One folder per module: `module-XX-short-name/`
- Notebook naming: `moduleXX_topic_name.ipynb`
- Notes file per module: `NOTES.md` — concept explanations alongside the notebook

## Environment

- Python virtual environment is in `~/Anthrophic/.venv`
- API key lives in `.env` — never commit this
- Primary model used: `claude-sonnet-4-0`

## Pushing Changes

```bash
git add .
git commit -m "module-XX: short description"
git push
```

## Course Progress

- [ ] Module 1 — Getting Started with Claude Code
- [ ] Module 2 — CLI Workflows & Automation
- [x] Module 3 — Accessing Claude with the API
- [ ] Module 4 — Agentic AI Patterns
- [ ] Module 5 — Advanced Use Cases
