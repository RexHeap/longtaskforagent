---
name: long-task-st
description: "Use when all features in feature-list.json are passing - run comprehensive system testing before release, aligned with IEEE 829 and ISTQB best practices"
---

# System Testing — Integrated Verification Before Release

Run comprehensive system-level testing after all features are implemented and passing. Verifies the integrated system against the full SRS — including cross-feature interactions, end-to-end workflows, non-functional requirements, and exploratory testing.

**Announce at start:** "I'm using the long-task-st skill. All features are passing — time for system testing."

**Core principle:** Feature-level tests prove parts work in isolation. System testing proves the whole works together.

<HARD-GATE>
Do NOT skip any applicable test category. A "Go" verdict requires evidence from EVERY category that applies to this project. "It probably works" is not evidence.
</HARD-GATE>

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

### 1. ST Readiness Gate
```bash
python scripts/check_st_readiness.py feature-list.json
```
Verify preconditions:
- All features in `feature-list.json` have `"status": "passing"` — if any are failing, invoke `long-task:long-task-work` instead
- SRS document exists (`docs/plans/*-srs.md`)
- Design document exists (`docs/plans/*-design.md`)

Then orient:
- Load `.env` if it exists
- Run `start.sh` / `start.ps1` — ensure all runtime services are up for ST
  - If `start.sh` does not exist: skip (project may be CLI/library only)
  - If `start.sh` fails: STOP. Record failure in `task-progress.md`. Ask user to start services manually. ST cannot proceed without a running environment.
- Read `feature-list.json` — note `tech_stack`, `quality_gates`, `constraints[]`, `assumptions[]`
- Read SRS document — extract all FR-xxx, NFR-xxx, IFR-xxx, CON-xxx requirements
- Read design document — extract architecture, API design, testing strategy (section 9), third-party dependencies (section 8)
- If UI features exist and UCD doc exists (`docs/plans/*-ucd.md`), read UCD style guide
- Read SRS **Stakeholders & User Personas** section and **Glossary** section (`docs/plans/*-srs.md`) — needed for E2E scenario derivation and exploratory testing
- Read `task-progress.md` — session history context

### 2. ST Plan
Create `docs/plans/YYYY-MM-DD-st-plan.md` with:

#### 2a. Test Scope
Determine which test categories apply based on project characteristics:

| Category | Applies When | Skip When |
|----------|-------------|-----------|
| Regression | Always | Never |
| Integration | 2+ features with shared data/state/APIs | Single isolated feature |
| E2E Scenarios | SRS has multi-step user workflows | Pure library/utility projects |
| Performance | SRS has NFR-xxx with response time / throughput / resource targets | No performance NFRs |
| Security | SRS has security NFRs OR project handles user input / auth / external data | Isolated offline tools |
| Accessibility | UI features exist (`"ui": true`) | No UI features |
| Compatibility | SRS specifies platform / browser / runtime targets | Single-platform CLI tools |
| Exploratory | Always | Never |

#### 2b. Requirements Traceability Matrix (RTM)
Map EVERY requirement from SRS to ST test approach:

```markdown
| Req ID | Requirement | ST Category | Test Approach | Priority |
|--------|-------------|-------------|---------------|----------|
| FR-001 | ... | E2E | Scenario: ... | High |
| NFR-001 | ... | Performance | Benchmark: ... | Critical |
| IFR-001 | ... | Integration | Contract test: ... | High |
```

Every FR-xxx, NFR-xxx, IFR-xxx must appear in the RTM. Requirements without a test approach = **gap**.

#### 2c. Test Environment
- Required infrastructure (servers, databases, external services)
- Test data strategy (fixtures, seeds, mocks for external services)
- Environment variables from `.env`

#### 2d. Entry / Exit Criteria

**Entry criteria** (must ALL be true before testing begins):
- All features passing (`check_st_readiness.py` returns 0)
- Test environment is provisioned and accessible
- All required configs are present (`.env` loaded)

**Exit criteria** (must ALL be true for Go verdict):
- All regression tests pass
- All integration tests pass
- All E2E scenarios pass
- All NFR thresholds met with measured evidence
- No Critical or Major defects open
- RTM shows 100% requirement coverage

#### 2e. Risk-Based Prioritization
Order test execution by risk:
1. **Critical path** — core user workflows, highest business impact
2. **Integration boundaries** — cross-feature data flows, API contracts
3. **NFR thresholds** — performance, security (highest technical risk)
4. **Edge cases** — boundary conditions, error recovery
5. **Compatibility** — platform/browser variations

### 3. Regression Testing
Run the full project test suite and verify system-wide health:

