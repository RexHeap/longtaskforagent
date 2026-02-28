# Long-Task Agent

**A Claude Code skill plugin that turns single-session AI coding into a rigorous, multi-session software engineering workflow.**

Most AI coding assistants lose context after one conversation. Long-Task Agent solves this by implementing a six-phase architecture with persistent state bridging — enabling Claude Code to build complex projects across unlimited sessions with the discipline of a professional engineering team.

<!-- ILLUSTRATION: Hero Banner
![Hero Banner](docs/images/hero-banner.png)
> **Text-to-image prompt**: A wide panoramic digital illustration in a clean, modern tech style. A long horizontal pipeline flowing left to right, divided into six glowing phases labeled "Requirements → UCD → Design → Init → Worker → System Testing". Each phase is represented by a distinct geometric icon (clipboard, palette, blueprint, gear, hammer, checkmark shield). The pipeline sits above a translucent layer of JSON files, markdown documents, and git commits representing persistent state. Background is a subtle dark gradient with soft blue and purple accents. Minimalist, professional, suitable for a GitHub README hero image. 16:9 aspect ratio, 1920×540px.
-->

---

## Why Long-Task Agent?

| Problem | How Long-Task Agent Solves It |
|---------|-------------------------------|
| AI forgets everything after `/clear` | Persistent artifacts (`feature-list.json`, `task-progress.md`, git history) bridge sessions automatically |
| AI generates code without understanding requirements | ISO/IEC/IEEE 29148-aligned requirements elicitation produces an approved SRS before any code is written |
| AI skips testing or writes shallow tests | Strict TDD (Red→Green→Refactor) with coverage gates (≥90% line, ≥80% branch) and mutation testing (≥80% score) |
| AI produces inconsistent UI | UCD style guide with token-based design system ensures visual consistency across all features |
| AI drifts from the approved design | Automated spec & design compliance review after every feature |
| No way to add features to an existing project safely | Increment skill performs impact analysis, updates SRS/Design/UCD in place, tracks changes with waves |
| "Works on my machine" syndrome | System Testing phase (IEEE 829) with regression, integration, E2E, and NFR verification |

<!-- ILLUSTRATION: Problem vs Solution
![Problem vs Solution](docs/images/problem-solution.png)
> **Text-to-image prompt**: A split-screen comparison illustration. LEFT side (labeled "Without Long-Task Agent"): chaotic scene with tangled code lines, a broken chain of conversation bubbles fading away, red X marks on untested code, and a confused robot. RIGHT side (labeled "With Long-Task Agent"): orderly pipeline with connected phases, green checkmarks, test coverage badges, documents flowing between sessions via a golden bridge. Clean vector art style, tech-professional color palette (deep navy, electric blue, emerald green, coral red for problems). 16:9 aspect ratio, 1200×675px.
-->

---

## Core Philosophy

### 1. Requirements-Driven, Not Code-First

Every project starts with structured requirements elicitation — not coding. The SRS captures the *what*, the UCD captures the *look*, and the design document captures the *how*. No code is written until all three are approved.

### 2. Persistent State Bridges Sessions

Seven persistent artifacts ensure zero knowledge loss between sessions:

| Artifact | Purpose |
|----------|---------|
| `feature-list.json` | Structured task inventory with status tracking (JSON prevents model corruption) |
| `task-progress.md` | Session-by-session log with current state header |
| `docs/plans/*-srs.md` | Approved Software Requirements Specification |
| `docs/plans/*-design.md` | Approved technical design document |
| `docs/plans/*-ucd.md` | Approved UCD style guide (UI projects) |
| `RELEASE_NOTES.md` | Living changelog in Keep a Changelog format |
| Git history | Full change history with descriptive commits |

### 3. Quality is Non-Negotiable

Every feature passes through a gauntlet of automated quality gates — no exceptions, no shortcuts:

