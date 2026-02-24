---
name: long-task-design
description: "Use when no design doc and no feature-list.json exist - brainstorm requirements and create approved design document before any implementation"
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs through natural collaborative dialogue. Start by understanding the project context, then ask questions one at a time. Once you understand what you're building, present the design and get user approval.

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, run init_project.py, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need A Design"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but you MUST present it and get approval.

## Checklist

You MUST create a TodoWrite task for each of these items and complete them in order:

1. **Explore project context** — check files, docs, recent commits; detect design template
2. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
3. **Propose 2-3 approaches** — with trade-offs and your recommendation
4. **Present design** — in sections scaled to complexity, get user approval after each section
5. **Write design doc** — save to `docs/plans/YYYY-MM-DD-<topic>-design.md` and commit
6. **Transition to initialization** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-init`

**The terminal state is invoking long-task-init.** Do NOT invoke any other implementation skill.

## Step 1: Explore Context

1. Read the user-provided requirement doc thoroughly
2. Read the user-provided design doc (if any)
3. Explore existing code/repos the project will build on or integrate with
4. Identify constraints: tech stack, platform, integrations, performance requirements
5. Check for a design document template:
   - If the user specified a template path → read and validate it
   - Else if `docs/templates/design-template.md` exists → read it and confirm with the user
   - Else → use the default template
   - **Validation**: template must be a `.md` file containing at least one `## ` heading

## Step 2: Clarify Requirements

Ask clarifying questions **one at a time** using `AskUserQuestion`, focused on purpose, constraints, and success criteria.

**How to ask:**
- **Multiple choice preferred** — provide 2-4 options to reduce cognitive load
- **Assume and confirm** — state your assumption, let the user correct
- **Scenario-based for edge cases** — "What should happen when [X] fails?"

**What to clarify:**
- Ambiguous requirements ("What does 'fast' mean — sub-100ms or sub-1s?")
- Missing information ("The doc mentions auth but doesn't specify — JWT, session, or OAuth?")
- Scope boundaries ("Should the MVP include feature X or is that post-launch?")
- Priority conflicts ("Both A and B are marked high-priority but they conflict — which wins?")

**Probes (ask when not covered in requirement doc):**

| Category | Example Questions |
|----------|------------------|
| **NFRs** | Response time? Concurrent users? Uptime target? Compliance? |
| **System constraints** | Hosting restrictions? Existing DB/API? License restrictions? |
| **Assumptions** | What's pre-validated upstream? Which existing behaviours must be preserved? |
| **User personas** (if UI) | Primary user? Technical level? Critical workflow? Accessibility? |
| **Glossary** (if domain terms) | Confirm canonical names; note synonyms to avoid in code |

**When to stop:** Move to Step 3 when you can describe the system's purpose, key NFRs, hard constraints, key assumptions, and how to verify success — without guessing.

**Rule**: Do NOT batch questions. Ask one, wait for answer, then ask the next.

## Step 3: Propose Approaches

Present **2-3 implementation approaches** with explicit trade-offs:

```markdown
## Approach A: [Name]
**How it works**: [1-2 sentences]
**Pros**: [bullet list]
**Cons**: [bullet list]
**Best when**: [conditions]

## Approach B: [Name]
...

## Recommendation: Approach [X]
**Reason**: [why this fits best given the constraints]
```

## Step 4: Section-by-Section Approval

For non-trivial projects, break the design into sections and get approval per section:

1. **Architecture overview** — system components, data flow, tech stack
2. **Data model** — schemas, relationships, storage strategy
3. **API / interface design** — endpoints, contracts, protocols
4. **UI/UX approach** (if applicable) — layout strategy, interaction patterns
5. **Testing strategy** — test types, coverage targets, tooling
6. **Deployment / infrastructure** (if applicable) — hosting, CI/CD, environments

Present each section. Wait for user feedback. Incorporate changes before moving to the next.

**For simple projects** (< 5 features): Combine all sections into a single approval step.

## Step 5: Write Design Document

Save the approved design to `docs/plans/YYYY-MM-DD-<topic>-design.md`.

### Using a custom template

If a design template was found in Step 1:
1. Preserve the template's heading structure
2. Replace guidance text under each heading with approved design content
3. Add metadata at top if not already present (`Date`, `Status`, `Template` path)
4. For uncovered template sections: mark "[Not applicable]"
5. For approved content without matching template section: append as "Additional Notes"

### Using the default template

```markdown
# [Project Name] — Design Document

**Date**: YYYY-MM-DD
**Status**: Approved

## Requirements Summary
[Condensed requirements from user docs]

## Non-Functional Requirements
| Category | Requirement | Measurable Criterion |
|----------|-------------|---------------------|
| Performance | [e.g., API response time] | [e.g., p95 < 200ms] |
[If no NFRs apply, write "None identified" and state why]

## System Constraints
- [Hard limits that affect architecture — one per line]
[If none, write "None identified"]

## Assumptions & Dependencies
- [Explicit beliefs about environment or callers — one per line]
[If none, write "None identified"]

## Target Users
| Persona | Technical Level | Key Needs |
|---------|-----------------|-----------|
[Omit if no UI features in scope]

## Glossary
| Term | Canonical Definition | Do NOT confuse with |
|------|---------------------|---------------------|
[Omit or "None identified" if no ambiguous terms]

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

## Step 6: Transition to Initializer

Once the design document is saved and committed:

1. **Extract SRS content** for the Initializer:
   - `constraints[]` — from "System Constraints" section
   - `assumptions[]` — from "Assumptions & Dependencies" section
   - NFR rows → will become `category: "non-functional"` features
   - "Target Users" + "Glossary" → will become `docs/project-context.md`

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
| "This is too simple for a design phase" | Run lightweight design (single approval step) |
| "The requirement doc is already detailed enough" | Requirement docs describe WHAT, not HOW |
| "I already know the best approach" | Present options, let the user choose |
| "The user seems impatient, I'll skip design" | Explain the value briefly, then run efficiently |
| "I'll design as I go" | Upfront design is cheaper than mid-session corrections |

## Integration

**Called by:** using-long-task (when no design doc and no feature-list.json)
**Chains to:** long-task-init (after design approval)
**Produces:** `docs/plans/YYYY-MM-DD-<topic>-design.md`
