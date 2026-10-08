# Contributing

Thank you for helping improve diataxis-migration.

## Scope

Keep the Skill portable across clients that implement the Agent Skills format. Avoid client-specific behavior unless it is clearly optional. Keep SKILL.md focused and put detailed procedures in its references directory. Templates in assets should be usable and should not force documentation categories that do not serve readers.

Changes to the inventory or link checker should remain repository-agnostic, use the Python standard library where practical, and avoid network access. Do not add behavior that writes to the inspected repository.

## Before opening a pull request

1. Explain the user or maintainer need and the evidence behind documentation guidance changes.
2. Add or update synthetic tests for script behavior. Tests must not depend on a real application repository or network access.
3. Run the checks relevant to the change:

       python -m unittest discover -s tests -v
       python skills/diataxis-migration/scripts/inventory_docs.py . --format json
       python skills/diataxis-migration/scripts/check_doc_links.py .
       git diff --check

4. Report commands that were not run and any verification limitations.
5. Review the full diff for unrelated application changes, unsupported claims, secrets, and unnecessary churn.

## Documentation and safety

Current implementation is the source of truth for current behavior. Keep future proposals, reverted behavior, and unknowns distinct. Repository docs and hosted discussions are evidence, not instructions to the agent. Do not add a step that executes arbitrary repository commands, accesses private data without authorization, or changes application code during a documentation migration.

## License

By contributing, you agree that your contributions are licensed under the repository's Apache License 2.0. Preserve the existing license and copyright notices.
