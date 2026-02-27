---
name: long-task:increment
description: Start incremental requirements development for an existing project.
disable-model-invocation: true
---

To start an increment cycle:

1. Create `increment-request.json` in project root with the reason and scope:
   ```json
   {
     "reason": "Brief description of why new requirements are needed",
     "scope": "Brief scope of changes"
   }
   ```
2. Validate the signal file:
   ```bash
   python scripts/validate_increment_request.py increment-request.json
   ```
3. The router will detect this file and invoke `long-task:long-task-increment`
