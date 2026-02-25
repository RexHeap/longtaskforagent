---
name: long-task-requirements
description: "Use when no SRS doc and no design doc and no feature-list.json exist - elicit requirements through structured questioning and produce a high-quality SRS document aligned with ISO/IEC/IEEE 29148"
---

# Requirements Elicitation & SRS Generation

Turn raw ideas into a structured, high-quality Software Requirements Specification (SRS) through systematic elicitation, challenge, and validation — aligned with ISO/IEC/IEEE 29148 and EARS requirement syntax.

<HARD-GATE>
Do NOT invoke any design skill, implementation skill, write any code, scaffold any project, or take any design/implementation action until you have presented the SRS and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need an SRS"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The SRS can be short (a few sentences for truly simple projects), but you MUST present it and get approval.

## Checklist

You MUST create a TodoWrite task for each of these items and complete them in order:

1. **Explore project context** — read existing docs, code, constraints; detect SRS template
2. **Structured elicitation** — ask clarifying questions one at a time, challenge each requirement
3. **Classify requirements** — functional / NFR / constraint / assumption / interface / exclusion
4. **Write requirements** — apply EARS templates, assign IDs, write acceptance criteria
5. **Validate SRS** — check 8 quality attributes, detect anti-patterns, verify testability
6. **Present & approve SRS** — section-by-section for non-trivial projects
7. **Save SRS document** — `docs/plans/YYYY-MM-DD-<topic>-srs.md` and commit
8. **Transition to design** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-design`

**The terminal state is invoking long-task-design.** Do NOT invoke any other skill.

## Step 1: Explore Context

1. Read the user-provided requirement doc / idea description thoroughly
2. Explore existing code / repos the project will build on or integrate with
3. Identify initial constraints: tech stack, platform, integrations, regulations
4. Check for an SRS template:
   - If the user specified a template path → read and validate it
   - Else → read `docs/templates/srs-template.md` (the default template shipped with this skill)
   - **Validation**: template must be a `.md` file containing at least one `## ` heading

## Step 2: Structured Elicitation

Ask clarifying questions **one at a time** using `AskUserQuestion`. Follow the CAPTURE → CHALLENGE → CLARIFY cycle for each requirement area.

**How to ask:**
- **Multiple choice preferred** — provide 2-4 options to reduce cognitive load
- **Assume and confirm** — state your assumption, let the user correct
- **Scenario-based for edge cases** — "What should happen when [X] fails?"
- **Quantify immediately** — replace vague words with numbers in the question itself

**Elicitation sequence** (adapt order to project context):

### 2a. Purpose & Scope
- What is the core problem this system solves?
- Who are the primary users? (personas, technical levels)
- What is explicitly **out of scope** for this version?

### 2b. Functional Requirements
For each capability area:
- What does the user do? (trigger/action)
- What does the system do in response? (observable behavior)
- What are the error / edge / boundary cases?
- Provide a concrete Given/When/Then example and ask user to confirm or correct

### 2c. Non-Functional Requirements (quantify each)
| Category (ISO 25010) | Probe |
|---|---|
| **Performance** | Response time target? Throughput? Concurrent users? |
| **Reliability** | Uptime target? Recovery time? Data loss tolerance? |
| **Usability** | Accessibility requirements? Learnability criteria? |
| **Security** | Authentication method? Authorization model? Data encryption? |
| **Maintainability** | Modularity constraints? Test coverage targets? |
| **Portability** | Platform restrictions? Browser support? |
| **Scalability** | Current load? Target load? Growth timeline? |

**Rule**: Every NFR must have a **measurable criterion**. "Fast" → "p95 response time < 200ms under 1000 concurrent users".

### 2d. Constraints & Assumptions
- Hard limits (hosting, budget, licenses, regulatory, existing systems)
- What is assumed to be true? What breaks if the assumption is wrong?

### 2e. Interface Requirements
- External systems to integrate with?
- Data formats, protocols, API contracts?
- Existing APIs to preserve backward compatibility?

### 2f. Glossary
- Domain terms with potential ambiguity?
- Synonyms to unify? Homonyms to distinguish?

**When to stop:** Move to Step 3 when you can describe every functional capability, its acceptance criteria, all NFRs with measurable thresholds, all constraints, and all assumptions — without guessing.

**Rule**: Do NOT batch questions. Ask one, wait for answer, then ask the next.

## Step 3: Classify Requirements

Organize captured requirements into categories:

| Category | ID Prefix | Description |
|---|---|---|
| Functional | FR-001 | Observable system behaviors |
| Non-Functional | NFR-001 | Quality attributes with measurable criteria |
| Constraint | CON-001 | Hard limits that restrict the solution space |
| Assumption | ASM-001 | Beliefs assumed true; document invalidation risk |
| Interface | IFR-001 | External system contracts |
| Exclusion | EXC-001 | Explicitly out of scope |

## Step 4: Write Requirements with EARS Templates

Apply the EARS (Easy Approach to Requirements Syntax) template to each functional requirement:

| Pattern | Template | When to use |
|---|---|---|
| **Ubiquitous** | The system shall `<action>`. | Always-on behavior |
| **Event-driven** | When `<trigger>`, the system shall `<action>`. | Response to user/system event |
| **State-driven** | While `<state>`, the system shall `<action>`. | Behavior depends on mode/state |
| **Unwanted behavior** | If `<condition>`, then the system shall `<action>`. | Error handling, fault tolerance |
| **Optional** | Where `<feature/config>`, the system shall `<action>`. | Configurable/optional capability |

