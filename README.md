# diataxis-migration

An Agent Skill for auditing, improving, and migrating existing repository documentation with the Diátaxis framework and current implementation as evidence.

## Overview

diataxis-migration guides an AI agent through a documentation inventory, reader-need classification, information architecture decisions, targeted migration, source reconciliation, and evidence-based verification. It can assess documentation without editing or carry out requested documentation changes.

The Skill is written against the client-neutral [Agent Skills format](https://agentskills.io/specification). It is intended for Codex, Claude Code, and other agents that support that format; it has not been tested on every client.

## Why Diátaxis?

Diátaxis distinguishes four reader needs: learning through a tutorial, completing a task with a how-to guide, looking up facts in reference, and understanding a system through explanation. It helps improve both content and information architecture. The framework is a guide, not a requirement to create four populated directories.

See the official [Diátaxis overview](https://diataxis.fr/) and [guidance for using the framework](https://diataxis.fr/how-to-use-diataxis/).

## Features

- Inventories Markdown files without inferring their meaning.
- Classifies content by its primary reader need, not its filename.
- Reconciles current behavior with source code, migrations, configuration, tests, and relevant merged changes.
- Records canonical sources, migration decisions, unresolved documentation gaps, and verification status.
- Checks supported Markdown links and heading anchors locally, with no external URL fetching.
- Keeps source-code changes out of documentation migrations.
- Provides a resumable, opt-in audit path for closed Issues, merged pull requests, reverts, and local Git history.

## Standard Mode

Standard Mode is the default. The Skill inspects repository instructions, existing docs and navigation, relevant current implementation, tests, and configuration. It makes only the requested, evidence-backed documentation changes and does not exhaustively audit Issues or pull requests.

It preserves useful structure, avoids empty categories and unnecessary rewrites, and records facts that could not be verified.

## Deep Audit Mode

Deep Audit Mode runs only when the user explicitly requests a history audit. In addition to Standard Mode, it reviews available closed Issues, merged pull requests, and Git history in bounded batches. It checks historical claims against current source, looks for reverts and superseding changes, and records coverage and a resume point.

GitHub access is optional. When remote history cannot be accessed, the Skill uses available local Git history and marks unavailable Issue or PR coverage as not verified. Audit-generated PRs remain in the inventory; a narrowly scoped PR can be omitted from ordinary re-review only after its actual merged diff and behavior are checked.

## Installation

The repository does not provide a universal installer because supported agents discover skills in client-specific locations. Clone or download this repository, then copy the Skill directory into the skills directory configured for your agent:

    git clone https://github.com/yuuzin217/diataxis-migration.git
    mkdir -p /path/to/your-agent/skills/
    cp -R diataxis-migration/skills/diataxis-migration /path/to/your-agent/skills/

Replace /path/to/your-agent/skills/ with the location documented by your client. Keep the diataxis-migration directory name and its contents together. The Python scripts are repository tools and do not need to be installed with the Skill.

## Usage

Ask your agent for a documentation task, for example:

> Migrate the existing documentation in this repository to Diátaxis.

> Perform a deep documentation audit using current source code, Git history, merged PRs, and closed Issues.

To ask for assessment only, say not to edit files. Deep Audit Mode is not inferred from a generic migration or audit request.

## Repository Structure

    skills/diataxis-migration/
      SKILL.md
      references/       Detailed workflow, classification, source, audit, safety, and verification guidance
      assets/           Inventory, migration, gap register, and final report templates
    scripts/
      inventory_docs.py
      check_doc_links.py
    tests/              Synthetic, network-free unit tests
    evals/cases.md      Skill behavior evaluation scenarios

## Verification

The project scripts use the Python standard library (Python 3.9 or newer):

    python scripts/inventory_docs.py . --format json
    python scripts/check_doc_links.py .
    python -m unittest discover -s tests -v

The inventory output is deterministic and can be consumed as JSON. The link checker validates supported local inline and reference-style Markdown links, files, and GitHub-style heading anchors. External URLs are not fetched. Raw HTML/JSX links, explicit HTML anchors, multiline Markdown destinations, angle-bracket autolinks, and fragments on non-Markdown or directory targets are outside its verification scope; when encountered, it reports NOT VERIFIED and exits non-zero.

For frontmatter validation, use the official skills-ref validate command when it is available. It validates Skill metadata and naming, not behavior or compatibility across clients. See the [skills-ref project](https://github.com/agentskills/agentskills/tree/main/skills-ref).

## Limitations

- The link checker intentionally supports a practical Markdown subset rather than all CommonMark, MDX, or renderer extensions. Its result identifies unsupported syntax it encounters.
- Heading anchor generation approximates GitHub's Markdown behavior; a documentation host may generate different anchors.
- The inventory discovers Markdown files only. Classification and content interpretation are the agent's responsibility.
- Deep audits depend on accessible Issues, PRs, and Git history. Incomplete history is reported as not verified.
- This project does not guarantee full compatibility with every Agent Skills client.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for scope and local checks. Contributions should preserve the client-neutral format, add synthetic tests for behavior changes, and avoid changing the license without a specific reason.

## License

Licensed under the [Apache License 2.0](LICENSE).
