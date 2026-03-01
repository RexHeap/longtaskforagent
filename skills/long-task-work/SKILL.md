---
name: long-task-work
description: "Use when feature-list.json exists - orchestrate features through the full TDD pipeline with quality gates and code review"
---

# Worker — One Feature Per Cycle

Execute multi-session software projects by implementing one feature per cycle. Each cycle follows a strict pipeline: Orient → Gate → Plan → TDD → Quality → ST Acceptance → Review → Persist.

**Announce at start:** "I'm using the long-task-work skill. Let me orient myself."

**Core principle:** Each sub-step has its own skill. Follow the orchestration order exactly.

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

### 1. Orient
- Load `.env` file if it exists — this populates environment variables for required configs collected in previous sessions
- Read `task-progress.md` `## Current State` section — progress stats, last completed feature, next feature up
- Read `feature-list.json` — note `constraints[]`, `assumptions[]`, `required_configs[]`, feature statuses
- Read `long-task-guide.md` — project-specific workflow guidance
- Read design doc **Section 1** (`docs/plans/*-design.md`) — project overview and architecture snapshot for global context
- Run `git log --oneline -10` — recent commit context
- Pick next `"status": "failing"` feature by priority, then by array position in `features[]` (first eligible wins) — **skip features with `"deprecated": true`**
- **Dependency satisfaction check**: After selecting a candidate feature, verify that ALL feature IDs in its `dependencies[]` have `"status": "passing"` in `feature-list.json`. If any dependency is still `"failing"`:
  - Log: "Feature #{id} ({title}) skipped — unsatisfied deps: #{dep1}, #{dep2}"
  - Pick the next eligible `"failing"` feature (by priority + dependency order) whose dependencies are all satisfied
  - If NO features have all dependencies satisfied → warn user via `AskUserQuestion`: "All remaining features have unsatisfied dependencies. Circular or over-constrained dependency graph detected." → let user choose which feature to force-start (override dependency check)
  - Record skipped features and reason in `task-progress.md`
- If target feature has `"ui": true` and UCD document exists (`docs/plans/*-ucd.md`), read the UCD style guide — reference style tokens, component prompts, and page prompts to ensure frontend implementation matches the approved visual style

**Document Lookup Protocol (used by Steps 5, 10, and 11):**

When you need the design section or SRS requirement for a feature, do NOT grep for the feature title. Instead:

1. **Design document** (`docs/plans/*-design.md`):
   - Read the design document's **Section 4 heading area** (use Read tool with offset/limit to scan section 4 headers — look for lines matching `### 4.N Feature:`)
   - Identify which `### 4.N` subsection corresponds to the target feature by matching the feature title or FR-ID
   - Read the **entire subsection** from `### 4.N` through the line before `### 4.(N+1)` (or end of section 4) — this includes Overview, Class Diagram, Sequence Diagram, Flow Diagram, and Design Decisions
   - Store this full text as `{design_section}` for use in Plan (Step 5), ST Acceptance (Step 10), and Review (Step 11)

2. **SRS document** (`docs/plans/*-srs.md`):
   - Read the SRS **Section 4 (Functional Requirements)** heading area to find the `### FR-xxx` subsection matching the target feature
   - Read the **entire FR-xxx subsection** including EARS statement, priority, acceptance criteria, and Given/When/Then scenarios
   - Store this as `{srs_section}` for use in Plan and Review

3. **UCD document** (`docs/plans/*-ucd.md`, only for `"ui": true` features):
   - Read the UCD's table of contents or section headers
   - Find sections referencing the target feature's UI components or pages
   - Read the **full relevant sections** including style tokens, component prompts, and page prompts

**Why this matters:** Grep returns isolated matching lines without surrounding context. Design sections contain class diagrams, sequence diagrams, flow diagrams, and design rationale that span dozens of lines — all of which are needed for correct implementation and compliance review.

### 2. Bootstrap
- **Development environment readiness**: Check if environment is set up
  - If `init.sh` / `init.ps1` exists and environment is not ready: run it once
  - Record decision in `task-progress.md` if script was executed
