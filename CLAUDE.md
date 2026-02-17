# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Claude Code skill** called `long-task-agent` that enables multi-session execution of complex software projects exceeding a single context window. It implements a two-phase architecture (Initializer + Worker sessions) with persistent state bridging via on-disk artifacts.

## Key Commands

### Initialize a new long-task project
```bash
python long-task-agent/scripts/init_project.py <project-name> --path <output-dir>
```

### Validate feature-list.json
```bash
python long-task-agent/scripts/validate_features.py feature-list.json
```

## Architecture

### Two-Phase Workflow

1. **Initializer Session** (runs once):
   - Reads requirement doc + design doc
   - Runs `init_project.py` to scaffold artifacts
   - Decomposes requirements into 10-200+ verifiable features in `feature-list.json`
   - Customizes `init.sh`/`init.ps1` for tech stack
   - Creates project skeleton + initial git commit

2. **Worker Session** (each context cycle):
   - Orient: read `task-progress.md`, `feature-list.json`, `git log`
   - Bootstrap: run init script, smoke test
   - TDD Red: write failing tests (unit tests + Chrome DevTools MCP for UI)
   - TDD Green: implement minimal code to pass
   - TDD Refactor: clean up while keeping tests green
   - Add Examples: create runnable examples in `examples/` for user-facing features
   - Persist: git commit, update `RELEASE_NOTES.md`, `task-progress.md`

### Critical Rules

- **Strict TDD**: Always Red→Green→Refactor; never write implementation before tests
- **One feature per cycle**: Prevents context exhaustion
- **JSON for feature list**: Models corrupt markdown more easily
- **Immutable verification_steps**: Never remove or edit once created
- **No passing without testing**: Run actual tests (UT + functional) before marking `"passing"`
- **UI features require Chrome DevTools MCP testing**: Use `take_snapshot`, `click`, `fill`, `take_screenshot`
- **Update RELEASE_NOTES.md after every git commit**: Keep a Changelog format

### Generated Persistent Artifacts

| File | Purpose |
|------|---------|
| `feature-list.json` | Structured task inventory with status (`failing`/`passing`) |
| `task-progress.md` | Session-by-session progress log |
| `RELEASE_NOTES.md` | Living release notes (Keep a Changelog format) |
| `examples/` | Runnable examples demonstrating completed features |
| `init.sh` / `init.ps1` | Deterministic environment bootstrap |
| `long-task-guide.md` | Worker session workflow guide |

### Feature Schema

Each feature in `feature-list.json`:
```json
{
  "id": 1,
  "category": "core",
  "title": "Feature title",
  "description": "What it does",
  "priority": "high|medium|low",
  "status": "failing|passing",
  "verification_steps": ["step 1", "step 2"],
  "dependencies": []
}
```

## File Structure

```
long-task-agent/
├── SKILL.md                        # Skill definition (entry point)
├── scripts/
│   ├── init_project.py             # Project scaffolding
│   └── validate_features.py        # Feature list validation
└── references/
    └── architecture.md             # Detailed architecture patterns
```

## See Also

- [ReadMe.md](ReadMe.md) - Overview and design rationale
- [long-task-agent/references/architecture.md](long-task-agent/references/architecture.md) - Detailed TDD workflow, Chrome DevTools testing patterns, anti-patterns