- **TDD Red→Green→Refactor** — tests are written before code, always
- **Coverage Gate** — line ≥90%, branch ≥80%
- **Mutation Gate** — mutation score ≥80% (catches tests that pass without actually testing anything)
- **Spec & Design Compliance Review** — every feature is checked against the SRS and design doc
- **UCD Compliance** — UI features are verified against style tokens

### 4. One Feature Per Cycle

Each worker session focuses on exactly one feature. This prevents context exhaustion, ensures clean commits, and keeps every feature independently verifiable.

<!-- ILLUSTRATION: Quality Gates Pipeline
![Quality Gates](docs/images/quality-gates.png)
> **Text-to-image prompt**: A vertical funnel/pipeline diagram showing a feature flowing through quality gates. From top to bottom: "TDD Red" (red test tube icon), "TDD Green" (green test tube), "Coverage Gate" (shield with "90%" badge), "TDD Refactor" (wrench icon), "Mutation Gate" (DNA helix with "80%" badge), "Compliance Review" (magnifying glass over document), and finally "Feature Passing ✓" (golden star). Each gate has a side arrow labeled "Fix & Retry" pointing back up. Clean infographic style, white background, color-coded stages. Portrait orientation, 800×1200px.
-->

---

## Six-Phase Architecture

```
Requirements (SRS) → UCD Style Guide → Design → Initializer → Worker Cycles → System Testing
     Phase 0a          Phase 0b        Phase 0c    Phase 1       Phase 2         Phase 3
                                                                    ↑
                                                          Increment (Phase 1.5)
                                                     (add features to live project)
```

<!-- ILLUSTRATION: Six-Phase Architecture Diagram
![Architecture](docs/images/architecture.png)
> **Text-to-image prompt**: A horizontal flowchart showing six connected phases of software development, drawn in an isometric 3D style. Phase 0a "Requirements" shows a person interviewing stakeholders with a clipboard. Phase 0b "UCD" shows a color palette and typography specimens. Phase 0c "Design" shows architectural blueprints and Mermaid diagrams. Phase 1 "Init" shows scaffolding and file generation. Phase 2 "Worker" shows a cyclical loop (TDD → Quality → Review → next feature) with a counter showing "Feature 3/15". Phase 3 "System Testing" shows a comprehensive test dashboard with green/red indicators. An arrow labeled "Increment" connects from below back to Phase 1, showing iterative development. Between each phase, glowing document icons (SRS, UCD, Design Doc, feature-list.json) flow as handoff artifacts. Soft gradient background, professional tech illustration. 16:9, 1600×900px.
-->

### Phase 0a: Requirements Elicitation

- Structured questioning aligned with ISO/IEC/IEEE 29148
- EARS requirement templates (Given/When/Then acceptance criteria)
- Anti-pattern detection: weasel words, compound requirements, design leakage
- Produces an approved **SRS** (`docs/plans/*-srs.md`)

### Phase 0b: UCD Style Guide

- Defines visual direction, color tokens, typography, spacing
- Generates text-to-image prompts for component mockups
- Auto-skips for non-UI projects
- Produces an approved **UCD** (`docs/plans/*-ucd.md`)

### Phase 0c: Design

- Proposes 2-3 approaches with trade-offs
- Per-feature Mermaid diagrams (class, sequence, flow)
- Third-party dependency versions with compatibility verification
- Produces an approved **Design Document** (`docs/plans/*-design.md`)

### Phase 1: Initialization

- Reads SRS + Design, scaffolds project skeleton
- Decomposes requirements into 10-200+ verifiable features
- Generates environment bootstrap scripts (`init.sh` / `init.ps1`)
- Creates initial git commit

### Phase 2: Worker Cycles

Each cycle follows a strict discipline:

```
Orient → Bootstrap → Config Gate → DevTools Gate → Plan
  → TDD Red → TDD Green → Coverage Gate
    → TDD Refactor → Mutation Gate
      → Compliance Review → Add Examples → Persist → Next Feature
```