- **Confirm test commands available**: Run `python scripts/get_tool_commands.py feature-list.json` and verify the test/coverage/mutation commands are correct for the tech stack; use these commands directly throughout the cycle (no wrapper scripts)
- Smoke-test previously passing features (activate environment per `long-task-guide.md` → run test command directly)

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

### 4. Plan
Write a step-by-step implementation plan for the selected feature.
Save to `docs/plans/YYYY-MM-DD-<feature-name>.md`.
See `references/plan-writing.md` for plan structure and task granularity.

**Design document reference (mandatory):**
- Using the Document Lookup Protocol above, read the full `{design_section}` for this feature — do NOT grep; read the complete subsection including all diagrams and design decisions
- Also read the full `{srs_section}` (the FR-xxx requirement from the SRS) for complete acceptance criteria
- The plan MUST align with the approved class diagrams, sequence flows, and architectural decisions
- If the plan deviates from the design → explain why and get user approval before proceeding
- Reference the design's third-party dependency versions when choosing libraries

**UCD style guide reference (mandatory for `"ui": true` features):**
- If `docs/plans/*-ucd.md` exists, read the relevant component prompts and page prompts for this feature
- The plan MUST specify which UCD style tokens (colors, typography, spacing) apply to each UI element
- The plan MUST reference the UCD component prompt for each UI component being implemented
- Any visual deviation from UCD → explain why and get user approval

### 5-7. TDD Cycle (Red → Green → Refactor)
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-tdd` and follow it exactly.

Context to carry forward:
- Current feature object from feature-list.json
- `quality_gates` and `tech_stack` from feature-list.json
- Plan file path from Step 5
- Full `{srs_section}` from Document Lookup Protocol — TDD Red uses this as primary specification input alongside `verification_steps`
- Full `{design_section}` from Document Lookup Protocol — architectural constraints and interface contracts
- **Test commands**: from `python scripts/get_tool_commands.py feature-list.json` — use these directly (no wrapper scripts)

### 8. Quality Gates
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-quality` and follow it exactly.

Context to carry forward:
- Feature ID and verification_steps
- `quality_gates` thresholds from feature-list.json
- `tech_stack` tool names for coverage/mutation commands
- **Test commands**: from `python scripts/get_tool_commands.py feature-list.json` — use directly

### 9. ST Acceptance Test Cases
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-feature-st` and follow it exactly.

Execute black-box acceptance testing for the feature **after** TDD and quality gates pass. The skill generates ISO/IEC/IEEE 29119 compliant test case documents.

Context to carry forward:
- Current feature object from feature-list.json
- Full `{srs_section}` and `{design_section}` from Document Lookup Protocol
- Plan file path from Step 5
- UCD sections (if `"ui": true`)
- `quality_gates` and `tech_stack` from feature-list.json
- **Implementation code** — files created/modified during TDD (from git diff or plan document file list)
- **Test results summary** — from TDD and Quality Gates (coverage %, mutation score)

Output: `docs/test-cases/feature-{id}-{slug}.md`

**Hard Gate:**
- Any execution failure (environment or test case) must be reported to user via `AskUserQuestion`
- **No bypass allowed** — cannot skip ST for any reason

### 10. Spec & Design Compliance Review
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-review` and follow it exactly.

Context to carry forward:
- Feature object from feature-list.json
- Full `{design_section}` text extracted via Document Lookup Protocol (the entire §4.N subsection, NOT a grep snippet)
- Full `{srs_section}` text (the entire FR-xxx subsection from SRS)
- Plan document (`docs/plans/YYYY-MM-DD-<feature-name>.md`) from Step 5
- **ST test case document** (`docs/test-cases/feature-{id}-{slug}.md`) from Step 10
- UCD style guide sections (`docs/plans/*-ucd.md`) — if feature has `"ui": true` and UCD exists
- Git diff since before implementation began
- Test results summary

### 11. Add Examples
Create runnable examples in `examples/` demonstrating the completed feature.
- Match example granularity to feature scope
- Skip only for pure infrastructure features
- Include in git commit

