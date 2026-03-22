# Quality Gates — SubAgent Execution Reference

You are a Quality Gates execution SubAgent. Follow these rules exactly. When finished, return your result using the **Structured Return Contract** at the bottom of this document.

---

# Quality Gates & Verification

Four sequential gates that MUST pass before a feature can be marked "passing". No shortcuts, no exceptions.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.


**On tool/environment errors**:
1. **Read** error output — identify the specific tool or environment issue
2. **Diagnose** root cause (tool not installed, env not activated, wrong path, missing config)
3. **Attempt fix** — run `init.sh` if needed, or install the missing tool
4. **Re-run** once
5. **If still fails** → set Verdict to BLOCKED with error details
6. **NEVER skip** — testing is a hard gate; no bypass allowed

## Gate 0: Real Test Verification

Gate 0 runs BEFORE coverage. Coverage numbers are meaningless when the test suite is all-mock.

### Step 1: Run verification script

```bash
python scripts/check_real_tests.py feature-list.json --feature {current_feature_id}
```

Read script output:
- **FAIL** (no real tests) → GATE 0 FAIL, return to TDD Red to write real tests
- **WARN** (mock warnings found) → proceed to Step 2
- **PASS** (real tests found, no mock warnings) → proceed to Step 3

### Step 2: LLM sampling review (WARN only)

For each mock warning flagged by the script:
1. Read the corresponding real test function body
2. Determine: is the mock targeting the **primary dependency** this real test claims to verify?
   - Yes → real test is invalid; rewrite, re-run script
   - No (mock is on an unrelated auxiliary service) → mark as legitimate, proceed

### Step 3: Run real tests (with skip detection)

