---
name: long-task-init
description: "Use when design doc exists but feature-list.json not yet created - scaffold project artifacts and decompose requirements into features"
---

# Initialize Long-Task Project

Run once after design is approved. Scaffolds all persistent artifacts, decomposes requirements into verifiable features, and prepares the project for iterative Worker cycles.

**Announce at start:** "I'm using the long-task-init skill to scaffold the project."

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

1. **Read the approved design document** from `docs/plans/`
2. **Run `scripts/init_project.py`** to scaffold deterministic artifacts:
   ```bash
   python scripts/init_project.py <project-name> --path . --lang <language>
   ```
   - `<project-name>` — from the design doc title
   - `<language>` — one of `python|java|typescript|c|cpp` from the design doc tech stack
   - Use `--line-cov`, `--branch-cov`, `--mutation-score` to override thresholds (defaults: 90/80/80)
   - Creates: `feature-list.json`, `CLAUDE.md` (appended), `task-progress.md`, `RELEASE_NOTES.md`, `examples/`, `scripts/`, `docs/plans/`
3. **Copy helper scripts** into `scripts/`:
   ```bash
   cp scripts/validate_features.py scripts/check_configs.py scripts/check_devtools.py scripts/validate_guide.py ./scripts/
   ```
   Source: `scripts/` in the plugin root. Target: `scripts/` in the project root.
4. **Verify `tech_stack` and `quality_gates`** in `feature-list.json`:
   - Confirm `language`, `test_framework`, `coverage_tool`, `mutation_tool` match the project
   - Adjust `quality_gates` thresholds if needed (defaults: line 90%, branch 80%, mutation 80%)
5. **Generate `long-task-guide.md`** — Create a project-tailored Worker session guide:
   - Read these files for reference:
     - `skills/long-task-work/SKILL.md` — Worker workflow
     - `skills/long-task-quality/SKILL.md` — verification enforcement
     - `skills/long-task-quality/coverage-recipes.md` — coverage/mutation tool setup
     - `references/architecture.md` — TDD workflow details
   - Include ONLY the project's language-specific coverage/mutation commands (from `tech_stack`)
   - Include Chrome DevTools MCP testing section ONLY if the project has UI features (`"ui": true`)
   - **Must include all required sections**: Orient, Bootstrap, Config Gate, TDD Red, TDD Green, Coverage Gate, TDD Refactor, Mutation Gate, Verification Enforcement, Code Review, Examples, Persist, Critical Rules
   - Validate:
     ```bash
     python scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json
     ```
6. **Generate `init.sh` / `init.ps1`** — Create real, runnable bootstrap scripts:
   - Actual dependency installation commands (not commented stubs)
   - Service startup commands if needed
   - Must be immediately executable after `git clone`
7. **Populate SRS fields in `feature-list.json`** from the approved design doc:
   - `constraints[]` — copy "System Constraints" items; each a concise string
   - `assumptions[]` — copy "Assumptions & Dependencies" items; each a concise string
   - NFR rows → create `category: "non-functional"` features with measurable `verification_steps`; coverage/mutation gates do not apply to NFR features
8. **Generate `docs/project-context.md`** — Extract "Target Users" and "Glossary" tables from the design doc; omit sections that are "None identified"
9. **Decompose requirements into features** — Populate `feature-list.json` `features[]`:
   - Each feature: `id`, `category`, `title`, `description`, `priority`, `status` (always `"failing"`), `verification_steps`, `dependencies`
   - For UI features: set `"ui": true`, optionally `"ui_entry": "/path"`; include `[devtools]`-prefixed verification steps
   - Aim for 10-200+ features; each independently verifiable and completable in one session
   - Order by priority and dependency chain
10. **Populate `required_configs`** — Identify external configuration requirements:
    - API keys, service URLs → type `env`
    - Config files, certificates → type `file`
    - Link each to features via `required_by`; provide `check_hint` with setup instructions
11. **Validate**:
    ```bash
    python scripts/validate_features.py feature-list.json
    ```
12. **Scaffold project skeleton** (dirs, configs, dependency manifests)
13. **Git init + initial commit**
14. **Run init script**, verify environment works
15. **Update `task-progress.md`** with Session 0 entry (include design doc reference)
16. **Begin first Worker cycle** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-work`

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
**Chains to:** long-task-work (after initialization complete)
**Produces:** feature-list.json + all scaffolded artifacts listed above
