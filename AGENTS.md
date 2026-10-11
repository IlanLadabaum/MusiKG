# AGENTS.md

Instructions for AI coding agents (Claude, Codex, Gemini, etc.) working in this repository.
This is the single source of truth for project-specific agent guidance — keep it up to date and model-agnostic.

## Required reading

Before doing any work in this repo, every agent **must** read, in order:

1. [`Coding_Agent_Skill.md`](Coding_Agent_Skill.md) — the developer's general working rules (planning docs, status markers, who decides what). Follow it on every task.

2. This file.

3. [`Plan/Global Plan.md`](Plan/Global%20Plan.md) — the top-level project plan, then whichever sub-plan it points to for the task at hand.

`Coding_Agent_Skill.md` is curated by the developer and is not project-specific. **Do not edit it** without explicit approval, and never add project-specific information to it — that belongs here or in `Plan/`.

## Project overview

**Music Graph Generator** — builds a graph of a person's music taste from their listening data, linking tracks to the people behind them (performers, session musicians, writers, producers) to surface hidden influences. Details in `Plan/Global Plan.md`.

- **Status:** planning

## Repository layout

```
.
├── AGENTS.md               # This file — project-specific agent instructions
├── CLAUDE.md               # Pointer to this file for Claude Code (do not edit)
├── Coding_Agent_Skill.md   # Developer's general agent rules (do not edit)
├── README.md               # Human-facing project overview
└── Plan/                   # Planning docs (see Coding_Agent_Skill.md)
    └── Global Plan.md      # Top-level plan; links to topic sub-plans
```

## Git workflow

- Default branch: `main`. Do work on feature branches (`feature/<short-name>`, `fix/<short-name>`).

- Write concise, imperative commit messages (e.g. "Add tempo extraction to parser").

- Only commit or push when asked. Never force-push `main`.

- Never commit secrets, API keys, or large data/audio files (see `.gitignore`).

## Agent guidelines

- Ask before making large architectural changes or deleting files.

- Prefer small, reviewable changes over sweeping rewrites.

- Keep model-specific instructions out of this file; it is shared by all agents.

## Maintaining this file

This file starts minimal and grows with the project. Plans, decisions, and status belong in `Plan/`, not here — this file holds only stable, repo-wide facts an agent needs on every task. Update it (and mention the change to the user) when:

- **The stack is chosen** (once [DECIDED] in `Plan/`): add the language/framework and key dependencies to *Project overview*.

- **Setup becomes non-trivial**: add a *Setup* section with exact environment/install steps.

- **Run/test/lint/build commands exist**: add a *Common commands* table. Only list commands that have been verified to work.

- **Conventions are settled**: add a *Coding conventions* section (formatter, linter, typing, docstring style, naming) and a *Testing* section (framework, test location, what must pass before work is complete).

- **The directory structure changes**: update *Repository layout* so new top-level directories are described (e.g. add `src/` when source code is first created there).

- **A recurring gotcha is found**: something that cost time and would trip up the next agent (environment quirks, fragile modules, non-obvious invariants) goes in a *Gotchas* section. One-off issues and task status do not.

Keep it short: remove sections or lines that become stale, and link to `Plan/` docs rather than duplicating their content.
