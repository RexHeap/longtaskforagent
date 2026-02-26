---
name: long-task-init
description: "Use when design doc exists but feature-list.json not yet created - scaffold project artifacts and decompose requirements into features"
---

# Initialize Long-Task Project

Run once after both SRS and design are approved. Scaffolds all persistent artifacts, decomposes requirements into verifiable features, and prepares the project for iterative Worker cycles.

**Announce at start:** "I'm using the long-task-init skill to scaffold the project."

## Input Documents

This skill reads from **two** approved documents:

| Document | Location | Provides |
|----------|----------|----------|
| **SRS** | `docs/plans/*-srs.md` | Functional requirements (FR-xxx), NFRs (NFR-xxx), constraints (CON-xxx), assumptions (ASM-xxx), interface requirements (IFR-xxx), glossary, user personas, acceptance criteria |
| **Design** | `docs/plans/*-design.md` | Tech stack, architecture, data model, API design, testing strategy |

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

1. **Read the approved SRS and design documents** from `docs/plans/`
   - SRS: `docs/plans/*-srs.md` — for requirements, constraints, assumptions, NFRs, glossary, personas
   - Design: `docs/plans/*-design.md` — for tech stack, architecture decisions
2. **Run `scripts/init_project.py`** to scaffold deterministic artifacts:
   ```bash
   python scripts/init_project.py <project-name> --path . --lang <language>
   ```
   - `<project-name>` — from the SRS title
   - `<language>` — one of `python|java|typescript|c|cpp` from the design doc tech stack
   - Use `--line-cov`, `--branch-cov`, `--mutation-score` to override thresholds (defaults: 90/80/80)
   - Creates: `feature-list.json`, `CLAUDE.md` (appended), `task-progress.md`, `RELEASE_NOTES.md`, `examples/`, `docs/plans/`
   - Auto-copies helper scripts (`validate_features.py`, `check_configs.py`, `check_devtools.py`, `validate_guide.py`, `get_tool_commands.py`) into project `scripts/`
3. **Verify `tech_stack` and `quality_gates`** in `feature-list.json`:
   - Confirm `language`, `test_framework`, `coverage_tool`, `mutation_tool` match the design doc
   - Adjust `quality_gates` thresholds if needed (defaults: line 90%, branch 80%, mutation 80%)
   - Verify tool commands resolve correctly:
     ```bash
     python scripts/get_tool_commands.py feature-list.json
     ```
4. **Generate `long-task-guide.md`** — Create a project-tailored Worker session guide:
   - Read these files for reference:
     - `skills/long-task-work/SKILL.md` — Worker workflow
     - `skills/long-task-quality/SKILL.md` — verification enforcement
     - `skills/long-task-quality/coverage-recipes.md` — coverage/mutation tool setup
     - `skills/using-long-task/references/architecture.md` — TDD workflow details
   - Include ONLY the project's language-specific coverage/mutation commands (get from `python scripts/get_tool_commands.py feature-list.json`)
   - Include Chrome DevTools MCP testing section ONLY if the project has UI features (`"ui": true`)
   - **Must include all required sections**: Orient, Bootstrap, Config Gate, TDD Red, TDD Green, Coverage Gate, TDD Refactor, Mutation Gate, Verification Enforcement, Code Review, Examples, Persist, Critical Rules
   - Validate:
     ```bash
     python scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json
     ```
5. **Generate `init.sh` / `init.ps1`** — Create real, runnable bootstrap scripts:
   - Read `references/init-script-recipes.md` (in the long-task-init skill directory) for per-tool templates and best practices
   - **Detect environment manager** from design doc tech stack and project constraints:
     - Python: miniconda/conda/mamba, venv, poetry, pipenv, uv, pyenv
     - Node.js: nvm, fnm, volta, corepack
     - Java: sdkman, jenv
     - General: devcontainer, docker, nix
   - **Must handle**: env creation, activation, dependency install, tool version verification
   - **Must be idempotent** — safe to re-run without breaking an existing environment
   - **Must be cross-platform** — `init.sh` for Unix/macOS, `init.ps1` for Windows
   - **Must include**: error handling, version checks, clear success/failure output
   - Actual dependency installation commands (not commented stubs)
   - Service startup commands if needed
   - Must be immediately executable after `git clone`