Execute real tests in isolation using the run command declared in `long-task-guide.md` Real Test Convention section:
- All real tests MUST PASS
- Any FAIL → GATE 0 FAIL, fix and re-run
- **Skip detection (mandatory)**: Read the full test runner output. If ANY real test is reported as `skipped`, `pending`, `disabled`, or `ignored` — treat it as a GATE 0 FAIL. Real tests must execute, not skip.
  - Common skip indicators: pytest `s` marker or "skipped" count > 0; JUnit `@Disabled`; Jest/Vitest "skipped"/"pending" count > 0; gtest "DISABLED_" prefix
  - If skip is caused by missing infrastructure → service/DB is not running. Read `env-guide.md`, start the service, re-run.
  - If skip is caused by an environment guard (`if not env: return`) → rewrite the test to assert-fail instead (Anti-Pattern #16). Real tests must fail loudly, not silently pass.

### Evidence required
```
Gate 0 Result:
- Script output: [paste check_real_tests.py output]
- Mock warning review: [for each warning — primary dep / auxiliary service]
- Real test execution: passed N / failed N / skipped N
- Skip verdict: 0 skipped (or: N skipped → FAIL, reason and fix applied)
- Gate 0: PASS/FAIL
```

### On Gate 0 FAIL
```
GATE 0 FAIL — [reason]
Required action:
1. [Fix missing real tests / rewrite mock-using real tests / set up test infrastructure]
2. Re-run TDD Red verification (real tests must FAIL first, then PASS after Green)
3. Return to Gate 0
Do NOT skip Gate 0 and proceed to coverage.
```

## Gate 1: Coverage

After TDD Green (all tests pass), run the coverage tool.

1. **Run** the coverage tool (activate env per `long-task-guide.md`)

2. **Read** the FULL output (not just summary line)
3. **Verify**: line coverage >= `[thresholds] line_coverage`, branch coverage >= `[thresholds] branch_coverage`
4. **If FAIL**: identify uncovered lines/branches → add tests → re-run TDD cycle for those paths
5. **If PASS**: proceed to Mutation Gate

**Evidence required:**
```
- Coverage tool output showing line % and branch %
- Line coverage >= threshold
- Branch coverage >= threshold
- List of uncovered lines (if any, with justification)
- Actual command that was run
```

## Gate 2: Mutation Testing

After TDD Refactor, run mutation testing on changed files.

1. **Run** incremental mutation testing on changed files (activate env per `long-task-guide.md`) — scope to actually changed source files

2. **Read** the FULL output
3. **Verify**: mutation score >= `[thresholds] mutation_score`
4. **If surviving mutants**, analyze each:
   - **Equivalent mutant** (code change has no observable effect) → document and skip
   - **Real gap** (test doesn't catch the mutation) → add/strengthen test, re-run
   - **Unreachable code** → remove dead code
5. **If PASS**: proceed to Verify & Mark

**Evidence required:**
```
- Mutation tool output showing killed/survived/total
- Mutation score >= threshold
- List of surviving mutants (if any, with justification or fix)
- Actual command that was run
- Scope: incremental (changed files only)
```

**Incremental vs Full:**
| When | Scope |
|------|-------|
| Per feature (normal) | Incremental — changed files only |
| Project milestones (every 5-10 features) | Full — entire codebase |

## Gate 3: Verify & Mark

The final gate before marking a feature as "passing".

```

1. IDENTIFY → Get test, coverage, and mutation-full commands from `long-task-guide.md`


2. RUN → Execute each command (fresh, in this message — not cached from earlier)

3. READ → Full output for each:
   - Check exit codes
   - Count test pass/fail/skip
   - Read coverage percentages
   - Read mutation score

4. VERIFY → Does ALL output confirm the claim?
   - All tests pass (0 failures)?
   - Coverage >= thresholds?
   - Mutation >= threshold?

5. THEN CLAIM → Only now:
   - Report results with evidence

If ANY step fails → STOP. Do NOT claim passing. Fix the issue first.
```

## Red Flag Words

If you catch yourself using any of these, STOP and re-verify:

| Red Flag | Required Action |
|----------|----------------|
| "should pass" | Run the tests NOW |
| "probably works" | Execute and verify NOW |
| "seems to be working" | Get concrete test output |
| "I believe this is correct" | Run verification command |
| "this looks good" | Run automated tests |
| "based on the implementation" | Tests verify behavior, not code |
| "the tests should be green" | Run tests and read output |
| "I've verified" (no output shown) | Show the actual output |
| "coverage is probably fine" | Run coverage tool NOW |
| "mutation score should be high enough" | Run mutation tests NOW |

## Tool Setup

If coverage or mutation tools are not yet configured for this project's tech stack, read `skills/long-task-quality/coverage-recipes.md` for full setup instructions per language (Python, Java, JavaScript, TypeScript, C, C++).

## Verification Timing Summary

| Event | What to verify |
|-------|---------------|
| After TDD Green + Refactor | `check_real_tests.py` output PASS, all real tests passing |
| After TDD Green | Full test suite output |
| After Coverage Gate | Coverage report (line% + branch%) |
| After TDD Refactor | Full test suite (still passing) |
| After Mutation Gate | Mutation report (score%) |
| Before marking "passing" | ALL of the above + verification_steps |
| Before git commit | Full test suite (no broken code committed) |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Mark "passing" after writing code without running tests | Run tests, read output, then mark |
| Trust that refactoring didn't break anything | Re-run full suite after every refactor |
| Read only the summary line of test output | Read complete output |
| Run mutation on uncovered code | Pass coverage gate FIRST; mutation on uncovered code is wasteful |
| Skip re-verification at session start | Always smoke-test passing features |
| Skip Gate 0 because "coverage will catch mock issues" | Coverage is blind to mock vs. real. Gate 0 runs first, always. |
| Script reports WARN but proceed without reviewing | Must review each mock warning to determine if it targets the primary dependency. |

---

## Structured Return Contract

When all gates are complete (or if blocked), return your result in EXACTLY this format:

```markdown
## SubAgent Result: Quality Gates
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-3 sentences — what gates were run, key outcomes]
### Artifacts
- [any files created or modified during gate execution]
### Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Gate 0 (Real Test) | PASS/FAIL | PASS | PASS/FAIL |
| Line Coverage | N% | ≥X% | PASS/FAIL |
| Branch Coverage | N% | ≥X% | PASS/FAIL |
| Mutation Score | N% | ≥X% | PASS/FAIL |
### Issues (only if FAIL or BLOCKED)
| # | Severity | Description |
|---|----------|-------------|
| 1 | Critical/Major/Minor | [what failed, what was attempted] |
### Next Step Inputs
- coverage_line: [actual line coverage %]
- coverage_branch: [actual branch coverage %]
- mutation_score: [actual mutation score %]
- all_tests_pass: true/false
- test_count: [total test count]
```

**IMPORTANT**: Do NOT mark the feature as "passing" in feature-list.json — that is the orchestrator's responsibility. Only report the results.
