---
name: file-output-location
description: Put standalone generated files in the right place.
---

Standalone files — HTML, scripts, docs, exports, reports, visualizations, anything not already part of a project the user is editing — go under `~/Documents/ai_gen_files/`, not the current working directory and not wherever feels convenient.

Create the directory (and subfolders) if it doesn't exist yet — don't ask permission, don't ask where to save.

Skip this rule in two cases only:

- You're editing inside an existing project the user already has open — the file belongs with that project, not in `ai_gen_files/`.
- The user names an explicit path — that instruction wins.

Some skills carve out their own subfolder under `ai_gen_files/` for a specific kind of stateful output (e.g. the `teach` skill uses `ai_gen_files/teach/<topic>/`). If the skill you're running names a subfolder, use it; otherwise write directly under `ai_gen_files/`.