### Phase 3: System Testing

- IEEE 829-aligned test planning with Requirements Traceability Matrix
- Regression, integration, E2E, NFR verification, exploratory testing
- Go/No-Go verdict — defects loop back to Worker for fixes

### Phase 1.5: Increment (Post-Launch Changes)

- Place an `increment-request.json` signal file → the skill auto-detects it
- Impact analysis against existing features
- Updates SRS, Design, UCD in place (git tracks history)
- Appends new features with wave metadata for traceability

<!-- ILLUSTRATION: Worker Cycle Detail
![Worker Cycle](docs/images/worker-cycle.png)
> **Text-to-image prompt**: A circular workflow diagram showing the Worker cycle in detail. The cycle starts at "Orient" (compass icon) at the top, then flows clockwise through: "Bootstrap" (rocket), "Config Gate" (key), "Plan" (map), "TDD Red" (red circle with failing test), "TDD Green" (green circle with passing test), "Coverage Gate" (bar chart showing 92%), "Refactor" (recycling arrows), "Mutation Gate" (DNA strand with score), "Review" (checklist), "Examples" (book), "Persist" (floppy disk + git icon). In the center of the circle: "ONE FEATURE" in bold. An arrow from "Persist" leads to either "Next Feature" (loops back to Orient) or "System Testing" (exits the cycle). Clean, modern infographic with consistent icon style. Square format, 1000×1000px.
-->

---

## 11-Skill Superpowers Architecture

Long-Task Agent uses an **on-demand skill loading** pattern — only the bootstrap router is loaded at session start; phase skills are loaded as needed, keeping context lean.

```
using-long-task (bootstrap router — always loaded)
   │
   ├─→ long-task-requirements ──→ long-task-ucd ──→ long-task-design ──→ long-task-init
   │                              (auto-skip if no UI)                        │
   │                                                                          ↓
   ├─→ long-task-increment (if increment-request.json exists)          long-task-work
   │                                                                     │  │  │
   │                                                              ┌──────┘  │  └──────┐
   │                                                              ↓         ↓         ↓
   │                                                         long-task  long-task  long-task
   │                                                           -tdd     -quality   -review
   │
   └─→ long-task-st (when all features pass)
```

| Skill | Role |
|-------|------|
| `using-long-task` | Bootstrap router — detects project state, invokes correct phase |
| `long-task-requirements` | ISO 29148 requirements elicitation → SRS |
| `long-task-ucd` | UCD style guide with design tokens |
| `long-task-design` | Technical design with trade-off analysis |
| `long-task-init` | Project scaffolding and feature decomposition |
| `long-task-work` | Worker orchestrator (one feature per cycle) |
| `long-task-tdd` | TDD Red→Green→Refactor discipline |
| `long-task-quality` | Coverage gate + mutation gate |
| `long-task-review` | Spec, design, and UCD compliance review |
| `long-task-increment` | Post-launch feature additions with impact analysis |
| `long-task-st` | IEEE 829 system testing with Go/No-Go verdict |

---

## Quick Start

### 1. Install

Clone this repository into your Claude Code skills directory:

```bash
# Clone into your project or a shared skills location
git clone https://github.com/anthropics/long-task-agent.git
```

### 2. Configure Hooks

The plugin uses a `SessionStart` hook to inject the router skill into every session. Copy or symlink the hooks configuration:

```bash
# The hooks/ directory contains:
# - hooks.json         → SessionStart hook config
# - session-start      → Phase detection script
# - run-hook.cmd       → Cross-platform wrapper
```

### 3. Start a New Project

Simply start a Claude Code session in your project directory. The bootstrap router auto-detects your project state and invokes the correct phase:

```
# No existing artifacts → starts Requirements phase
# SRS exists → starts UCD phase (or skips to Design if no UI)
# Design exists → starts Initialization phase
# feature-list.json exists → starts Worker or System Testing
```

