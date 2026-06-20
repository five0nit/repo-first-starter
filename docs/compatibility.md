# Compatibility

## Hermes Agent

Compatible: **yes**.

Hermes reads skills from `$HERMES_HOME/skills/` and supports `SKILL.md` packages with YAML frontmatter. This repo includes:

```text
skills/repo-first-base-selection/SKILL.md
```

Install locally:

```bash
git clone https://github.com/five0nit/repo-first-starter
cd repo-first-starter
scripts/install-skill.sh --hermes-only
```

Then load it in Hermes with:

```text
/skill repo-first-base-selection
```

or launch with:

```bash
hermes -s repo-first-base-selection
```

## OpenClaw

Compatible: **yes, file-format compatible**.

OpenClaw installations commonly use `~/.openclaw/skills/<skill-name>/SKILL.md`. This repo ships the same portable skill package and an installer:

```bash
git clone https://github.com/five0nit/repo-first-starter
cd repo-first-starter
scripts/install-skill.sh --openclaw-only
```

The skill is plain Markdown + YAML frontmatter, so it is portable across OpenClaw-style skill loaders and other agents that ingest `SKILL.md`.

## Other agents

This repo also includes:

- `AGENTS.md` for Codex/OpenAI-style coding agents and many agent runners.
- `CLAUDE.md` for Claude Code-style agents.
- `.cursorrules` for Cursor-style IDE agents.
- `README.md` with human-readable workflow.

## CLI compatibility

Runtime: Python 3.9+ with stdlib only.

Install:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
repo-first "repo discovery scoring cli" --limit 8
```

The CLI uses GitHub's public Search API. It works without a token for light use. Set `GITHUB_TOKEN` for higher rate limits.
