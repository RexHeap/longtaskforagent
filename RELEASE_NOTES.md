# Release Notes — test-quality-enhancement

## [Unreleased]

### Added
- Initial project scaffold
- Anti-pattern #14: Low-Value Assertions — 7 BAD/GOOD examples, 20% ratio rule, wrong implementation criterion (testing-anti-patterns.md)
- Test Scenario Rules Reference — category coverage, negative ratio >= 40%, assertion quality, wrong implementation challenge, UI-specific rules (references/test-scenario-rules.md)
- UI Error Detection Reference — 3-layer detection: automated JS script, EXPECT/REJECT format, console error hard gate (references/ui-error-detection.md)
- Test Plan Review Reference — hard gate between TDD Red and Green, structured scoring rubric (A-D sections), max 2 rounds (references/test-plan-review.md)
- Test Plan Reviewer Prompt Template — adversarial 5-step process with wrong implementation challenge (agents/prompts/test-plan-reviewer-prompt.md)
- EXPECT/REJECT format validation in validate_features.py (warnings for missing clauses)
- 3 new test cases for EXPECT/REJECT validation (32 total tests passing)

### Changed
- Plan template expanded from 4 to 7 tasks: added Test Plan Review, Coverage Gate, Mutation Gate (references/plan-writing.md)
- Code reviewer now uses adversarial framing (find 3+ issues before verdict) and dual review for high-priority/UI features (agents/code-reviewer.md)
- Spec reviewer prompt uses structured YES/NO scoring rubric instead of free-text verdict (agents/prompts/spec-reviewer-prompt.md)
- Code quality reviewer prompt includes test quality rubric T1-T6 (agents/prompts/code-quality-reviewer-prompt.md)
- Architecture document updated with Test Plan Review phase, TDD diagram, Chrome DevTools pattern, 4 new anti-patterns (references/architecture.md)
- SKILL.md updated with Test Plan Review step (4a), Critical Rules, Red Flags, Resources
- CLAUDE.md updated with new file structure entries, EXPECT/REJECT example, See Also references
- validate_features.py returns (errors, warnings) tuple instead of just errors list

### Fixed
- (none)

---

_Format: [Keep a Changelog](https://keepachangelog.com/) — Updated after every git commit._
