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
   - Test case A: [exact test code or description]
   - Test case B: [exact test code or description]
3. Run: `pytest tests/test_<module>.py`
4. **Expected**: All tests FAIL (no implementation yet)

### Task 2: [Implement minimal code]
**Files**: `src/<module>.py` (create/modify)
**Steps**:
1. [Exact change: add function X to file Y]
2. [Exact change: wire up route in file Z]
3. Run: `pytest tests/test_<module>.py`
4. **Expected**: All tests PASS

### Task 3: [Refactor]
**Files**: `src/<module>.py` (modify)
**Steps**:
1. [Specific refactoring action]
2. Run: `pytest` (full suite)
3. **Expected**: All tests still PASS

### Task 4: [Create example]
**Files**: `examples/<NN>-<name>.<ext>` (create)
**Steps**:
1. Create example file demonstrating the feature
2. Update `examples/README.md`
3. Run the example to verify it works

## Verification
- [ ] All verification_steps from feature spec covered by tests
- [ ] All tests pass
- [ ] No regressions on existing features
- [ ] Example is runnable
```

## Plan Writing Rules

1. **Assume zero context** — plans must be executable by someone who has never seen the codebase. Include exact file paths, exact function names, exact imports.

2. **Each task is 2-5 minutes of work** — if a task would take longer, split it.

3. **Every task has verification** — "Run X, expect Y" at the end of each task. Never leave a task without a way to confirm it worked.

4. **Follow TDD order** — Task 1 is always "write failing tests", Task 2 is always "implement", etc.

5. **Be specific about file operations** — say "create" vs "modify" vs "add to existing". Include the exact location within a file when modifying.

## Execution Modes

After writing the plan, choose an execution mode:

### Mode A: Self-Execute (Default)
The current agent executes the plan step by step in the Worker cycle.

### Mode B: Subagent-Driven
Dispatch a fresh subagent per task. Each subagent receives the full task text (not file references). See [subagent-development.md](subagent-development.md) for details.

## Plan Persistence

Plans are saved to `docs/plans/` and committed to git. This provides:
- Audit trail of implementation decisions
- Context for code review (reviewer can check plan vs implementation)
- Reference for future sessions if work is interrupted
