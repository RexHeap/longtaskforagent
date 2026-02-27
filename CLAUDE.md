# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Claude Code skill plugin** called `long-task-agent` that enables multi-session execution of complex software projects exceeding a single context window. It implements a six-phase architecture (Requirements → Design → Initializer → Worker → System Testing, with an Increment re-entry point) with persistent state bridging via on-disk artifacts.

The skill system follows the **superpowers architectural pattern**: 11 independent skills loaded on-demand via the `Skill` tool, with a bootstrap router (`using-long-task`) injected at session start via hook.

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
python long-task-agent/scripts/check_configs.py feature-list.json --feature 3 --dotenv .env
```

### Check Chrome DevTools MCP availability (for UI features)
```bash
python long-task-agent/scripts/check_devtools.py feature-list.json
python long-task-agent/scripts/check_devtools.py feature-list.json --feature 3
```

### Check system testing readiness
```bash
python long-task-agent/scripts/check_st_readiness.py feature-list.json
```

### Validate increment request
```bash
python long-task-agent/scripts/validate_increment_request.py increment-request.json
```

### Get tech-stack CLI commands (eliminates per-language lookup)
```bash
python long-task-agent/scripts/get_tool_commands.py feature-list.json
python long-task-agent/scripts/get_tool_commands.py feature-list.json --json
```

### Run tests
```bash
# Run all tests (from this repo's root)
python -m pytest tests/

# Run a single test file
python -m pytest tests/test_validate_features.py
python -m pytest tests/test_init_project.py
python -m pytest tests/test_check_configs.py
python -m pytest tests/test_validate_guide.py
python -m pytest tests/test_check_devtools.py
python -m pytest tests/test_check_st_readiness.py
python -m pytest tests/test_get_tool_commands.py
python -m pytest tests/test_validate_increment_request.py
```

> **Path note**: the `python long-task-agent/scripts/...` paths above are consumer-facing (run from the target project root after plugin install). When developing in this repo, replace `long-task-agent/` with `./` or omit it entirely.

### Shortcut commands
- `/long-task:requirements` — Start requirements elicitation and SRS generation
- `/long-task:ucd` — Start UCD style guide generation (requires approved SRS with UI features)
- `/long-task:design` — Start design phase (requires approved SRS + UCD if UI project)
- `/long-task:init` — Initialize a project after design approval
- `/long-task:work` — Start a Worker cycle
- `/long-task:st` — Run system testing (requires all features passing)
- `/long-task:increment` — Start incremental requirements development (requires existing project)
- `/long-task:status` — Check project progress

## Architecture

### 11-Skill System

The skill system uses on-demand loading via the `Skill` tool. Only the bootstrap router is loaded at session start; other skills are loaded as needed.

#### Phase Skills (loaded one at a time based on project state)

| Skill | Phase | Trigger |
|-------|-------|---------|
| `using-long-task` | Bootstrap | Injected via SessionStart hook into every session |
| `long-task-increment` | Phase 1.5 | increment-request.json exists (highest priority) |
| `long-task-requirements` | Phase 0a | No SRS, no design doc, no feature-list.json |
| `long-task-ucd` | Phase 0b | SRS exists, no UCD doc, no design doc, no feature-list.json |
| `long-task-design` | Phase 0c | SRS + UCD exist (or no UI features), no design doc, no feature-list.json |
| `long-task-init` | Phase 1 | Design doc exists, no feature-list.json |
| `long-task-work` | Phase 2 | feature-list.json exists, some active features failing |
| `long-task-st` | Phase 3 | feature-list.json exists, ALL active features passing |

#### Discipline Skills (loaded by long-task-work as sub-skills)

| Skill | Purpose |
|-------|---------|
| `long-task-tdd` | TDD Red-Green-Refactor with Test Plan Review hard gate |
| `long-task-quality` | Coverage Gate + Mutation Gate + Verification enforcement |
| `long-task-review` | Two-stage Code Review (spec compliance → code quality) |

#### Skill Call Graph

```
using-long-task (router)
   ├─→ long-task-requirements ──→ long-task-ucd ──→ long-task-design ──→ long-task-init ──→ long-task-work
   │                              (auto-skip if no UI)                                        │
   ├─→ long-task-increment (if increment-request.json exists — highest priority)
   │      └─→ updates SRS/Design/UCD in place, appends features to feature-list.json
   │          └─→ long-task-work (new failing features detected)
   │
   ├─→ long-task-work (if active features remain failing)
   │      ├─→ long-task-tdd (Steps 6-8)
   │      ├─→ long-task-quality (Step 9)
   │      └─→ long-task-review (Step 10, includes UCD compliance for ui:true features)
   │
   └─→ long-task-st (if ALL active features passing)
          └─→ long-task-work (if defects found → fix → return to ST)
