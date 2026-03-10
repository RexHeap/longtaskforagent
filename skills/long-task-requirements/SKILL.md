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
4. **Write requirements** — apply EARS templates, assign IDs, write acceptance criteria, generate diagrams
5. **Validate SRS** — check 8 quality attributes, detect anti-patterns, verify testability
6. **SRS Compliance Review** — dispatch srs-reviewer subagent; gate: all R/A/C/S/D checks PASS before proceeding
7. **Present & approve SRS** — section-by-section for non-trivial projects
8. **Save SRS document** — `docs/plans/YYYY-MM-DD-<topic>-srs.md` and commit
9. **Transition to UCD** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-ucd` (it auto-skips to design if no UI features in SRS)

**The terminal state is invoking long-task-ucd.** Do NOT invoke any other skill.

## Step 1: Explore Context

1. Read the user-provided requirement doc / idea description thoroughly
2. Explore existing code / repos the project will build on or integrate with
3. Identify initial constraints: tech stack, platform, integrations, regulations
4. Check for an SRS template:
   - If the user specified a template path → read and validate it
   - Else → read `docs/templates/srs-template.md` (the default template shipped with this skill)
   - **Validation**: template must be a `.md` file containing at least one `## ` heading

## Step 2: Structured Elicitation

Use `AskUserQuestion` to elicit requirements in **multi-question rounds** — each round covers one topic area with up to 4 related questions. Follow the CAPTURE → CHALLENGE → CLARIFY cycle for each area.

**How to ask:**
- **Batch by topic** — group 2-4 related questions into a single `AskUserQuestion` call per round
- **Multiple choice preferred** — provide 2-4 options per question to reduce cognitive load
- **Assume and confirm** — state your assumption, let the user correct
- **Scenario-based for edge cases** — "What should happen when [X] fails?"
- **Quantify immediately** — replace vague words with numbers in the question itself
- **Follow up within round** — if an answer in round N reveals ambiguity, address it in round N+1 before moving to the next topic

**Elicitation rounds** (adapt order and grouping to project context):

### Round 1: Purpose & Scope
Ask in a single `AskUserQuestion` call (up to 4 questions):
- What is the core problem this system solves?
- Who are the primary users? (personas, technical levels)
- What is explicitly **out of scope** for this version?
- What is the target release scope? (MVP vs full)

### Round 2–N: Functional Requirements
For each capability area, ask per round (up to 4 questions):
- What does the user do? (trigger/action)
- What does the system do in response? (observable behavior)
- What are the error / edge / boundary cases?
- Confirm a concrete Given/When/Then example

Group related capabilities into the same round when they share a workflow. Split large capability areas across multiple rounds.

### Round N+1: Non-Functional Requirements
Batch NFR probes into 1-2 rounds by relevance:

| Category (ISO 25010) | Probe |
|---|---|
| **Performance** | Response time target? Throughput? Concurrent users? |
| **Reliability** | Uptime target? Recovery time? Data loss tolerance? |
| **Usability** | Accessibility requirements? Learnability criteria? |
| **Security** | Authentication method? Authorization model? Data encryption? |
| **Maintainability** | Modularity constraints? Test coverage targets? |
| **Portability** | Platform restrictions? Browser support? |
| **Scalability** | Current load? Target load? Growth timeline? |

Skip categories clearly irrelevant to the project. **Rule**: Every NFR must have a **measurable criterion**. "Fast" → "p95 response time < 200ms under 1000 concurrent users".

### Round N+2: Constraints, Assumptions & Interfaces
Combine into one round (up to 4 questions):
- Hard limits (hosting, budget, licenses, regulatory, existing systems)
- What is assumed to be true? What breaks if the assumption is wrong?
- External systems to integrate with? Protocols and data formats?
- Existing APIs to preserve backward compatibility?

### Round N+3: Glossary & Terminology
Ask in one round if needed:
- Domain terms with potential ambiguity?
- Synonyms to unify? Homonyms to distinguish?

**When to stop:** Move to Step 3 when you can describe every functional capability, its acceptance criteria, all NFRs with measurable thresholds, all constraints, and all assumptions — without guessing.

**Rule**: Batch related questions per round (2-4 per `AskUserQuestion` call). Only split into single questions when a topic requires deep sequential probing (e.g., complex workflow with branching logic).

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

### 4c. Generate Diagrams

After all requirements are written, generate two Mermaid visual aids and place them in the SRS template sections reserved for them.

#### Use Case View (place in Section 3.1 of the SRS)

Generate one `graph LR` diagram with:
- All actors from Section 3 as external nodes — use ellipse syntax: `Actor((Name))`
- All FR-xxx titles as use case nodes inside a `subgraph System Boundary` enclosure
- One directed edge per actor-to-use-case participation implied by the acceptance criteria
- Every actor must have at least one edge; every FR must appear as a use case node

#### Process Flows (place in Section 4.1 of the SRS)

Generate one `flowchart TD` per functional area. A functional area qualifies if it has:
- 3+ sequential steps, OR
- At least one decision/branching node in its acceptance criteria