Or use shortcut commands for explicit phase control:

```
/long-task:requirements  — Start requirements elicitation
/long-task:ucd           — Start UCD style guide generation
/long-task:design        — Start design phase
/long-task:init          — Initialize project after design approval
/long-task:work          — Start a Worker cycle
/long-task:st            — Run system testing
/long-task:increment     — Start incremental development
/long-task:status        — Check project progress
```

### 4. Scaffold a Project (Alternative: CLI)

```bash
# Basic initialization
python long-task-agent/scripts/init_project.py my-project --path ./my-project

# With language preset (auto-fills test/coverage/mutation tools)
python long-task-agent/scripts/init_project.py my-project --path ./my-project --lang python

# With custom quality thresholds
python long-task-agent/scripts/init_project.py my-project --path ./my-project --lang java \
  --line-cov 85 --branch-cov 75 --mutation-score 70
```

<!-- ILLUSTRATION: Quick Start Flow
![Quick Start](docs/images/quick-start.png)
> **Text-to-image prompt**: A step-by-step tutorial illustration showing four numbered steps arranged vertically. Step 1 "Install": a terminal window with a git clone command and a download arrow. Step 2 "Configure": a gear icon connecting to a hooks.json file. Step 3 "Start Session": a Claude Code terminal with the router auto-detecting project state, showing a decision tree with glowing path. Step 4 "Build": multiple session windows cascading, each showing a feature being completed with a green checkmark. Flat design, numbered circles (1-4) on the left margin, light background. Portrait, 800×1400px.
-->

---

## Multi-Language Support

Long-Task Agent is language-agnostic. It supports any tech stack through configurable tool settings:

| Language | Test Framework | Coverage | Mutation Testing |
|----------|---------------|----------|------------------|
| Python | pytest | pytest-cov | mutmut |
| Java | JUnit | JaCoCo | PIT (pitest) |
| TypeScript | Vitest / Jest | c8 / istanbul | Stryker |
| C/C++ | Google Test | gcov + lcov | Mull |
| *Custom* | *Any* | *Any* | *Any* |

The `tech_stack` field in `feature-list.json` drives all tool commands — use `get_tool_commands.py` to eliminate per-language lookup:

```bash
python long-task-agent/scripts/get_tool_commands.py feature-list.json
```

---

## Validation & Safety Scripts

The plugin includes a suite of validation scripts to prevent common failures:

| Script | Purpose |
|--------|---------|
| `validate_features.py` | Validates `feature-list.json` schema and data integrity |
| `validate_guide.py` | Validates `long-task-guide.md` structural completeness |
| `check_configs.py` | Verifies required environment configs before feature work |
| `check_devtools.py` | Verifies Chrome DevTools MCP availability for UI features |
| `check_st_readiness.py` | Confirms all features pass before system testing |
| `validate_increment_request.py` | Validates increment request signal file |
| `get_tool_commands.py` | Maps tech stack to CLI commands |

---

## How It Compares

<!-- ILLUSTRATION: Comparison Matrix
![Comparison](docs/images/comparison.png)
> **Text-to-image prompt**: A feature comparison matrix rendered as a clean infographic table. Rows represent capabilities: "Multi-session persistence", "Requirements elicitation", "TDD enforcement", "Coverage gates", "Mutation testing", "UI style consistency", "Design compliance review", "System testing", "Incremental development". Columns compare "Typical AI Coding" (mostly red X marks) vs "Long-Task Agent" (all green checkmarks). The Long-Task Agent column glows with a subtle highlight. Clean table design with alternating row colors, professional fonts. Landscape, 1200×800px.
-->

