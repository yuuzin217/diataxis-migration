#!/usr/bin/env python3
"""Check supported Markdown links and heading anchors without network access.

The checker understands inline links and images, full/collapsed/shortcut
reference links, URL-encoded paths, and GitHub-style Markdown heading anchors.
It deliberately does not fetch external URLs.
"""

import argparse
import html
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple
from urllib.parse import unquote, urlsplit


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
FENCE_START = re.compile(r"^ {0,3}(\x60{3,}|~{3,})(.*)$")
FENCE_END = re.compile(r"^ {0,3}(\x60{3,}|~{3,})\s*$")
ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)\s*#*\s*$")
SETEXT_HEADING = re.compile(r"^ {0,3}(=+|-+)\s*$")
REFERENCE_DEFINITION = re.compile(
    r"^ {0,3}\[([^\]]+)\]:[ \t]*(<[^>]*>|(?:\\.|[^ \t]+))"
)
INLINE_HTML_LINK = re.compile(r"(?i)\b(?:href|src)\s*=|<\s*(?:a|img|source|iframe)\b")
HTML_ANCHOR = re.compile(r"(?i)\b(?:id|name)\s*=")
AUTOLINK = re.compile(r"<([^<>\s]+)>")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass
class Link:
    destination: str
    line: int
    syntax: str


@dataclass
class Finding:
    code: str
    path: str
    line: int
    message: str


def _is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def _mask_fenced_code(text: str) -> str:
    """Replace fenced code with spaces, preserving newlines and line numbers."""
    output: List[str] = []
    active_char: Optional[str] = None
    active_length = 0
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        if active_char is None:
            match = FENCE_START.match(body)
            if match:
                marker = match.group(1)
                active_char = marker[0]
                active_length = len(marker)
                output.append(" " * len(body) + ending)
                continue
            output.append(line)
            continue

        match = FENCE_END.match(body)
        if (
            match
            and match.group(1)[0] == active_char
            and len(match.group(1)) >= active_length
        ):
            active_char = None
            active_length = 0
        output.append(" " * len(body) + ending)
    return "".join(output)


def _mask_html_comments(text: str) -> str:
    """Mask HTML comments while preserving line numbers and character offsets."""
    def replace(match: re.Match) -> str:
        return "".join("\n" if char == "\n" else "\r" if char == "\r" else " " for char in match.group(0))

    return HTML_COMMENT.sub(replace, text)


def _mask_inline_code(text: str) -> str:
    """Mask matching Markdown code spans, including spans across lines."""
    chars = list(text)
    index = 0
    while index < len(text):
        if text[index] != "\x60" or _is_escaped(text, index):
            index += 1
            continue
        end = index + 1
        while end < len(text) and text[end] == "\x60":
            end += 1
        marker_length = end - index
        search = end
        closing_start: Optional[int] = None
        while search < len(text):
            candidate = text.find("\x60", search)
            if candidate < 0:
                break
            candidate_end = candidate + 1
            while candidate_end < len(text) and text[candidate_end] == "\x60":
                candidate_end += 1
            if candidate_end - candidate == marker_length:
                closing_start = candidate
                break
            search = candidate_end
        if closing_start is None:
            index = end
            continue
        closing_end = closing_start + marker_length
        for position in range(index, closing_end):
            if chars[position] not in "\r\n":
                chars[position] = " "
        index = closing_end
    return "".join(chars)


def _reference_key(label: str) -> str:
    return " ".join(label.split()).casefold()


def _unescape_destination(destination: str) -> str:
    destination = html.unescape(destination.strip())
    return re.sub(
        r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\]\\^_\x60{|}~])",
        r"\1",
        destination,
    )


def _definition_map(masked_text: str) -> Tuple[Dict[str, str], str]:
    references: Dict[str, str] = {}
    chars = list(masked_text)
    line_start = 0
    for line in masked_text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        match = REFERENCE_DEFINITION.match(body)
        if match:
            raw_destination = match.group(2)
            if raw_destination.startswith("<") and raw_destination.endswith(">"):
                raw_destination = raw_destination[1:-1]
            label = _reference_key(match.group(1))
            if not label.startswith("^"):
                references.setdefault(label, _unescape_destination(raw_destination))
            for position in range(line_start, line_start + len(body)):
                chars[position] = " "
        line_start += len(line)
    return references, "".join(chars)


