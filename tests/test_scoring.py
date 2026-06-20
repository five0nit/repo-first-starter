from repo_first_starter.cli import score_item


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
