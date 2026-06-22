from repo_first_starter.cli import curated_list_search, entropy_gate_markdown, local_workspace_search, markdown, score_item


def test_score_prefers_matching_licensed_recent_repo():
    item = {
        "full_name": "owner/talking-avatar",
        "html_url": "https://github.com/owner/talking-avatar",
        "description": "Local browser talking avatar lip sync library",
        "stargazers_count": 1200,
        "forks_count": 20,
        "open_issues_count": 5,
        "license": {"spdx_id": "MIT"},
        "language": "JavaScript",
        "updated_at": "2026-01-01T00:00:00Z",
        "archived": False,
        "homepage": "https://example.com",
    }
    c = score_item(item, ["talking", "avatar", "lip", "sync"])
    assert c.score >= 80
    assert c.license == "MIT"
    assert c.fit == "directly relevant"


def test_unknown_license_is_flagged():
    item = {
        "full_name": "owner/mystery",
        "html_url": "https://github.com/owner/mystery",
        "description": "Repo analyzer",
        "stargazers_count": 1,
        "forks_count": 0,
        "open_issues_count": 0,
        "license": None,
        "language": "Python",
        "updated_at": "2024-01-01T00:00:00Z",
        "archived": False,
        "homepage": None,
    }
    c = score_item(item, ["repo", "analyzer"])
    assert c.license == "UNKNOWN"
    assert "license unclear" in c.risk


def test_score_uses_forks_contributors_and_issue_health():
    healthy = {
        "full_name": "owner/healthy-bot",
        "html_url": "https://github.com/owner/healthy-bot",
        "description": "Telegram bot starter",
        "stargazers_count": 500,
        "forks_count": 80,
        "subscribers_count": 60,
        "contributors_count": 12,
        "open_issues_count": 8,
        "license": {"spdx_id": "MIT"},
        "language": "TypeScript",
        "updated_at": "2026-01-01T00:00:00Z",
        "pushed_at": "2026-01-01T00:00:00Z",
        "archived": False,
        "homepage": "https://example.com",
    }
    noisy = {**healthy, "forks_count": 0, "subscribers_count": 0, "contributors_count": 0, "open_issues_count": 400, "homepage": None}

    healthy_score = score_item(healthy, ["telegram", "bot", "starter"])
    noisy_score = score_item(noisy, ["telegram", "bot", "starter"])

    assert healthy_score.forks == 80
    assert healthy_score.watchers == 60
    assert healthy_score.contributors == 12
    assert healthy_score.score > noisy_score.score
    assert "many open issues" in noisy_score.risk


def test_local_workspace_search_finds_matching_project(tmp_path):
    project = tmp_path / "starter-demo"
    project.mkdir()
    (project / "pyproject.toml").write_text("[project]\nname = 'starter-demo'\n")
    (project / "README.md").write_text("# Starter Demo\n\nLocal starter repo for agents.\n")
    (project / "LICENSE").write_text("MIT\n")

    items = local_workspace_search("starter agents", [str(tmp_path)], limit=5)

    assert len(items) == 1
    assert items[0]["source"] == "local"
    assert items[0]["full_name"] == "local/starter-demo"
    assert items[0]["language"] == "Python"


def test_markdown_uses_cd_for_local_choice():
    local_candidate = score_item(
        {
            "full_name": "local/starter-demo",
            "html_url": "file:///tmp/starter-demo",
            "description": "Local starter repo",
            "stargazers_count": 0,
            "forks_count": 0,
            "open_issues_count": 0,
            "license": {"spdx_id": "LOCAL-CHECK"},
            "language": "Python",
            "updated_at": "2026-01-01T00:00:00Z",
            "archived": False,
            "source": "local",
        },
        ["starter"],
    )

    out = markdown([local_candidate], "starter")

    assert "| Source |" in out
    assert "**Next command:** `cd /tmp/starter-demo`" in out


def test_curated_list_search_extracts_matching_links(monkeypatch):
    sample = """
# CLI Tools
- [ripgrep](https://github.com/BurntSushi/ripgrep) - fast recursive grep CLI tool
- [not relevant](https://example.com/nope) - drawing app
"""

    monkeypatch.setattr("repo_first_starter.cli.fetch_text", lambda url: sample)

    items = curated_list_search("grep cli", limit=3)

    assert any(item["full_name"] == "BurntSushi/ripgrep" for item in items)
    assert all(item["source"].startswith("curated:") for item in items)


def test_curated_hits_get_useful_but_cautious_score():
    item = {
        "full_name": "BurntSushi/ripgrep",
        "html_url": "https://github.com/BurntSushi/ripgrep",
        "description": "fast recursive grep CLI tool [section: CLI Tools]",
        "stargazers_count": 0,
        "forks_count": 0,
        "open_issues_count": 0,
        "license": {"spdx_id": "UNKNOWN"},
        "language": "",
        "updated_at": "",
        "archived": False,
        "homepage": "https://github.com/sindresorhus/awesome",
        "source": "curated:awesome",
        "curated_matches": 2,
    }

    c = score_item(item, ["grep", "cli"])

    assert c.score >= 50
    assert "curated list hit" in c.risk
    assert "license unclear" in c.risk


def test_personal_config_repos_are_penalized_for_non_dotfile_queries():
    config = {
        "full_name": "owner/.config",
        "html_url": "https://github.com/owner/.config",
        "description": "GNU Bash shell features CLI tools generated config",
        "stargazers_count": 500,
        "forks_count": 90,
        "open_issues_count": 0,
        "license": {"spdx_id": "MIT"},
        "language": "Shell",
        "updated_at": "2026-01-01T00:00:00Z",
        "archived": False,
    }

    c = score_item(config, ["gnu", "bash", "shell", "features", "cli", "tools"])

    assert c.score < 80
    assert "personal config/dotfiles repo" in c.risk


def test_markdown_does_not_git_clone_non_github_urls():
    candidate = score_item(
        {
            "full_name": "GNU Bash",
            "html_url": "https://www.gnu.org/software/bash/",
            "description": "GNU Bash shell reference",
            "stargazers_count": 0,
            "forks_count": 0,
            "open_issues_count": 0,
            "license": {"spdx_id": "UNKNOWN"},
            "language": "",
            "updated_at": "",
            "archived": False,
            "homepage": "https://github.com/trimstray/the-book-of-secret-knowledge",
            "source": "curated:secret-knowledge",
            "curated_matches": 3,
        },
        ["gnu", "bash", "shell"],
    )

    out = markdown([candidate], "GNU Bash shell")

    assert "git clone https://www.gnu.org/software/bash/" not in out
    assert "curl -L https://www.gnu.org/software/bash/" in out


def test_entropy_gate_markdown_includes_prime_directive_and_core_gates():
    out = entropy_gate_markdown()

    assert "Agent code entropy gate" in out
    assert "avoid creating systems that only make sense inside the chat session" in out
    assert "Hidden truth" in out
    assert "Duplicate business logic" in out
    assert "Global coherence" in out
    assert "working code is not enough" in out
