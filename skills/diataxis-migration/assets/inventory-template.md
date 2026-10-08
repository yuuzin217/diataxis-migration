# Documentation inventory and decision register

Use one row per document. Keep paths repository-relative. Add evidence references that a reviewer can verify. `Current category` may be `mixed`, `unclear`, or `unclassified`; do not force a label.

| Document path | Current category | Primary purpose / reader need | Target category | Decision | Evidence | Reason | Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `path/to/page.md` | `mixed` | `[What the reader is trying to do or understand]` | `[Tutorial / How-to / Reference / Explanation / unchanged]` | `[KEEP / MOVE / SPLIT / MERGE / REWRITE / CROSS-LINK / ARCHIVE / DEPRECATE / FOLLOW-UP]` | `[Source paths, symbols, tests, or history]` | `[Why this decision best serves the reader]` | `[Specific edit or no change]` |

## Review notes

- Scope and inventory method: `[directories, exclusions, date or commit]`
- Existing canonical pages: `[path and owned subject]`
- Navigation entry points: `[README, sidebar, index, or generator config]`
- Unavailable evidence: `[what could not be inspected]`
