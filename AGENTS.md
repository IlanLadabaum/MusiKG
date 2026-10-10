# AGENTS.md

Instructions for AI coding agents (Claude, Codex, Gemini, etc.) working in this repository.
This is the single source of truth for agent guidance — keep it up to date and model-agnostic.

## Project overview

**Music Graph Generator** — _TODO: one or two sentences on what this project does and who it's for._

- **Status:** early development
- **Primary language / stack:** _TODO (e.g. Python 3.12, TypeScript/React)_
- **Key dependencies:** _TODO_

## Repository layout

```
.
├── AGENTS.md        # This file — agent instructions
├── README.md        # Human-facing project overview
├── Code/            # Source code
└── docs/            # Design notes, specs, references
```

_Update this tree as the structure evolves._

## Setup

```bash
# TODO: environment setup, e.g.
# python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

## Common commands

| Task         | Command |
|--------------|---------|
| Run          | _TODO_  |
| Test         | _TODO_  |
| Lint/format  | _TODO_  |
| Build        | _TODO_  |

## Coding conventions

- Match the style, naming, and comment density of surrounding code.
- Keep functions small and focused; prefer clear names over comments.
- Don't add new dependencies without noting why in the PR/commit message.
- _TODO: formatter, linter, type-checking rules, docstring style._

## Testing

- Add or update tests alongside any behavior change.
- Run the test suite before declaring work complete; report failures honestly.
- _TODO: test framework and location of tests._

## Git workflow

- Default branch: `main`. Do work on feature branches (`feature/<short-name>`, `fix/<short-name>`).
- Write concise, imperative commit messages (e.g. "Add tempo extraction to parser").
- Only commit or push when asked. Never force-push `main`.
- Never commit secrets, API keys, or large data/audio files (see `.gitignore`).

## Agent guidelines

- Read this file and `README.md` before making changes.
- Ask before making large architectural changes or deleting files.
- Prefer small, reviewable changes over sweeping rewrites.
- If you learn something non-obvious about the project (gotchas, conventions, decisions),
  propose an addition to this file.
- Keep model-specific instructions out of this file; it is shared by all agents.

## Notes & decisions

_Record important design decisions, known issues, and gotchas here._
