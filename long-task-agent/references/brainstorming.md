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
5. Check for a design document template:
   - If the user specified a template path → read and validate it
   - Else if `docs/templates/design-template.md` exists in the project directory → read it and confirm with the user: "Found design template at `docs/templates/design-template.md`. Use it for the design document structure?"
   - Else → use the default template (no action needed)
   - **Validation**: template must be a `.md` file containing at least one `## ` heading. If invalid, warn the user and offer to fall back to the default template.

### Step 2: Clarify Requirements

Ask clarifying questions **one at a time** using `AskUserQuestion`, focused on **purpose, constraints, and success criteria**.

**How to ask:**
- **Multiple choice preferred** — provide 2-4 options to reduce user cognitive load ("Auth approach? [JWT / session-based / OAuth 2.0 / other]")
- **Assume and confirm** — state your assumption, let the user correct ("I'm assuming JWT for auth — correct, or do you prefer session-based?")
- **Scenario-based for edge cases** — "What should happen when [X] fails?" is better than "How should errors be handled?"

**What to clarify:**
- Ambiguous requirements ("What does 'fast' mean — sub-100ms or sub-1s?")
- Missing information ("The doc mentions auth but doesn't specify — JWT, session, or OAuth?")
- Scope boundaries ("Should the MVP include feature X or is that post-launch?")
- Priority conflicts ("Both A and B are marked high-priority but they conflict — which wins?")

**Non-Functional Requirements probe** — ask when not explicitly covered in the requirement doc:
- Performance: "What's the acceptable response time? Expected concurrent users / requests per second?"
- Security: "Any auth, encryption, or compliance requirements? (e.g., OWASP Top 10, GDPR, HIPAA)"
- Availability: "What's the uptime target? Any SLA/SLO? Acceptable downtime window?"
- Scalability: "What user or data growth is expected in the next 12 months?"
- Compatibility: "Target browsers / OS / runtime versions? Any accessibility requirements (WCAG)?"

**System constraints probe** — capture hard limits that shape architecture:
- Deployment: "Any hosting restrictions? (offline/intranet/specific cloud/no Docker)"
- Existing infrastructure: "Must reuse any existing DB, API, or service? Must stay compatible with any version?"
- Legal/license: "Any open-source license restrictions? (e.g., GPL forbidden)"
- Team/budget: "Any runtime cost ceilings? Team size or skill constraints that affect tech choices?"

**Assumptions probe** — surface implicit beliefs before they cause cross-session drift:
- "What do you assume is true about the environment that callers won't need to verify?"
- "Are there upstream services or data that are expected to be pre-validated before reaching this system?"
- "Which behaviours from the existing system must be preserved unchanged?"

**User personas probe** (ask when UI features are in scope):
- "Who is the primary user? Technical level? (developer / analyst / end-customer / admin)"
- "Any accessibility needs? Language/locale requirements?"
- "What is the single most critical user workflow — the one that must never be broken?"

**Glossary probe** (ask when domain terms appear in the requirement doc):
- Identify terms that could be ambiguous (e.g., "user", "order", "account", "bill", "project")
- Confirm the canonical name and definition for each ("When you say 'Invoice', do you mean the issued document or the internal DB record?")
- Note synonyms that must NOT be used interchangeably in code

**When to stop:** Move to Step 3 when you can describe the system's purpose, key NFRs, hard constraints, key assumptions, and how to verify success — without guessing.

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

#### Using a custom template

If a design template was found in Step 1:

1. Read the template file in full
2. Preserve the template's heading structure (all H1, H2, H3 headings)
3. Replace guidance text under each heading with the approved design content for that topic
4. Add standard metadata at the top if the template does not already include it:
   ```
   **Date**: YYYY-MM-DD
   **Status**: Approved
   **Template**: <path-to-template-file>
   ```
5. For template sections not covered during Step 4 approval, mark them "[Not applicable]" or fill with relevant content from the design discussion
6. For approved content that does not map to any template section, append an "Additional Notes" section

#### Using the default template

If no custom template was provided, use this structure:

