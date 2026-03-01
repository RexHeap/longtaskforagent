---
name: long-task-st-case
description: "Use after quality gates pass in a long-task project - generates and executes ISO/IEC/IEEE 29119 compliant acceptance test case documents per feature"
---

# ST Test Case Generation — Per Feature

Generate structured, standards-compliant acceptance test case documents for a feature **after** TDD implementation and quality gates pass. Test cases validate the completed implementation against requirements and design.

**Announce at start:** "I'm using the long-task-st-case skill to generate test cases for this feature."

## Standard

Default: **ISO/IEC/IEEE 29119-3** (Test Documentation).

Users may override the template and style via `feature-list.json` root fields:
- `st_case_template_path` — custom template file (defines structure)
- `st_case_example_path` — example file (defines style, language, detail level)

## When to Run

- After **every** feature's Quality Gates step (Worker Step 9), before Review (Worker Step 11)
- No exceptions — even "simple" features need acceptance test case documentation
- Invoked by `long-task-work` as a sub-skill (not directly by router)

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

### 1. Load Context

Read all input artifacts for the target feature:

- **Feature object** from `feature-list.json` — ID, title, description, verification_steps, ui flag, dependencies, priority
- **SRS section** — full FR-xxx from `docs/plans/*-srs.md` via Document Lookup Protocol (read the entire subsection, NOT grep)
- **Design section** — full §4.N from `docs/plans/*-design.md` via Document Lookup Protocol
- **Plan document** — from Step 5 (`docs/plans/YYYY-MM-DD-<feature-name>.md`)
- **UCD sections** (only if `"ui": true`) — relevant component prompts and page prompts from `docs/plans/*-ucd.md`
- **Root context** — `constraints[]`, `assumptions[]` from `feature-list.json` root
- **Related NFRs** — check SRS for NFR-xxx requirements that trace to this feature
- **Implementation code** — read the files created/modified during TDD (from git diff or plan document file list)
- **Test results summary** — from TDD and Quality Gates (coverage %, mutation score)
- **Existing unit tests** — read the test files written during TDD Red to understand what's already covered at unit level

### 2. Load Template

1. Check `feature-list.json` root for `st_case_template_path`:
   - If present and file exists: read the custom template
   - If absent: use default template at `docs/templates/st-case-template.md`
2. Check `feature-list.json` root for `st_case_example_path`:
   - If present and file exists: read the example file — adapt style, language, and detail level from it
   - If absent: use standard professional style

**Template + Example interaction:**
- Both provided → use template's **structure**, example's **style**
- Only template → use template structure with default style
- Only example → infer structure from example, use example's style
- Neither → use the built-in default template (ISO/IEC/IEEE 29119-3)

### 2b. Load E2E Scenario Prompt (for `"ui": true` features)

If the target feature has `"ui": true`, read `prompts/e2e-scenario-prompt.md`. This provides mandatory rules for generating Chrome DevTools MCP-executable E2E test scenarios. Apply these rules during Step 3 for all UI and A11Y category test cases.

**Why**: Without this prompt, UI test cases tend to be simple page-load checks. The prompt ensures each test step maps to a concrete MCP tool call (navigate_page, click, fill, take_snapshot, evaluate_script, list_console_messages) and follows the three-layer detection model.

### 3. Derive Test Cases

For each `verification_step` in the feature, generate **one or more** test cases.

**Category assignment rules:**

| Category | Abbrev | When to generate |
|----------|--------|------------------|
| `functional` | FUNC | Always — happy path + error path for every feature |
| `boundary` | BNDRY | Always — edge cases, limits, empty/max/zero values |
| `ui` | UI | Only when `"ui": true` — Chrome DevTools interaction + visual verification |
| `security` | SEC | When feature handles user input, auth, or external data |
| `accessibility` | A11Y | Only when `"ui": true` — WCAG 2.1 AA checks |
| `performance` | PERF | Only when traceable to NFR-xxx with performance metrics |

**UI test case enrichment (mandatory for `"ui": true` features):**
- Every UI category test case MUST have ≥ 5 steps in the test step table
- Every step MUST specify the Chrome DevTools MCP tool that executes it (navigate_page, click, fill, take_snapshot, evaluate_script, etc.)
- Every test case MUST include all three detection layers (Layer 1: evaluate_script, Layer 2: EXPECT/REJECT, Layer 3: list_console_messages)
- Test cases that verify data MUST include backend integration steps (real API data, not mocked)
- Test cases MUST test at least one negative path via UI (e.g., submit invalid form → verify error message)
- See `prompts/e2e-scenario-prompt.md` for detailed expansion rules and examples

**Minimum coverage:**
- Every feature MUST have at least one FUNC and one BNDRY test case
- Every `verification_step` MUST map to at least one test case
- UI features MUST have at least one UI and one A11Y test case

**Case ID format:**
```
ST-{CATEGORY}-{FEATURE_ID(3 digits)}-{SEQ(3 digits)}
```
Examples: `ST-FUNC-005-001`, `ST-UI-005-002`, `ST-SEC-012-001`

**Test case content rules:**
- Test steps MUST be concrete and executable (no vague "verify it works")
- Expected results MUST be specific and assertable (no "should look correct")
- Preconditions MUST list real, verifiable states
- Verification points MUST be observable and automatable where possible

**Acceptance-level focus:** Since implementation code and unit tests now exist, test cases should focus on **acceptance-level verification** — confirming the implementation matches requirements from a user/system perspective. Avoid duplicating unit test assertions. Focus on behavioral scenarios, integration paths, and end-to-end workflows that unit tests cannot cover.

### 4. UI Test Case Requirements (only if `"ui": true`)

For UI features, test cases consolidate previously separate concerns:

