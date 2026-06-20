from __future__ import annotations

import argparse
import json
import os
import sys
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
    open_issues: int
    license: str
    language: str
    updated_at: str
    archived: bool
    score: int
    fit: str
    risk: str


def github_search(query: str, limit: int) -> list[dict]:
    q = urllib.parse.quote(query)
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={limit}"
    headers = {"User-Agent": "repo-first-starter"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8")).get("items", [])


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
    local = 8
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
    license_score = 10 if lic in PREFERRED_LICENSES else (4 if lic != "UNKNOWN" else 0)

    stars = int(item.get("stargazers_count") or 0)
    quality = 2
    if stars >= 1000: quality += 6
    elif stars >= 100: quality += 4
    elif stars >= 10: quality += 2
    if item.get("homepage"): quality += 2
    quality = min(10, quality)

    score = functional + local + maintenance + integration + license_score + quality
    risk_parts = []
    if lic == "UNKNOWN": risk_parts.append("license unclear")
    if item.get("archived"): risk_parts.append("archived")
    if int(item.get("open_issues_count") or 0) > max(50, stars // 2): risk_parts.append("many open issues")
    if not risk_parts: risk_parts.append("requires code inspection")

    fit = "directly relevant" if functional >= 28 else ("partial fit" if functional >= 20 else "weak/needs inspection")
    return Candidate(
        full_name=item.get("full_name", ""),
        url=item.get("html_url", ""),
        description=item.get("description") or "",
        stars=stars,
        forks=int(item.get("forks_count") or 0),
        open_issues=int(item.get("open_issues_count") or 0),
        license=lic,
        language=item.get("language") or "",
        updated_at=item.get("updated_at", ""),
        archived=bool(item.get("archived")),
        score=int(score),
        fit=fit,
        risk=", ".join(risk_parts),
    )


def markdown(candidates: list[Candidate], query: str) -> str:
    lines = [f"## Repo/tool candidates for: `{query}`", "", "| Score | Candidate | Stars | License | What it is | Fit | Risk |", "|---:|---|---:|---|---|---|---|"]
    for c in candidates:
        desc = c.description.replace("|", "-")[:110]
        lines.append(f"| {c.score} | [{c.full_name}]({c.url}) | {c.stars} | {c.license} | {desc} | {c.fit} | {c.risk} |")
    if candidates:
        best = candidates[0]
        lines += ["", f"**Choice:** [{best.full_name}]({best.url})", "**Decision:** inspect/clone as base if license, runtime, and seams check out.", f"**Next command:** `git clone {best.url}`"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Search and score repository candidates before building from scratch.")
    ap.add_argument("query", help="GitHub search query / project target")
    ap.add_argument("--limit", type=int, default=8, help="number of candidates to fetch")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    ap.add_argument("--markdown", action="store_true", help="emit Markdown (default)")
    args = ap.parse_args(argv)

    terms = [t.lower() for t in args.query.replace('-', ' ').split() if len(t) > 2]
    try:
        items = github_search(args.query, args.limit)
    except Exception as e:
        print(f"repo-first: GitHub search failed: {e}", file=sys.stderr)
        return 2
    candidates = sorted((score_item(i, terms) for i in items), key=lambda c: c.score, reverse=True)
    if args.json:
        print(json.dumps([c.__dict__ for c in candidates], indent=2))
    else:
        print(markdown(candidates, args.query))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
