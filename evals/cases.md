# Skill evaluation scenarios

These are evaluation specifications, not executed runs. They describe expected agent behavior; they do not claim that the Skill has been evaluated against each scenario.

## Case A — Mixed-purpose page

- **Input conditions:** One page mixes a learner walkthrough, a task procedure, factual CLI options, and architectural rationale.
- **Expected behavior:** Identify the distinct reader needs. Recommend or perform focused splits when each part can stand alone, preserve useful summaries, and add links and navigation updates.
- **Failure conditions:** Classify only by filename, place every section into one quadrant, lose facts during a split, or create empty category pages.
- **Evaluation method:** Inspect the decision register, resulting pages, inbound links, and navigation against the original content.

## Case B — Existing structure is already useful

- **Input conditions:** Documents have clear purposes, accurate content, working links, and discoverable navigation.
- **Expected behavior:** Keep sound pages and report why broader restructuring is unnecessary.
- **Failure conditions:** Move, split, or rewrite documents only to make the directory tree look like four quadrants.
- **Evaluation method:** Review the diff and ensure every change addresses an evidence-backed problem.

## Case C — No tutorial exists

- **Input conditions:** The repository has accurate reference and task guides but no guided learning material.
- **Expected behavior:** Leave the category absent unless the user requests a tutorial and a meaningful learning outcome can be supported.
- **Failure conditions:** Invent a tutorial to complete a four-category layout or label a command list as a tutorial.
- **Evaluation method:** Inspect the new files and the stated rationale for any tutorial content.

## Case D — Reference conflicts with current code

- **Input conditions:** A reference page documents an API field or configuration default that differs from current implementation.
- **Expected behavior:** Check source, configuration, migrations, and relevant tests; update the canonical reference to supported current behavior and record uncertainty.
- **Failure conditions:** Repeat the stale text, trust a test or doc without checking relevant implementation, or invent the correct value.
- **Evaluation method:** Trace each corrected statement to current source evidence and inspect the gap register.

## Case E — Open Issue describes an unimplemented feature

- **Input conditions:** An open Issue proposes a feature absent from current source.
- **Expected behavior:** Identify it as planned or proposed, never as current behavior. In Standard Mode, inspect it only if relevant; Deep Audit coverage is explicit.
- **Failure conditions:** Add the proposed feature to current reference or omit its future status when mentioning it.
- **Evaluation method:** Compare the text with current code and the Issue's state.

## Case F — Historical behavior was reverted

- **Input conditions:** A merged change added behavior that a later revert or superseding change removed.
- **Expected behavior:** Confirm the current implementation, label the old behavior removed or reverted, and avoid restoring it to current docs.
- **Failure conditions:** Treat the first merged PR as authoritative or miss the revert.
- **Evaluation method:** Inspect the relevant diff chain and compare documented claims with current source.

## Case G — GitHub history is unavailable

- **Input conditions:** Remote GitHub access is unavailable, but the working repository and local history are readable.
- **Expected behavior:** Continue Standard Mode; use local history where useful. In Deep Audit Mode, report unavailable Issue/PR coverage as NOT VERIFIED and save a resume point.
- **Failure conditions:** Stop an otherwise possible Standard Mode, claim complete remote history, or fabricate Issue/PR evidence.
- **Evaluation method:** Inspect the final report's scope, evidence, and status labels.

## Case H — Audit-generated PR exists

- **Input conditions:** A prior documentation audit created a PR that is now merged.
- **Expected behavior:** Keep it in the PR inventory. Exclude it from ordinary re-audit only after checking the actual diff and confirming it contains no independent behavior changes; still revalidate its current docs.
- **Failure conditions:** Ignore it by title, remove it from the inventory, skip checking its diff, or repeatedly re-audit it without a documented exclusion.
- **Evaluation method:** Review the inventory, diff evidence, exclusion rationale, and current-doc checks.

## Case I — Broken Markdown link

- **Input conditions:** A page links to a missing local file or heading.
- **Expected behavior:** Identify the source line and target, repair it when in scope, and report a failing check until rerun successfully. State unsupported syntax separately.
- **Failure conditions:** Report an unrun checker as passing, silently skip the link, or fetch external URLs by default.
- **Evaluation method:** Run the checker against the fixture, inspect exit status and diagnostic, then rerun after correction.
