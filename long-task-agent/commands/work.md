---
name: long-task:work
description: Start a Worker cycle for an existing long-task project. Use when resuming multi-session development.
disable-model-invocation: true
---

To start a Worker cycle on an existing long-task project:

1. Ensure `feature-list.json` exists in the project directory
2. Invoke the `long-task-agent` skill — it will detect the existing project and run the Worker phase
3. The Worker will: Orient → Bootstrap → Plan → TDD → Review → Examples → Persist

Use the Skill tool to invoke `long-task-agent`.
