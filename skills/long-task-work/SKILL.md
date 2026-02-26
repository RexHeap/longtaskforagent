---
name: long-task-work
description: "Use when feature-list.json exists - orchestrate one feature per session through the full TDD pipeline with quality gates and code review"
---

# Worker Session — One Feature Per Cycle

Execute multi-session software projects by implementing one feature per context cycle. Each cycle follows a strict pipeline: Orient → Gate → Plan → TDD → Quality → Review → Persist.

**Announce at start:** "I'm using the long-task-work skill. Let me orient myself."

**Core principle:** Each sub-step has its own skill. Follow the orchestration order exactly.

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

### 1. Orient
- Load `.env` file if it exists — this populates environment variables for required configs collected in previous sessions
- Read `task-progress.md` — what was done in previous sessions
- Read `feature-list.json` — note `constraints[]`, `assumptions[]`, `required_configs[]`, feature statuses
- Read `long-task-guide.md` — project-specific workflow guidance
- Read design document (`docs/plans/*-design.md`) — locate the **Key Feature Design** section (section 4.N) for the target feature to understand the approved architecture, class diagrams, sequence flows, and design decisions
- Run `git log --oneline -10` — recent commit context
- Pick next `"status": "failing"` feature by priority + dependency order
- If target feature has `"ui": true` or involves domain terms, read `docs/project-context.md`
- If target feature has `"ui": true` and UCD document exists (`docs/plans/*-ucd.md`), read the UCD style guide — reference style tokens, component prompts, and page prompts to ensure frontend implementation matches the approved visual style

### 2. Bootstrap
- Run `init.sh` / `init.ps1` — ensure environment is ready
- Smoke-test previously passing features (quick verify)

### 3. Config Gate
```bash
python scripts/check_configs.py feature-list.json --feature <id> --dotenv .env
```
`<id>` = the feature ID selected in Step 1. The `--dotenv .env` flag loads previously stored config values before checking.

**If configs are missing — prompt for text input and save to `.env`:**

1. For each missing `env`-type config, use `AskUserQuestion` to ask the user to **type the value** — do NOT provide predefined option buttons. Frame the question with the config's `name`, `description`, and `check_hint` so the user knows what to provide.
   - Example: "Please enter the value for `OPENAI_API_KEY` (OpenAI API key for LLM integration). Hint: Get it from https://platform.openai.com/api-keys"
2. For each missing `file`-type config, ask the user to provide the file path or create the file manually.
3. After receiving all values, **append env-type configs to `.env`**:
   ```
   # <config name> — <description>
   KEY=value
   ```
4. Re-run the check to confirm:
   ```bash
   python scripts/check_configs.py feature-list.json --feature <id> --dotenv .env
   ```
5. Add `.env` to `.gitignore` if not already present (contains secrets).
6. **Block until all configs pass.**

### 4. DevTools Gate (only if `"ui": true`)
```bash
python scripts/check_devtools.py feature-list.json --feature <id>
```
`<id>` = same feature ID. If Chrome DevTools MCP not available → prompt user and **block until resolved**.

### 5. Plan
Write a step-by-step implementation plan for the selected feature.
Save to `docs/plans/YYYY-MM-DD-<feature-name>.md`.
See `references/plan-writing.md` for plan structure and task granularity.

**Design document reference (mandatory):**
- Read the corresponding Key Feature Design section (section 4.N) from `docs/plans/*-design.md`
- The plan MUST align with the approved class diagrams, sequence flows, and architectural decisions
- If the plan deviates from the design → explain why and get user approval before proceeding
- Reference the design's third-party dependency versions when choosing libraries

**UCD style guide reference (mandatory for `"ui": true` features):**
- If `docs/plans/*-ucd.md` exists, read the relevant component prompts and page prompts for this feature
- The plan MUST specify which UCD style tokens (colors, typography, spacing) apply to each UI element
- The plan MUST reference the UCD component prompt for each UI component being implemented
- Any visual deviation from UCD → explain why and get user approval

