# Verification Enforcement

## Iron Law

**NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.**

Never say a feature "works", "passes", or "is done" unless you have just run the verification and read the output.

## The Verification Gate

Before marking ANY feature as `"passing"`, execute this exact sequence:

```
1. IDENTIFY  → What proof is needed? (test command, URL check, output comparison)
2. EXECUTE   → Run the actual command / test / check
3. READ      → Read the complete output (not just the last line)
4. VERIFY    → Does the output match expectations? All tests green? No errors?
5. THEN CLAIM → Only now update status to "passing"
```

**If any step fails → STOP. Do NOT mark as passing. Fix the issue first.**

## Red Flag Words

If you catch yourself using any of these words about feature status, STOP and re-verify:

| Red Flag | What It Signals | Required Action |
|----------|----------------|-----------------|
| "should pass" | Haven't actually run the tests | Run the tests now |
| "probably works" | Guessing, not verifying | Execute and verify |
| "seems to be working" | Vague observation, not evidence | Get concrete test output |
| "I believe this is correct" | Assertion without proof | Run verification command |
| "this looks good" | Visual inspection, not execution | Run automated tests |
| "based on the implementation" | Trusting code, not tests | Tests verify behavior, not code |
| "the tests should be green" | Predicting, not observing | Run tests and read output |
| "I've verified" (without showing output) | Claiming without evidence | Show the actual output |

## Verification Evidence Requirements

### For Unit Tests
```
Required evidence: Full test runner output showing:
- Number of tests run
- Number passed / failed / skipped
- 0 failures
- Actual command that was run
```

### For Chrome DevTools MCP Functional Tests
```
Required evidence:
- take_snapshot() output showing expected elements
- Screenshot showing expected visual state
- list_console_messages() showing no errors
- Actual interaction results (click/fill responses)
```

### For API Endpoints
```
Required evidence:
- Actual HTTP response status code
- Response body content
- Error case responses
```

### For Build / Compile
```
Required evidence:
- Build command output
- Exit code 0
- No warnings treated as errors
```

## Verification Timing

| Event | Verification Required |
|-------|----------------------|
| After TDD Green (all tests pass) | Full test suite output |
| After TDD Refactor | Full test suite output (confirm still passing) |
| Before marking "passing" | Feature-specific verification_steps executed |
| Before code review | Re-run tests to ensure clean state |
| Session start (smoke test) | Re-verify previously passing features |
| Before git commit | Full test suite (no broken code committed) |

## Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| Mark "passing" after writing code (without running tests) | Code may have syntax errors, logic bugs, or missing imports | Run tests, read output, then mark |
| Trust that refactoring didn't break anything | Refactoring can introduce subtle bugs | Re-run full suite after every refactor |
| Skip re-verification at session start | Previously passing features may have regressed | Always smoke-test passing features |
| Read only the summary line of test output | May miss individual test failures or warnings | Read the complete output |
| Verify only the happy path | Edge cases and error paths may be broken | Run ALL verification_steps, including error scenarios |
