---
name: repo-first-base-selection
description: "Hard first-step rule for build/prototype tasks: search available repositories/tools, score candidates, choose the best base, then clone/start from it when feasible instead of building from scratch."
version: 1.1.0
tags: [repo-discovery, base-selection, github, prototyping, build-discipline, openclaw, hermes]
---

# Repo-First Base Selection

Use this skill for **any new build, prototype, automation, app, library, integration, demo, or reusable project** unless the user explicitly says to build from scratch or the task is a tiny edit inside an already-canonical repo.

## Hard rule

**Before creating a new implementation, search for available repositories/tools/templates, score them, choose the best base, and clone/start from that base when feasible.**

Do not jump straight into bespoke code because it feels faster. Repository discovery is part of the build, not an optional research detour.

## Required workflow

1. **Define the target in one sentence**
   - What are we trying to build?
   - What inputs/outputs matter?
   - What constraints matter: local/no-cloud, license, mobile, GPU, browser, CLI, etc.

2. **Search candidates**
   - Search GitHub and/or known package ecosystems.
   - Search scoped local workspaces when an existing clone/template may already exist.
   - Include repos the user names, but do not stop there if comparison is useful.
   - Prefer active, licensed, well-starred, directly relevant projects with healthy issue ratios and maintainer/contributor history.

3. **Return a scored candidate list before choosing**
   Include at least:
   - **Score /100**
   - **Repo/tool name + URL**
   - **Description**
   - **License/posture** if visible
   - **Stars / forks / issue health** if available
   - **Developer/contributor history** if deep metadata is available
   - **Why it fits**
   - **Key risk**

4. **Choose the base**
   - Pick the highest-fit candidate, not necessarily highest-starred.
   - State direct fork / selective fork / use as library / inspiration only / clean build.
   - If no candidate is a fit, say why and only then build cleanly.

5. **Clone/inspect the chosen base**
   - Verify real files, package/runtime, examples, license, and seams.
   - Do not rely on README alone.

6. **Start from the base when feasible**
   - Create one canonical local repo/worktree.
   - Record upstream/source and active branch.
   - Keep vendor/reference repos clearly labeled.

7. **Verify with receipts**
   - Run install/test/demo commands where practical.
   - Report real outputs and blockers.

## CLI helper

If this repo is installed, run:

```bash
repo-first "your project target" --limit 8
repo-first "your project target" --local ~/workspace --limit 8
repo-first "your project target" --deep-github --limit 5  # slower, stronger ranking metadata
```

Or without installing:

```bash
python -m repo_first_starter.cli "your project target" --limit 8
```

## Output template

```markdown
## Repo/tool candidates
| Score | Source | Candidate | Stars | Forks | Devs | Issues | What it is | Fit | Risk |
|---:|---|---|---:|---:|---:|---:|---|---|---|
| 92 | github | owner/repo | 1200 | 140 | 22 | 8 | ... | ... | ... |

**Choice:** owner/repo
**Decision:** clone as base / selective fork / library / inspiration / clean build
**Why:** ...
**Next command:** `git clone ...`
```

## Exceptions

Skip full discovery only when:
- The user explicitly names the exact repo/base and asks to proceed immediately.
- The task is a small edit in an existing canonical repo.
- Security/privacy constraints forbid external search.

Even then, note the exception briefly.

## Pitfalls

- Do not confuse "popular" with "best base".
- Do not clone repos with unclear license into shareable work without flagging risk.
- Do not build a custom implementation before checking whether an existing repo already does it.
- Do not leave multiple candidate clones without naming the canonical lane.
