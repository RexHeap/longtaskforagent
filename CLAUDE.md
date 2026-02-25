# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Claude Code skill plugin** called `long-task-agent` that enables multi-session execution of complex software projects exceeding a single context window. It implements a four-phase architecture (Requirements → Design → Initializer → Worker sessions) with persistent state bridging via on-disk artifacts.

The skill system follows the **superpowers architectural pattern**: 8 independent skills loaded on-demand via the `Skill` tool, with a bootstrap router (`using-long-task`) injected at session start via hook.

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
python long-task-agent/scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json
```

### Check required configurations
```bash
python long-task-agent/scripts/check_configs.py feature-list.json
python long-task-agent/scripts/check_configs.py feature-list.json --feature 3
```

### Check Chrome DevTools MCP availability (for UI features)
```bash
python long-task-agent/scripts/check_devtools.py feature-list.json
python long-task-agent/scripts/check_devtools.py feature-list.json --feature 3
```

### Run tests
```bash
python long-task-agent/tests/test_validate_features.py
python long-task-agent/tests/test_init_project.py
python long-task-agent/tests/test_check_configs.py
python long-task-agent/tests/test_validate_guide.py
python long-task-agent/tests/test_check_devtools.py
```

### Shortcut commands
- `/long-task:requirements` — Start requirements elicitation and SRS generation
- `/long-task:design` — Start design phase (requires approved SRS)
- `/long-task:init` — Initialize a project after design approval
- `/long-task:work` — Start a Worker cycle
- `/long-task:status` — Check project progress

## Architecture

### 8-Skill System

The skill system uses on-demand loading via the `Skill` tool. Only the bootstrap router is loaded at session start; other skills are loaded as needed.

#### Phase Skills (loaded one at a time based on project state)

| Skill | Phase | Trigger |
|-------|-------|---------|
| `using-long-task` | Bootstrap | Injected via SessionStart hook into every session |
| `long-task-requirements` | Phase 0a | No SRS, no design doc, no feature-list.json |
| `long-task-design` | Phase 0b | SRS exists, no design doc, no feature-list.json |
| `long-task-init` | Phase 1 | Design doc exists, no feature-list.json |
| `long-task-work` | Phase 2 | feature-list.json exists |

#### Discipline Skills (loaded by long-task-work as sub-skills)

| Skill | Purpose |
|-------|---------|
| `long-task-tdd` | TDD Red-Green-Refactor with Test Plan Review hard gate |
| `long-task-quality` | Coverage Gate + Mutation Gate + Verification enforcement |
| `long-task-review` | Two-stage Code Review (spec compliance → code quality) |

#### Skill Call Graph

```
using-long-task (router)
   ├─→ long-task-requirements ──→ long-task-design ──→ long-task-init ──→ long-task-work
   │                                                                         │
   └─→ long-task-work (if feature-list.json exists)
          ├─→ long-task-tdd (Steps 6-8)
          ├─→ long-task-quality (Step 9)
          └─→ long-task-review (Step 10)
