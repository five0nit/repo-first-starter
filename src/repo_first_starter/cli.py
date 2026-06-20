from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

PREFERRED_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0"}

@dataclass
class Candidate:
    full_name: str
    url: str
    description: str
    stars: int
    forks: int
    watchers: int
    contributors: int
    open_issues: int
    license: str
    language: str
    updated_at: str
    archived: bool
    score: int
    fit: str
    risk: str
    source: str = "github"


def github_headers() -> dict[str, str]:
    headers = {"User-Agent": "repo-first-starter", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_get_json(url: str) -> object:
    req = urllib.request.Request(url, headers=github_headers())
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def github_search(query: str, limit: int) -> list[dict]:
    q = urllib.parse.quote(query)
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={limit}"
    data = github_get_json(url)
    return data.get("items", []) if isinstance(data, dict) else []


def enrich_github_items(items: list[dict], deep: bool = False) -> list[dict]:
    """Optionally add slower quality signals not returned by GitHub search."""
    if not deep:
        return items
    enriched = []
    for item in items:
        merged = dict(item)
        try:
            details = github_get_json(item.get("url", ""))
            if isinstance(details, dict):
                for key in ("subscribers_count", "network_count", "pushed_at", "created_at", "topics"):
                    if key in details:
                        merged[key] = details[key]
        except Exception as e:
            merged["deep_error"] = str(e)
        try:
            contributors_url = (item.get("contributors_url") or "").split("{", 1)[0]
            if contributors_url:
                contributors = github_get_json(f"{contributors_url}?per_page=100")
                if isinstance(contributors, list):
                    merged["contributors_count"] = len(contributors)
                    merged["top_contributor_commits"] = sum(int(c.get("contributions") or 0) for c in contributors[:10])
        except Exception as e:
            merged["contributors_error"] = str(e)
        enriched.append(merged)
    return enriched


SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}
PROJECT_MARKERS = ("pyproject.toml", "package.json", "Cargo.toml", "go.mod", "README.md")


def local_workspace_search(query: str, roots: list[str], limit: int) -> list[dict]:
    """Return GitHub-shaped items for matching local project directories.

    The limit is a scan cap, not the final output size; callers score and sort
    local results with remote results before truncating the displayed list.
    """
    terms = [t.lower() for t in query.replace("-", " ").split() if len(t) > 2]
    results: list[dict] = []
    seen: set[Path] = set()
    for root_s in roots:
        root = Path(root_s).expanduser().resolve()
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
            path = Path(dirpath)
            if path in seen:
                continue
            has_project_marker = any(marker in filenames for marker in PROJECT_MARKERS) or ".git" in dirnames
            if not has_project_marker:
                continue
            text_bits = [path.name]
            readme = path / "README.md"
            description = "Local workspace project"
            if readme.exists():
                try:
                    first_lines = readme.read_text(errors="ignore").splitlines()[:8]
                    text_bits.extend(first_lines)
                    description = next((line.strip("# ") for line in first_lines if line.strip()), description)
                except OSError:
                    pass
            haystack = " ".join(text_bits).lower()
            if terms and not any(term in haystack for term in terms):
                continue
            seen.add(path)
            try:
                updated = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
            except OSError:
                updated = ""
            language = ""
            if (path / "pyproject.toml").exists():
                language = "Python"
            elif (path / "package.json").exists():
                language = "JavaScript"
            elif (path / "Cargo.toml").exists():
                language = "Rust"
            elif (path / "go.mod").exists():
                language = "Go"
            license_name = "UNKNOWN"
            for candidate in ("LICENSE", "LICENSE.md", "COPYING"):
                if (path / candidate).exists():
                    license_name = "LOCAL-CHECK"
                    break
            results.append({
                "full_name": f"local/{path.name}",
                "html_url": path.as_uri(),
                "description": description,
                "stargazers_count": 0,
                "forks_count": 0,
                "subscribers_count": 0,
                "contributors_count": 0,
                "open_issues_count": 0,
                "license": {"spdx_id": license_name},
                "language": language,
                "updated_at": updated,
                "archived": False,
                "homepage": None,
                "source": "local",
            })
            if len(results) >= limit:
                return results
    return results


def age_score(updated_at: str) -> int:
    try:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        days = (datetime.now(timezone.utc) - dt).days
    except Exception:
        return 3
    if days <= 90: return 15
    if days <= 365: return 12
    if days <= 730: return 8
    if days <= 1460: return 4
    return 1


