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
6. **Generate `start.sh` / `start.ps1` and `cleanup.sh` / `cleanup.ps1`** — Create runtime service lifecycle scripts:
   - Read `references/start-cleanup-recipes.md` (in the long-task-init skill directory) for per-service templates and best practices
   - **Detect all runtime services** from design doc (dev servers, databases, caches, queues, message brokers)
   - **Detect build/compile requirements** from tech stack (TypeScript→tsc, Java→mvn/gradle, C/C++→cmake/make, Go→go build, Rust→cargo build)
   - **Determine startup order**: build/compile → databases/caches → backend → frontend
   - **Must include**: build step (if compiled language; explicit skip comment for interpreted), proxy detection (HTTP_PROXY/HTTPS_PROXY/NO_PROXY with localhost always added), health checks per service (port or HTTP polling), retry logic (up to 3 attempts with backoff), PID management (`.run/` directory), graceful failure handling (record to `task-progress.md`, print manual commands, exit non-zero)
   - **Build failure = hard stop** — if compilation fails, no services should start; report the build error clearly
   - **Must be idempotent** — re-running when services already running should detect and skip
   - **Must be cross-platform** — `start.sh`/`cleanup.sh` for Unix/macOS, `start.ps1`/`cleanup.ps1` for Windows
   - Add `.run/` to `.gitignore` (PID files and service logs — not committed)
   - If project is CLI/library only (no runtime services), generate minimal scripts that print "No services to start" and exit 0
   - If project has `"ui": true` features, start script MUST ensure the frontend dev server is running and health-checked — this is the prerequisite for Chrome DevTools MCP testing
   - Validate:
     ```bash
     python scripts/validate_start_cleanup.py start.sh cleanup.sh
     ```
7. **Generate `test.sh` / `test.ps1` and `mutate.sh` / `mutate.ps1`** — Create test runner and mutation testing wrapper scripts:
   - Read `references/test-mutation-recipes.md` (in the long-task-init skill directory) for per-tech-stack templates and best practices
   - **test.sh / test.ps1**: Wrapper for running unit tests and coverage
     - Modes: `./test.sh` (full test suite), `./test.sh --coverage` (with coverage report)
     - Must: load `.env`, activate environment (venv/conda/nvm/sdkman), check tool availability (`command -v` / `Get-Command`), parse output for structured results
     - Exit codes: `0` = all tests pass (coverage above threshold if `--coverage`), `1` = test failures or coverage below threshold, `2` = tool not found / environment error
   - **mutate.sh / mutate.ps1**: Wrapper for running mutation testing
     - Modes: `./mutate.sh --incremental <files>` (changed files only), `./mutate.sh --full` (entire codebase)
     - Must: load `.env`, activate environment, check mutation tool availability, parse output for mutation score
     - Exit codes: `0` = mutation score above threshold, `1` = score below threshold, `2` = tool not found / environment error
   - **Must be cross-platform** — `test.sh`/`mutate.sh` for Unix/macOS, `test.ps1`/`mutate.ps1` for Windows
   - **Must be idempotent** — safe to re-run without side effects
   - **Graceful failure**: if tool is missing or environment broken, print clear diagnostic and manual fix instructions; record to `task-progress.md`; never silently skip
   - If project has no tests configured (CLI/library only), generate minimal scripts that print "No tests configured" and exit 0
   - Validate:
     ```bash
     python scripts/validate_test_mutation.py test.sh mutate.sh
     ```
8. **Populate SRS fields in `feature-list.json`** — from the **SRS document**:
   - `constraints[]` — copy CON-xxx items from SRS "Constraints" section; each a concise string
   - `assumptions[]` — copy ASM-xxx items from SRS "Assumptions & Dependencies" section; each a concise string
   - NFR-xxx rows → create `category: "non-functional"` features with measurable `verification_steps`; coverage/mutation gates do not apply to NFR features
