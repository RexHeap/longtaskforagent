---
name: using-long-task
description: "Use when starting any session in a long-task project - routes to the correct phase skill based on project state"
---

<EXTREMELY-IMPORTANT>
You are in a long-task multi-session project. You MUST invoke the correct phase skill BEFORE any response or action — including clarifying questions.

IF A PHASE SKILL APPLIES, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## How to Access Skills

Use the `Skill` tool to invoke skills by name (e.g., `long-task:long-task-work`). When invoked, the skill content is loaded and presented to you — follow it directly. Never use the Read tool on skill files.

## Phase Detection

Check project state and invoke the corresponding skill:

```dot
digraph phase_detection {
    "Session Start" [shape=doublecircle];
    "feature-list.json exists?" [shape=diamond];
    "Design doc in docs/plans/?" [shape=diamond];
    "Invoke long-task:long-task-design" [shape=box style=filled fillcolor=lightblue];
    "Invoke long-task:long-task-init" [shape=box style=filled fillcolor=lightyellow];
    "Invoke long-task:long-task-work" [shape=box style=filled fillcolor=lightgreen];

    "Session Start" -> "feature-list.json exists?";
    "feature-list.json exists?" -> "Invoke long-task:long-task-work" [label="yes"];
    "feature-list.json exists?" -> "Design doc in docs/plans/?" [label="no"];
    "Design doc in docs/plans/?" -> "Invoke long-task:long-task-init" [label="yes"];
    "Design doc in docs/plans/?" -> "Invoke long-task:long-task-design" [label="no"];
}
```

## Skill Catalog

### Phase Skills (invoke ONE based on detection above)
| Skill | Phase | When |
|-------|-------|------|
| `long-task:long-task-design` | Phase 0 | No design doc and no feature-list.json |
| `long-task:long-task-init` | Phase 1 | Design doc exists, no feature-list.json |
| `long-task:long-task-work` | Phase 2 | feature-list.json exists |

### Discipline Skills (invoked by long-task-work as sub-skills — do NOT invoke directly)
| Skill | Purpose |
|-------|---------|
| `long-task:long-task-tdd` | TDD Red-Green-Refactor with Test Plan Review |
| `long-task:long-task-quality` | Coverage Gate + Mutation Gate + Verification |
| `long-task:long-task-review` | Two-stage Code Review |

## Key Files (shared contract)

| File | Role |
|------|------|
| `feature-list.json` | Task inventory — the central shared state |
| `task-progress.md` | Session-by-session log |
| `long-task-guide.md` | Project-specific Worker guide |
| `RELEASE_NOTES.md` | Living changelog |

## Red Flags

These thoughts mean STOP — you're rationalizing:

| Thought | Reality |
|---------|---------|
| "Let me just look at the code first" | Invoke phase skill first. It tells you HOW to orient. |
| "I know which feature to work on" | Worker skill has Orient step. Follow it. |
| "This feature is simple, skip TDD" | long-task-tdd is non-negotiable. |
| "Tests pass, I can mark it done" | long-task-quality gates MUST pass first. |
| "Code review is overkill for this" | long-task-review runs after EVERY feature. |
| "I remember the workflow" | Skills evolve. Load current version via Skill tool. |
| "I need more context first" | Skill check comes BEFORE exploration. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |

## Skill Priority

1. **Phase skill first** — determines the entire session workflow
2. **Discipline skills second** — invoked by Worker in strict order (tdd → quality → review)
3. **On error** — follow systematic-debugging approach in `references/systematic-debugging.md` before any fix
