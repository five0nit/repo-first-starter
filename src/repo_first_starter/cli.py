from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

PREFERRED_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0"}

CURATED_LISTS = (
    {
        "name": "awesome",
        "source": "curated:awesome",
        "repo_url": "https://github.com/sindresorhus/awesome",
        "raw_url": "https://raw.githubusercontent.com/sindresorhus/awesome/main/readme.md",
        "description": "sindresorhus/awesome curated topic indexes",
    },
    {
        "name": "secret-knowledge",
        "source": "curated:secret-knowledge",
        "repo_url": "https://github.com/trimstray/the-book-of-secret-knowledge",
        "raw_url": "https://raw.githubusercontent.com/trimstray/the-book-of-secret-knowledge/master/README.md",
        "description": "trimstray/the-book-of-secret-knowledge ops/CLI/security tool list",
    },
)

ENTROPY_GATE_CHECKS = (
    ("Hidden truth", "Can a maintainer find the authoritative rule without archaeology?"),
    ("Duplicate business logic", "Does each business rule have one clear owner?"),
    ("Pattern drift", "Does the change follow existing architecture unless the reason to diverge is explicit?"),
    ("Abstraction without tension", "Is each abstraction justified by real duplication or volatility pressure?"),
    ("Indirection chains", "Does every layer enforce a boundary, isolate volatility, protect an invariant, simplify testing, or model a real domain concept?"),
    ("Context bombs", "Are files/functions/classes small and coherent enough for practical human/agent reasoning?"),
    ("Clever runtime behavior", "Is behavior inspectable statically, avoiding unjustified eval/dynamic imports/monkey patches/reflection/codegen?"),
    ("Silent failure", "Does every important failure leave evidence?"),
    ("Undebuggable success", "Can critical successes explain inputs, applied rule/version, actor/process, and downstream action?"),
    ("Temporal coupling", "If order matters, is it encoded explicitly instead of hidden in tribal/manual setup?"),
    ("Non-idempotent operations", "Are retries/reruns guarded with idempotency keys, dedupe, dry-run, or confirmation where needed?"),
    ("Test theatre", "Do tests protect real invariants, including edge and failure paths?"),
    ("Dependency inflation", "Is each dependency worth its maintenance/security/upgrade risk?"),
    ("Config as logic", "Is metadata/config governed like code with schema, tests, ownership, and docs?"),
    ("Premature distribution", "Are services/queues/events/network boundaries justified by real pressure?"),
    ("Security as later patch", "Are auth, validation, secrets, permissions, and safe defaults part of the code shape?"),
    ("Orphaned code", "Are dead paths removed or given a clear removal plan?"),
    ("Global coherence", "Would another agent understand and safely extend this without the original chat?"),
)

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


def fetch_text(url: str, max_bytes: int = 500_000) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "repo-first-starter"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read(max_bytes).decode("utf-8", errors="ignore")


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


MARKDOWN_LINK_RE = re.compile(r"\[([^\]]{2,160})\]\((https?://[^)\s]+)\)(?:\s*[-–—:]\s*([^\n]+))?")
HTML_LINK_RE = re.compile(r"<a\s+[^>]*href=[\"'](https?://[^\"']+)[\"'][^>]*>(.{2,160}?)</a>", re.I)