1. Run all unit tests:
   ```bash
   # Use tech_stack.test_framework command from get_tool_commands.py
   python scripts/get_tool_commands.py feature-list.json
   ```
2. Verify ALL tests pass — zero failures, zero errors
3. Run coverage tool — verify line and branch coverage thresholds are met project-wide (not per-feature)
4. Check for new warnings, deprecation notices, or dependency conflicts
5. If any failure → **STOP** — this is a regression. Diagnose before proceeding.

**Record in ST report:**
- Total tests: N, Passed: N, Failed: N, Skipped: N
- Line coverage: X% (threshold: Y%)
- Branch coverage: X% (threshold: Y%)

### 4. Integration Testing
Test cross-feature interactions. Read `references/st-recipes.md` for language-specific patterns.

For each pair of features that share data, state, or API boundaries:

#### 4a. Data Flow Testing
- Feature A produces data → Feature B consumes it → verify data integrity end-to-end
- Shared database/state consistency under concurrent-like access patterns
- File I/O: Feature A writes → Feature B reads → verify format and content

#### 4b. API Contract Testing
- Internal API calls between modules: verify request/response schemas match
- Error propagation: when Feature A fails, does Feature B handle it correctly?
- Version compatibility: if modules have independent versioning

#### 4c. Dependency Chain Validation
- Walk the `dependencies[]` graph in `feature-list.json`
- For each dependency edge: verify the dependent feature works correctly when its dependency is in expected states
- Test initialization order: features must work when bootstrapped in dependency order

**Write integration tests** in a dedicated directory (e.g., `tests/integration/` or `tests/st/`).
Run them and record results.

### 5. E2E Scenario Testing
Test complete user workflows from SRS acceptance criteria (Given/When/Then).

#### 5a. Scenario Derivation
For each user persona in the SRS Stakeholders section:
- Extract the persona's primary workflows from SRS
- Create E2E scenarios that span multiple features
- Include both happy path and error recovery

#### 5b. Scenario Execution
For each E2E scenario:
1. Set up initial state (test fixtures)
2. Execute the full workflow step-by-step
3. Verify intermediate states AND final outcome
4. Clean up test state

#### 5c. UI E2E Testing (only if `"ui": true` features exist)
Use Chrome DevTools MCP tools:
1. `navigate_page` to the entry URL (`ui_entry` from feature)
2. `take_snapshot` to capture page state
3. Execute user interactions (`click`, `fill`, `press_key`)
4. Verify visual outcomes via `take_screenshot` and `take_snapshot`
5. Check console for errors via `list_console_messages`
6. Verify network requests via `list_network_requests`

**Write E2E tests** in `tests/e2e/` or `tests/st/`.
Run them and record results.

### 6. NFR Verification
For each NFR-xxx in the SRS, verify with **measured evidence** — not estimates.

#### 6a. Performance
- **Response time**: measure p50, p95, p99 under expected load
- **Throughput**: measure requests/operations per second
- **Resource usage**: measure memory, CPU, disk I/O
- **Tools**: see `references/st-recipes.md` for language-specific benchmarking tools
- **Record**: measured value vs SRS threshold, PASS/FAIL

#### 6b. Security
- **Input validation audit**: review all user-facing inputs for injection risks (SQL, XSS, command injection, path traversal)
- **Authentication/authorization**: verify auth flows, session management, privilege escalation resistance
- **Dependency vulnerabilities**: run dependency scanner (npm audit, pip-audit, cargo-audit, etc.)
- **OWASP Top 10 checklist**: systematically check each applicable category
- **Secrets handling**: verify no secrets in code, logs, or error messages
- **Record**: per-check PASS/FAIL with evidence

#### 6c. Accessibility (only if UI features exist)
- **WCAG 2.1 AA compliance**: run automated accessibility scanner
- **Keyboard navigation**: verify all interactive elements are reachable via keyboard
- **Screen reader compatibility**: verify semantic HTML and ARIA attributes
- **Color contrast**: verify against WCAG minimum contrast ratios
- **Tools**: axe-core, pa11y, Lighthouse accessibility audit
- **Record**: per-criterion PASS/FAIL

#### 6d. Scalability (if SRS specifies load targets)
- Run load tests at 1x, 2x, 5x expected load
- Measure degradation curve
- Identify bottlenecks
- **Record**: performance at each load level vs SRS target

#### 6e. Reliability
- Error handling: verify all error paths produce meaningful messages
- Graceful degradation: verify system behavior when dependencies are unavailable
- Data integrity: verify no data corruption under error conditions
- **Record**: per-scenario PASS/FAIL

### 7. Compatibility Testing
Skip if SRS does not specify platform/browser/runtime targets.