### 12. Persist
- Git commit (include implementation, tests, examples, **test case document**)
- Update `RELEASE_NOTES.md` (Keep a Changelog format)
- Update `task-progress.md`:
  - Update `## Current State` header: progress count (X/Y passing), last completed feature (#id title, date), next feature (#id title)
  - Append session entry below the log separator
- Mark feature `"status": "passing"` in `feature-list.json`
- Set `"st_case_path"` and `"st_case_count"` on the feature object in `feature-list.json`
- Validate:
  ```bash
  python scripts/validate_features.py feature-list.json
  ```
- Git commit again (progress files)

### 13. Continue
- If failing non-deprecated features remain and context allows → proceed to next feature (back to Step 1)
- If **no failing non-deprecated features remain** → all active features are passing. **Invoke `long-task:long-task-st`** to begin system testing.
- If context is exhausted → end session (ensure task-progress.md is updated)

**Note**: Stop any services you started directly during this cycle before ending the session. Services started during ST acceptance testing (Step 10) are stopped by `long-task-feature-st`.

## Critical Rules

- **One feature per cycle** — prevents context exhaustion
- **Strict step order** — no skipping, no reordering
- **Sub-skills are non-negotiable** — ST Test Cases, TDD, Quality, Compliance Review MUST be invoked via Skill tool
- **Config gate before planning** — never plan or code when required configs are missing
- **Never mark "passing" without fresh evidence** — run tests, read output, then mark
- **Never remove or edit `verification_steps` in Worker** — use `/long-task:increment` for requirement changes
- **Systematic debugging only** — on error, read `references/systematic-debugging.md`; trace root cause, never guess-and-fix
- **Update RELEASE_NOTES.md after every git commit**
- **Always commit + update progress before ending session** — bridges context gap
- **Never leave broken code** — revert incomplete work

## Red Flags

| Rationalization | Correct Action |
|---|---|
| "I'll mock that config later" | Run Config Gate. Real configs needed. |
| "This feature is trivial, skip test cases" | Invoke long-task-feature-st. Every feature. |
| "This feature is trivial, skip TDD" | Invoke long-task-tdd. Every feature. |
| "Tests pass, mark it done" | Invoke long-task-quality first. |
| "Coverage looks close enough" | Thresholds are hard gates. Run the tool. |
| "I'll review it myself quickly" | Invoke long-task-review. Always. |
| "Let me just try this quick fix" | Systematic debugging first. |
| "I'll skip the example for this one" | Only skip for pure infrastructure. |
| "I'll update release notes at the end" | Update after every commit. |
| "Mutation score is probably OK" | Run mutation tests and read the report. |
| "The UI looks correct to me" | Run automated detection + EXPECT/REJECT. |
| "ST test case failed but the code is fine" | Report to user. No bypass. Fix code or use `/long-task:increment` to modify test case. |
| "Port is busy, let me kill manually" | The port-guard hook handles this automatically. Just re-run the command. |
| "Environment is down, skip ST cases" | BLOCKED, not skipped. Fix environment or ask user. |
| "I need to change the verification_steps" | Use `/long-task:increment` — Worker cannot modify them. |
| "This deprecated feature still needs work" | Skip it. Deprecated features are excluded. |
| "Backend isn't ready but I'll mock it for now" | Dependency check exists for a reason. Develop backend features first. |
| "I'll skip the dependency check this once" | Never skip. Reorder features so deps are satisfied. |

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
1. `long-task:long-task-tdd` (Steps 6-8) — TDD Red-Green-Refactor
2. `long-task:long-task-quality` (Step 9) — Coverage + Mutation
3. `long-task:long-task-feature-st` (Step 10) — Black-Box Feature Acceptance Testing (ISO/IEC/IEEE 29119, self-managed lifecycle)
4. `long-task:long-task-review` (Step 11) — Spec & Design Compliance Review
**Reads/Writes:** feature-list.json, task-progress.md (including `## Current State`), RELEASE_NOTES.md
**Read on-demand (via Read tool, NOT Skill tool):** `references/plan-writing.md`, `references/systematic-debugging.md`
