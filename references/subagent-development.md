# Subagent-Driven Development

## Purpose

Dispatch a fresh subagent for each implementation task. This prevents context pollution (one task's details don't confuse the next) and enables two-stage code review per task.

## When to Use

- Complex features with multiple tasks
- Features where context pollution is a concern
- When the implementation plan has been written (see [plan-writing.md](plan-writing.md))

For simple features (1-2 tasks), self-execution is faster and sufficient.

## Architecture

```
Controller (main agent)
  │
  ├─ Dispatch Subagent: Task 1 (implementer)
  │   └─ Returns: code changes + test results
  │
  ├─ Dispatch Subagent: Spec Review (reviewer)
  │   └─ Returns: PASS or list of gaps
  │
  ├─ [If FAIL] Dispatch Subagent: Fix (implementer)
  │   └─ Returns: fixed code + test results
  │
  ├─ Dispatch Subagent: Code Quality Review (reviewer)
  │   └─ Returns: PASS or list of issues
  │
  └─ Repeat for Task 2, Task 3, ...
```

## Controller Responsibilities

The main agent acts as controller. It:

1. **Loads the implementation plan** from `docs/plans/`
2. **Dispatches one subagent per task** with the full task text
3. **Reviews results** after each task (or dispatches a reviewer subagent)
4. **Tracks progress** — marks tasks complete, updates feature status
5. **Handles failures** — if a task fails, provides context for retry

## Dispatching Implementer Subagents

### Key Rules

1. **Provide full task text** — copy the entire task description into the prompt. Do NOT say "read file X" — the subagent may not have context.

2. **Include project context** — tell the subagent:
   - What the project is
   - What tech stack is used
   - Where key files are
   - What patterns to follow

3. **Define clear exit criteria** — tell the subagent exactly what "done" looks like:
   - Which tests must pass
   - Which files should be created/modified
   - What verification command to run

### Prompt Template

```markdown
You are implementing a task for the [project-name] project.

## Project Context
- Tech stack: [stack]
- Key patterns: [patterns]
- Test framework: [framework]

## Task
[Full task text from the plan, including exact file paths, code, and verification steps]

## Exit Criteria
1. Run [test command] — all tests pass
2. Files created/modified: [list]
3. No regressions: run [full test command] — all pass

## Rules
- Follow TDD: write failing tests first, then implement
- Do not modify files outside the scope of this task
- Commit your changes with a descriptive message
```

## Dispatching Reviewer Subagents

After each task, dispatch a reviewer subagent:

### Spec Reviewer Prompt Template

```markdown
You are reviewing a completed implementation task for spec compliance.

## Feature Spec
[Feature JSON from feature-list.json]

## Task Plan
[The task that was supposed to be implemented]

## Changes Made
[git diff output]

## Test Results
[test output]

## Your Job
1. Check: does the implementation satisfy ALL verification_steps?
2. Check: do tests cover the right behaviors?
3. Verdict: PASS or FAIL with specific gaps
```

### Code Quality Reviewer Prompt Template

```markdown
You are reviewing code quality for a completed implementation task.

## Changes Made
[git diff output]

## Existing Patterns
[Examples of how similar code is written in this project]

## Your Job
1. Check: architecture, error handling, type safety, security, test quality
2. Issues: list by severity (Critical / Important / Minor)
3. Each issue: file:line + description + suggested fix
```

## Review Loop

```
Implementer completes task
  → Spec Review
    → PASS → Code Quality Review
               → PASS → Task complete
               → FAIL → Implementer fixes → Code Quality Re-review
    → FAIL → Implementer fixes → Spec Re-review
  → Max 3 rounds → Escalate to user
```

## Parallel Dispatch (Advanced)

When multiple tasks are independent (no shared files, no dependencies):

1. Identify independent tasks in the plan
2. Dispatch implementer subagents in parallel using the Task tool
3. Wait for all to complete
4. Run full test suite to check for conflicts
5. Review each task's changes
6. Resolve any conflicts

**Constraints**:
- Only parallelize truly independent tasks
- Always run full test suite after parallel completion
- If conflicts found, resolve sequentially

## Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| Reference files instead of providing full text | Subagent may not have access or context | Copy full task text into prompt |
| Skip spec review, only do code quality | May polish code that doesn't meet spec | Spec review gates code quality review |
| Dispatch without clear exit criteria | Subagent doesn't know when it's done | Define exact verification commands |
| Parallelize dependent tasks | Race conditions, conflicting changes | Only parallelize truly independent tasks |
| Ignore reviewer feedback | Compounds quality issues | Fix Critical/Important before proceeding |
