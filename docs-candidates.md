# Initial candidate scan

Target: a shareable repo/tool that enforces repo-first discovery and candidate scoring for AI build agents.

| Score | Candidate | What it is | Fit | Risk |
|---:|---|---|---|---|
| 72 | `Sidhant0707/codeautopsy` | AI-powered GitHub repository analyzer | Useful for after clone/code inspection | Heavier than needed; not a pre-build discovery scorer |
| 65 | `orsinium-labs/awesome-generator` | Generates awesome lists via GitHub API | Good GitHub API precedent | LGPL and awesome-list oriented, not base selection |
| 58 | `abhijithvijayan/stargazed` | Builds awesome lists from starred repos | Good list-generation idea | Personal stars, not task-specific discovery |
| 45 | `kodepandai/awesome-gh-cli-extensions` | Awesome list of gh extensions | Reference list only | Not a scoring tool |

**Choice:** clean build with GitHub Search API, borrowing only the general idea of awesome-list/scoring output. No candidate was a direct, lightweight fit for an agent-first base-selection CLI.
