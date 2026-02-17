# Code Review Process

## Overview

Two-stage code review runs after each feature is implemented and tests pass. The review ensures both spec compliance and code quality before the feature is considered complete.

## When to Run

- After **every** feature is marked "passing" in `feature-list.json`
- Before the Persist phase (git commit)
- Triggered automatically in the Worker cycle

## Two-Stage Review

### Why Two Stages?

Reviewing spec compliance and code quality separately prevents a common failure mode: fixing style issues on code that doesn't meet the spec. Stage 1 (spec) gates Stage 2 (quality) — no point polishing wrong code.

### Stage 1: Spec Compliance

**Question**: Does the implementation do what the feature spec says?

Checklist:
- [ ] All `verification_steps` from the feature are covered by tests
- [ ] Tests verify behavior, not implementation details
- [ ] No undocumented side effects
- [ ] Edge cases from the spec are handled
- [ ] Feature description matches actual behavior

**If FAIL**: Fix gaps, re-run tests, re-review Stage 1 only.

### Stage 2: Code Quality

**Question**: Is the implementation well-crafted?

Checklist:
- [ ] Follows existing project patterns and conventions
- [ ] Error handling is appropriate (not excessive, not missing)
- [ ] No security vulnerabilities (input validation, no hardcoded secrets)
- [ ] No obvious performance issues
- [ ] Types used correctly (if applicable)
- [ ] Tests are independent, deterministic, and meaningful

**If issues found**: Fix by severity (Critical → Important → Minor), re-review changed items only.

## How to Dispatch the Review

### Option A: Self-Review (Default)

The implementing agent reviews its own work with a reviewer mindset:

1. Get the git diff: `git diff <commit-before-feature>..HEAD`
2. Re-read the feature spec from `feature-list.json`
3. Walk through Stage 1, then Stage 2
4. Document findings and fix issues

### Option B: Subagent Review (Recommended for complex features)

Dispatch a fresh subagent using the code-reviewer agent definition:

1. Record BASE_SHA before implementation: `git rev-parse HEAD`
2. After implementation + tests pass, record HEAD_SHA
3. Dispatch subagent with:
   - Feature spec (full JSON entry from `feature-list.json`)
   - Diff: `git diff <BASE_SHA>..HEAD`
   - Test results summary
4. Act on feedback by severity level
5. Re-dispatch reviewer for changed items if needed

```
# Dispatch example
Task(
  subagent_type="general-purpose",
  prompt="""
  You are a code reviewer. Read agents/code-reviewer.md for your review protocol.

  Feature spec:
  {feature_json}

  Git diff:
  {diff_output}

  Test results:
  {test_summary}

  Perform a two-stage review (spec compliance, then code quality).
  """
)
```

## Issue Severity and Response

| Severity | Response Time | Blocks Feature? |
|----------|--------------|-----------------|
| Critical | Fix immediately | Yes |
| Important | Fix before proceeding to next feature | Yes |
| Minor | Fix in refactor phase or next session | No |

## Review Loop

```
Implement → Tests Pass → Review Stage 1
                              ↓
                         PASS? → Review Stage 2
                         FAIL? → Fix → Re-test → Re-review Stage 1
                                          ↓
                                     PASS? → Feature complete
                                     FAIL? → Fix → Re-review (changed items only)
                                                      ↓
                                                 Max 3 rounds → escalate to user
```

## Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| Skip review for "simple" features | Simple features still have specs to comply with | Always run at least Stage 1 |
| Review code quality before spec compliance | May polish code that doesn't meet the spec | Stage 1 gates Stage 2 |
| Bundle multiple issues into one finding | Makes fixing and re-review harder | One concern per issue |
| Performative agreement ("Great code!") | Wastes tokens, doesn't improve quality | PASS or specific issues, no filler |
| Implement reviewer suggestions without checking YAGNI | May add unnecessary complexity | Verify suggestion is actually needed |