def score_item(item: dict, query_terms: list[str]) -> Candidate:
    text = " ".join([item.get("full_name", ""), item.get("description") or "", item.get("language") or ""]).lower()
    matched = sum(1 for t in query_terms if t in text)
    functional = min(35, 10 + matched * 6)

    desc = (item.get("description") or "").lower()
    local = 12 if item.get("source") == "local" else 8
    if any(w in desc for w in ["local", "self-host", "offline", "browser", "cli", "library"]):
        local += 5
    if any(w in desc for w in ["api key", "cloud", "saas"]):
        local -= 4
    local = max(0, min(15, local))

    maintenance = age_score(item.get("updated_at", ""))
    integration = 8
    if item.get("language") in {"Python", "JavaScript", "TypeScript", "Shell", "Go"}:
        integration += 4
    if item.get("archived"):
        integration -= 8
    integration = max(0, min(15, integration))

    lic = (item.get("license") or {}).get("spdx_id") or "UNKNOWN"
    license_score = 10 if lic in PREFERRED_LICENSES else (5 if lic == "LOCAL-CHECK" else (4 if lic != "UNKNOWN" else 0))

    stars = int(item.get("stargazers_count") or 0)
    forks = int(item.get("forks_count") or item.get("network_count") or 0)
    watchers = int(item.get("subscribers_count") or item.get("watchers_count") or 0)
    contributors = int(item.get("contributors_count") or 0)
    open_issues = int(item.get("open_issues_count") or 0)

    adoption = 0
    if stars >= 1000: adoption += 6
    elif stars >= 100: adoption += 5
    elif stars >= 10: adoption += 3
    elif stars > 0: adoption += 1
    if forks >= 100: adoption += 3
    elif forks >= 20: adoption += 2
    elif forks >= 3: adoption += 1
    if watchers >= 50: adoption += 1
    adoption = min(10, adoption)

    developer_history = 0
    if contributors >= 20: developer_history += 4
    elif contributors >= 5: developer_history += 3
    elif contributors >= 2: developer_history += 2
    elif contributors == 1: developer_history += 1
    if forks >= 20: developer_history += 2
    if item.get("pushed_at") and age_score(item.get("pushed_at", "")) >= 12:
        developer_history += 2
    if item.get("homepage"): developer_history += 2
    developer_history = min(10, developer_history)

    issue_penalty = 0
    if open_issues > max(50, stars // 2):
        issue_penalty = 5
    elif open_issues > max(20, stars // 4):
        issue_penalty = 2

    score = functional + local + maintenance + integration + license_score + adoption + developer_history - issue_penalty
    score = max(0, min(100, score))
    risk_parts = []
    if lic == "UNKNOWN": risk_parts.append("license unclear")
    if lic == "LOCAL-CHECK": risk_parts.append("inspect local license")
    if item.get("archived"): risk_parts.append("archived")
    if issue_penalty >= 5: risk_parts.append("many open issues")
    elif issue_penalty: risk_parts.append("elevated open issues")
    if item.get("deep_error"): risk_parts.append("deep repo metadata unavailable")
    if item.get("contributors_error"): risk_parts.append("contributor metadata unavailable")
    if not risk_parts: risk_parts.append("requires code inspection")

    fit = "directly relevant" if functional >= 28 else ("partial fit" if functional >= 20 else "weak/needs inspection")
    return Candidate(
        full_name=item.get("full_name", ""),
        url=item.get("html_url", ""),
        description=item.get("description") or "",
        stars=stars,
        forks=forks,
        watchers=watchers,
        contributors=contributors,
        open_issues=open_issues,
        license=lic,
        language=item.get("language") or "",
        updated_at=item.get("updated_at", ""),
        archived=bool(item.get("archived")),
        score=int(score),
        fit=fit,
        risk=", ".join(risk_parts),
        source=item.get("source", "github"),
    )


def markdown(candidates: list[Candidate], query: str) -> str:
    lines = [f"## Repo/tool candidates for: `{query}`", "", "| Score | Source | Candidate | Stars | Forks | Devs | Issues | License | What it is | Fit | Risk |", "|---:|---|---|---:|---:|---:|---:|---|---|---|---|"]
    for c in candidates:
        desc = c.description.replace("|", "-")[:110]
        lines.append(f"| {c.score} | {c.source} | [{c.full_name}]({c.url}) | {c.stars} | {c.forks} | {c.contributors} | {c.open_issues} | {c.license} | {desc} | {c.fit} | {c.risk} |")
    if candidates:
        best = candidates[0]
        if best.source == "local":
            next_command = f"cd {best.url.removeprefix('file://')}"
            decision = "inspect local workspace as base if license, runtime, and seams check out."
        else:
            next_command = f"git clone {best.url}"
            decision = "inspect/clone as base if license, runtime, and seams check out."
        lines += ["", f"**Choice:** [{best.full_name}]({best.url})", f"**Decision:** {decision}", f"**Next command:** `{next_command}`"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Search and score repository candidates before building from scratch.")
    ap.add_argument("query", help="GitHub search query / project target")
    ap.add_argument("--limit", type=int, default=8, help="number of candidates to fetch")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    ap.add_argument("--local", action="append", default=[], metavar="PATH", help="search a local workspace path before GitHub; can be repeated")
    ap.add_argument("--no-github", action="store_true", help="only search local paths supplied with --local")
    ap.add_argument("--deep-github", action="store_true", help="fetch extra GitHub repo/contributor metadata for stronger ranking; slower and uses more API calls")
    ap.add_argument("--markdown", action="store_true", help="emit Markdown (default)")
    args = ap.parse_args(argv)

    terms = [t.lower() for t in args.query.replace('-', ' ').split() if len(t) > 2]
    items = local_workspace_search(args.query, args.local, max(args.limit * 25, 100)) if args.local else []
    if not args.no_github:
        try:
            items.extend(enrich_github_items(github_search(args.query, args.limit), args.deep_github))
        except Exception as e:
            if not items:
                print(f"repo-first: GitHub search failed: {e}", file=sys.stderr)
                return 2
            print(f"repo-first: GitHub search failed; showing local results only: {e}", file=sys.stderr)
    candidates = sorted((score_item(i, terms) for i in items), key=lambda c: c.score, reverse=True)[:args.limit]
    if args.json:
        print(json.dumps([c.__dict__ for c in candidates], indent=2))
    else:
        print(markdown(candidates, args.query))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