6. **Populate SRS fields in `feature-list.json`** — from the **SRS document**:
   - `constraints[]` — copy CON-xxx items from SRS "Constraints" section; each a concise string
   - `assumptions[]` — copy ASM-xxx items from SRS "Assumptions & Dependencies" section; each a concise string
   - NFR-xxx rows → create `category: "non-functional"` features with measurable `verification_steps`; coverage/mutation gates do not apply to NFR features
7. **Generate `docs/project-context.md`** — from the **SRS document**:
   - Extract "Stakeholders & User Personas" table
   - Extract "Glossary & Definitions" table
   - Omit sections that are "None identified" or "[Not applicable]"
8. **Decompose requirements into features** — from the **SRS document** and **design document's Development Plan** (section 11), populate `feature-list.json` `features[]`:
   - Each FR-xxx → one or more features with `id`, `category`, `title`, `description`, `priority`, `status` (always `"failing"`), `verification_steps`, `dependencies`
   - `verification_steps` should trace to SRS acceptance criteria (Given/When/Then)
   - For UI features: set `"ui": true`, optionally `"ui_entry": "/path"`; include `[devtools]`-prefixed verification steps
   - Aim for 10-200+ features; each independently verifiable and completable in one session
   - **Priority ordering**: follow the design document's Task Decomposition table (section 11.2) — P0/P1/P2/P3 maps to high/high/medium/low
   - **Dependency chain**: follow the design document's Dependency Chain diagram (section 11.3) to populate each feature's `dependencies[]`
   - **Milestone mapping**: group features by the design document's milestones for logical ordering
9. **Populate `required_configs`** — from the **SRS document** (IFR-xxx interface requirements) and design doc:
   - API keys, service URLs → type `env`
   - Config files, certificates → type `file`
   - Link each to features via `required_by`; provide `check_hint` with setup instructions
10. **Validate**:
    ```bash
    python scripts/validate_features.py feature-list.json
    ```
11. **Scaffold project skeleton** (dirs, configs, dependency manifests) — based on **design doc** architecture
12. **Git init + initial commit**
13. **Run init script**, verify environment works
14. **Update `task-progress.md`** with Session 0 entry (include SRS + design doc references)
15. **Begin first Worker cycle** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-work`

## Feature List Schema

Root structure:
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
      "name": "Display name",
      "type": "env|file",
      "key": "ENV_VAR (for env type)",
      "path": "path/to/file (for file type)",
      "description": "What this config is for",
      "required_by": [1, 3],
      "check_hint": "How to set it up"
    }
  ],
  "features": [...]
}
```

Each feature:
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

## Generated Persistent Artifacts

| File | Purpose |
|------|---------|
| `feature-list.json` | Structured task inventory with status |
| `CLAUDE.md` | Cross-session navigation index (appended) |
| `task-progress.md` | Session-by-session progress log |
| `RELEASE_NOTES.md` | Living release notes (Keep a Changelog format) |
| `examples/` | Runnable examples directory |
| `init.sh` / `init.ps1` | Environment bootstrap (LLM-generated) |
| `long-task-guide.md` | Worker session guide (LLM-generated, validated) |
| `docs/project-context.md` | User personas and domain glossary |

## Integration

**Called by:** long-task-design (Step 6) or using-long-task (when design doc exists, no feature-list.json)
**Reads:** `docs/plans/*-srs.md` (requirements) + `docs/plans/*-design.md` (architecture)
**Chains to:** long-task-work (after initialization complete)
**Produces:** feature-list.json + all scaffolded artifacts listed above
