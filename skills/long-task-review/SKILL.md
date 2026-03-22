---
name: long-task-review
description: "Use after quality gates pass in a long-task project - runs spec & design compliance review before persisting"
---

# Spec & Design Compliance Review — SubAgent Dispatch

Review runs after every feature, before Persist. No exceptions. The main Agent dispatches a review SubAgent with file paths — the SubAgent reads all documents and evidence itself in fresh context.

**Announce at start:** "I'm using the long-task-review skill to review this feature."

## When to Run

- After **every** feature passes quality gates
- Before the Persist phase (git commit)
- No exceptions — even "simple" features need review

## Step 1: Gather Path Parameters

Collect these from the current session state. Do NOT read document contents yourself:

- `feature_json` — current feature object from feature-list.json (compact JSON)
- `feature_id` — feature ID
- `feature_title` — feature title
- `srs_file` — path to SRS doc (`docs/plans/*-srs.md`)
- `srs_start` / `srs_end` — line range of the FR-xxx subsection (from Orient Document Lookup)
- `design_file` — path to design doc (`docs/plans/*-design.md`)
- `design_start` / `design_end` — line range of the §4.N subsection (from Orient Document Lookup)
- `plan_doc_path` — path to feature detailed design (`docs/features/YYYY-MM-DD-<feature-name>.md`)
- `st_case_path` — path to ST test case document (`docs/test-cases/feature-{id}-{slug}.md`)
- `ucd_file` / `ucd_start` / `ucd_end` — UCD doc path + line range (only for `"ui": true`; omit otherwise)
- `base_sha` — git SHA before implementation began (for `git diff`)
- `test_command` — test command from `long-task-guide.md`

## Step 2: Construct SubAgent Prompt

Read `skills/long-task-review/prompts/spec-reviewer-prompt.md` and fill the template variables with the path parameters collected above:

| Template Variable | Value |
|-------------------|-------|
| `{{FEATURE_JSON}}` | feature object (compact JSON) |
| `{{FEATURE_ID}}` | feature ID |
| `{{FEATURE_TITLE}}` | feature title |
| `{{SRS_FILE}}` | SRS doc path |
| `{{SRS_START}}` / `{{SRS_END}}` | FR-xxx line range |
| `{{DESIGN_FILE}}` | design doc path |
| `{{DESIGN_START}}` / `{{DESIGN_END}}` | §4.N line range |
| `{{PLAN_DOC_PATH}}` | feature design doc path |
| `{{ST_CASE_PATH}}` | ST test case doc path |
| `{{UCD_FILE}}` / `{{UCD_START}}` / `{{UCD_END}}` | UCD path + range (ui:true only) |
| `{{BASE_SHA}}` | base SHA for git diff |
| `{{TEST_COMMAND}}` | test command |

**Key difference from before**: You are passing FILE PATHS and LINE RANGES, not file contents. The SubAgent will use the Read tool and Bash tool to read documents and gather evidence itself.

## Step 3: Dispatch SubAgent

**Claude Code:** Use the `Agent` tool:
```
Agent(
  description = "Spec & Design Review for feature #{feature_id}",
  prompt = [the filled prompt template]
)
```

**OpenCode:** Use `@mention` syntax or the platform's native subagent mechanism with the same prompt content.

## Step 4: Parse Result

Read the SubAgent's review output:

- **Verdict: PASS** (all S1-S5, D1-D5, R1-R3, and U1-U4 if applicable are YES)
  1. Record in `task-progress.md`: "Review: PASS"
  2. Proceed to Add Examples + Persist

- **Verdict: FAIL** (any NO found)
  1. Read the specific violations from the rubric
  2. Fix the issues (code changes, test additions, etc.)
  3. Re-run tests to confirm fixes
  4. Re-dispatch SubAgent for re-review (only changed items need re-check)
  5. Max 3 review rounds → escalate to user via `AskUserQuestion`

