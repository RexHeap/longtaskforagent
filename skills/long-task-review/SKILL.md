---
name: long-task-review
description: "Use after quality gates pass in a long-task project - runs spec & design compliance review before persisting"
---

# Spec & Design Compliance Review

Review runs after every feature, before Persist. No exceptions. Verifies implementation matches the approved spec, design, plan, and UCD.

**Announce at start:** "I'm using the long-task-review skill to review this feature."

## When to Run

- After **every** feature passes quality gates
- Before the Persist phase (git commit)
- No exceptions — even "simple" features need review

## Stage 1: Spec & Design Compliance

**Questions**:
1. Does the implementation do what the **feature spec** says? (SRS traceability)
2. Does the implementation follow the **design document**? (architecture, class structure, interaction flows, dependency versions)
3. Does the implementation follow the **plan document**? (task decomposition, agreed approach)
4. For `"ui": true` features: Does the implementation follow the **UCD style guide**? (style tokens, component visual spec, page layouts)

Dispatch subagent with `skills/long-task-review/prompts/spec-reviewer-prompt.md`:

```
Task(
  subagent_type="general-purpose",
  prompt="""
  You are a spec & design compliance reviewer.
  Read the prompt at: skills/long-task-review/prompts/spec-reviewer-prompt.md

  Feature spec:
  {feature_json}

  SRS requirement section (full FR-xxx from SRS):
  {srs_section}

  Design document (Key Feature Design section for this feature — full §4.N subsection, NOT a grep snippet):
  {design_section}

  Plan document:
  {plan_content}

  UCD style guide (only for ui:true features, omit if not applicable):
  {ucd_content}

  ST test case document (from Worker Step 10):
  {st_case_content}

  Git diff:
  {diff_output}

  Test results:
  {test_summary}

  Perform the review following the prompt template.
  """
)
```

### Spec Compliance Checklist (S1-S5)

| # | Check |
|---|-------|
| S1 | All `verification_steps` covered by tests |
| S2 | Tests verify behavior, not implementation details |
| S3 | No undocumented side effects |
| S4 | Edge cases from the spec are handled |
| S5 | Feature `description` matches actual behavior |

### Design Compliance Checklist (D1-D5)

| # | Check |
|---|-------|
| D1 | Class/module structure matches the design document's class diagram |
| D2 | Interaction flow matches the design document's sequence diagram |
| D3 | Third-party dependency versions match the design document's dependency table |
| D4 | Architectural layers/boundaries respected as defined in the logical view |
| D5 | No unauthorized design deviations (or deviations are documented with user approval in the plan) |

### Detailed Design Compliance Checklist (P1-P6)

| # | Check |
|---|-------|
| P1 | Implementation tasks match the feature detailed design's task decomposition (§8) |
| P2 | Public method signatures match the Interface Contract table (§3) — parameters, return types, exceptions |
| P3 | Core algorithm matches the pseudocode and flow diagram in §5 — control flow, key decisions, data transformations |
| P4 | Boundary conditions handled match the boundary matrix (§5.3) — all rows covered |
| P5 | Error handling matches the error table (§5.4) — trigger conditions, recovery actions, error types |
| P6 | State transitions (if any) match the state diagram (§6) — all states reachable, no undocumented transitions |

### UCD Compliance Checklist (U1-U4) — only for `"ui": true` features with UCD document

| # | Check |
|---|-------|
| U1 | Color values used in CSS/styles match UCD color palette tokens |
| U2 | Typography (font family, size, weight, line height) matches UCD typography scale |
| U3 | Spacing and layout (padding, margin, border radius, shadow) follow UCD spacing tokens |
| U4 | Component structure and visual hierarchy match UCD component prompts for the implemented components |

### Test Case Completeness Checklist (T1-T3) — requires ST test case document from Worker Step 10

| # | Check |
|---|-------|
| T1 | Every `verification_step` has at least one corresponding ST test case in `docs/test-cases/feature-{id}-{slug}.md` |
| T2 | Every ST test case has at least one automated test implementing it (check test file comments for `# ST-xxx` references) |
| T3 | UI test cases (if any) include EXPECT/REJECT clauses, console error gate, and accessibility checkpoint |

**Any NO in S1-S5 or D1-D5 → FAIL. Fix gaps, re-run tests, re-review.**
**Any NO in U1-U4 → FAIL (for ui:true features). Visual inconsistency must be fixed before proceeding.**
**Any NO in T1-T3 → FAIL. Test case coverage gaps must be filled before proceeding.**
**Any NO in P1-P6 → FAIL (must fix before feature complete). Interface contract and algorithm deviations indicate spec drift.**

## Issue Severity

| Severity | Response | Blocks? |
|----------|----------|---------|
| Critical | Fix immediately | Yes |
| Important | Fix before next feature | Yes |
| Minor | Fix in refactor or next session | No |

## Review Loop

```
Quality Gates Pass → Spec & Design Compliance Review
                          ↓
                     S1-S5, D1-D5, T1-T3 all PASS (and U1-U4 if ui:true)?
                          ↓ YES                    ↓ NO
                     Feature complete         Fix → Re-test → Re-review
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
| Skip review for "simple" features | Always run review |
| Bundle multiple issues into one finding | One concern per issue |
| Performative agreement ("Great code!") | PASS or specific issues, no filler |

## Integration

**Called by:** long-task-work (Step 11)
**Dispatches:** spec-reviewer subagent (`skills/long-task-review/prompts/spec-reviewer-prompt.md`)
**Requires:** Quality gates passed (long-task-quality)
**Inputs:**
- Feature spec from `feature-list.json`
- SRS requirement section (full FR-xxx subsection from `docs/plans/*-srs.md`)
- Design document section (full §4.N subsection from `docs/plans/*-design.md` — NOT a grep snippet)
- Feature detailed design document (`docs/plans/YYYY-MM-DD-<feature-name>.md`) — includes Interface Contract, Algorithm, State Diagram, Test Inventory
- ST test case document (`docs/test-cases/feature-{id}-{slug}.md`) — from Worker Step 10
- UCD style guide (`docs/plans/*-ucd.md`) — only for `"ui": true` features
- Git diff, test results
**Produces:** Review verdict (PASS/FAIL with findings)
**Returns to:** long-task-work for Add Examples + Persist steps
