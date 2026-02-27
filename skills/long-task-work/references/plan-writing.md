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
**Design Reference**: docs/plans/YYYY-MM-DD-<topic>-design.md § 4.N

## Context
[1-2 sentences: what this feature does and why it matters]

## Design Alignment
[Copy the full design section §4.N content here — including class diagram, sequence diagram, and design decisions. Do NOT summarize or paraphrase the diagrams; include the Mermaid code blocks verbatim so the plan is self-contained for subagent execution.]
- **Key classes**: [from design class diagram — list classes to create/modify with their key methods]
- **Interaction flow**: [from design sequence diagram — describe the key call chains]
- **Third-party deps**: [from design dependency table — exact library versions to use]
- **Deviations**: [none, or explain why the plan deviates from design and note user approval]

## SRS Requirement
[Copy the full FR-xxx section from the SRS here — including EARS statement, priority, acceptance criteria, and Given/When/Then scenarios. This ensures the plan is traceable to the approved requirement.]

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

### Task 2: [Implement minimal code]
**Files**: `src/<module>.py` (create/modify)
**Steps**:
1. [Exact change: add function X to file Y]
2. [Exact change: wire up route in file Z]
3. Run: `pytest tests/test_<module>.py`
4. **Expected**: All tests PASS

### Task 3: [Coverage Gate]
**Steps**:
1. Run coverage tool: `pytest --cov=src --cov-branch --cov-report=term-missing`
2. Check: line coverage >= quality_gates.line_coverage_min (default 90%)
3. Check: branch coverage >= quality_gates.branch_coverage_min (default 80%)
4. **If BELOW threshold**: write additional tests (return to Task 1 for new test cases)
5. **Expected**: Coverage meets thresholds
6. Record coverage report output as evidence

### Task 4: [Refactor]
**Files**: `src/<module>.py` (modify)
**Steps**:
1. [Specific refactoring action]
2. Run: `pytest` (full suite)
3. **Expected**: All tests still PASS

### Task 5: [Mutation Gate]
**Steps**:
1. Run mutation tool (incremental): `mutmut run --paths-to-mutate=<changed-files>`
2. Check: mutation score >= quality_gates.mutation_score_min (default 80%)
3. **If BELOW threshold**: improve test assertions to kill surviving mutants (return to Task 1)
4. **Expected**: Mutation score meets threshold
5. Record mutation report output as evidence
6. See [coverage-and-mutation.md](coverage-and-mutation.md) for per-language tool setup

### Task 6: [Create example]
**Files**: `examples/<NN>-<name>.<ext>` (create)
**Steps**:
1. Create example file demonstrating the feature
2. Update `examples/README.md`
3. Run the example to verify it works

## Verification
- [ ] All verification_steps from feature spec covered by tests
- [ ] All tests pass
- [ ] Coverage meets thresholds (line >= 90%, branch >= 80%)
- [ ] Mutation score meets threshold (>= 80%)
- [ ] No regressions on existing features
- [ ] Example is runnable
```

## Plan Writing Rules

1. **Assume zero context** — plans must be executable by someone who has never seen the codebase. Include exact file paths, exact function names, exact imports.

2. **Each task is 2-5 minutes of work** — if a task would take longer, split it.

3. **Every task has verification** — "Run X, expect Y" at the end of each task. Never leave a task without a way to confirm it worked.

4. **Follow TDD order** — Task 1 is always "write failing tests", Task 2 is always "implement", etc.

5. **Be specific about file operations** — say "create" vs "modify" vs "add to existing". Include the exact location within a file when modifying.

6. **Quality gates are explicit tasks** — Coverage Gate (Task 3) and Mutation Gate (Task 5) are separate tasks with clear pass/fail criteria, not afterthoughts.

8. **Design alignment is mandatory** — every plan MUST reference the corresponding Key Feature Design section from the design document. The plan's class structure, interaction flow, and dependency choices must match the approved design. Any deviation requires explicit justification and user approval.

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