def _matching_bracket(text: str, start: int) -> Optional[int]:
    depth = 1
    index = start + 1
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            index += 2
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _matching_paren(text: str, start: int) -> Optional[int]:
    depth = 1
    index = start + 1
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            index += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _destination_from_parens(content: str) -> str:
    content = content.strip()
    if not content:
        return ""
    if content.startswith("<"):
        close = content.find(">")
        if close >= 0:
            return _unescape_destination(content[1:close])
    depth = 0
    index = 0
    while index < len(content):
        char = content[index]
        if char == "\\" and index + 1 < len(content):
            index += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif char.isspace() and depth == 0:
            content = content[:index]
            break
        index += 1
    return _unescape_destination(content)


def _has_multiline_inline_link(text: str) -> bool:
    """Return whether an inline link spans lines and cannot be parsed here."""
    index = 0
    while index < len(text):
        start = text.find("[", index)
        if start < 0:
            return False
        if _is_escaped(text, start):
            index = start + 1
            continue
        close_bracket = _matching_bracket(text, start)
        if close_bracket is None:
            index = start + 1
            continue
        open_paren = close_bracket + 1
        if open_paren < len(text) and text[open_paren] == "(":
            close_paren = _matching_paren(text, open_paren)
            if close_paren is None:
                if "\n" in text[open_paren:] or "\r" in text[open_paren:]:
                    return True
            elif "\n" in text[start:close_paren + 1] or "\r" in text[start:close_paren + 1]:
                return True
        index = close_bracket + 1
    return False


def extract_links(text: str) -> Tuple[List[Link], List[str]]:
    """Extract supported inline/reference links and parser limitations."""
    masked = _mask_inline_code(_mask_html_comments(_mask_fenced_code(text)))
    references, searchable = _definition_map(masked)
    links: List[Link] = []
    limitations: List[str] = []
    if _has_multiline_inline_link(searchable):
        limitations.append("Multiline Markdown links are not inspected.")
    if re.search(r"(?m)^ {0,3}\[[^\]\r\n]+\]:[ \t]*\r?\n[ \t]+", searchable):
        limitations.append("Multiline Markdown reference definitions are not inspected.")

    for line_number, line in enumerate(searchable.splitlines(), start=1):
        if INLINE_HTML_LINK.search(line):
            limitations.append("Raw HTML/JSX href/src links are not inspected.")
        if HTML_ANCHOR.search(line):
            limitations.append("Explicit HTML id/name anchors are not inspected.")
        for match in AUTOLINK.finditer(line):
            value = match.group(1)
            if not re.match(r"(?i)^[a-z][a-z0-9+.-]*:", value):
                limitations.append("Angle-bracket autolinks are not inspected.")

        index = 0
        while index < len(line):
            if line[index] != "[" or _is_escaped(line, index):
                index += 1
                continue
            close = _matching_bracket(line, index)
            if close is None:
                index += 1
                continue
            label = line[index + 1:close]
            if label.lstrip().startswith("^"):
                index = close + 1
                continue
            after = close + 1
            if after < len(line) and line[after] == "(":
                paren_close = _matching_paren(line, after)
                if paren_close is not None:
                    destination = _destination_from_parens(line[after + 1:paren_close])
                    links.append(Link(destination, line_number, "inline"))
                    index = paren_close + 1
                    continue
            if after < len(line) and line[after] == "[":
                ref_close = _matching_bracket(line, after)
                if ref_close is not None:
                    reference = line[after + 1:ref_close] or label
                    destination = references.get(_reference_key(reference))
                    if destination is not None:
                        links.append(Link(destination, line_number, "reference"))
                    else:
                        links.append(Link(reference, line_number, "undefined-reference"))
                    index = ref_close + 1
                    continue
            destination = references.get(_reference_key(label))
            if destination is not None:
                links.append(Link(destination, line_number, "reference"))
            index = close + 1

    return links, sorted(set(limitations))


def _heading_text(markdown: str) -> str:
    markdown = html.unescape(markdown)
    markdown = re.sub(r"\s*\{#[^}]+\}\s*$", "", markdown)
    markdown = re.sub(r"!?(\[([^\]]+)\])\([^)]*\)", r"\2", markdown)
    markdown = re.sub(r"!?(\[([^\]]+)\])(?:\[[^\]]*\])?", r"\2", markdown)
    markdown = re.sub(r"<[^>]*>", "", markdown)
    markdown = markdown.replace("\x60", "")
    markdown = re.sub(r"[*_~]", "", markdown)
    return markdown.strip()


