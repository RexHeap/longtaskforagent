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
   - Auto-copies helper scripts (`validate_features.py`, `check_configs.py`, `check_devtools.py`, `validate_guide.py`, `get_tool_commands.py`, `validate_st_cases.py`) into project `scripts/`
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
   - **Must include `Environment Commands` section** with:
     - Environment activation command (e.g., `source .venv/bin/activate`, `conda activate myenv`, `nvm use 20`)
     - Direct test execution command (e.g., `pytest --cov=src tests/`)
     - Direct mutation testing command (e.g., `mutmut run`)
     - Direct coverage report command
     - These replace the now-removed test.sh/mutate.sh wrappers — Claude runs these directly
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
   - Must be immediately executable after `git clone`
   - **Must include at the end**: psutil installation for ST port-guard hooks:
     ```bash
     # Install psutil for ST port-guard hooks (cross-platform process management)
     if command -v pip &>/dev/null; then pip install psutil --quiet
     elif command -v pip3 &>/dev/null; then pip3 install psutil --quiet
     else echo "[WARN] pip not found — ST port-guard hook will use stdlib fallback"; fi
     ```
   - For Python projects: also add `psutil` to `requirements.txt` or `pyproject.toml`
6. **Generate `.claude/st-config.json`** — Declare service ports for the plugin-level port-guard hook:

   **Why**: The long-task-agent plugin registers a PreToolUse/Bash hook (`hooks/port_guard.py`) that fires automatically before every server-start command. It reads `.claude/st-config.json` to know which ports belong to this project.

   Extract port information from:
   - Design doc: service port declarations in API design or architecture sections
   - `.env.example`: extract `*_PORT=` variables
   - `package.json` scripts: extract `--port` arguments
   - `application.yml` / `application.properties`: extract `server.port`

   Generate `.claude/st-config.json`:
   ```json
   {
     "ports": [<all discovered port numbers as integers>],
     "port_range": null,
     "process_patterns": [<project-specific process names, e.g., "uvicorn", "myapp">],
     "health_check": {
       "url": "http://localhost:<primary_port>/health",
       "timeout": 30
     },
     "exclude_pids": []
   }
   ```
   If no ports can be determined, use `"ports": []` — the hook falls back to runtime auto-discovery.

   **Note**: No hook scripts or settings.json changes needed — the PreToolUse, SessionStart, and SessionEnd hooks are already registered at the plugin level via the long-task-agent `hooks/hooks.json`.

7. **Populate SRS fields in `feature-list.json`** — from the **SRS document**:
   - `constraints[]` — copy CON-xxx items from SRS "Constraints" section; each a concise string
   - `assumptions[]` — copy ASM-xxx items from SRS "Assumptions & Dependencies" section; each a concise string
   - NFR-xxx rows → create `category: "non-functional"` features with measurable `verification_steps`; coverage/mutation gates do not apply to NFR features
8. **Decompose requirements into features** — from the **SRS document** and **design document's Development Plan** (section 11), populate `feature-list.json` `features[]`:
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
   - **Backend-frontend pairing rule**: Frontend features (`"ui": true`) MUST list their backend API dependency features in `dependencies[]`. Additionally, features MUST be ordered in the `features[]` array using **paired grouping**: after each backend feature, place its corresponding frontend feature(s) immediately next in the array. This ensures the Worker develops Backend A → Frontend A → Backend B → Frontend B, rather than all backends then all frontends.
   - Aim for 10-200+ features; each independently verifiable and completable in one session
   - **Priority ordering**: follow the design document's Task Decomposition table (section 11.2) — P0/P1/P2/P3 maps to high/high/medium/low
   - **Dependency chain**: follow the design document's Dependency Chain diagram (section 11.3) to populate each feature's `dependencies[]`
   - **Milestone mapping**: group features by the design document's milestones for logical ordering
   - **Paired ordering within priorities**: Within each priority level, order features so that each backend feature is immediately followed by its frontend counterpart(s). Framework/infrastructure features (P0) come first without pairing. Example ordering:
     - P0: framework/infrastructure features (no pairing needed)
     - P1: [Backend Auth API, Frontend Auth Pages, Backend Orders API, Frontend Orders Pages, ...]
     - P2: [Backend Reports API, Frontend Reports Dashboard, ...]
     - The dependency mechanism ensures Frontend A cannot start until Backend A passes. The array ordering ensures Frontend A is the next candidate after Backend A.
9. **Populate `required_configs`** — from the **SRS document** (IFR-xxx interface requirements) and design doc:
   - API keys, service URLs → type `env`
   - Config files, certificates → type `file`
   - Link each to features via `required_by`; provide `check_hint` with setup instructions
10. **Generate `.env.example`** — from `required_configs`:
    - For each `env`-type config, write a commented template line:
      ```
      # <name> — <description>
      # Hint: <check_hint>
      # Required by features: <required_by ids>
      <KEY>=
      ```
    - Add `.env` to `.gitignore` (`.env.example` is safe to commit; `.env` contains secrets)
    - This template helps users know which values to fill in; the Worker Config Gate will prompt for missing values and store them in `.env`
11. **Validate**:
    ```bash
    python scripts/validate_features.py feature-list.json
    ```
12. **Scaffold project skeleton** (dirs, configs, dependency manifests) — based on **design doc** architecture
13. **Git init + initial commit**
14. **Run init script and verify environment**:
    - Run `init.sh` (or `init.ps1`), verify environment setup completes without errors
    - Verify test execution works: activate env → run test command from `long-task-guide.md` → confirm tests execute (may all fail at this point — that's expected)
    - Verify mutation testing command is available: activate env → run mutation tool version check
    - If any check fails: diagnose root cause, fix the script or configuration, re-run
    - Do NOT manually start services here — services are started by Claude directly during ST testing; the plugin-level port-guard hook fires automatically to ensure clean ports
15. **Update `task-progress.md`** — update `## Current State` with initial progress (0/N features passing), then append Session 0 entry (include SRS + design doc references)
16. **Begin first Worker cycle** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-work`

## Port Config Maintenance (Worker cycles)

When a Worker cycle introduces a **new backend service or changes a service port**, update `.claude/st-config.json`:
- Add the new port to `ports[]`
- Add the process name to `process_patterns[]` if project-specific
- Include in the git commit for that feature

The plugin-level port-guard hook reads this file at runtime — no hook scripts need to be regenerated.

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
| `init.sh` / `init.ps1` | Environment bootstrap (LLM-generated); includes psutil install for plugin port-guard hook |
| `.claude/st-config.json` | Port declarations for plugin port-guard hook (LLM-generated, Worker-maintained) |
| `long-task-guide.md` | Worker session guide with env activation + direct test commands (LLM-generated, validated) |
| `.env.example` | Template for required env configs (safe to commit) |

## Integration

**Called by:** long-task-design (Step 6) or using-long-task (when design doc exists, no feature-list.json)
**Reads:** `docs/plans/*-srs.md` (requirements) + `docs/plans/*-design.md` (architecture)
**Chains to:** long-task-work (after initialization complete)
**Produces:** feature-list.json + all scaffolded artifacts listed above
