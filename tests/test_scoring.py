from repo_first_starter.cli import local_workspace_search, markdown, score_item


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