#### 7a. Cross-Browser (UI projects only)
For each target browser in SRS:
- Run E2E scenarios
- Verify visual consistency via screenshots
- Check for browser-specific errors in console

#### 7b. Cross-Platform
For each target platform (Windows, macOS, Linux):
- Verify build and install process
- Run full test suite
- Verify platform-specific behavior (file paths, line endings, permissions)

#### 7c. Runtime Version Compatibility
For each target runtime version from design doc:
- Run full test suite
- Verify no version-specific API issues

**Record**: per-platform/browser PASS/FAIL matrix.

### 8. Exploratory Testing
Charter-based, time-boxed sessions to find issues that scripted tests miss.

#### 8a. Charter Creation
Create one charter per major feature area:
```
Charter: Explore [feature area]
         with [technique: stress/edge/abuse/workflow variation]
         to discover [bugs/usability issues/undocumented behavior]
```

#### 8b. Session Execution
For each charter:
1. Time-box: 15-30 minutes per charter
2. Follow intuition — try unexpected inputs, unusual sequences, rapid interactions
3. Log observations in real-time:
   - **Bug**: unexpected behavior (classify severity)
   - **Question**: requirement ambiguity discovered
   - **Note**: observation worth documenting

#### 8c. Session Debrief
After all charters:
- Consolidate findings
- Cross-reference with RTM — does any finding reveal a requirement gap?
- Add new defects to triage queue

### 9. Defect Triage
If ANY defects were found in Steps 3-8:

#### 9a. Classification
For each defect:
| Severity | Definition | Action |
|----------|-----------|--------|
| **Critical** | System crash, data loss, security breach | BLOCK release — fix immediately |
| **Major** | Core workflow broken, NFR threshold failed | BLOCK release — fix before release |
| **Minor** | Non-core functionality affected, workaround exists | Document — fix-now or defer (decide with user) |
| **Cosmetic** | Visual/text issue, no functional impact | Document — defer to next release |

#### 9b. Fix Loop (if Critical/Major defects exist)
1. For each Critical/Major defect:
   - Identify the affected feature(s)
   - Mark affected features `"status": "failing"` in `feature-list.json`
   - Document defect in `task-progress.md`
2. **Invoke `long-task:long-task-work`** to fix — Worker will pick up failing features
3. After fixes: re-run affected ST test categories (not full ST)
4. Return to Defect Triage — repeat until no Critical/Major defects remain

#### 9c. Deferred Defects
For Minor/Cosmetic defects the user chooses to defer:
- Document in ST report with severity, description, and workaround
- Create tracking entries (if project uses issue tracker)

### 10. ST Report
Before writing, verify completeness:
- Every FR-xxx, NFR-xxx, IFR-xxx, CON-xxx from SRS appears in the RTM
- Every NFR has a measured value (not estimate) that meets the SRS threshold
- Every applicable test category (Step 2a) has execution results
- All defects are classified with severity and status

Generate `docs/plans/YYYY-MM-DD-st-report.md`:

```markdown
# System Testing Report — <project-name>

**Date**: YYYY-MM-DD
**SRS**: [link to SRS doc]
**Design**: [link to design doc]
**Verdict**: Go / No-Go / Conditional-Go

## 1. Executive Summary
[1-3 sentences: overall system quality assessment and release recommendation]

## 2. Requirements Traceability Matrix

| Req ID | Requirement | ST Category | Test Result | Evidence |
|--------|-------------|-------------|-------------|----------|
| FR-001 | ... | E2E | PASS | [test name / log reference] |
| NFR-001 | ... | Performance | PASS (measured: 150ms, threshold: 200ms) | [benchmark report] |

**Coverage**: X/Y requirements tested (Z%)
**Untested**: [list any gaps with justification]

## 3. Test Execution Summary

| Category | Tests | Passed | Failed | Skipped | Notes |
|----------|-------|--------|--------|---------|-------|
| Regression | N | N | 0 | 0 | |
| Integration | N | N | 0 | 0 | |
| E2E Scenarios | N | N | 0 | 0 | |
| NFR: Performance | N | N | 0 | 0 | |
| NFR: Security | N | N | 0 | 0 | |
| NFR: Accessibility | N | N | 0 | N/A | |
| Compatibility | N | N | 0 | N/A | |
| Exploratory | N charters | — | — | — | [X bugs, Y questions found] |

## 4. Defect Summary

| # | Severity | Category | Description | Status | Fix Reference |
|---|----------|----------|-------------|--------|---------------|
| 1 | ... | ... | ... | Fixed / Deferred | [commit/PR] |

**Total**: X found, Y fixed, Z deferred
**Open Critical/Major**: 0 (required for Go)

## 5. Quality Metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Line coverage | X% | Y% | PASS/FAIL |
| Branch coverage | X% | Y% | PASS/FAIL |
| Mutation score | X% | Y% | PASS/FAIL |
| Total test count | N | — | — |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [Residual risk 1] | Low/Med/High | Low/Med/High | [What was done] |

## 7. Recommendations
[Action items for post-release monitoring, known limitations, suggested improvements]
```

