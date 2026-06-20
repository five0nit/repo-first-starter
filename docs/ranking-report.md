# Ranking Report

This report summarizes the current `repo-first-starter` ranking behavior and the latest live verification runs.

## Current version

The CLI now supports:

- GitHub repository search and scoring.
- Scoped local workspace search with `--local PATH`.
- Local-only mode with `--no-github`.
- Richer GitHub ranking metadata with `--deep-github`.
- Markdown and JSON output.

## Ranking signals

GitHub does not expose a repo-level review score like an app store, so the CLI uses practical public signals:

| Category | Signals |
|---|---|
| Functional fit | Query terms in repo name, description, and language |
| Local/control fit | Local/self-host/offline/browser/CLI/library signals; cloud/SaaS penalty |
| Maintenance/activity | Recent update, and push recency in deep mode |
| Integration simplicity | Practical language and non-archived status |
| License/shareability | Preferred SPDX licenses vs unknown/unclear license |
| Adoption | Stars, forks, watchers/subscribers |
| Developer history | Contributor count, fork activity, recent push, homepage/demo |
| Issue health | Penalty for unusually high open issue count |

Use deep mode when the base choice matters enough to spend extra time/API calls:

```bash
repo-first "your project target" --deep-github --limit 5
```

## Latest live test: 3D talking avatar

Query:

```text
3d talking avatar lip sync
```

### Resource results

| Mode | Time | Output size | Winner |
|---|---:|---:|---|
| Normal GitHub ranking | 0.69s | 2,523 chars | `met4citizen/TalkingHead` |
| Deep GitHub ranking | 9.74s | 2,523 chars | `met4citizen/TalkingHead` |
| Combined local + deep GitHub | 1.46s | 2,523 chars | `met4citizen/TalkingHead` |

The combined run can be faster after a prior deep request because GitHub/API responses may be warmed or cached by the network path. Treat timings as indicative, not guaranteed.

### Deep-ranking top candidates

| Score | Candidate | Stars | Forks | Devs | Issues | License | Notes |
|---:|---|---:|---:|---:|---:|---|---|
| 95 | `met4citizen/TalkingHead` | 1353 | 314 | 5 | 7 | MIT | Clear winner: real-time lip-sync using full-body 3D avatars |
| 89 | `AgriciDaniel/claude-avatar` | 21 | 5 | 1 | 0 | MIT | Claude Code voice/avatar integration |
| 84 | `ElmoGaber/talking-avatar-with-ai` | 0 | 0 | 1 | 0 | MIT | Direct topic fit but no adoption yet |
| 83 | `kenken64/remotion-3d-AI-avatar` | 0 | 3 | 1 | 0 | MIT | Direct fit, low adoption |
| 73 | `Scthe/ai-iris-avatar` | 189 | 51 | 1 | 3 | GPL-3.0 | Good activity, but GPL risk |

Recommended base:

```bash
git clone https://github.com/met4citizen/TalkingHead
```

## Interpretation

The richer scoring did not change the winner for this query, but it made the choice more defensible. The winner is now supported by:

- direct topic match,
- high adoption,
- strong fork count,
- low issue count for its size,
- MIT license,
- visible contributor history.

The recommended human/agent workflow remains:

1. Run repo-first ranking.
2. Inspect the top 1–3 repositories.
3. Verify install/runtime/examples/license.
4. Choose direct fork, selective fork, library use, inspiration only, or clean build.
