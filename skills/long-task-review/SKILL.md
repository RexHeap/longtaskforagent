---
name: long-task-review
description: "Use after quality gates pass in a long-task project - runs two-stage code review (spec compliance then code quality) before persisting"
---

# Two-Stage Code Review

Review runs after every feature, before Persist. No exceptions. Spec compliance gates code quality — no point polishing wrong code.

**Announce at start:** "I'm using the long-task-review skill to review this feature."

## When to Run

- After **every** feature passes quality gates
- Before the Persist phase (git commit)
- No exceptions — even "simple" features need at least Stage 1

## Stage 1: Spec Compliance

**Question**: Does the implementation do what the feature spec says?

Dispatch subagent with `skills/long-task-review/prompts/spec-reviewer-prompt.md`:

```
Task(
  subagent_type="general-purpose",
  prompt="""
  You are a spec compliance reviewer.
  Read the prompt at: skills/long-task-review/prompts/spec-reviewer-prompt.md

  Feature spec:
  {feature_json}

  Git diff:
  {diff_output}

  Test results:
  {test_summary}

  Perform the review following the prompt template.
  """
)
```

### Checklist (S1-S5)

| # | Check |
|---|-------|
| S1 | All `verification_steps` covered by tests |
| S2 | Tests verify behavior, not implementation details |
| S3 | No undocumented side effects |
| S4 | Edge cases from the spec are handled |
| S5 | Feature `description` matches actual behavior |

**Any NO → FAIL. Stage 2 is skipped. Fix gaps, re-run tests, re-review Stage 1.**

## Stage 2: Code Quality

**Question**: Is the implementation well-crafted?

Dispatch subagent with `skills/long-task-review/prompts/code-quality-reviewer-prompt.md`:

```
Task(
  subagent_type="general-purpose",
  prompt="""
  You are a code quality reviewer.
  Read the prompt at: skills/long-task-review/prompts/code-quality-reviewer-prompt.md

  Feature spec:
  {feature_json}

  Git diff (BASE_SHA..HEAD_SHA):
  {diff_output}

  Test results:
  {test_summary}

  Coverage report:
  {coverage_output}

  Mutation report:
  {mutation_output}

  Perform the review following the prompt template.
  """
)
```

### Checklist (Q1-Q12)

**Code Quality (Q1-Q6):**
| # | Check |
|---|-------|
| Q1 | Follows existing project patterns and conventions |
| Q2 | Error handling is appropriate (not excessive, not missing) |
| Q3 | No security vulnerabilities (input validation, no hardcoded secrets) |
| Q4 | No obvious performance issues |
| Q5 | Types used correctly (if applicable) |
| Q6 | YAGNI — no unnecessary features or abstractions |

**Test Quality (Q7-Q12):**
| # | Check |
|---|-------|
| Q7 | Tests are independent, deterministic, meaningful |
| Q8 | Low-value assertion ratio <= 20% |
| Q9 | Negative test ratio >= 40% |
| Q10 | Coverage meets thresholds (line >= 90%, branch >= 80%) |
| Q11 | Mutation score meets threshold (>= 80%) |
| Q12 | No surviving mutants without documented justification |

**Critical/Important NO in Q1-Q6 → FAIL. Issues in Q7-Q12 → listed as Important.**

## Dual Review (for `priority: "high"` or `"ui": true`)

For high-priority or UI features, dispatch **two independent subagents**:

- **Reviewer A**: Standard rubric (as above)
- **Reviewer B**: Adversarial framing — "Assume this code HAS bugs. Find them."

Controller merges results:
- Both must PASS
- Either FAIL takes precedence
- Conflicting findings → err on the side of the FAIL

## Issue Severity

| Severity | Response | Blocks? |
|----------|----------|---------|
| Critical | Fix immediately | Yes |
| Important | Fix before next feature | Yes |
| Minor | Fix in refactor or next session | No |

## Review Loop

```
Quality Gates Pass → Stage 1 (Spec Compliance)
                          ↓
                     PASS? → Stage 2 (Code Quality)
                     FAIL? → Fix → Re-test → Re-review Stage 1
                                      ↓
                                 PASS? → Feature complete
                                 FAIL? → Fix → Re-review (changed items only)
                                                  ↓
                                             Max 3 rounds → Escalate to user
```

After 3 failed rounds, escalate via `AskUserQuestion` with:
- All issues found across rounds
- What was tried and fixed
- What remains unresolved

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Skip review for "simple" features | Always run at least Stage 1 |
| Review quality before spec compliance | Stage 1 gates Stage 2 |
| Bundle multiple issues into one finding | One concern per issue |
| Performative agreement ("Great code!") | PASS or specific issues, no filler |
| Implement suggestions without checking YAGNI | Verify suggestion is actually needed |

## Integration

**Called by:** long-task-work (Step 10)
**Dispatches:** spec-reviewer subagent (`skills/long-task-review/prompts/spec-reviewer-prompt.md`), code-quality-reviewer subagent (`skills/long-task-review/prompts/code-quality-reviewer-prompt.md`)
**Requires:** Quality gates passed (long-task-quality)
**Produces:** Review verdict (PASS/FAIL with findings)
**Returns to:** long-task-work for Add Examples + Persist steps
