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
- [ ] Module 2 — Building with the Claude API
  - [x] Accessing Claude with the API
  - [ ] Prompt Evaluation
  - [ ] Prompt Engineering Techniques
  - [ ] Tools with Claude
  - [ ] Retrieval Augmented Generation
  - [ ] Features of Claude
  - [ ] Model Context Protocol
  - [ ] Anthropic Apps — Claude Code and Computer Use
  - [ ] Agents and Workflows
- [ ] Module 3 — Introduction to Model Context Protocol
- [ ] Module 4 — Model Context Protocol: Advanced Topics
- [ ] Module 5 — Introduction to Agent Skills