### 6-8. TDD Cycle
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-tdd` and follow it exactly.

Context to carry forward:
- Current feature object from feature-list.json
- `quality_gates` and `tech_stack` from feature-list.json
- Plan file path from Step 5

### 9. Quality Gates
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-quality` and follow it exactly.

Context to carry forward:
- Feature ID and verification_steps
- `quality_gates` thresholds from feature-list.json
- `tech_stack` tool names for coverage/mutation commands

### 10. Code Review
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-review` and follow it exactly.

Context to carry forward:
- Feature object from feature-list.json
- Design document Key Feature Design section (section 4.N from `docs/plans/*-design.md`) for the target feature
- Plan document (`docs/plans/YYYY-MM-DD-<feature-name>.md`) from Step 5
- UCD style guide (`docs/plans/*-ucd.md`) — if feature has `"ui": true` and UCD exists
- Git diff since before implementation began
- Test results summary

### 11. Add Examples
Create runnable examples in `examples/` demonstrating the completed feature.
- Match example granularity to feature scope
- Skip only for pure infrastructure features
- Include in git commit

### 12. Persist
- Git commit (include implementation, tests, examples)
- Update `RELEASE_NOTES.md` (Keep a Changelog format)
- Update `task-progress.md` with session entry
- Mark feature `"status": "passing"` in `feature-list.json`
- Validate:
  ```bash
  python scripts/validate_features.py feature-list.json
  ```
- Git commit again (progress files)

### 13. Continue
- If failing features remain and context allows → proceed to next feature (back to Step 1)
- If context is exhausted → end session (ensure task-progress.md is updated)

## Critical Rules

- **One feature per cycle** — prevents context exhaustion
- **Strict step order** — no skipping, no reordering
- **Sub-skills are non-negotiable** — TDD, Quality, Review MUST be invoked via Skill tool
- **Config gate before planning** — never plan or code when required configs are missing
- **Never mark "passing" without fresh evidence** — run tests, read output, then mark
- **Never remove or edit `verification_steps`** — immutable once created
- **Systematic debugging only** — on error, read `references/systematic-debugging.md`; trace root cause, never guess-and-fix
- **Update RELEASE_NOTES.md after every git commit**
- **Always commit + update progress before ending session** — bridges context gap
- **Never leave broken code** — revert incomplete work

## Red Flags

| Rationalization | Correct Action |
|---|---|
| "I'll mock that config later" | Run Config Gate. Real configs needed. |
| "This feature is trivial, skip TDD" | Invoke long-task-tdd. Every feature. |
| "Tests pass, mark it done" | Invoke long-task-quality first. |
| "Coverage looks close enough" | Thresholds are hard gates. Run the tool. |
| "I'll review it myself quickly" | Invoke long-task-review. Always. |
| "Let me just try this quick fix" | Systematic debugging first. |
| "I'll skip the example for this one" | Only skip for pure infrastructure. |
| "I'll update release notes at the end" | Update after every commit. |
| "Mutation score is probably OK" | Run mutation tests and read the report. |
| "I'll skip test review for this simple feature" | Test Plan Review is mandatory. |
| "The UI looks correct to me" | Run automated detection + EXPECT/REJECT. |

## On Error

Follow the systematic debugging process — **never guess-and-fix**:
1. Collect evidence (error message, stack trace, git diff)
2. Reproduce the issue
3. Trace root cause (read `references/systematic-debugging.md` for detailed process)
4. Write failing test for the bug
5. Fix with single targeted change
6. Give up after 3 attempts → escalate to user

## Integration

**Called by:** using-long-task (when feature-list.json exists) or long-task-init (Step 16)
**Invokes (in strict order):**
1. `long-task:long-task-tdd` (Steps 6-8) — TDD Red-Green-Refactor with Test Plan Review
2. `long-task:long-task-quality` (Step 9) — Coverage + Mutation + Verification
3. `long-task:long-task-review` (Step 10) — Two-stage Code Review
**Reads/Writes:** feature-list.json, task-progress.md, RELEASE_NOTES.md
**Read on-demand (via Read tool, NOT Skill tool):** `references/plan-writing.md`, `references/systematic-debugging.md`
