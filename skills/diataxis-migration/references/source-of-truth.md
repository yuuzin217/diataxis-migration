# Source-of-truth policy

Document what can be established from the repository's current state. For current behavior, use this evidence in order of practical authority:

1. Current source code and generated interfaces.
2. Current database migrations and schema definitions.
3. Active configuration, defaults, and deployment manifests.
4. Relevant current tests and fixtures.
5. Merged implementation history when it explains a decision or transition.
6. Existing documentation, Issues, pull requests, and discussions as leads or historical context.

The order is not a substitute for checking whether a source is relevant. Tests can encode stale assumptions; documentation can describe external behavior the repository cannot prove. Record conflicts rather than choosing silently.

## Label time and certainty

Keep these states separate in prose and the gap register:

- **Current:** confirmed in the current implementation or other appropriate live source.
- **Planned:** proposed or tracked but not implemented; cite the open Issue or proposal and label it as future work.
- **Removed / reverted:** no longer current; identify the evidence and do not restore it from historical text.
- **Unknown:** not established by available repository evidence.
- **Externally unverified:** source inspection suggests behavior, but the relevant external service, deployment, device, or runtime was not exercised.

An open Issue, draft PR, or unmerged commit never establishes current behavior by itself. A merged PR can explain when or why a behavior changed; verify that it still exists in the current source before documenting it as current. A revert or superseding change takes precedence over an older feature description.

## Evidence record

For each material factual correction, cite a path and symbol, configuration key, migration, test name, commit, or hosted record. Capture the observed fact and any limit on that evidence. Use relative repository paths and line or symbol references when practical. If source access is incomplete, report that boundary rather than filling it with an assumption.

Keep a canonical page for important specifications. Other pages may include a brief task-relevant summary and a link to the canonical page. Avoid duplicate normative details that can drift.
