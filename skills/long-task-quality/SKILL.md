---
name: long-task-quality
description: "Use after TDD cycle in a long-task project - enforces coverage gate, mutation gate, and fresh verification evidence before marking features as passing"
---

# Quality Gates & Verification

Three sequential gates that MUST pass before a feature can be marked "passing". No shortcuts, no exceptions.

**Announce at start:** "I'm using the long-task-quality skill to run quality gates."

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## Gate 1: Coverage

After TDD Green (all tests pass), run the coverage tool.

1. **Run** the coverage tool from `tech_stack.coverage_tool`:
   ```bash
   # Python example:
   pytest --cov=src --cov-branch --cov-report=term-missing
   # Java example:
   mvn verify  # JaCoCo
   # TypeScript example:
   npx vitest run --coverage
   ```
2. **Read** the FULL output (not just summary line)
3. **Verify**: line coverage >= `quality_gates.line_coverage_min`% (default 90%), branch coverage >= `quality_gates.branch_coverage_min`% (default 80%)
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

1. **Run** the mutation tool from `tech_stack.mutation_tool` — **incremental** (changed files only):
   ```bash
   # Python example:
   mutmut run --paths-to-mutate=src/changed_module.py
   # Java example:
   mvn org.pitest:pitest-maven:mutationCoverage -DtargetClasses=com.example.Changed*
   # TypeScript example:
   npx stryker run --mutate 'src/changed/**/*.ts'
   ```
2. **Read** the FULL output
3. **Verify**: mutation score >= `quality_gates.mutation_score_min`% (default 80%)
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
1. IDENTIFY → What commands prove this feature works?
   - Test command (full suite)
   - Coverage command
   - Mutation command
   - Feature-specific verification_steps

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
   - All verification_steps satisfied?

5. THEN CLAIM → Only now:
   - Mark feature "status": "passing" in feature-list.json
   - Report results with evidence

If ANY step fails → STOP. Do NOT mark as passing. Fix the issue first.
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

If coverage or mutation tools are not yet configured for this project's tech stack, read `skills/long-task-quality/coverage-recipes.md` for full setup instructions per language (Python, Java, TypeScript, C, C++).

## Verification Timing Summary

| Event | What to verify |
|-------|---------------|
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

## Integration

**Called by:** long-task-work (Step 9)
**Requires:** TDD cycle completed (long-task-tdd passed — tests exist and pass)
**Produces:** Fresh verification evidence (test output, coverage %, mutation score)
**Chains to:** long-task-review (via Work Step 10)
