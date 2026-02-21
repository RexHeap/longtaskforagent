# Test Quality Enhancement — Design Document

**Date**: 2026-02-22
**Status**: Draft

## Requirements Summary

The long-task-agent skill's testing subsystem has structural deficiencies that undermine test effectiveness:

1. **UI verification lacks error identification spec** — LLM sees obvious UI errors but still reports "correct" due to absence of objective criteria
2. **Plan template is out of sync with Worker workflow** — Coverage Gate and Mutation Gate missing from plan-writing.md, causing subagents to skip quality gates
3. **No test quality review before implementation** — Bad tests discovered only after full TDD cycle is wasted
4. **SubAgent review suffers from LLM-specific failure modes** — helpfulness bias causes "polite PASS", shared model blindness misses common errors
5. **Low-value assertions inflate coverage** — `assert x is not None`, `isinstance()`, import tests provide zero bug-finding ability
6. **No test scenario completeness rules** — LLM can omit entire categories of tests (error paths, boundaries) with no guardrail

## Approach

**Selected approach**: Rule-driven test scenario generation + SubAgent review with adversarial design + automated UI error detection.

**Key decision**: No hardcoded test specifications (L1) in `feature-list.json`. Instead, testing requirements are expressed as rules in reference docs that guide the LLM during Plan/TDD Red phases, and are enforced by the Test Plan Review subagent.

**Justification**: Hardcoded test specs create maintenance burden, bloat the schema, and are too rigid to adapt to diverse tech stacks. Rules + review achieve the same quality assurance with more flexibility.

## Architecture

### New Phase: Test Plan Review (inserted into Worker workflow)

```
Config Gate → DevTools Gate → Plan → TDD Red
                                        ↓
                              ★ Test Plan Review ★ (NEW — hard gate)
                                        ↓
                                    TDD Green
                                        ↓
                              Coverage Gate → Refactor → Mutation Gate
                                        ↓
                              Code Review (existing, enhanced)
```

The Test Plan Review is:
- Executed by an **independent subagent** (not self-review)
- A **hard gate** — FAIL blocks TDD Green
- Uses a **structured scoring rubric** with binary YES/NO items
- Maximum 2 review rounds before escalating to user

### UI Error Detection: Three-Layer Model

| Layer | Mechanism | Type | Blocks on |
|-------|-----------|------|-----------|
| Automated Detection | JS script via `evaluate_script()` | Objective | Any detected error |
| EXPECT/REJECT Format | Structured verification_steps | Semi-objective | Missing EXPECT or present REJECT |
| Console Error Gate | `list_console_messages(types=["error"])` | Objective | error count > 0 (unless explicitly expected) |

### SubAgent Review Redesign

| Aspect | Current | Proposed |
|--------|---------|----------|
| Verdict flow | Verdict first, then issues | Issues first (min 3), then verdict |
| Format | Free-text PASS/FAIL | Structured scoring rubric with YES/NO items |
| Critical features | Single reviewer | Dual independent reviewers |
| Test-specific review | Part of Code Review Stage 2 | Dedicated Test Plan Review (separate phase) |

### Test Scenario Rules (replacing hardcoded test_spec)

Rules embedded in reference docs that the LLM must follow when writing tests:

1. **Scenario category coverage**: Every test suite must include tests from these categories where applicable: happy path, error handling, boundary/edge cases, security (input validation)
2. **Negative ratio**: At least 40% of test functions must test error/boundary/negative paths
3. **Assertion quality**: Low-value assertions (None checks, isinstance, import, len>0, key-in-dict, bool) must be <= 20% of total assertions
4. **UI-specific**: Every `[devtools]` step must run the automated error detection script; EXPECT/REJECT format required

## Detailed Design

### 1. Plan Template Alignment (plan-writing.md)

Current 4-task template → Expanded 7-task template:

```markdown
### Task 1: Write failing tests (unit + functional)
### Task 2: ★ Test Plan Review checkpoint ★
### Task 3: Implement minimal code
### Task 4: Coverage Gate — verify line >= threshold, branch >= threshold
### Task 5: Refactor
### Task 6: Mutation Gate — verify score >= threshold
### Task 7: Create example
```

Task 2 is a hard gate — the plan must explicitly include a review checkpoint before implementation begins.

### 2. Test Plan Review Phase

**New reference file**: `references/test-plan-review.md`

**New prompt template**: `agents/prompts/test-plan-reviewer-prompt.md`

Review checklist (structured scoring rubric):

```markdown
## Scoring Rubric (answer YES or NO for each, cite evidence)

### A. Scenario Completeness
| # | Check | YES/NO | Evidence |
|---|-------|--------|----------|
| A1 | Happy path scenarios present? | | |
| A2 | Error/failure scenarios present? | | |
| A3 | Boundary/edge case scenarios present? | | |
| A4 | Negative test ratio >= 40%? | | |

### B. Assertion Quality
| # | Check | YES/NO | Evidence |
|---|-------|--------|----------|
| B1 | Zero tests that only assert None/isinstance/import? | | |
| B2 | Low-value assertion ratio <= 20%? | | |
| B3 | Each test asserts specific observable outcomes? | | |
| B4 | No test recalculates expected value using impl logic? | | |

### C. Test Independence
| # | Check | YES/NO | Evidence |
|---|-------|--------|----------|
| C1 | Tests assert behavior, not implementation details? | | |
| C2 | A plausible wrong implementation would fail these tests? | | |
| C3 | No shared mutable state between tests? | | |

### D. UI Checks (if ui=true)
| # | Check | YES/NO | Evidence |
|---|-------|--------|----------|
| D1 | EXPECT/REJECT format used in [devtools] steps? | | |
| D2 | Automated UI error detection script included? | | |
| D3 | Console error check included? | | |
| D4 | Cross-page state verified (if multi-page flow)? | | |

**Verdict rule**: Any NO → FAIL (reviewer cannot override).
```

