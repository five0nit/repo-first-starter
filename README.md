# Repo First Starter

A small, shareable CLI/template that enforces Mike's **repo-first base-selection rule**:

> Before building from scratch, search available repositories/tools, score candidates, choose the best base, then clone/start from that base when feasible.

This project is deliberately lightweight: one Python CLI, no required third-party runtime dependencies, GitHub API search, a transparent scoring rubric, and Markdown output that can be pasted into agent chats or project docs.

## Why

AI agents often jump straight into writing custom code. That wastes time when a maintained repo, template, or library already solves 80% of the task. This tool makes repository discovery a required first step.

## Candidate scoring

Default rubric totals 100 points:

| Component | Points |
|---|---:|
| Functional fit | 35 |
| Local/control fit | 15 |
| Maintenance/activity | 15 |
| Integration simplicity | 15 |
| License/shareability | 10 |
| Quality/demo proof | 10 |

The CLI estimates these from GitHub metadata and query matching. Humans/agents should adjust scores after code inspection.

## Install / run locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
repo-first "talking avatar lip sync javascript" --limit 5
```

No token is required for light use. Set `GITHUB_TOKEN` for higher API limits.

## Example

```bash
repo-first "ready player me lip sync avatar" --limit 5 --markdown
```

Output shape:

```markdown
## Repo/tool candidates
| Score | Candidate | Stars | License | What it is | Fit | Risk |
|---:|---|---:|---|---|---|---|
| 87 | owner/repo | 1234 | MIT | ... | ... | ... |

**Choice:** owner/repo
**Decision:** inspect/clone as base if license and seams check out.
```

## Agent workflow

1. Define target in one sentence.
2. Run this search or equivalent manual search.
3. Present scored candidate table.
4. Choose base: direct fork / selective fork / use as library / inspiration / clean build.
5. Clone/inspect the chosen repo before implementation claims.
6. Start from the base when feasible.
7. Report real install/test/demo receipts.

## License

MIT


## Agent compatibility

This repo is designed to be agent-portable:

| Agent/runtime | Status | Files |
|---|---|---|
| Hermes Agent | Compatible | `skills/repo-first-base-selection/SKILL.md`, `scripts/install-skill.sh` |
| OpenClaw | Compatible with SKILL.md-style skill folders | `skills/repo-first-base-selection/SKILL.md`, `scripts/install-skill.sh` |
| Codex / OpenAI-style coding agents | Compatible instructions | `AGENTS.md` |
| Claude Code | Compatible instructions | `CLAUDE.md` |
| Cursor | Compatible instructions | `.cursorrules` |

Install the skill locally:

```bash
scripts/install-skill.sh              # Hermes + OpenClaw common locations
scripts/install-skill.sh --hermes-only
scripts/install-skill.sh --openclaw-only
```

See [`docs/compatibility.md`](docs/compatibility.md).

## Recommended improvements for adopters

- Tune scoring weights for your domain.
- Add ecosystem providers beyond GitHub: npm, PyPI, Hugging Face, Docker Hub.
- Add an MCP wrapper so agents can call repo-first as a structured tool.
- Add CI and publish to PyPI or as a `gh` extension.