```markdown
# [Project Name] — Design Document

**Date**: YYYY-MM-DD
**Status**: Approved

## Requirements Summary
[Condensed requirements from user docs]

## Non-Functional Requirements
| Category     | Requirement                        | Measurable Criterion                        |
|--------------|------------------------------------|---------------------------------------------|
| Performance  | [e.g., API response time]          | [e.g., p95 latency < 200ms at 100 rps]     |
| Security     | [e.g., authentication policy]      | [e.g., JWT + HTTPS only, OWASP Top 10]     |
| Availability | [e.g., uptime target]              | [e.g., 99.9% monthly uptime]               |
| Scalability  | [e.g., expected load growth]       | [e.g., support 10× users in 12 months]     |
| Compliance   | [e.g., data regulations]           | [e.g., GDPR: no PII in logs]               |

[If no NFRs apply, write "None identified" and state why]

## System Constraints
[Hard limits that affect architecture — one item per line, be specific]
- [e.g., Must run offline — no external API calls permitted]
- [e.g., Python 3.8+ only — no 3.10+ syntax]
- [e.g., GPL-licensed dependencies prohibited]
- [e.g., Must reuse existing PostgreSQL 14 instance]

[If no constraints, write "None identified"]

## Assumptions & Dependencies
[Explicit beliefs about the environment or caller behaviour — one item per line]
- [e.g., JWT validation is handled by API Gateway; business layer must NOT re-validate]
- [e.g., Input data is pre-sanitised before reaching this service]
- [e.g., Feature B will be completed before Feature C is implemented]

[If none, write "None identified"]

## Target Users
| Persona         | Technical Level | Key Needs / Constraints                   |
|-----------------|-----------------|-------------------------------------------|
| [Persona name]  | [low/med/high]  | [e.g., max 3 steps per workflow, Chinese UI] |

[Omit this section if no UI features are in scope]

## Glossary
| Term            | Canonical Definition                                   | Do NOT confuse with   |
|-----------------|--------------------------------------------------------|-----------------------|
| [Term]          | [Precise definition in this project's context]         | [Synonyms to avoid]   |

[Omit or write "None identified" if no domain-ambiguous terms exist]

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

#### Design template format

A design template is a standard markdown file whose headings define the output structure. No special syntax is needed.

- **H1 (`#`)** — Document title pattern (optional)
- **H2 (`##`)** — Major sections (at least one required)
- **H3 (`###`)** — Subsections (optional)
- Body text under headings — guidance for the agent; replaced with real design content in the output

**Conventional location**: `docs/templates/design-template.md` (auto-detected if present)

**Example**:

```markdown
# [Project] — Technical Design

**Date**: YYYY-MM-DD
**Status**: Draft | Approved

## Problem Statement
Describe the problem being solved.

## Goals and Non-Goals
### Goals
### Non-Goals

## Proposed Solution
### High-Level Design
### Detailed Design

## Alternatives Considered

## Testing Plan

## Open Questions
```

### Step 6: Transition to Initializer

Once the design document is saved and committed:
- Proceed to the Initializer phase
- Use the approved design to guide feature decomposition
- Reference the design document path in `task-progress.md`

**Before handing off to the Initializer**, extract SRS content from the design doc into the two worker-facing artifacts:

1. **`feature-list.json` root fields** (Initializer populates these during decomposition):
   - `constraints[]` — copy the "System Constraints" bullet list; each item is a string
   - `assumptions[]` — copy the "Assumptions & Dependencies" bullet list; each item is a string
   - NFR rows from "Non-Functional Requirements" → create `category: "non-functional"` features with measurable `verification_steps`

2. **`docs/project-context.md`** (Initializer LLM generates this file):
   - Contains "Target Users" table and "Glossary" table from the design doc
   - Stored at `docs/project-context.md` in the project root
   - Workers read this file when implementing UI features or when encountering domain term ambiguity
   - Template:
     ```markdown
     # Project Context

     ## Target Users
     | Persona | Technical Level | Key Needs |
     |---------|-----------------|-----------|
     | ...     | ...             | ...       |

     ## Glossary
     | Term | Definition | Do NOT confuse with |
     |------|-----------|---------------------|
     | ...  | ...        | ...                 |
     ```
   - Omit sections that have "None identified" in the design doc

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

## Design Template Reference

### What is a design template?

A markdown file whose heading structure defines the format for design documents. When provided, the agent follows the template's section layout instead of the default.

### How to specify a template

| Method | How | Priority |
|--------|-----|----------|
| Explicit | User tells the agent: "Use `path/to/template.md` as the design template" | Highest |
| Conventional location | Place a file at `docs/templates/design-template.md` in the project | Middle |
| Default | No template specified — agent uses the built-in template | Lowest (fallback) |

### Template validation rules

- Must be a `.md` file
- Must contain at least one `## ` (H2) heading
- If validation fails: warn the user, offer to use the default template

### What happens during Step 5

| Scenario | Agent behavior |
|----------|---------------|
| Template section maps to an approved topic | Fill with approved content |
| Template section was not discussed during approval | Mark "[Not applicable]" or fill with relevant discussion content |
| Approved content has no matching template section | Append as "Additional Notes" at the end |
| Template has metadata placeholders (Date, Status) | Fill with actual values |
