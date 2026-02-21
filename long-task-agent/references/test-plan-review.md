# Test Plan Review

## Purpose

A dedicated quality gate for test suites, executed **after TDD Red and before TDD Green**. Ensures tests are complete, meaningful, and independent before any implementation code is written.

This phase addresses three LLM-specific failure modes:
1. **Circular reasoning** — same LLM writes tests and implementation, embedding shared blind spots
2. **Happy path bias** — LLMs naturally favor positive scenarios, underrepresenting error/boundary tests
3. **Low-value assertions** — LLMs generate tests that pass for almost any implementation

## When It Runs

```
Config Gate → DevTools Gate → Plan → TDD Red
                                        ↓
                              ★ Test Plan Review ★  ← HERE (hard gate)
                                        ↓
                                    TDD Green → Coverage Gate → ...
```

**Hard gate**: FAIL blocks TDD Green. No implementation code may be written until the test suite passes review.

## Who Executes It

**Independent subagent** — never self-review. The reviewer:
- Has NOT seen any implementation code (only feature spec + test code + test run output)
- Uses adversarial framing (find issues first, then decide)
- Follows a structured scoring rubric (not free-text judgment)

## Review Process

### Step 1: Find Issues First (Mandatory)

The reviewer must identify **at least 3 potential issues** with the test suite before making any verdict decision. This counteracts the LLM helpfulness bias that leads to premature PASS verdicts.

For each issue:
- What could go wrong
- Under what conditions it would manifest
- Severity if it occurred

If the reviewer genuinely cannot find 3 real issues, they must list 2 real issues + 1 area where additional test coverage would strengthen confidence.

### Step 2: Challenge Own Findings

For each issue from Step 1:
- **Real issue** → Keep, classify as Critical/Important/Minor
- **False positive** → Explain why with evidence from the test code
- This prevents over-reporting while maintaining thoroughness

### Step 3: Fill Scoring Rubric

Complete the structured rubric below with binary YES/NO answers and evidence citations.

### Step 4: Compute Verdict

Verdict is **computed from the rubric**, not a subjective decision. The reviewer cannot override the computation.

## Structured Scoring Rubric

```markdown
## Test Plan Review — Feature #{{FEATURE_ID}}: {{FEATURE_TITLE}}

### Issues Found (Step 1-2)

| # | Issue | Real/False Positive | Severity | Evidence |
|---|-------|-------------------|----------|----------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

### A. Scenario Completeness

| # | Check | YES/NO | Evidence |
|---|-------|--------|----------|
| A1 | Happy path scenarios present and test specific outcomes? | | |
| A2 | Error/failure scenarios present (invalid input, missing data, unauthorized)? | | |
| A3 | Boundary/edge case scenarios present (empty, max, zero, special chars)? | | |
| A4 | Negative test ratio >= 40% of total test functions? | | Count: __ negative / __ total = __% |

### B. Assertion Quality

| # | Check | YES/NO | Evidence |
|---|-------|--------|----------|
| B1 | Zero tests that ONLY assert None/isinstance/import? | | |
| B2 | Low-value assertion ratio <= 20% of total assertions? | | Count: __ low-value / __ total = __% |
| B3 | Each test asserts specific observable outcomes (values, state changes)? | | |
| B4 | No test recalculates expected value using the same algorithm as the implementation would? | | |

### C. Test Independence

| # | Check | YES/NO | Evidence |
|---|-------|--------|----------|
| C1 | Tests assert behavior (outputs/state), not implementation details (method calls)? | | |
| C2 | At least 2 plausible wrong implementations would FAIL these tests? | | Wrong impl 1: __ ; Wrong impl 2: __ |
| C3 | No shared mutable state between tests (each test is independent)? | | |

### D. UI Checks (if feature has ui=true — skip if not applicable)

| # | Check | YES/NO | Evidence |
|---|-------|--------|----------|
| D1 | Every [devtools] step uses EXPECT/REJECT format? | | |
| D2 | Automated UI error detection script (evaluate_script) included in test flow? | | |
| D3 | Console error check (list_console_messages) included? | | |
| D4 | Cross-page state verified for multi-page flows? | | |

### Verdict

**Rule**: Any NO in sections A-C → FAIL. Any NO in section D (when applicable) → FAIL.

The reviewer CANNOT override this rule. A single NO means FAIL, regardless of the reviewer's overall impression.

**Verdict**: PASS / FAIL

**If FAIL — required actions**:
- [List specific items to fix, referencing rubric items]
```

## Review Loop

```
TDD Red → Tests Written (all FAIL)
  ↓
Dispatch Test Plan Reviewer (subagent)
  ↓
PASS? → Proceed to TDD Green
FAIL? → Fix test suite → Re-dispatch reviewer (round 2)
         ↓
     PASS? → Proceed to TDD Green
     FAIL? → Escalate to user (ask for guidance)
```

**Maximum 2 review rounds**. If the test suite still fails after 2 rounds, escalate to the user via `AskUserQuestion` with:
- The rubric with failing items
- What was tried in each round
- Request for guidance on which items to prioritize

## Dispatch Pattern

```python
Task(
  subagent_type="general-purpose",
  prompt="""
  You are a test plan reviewer. Read the prompt at:
  <skill-dir>/agents/prompts/test-plan-reviewer-prompt.md

  Feature spec:
  {feature_json}

  Test code:
  {test_code}

  Test run output (should all FAIL):
  {test_run_output}

  Perform the review following the 4-step process in the prompt.
  """
)
```

## The "Wrong Implementation" Challenge

The most important check in the rubric is **C2**: the reviewer must imagine plausible wrong implementations and verify the tests would catch them.

**Why this matters for LLM-generated tests**: When the same model writes tests and implementation, it may embed the same assumptions in both. The reviewer (a fresh subagent) breaks this cycle by testing from a different perspective.

**How to apply**:

1. Read the feature description (what the code should do)
2. Imagine 2-3 wrong implementations:
   - Returns hardcoded value instead of computing
   - Swaps two fields
   - Off-by-one error
   - Skips a validation step
   - Returns stale data
3. For each, mentally run the test suite: would it catch the bug?
4. If most tests would pass despite the wrong implementation → C2 = NO → FAIL

## Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Response |
|---|---|---|
| Self-reviewing test suite | Same LLM has same blind spots | Always dispatch independent subagent |
| Giving PASS without filling rubric | Skips systematic evaluation | Rubric is mandatory; verdict is computed |
| Accepting 0 issues found | Likely insufficient review effort | Minimum 3 issues must be listed (Step 1) |
| Fixing tests in the review itself | Reviewer should identify, not fix | Return FAIL with specific items; implementer fixes |
| Skipping section D for UI features | UI errors go undetected | Section D is mandatory when ui=true |
| Reviewing after implementation | Defeats the purpose — tests may be shaped by implementation knowledge | Review BEFORE any implementation code exists |

## Relationship to Other Documents

| Document | Relationship |
|----------|-------------|
| [test-scenario-rules.md](test-scenario-rules.md) | Rules enforced by this review |
| [testing-anti-patterns.md](testing-anti-patterns.md) | Anti-pattern #14 defines low-value assertions |
| [ui-error-detection.md](ui-error-detection.md) | Section D checks reference UI detection spec |
| [plan-writing.md](plan-writing.md) | Task 2 in plan template is this review checkpoint |
| [code-review.md](code-review.md) | Complementary review — Code Review runs after implementation |
| [architecture.md](architecture.md) | Test Plan Review phase in Worker workflow |
