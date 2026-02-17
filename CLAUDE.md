# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Claude Code skill** called `long-task-agent` that enables multi-session execution of complex software projects exceeding a single context window. It implements a three-phase architecture (Brainstorming + Initializer + Worker sessions) with persistent state bridging via on-disk artifacts.

## Key Commands

### Initialize a new long-task project
```bash
python long-task-agent/scripts/init_project.py <project-name> --path <output-dir>
```

### Validate feature-list.json
```bash
python long-task-agent/scripts/validate_features.py feature-list.json
```

### Run tests
```bash
python long-task-agent/tests/test_validate_features.py
python long-task-agent/tests/test_init_project.py
```

### Shortcut commands
- `/long-task:init` — Initialize a new project
- `/long-task:work` — Start a Worker cycle
- `/long-task:status` — Check project progress

## Architecture

### Three-Phase Workflow

0. **Brainstorming & Design** (before initialization):
   - Explore requirements, clarify ambiguities with user
   - Propose 2-3 approaches with trade-offs
   - Get section-by-section design approval
   - Save design doc to `docs/plans/YYYY-MM-DD-<topic>-design.md`
   - **Hard gate**: no coding until design approved

1. **Initializer Session** (runs once):
   - Reads approved design document
   - Runs `init_project.py` to scaffold artifacts
   - Decomposes requirements into 10-200+ verifiable features in `feature-list.json`
   - Customizes `init.sh`/`init.ps1` for tech stack
   - Creates project skeleton + initial git commit

2. **Worker Session** (each context cycle):
   - Orient: read `task-progress.md`, `feature-list.json`, `git log`
   - Bootstrap: run init script, smoke test; optionally create git worktree for isolation
   - **Plan**: write step-by-step implementation plan before coding
   - TDD Red: write failing tests (unit tests + Chrome DevTools MCP for UI)
   - TDD Green: implement minimal code to pass (self-execute or subagent-driven)
   - TDD Refactor: clean up while keeping tests green
   - **Verify & Mark**: fresh evidence required — run tests, read output, then mark "passing"
   - **Code Review**: two-stage review (spec compliance → code quality)
   - Add Examples: create runnable examples in `examples/` for user-facing features
   - Persist: git commit, update `RELEASE_NOTES.md`, `task-progress.md`
   - **Finish Branch**: merge / push+PR / keep / discard (when using worktrees)
   - On errors: follow systematic debugging (never guess-and-fix)

### Critical Rules

- **Design before implementation**: Run brainstorming; no coding until design approved
- **Strict TDD**: Always Red→Green→Refactor; never write implementation before tests
- **Verification enforcement**: Never mark "passing" without fresh evidence (run tests, read output, confirm)
- **Code review after every feature**: Two-stage (spec compliance → code quality) before Persist
- **Systematic debugging**: Never guess-and-fix; always trace root cause first
- **One feature per cycle**: Prevents context exhaustion
- **JSON for feature list**: Models corrupt markdown more easily
- **Immutable verification_steps**: Never remove or edit once created
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
├── agents/
│   ├── code-reviewer.md            # Code reviewer agent definition
│   └── prompts/                    # Subagent prompt templates
│       ├── implementer-prompt.md
│       ├── spec-reviewer-prompt.md
│       └── code-quality-reviewer-prompt.md
├── commands/                       # User shortcut commands
│   ├── init.md                     # /long-task:init
│   ├── work.md                     # /long-task:work
│   └── status.md                   # /long-task:status
├── hooks/
│   ├── hooks.json                  # Session start hook config
│   └── session-start.sh            # Auto-inject context on session start
├── scripts/
│   ├── init_project.py             # Project scaffolding
│   └── validate_features.py        # Feature list validation
├── tests/
│   ├── test_validate_features.py   # Validator unit tests
│   └── test_init_project.py        # Scaffolding unit tests
└── references/
    ├── architecture.md             # Detailed architecture patterns
    ├── brainstorming.md            # Brainstorming & design phase process
    ├── plan-writing.md             # Step-by-step implementation planning
    ├── code-review.md              # Two-stage code review process
    ├── verification-enforcement.md # Verification iron law & evidence requirements
    ├── systematic-debugging.md     # Four-phase debugging process
    ├── subagent-development.md     # Subagent-driven development mode
    ├── worktree-isolation.md       # Git worktree isolation & branch finishing
    ├── testing-anti-patterns.md    # Common testing mistakes catalog
    └── roadmap.md                  # Future enhancements roadmap
```

## See Also

- [ReadMe.md](ReadMe.md) - Overview and design rationale
- [long-task-agent/references/architecture.md](long-task-agent/references/architecture.md) - Detailed TDD workflow, Chrome DevTools testing patterns, anti-patterns
- [long-task-agent/references/brainstorming.md](long-task-agent/references/brainstorming.md) - Brainstorming & design phase
- [long-task-agent/references/plan-writing.md](long-task-agent/references/plan-writing.md) - Implementation planning
- [long-task-agent/references/code-review.md](long-task-agent/references/code-review.md) - Code review process
- [long-task-agent/references/verification-enforcement.md](long-task-agent/references/verification-enforcement.md) - Verification enforcement
- [long-task-agent/references/systematic-debugging.md](long-task-agent/references/systematic-debugging.md) - Systematic debugging
- [long-task-agent/references/subagent-development.md](long-task-agent/references/subagent-development.md) - Subagent-driven development
- [long-task-agent/references/worktree-isolation.md](long-task-agent/references/worktree-isolation.md) - Worktree isolation & branch finishing