**a) Functional UI testing** — navigation, interaction, state changes:
- Navigation path from `ui_entry` or specific route
- Interaction sequence: click, fill, press_key steps
- EXPECT/REJECT clauses (mandatory for every UI test step)

**b) UCD compliance** — style token verification:
- Reference which UCD color palette tokens apply to verified elements
- Reference which typography scale values apply
- Reference which spacing tokens apply
- This replaces the separate U1-U4 review check for individual elements

**c) Accessibility** — WCAG 2.1 AA:
- Keyboard navigability for interactive elements
- Color contrast verification against WCAG minimum ratios
- ARIA attributes and semantic HTML verification
- Screen reader compatibility notes

**d) Console error gate:**
- Every UI test case MUST include a post-step check: `list_console_messages(types=["error"])` must return 0
- Exception: if test explicitly expects console errors, note with `[expect-console-error: <pattern>]`

**e) Three-layer detection:**
- Layer 1: Automated error detection script via `evaluate_script()` — reference `skills/long-task-tdd/references/ui-error-detection.md`
- Layer 2: EXPECT/REJECT format in test steps
- Layer 3: Console error gate

**f) MCP tool call mapping:**
- Each test step's "操作" column must be specific enough to map to a single Chrome DevTools MCP tool call
- BAD: "检查登录页面" — which tool? what to check?
- GOOD: "navigate_page(url='/login') → wait_for(['Sign In']) → take_snapshot() → 验证 EXPECT: 邮箱输入框, 密码输入框, 登录按钮"
- The test step table becomes a **script** that TDD can mechanically translate into Chrome DevTools MCP calls during Red phase
- See `prompts/e2e-scenario-prompt.md` for the full MCP tool → test step mapping table

### 5. Write Test Case Document

Output file: `docs/test-cases/feature-{id}-{slug}.md`
- `{id}` is the feature ID (as-is, not zero-padded in filename)
- `{slug}` is a kebab-case version of the feature title

**Document structure (following template):**

1. **Header** — Feature ID, related requirements, date, standard
2. **Summary table** — count by category
3. **Test case blocks** — one per case, all required sections
4. **Traceability matrix** — Case ID ↔ Requirement ↔ verification_step ↔ Automated test ↔ Result

The traceability matrix `结果` column starts as `PENDING`. Execute each test case in Step 7 below and update to `PASS`/`FAIL` during this step.

### 6. Validate

Run the validation script:

```bash
python scripts/validate_st_cases.py docs/test-cases/feature-{id}-{slug}.md --feature-list feature-list.json --feature {id}
```

- **Exit 0**: proceed to Execute Test Cases (Step 7)
- **Exit 1**: fix errors and re-validate (do NOT proceed with errors)

### 7. Execute Test Cases

Since implementation code already exists (TDD and Quality Gates are complete), execute each test case to verify acceptance:

1. For **non-UI test cases**: verify by running the relevant test commands or manual checks against the running system
2. For **UI test cases**: execute via Chrome DevTools MCP tools following the step tables (navigate_page, click, fill, take_snapshot, evaluate_script, list_console_messages)
3. Update the traceability matrix `结果` column to `PASS` or `FAIL` for each case

**If any test case FAILS:**
- Report to user via `AskUserQuestion` with: failed case ID, step details, actual vs expected
- Options: fix code and re-execute / modify test case via `/long-task:increment` / terminate cycle
- A failure here blocks the feature from proceeding to Review

**If all test cases PASS:**
- Proceed to Review (Worker Step 11)

Each automated test SHOULD reference its corresponding ST case ID via a comment:
```python
# ST-FUNC-005-001
def test_valid_order_creation():
    ...
```

## Execution Rules (Hard Gates)

### Environment Prerequisite

ST test case execution depends on the runtime environment provided by `start.sh` / `start.ps1` (started in Worker Step 2 Bootstrap).

- If Bootstrap failed or services are not running: runtime test steps (UI interaction, API calls, DB verification) are **BLOCKED**
- BLOCKED status means: **cannot proceed to TDD for those test cases**
- Must report to user via `AskUserQuestion` with details:
  - Which services are down
  - Which test cases are blocked
  - Options: fix environment / start services manually / terminate this cycle

### Failure Is Not Bypassable

- **Any test case execution failure** (step result ≠ expected, verification point unmet, post-check failure) blocks the feature from being marked `"passing"`
- Must report to user via `AskUserQuestion`:
  - Failed case ID(s)
  - Failed step number and details (actual vs expected)
  - Options: fix code and re-execute / modify test case via `/long-task:increment` / terminate this cycle
- **No bypass allowed** for any reason:
  - "Simple feature" — still needs test cases
  - "Environment temporarily unavailable" — BLOCKED, not skipped
  - "Test case might be wrong" — use `/long-task:increment` to modify, don't skip
- All failures MUST be recorded in `task-progress.md`

### Environment Cleanup

Worker handles cleanup in Step 14 (Continue) via `cleanup.sh` / `cleanup.ps1`. This skill does not manage cleanup directly.

## Critical Rules

- **Requirements-driven**: Test cases derive from SRS/Design, validating implementation against requirements — not duplicating unit test assertions
- **Complete after Quality Gates**: All test cases must be written, validated, and executed after TDD and quality gates pass
- **Immutable after generation**: Test case documents are written and executed in this step and not modified during Review. Changes require `/long-task:increment`
- **Traceability mandatory**: Every test case traces to a requirement; every verification_step traces to a test case
- **UI consolidation**: For UI features, this skill consolidates functional, UCD compliance, and accessibility testing into unified test cases
- **Template flexibility**: Users can override the default ISO/IEC/IEEE 29119 template with custom templates and style examples