### 11. Persist
- Git commit ST artifacts (`docs/plans/*-st-plan.md`, `docs/plans/*-st-report.md`, test files)
- Update `RELEASE_NOTES.md` — add ST completion entry
- Update `task-progress.md` with ST session entry
- Validate:
  ```bash
  python scripts/validate_features.py feature-list.json
  ```
- Run `cleanup.sh` / `cleanup.ps1` if it exists — clean up runtime services after ST is complete

### 12. Verdict
Present the ST report summary and Go/No-Go recommendation to the user via `AskUserQuestion`:
- **Go**: All exit criteria met, no open Critical/Major defects, RTM 100% covered
- **Conditional-Go**: Minor/Cosmetic defects deferred, all critical paths verified
- **No-Go**: Open Critical/Major defects, NFR thresholds not met, or RTM gaps

## Scaling ST to Project Size

| Project Size | Features | ST Depth |
|---|---|---|
| Tiny (1-5) | 1-5 features | Regression + lightweight integration + 2-3 E2E scenarios + 1-2 exploratory charters |
| Small (5-15) | 5-15 features | Full regression + integration per shared boundary + E2E per persona + NFR spot-checks + 3-5 charters |
| Medium (15-50) | 15-50 features | Full regression + systematic integration + comprehensive E2E + full NFR verification + compatibility matrix + 5-10 charters |
| Large (50+) | 50+ features | Full regression + integration test suite + E2E automation + full NFR load testing + full compatibility + security audit + 10+ charters |

## Critical Rules

- **Readiness gate first** — never start ST with failing features
- **Evidence-based verdicts** — every PASS must have measured evidence; "it looks OK" is not evidence
- **RTM completeness** — every SRS requirement must appear in the RTM; gaps are findings
- **NFR thresholds are hard gates** — measured value must meet SRS threshold, not "close enough"
- **Defect severity is non-negotiable** — Critical/Major defects block release; no exceptions
- **Re-test after fix** — never assume a fix works; re-run affected test categories
- **Exploratory testing is mandatory** — scripted tests cannot find everything
- **ST report before verdict** — document first, then decide; never skip the report
- **No new features during ST** — ST tests the integrated system as-is; scope creep breaks isolation

## Red Flags

| Rationalization | Correct Action |
|---|---|
| "All features pass, so the system works" | Feature tests prove parts, not the whole. Run ST. |
| "Integration testing is overkill for this" | If 2+ features share state, integration tests are mandatory. |
| "Performance is probably fine" | Measure it. "Probably" is not evidence. |
| "Security doesn't apply to this project" | Every project handling user input needs security checks. |
| "Exploratory testing won't find anything" | It always does. Run the charters. |
| "This defect is minor, let's ship" | Classify per severity table. Only Minor/Cosmetic can defer. |
| "We already tested this during development" | Feature-level tests ≠ system-level tests. Different scope. |
| "Let me quickly fix this before documenting" | Document the defect FIRST. Then fix via Worker loop. |
| "NFR is close to the threshold" | Close is not met. Optimize until the threshold is achieved. |
| "Skip compatibility, we only target one platform" | Verify SRS platform requirements. If only one target, test that one. |

## On Error

Follow the systematic debugging process:
1. Collect evidence (test output, logs, screenshots)
2. Reproduce the issue
3. Classify: is this a test environment issue or a genuine defect?
4. If genuine defect → add to Defect Triage (Step 9)
5. If test environment issue → fix environment, re-run
6. Escalate to user after 3 failed attempts

## Integration

**Called by:** using-long-task (when feature-list.json exists AND all features passing), or long-task-work (Step 13 when no failing features remain)
**Reads:** feature-list.json, `docs/plans/*-srs.md`, `docs/plans/*-design.md`, `docs/plans/*-ucd.md` (if UI), `task-progress.md`, `.env`
**May invoke:** `long-task:long-task-work` (if Critical/Major defects found → fix loop)
**Produces:** `docs/plans/YYYY-MM-DD-st-plan.md`, `docs/plans/YYYY-MM-DD-st-report.md`
**Read on-demand (via Read tool, NOT Skill tool):** `references/st-recipes.md`
