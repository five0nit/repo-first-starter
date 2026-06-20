# Agent Instructions: Repo-First Starter

This repository exists to enforce a build discipline for AI agents:

1. Search available repositories/tools/templates first.
2. Score candidates with a visible rubric.
3. Choose the best base.
4. Clone/inspect before implementing.
5. Build from an existing base when feasible.

When editing this repo:

- Keep the CLI dependency-light and usable with Python stdlib only at runtime.
- Keep `skills/repo-first-base-selection/SKILL.md` compatible with Hermes and OpenClaw skill loaders.
- Run `pytest -q` and `bash -n scripts/install-skill.sh` before committing.
- Do not add API keys, tokens, or private machine paths to docs.
- Keep examples copy-pasteable for agents and humans.