def github_name_from_url(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return None


def curated_list_search(query: str, limit: int) -> list[dict]:
    """Search trusted curated Markdown lists before deciding a build base.

    These are not substitutes for repo inspection. They act as high-signal
    discovery guides, especially for broad CLI/devops/security/tooling tasks
    where normal GitHub search can return noisy project matches.
    """
    terms = [t.lower() for t in query.replace("-", " ").replace("/", " ").split() if len(t) > 2]
    generic_terms = {
        "cli", "tool", "tools", "repo", "repos", "github", "awesome", "starter",
        "template", "library", "libraries", "framework", "frameworks", "software",
        "solution", "solutions", "app", "apps", "project", "projects",
    }
    distinctive_terms = [t for t in terms if t not in generic_terms]
    if not terms:
        return []
    results: list[dict] = []
    seen: set[tuple[str, str]] = set()
    per_list_limit = max(limit * 4, 20)
    for curated in CURATED_LISTS:
        try:
            text = fetch_text(curated["raw_url"])
        except Exception:
            continue
        section = ""
        found_for_list = 0
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                section = stripped.lstrip("# ").strip()
            matches = list(MARKDOWN_LINK_RE.finditer(line))
            matches.extend(HTML_LINK_RE.finditer(line))
            for match in matches:
                if match.re is MARKDOWN_LINK_RE:
                    title, url, trailing = match.group(1), match.group(2), match.group(3) or ""
                else:
                    url, title, trailing = match.group(1), re.sub(r"<[^>]+>", "", match.group(2)), ""
                haystack = " ".join([title, url, trailing, section, curated["name"]]).lower()
                matched = sum(1 for term in terms if term in haystack)
                distinctive_matched = sum(1 for term in distinctive_terms if term in haystack)
                if matched == 0 or (distinctive_terms and distinctive_matched == 0):
                    continue
                key = (curated["source"], url.lower().rstrip("/"))
                if key in seen:
                    continue
                seen.add(key)
                gh_name = github_name_from_url(url)
                full_name = gh_name or title.strip() or url
                description = trailing.strip(" -–—:") or f"Curated in {curated['description']}"
                if section:
                    description = f"{description} [section: {section}]"
                results.append({
                    "full_name": full_name,
                    "html_url": url,
                    "description": description,
                    "stargazers_count": 0,
                    "forks_count": 0,
                    "subscribers_count": 0,
                    "contributors_count": 0,
                    "open_issues_count": 0,
                    "license": {"spdx_id": "UNKNOWN"},
                    "language": "",
                    "updated_at": "",
                    "archived": False,
                    "homepage": curated["repo_url"],
                    "source": curated["source"],
                    "curated_matches": matched,
                    "curated_list": curated["name"],
                })
                found_for_list += 1
                if found_for_list >= per_list_limit:
                    break
            if found_for_list >= per_list_limit:
                break
    return results


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
    curated = str(item.get("source", "")).startswith("curated:")
    matched = max(matched, int(item.get("curated_matches") or 0))
    functional = min(35, 10 + matched * 6)
    if curated and matched:
        functional = min(35, functional + 6)

    desc = (item.get("description") or "").lower()
    local = 12 if item.get("source") == "local" else 8
    if curated:
        local += 2
    if any(w in desc for w in ["local", "self-host", "offline", "browser", "cli", "library"]):
        local += 5
    if any(w in desc for w in ["api key", "cloud", "saas"]):
        local -= 4
    local = max(0, min(15, local))

    maintenance = age_score(item.get("updated_at", ""))
    if curated and not item.get("updated_at"):
        maintenance = 8
    integration = 8
    if item.get("language") in {"Python", "JavaScript", "TypeScript", "Shell", "Go"}:
        integration += 4
    if item.get("archived"):
        integration -= 8
    integration = max(0, min(15, integration))

    lic = (item.get("license") or {}).get("spdx_id") or "UNKNOWN"
    license_score = 10 if lic in PREFERRED_LICENSES else (5 if lic == "LOCAL-CHECK" else (4 if lic != "UNKNOWN" else (2 if curated else 0)))

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
    if curated: adoption += 3
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
    if curated: developer_history += 2
    developer_history = min(10, developer_history)

    issue_penalty = 0
    if open_issues > max(50, stars // 2):
        issue_penalty = 5
    elif open_issues > max(20, stars // 4):
        issue_penalty = 2

    personal_config_penalty = 0
    repo_basename = item.get("full_name", "").rsplit("/", 1)[-1].lower()
    if repo_basename in {".config", "dotfiles", "configs", "config"} and not {"dotfile", "dotfiles", "config", "configs"}.intersection(query_terms):
        personal_config_penalty = 25

    score = functional + local + maintenance + integration + license_score + adoption + developer_history - issue_penalty - personal_config_penalty
    score = max(0, min(100, score))
    risk_parts = []
    if lic == "UNKNOWN": risk_parts.append("license unclear")
    if curated: risk_parts.append("curated list hit; inspect upstream health/license")
    if lic == "LOCAL-CHECK": risk_parts.append("inspect local license")
    if item.get("archived"): risk_parts.append("archived")
    if personal_config_penalty: risk_parts.append("personal config/dotfiles repo")
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
            if urllib.parse.urlparse(best.url).netloc.lower() in {"github.com", "www.github.com"}:
                next_command = f"git clone {best.url}"
                decision = "inspect/clone as base if license, runtime, and seams check out."
            else:
                next_command = f"curl -L {best.url}"
                decision = "inspect upstream URL as a reference; only clone if a real VCS/source URL is found and license/seams check out."
        lines += ["", f"**Choice:** [{best.full_name}]({best.url})", f"**Decision:** {decision}", f"**Next command:** `{next_command}`"]
    return "\n".join(lines)


def entropy_gate_markdown() -> str:
    lines = [
        "",
        "## Agent code entropy gate",
        "",
        "**Prime directive:** avoid creating systems that only make sense inside the chat session that produced them.",
        "The codebase must explain itself after the agent, prompt, and conversation history are gone.",
        "",
        "Before accepting the implementation, verify:",
        "",
    ]
    for name, question in ENTROPY_GATE_CHECKS:
        lines.append(f"- [ ] **{name}:** {question}")
    lines += [
        "",
        "**Final rule:** every AI-generated change should reduce or preserve system entropy; working code is not enough.",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Search and score repository candidates before building from scratch.")
    ap.add_argument("query", help="GitHub search query / project target")
    ap.add_argument("--limit", type=int, default=8, help="number of candidates to fetch")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    ap.add_argument("--local", action="append", default=[], metavar="PATH", help="search a local workspace path before GitHub; can be repeated")
    ap.add_argument("--no-github", action="store_true", help="only search local paths supplied with --local")
    ap.add_argument("--deep-github", action="store_true", help="fetch extra GitHub repo/contributor metadata for stronger ranking; slower and uses more API calls")
    ap.add_argument("--no-curated", action="store_true", help="skip trusted curated-list discovery (sindresorhus/awesome and trimstray/the-book-of-secret-knowledge)")
    ap.add_argument("--entropy-gate", action="store_true", help="append the agent-code entropy/maintainability acceptance gate to Markdown output")
    ap.add_argument("--markdown", action="store_true", help="emit Markdown (default)")
    args = ap.parse_args(argv)

    terms = [t.lower() for t in args.query.replace('-', ' ').split() if len(t) > 2]
    items = local_workspace_search(args.query, args.local, max(args.limit * 25, 100)) if args.local else []
    if not args.no_curated:
        items.extend(curated_list_search(args.query, args.limit))
    if not args.no_github:
        try:
            items.extend(enrich_github_items(github_search(args.query, args.limit), args.deep_github))
        except Exception as e:
            if not items:
                print(f"repo-first: GitHub search failed: {e}", file=sys.stderr)
                return 2
            print(f"repo-first: GitHub search failed; showing local results only: {e}", file=sys.stderr)
    scored = sorted((score_item(i, terms) for i in items), key=lambda c: c.score, reverse=True)
    deduped: list[Candidate] = []
    seen_urls: set[str] = set()
    for candidate in scored:
        key = candidate.url.lower().rstrip("/")
        if key in seen_urls:
            continue
        seen_urls.add(key)
        deduped.append(candidate)
    candidates = deduped[:args.limit]
    if args.json:
        print(json.dumps([c.__dict__ for c in candidates], indent=2))
    else:
        out = markdown(candidates, args.query)
        if args.entropy_gate:
            out += entropy_gate_markdown()
        print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
