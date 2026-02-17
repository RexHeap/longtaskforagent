# Brainstorming & Design Phase

## Purpose

Mandatory design phase before any implementation. Ensures architectural decisions are deliberate, trade-offs are explicit, and the user approves the approach before work begins.

## When This Phase Runs

- **Always** — before the Initializer decomposes requirements into features
- **Hard gate** — no feature decomposition, no scaffolding, no coding until design is approved

## Process

### Step 1: Explore Context

1. Read the user-provided requirement doc thoroughly
2. Read the user-provided design doc (if any)
3. Explore existing code/repos the project will build on or integrate with
4. Identify constraints: tech stack, platform, integrations, performance requirements

### Step 2: Clarify Requirements

Ask clarifying questions **one at a time** using `AskUserQuestion`:

- Ambiguous requirements ("What does 'fast' mean — sub-100ms or sub-1s?")
- Missing information ("The doc mentions auth but doesn't specify — JWT, session, or OAuth?")
- Scope boundaries ("Should the MVP include feature X or is that post-launch?")
- Priority conflicts ("Both A and B are marked high-priority but they conflict — which wins?")

**Rule**: Do NOT batch questions. Ask one, wait for answer, then ask the next if needed.

### Step 3: Propose Approaches

Present **2-3 implementation approaches** with explicit trade-offs:

```markdown
## Approach A: [Name]
**How it works**: [1-2 sentences]
**Pros**: [bullet list]
**Cons**: [bullet list]
**Best when**: [conditions]

## Approach B: [Name]
**How it works**: [1-2 sentences]
**Pros**: [bullet list]
**Cons**: [bullet list]
**Best when**: [conditions]

## Recommendation: Approach [X]
**Reason**: [why this fits best given the constraints]
```

### Step 4: Section-by-Section Approval

For non-trivial projects, break the design into sections and get approval per section:

1. **Architecture overview** — system components, data flow, tech stack
2. **Data model** — schemas, relationships, storage strategy
3. **API / interface design** — endpoints, contracts, protocols
4. **UI/UX approach** (if applicable) — layout strategy, interaction patterns
5. **Testing strategy** — test types, coverage targets, tooling
6. **Deployment / infrastructure** (if applicable) — hosting, CI/CD, environments

Present each section. Wait for user feedback. Incorporate changes before moving to the next section.

**For simple projects** (< 5 features): Combine all sections into a single approval step.

### Step 5: Write Design Document

After all sections are approved, save the complete design to:

```
docs/plans/YYYY-MM-DD-<topic>-design.md
```

Design document structure:

```markdown
# [Project Name] — Design Document

**Date**: YYYY-MM-DD
**Status**: Approved

## Requirements Summary
[Condensed requirements from user docs]

## Approach
[Selected approach with justification]

## Architecture
[System components, data flow, tech stack decisions]

## Data Model
[Schemas, relationships]

## API / Interface Design
[Endpoints, contracts]

## UI/UX Approach
[If applicable]

## Testing Strategy
[Test types, coverage approach]

## Open Questions
[Any remaining items to resolve during implementation]
```

### Step 6: Transition to Initializer

Once the design document is saved and committed:
- Proceed to the Initializer phase
- Use the approved design to guide feature decomposition
- Reference the design document path in `task-progress.md`

## Hard Gates

| Gate | Rule |
|------|------|
| No feature decomposition | Until design is approved |
| No scaffolding | Until design is approved |
| No code writing | Until design is approved |
| No init_project.py | Until design is approved |

## Red Flags (Agent Rationalizations to Resist)

| Rationalization | Why It's Wrong | Correct Response |
|---|---|---|
| "This is too simple for a design phase" | Even simple projects benefit from explicit tech stack and testing strategy decisions | Run a lightweight design (single approval step) |
| "The requirement doc is already detailed enough" | Requirement docs describe WHAT, not HOW — design decisions are still needed | Propose approaches for the HOW |
| "I already know the best approach" | The user hasn't approved it — their constraints may differ from assumptions | Present options, let the user choose |
| "The user seems impatient, I'll skip design" | Rework costs far more than upfront alignment | Explain the value briefly, then run efficiently |
| "I'll design as I go" | Ad-hoc design causes inconsistency and rework across sessions | Upfront design is cheaper than mid-session course corrections |

## Scaling the Design Phase

| Project Size | Features | Design Depth |
|---|---|---|
| Tiny | 1-5 | Single paragraph approach + 1 approval step |
| Small | 5-20 | 2-3 approach options + combined section approval |
| Medium | 20-50 | Full multi-section approval |
| Large | 50-200+ | Full multi-section approval + architecture diagrams |
