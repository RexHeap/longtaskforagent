# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Claude Code skill** called `long-task-agent` that enables multi-session execution of complex software projects exceeding a single context window. It implements a three-phase architecture (Brainstorming + Initializer + Worker sessions) with persistent state bridging via on-disk artifacts.

## Key Commands

### Initialize a new long-task project
```bash
python long-task-agent/scripts/init_project.py <project-name> --path <output-dir>

# With language preset (auto-fills test/coverage/mutation tools):
python long-task-agent/scripts/init_project.py <project-name> --path <output-dir> --lang python

# With custom thresholds:
python long-task-agent/scripts/init_project.py <project-name> --path <output-dir> --lang java \
  --line-cov 85 --branch-cov 75 --mutation-score 70
```

### Validate feature-list.json
```bash
python long-task-agent/scripts/validate_features.py feature-list.json
```

### Validate LLM-generated guide
```bash
python long-task-agent/scripts/validate_guide.py long-task-guide.md
```

### Check required configurations
```bash
python long-task-agent/scripts/check_configs.py feature-list.json
python long-task-agent/scripts/check_configs.py feature-list.json --feature 3
```

### Run tests
```bash
python long-task-agent/tests/test_validate_features.py
python long-task-agent/tests/test_init_project.py
python long-task-agent/tests/test_check_configs.py
python long-task-agent/tests/test_validate_guide.py
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
   - Supports custom design template: specify a path or place template at `docs/templates/design-template.md`
   - **Hard gate**: no coding until design approved

1. **Initializer Session** (runs once):
   - Reads approved design document
   - Runs `init_project.py` to scaffold deterministic artifacts (`feature-list.json`, `task-progress.md`, `RELEASE_NOTES.md`, `examples/`, `docs/plans/`)
   - LLM generates project-tailored `long-task-guide.md` (validated by `validate_guide.py`)
   - LLM generates real, runnable `init.sh`/`init.ps1` based on tech stack
   - Decomposes requirements into 10-200+ verifiable features in `feature-list.json`
   - Creates project skeleton + initial git commit

2. **Worker Session** (each context cycle):
   - Orient: read `task-progress.md`, `feature-list.json`, `git log`
   - Bootstrap: run init script, smoke test; optionally create git worktree for isolation
   - **Config Gate**: check `required_configs` for target feature; block until resolved
   - **Plan**: write step-by-step implementation plan before coding
   - TDD Red: write failing tests (unit tests + Chrome DevTools MCP for UI)
   - TDD Green: implement minimal code to pass (self-execute or subagent-driven)
   - **Coverage Gate**: run coverage tool, verify line >= 90%, branch >= 80%
   - TDD Refactor: clean up while keeping tests green
   - **Mutation Gate**: run incremental mutation testing, verify score >= 80%
   - **Verify & Mark**: fresh evidence required — run tests, coverage, mutation; read output, then mark "passing"
   - **Code Review**: two-stage review (spec compliance → code quality)
   - Add Examples: create runnable examples in `examples/` for user-facing features
   - Persist: git commit, update `RELEASE_NOTES.md`, `task-progress.md`
   - **Finish Branch**: merge / push+PR / keep / discard (when using worktrees)
   - On errors: follow systematic debugging (never guess-and-fix)

### Critical Rules

- **Config gate before planning**: Never plan or code when required configs for the target feature are missing
- **Design before implementation**: Run brainstorming; no coding until design approved
- **Strict TDD**: Always Red→Green→Coverage→Refactor→Mutation; never write implementation before tests
- **Coverage gate after TDD Green**: Run coverage tool, verify line >= 90%, branch >= 80%
- **Mutation gate after TDD Refactor**: Run incremental mutation testing, verify score >= 80%
- **Multi-language support**: Coverage/mutation tools per language (Python, Java, TypeScript, C, C++) — see `references/coverage-and-mutation.md`
- **Verification enforcement**: Never mark "passing" without fresh evidence (run tests, coverage, mutation; read output, confirm)
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
| `init.sh` / `init.ps1` | Environment bootstrap (LLM-generated, project-specific) |
| `long-task-guide.md` | Worker session workflow guide (LLM-generated, validated by `validate_guide.py`) |

### Feature List Schema

`feature-list.json` root structure:
```json
{
  "project": "project-name",
  "created": "2025-01-15",
  "tech_stack": {
    "language": "python|java|typescript|c|cpp",
    "test_framework": "pytest|junit|vitest|gtest|...",
    "coverage_tool": "pytest-cov|jacoco|c8|gcov|...",
    "mutation_tool": "mutmut|pitest|stryker|mull|..."
  },
  "quality_gates": {
    "line_coverage_min": 90,
    "branch_coverage_min": 80,
    "mutation_score_min": 80
  },
  "required_configs": [
    {
      "name": "Config display name",
      "type": "env|file",
      "key": "ENV_VAR_NAME (for env type)",
      "path": "path/to/file (for file type)",
      "description": "What this config is for",
      "required_by": [1, 3],
      "check_hint": "How to set it up"
    }
  ],
  "features": [...]
}
```

Each feature in `features` array:
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
│   ├── init_project.py             # Project scaffolding (deterministic artifacts only)
│   ├── validate_features.py        # Feature list validation
│   ├── validate_guide.py           # LLM-generated guide structural validation
│   └── check_configs.py            # Required config checking
├── tests/
│   ├── test_validate_features.py   # Validator unit tests
│   ├── test_init_project.py        # Scaffolding unit tests
│   ├── test_check_configs.py       # Config checker unit tests
│   └── test_validate_guide.py      # Guide validator unit tests
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
    ├── coverage-and-mutation.md   # Coverage tracking & mutation testing (multi-language)
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
- [long-task-agent/references/coverage-and-mutation.md](long-task-agent/references/coverage-and-mutation.md) - Coverage tracking & mutation testing (multi-language)