Rules per diagram:
- Start node: `([Start: <trigger>])`, End node: `([End: <outcome>])` — rounded stadium style
- Decision node: diamond `{condition?}`, with `-- YES -->` and `-- NO -->` labeled branches
- Every error/boundary case from acceptance criteria must appear as a branch path
- Use a `####` subheading naming each workflow (e.g., `#### Flow: User Registration`)

Scope: one combined flow if the SRS has ≤4 requirements with no branching; one flow per functional area if the SRS has ≥5 requirements across 2+ areas.

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

## Step 6: SRS Compliance Review

Dispatch a subagent to independently verify the SRS against ISO/IEC/IEEE 29148 standards and diagram requirements before presenting to the user. This is mandatory — self-validation in Step 5 is not a substitute.

### 6a. Dispatch SRS Reviewer Subagent

```
Task(
  subagent_type="general-purpose",
  prompt="""
  You are an SRS compliance reviewer aligned with ISO/IEC/IEEE 29148.
  Read the reviewer prompt at: skills/long-task-requirements/prompts/srs-reviewer-prompt.md

  Project context:
  {project_context}

  Full SRS draft (all sections):
  {srs_draft}

  Requirement ID list:
  {requirement_id_list}

  Perform the review following the prompt exactly.
  """
)
```

### 6b. Review Gate Logic

**ALL checks must PASS to proceed to Step 7:**
- Group R (R1-R8): quality attributes — every requirement passes all 8 checks
- Group A (A1-A6): anti-patterns — none found in the full SRS
- Group C (C1-C5): completeness — all cross-checks confirmed
- Group S (S1-S4): structural compliance — all required sections present
- Group D (D1-D4): diagrams — Use Case View and Process Flows present and populated

**On FAIL — two-track resolution:**

**Track 1: USER-INPUT items → ask immediately**

Read the reviewer's "Clarification Questions" table. If any rows are present (USER-INPUT items exist):

Use `AskUserQuestion` with a targeted questionnaire — do NOT dump the full review report. Format:
```
The SRS needs clarification on a few points before I can finalize it. Please answer:

1. [FR-xxx] [Issue in plain language]
   Your requirement says "[exact phrase]". What is the correct value?
   (e.g., [example format/unit])

2. [FR-yyy] [Next issue]
   ...
```

**Do NOT guess or invent answers. WAIT for the user's response before proceeding.**

After receiving answers: incorporate them into the SRS draft.

**Track 2: LLM-FIXABLE items → auto-fix**

Fix all LLM-FIXABLE items in parallel: split compound requirements, add actors, populate sections, generate diagrams, assign IDs. Apply these together with any user answers from Track 1.

**Re-dispatch reviewer (Cycle 2)**

Re-dispatch the subagent with the revised draft. If Cycle 2 PASS → proceed to Step 7.

**If Cycle 2 still fails:**
- New USER-INPUT items found → use `AskUserQuestion` again with the same targeted format
- Only LLM-FIXABLE items remain after 2 cycles → use `AskUserQuestion` with:
  - Table of remaining failures (check ID, location, issue description)
  - Summary of fixes attempted
  - Request for user direction (fix, waive, or restructure)

**Maximum: 2 re-dispatch cycles.** Never attempt Cycle 3 without user input.

After all groups PASS, record the review outcome in the SRS header:
```markdown
<!-- SRS Review: PASS after N cycle(s) — YYYY-MM-DD -->
```

## Step 7: Present & Approve SRS

For non-trivial projects, present section by section and get approval per section:

1. **Purpose, Scope & Exclusions** — boundaries and what's NOT included
2. **Glossary & User Personas** — shared vocabulary and user understanding
3. **Functional Requirements** — core capabilities with acceptance criteria
4. **Non-Functional Requirements** — quality attributes with metrics
5. **Constraints, Assumptions & Interfaces** — hard limits and external contracts

Present each section. Wait for user feedback. Incorporate changes before moving to the next.

**For simple projects** (< 5 functional requirements): combine all sections into a single approval step.

## Step 8: Save SRS Document

Save the approved SRS to `docs/plans/YYYY-MM-DD-<topic>-srs.md`.

### Template usage

Read the template found in Step 1 (user-specified or default `docs/templates/srs-template.md`):
1. Preserve the template's heading structure
2. Replace guidance text under each heading with approved SRS content
3. Add metadata at top if not already present (`Date`, `Status`, `Standard`, `Template` path)
4. For uncovered template sections: mark "[Not applicable]"
5. For approved content without matching template section: append as "Additional Notes"

## Step 9: Transition to UCD

Once the SRS document is saved and committed:

1. Summarize key inputs the next phase will need:
   - Functional requirement count and priority distribution
   - Key constraints that affect architecture choices
   - NFR thresholds that affect technology selection
   - Whether the SRS contains UI-related functional requirements (determines if UCD runs or auto-skips)
2. **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-ucd` to generate UCD style guide (auto-skips to design if no UI features)

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
**Chains to:** long-task-ucd (after SRS approval; auto-skips to design if no UI features)
**Produces:** `docs/plans/YYYY-MM-DD-<topic>-srs.md`