9. **Decompose requirements into features** — from the **SRS document** and **design document's Development Plan** (section 11), populate `feature-list.json` `features[]`:
   - Each FR-xxx → one or more features with `id`, `category`, `title`, `description`, `priority`, `status` (always `"failing"`), `verification_steps`, `dependencies`
   - `verification_steps` should trace to SRS acceptance criteria (Given/When/Then)
   - For UI features: set `"ui": true`, optionally `"ui_entry": "/path"`; include `[devtools]`-prefixed verification steps
   - **Verification steps quality rules** (drives downstream ST case and TDD quality):
     - Each step MUST be a behavioral scenario with Given/When/Then structure, not a simple assertion
     - BAD: `"Login page displays correctly"` → no action, no assertion
     - GOOD: `"[devtools] Navigate /login → EXPECT: email input, password input, 'Sign In' button; fill valid creds → click Sign In → EXPECT: redirect to /dashboard, user name in header; REJECT: console errors, broken images"`
     - BAD: `"API returns 200 on valid input"` → this is an assertion, not a scenario
     - GOOD: `"Given a registered user, when POST /api/orders with valid payload, then response 201 with order ID; and GET /api/orders/{id} returns the created order with correct fields"`
     - For `"ui": true` features: every `[devtools]` step MUST describe a multi-step interaction chain (navigate → interact → verify → interact → verify)
     - For features with backend dependencies: at least one step MUST verify real data flow across the dependency boundary
     - **Minimum complexity**: each feature SHOULD have ≥ 1 verification_step with 3+ chained actions
   - **Backend-before-frontend dependency rule**: Frontend features (`"ui": true`) MUST list their backend API dependency features in `dependencies[]`. This ensures the Worker's dependency satisfaction check naturally develops backend APIs before frontend pages that consume them.
   - Aim for 10-200+ features; each independently verifiable and completable in one session
   - **Priority ordering**: follow the design document's Task Decomposition table (section 11.2) — P0/P1/P2/P3 maps to high/high/medium/low
   - **Dependency chain**: follow the design document's Dependency Chain diagram (section 11.3) to populate each feature's `dependencies[]`
   - **Milestone mapping**: group features by the design document's milestones for logical ordering
10. **Populate `required_configs`** — from the **SRS document** (IFR-xxx interface requirements) and design doc:
   - API keys, service URLs → type `env`
   - Config files, certificates → type `file`
   - Link each to features via `required_by`; provide `check_hint` with setup instructions
11. **Generate `.env.example`** — from `required_configs`:
   - For each `env`-type config, write a commented template line:
     ```
     # <name> — <description>
     # Hint: <check_hint>
     # Required by features: <required_by ids>
     <KEY>=
     ```
   - Add `.env` to `.gitignore` (`.env.example` is safe to commit; `.env` contains secrets)
   - This template helps users know which values to fill in; the Worker Config Gate will prompt for missing values and store them in `.env`
12. **Validate**:
    ```bash
    python scripts/validate_features.py feature-list.json
    ```
13. **Scaffold project skeleton** (dirs, configs, dependency manifests) — based on **design doc** architecture
14. **Git init + initial commit**
15. **Run init script**, verify environment works. Then run `start.sh`, verify all services respond to health checks. Then run `test.sh`, verify tests execute. Then run `mutate.sh --full`, verify mutation testing works. Then run `cleanup.sh`, verify ports are released and PID files cleaned
16. **Update `task-progress.md`** — update `## Current State` with initial progress (0/N features passing), then append Session 0 entry (include SRS + design doc references)
17. **Begin first Worker cycle** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-work`

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
| `start.sh` / `start.ps1` | Runtime service startup: build → DB → backend → frontend; proxy-aware, health-checked, self-healing (LLM-generated) |
| `cleanup.sh` / `cleanup.ps1` | Reverse-order service teardown; PID cleanup; port release verification (LLM-generated) |
| `test.sh` / `test.ps1` | Test runner wrapper: env activation, tool check, coverage mode, structured output (LLM-generated) |
| `mutate.sh` / `mutate.ps1` | Mutation testing wrapper: env activation, tool check, incremental/full modes, structured output (LLM-generated) |
| `long-task-guide.md` | Worker session guide (LLM-generated, validated) |
| `.env.example` | Template for required env configs (safe to commit) |

## Integration

**Called by:** long-task-design (Step 6) or using-long-task (when design doc exists, no feature-list.json)
**Reads:** `docs/plans/*-srs.md` (requirements) + `docs/plans/*-design.md` (architecture)
**Chains to:** long-task-work (after initialization complete)
**Produces:** feature-list.json + all scaffolded artifacts listed above
