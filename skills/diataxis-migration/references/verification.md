# Verification rules

Report only checks that were actually run. Use these status labels consistently:

- `PASS`: the named check ran and succeeded within its stated scope.
- `FAIL`: the named check ran and found a failure.
- `NOT RUN`: the check was not attempted.
- `NOT VERIFIED`: evidence or access was insufficient to decide.
- `NOT APPLICABLE`: the check does not apply to this change.

State the command or method and the scope. Static source inspection does not verify behavior in an external service, deployed environment, or physical device. A successful link checker does not establish that prose is accurate or that a rendered documentation site builds.

## Packaged helper scripts

The inventory and link-check helpers are bundled in this Skill's `scripts/` directory and are included when the Skill directory is copied during installation. Set `SKILL_DIR` to the installed `diataxis-migration` directory containing `SKILL.md`, and `REPOSITORY_ROOT` to the repository being checked:

```sh
SKILL_DIR="/path/to/your-agent/skills/diataxis-migration"
REPOSITORY_ROOT="/path/to/repository"
python "$SKILL_DIR/scripts/inventory_docs.py" "$REPOSITORY_ROOT" --format json
python "$SKILL_DIR/scripts/check_doc_links.py" "$REPOSITORY_ROOT"
```

The inventory lists Markdown paths only; it does not infer categories. It skips symlinked directories, includes file symlinks only when their targets stay within the repository root, and exits with an error rather than returning a successful inventory if an external Markdown file symlink is found. The link checker validates supported Markdown inline and reference links, local files, and GitHub-style Markdown heading anchors. It does not fetch external URLs. It reports parser limitations (including raw HTML/JSX links) in its result; such syntax is not verified and must not be described as covered by a `PASS`.

If either helper is missing or cannot be run from the installed Skill, report that check as `NOT RUN` and the related inventory or verification coverage as `NOT VERIFIED`. Do not claim a `PASS`; describe any other method and its limits separately.

For the Skill format, use the official [`skills-ref validate`](https://github.com/agentskills/agentskills/tree/main/skills-ref) validator when available. It checks frontmatter and naming rules, not behavior or compatibility with every client. If it is unavailable, say so and report any manual structural review separately.

If a check reports a problem, correct the cause and rerun it. Do not suppress, relabel, or skip a detected error to obtain a passing summary.

The checker also marks raw HTML/JSX links, explicit HTML anchors, multiline Markdown links, angle-bracket autolinks, and fragments on directory or non-Markdown targets as not verified when encountered. An explicit full or collapsed reference link without a matching definition is a failure; a standalone shortcut label without a definition is treated as ordinary text.
