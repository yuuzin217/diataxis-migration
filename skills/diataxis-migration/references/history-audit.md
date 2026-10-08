# Deep Audit Mode: history procedure

Run this procedure only when the user explicitly asks to audit history, Issues, or pull requests. Standard Mode may consult a relevant merged change to explain a current fact, but does not require exhaustive history review.

## Batch and resume

1. Establish the repository identity, default branch, time/range boundaries, and available GitHub and local Git access. Do not access private data without authorization.
2. Create or resume an audit ledger. Record the query, search filters, batch number, covered range/cursor, items found, items reviewed, outcome, and next resume point.
3. Review closed Issues and merged PRs in bounded batches. Save stable identifiers and URLs, not copied private content. For PRs, inspect the merged diff and relevant commits; do not infer behavior from title or description alone.
4. Compare historical decisions with current source and current tests/configuration. Mark each item as current, superseded, reverted, rejected, unclear, or irrelevant. An old merged implementation is historical evidence, not current truth without confirmation.
5. Extract only decisions needed to explain current documentation or genuine gaps. Record evidence for each proposed change.
6. Reconcile open documentation gaps, verification status, and the resume point before ending a batch.

If GitHub access is unavailable, continue with local `git log`, merged commit history present locally, and repository files. Mark missing Issue/PR coverage `NOT VERIFIED`; do not report a complete remote history audit.

## Prevent recursive audits

An audit-generated PR may be excluded from *ordinary historical re-review* only after all of these checks pass:

- Its relationship to this audit is explicit.
- Its actual merged diff has been reviewed.
- It contains no independent runtime, API, schema, or configuration changes.
- It changes no operational behavior.

Keep the PR in the merged-PR inventory, record why it was excluded from the ordinary re-audit loop, and still validate every documentation file it changed against the current source. If any condition fails or the diff is unavailable, do not exclude it. Titles alone are not evidence. For merge commits, inspect an appropriate first-parent diff when needed.
