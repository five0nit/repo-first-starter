# Repo First Starter

A small, shareable CLI/template that enforces Mike's **repo-first base-selection rule** plus an **agent-code entropy gate**:

> Before building from scratch, search available repositories/tools, score candidates, choose the best base, then clone/start from that base when feasible.
>
> After selecting a base, avoid agent-written changes that increase future reasoning cost. Working code is not enough; every AI-generated change should reduce or preserve system entropy.

This project is deliberately lightweight: one Python CLI, no required third-party runtime dependencies, GitHub API search, trusted curated-list discovery, an optional maintainability/entropy gate, a transparent scoring rubric, and Markdown output that can be pasted into agent chats or project docs.

## Why

AI agents often jump straight into writing custom code. That wastes time when a maintained repo, template, or library already solves 80% of the task. This tool makes repository discovery a required first step.

## Candidate scoring

Default rubric totals 100 points:

| Component | Points | Signals |
|---|---:|---|
| Functional fit | 35 | Query terms in repo name, description, and language |
| Local/control fit | 15 | Local/self-host/offline/browser/CLI/library signals; cloud/SaaS penalty |
| Maintenance/activity | 15 | Recent update/push recency |
| Integration simplicity | 15 | Practical implementation language, non-archived status |
| License/shareability | 10 | Preferred SPDX licenses vs unknown/unclear license |
| Adoption | 10 | Stars, forks, watchers/subscribers |
| Developer history | 10 | Contributor count, fork activity, recent push, homepage/demo |
| Issue-health penalty | -5 | Penalizes unusually high open issue count |

GitHub does not provide a repo-level “review score” like an app store. The CLI uses practical proxies: stars, forks, watchers, issue health, maintainer activity, contributor count, license clarity, and demo/homepage evidence. Use `--deep-github` to fetch contributor/watchers/push metadata for stronger ranking; it is slower and uses more GitHub API calls.

## Install / run locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
repo-first "talking avatar lip sync javascript" --limit 5
```

No token is required for light use. Set `GITHUB_TOKEN` for higher API limits.

By default, the CLI also searches two high-signal curated lists before final ranking:

- [`sindresorhus/awesome`](https://github.com/sindresorhus/awesome) for broad language/framework/tooling indexes.
- [`trimstray/the-book-of-secret-knowledge`](https://github.com/trimstray/the-book-of-secret-knowledge) for CLI, ops, security, networking, and practical engineering tools.

Curated-list hits are treated as discovery leads, not automatic winners: they receive a modest ranking boost but are flagged with `curated list hit; inspect upstream health/license`. Use `--no-curated` to disable this path for fully direct GitHub/local-only searches.

Search local workspaces before GitHub when you may already have a suitable clone/template:

```bash
repo-first "telegram bot starter" --local ~/workspace --limit 8
repo-first "agent dashboard" --local ~/workspace --no-github
repo-first "telegram bot starter" --deep-github --limit 5  # slower, stronger ranking signals
repo-first "marketplace messaging" --entropy-gate      # append agent-code maintainability gate
```

## Agent-code entropy gate

Repo-first should not stop at "it works." After selecting a base and implementing changes, use the entropy gate to avoid agent-written code that only makes sense inside the original chat session.

The gate checks for hidden truth, duplicate business logic, pattern drift, unjustified abstractions, pointless indirection, context bombs, clever runtime magic, silent failure, undebuggable success, temporal coupling, retry-unsafe operations, test theatre, dependency inflation, config masquerading as logic, premature distribution, bolted-on security, orphaned code, and local correctness that breaks global coherence.

```bash
repo-first "payments workflow starter" --entropy-gate
```

See [`docs/agent-code-entropy-gate.md`](docs/agent-code-entropy-gate.md).

## Example

```bash
repo-first "ready player me lip sync avatar" --limit 5 --markdown
```

Output shape:

```markdown
## Repo/tool candidates
| Score | Source | Candidate | Stars | Forks | Devs | Issues | License | What it is | Fit | Risk |
|---:|---|---|---:|---:|---:|---:|---|---|---|---|
| 87 | github | owner/repo | 1234 | 120 | 25 | 8 | MIT | ... | ... | ... |

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
7. Apply the agent-code entropy gate: reject hidden truth, duplicated business logic, pattern drift, unjustified abstraction, weak observability, retry-unsafe operations, test theatre, dependency inflation, and orphaned code.
8. Report real install/test/demo receipts.

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

## Latest ranking report

See [`docs/ranking-report.md`](docs/ranking-report.md) for the current scoring signals, deep GitHub ranking mode, and the latest live verification run.

## Recommended improvements for adopters

- Tune scoring weights for your domain.
- Add ecosystem providers beyond GitHub: npm, PyPI, Hugging Face, Docker Hub.
- Add an MCP wrapper so agents can call repo-first as a structured tool.
- Add CI and publish to PyPI or as a `gh` extension.
