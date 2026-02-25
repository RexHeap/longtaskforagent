---
name: long-task-design
description: "Use when SRS doc exists but no design doc and no feature-list.json - take the approved SRS as input and produce an architecture/design document focused on HOW to build it"
---

# Design Document Generation

Take the approved SRS as input. Propose implementation approaches, get section-by-section design approval, and produce a design document that answers HOW — while the SRS answers WHAT.

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, run init_project.py, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Anti-Pattern: "The SRS Is Detailed Enough To Start Coding"

The SRS describes WHAT the system must do. The design document describes HOW. Even when requirements are crystal clear, the implementation approach (architecture, data model, tech stack choices) needs explicit decisions and user approval. Skipping design causes mid-session corrections and rework.

## Checklist

You MUST create a TodoWrite task for each of these items and complete them in order:

1. **Read the approved SRS** — from `docs/plans/*-srs.md`
2. **Explore technical context** — existing code, frameworks, deployment environment
3. **Propose 2-3 approaches** — with trade-offs and your recommendation
4. **Section-by-section design approval** — architecture, data model, API, UI, testing, deployment
5. **Write design document** — save to `docs/plans/YYYY-MM-DD-<topic>-design.md` and commit
6. **Transition to initialization** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-init`

**The terminal state is invoking long-task-init.** Do NOT invoke any other implementation skill.

## Step 1: Read SRS & Extract Design Inputs

1. Read the approved SRS document from `docs/plans/*-srs.md`
2. Extract key design drivers:
   - **Functional scope** — FR count, priority distribution, dependency chains
   - **NFR thresholds** — performance targets, reliability, scalability that affect architecture
   - **Constraints** — hard limits that restrict technology/approach choices
   - **Interface requirements** — external systems, protocols, data formats to integrate with
   - **User personas** — technical levels that affect API/UI design decisions
3. List any SRS **Open Questions** that must be resolved before design can proceed
   - If unresolved questions affect architecture → ask user via `AskUserQuestion` before Step 2

## Step 2: Explore Technical Context

1. Explore existing code / repos the project will build on
2. Identify technical constraints not in the SRS (e.g., monorepo structure, CI/CD pipeline, existing libraries)
3. Check for a design document template:
   - If the user specified a template path → read and validate it
   - Else → read `docs/templates/design-template.md` (the default template shipped with this skill)
   - **Validation**: template must be a `.md` file containing at least one `## ` heading

## Step 3: Propose Approaches

Present **2-3 implementation approaches** with explicit trade-offs:

```markdown
## Approach A: [Name]
**How it works**: [1-2 sentences]
**Pros**: [bullet list]
**Cons**: [bullet list]
**Best when**: [conditions]
**NFR impact**: [how this approach affects the SRS NFR thresholds]

## Approach B: [Name]
...

## Recommendation: Approach [X]
**Reason**: [why this fits best given the SRS constraints and NFRs]
```

**Key**: Each approach must be evaluated against the SRS constraints and NFR thresholds. An approach that cannot meet a "Must" NFR is disqualified.

## Step 4: Section-by-Section Approval

For non-trivial projects, break the design into sections and get approval per section:

1. **Architecture overview** — system components, data flow, tech stack decisions
   - Must justify tech stack choices against SRS constraints
   - Must show how NFR thresholds will be met
2. **Data model** — schemas, relationships, storage strategy
3. **API / interface design** — endpoints, contracts, protocols
   - Must align with SRS Interface Requirements (IFR-xxx)
4. **UI/UX approach** (if applicable) — layout strategy, interaction patterns
   - Must address SRS User Personas
5. **Testing strategy** — test types, coverage targets, tooling
   - Must cover all SRS acceptance criteria
6. **Deployment / infrastructure** (if applicable) — hosting, CI/CD, environments

Present each section. Wait for user feedback. Incorporate changes before moving to the next.

**For simple projects** (< 5 features): Combine all sections into a single approval step.

## Step 5: Write Design Document

Save the approved design to `docs/plans/YYYY-MM-DD-<topic>-design.md`.

### Template usage

Read the template found in Step 2 (user-specified or default `docs/templates/design-template.md`):
1. Preserve the template's heading structure
2. Replace guidance text under each heading with approved design content
3. Add metadata at top if not already present (`Date`, `Status`, `SRS Reference`, `Template` path)
4. For uncovered template sections: mark "[Not applicable]"
5. For approved content without matching template section: append as "Additional Notes"

## Step 6: Transition to Initializer

Once the design document is saved and committed:

1. Summarize key inputs the Initializer will need:
   - **From SRS**: constraints, assumptions, NFRs, user personas, glossary, functional requirements → features
   - **From Design**: tech stack, architecture decisions → `tech_stack` in feature-list.json, project skeleton
2. **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-init` to scaffold the project

## Scaling the Design Phase

| Project Size | Features | Design Depth |
|---|---|---|
| Tiny | 1-5 | Single paragraph approach + 1 approval step |
| Small | 5-20 | 2-3 approach options + combined section approval |
| Medium | 20-50 | Full multi-section approval |
| Large | 50-200+ | Full multi-section approval + architecture diagrams |

## Red Flags

| Rationalization | Correct Response |
|---|---|
| "The SRS already implies the architecture" | SRS describes WHAT, not HOW. Present options. |
| "There's only one way to build this" | Present at least 2 approaches. Even obvious choices benefit from stated trade-offs. |
| "I already know the best approach" | Present options, let the user choose |
| "The user seems impatient, I'll skip design" | Explain the value briefly, then run efficiently |
| "I'll design as I go" | Upfront design is cheaper than mid-session corrections |
| "Let me re-clarify requirements here" | Requirements belong in the SRS. If missing, note as Open Question and resolve with user before design. |

## Integration

**Called by:** using-long-task (when SRS exists, no design doc, no feature-list.json)
**Requires:** Approved SRS at `docs/plans/*-srs.md`
**Chains to:** long-task-init (after design approval)
**Produces:** `docs/plans/YYYY-MM-DD-<topic>-design.md`