```

### Seven-Phase Workflow

0a. **Requirements** (`long-task-requirements`):
   - Structured elicitation aligned with ISO/IEC/IEEE 29148
   - Challenge each requirement against 8 quality attributes
   - Apply EARS templates, assign unique IDs, write Given/When/Then acceptance criteria
   - Anti-pattern detection (weasel words, compound requirements, design leakage)
   - Save SRS to `docs/plans/YYYY-MM-DD-<topic>-srs.md`
   - **Hard gate**: no UCD/design until SRS approved

0b. **UCD Style Guide** (`long-task-ucd`):
   - Takes approved SRS as input; auto-skips to design if no UI features
   - Define visual style direction (2-3 options), style tokens (colors, typography, spacing)
   - Generate text-to-image prompts per component type and per page
   - Save UCD to `docs/plans/YYYY-MM-DD-<topic>-ucd.md`
   - **Hard gate**: no design until UCD approved (for UI projects)
   - Referenced by design (UI/UX section), worker (frontend features), and review (UCD compliance)

0c. **Design** (`long-task-design`):
   - Takes approved SRS + UCD as input (WHAT + LOOK → HOW)
   - Propose 2-3 approaches with trade-offs, evaluate against SRS constraints/NFRs
   - Per-feature detailed design with Mermaid diagrams (class, sequence, flow)
   - Third-party dependency versions with compatibility verification
   - Development plan with milestones, task decomposition, priority ordering
   - Get section-by-section design approval
   - Save design doc to `docs/plans/YYYY-MM-DD-<topic>-design.md`
   - **Hard gate**: no coding until design approved

1.5. **Increment** (`long-task-increment`):
   - Triggered by `increment-request.json` signal file (highest routing priority)
   - Collects new/modified/deprecated requirements with EARS templates
   - Impact analysis against existing features (user-approved)
   - Updates SRS, Design, UCD documents **in place** (git tracks history)
   - Appends new features to `feature-list.json` with `wave` metadata
   - Resets modified features to `"failing"`, marks deprecated features with `"deprecated": true`
   - Deletes signal file on completion; router auto-detects failing features → Worker

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
   - Add Examples → Persist → Continue (chains to ST when all features pass)

3. **System Testing** (`long-task-st`):
   - ST Readiness Gate → ST Plan (RTM) → Regression → Integration → E2E → NFR Verification
   - Compatibility → Exploratory → Defect Triage → ST Report → Verdict (Go/No-Go)
   - If Critical/Major defects found → loops back to Worker for fixes
   - Aligned with IEEE 829 and ISTQB best practices

### Critical Rules

- **Config gate before planning**: Never plan or code when required configs are missing; load `.env` first, prompt user for missing values via text input, save to `.env`
- **Requirements before UCD/design**: Run requirements elicitation; no UCD/design until SRS approved
- **UCD before design (UI projects)**: Run UCD style guide generation; no design until UCD approved (auto-skips for non-UI projects)
- **Design before implementation**: Run design phase; no coding until design approved
- **Strict TDD**: Always Red→Test Plan Review→Green→Coverage→Refactor→Mutation
- **Coverage gate after TDD Green**: Run coverage tool, verify line >= 90%, branch >= 80%
- **Mutation gate after TDD Refactor**: Run incremental mutation testing, verify score >= 80%
- **Verification enforcement**: Never mark "passing" without fresh evidence
- **Code review after every feature**: Two-stage (spec + design + UCD compliance → code quality)
- **UCD compliance for frontend features**: UI features must pass UCD style token checks (U1-U4) during review
- **Systematic debugging**: Never guess-and-fix; always trace root cause first
- **One feature per cycle**: Prevents context exhaustion
- **UI features require Chrome DevTools MCP testing**: Mark with `"ui": true`
- **System testing before release**: When all features pass, run ST phase (regression, integration, E2E, NFR, exploratory); no release without Go verdict
- **Incremental changes via increment skill only**: Never manually edit feature-list.json to add/modify/deprecate features; use `/long-task:increment` for audited, tracked changes
- **verification_steps immutable in Worker**: Only the increment skill can update verification_steps; Worker must use `/long-task:increment` for requirement changes
- **Deprecated features excluded**: Worker skips deprecated features; ST readiness ignores them; routing counts only active features

### Generated Persistent Artifacts

| File | Phase | Purpose |
|------|-------|---------|
| `docs/plans/*-srs.md` | Requirements | Approved SRS — the WHAT (ISO/IEC/IEEE 29148 aligned) |
| `docs/plans/*-ucd.md` | UCD | Approved UCD style guide — the LOOK (UI projects only; text-to-image prompts, style tokens) |
| `docs/plans/*-design.md` | Design | Approved design — the HOW |
| `increment-request.json` | Increment | Signal file triggering incremental requirements (deleted after processing) |
| `feature-list.json` | Init | Structured task inventory with status; includes `constraints[]`, `assumptions[]`, `waves[]` |
| `CLAUDE.md` | Init | Cross-session navigation index (appended by `init_project.py`) |
| `task-progress.md` | Init | Session-by-session progress log |
| `RELEASE_NOTES.md` | Init | Living release notes (Keep a Changelog format) |
| `examples/` | Worker | Runnable examples demonstrating completed features |
| `init.sh` / `init.ps1` | Init | Environment bootstrap (LLM-generated) |
| `long-task-guide.md` | Init | Worker session guide (LLM-generated, validated) |
| `docs/project-context.md` | Init | User personas and domain glossary (from SRS) |
| `.env.example` | Init | Template for required env configs (safe to commit; `.env` has secrets) |
| `docs/plans/*-st-plan.md` | ST | System testing plan with Requirements Traceability Matrix |
| `docs/plans/*-st-report.md` | ST | System testing report with Go/No-Go verdict |
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
  "waves": [
    {
      "id": 0,
      "date": "2025-01-15",
      "description": "Initial release"
    }
  ],
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
  "wave": 0,
  "category": "core",
  "title": "Feature title",
  "description": "What it does",
  "priority": "high|medium|low",
  "status": "failing|passing",
  "verification_steps": ["step 1", "step 2"],
  "dependencies": [],
  "ui": false,
  "ui_entry": "/optional-path",
  "deprecated": false,
  "deprecated_reason": null,
  "supersedes": null
}
```

Increment-specific fields:
- `waves[]` (root): Tracks each increment batch — `id` (0=initial), `date`, `description`
- `wave` (feature): Which wave introduced/last modified this feature (default 0)
- `deprecated` (feature): If `true`, excluded from Worker/ST/routing counts
- `deprecated_reason` (feature): Required when `deprecated=true`
- `supersedes` (feature): ID of the deprecated feature this one replaces (optional)

## File Structure

```
long-task-agent/
├── skills/                            # 11 skills (on-demand loaded via Skill tool)
│   ├── using-long-task/               # Bootstrap router (injected via hook)
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── architecture.md        # Detailed architecture patterns
│   │       └── roadmap.md             # Future enhancements
│   ├── long-task-requirements/SKILL.md # Phase 0a: Requirements & SRS (ISO 29148)
│   ├── long-task-ucd/SKILL.md         # Phase 0b: UCD style guide (text-to-image prompts)
│   ├── long-task-increment/SKILL.md    # Phase 1.5: Incremental requirements development
│   ├── long-task-design/SKILL.md      # Phase 0c: Design (takes SRS + UCD as input)
│   ├── long-task-init/                # Phase 1: Initialization (reads SRS + UCD + design)
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── init-script-recipes.md # Environment bootstrap templates (conda, venv, nvm, etc.)
│   ├── long-task-work/               # Phase 2: Worker orchestrator
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── plan-writing.md        # Implementation plan structure
│   │       ├── systematic-debugging.md # Four-phase debugging process
│   │       ├── subagent-development.md # Subagent-driven development mode
│   │       └── worktree-isolation.md  # Git worktree isolation & branch finishing
│   ├── long-task-st/                  # Phase 3: System Testing (IEEE 829)
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   └── st-recipes.md          # Per-language ST tool recipes
│   │   └── prompts/
│   │       └── st-reviewer-prompt.md  # ST report review subagent
│   ├── long-task-tdd/                 # TDD discipline
│   │   ├── SKILL.md
│   │   ├── testing-anti-patterns.md   # 14 anti-patterns catalog
│   │   ├── references/
│   │   │   └── ui-error-detection.md  # Three-layer UI error detection
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
│   ├── ucd.md                         # /long-task:ucd
│   ├── design.md                      # /long-task:design
│   ├── init.md                        # /long-task:init
│   ├── work.md                        # /long-task:work
│   ├── st.md                          # /long-task:st
│   ├── increment.md                   # /long-task:increment
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
│   ├── check_devtools.py              # Chrome DevTools MCP checking
│   ├── check_st_readiness.py          # System testing readiness checking
│   └── validate_increment_request.py  # Increment request signal validation
├── tests/
│   ├── test_validate_features.py
│   ├── test_init_project.py
│   ├── test_get_tool_commands.py
│   ├── test_check_configs.py
│   ├── test_validate_guide.py
│   ├── test_check_devtools.py
│   ├── test_check_st_readiness.py
│   └── test_validate_increment_request.py
```

## See Also

- [ReadMe.md](ReadMe.md) - Overview and design rationale
- [skills/using-long-task/references/architecture.md](skills/using-long-task/references/architecture.md) - Detailed TDD workflow, Chrome DevTools testing patterns
- [skills/using-long-task/references/roadmap.md](skills/using-long-task/references/roadmap.md) - Future enhancements
- [skills/long-task-work/references/plan-writing.md](skills/long-task-work/references/plan-writing.md) - Implementation planning
- [skills/long-task-work/references/systematic-debugging.md](skills/long-task-work/references/systematic-debugging.md) - Systematic debugging
- [skills/long-task-work/references/subagent-development.md](skills/long-task-work/references/subagent-development.md) - Subagent-driven development
- [skills/long-task-work/references/worktree-isolation.md](skills/long-task-work/references/worktree-isolation.md) - Worktree isolation & branch finishing
- [skills/long-task-tdd/references/ui-error-detection.md](skills/long-task-tdd/references/ui-error-detection.md) - UI error detection specification
- [skills/long-task-st/references/st-recipes.md](skills/long-task-st/references/st-recipes.md) - System testing recipes per language


<!-- long-task-agent -->
## Long-Task Agent

This project uses a multi-session agent workflow with 11 skills loaded on-demand.
The `using-long-task` skill is injected at session start and routes to the correct phase.
Flow: Requirements (SRS) → UCD (UI projects) → Design → Init → Worker cycles → System Testing.
Incremental development: place `increment-request.json` → Increment skill updates SRS/Design/UCD in place → new features appended → Worker cycles → ST.

Key files: `docs/plans/*-srs.md` (SRS), `docs/plans/*-ucd.md` (UCD style guide), `docs/plans/*-design.md` (design), `feature-list.json` (task inventory), `task-progress.md` (session log), `RELEASE_NOTES.md` (changelog), `docs/plans/*-st-report.md` (ST report), `increment-request.json` (increment signal).
<!-- /long-task-agent -->