def heading_anchors(text: str) -> Tuple[Set[str], Dict[str, List[int]], List[str]]:
    """Return generated GitHub-style anchors, duplicate lines, and limitations."""
    masked = _mask_html_comments(_mask_fenced_code(text))
    lines = masked.splitlines()
    anchors: Set[str] = set()
    seen: Counter = Counter()
    duplicates: Dict[str, List[int]] = defaultdict(list)
    limitations: List[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        custom_id = re.search(r"\s*\{#([^}]+)\}\s*$", line)
        heading = ATX_HEADING.match(line)
        heading_source: Optional[str] = None
        line_number = index + 1
        if heading:
            heading_source = heading.group(2)
        elif (
            line.strip()
            and index + 1 < len(lines)
            and SETEXT_HEADING.match(lines[index + 1])
        ):
            heading_source = line.strip()
        if heading_source is not None:
            if custom_id:
                anchor = custom_id.group(1)
                if anchor in anchors:
                    duplicates[anchor].append(line_number)
                anchors.add(anchor)
            else:
                normalized = _heading_text(heading_source)
                parts: List[str] = []
                pending_space = False
                for char in normalized.lower():
                    if char.isspace():
                        pending_space = True
                        continue
                    category = unicodedata.category(char)
                    if category.startswith("P") and char not in "-_":
                        continue
                    if category.startswith("S"):
                        continue
                    if pending_space and parts and parts[-1] != "-":
                        parts.append("-")
                    pending_space = False
                    parts.append(char)
                base = "".join(parts).strip("-")
                occurrence = seen[base]
                anchor = base if occurrence == 0 else "{}-{}".format(base, occurrence)
                while anchor in anchors:
                    occurrence += 1
                    anchor = "{}-{}".format(base, occurrence)
                if occurrence > 0:
                    duplicates[base].append(line_number)
                seen[base] = occurrence + 1
                anchors.add(anchor)
        if re.search(
            r"(?i)<\s*[a-z][^>]*\bid\s*=|<\s*a\b[^>]*\bname\s*=", line
        ):
            limitations.append("Explicit HTML heading/anchor identifiers are not inspected.")
        index += 1

    return anchors, dict(duplicates), sorted(set(limitations))


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _markdown_files(root: Path) -> Tuple[List[Path], List[Finding]]:
    paths: List[Path] = []
    findings: List[Finding] = []

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
            if path.suffix.lower() not in MARKDOWN_SUFFIXES:
                continue
            resolved = path.resolve(strict=False)
            if not _inside(root, resolved):
                findings.append(
                    Finding(
                        "document-outside-root",
                        path.relative_to(root).as_posix(),
                        1,
                        "Markdown symlink resolves outside the repository root; file was not read.",
                    )
                )
                continue
            paths.append(path)
    return sorted(paths, key=lambda path: path.relative_to(root).as_posix()), findings


def check_repository(root: Path) -> Dict[str, object]:
    """Check supported local Markdown links under root and return a JSON-safe report."""
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(str(root))

    files, findings = _markdown_files(root)
    headings_by_path: Dict[str, Tuple[Set[str], Dict[str, List[int]], List[str]]] = {}
    texts: Dict[str, str] = {}
    limitations: Set[str] = set()
    for path in files:
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        texts[relative] = text
        headings_by_path[relative] = heading_anchors(text)
        limitations.update(headings_by_path[relative][2])
    links_checked = 0
    external_links_skipped = 0
    for path in files:
        source_relative = path.relative_to(root).as_posix()
        links, link_limitations = extract_links(texts[source_relative])
        limitations.update(link_limitations)
        for link in links:
            if link.syntax == "undefined-reference":
                findings.append(
                    Finding(
                        "undefined-reference",
                        source_relative,
                        link.line,
                        "Reference link label '{}' has no matching definition.".format(link.destination),
                    )
                )
                continue
            destination = link.destination.strip()
            if not destination:
                findings.append(
                    Finding("empty-link", source_relative, link.line, "Link destination is empty.")
                )
                continue
            try:
                parsed = urlsplit(destination)
            except ValueError as error:
                findings.append(
                    Finding(
                        "invalid-link",
                        source_relative,
                        link.line,
                        "Cannot parse link destination '{}': {}".format(destination, error),
                    )
                )
                continue
            if parsed.scheme or parsed.netloc:
                external_links_skipped += 1
                continue
            try:
                decoded_path = unquote(parsed.path, encoding="utf-8", errors="strict")
                decoded_fragment = unquote(parsed.fragment, encoding="utf-8", errors="strict")
            except UnicodeDecodeError:
                findings.append(
                    Finding(
                        "invalid-url-encoding",
                        source_relative,
                        link.line,
                        "Link contains percent-encoded bytes that are not valid UTF-8.",
                    )
                )
                continue

            if decoded_path.startswith("/"):
                candidate = root / decoded_path.lstrip("/")
            elif decoded_path:
                candidate = path.parent / decoded_path
            else:
                candidate = path
            resolved_target = candidate.resolve(strict=False)
            if not _inside(root, resolved_target):
                findings.append(
                    Finding(
                        "path-outside-root",
                        source_relative,
                        link.line,
                        "Link '{}' resolves outside the repository root; target was not read.".format(destination),
                    )
                )
                continue
            links_checked += 1
            if not resolved_target.exists():
                findings.append(
                    Finding(
                        "missing-target",
                        source_relative,
                        link.line,
                        "Link target '{}' does not exist.".format(decoded_path or source_relative),
                    )
                )
                continue
            if not decoded_fragment:
                continue
            if resolved_target.is_dir():
                limitations.add(
                    "Heading anchors on directory links are not inspected: '{}'".format(destination)
                )
                continue
            if resolved_target.suffix.lower() not in MARKDOWN_SUFFIXES:
                limitations.add(
                    "Fragments on non-Markdown targets are not heading-checked: '{}'".format(destination)
                )
                continue
            target_relative = resolved_target.relative_to(root).as_posix()
            if target_relative not in headings_by_path:
                target_text = resolved_target.read_text(encoding="utf-8")
                headings_by_path[target_relative] = heading_anchors(target_text)
                limitations.update(headings_by_path[target_relative][2])
            if decoded_fragment not in headings_by_path[target_relative][0]:
                target_limitations = headings_by_path[target_relative][2]
                if any("HTML" in limitation for limitation in target_limitations):
                    limitations.add(
                        "Anchor '#{}' in '{}' was not checked because explicit HTML anchors are unsupported.".format(
                            decoded_fragment, target_relative
                        )
                    )
                else:
                    findings.append(
                        Finding(
                            "missing-anchor",
                            source_relative,
                            link.line,
                            "Anchor '#{}' does not exist in '{}'.".format(decoded_fragment, target_relative),
                        )
                    )

    findings.sort(key=lambda finding: (finding.path, finding.line, finding.code, finding.message))
    status = "FAIL" if findings else ("NOT VERIFIED" if limitations else "PASS")
    return {
        "status": status,
        "root": ".",
        "documents_scanned": len(files),
        "links_checked": links_checked,
        "external_links_skipped": external_links_skipped,
        "findings": [asdict(finding) for finding in findings],
        "limitations": sorted(limitations),
        "scope": [
            "Supported local Markdown inline/reference links, existing targets, and heading anchors.",
            "External URLs are not fetched.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check supported Markdown links and heading anchors locally. "
            "External URLs are never fetched."
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


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    try:
        report = check_repository(root)
    except (OSError, RuntimeError, UnicodeError) as error:
        print("check_doc_links.py: cannot check '{}': {}".format(root, error), file=sys.stderr)
        return 2

    if args.format == "json":
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print("STATUS: {}".format(report["status"]))
        print(
            "Scanned {} document(s); checked {} local link(s); skipped {} external URL(s).".format(
                report["documents_scanned"],
                report["links_checked"],
                report["external_links_skipped"],
            )
        )
        for finding in report["findings"]:
            print(
                "{}:{}: {}: {}".format(
                    finding["path"], finding["line"], finding["code"], finding["message"]
                )
            )
        for limitation in report["limitations"]:
            print("NOT VERIFIED: {}".format(limitation))
    if report["status"] == "FAIL":
        return 1
    if report["status"] == "NOT VERIFIED":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