The reviewer prompt uses adversarial framing:
- Step 1: Find at least 3 potential issues before giving verdict
- Step 2: Challenge own findings (keep, dismiss with evidence)
- Step 3: Fill scoring rubric
- Step 4: Verdict is computed from rubric (not subjective)

### 3. UI Error Detection Specification

**New reference file**: `references/ui-error-detection.md`

Contains:

a) **Automated detection script** (JS, executed via `evaluate_script()`):
   - Zero-size visible interactive elements
   - Interactive elements outside viewport
   - Placeholder/error text: undefined, [object Object], NaN, null, TODO, FIXME
   - Interactive element overlap
   - Empty containers with layout roles
   - Broken images (naturalWidth === 0)
   - Returns `{errors: [...], count: N}` — count > 0 means FAIL

b) **EXPECT/REJECT verification_step format**:
   ```
   [devtools] <page-path> | EXPECT: <positive criteria> | REJECT: <negative criteria>
   ```
   - EXPECT: elements, text, states that MUST be present
   - REJECT: conditions that MUST NOT be present (forces LLM to look for errors)
   - Both are required for every `[devtools]` verification step

c) **Console error hard gate**:
   - `list_console_messages(types=["error"])` count must be 0
   - Exception: only when verification_step contains `[expect-console-error: <pattern>]`

### 4. SubAgent Review Enhancement

**Modified files**: `agents/code-reviewer.md`, `agents/prompts/spec-reviewer-prompt.md`, `agents/prompts/code-quality-reviewer-prompt.md`

Changes:
a) **Adversarial prompt structure**: "Find at least 3 issues FIRST, then decide verdict"
b) **Structured scoring rubric**: Binary YES/NO items, verdict computed from answers
c) **Dual review for high-priority/UI features**: Two independent subagents, controller merges results
d) **Test quality items added to Code Review Stage 2**: Low-value assertion check, negative ratio check

### 5. Anti-Pattern #14: Low-Value Assertions

**Modified file**: `references/testing-anti-patterns.md`

New anti-pattern with:
- Exhaustive list of low-value assertion patterns (with code examples)
- The "wrong implementation" test: "What wrong impl would NOT be caught?"
- Concrete fixes showing how to convert each low-value assertion to high-value
- Quantitative rule: low_value_count / total_assertions <= 0.20

### 6. Test Scenario Rules Template

**New reference file**: `references/test-scenario-rules.md`

Contains rules the LLM must follow when writing tests during TDD Red:

a) **Category coverage rule**: Test suites must include scenarios from applicable categories (happy path, error handling, boundary, security)
b) **Negative ratio rule**: >= 40% of test functions must test non-happy-path scenarios
c) **Assertion quality rule**: <= 20% low-value assertions
d) **UI coverage rule**: automated error detection + EXPECT/REJECT + console gate
e) **"Wrong implementation" challenge**: For each test, the author must consider whether a plausible wrong implementation would still pass

### 7. Worker Workflow Updates

**Modified files**: `SKILL.md`, `references/architecture.md`

Insert Test Plan Review phase into Worker workflow between TDD Red and TDD Green. Update:
- Phase numbering
- TDD workflow diagram
- Anti-patterns table (add "Skipping Test Plan Review")
- Critical Rules section

### 8. Validate Features Script Enhancement

**Modified file**: `scripts/validate_features.py`

Add validation for:
- `[devtools]` verification steps must use EXPECT/REJECT format (when present)
- Warning if a UI feature has no REJECT clause

## Testing Strategy

- Existing tests for `validate_features.py`, `init_project.py`, `check_configs.py`, `check_devtools.py`, `validate_guide.py` must continue to pass
- New tests needed for:
  - EXPECT/REJECT format validation in `validate_features.py`
  - Any new validation logic
- Manual verification: review all modified reference docs for internal consistency

## Files Affected

### New Files
| File | Purpose |
|------|---------|
| `references/test-plan-review.md` | Test Plan Review process and rules |
| `references/test-scenario-rules.md` | Rules for test scenario generation |
| `references/ui-error-detection.md` | UI error detection specification and JS script |
| `agents/prompts/test-plan-reviewer-prompt.md` | Test Plan Review subagent prompt |

### Modified Files
| File | Changes |
|------|---------|
| `references/plan-writing.md` | 4-task → 7-task template with Coverage/Mutation/Review gates |
| `references/architecture.md` | Insert Test Plan Review phase, update TDD diagram, update anti-patterns |
| `references/testing-anti-patterns.md` | Add anti-pattern #14 (low-value assertions) |
| `agents/code-reviewer.md` | Adversarial prompt structure, structured rubric, dual review |
| `agents/prompts/spec-reviewer-prompt.md` | Adversarial framing, structured scoring |
| `agents/prompts/code-quality-reviewer-prompt.md` | Add test quality checks, structured scoring |
| `SKILL.md` | Add Test Plan Review to Worker workflow, update Critical Rules |
| `CLAUDE.md` | Add Test Plan Review references |
| `scripts/validate_features.py` | EXPECT/REJECT format validation for [devtools] steps |
| `tests/test_validate_features.py` | Tests for new validation logic |

## Open Questions

None — all design decisions resolved during brainstorming discussion.
