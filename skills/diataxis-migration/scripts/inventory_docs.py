#!/usr/bin/env python3
"""List Markdown documents under a repository without changing them."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Set


EXCLUDED_DIRECTORIES: Set[str] = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".pytest_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "bower_components",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "site-packages",
    "target",
    "vendor",
    "venv",
}
MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown", ".mdx"}


def inventory(root: Path) -> List[str]:
    """Return sorted repository-relative Markdown paths.

    Symlinked directories are not traversed. Markdown file symlinks are
    included only when their resolved paths stay within the repository root;
    an external file symlink aborts the inventory. The function reads
    directory entries only and never opens or modifies document contents.
    """
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(str(root))

    documents: List[str] = []

    def on_walk_error(error: OSError) -> None:
        raise error

    for current, directories, filenames in os.walk(
        str(root), topdown=True, followlinks=False, onerror=on_walk_error
    ):
        current_path = Path(current)
        directories[:] = sorted(
            name
            for name in directories
            if name not in EXCLUDED_DIRECTORIES
            and not (current_path / name).is_symlink()
        )
        for filename in filenames:
            path = current_path / filename
            if path.suffix.lower() in MARKDOWN_SUFFIXES:
                if path.is_symlink():
                    try:
                        resolved = path.resolve(strict=False)
                    except (OSError, RuntimeError) as error:
                        raise RuntimeError(
                            "Markdown symlink '{}' could not be safely resolved; inventory was not completed.".format(
                                path.relative_to(root).as_posix()
                            )
                        ) from error
                    try:
                        resolved.relative_to(root)
                    except ValueError as error:
                        raise RuntimeError(
                            "Markdown symlink '{}' resolves outside the repository root; inventory was not completed.".format(
                                path.relative_to(root).as_posix()
                            )
                        ) from error
                documents.append(path.relative_to(root).as_posix())

    return sorted(documents)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "List Markdown files under a repository. This is a file inventory; "
            "it does not classify document meaning."
        )
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="repository or directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    try:
        documents = inventory(root)
    except (OSError, RuntimeError) as error:
        print(
            "inventory_docs.py: cannot inventory '{}': {}".format(root, error),
            file=sys.stderr,
        )
        return 2

    if args.format == "json":
        json.dump(
            {"count": len(documents), "documents": documents},
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        for document in documents:
            print(document)
        print("{} Markdown document(s)".format(len(documents)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
