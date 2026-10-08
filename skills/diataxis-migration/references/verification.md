# Verification rules

Report only checks that were actually run. Use these status labels consistently:

- `PASS`: the named check ran and succeeded within its stated scope.
- `FAIL`: the named check ran and found a failure.
- `NOT RUN`: the check was not attempted.
- `NOT VERIFIED`: evidence or access was insufficient to decide.
- `NOT APPLICABLE`: the check does not apply to this change.

State the command or method and the scope. Static source inspection does not verify behavior in an external service, deployed environment, or physical device. A successful link checker does not establish that prose is accurate or that a rendered documentation site builds.

## Local scripts

From the repository root:

```sh
python scripts/inventory_docs.py . --format json
python scripts/check_doc_links.py .
```

The inventory lists Markdown paths only; it does not infer categories. The link checker validates supported Markdown inline and reference links, local files, and GitHub-style Markdown heading anchors. It does not fetch external URLs. It reports parser limitations (including raw HTML/JSX links) in its result; such syntax is not verified and must not be described as covered by a `PASS`.

For the Skill format, use the official [`skills-ref validate`](https://github.com/agentskills/agentskills/tree/main/skills-ref) validator when available. It checks frontmatter and naming rules, not behavior or compatibility with every client. If it is unavailable, say so and report any manual structural review separately.

If a check reports a problem, correct the cause and rerun it. Do not suppress, relabel, or skip a detected error to obtain a passing summary.

The checker also marks raw HTML/JSX links, explicit HTML anchors, multiline destinations, angle-bracket autolinks, and fragments on directory or non-Markdown targets as not verified when encountered.
