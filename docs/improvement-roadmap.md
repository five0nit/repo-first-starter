# Improvement Roadmap

Useful next improvements for people who download this repo:

## Agent integrations

- Publish skill package to any public Hermes/OpenClaw skill registry when available.
- Add an MCP server wrapper so agents can call `repo_first.search` as a tool.
- Add GitHub CLI extension packaging: `gh extension install ...`.

## Search sources

- Add npm, PyPI, crates.io, Docker Hub, Hugging Face, and GitLab search providers.
- [x] Add local workspace search before web search to reuse existing clones (`--local PATH`, `--no-github`).
- [ ] Cache GitHub API responses for repeat queries.

## Scoring quality

- Inspect candidate READMEs and LICENSE files for stronger scoring.
- Penalize unmaintained repos more accurately with commit activity.
- Add domain-specific scoring profiles, e.g. `--profile webapp`, `--profile ml`, `--profile cli`.
- Add cached deep ranking metadata so contributor/watchers/history signals do not require repeated GitHub API calls.
- Add explicit security/licensing red flags.

## Output modes

- Add `--clone-best` with a dry-run default and explicit confirmation flag.
- Add `--save report.md`.
- Add `--agent-prompt` to generate a next-step implementation prompt.

## Testing/release

- Add GitHub Actions for pytest.
- Add PyPI packaging.
- Add example transcripts showing before/after agent behavior.
