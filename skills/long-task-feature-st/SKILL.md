---
name: long-task-feature-st
description: "Use after quality gates pass in a long-task project — independently manages test environment lifecycle (start/cleanup), executes black-box acceptance testing per feature via Chrome DevTools MCP, generates ISO/IEC/IEEE 29119 compliant test case documents"
---

# Feature-Level Black-Box Acceptance Testing

Execute black-box acceptance testing for a completed feature **after** TDD implementation and quality gates pass. This skill independently manages its own environment lifecycle (start → test → cleanup) and generates ISO/IEC/IEEE 29119 compliant test case documents.

**Announce at start:** "I'm using the long-task-feature-st skill to run black-box acceptance testing for this feature."

## Standard

Default: **ISO/IEC/IEEE 29119-3** (Test Documentation).

Users may override the template and style via `feature-list.json` root fields:
- `st_case_template_path` — custom template file (defines structure)
- `st_case_example_path` — example file (defines style, language, detail level)

## When to Run

- After **every** feature's Quality Gates step (Worker Step 9), before Review (Worker Step 11)
- No exceptions — even "simple" features need acceptance test case documentation
- Invoked by `long-task-work` as a sub-skill (not directly by router)

## Black-Box Testing Philosophy

TDD (long-task-tdd) has already verified the implementation from the inside:
unit tests exercise code paths; coverage and mutation gates verify completeness.

This skill verifies from the **outside** — as a user or external system would:
- Inputs go in through the real interface (HTTP endpoints, UI, CLI args)
- Outputs observed through the real interface (HTTP responses, rendered UI, stdout)
- Internal implementation is NOT consulted during test design or execution
- Chrome DevTools MCP is the primary execution environment for UI features

**Rule:** If a test case requires reading source code to determine the expected result, it is not a black-box test — rewrite it using only the SRS specification.

## Service Management

Manage services directly — no wrapper scripts. The `.claude/hooks/pre_bash_port_guard.py` hook automatically kills conflicting processes before any server-start command.

### Start (before first test case)

1. **Check if services are running**: Verify the health endpoint (HTTP GET or port check)
2. **If not running**: Start services directly using commands from `long-task-guide.md`:
   - The port-guard hook fires automatically and clears any conflicting ports first
   - Example: `uvicorn main:app --port 8000 &` (Python) or `npm run dev &` (Node)
   - Wait for health endpoint to respond (use `wait_for` MCP tool for UI, or `curl` for API)
3. **If start fails**: Diagnose root cause (check logs, verify environment activation, check `.env`)
   - If unresolvable: report to user via `AskUserQuestion`; do NOT proceed
4. **Record service info**: Note ports and process info in `task-progress.md`

### Cleanup (after all test cases complete) — MANDATORY

1. **Stop services**: Kill the processes started above (by PID recorded in task-progress.md, or by port)
   - By PID: `kill <pid>` (Unix) or `taskkill /F /PID <pid>` (Windows)
   - By port: use `python scripts/port_guard_hook_template.py` locally, or find PID via `netstat -ano | grep <port>` (Windows) / `lsof -i :<port>` (Unix)
2. **Verify cleanup**: confirm ports are released (health endpoint no longer responds)
3. **Record cleanup result**: Note cleanup status in `task-progress.md`

**Why mandatory**: Leaving services running causes port conflicts in subsequent ST cycles.

### Fix-and-Retest Protocol

When a test case fails and code is fixed:
1. Kill the currently running service (by PID or port)
2. Start fresh (port-guard hook clears any stale processes automatically)
3. Re-execute the failed test cases from the beginning of the affected scenario

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
- **Interface contracts** — API endpoints, CLI commands, UI entry points that form the observable surface of this feature
- **Test results summary** — from TDD and Quality Gates (coverage %, mutation score)

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

### 2b. Load Chrome DevTools Execution Protocol (for `"ui": true` features)

If the target feature has `"ui": true`, read `prompts/e2e-scenario-prompt.md`. This provides mandatory rules for generating Chrome DevTools MCP-executable E2E test scenarios. Apply these rules during Step 3 for all UI and A11Y category test cases.

**Why**: Without this prompt, UI test cases tend to be simple page-load checks. The prompt ensures each test step maps to a concrete MCP tool call (navigate_page, click, fill, take_snapshot, evaluate_script, list_console_messages) and follows the three-layer detection model. Chrome DevTools MCP is the **primary** testing vehicle for UI features in this skill.

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

**Acceptance-level focus:** Test cases confirm the implementation matches requirements from a user/system perspective — not duplicating unit test assertions. Focus on behavioral scenarios, integration paths, and end-to-end workflows.

**Black-box constraint:** Expected results must be derivable solely from the SRS (verification_steps, Given/When/Then, NFR thresholds) and the observable interface. If the expected result cannot be determined without reading implementation code, raise it as a specification gap via `AskUserQuestion`.

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
- The test step table becomes a **script** that can be mechanically translated into Chrome DevTools MCP calls
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

**HARD REQUIREMENT: Must execute test cases one by one as defined in `docs/test-cases/feature-{id}-{slug}.md`**
- Each test case must be executed individually and results recorded
- No test case may be skipped
- Do not merge or simplify the test case execution process
- **UI test cases MUST use Chrome DevTools MCP for verification**

1. **Start services** per Service Management above (port-guard hook ensures clean ports)
2. For **non-UI test cases**: verify by running relevant test commands or manual checks against the running system
3. For **UI test cases**: execute via Chrome DevTools MCP following the step tables
4. Update the traceability matrix `结果` column to `PASS` or `FAIL` for each case
5. **Stop services** per Service Management cleanup above

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

### Environment Gate

Always start from a known-clean state. Do not assume services are already running.

- Start services per Service Management above; verify health endpoint before running any test cases
- If service fails to start after diagnosis: **BLOCKED** — report to user via `AskUserQuestion` with service details and options (fix/start manually/terminate)
- After start: verify app is responding before running any test cases

### Failure Is Not Bypassable

- **Any test case execution failure** blocks the feature from being marked `"passing"`
- Must report to user via `AskUserQuestion`:
  - Failed case ID(s), failed step number, actual vs expected
  - Options: fix code and re-execute / modify test case via `/long-task:increment` / terminate
- **No bypass allowed** for any reason:
  - "Simple feature" — still needs test cases
  - "Environment temporarily unavailable" — BLOCKED, not skipped
  - "Test case might be wrong" — use `/long-task:increment` to modify, don't skip
- All failures MUST be recorded in `task-progress.md`

## Critical Rules

- **Requirements-driven**: Test cases derive from SRS/Design, validating implementation against requirements — not duplicating unit test assertions
- **Black-box only**: Expected results must be derivable from SRS and the observable interface alone — no reading implementation code
- **Complete after Quality Gates**: All test cases must be written, validated, and executed after TDD and quality gates pass
- **Immutable after generation**: Test case documents are written and executed in this step and not modified during Review. Changes require `/long-task:increment`
- **Traceability mandatory**: Every test case traces to a requirement; every verification_step traces to a test case
- **UI consolidation**: For UI features, this skill consolidates functional, UCD compliance, and accessibility testing into unified test cases
- **Template flexibility**: Users can override the default ISO/IEC/IEEE 29119 template with custom templates and style examples

## Integration

**Called by:** `long-task-work` (Step 10)
**Requires:** Quality Gates passed (long-task-quality Step 9 complete)
**Produces:** `docs/test-cases/feature-{id}-{slug}.md` with executed results
**Chains to:** `long-task-review` (Worker Step 11)