## Review Dimensions

### Spec Compliance (S1-S5)

| # | Check |
|---|-------|
| S1 | All `verification_steps` covered by tests |
| S2 | Tests verify behavior, not implementation details |
| S3 | No undocumented side effects |
| S4 | Edge cases from the spec are handled |
| S5 | Feature `description` matches actual behavior |

### Design Compliance (D1-D5)

| # | Check |
|---|-------|
| D1 | Class/module structure matches the design document's class diagram |
| D2 | Interaction flow matches the design document's sequence diagram |
| D3 | Third-party dependency versions match the design document's dependency table |
| D4 | Architectural layers/boundaries respected as defined in the logical view |
| D5 | No unauthorized design deviations (or deviations are documented with user approval in the plan) |

### Detailed Design Compliance (P1-P6)

| # | Check |
|---|-------|
| P1 | Implementation tasks match the feature detailed design's task decomposition (§8) |
| P2 | Public method signatures match the Interface Contract table (§3) — parameters, return types, exceptions |
| P3 | Core algorithm matches the pseudocode and flow diagram in §5 — control flow, key decisions, data transformations |
| P4 | Boundary conditions handled match the boundary matrix (§5.3) — all rows covered |
| P5 | Error handling matches the error table (§5.4) — trigger conditions, recovery actions, error types |
| P6 | State transitions (if any) match the state diagram (§6) — all states reachable, no undocumented transitions |

### UCD Compliance (U1-U4) — only for `"ui": true` features with UCD document

| # | Check |
|---|-------|
| U1 | Color values used in CSS/styles match UCD color palette tokens |
| U2 | Typography (font family, size, weight, line height) matches UCD typography scale |
| U3 | Spacing and layout (padding, margin, border radius, shadow) follow UCD spacing tokens |
| U4 | Component structure and visual hierarchy match UCD component prompts for the implemented components |

### Test Case Completeness (T1-T3)

| # | Check |
|---|-------|
| T1 | Every `verification_step` has at least one corresponding ST test case in `docs/test-cases/feature-{id}-{slug}.md` |
| T2 | Every ST test case has at least one automated test implementing it (check test file comments for `# ST-xxx` references) |
| T3 | UI test cases (if any) include EXPECT/REJECT clauses, console error gate, and accessibility checkpoint |

**Any NO in S1-S5 or D1-D5 → FAIL. Fix gaps, re-run tests, re-review.**
**Any NO in U1-U4 → FAIL (for ui:true features). Visual inconsistency must be fixed before proceeding.**
**Any NO in T1-T3 → FAIL. Test case coverage gaps must be filled before proceeding.**
**Any NO in P1-P6 → FAIL (must fix before feature complete). Interface contract and algorithm deviations indicate spec drift.**

## Issue Severity

| Severity | Response | Blocks? |
|----------|----------|---------|
| Critical | Fix immediately | Yes |
| Important | Fix before next feature | Yes |
| Minor | Fix in refactor or next session | No |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Skip review for "simple" features | Always run review |
| Bundle multiple issues into one finding | One concern per issue |
| Performative agreement ("Great code!") | PASS or specific issues, no filler |
| Read document contents into main agent context | Pass file paths to SubAgent |

## Integration

**Called by:** long-task-work (Step 10)
**Dispatches:** spec-reviewer subagent (`skills/long-task-review/prompts/spec-reviewer-prompt.md`)
**Requires:** Quality gates passed (long-task-quality), ST test cases executed (long-task-feature-st)
**Inputs (paths only — SubAgent reads contents itself):**
- Feature spec (compact JSON)
- File paths + line ranges: SRS doc, design doc, plan doc, ST case doc, UCD doc (if ui:true)
- Base SHA (for git diff)
- Test command (from long-task-guide.md)
**Produces:** Review verdict (PASS/FAIL with findings)
**Returns to:** long-task-work for Add Examples + Persist steps