| Capability | Typical AI Coding | Long-Task Agent |
|------------|------------------|-----------------|
| Multi-session persistence | Manual copy-paste | Automatic via 7 persistent artifacts |
| Requirements process | "Just build it" | ISO 29148-aligned SRS with structured elicitation |
| Design process | Ad-hoc | 2-3 approaches with trade-offs, section-by-section approval |
| TDD discipline | Optional, often skipped | Mandatory Red→Green→Refactor for every feature |
| Test quality verification | Line coverage only (if any) | Coverage + mutation testing with configurable thresholds |
| UI consistency | Per-developer taste | UCD style guide with token-based design system |
| Post-implementation review | None | Automated spec & design compliance review |
| System testing | Manual QA | IEEE 829-aligned with RTM, Go/No-Go verdict |
| Adding features post-launch | Edit code directly | Impact analysis, tracked waves, document updates |
| Project state visibility | Read the code | `task-progress.md` + `feature-list.json` + `/long-task:status` |

---

## Project Structure

```
long-task-agent/
├── skills/                          # 11 skills (on-demand loaded)
│   ├── using-long-task/             # Bootstrap router
│   ├── long-task-requirements/      # Phase 0a: Requirements & SRS
│   ├── long-task-ucd/               # Phase 0b: UCD style guide
│   ├── long-task-design/            # Phase 0c: Design
│   ├── long-task-init/              # Phase 1: Initialization
│   ├── long-task-work/              # Phase 2: Worker orchestrator
│   ├── long-task-tdd/               # TDD discipline
│   ├── long-task-quality/           # Coverage + mutation gates
│   ├── long-task-review/            # Compliance review
│   ├── long-task-increment/         # Incremental development
│   └── long-task-st/               # System testing
├── scripts/                         # Validation & utility scripts
├── tests/                           # Test suite for all scripts
├── hooks/                           # SessionStart hook config
├── commands/                        # User shortcut commands
├── docs/templates/                  # Customizable SRS & design templates
└── CLAUDE.md                        # Cross-session navigation index
```

---

## Guiding Principles

> **"Measure twice, cut once."**

1. **No code without approved requirements** — the SRS captures hidden assumptions before they become bugs
2. **No implementation without approved design** — 2-3 approaches are evaluated before committing to one
3. **No shortcuts on quality** — TDD, coverage, mutation testing, and compliance review are non-negotiable gates
4. **One feature, one cycle** — focused work prevents context exhaustion and ensures clean, atomic commits
5. **Persistent artifacts over ephemeral memory** — JSON state files and git history survive any context loss
6. **Systematic debugging over guess-and-fix** — root cause analysis before any fix attempt
7. **Immutable verification steps** — once set, the bar never lowers

<!-- ILLUSTRATION: Guiding Principles
![Principles](docs/images/principles.png)
> **Text-to-image prompt**: Seven principle cards arranged in a 3-3-1 grid layout, each card featuring a minimalist icon and a short title. Card 1: clipboard with checkmark "Requirements First". Card 2: blueprint icon "Design Before Code". Card 3: shield with star "Quality Non-Negotiable". Card 4: target with single arrow "One Feature, One Cycle". Card 5: bridge connecting two cliffs "Persistent State". Card 6: magnifying glass on root "Systematic Debugging". Card 7: locked padlock "Immutable Standards". Cards have subtle drop shadows on a light gray background. Each card uses a distinct accent color from a cohesive palette (navy, teal, emerald, amber, coral, violet, slate). Grid layout, 1200×900px.
-->

---

## Roadmap

- **Parallel Agent Dispatch** — identify independent features and dispatch worker subagents in parallel
- **Plugin Discovery System** — YAML frontmatter metadata, priority shadowing, marketplace distribution
- **Auto-Update Mechanism** — version checking with user notification (never auto-apply)
- **Multi-Platform Support** — Codex (OpenAI) and OpenCode adapter layers

---

## License

[MIT](LICENSE)

---

<p align="center">
  <i>Built for Claude Code — turning AI-assisted development into AI-engineered development.</i>
</p>