```

### Four-Phase Workflow

0a. **Requirements** (`long-task-requirements`):
   - Structured elicitation aligned with ISO/IEC/IEEE 29148
   - Challenge each requirement against 8 quality attributes
   - Apply EARS templates, assign unique IDs, write Given/When/Then acceptance criteria
   - Anti-pattern detection (weasel words, compound requirements, design leakage)
   - Save SRS to `docs/plans/YYYY-MM-DD-<topic>-srs.md`
   - **Hard gate**: no design until SRS approved

0b. **Design** (`long-task-design`):
   - Takes approved SRS as input (WHAT → HOW)
   - Propose 2-3 approaches with trade-offs, evaluate against SRS constraints/NFRs
   - Get section-by-section design approval
   - Save design doc to `docs/plans/YYYY-MM-DD-<topic>-design.md`
   - **Hard gate**: no coding until design approved

1. **Initializer Session** (`long-task-init`):
   - Reads both SRS and design documents
   - Runs `init_project.py` to scaffold deterministic artifacts
   - LLM generates project-tailored `long-task-guide.md`
   - Decomposes SRS requirements into 10-200+ verifiable features in `feature-list.json`
   - Creates project skeleton + initial git commit

2. **Worker Session** (`long-task-work` orchestrator):
   - Orient → Bootstrap → Config Gate → DevTools Gate → Plan
   - **TDD** (`long-task-tdd`): Red → Test Plan Review → Green → Refactor
   - **Quality** (`long-task-quality`): Coverage Gate → Mutation Gate → Verify & Mark
   - **Review** (`long-task-review`): Spec Compliance → Code Quality
   - Add Examples → Persist → Continue

### Critical Rules

- **Config gate before planning**: Never plan or code when required configs are missing
- **Requirements before design**: Run requirements elicitation; no design until SRS approved
- **Design before implementation**: Run design phase; no coding until design approved
- **Strict TDD**: Always Red→Test Plan Review→Green→Coverage→Refactor→Mutation
- **Coverage gate after TDD Green**: Run coverage tool, verify line >= 90%, branch >= 80%
- **Mutation gate after TDD Refactor**: Run incremental mutation testing, verify score >= 80%
- **Verification enforcement**: Never mark "passing" without fresh evidence
- **Code review after every feature**: Two-stage (spec compliance → code quality)
- **Systematic debugging**: Never guess-and-fix; always trace root cause first
- **One feature per cycle**: Prevents context exhaustion
- **UI features require Chrome DevTools MCP testing**: Mark with `"ui": true`

### Generated Persistent Artifacts

| File | Phase | Purpose |
|------|-------|---------|
| `docs/plans/*-srs.md` | Requirements | Approved SRS — the WHAT (ISO/IEC/IEEE 29148 aligned) |
| `docs/plans/*-design.md` | Design | Approved design — the HOW |
| `feature-list.json` | Init | Structured task inventory with status; includes `constraints[]` and `assumptions[]` |
| `CLAUDE.md` | Init | Cross-session navigation index (appended by `init_project.py`) |
| `task-progress.md` | Init | Session-by-session progress log |
| `RELEASE_NOTES.md` | Init | Living release notes (Keep a Changelog format) |
| `examples/` | Worker | Runnable examples demonstrating completed features |
| `init.sh` / `init.ps1` | Init | Environment bootstrap (LLM-generated) |
| `long-task-guide.md` | Init | Worker session guide (LLM-generated, validated) |
| `docs/project-context.md` | Init | User personas and domain glossary (from SRS) |
| `docs/templates/srs-template.md` | — | Default SRS template (user-customizable) |
| `docs/templates/design-template.md` | — | Default design document template (user-customizable) |

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
  "constraints": ["Hard limit — one string per item"],
  "assumptions": ["Implicit belief — one string per item"],
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
  "dependencies": [],
  "ui": false,
  "ui_entry": "/optional-path"
}
```

## File Structure

```
long-task-agent/
├── skills/                            # 8 skills (on-demand loaded via Skill tool)
│   ├── using-long-task/SKILL.md       # Bootstrap router (injected via hook)
│   ├── long-task-requirements/SKILL.md # Phase 0a: Requirements & SRS (ISO 29148)
│   ├── long-task-design/SKILL.md      # Phase 0b: Design (takes SRS as input)
│   ├── long-task-init/SKILL.md        # Phase 1: Initialization (reads SRS + design)
│   ├── long-task-work/SKILL.md        # Phase 2: Worker orchestrator
│   ├── long-task-tdd/                 # TDD discipline
│   │   ├── SKILL.md
│   │   ├── testing-anti-patterns.md   # 14 anti-patterns catalog
│   │   └── prompts/
│   │       ├── implementer-prompt.md
│   │       └── test-plan-reviewer-prompt.md
│   ├── long-task-quality/             # Quality gates
│   │   ├── SKILL.md
│   │   └── coverage-recipes.md        # Multi-language tool setup
│   └── long-task-review/              # Code review
│       ├── SKILL.md
│       └── prompts/
│           ├── spec-reviewer-prompt.md
│           └── code-quality-reviewer-prompt.md
├── agents/
│   └── code-reviewer.md              # Code reviewer agent definition
├── docs/
│   └── templates/                     # Document templates (user-customizable)
│       ├── srs-template.md            # Default SRS template (ISO 29148)
│       └── design-template.md         # Default design document template
├── commands/                          # User shortcut commands
│   ├── requirements.md                # /long-task:requirements
│   ├── design.md                      # /long-task:design
│   ├── init.md                        # /long-task:init
│   ├── work.md                        # /long-task:work
│   └── status.md                      # /long-task:status
├── hooks/
│   ├── hooks.json                     # SessionStart hook config
│   ├── session-start                  # Inject using-long-task + phase detection
│   └── run-hook.cmd                   # Cross-platform polyglot wrapper
├── scripts/
│   ├── init_project.py                # Project scaffolding
│   ├── get_tool_commands.py           # Tech stack → CLI commands lookup
│   ├── validate_features.py           # Feature list validation
│   ├── validate_guide.py              # Guide structural validation
│   ├── check_configs.py               # Required config checking
│   └── check_devtools.py              # Chrome DevTools MCP checking
├── tests/
│   ├── test_validate_features.py
│   ├── test_init_project.py
│   ├── test_get_tool_commands.py
│   ├── test_check_configs.py
│   ├── test_validate_guide.py
│   └── test_check_devtools.py
└── references/                        # On-demand reference docs (Read when needed)
    ├── architecture.md                # Detailed architecture patterns
    ├── plan-writing.md                # Implementation plan structure
    ├── systematic-debugging.md        # Four-phase debugging process
    ├── subagent-development.md        # Subagent-driven development mode
    ├── worktree-isolation.md          # Git worktree isolation & branch finishing
    ├── ui-error-detection.md          # Three-layer UI error detection
    └── roadmap.md                     # Future enhancements
```

## See Also

- [ReadMe.md](ReadMe.md) - Overview and design rationale
- [long-task-agent/references/architecture.md](long-task-agent/references/architecture.md) - Detailed TDD workflow, Chrome DevTools testing patterns
- [long-task-agent/references/plan-writing.md](long-task-agent/references/plan-writing.md) - Implementation planning
- [long-task-agent/references/systematic-debugging.md](long-task-agent/references/systematic-debugging.md) - Systematic debugging
- [long-task-agent/references/subagent-development.md](long-task-agent/references/subagent-development.md) - Subagent-driven development
- [long-task-agent/references/worktree-isolation.md](long-task-agent/references/worktree-isolation.md) - Worktree isolation & branch finishing
- [long-task-agent/references/ui-error-detection.md](long-task-agent/references/ui-error-detection.md) - UI error detection specification


<!-- long-task-agent -->
## Long-Task Agent

This project uses a multi-session agent workflow with 8 skills loaded on-demand.
The `using-long-task` skill is injected at session start and routes to the correct phase.
Flow: Requirements (SRS) → Design → Init → Worker cycles.

Key files: `docs/plans/*-srs.md` (SRS), `docs/plans/*-design.md` (design), `feature-list.json` (task inventory), `task-progress.md` (session log), `RELEASE_NOTES.md` (changelog).
<!-- /long-task-agent -->
