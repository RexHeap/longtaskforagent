---
name: long-task:init
description: Initialize a new long-task project. Use when starting a multi-session project from requirement/design docs.
disable-model-invocation: true
---

To initialize a new long-task project, use the `long-task-agent` skill:

1. Prepare your requirement doc and design doc
2. (Optional) Prepare a design template at `docs/templates/design-template.md` or specify its path when prompted
3. Invoke the skill: it will run Brainstorming → Initializer phases
4. The skill will scaffold all persistent artifacts automatically

Use the Skill tool to invoke `long-task-agent` with your project documents.