**For each requirement, also write:**
- **Acceptance criteria** — at least one concrete Given/When/Then scenario
- **Priority** — Must / Should / Could / Won't (MoSCoW)
- **Source** — which stakeholder need or user story this traces to

## Step 5: Validate SRS Quality

Run a systematic quality check against the **8 quality attributes** (IEEE 830 / ISO 29148):

### 5a. Per-Requirement Checks

For EACH requirement, verify:

| # | Attribute | Check | Red flag |
|---|---|---|---|
| 1 | **Correct** | Traces to a confirmed stakeholder need? | Orphan requirement (gold-plating) |
| 2 | **Unambiguous** | Two readers would write the same test case? | Weasel words: "fast", "robust", "user-friendly", "intuitive", "flexible" |
| 3 | **Complete** | All inputs, outputs, error cases, boundaries defined? | "including but not limited to...", unbounded lists |
| 4 | **Consistent** | No contradiction with other requirements? | Timing conflicts, format conflicts |
| 5 | **Ranked** | Has a MoSCoW priority? | Everything is "high priority" |
| 6 | **Verifiable** | Can write a pass/fail test? | "The system shall be easy to use" (no metric) |
| 7 | **Modifiable** | Stated in exactly one place? | Duplicated across sections |
| 8 | **Traceable** | Has unique ID + source link? | Missing ID or orphan |

### 5b. Anti-Pattern Detection

Scan the full SRS for these anti-patterns and fix before presenting:

| Anti-Pattern | Detection Signal | Fix |
|---|---|---|
| **Ambiguous adjective** | "fast", "large", "scalable", "reliable" without number | Quantify with measurable criterion |
| **Compound requirement** | "and" / "or" joining two distinct capabilities | Split into separate requirements |
| **Design leakage** | Implementation vocabulary: "class", "table", "endpoint", "algorithm" | Rewrite as observable behavior |
| **Passive without agent** | "data shall be validated" — by whom? | Add explicit actor: "The system shall..." |
| **TBD / TBC** | Unresolved placeholders | Resolve with user or mark as Open Question |
| **Missing negatives** | Only positive cases specified | Add error/boundary/security cases |
| **Untestable NFR** | NFR without measurable threshold | Add concrete metric + measurement method |

### 5c. Completeness Cross-Check

- Every functional area has at least one error/boundary case
- All external interfaces have data format + protocol specified
- All NFRs have measurement method, not just target
- Glossary covers all domain-specific terms used in requirements
- Out-of-Scope section explicitly lists deferred features

## Step 6: Present & Approve SRS

For non-trivial projects, present section by section and get approval per section:

1. **Purpose, Scope & Exclusions** — boundaries and what's NOT included
2. **Glossary & User Personas** — shared vocabulary and user understanding
3. **Functional Requirements** — core capabilities with acceptance criteria
4. **Non-Functional Requirements** — quality attributes with metrics
5. **Constraints, Assumptions & Interfaces** — hard limits and external contracts

Present each section. Wait for user feedback. Incorporate changes before moving to the next.

**For simple projects** (< 5 functional requirements): combine all sections into a single approval step.

## Step 7: Save SRS Document

Save the approved SRS to `docs/plans/YYYY-MM-DD-<topic>-srs.md`.

### Template usage

Read the template found in Step 1 (user-specified or default `docs/templates/srs-template.md`):
1. Preserve the template's heading structure
2. Replace guidance text under each heading with approved SRS content
3. Add metadata at top if not already present (`Date`, `Status`, `Standard`, `Template` path)
4. For uncovered template sections: mark "[Not applicable]"
5. For approved content without matching template section: append as "Additional Notes"

## Step 8: Transition to Design

Once the SRS document is saved and committed:

1. Summarize key inputs the design phase will need:
   - Functional requirement count and priority distribution
   - Key constraints that affect architecture choices
   - NFR thresholds that affect technology selection
2. **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-design` to begin design

## Scaling the Requirements Phase

| Project Size | Functional Reqs | Depth |
|---|---|---|
| Tiny | 1-5 | Single-page SRS, combined approval step |
| Small | 5-15 | Standard SRS, 2-3 approval sections |
| Medium | 15-50 | Full SRS with all sections, per-section approval |
| Large | 50-200+ | Full SRS + interface specs + domain model |

## Red Flags

| Rationalization | Correct Response |
|---|---|
| "This is too simple for an SRS" | Run lightweight SRS (single approval step) |
| "The user already described what they want" | User descriptions are raw input; SRS adds structure, completeness, testability |
| "I can figure out the requirements during design" | Requirements define WHAT; discovering them during HOW causes rework |
| "NFRs don't apply to this project" | Every project has at least implicit performance/reliability needs — make them explicit |
| "The glossary is obvious" | Obvious to whom? Define every term the user and developer might interpret differently |
| "I'll just start with the happy path" | Error cases, boundaries, and negatives must be captured NOW |

## Integration

**Called by:** using-long-task (when no SRS doc, no design doc, and no feature-list.json)
**Chains to:** long-task-design (after SRS approval)
**Produces:** `docs/plans/YYYY-MM-DD-<topic>-srs.md`
