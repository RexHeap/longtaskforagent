# Plan Writing

## Purpose

Transform each feature (or group of related features) into a bite-sized, step-by-step implementation plan. Plans are detailed enough that a fresh subagent with zero codebase knowledge can execute them.

## When to Write Plans

- After a feature is selected in the Worker Orient phase
- Before entering TDD Red
- Especially valuable for complex features or when using subagent-driven development

## Plan Structure

Each plan is saved to `docs/plans/YYYY-MM-DD-<feature-name>.md`:

```markdown
# Plan: [Feature Title] (Feature #ID)

**Date**: YYYY-MM-DD
**Feature**: #ID — [title]
**Priority**: high/medium/low
**Dependencies**: [list or "none"]

## Context
[1-2 sentences: what this feature does and why it matters]

## Tasks

### Task 1: [Write failing tests]
**Files**: `tests/test_<module>.py` (create)
**Steps**:
1. Create test file with imports
2. Write test cases covering each verification_step:
   - Follow test scenario rules (see references/test-scenario-rules.md):
     - Include happy path, error handling, boundary, and security scenarios (where applicable)
     - Ensure negative test ratio >= 40%
     - Ensure low-value assertion ratio <= 20%
     - Apply the "wrong implementation" challenge to each test
   - Test case A: [exact test code or description]
   - Test case B: [exact test code or description]
3. Run: `pytest tests/test_<module>.py`
4. **Expected**: All tests FAIL (no implementation yet)
5. **Expected**: Tests fail for the RIGHT REASON (not import error or syntax error)

### Task 2: [Test Plan Review — HARD GATE]
**Steps**:
1. Dispatch Test Plan Review subagent with:
   - Feature spec (from feature-list.json)
   - Test code (from Task 1)
   - Test run output (from Task 1, step 3)
2. Subagent fills scoring rubric (sections A-D)
3. **Gate**: Any NO in rubric → FAIL → fix tests and re-submit (max 2 rounds)
4. **Expected**: Verdict is PASS
5. See [test-plan-review.md](test-plan-review.md) for full rubric and process

### Task 3: [Implement minimal code]
**Files**: `src/<module>.py` (create/modify)
**Steps**:
1. [Exact change: add function X to file Y]
2. [Exact change: wire up route in file Z]
3. Run: `pytest tests/test_<module>.py`
4. **Expected**: All tests PASS

### Task 4: [Coverage Gate]
**Steps**:
1. Run coverage tool: `pytest --cov=src --cov-branch --cov-report=term-missing`
2. Check: line coverage >= quality_gates.line_coverage_min (default 90%)
3. Check: branch coverage >= quality_gates.branch_coverage_min (default 80%)
4. **If BELOW threshold**: write additional tests (return to Task 1 for new test cases, then re-run Task 2 review)
5. **Expected**: Coverage meets thresholds
6. Record coverage report output as evidence

### Task 5: [Refactor]
**Files**: `src/<module>.py` (modify)
**Steps**:
1. [Specific refactoring action]
2. Run: `pytest` (full suite)
3. **Expected**: All tests still PASS

### Task 6: [Mutation Gate]
**Steps**:
1. Run mutation tool (incremental): `mutmut run --paths-to-mutate=<changed-files>`
2. Check: mutation score >= quality_gates.mutation_score_min (default 80%)
3. **If BELOW threshold**: improve test assertions to kill surviving mutants (return to Task 1)
4. **Expected**: Mutation score meets threshold
5. Record mutation report output as evidence
6. See [coverage-and-mutation.md](coverage-and-mutation.md) for per-language tool setup

### Task 7: [Create example]
**Files**: `examples/<NN>-<name>.<ext>` (create)
**Steps**:
1. Create example file demonstrating the feature
2. Update `examples/README.md`
3. Run the example to verify it works

## Verification
- [ ] All verification_steps from feature spec covered by tests
- [ ] Test Plan Review passed (rubric verdict = PASS)
- [ ] All tests pass
- [ ] Coverage meets thresholds (line >= 90%, branch >= 80%)
- [ ] Mutation score meets threshold (>= 80%)
- [ ] Low-value assertion ratio <= 20%
- [ ] Negative test ratio >= 40%
- [ ] No regressions on existing features
- [ ] Example is runnable
```

## Plan Writing Rules

1. **Assume zero context** — plans must be executable by someone who has never seen the codebase. Include exact file paths, exact function names, exact imports.

2. **Each task is 2-5 minutes of work** — if a task would take longer, split it.

3. **Every task has verification** — "Run X, expect Y" at the end of each task. Never leave a task without a way to confirm it worked.

4. **Follow TDD order** — Task 1 is always "write failing tests", Task 2 is always "Test Plan Review", Task 3 is always "implement", etc.

5. **Be specific about file operations** — say "create" vs "modify" vs "add to existing". Include the exact location within a file when modifying.

6. **Test Plan Review is non-negotiable** — Task 2 is a hard gate. No implementation (Task 3) may begin until the test suite passes review. This prevents wasting an entire TDD cycle on inadequate tests.

7. **Quality gates are explicit tasks** — Coverage Gate (Task 4) and Mutation Gate (Task 6) are separate tasks with clear pass/fail criteria, not afterthoughts.

## Execution Modes

After writing the plan, choose an execution mode:

### Mode A: Self-Execute (Default)
The current agent executes the plan step by step in the Worker cycle.

### Mode B: Subagent-Driven
Dispatch a fresh subagent per task. Each subagent receives the full task text (not file references). See [subagent-development.md](subagent-development.md) for details.

**Note on Task 2**: The Test Plan Review is always dispatched as a separate subagent (even in Mode A self-execution), to ensure independent review.

## Plan Persistence

Plans are saved to `docs/plans/` and committed to git. This provides:
- Audit trail of implementation decisions
- Context for code review (reviewer can check plan vs implementation)
- Reference for future sessions if work is interrupted
