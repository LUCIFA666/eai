from __future__ import annotations

import argparse
import html
import io
import json
import keyword
import mimetypes
import re
import tokenize
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
SECTION = "section"
ALLOWED_STATIC_SUFFIXES = {
    ".css",
    ".csv",
    ".gif",
    ".html",
    ".jpeg",
    ".jpg",
    ".js",
    ".json",
    ".mp4",
    ".png",
    ".svg",
    ".txt",
    ".webp",
    ".webm",
}

mimetypes.add_type("text/css", ".css")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("video/webm", ".webm")

# Navigation, numbering and the page layout are all derived from the filesystem
# (the `NN-` prefix defines order; the displayed number is the sorted position).
# There is intentionally NO hand-maintained chapter/section table here — drop a
# Markdown file with the right prefix and it appears, numbered, in the sidebar.
# Page skeleton lives in templates/page.html; styling in static/*.css. See
# templates/CONTRACT.md for the class/placeholder contract between the layers.


def is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def reject_private_path(path: Path) -> bool:
    return any(part in {".git", "reference"} for part in path.parts)


def resolve_doc_path(raw_url_path: str, root: Path = ROOT) -> Path | None:
    """Resolve a request URL to a Markdown page inside the project."""
    root = root.resolve()
    request_path = unquote(urlparse(raw_url_path).path)
    if request_path == "/":
        candidate = root / "README.md"
    else:
        relative = request_path.lstrip("/")
        candidate = root / relative
        if request_path.endswith("/"):
            candidate = candidate / "README.md"
        elif candidate.is_dir():
            candidate = candidate / "README.md"
        elif candidate.suffix == "":
            markdown_candidate = candidate.with_suffix(".md")
            if markdown_candidate.exists():
                candidate = markdown_candidate

    candidate = candidate.resolve()
    if not is_under(candidate, root):
        return None
    if reject_private_path(candidate):
        return None
    if candidate.suffix.lower() != ".md":
        return None
    if not candidate.is_file():
        return None
    return candidate


def resolve_static_path(raw_url_path: str, root: Path = ROOT) -> Path | None:
    root = root.resolve()
    request_path = unquote(urlparse(raw_url_path).path)
    candidate = (root / request_path.lstrip("/")).resolve()
    if not is_under(candidate, root):
        return None
    if reject_private_path(candidate):
        return None
    if candidate.suffix.lower() not in ALLOWED_STATIC_SUFFIXES:
        return None
    if not candidate.is_file():
        return None
    return candidate


def extract_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1)
    return path.stem


def strip_leading_number(title: str) -> str:
    """Drop a hard-coded leading section number like '4.5 ' or '08 ' from a title."""
    return re.sub(r"^\d+(?:\.\d+)*\s+", "", title).strip()


def clean_title(path: Path) -> str:
    """Page title with any author-written leading number removed."""
    return strip_leading_number(extract_title(path))


def link_for_doc(path: Path, root: Path = ROOT) -> str:
    return "/" + path.resolve().relative_to(root.resolve()).as_posix()


def href_for_markdown_link(raw_href: str, current_doc: Path, root: Path = ROOT) -> str:
    parsed = urlparse(raw_href)
    if parsed.scheme or raw_href.startswith("#"):
        return raw_href

    path_part, anchor = raw_href, ""
    if "#" in raw_href:
        path_part, anchor = raw_href.split("#", 1)
        anchor = "#" + anchor

    target = (current_doc.parent / path_part).resolve()
    if target.is_dir():
        target = target / "README.md"
    elif target.suffix == "":
        markdown_target = target.with_suffix(".md")
        if markdown_target.exists():
            target = markdown_target

    if is_under(target, root) and target.suffix.lower() == ".md" and target.exists():
        return link_for_doc(target, root) + anchor
    if is_under(target, root) and target.exists():
        return "/" + target.relative_to(root.resolve()).as_posix() + anchor
    return raw_href


def render_text(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def render_inline(text: str, current_doc: Path, root: Path = ROOT) -> str:
    # **`code`** spans must be stashed before the backtick split separates the ** markers.
    # Placeholders use ASCII control chars that html.escape() passes through unchanged.
    _stash: dict[str, str] = {}

    def _stash_bold_code(m: re.Match) -> str:
        key = f"\x02{len(_stash)}\x03"
        _stash[key] = f"<strong><code>{html.escape(m.group(1)[1:-1])}</code></strong>"
        return key

    def _render_link_label(label: str) -> str:
        # Link labels may themselves contain `code` spans; render them here because
        # the whole link is stashed before the backtick split below.
        out: list[str] = []
        for piece in re.split(r"(`[^`]+`)", label):
            if piece.startswith("`") and piece.endswith("`") and len(piece) > 2:
                out.append(f"<code>{html.escape(piece[1:-1])}</code>")
            elif piece:
                out.append(render_text(piece))
        return "".join(out)

    def _stash_link(m: re.Match) -> str:
        # Links/images are stashed whole before the backtick split, so a `code`
        # span inside the label cannot break the [label](href) pattern apart.
        key = f"\x02L{len(_stash)}\x03"
        if m.group(0).startswith("!"):
            src = href_for_markdown_link(m.group(2), current_doc, root)
            alt = html.escape(m.group(1), quote=True)
            _stash[key] = (
                f'<img class="doc-img" src="{html.escape(src, quote=True)}" alt="{alt}">'
            )
        else:
            href = href_for_markdown_link(m.group(2), current_doc, root)
            _stash[key] = (
                f'<a href="{html.escape(href, quote=True)}">{_render_link_label(m.group(1))}</a>'
            )
        return key

    text = re.sub(r"\*\*(`[^`]+`)\*\*", _stash_bold_code, text)
    text = re.sub(r"!?\[([^\]]*)\]\(([^)]+)\)", _stash_link, text)
    parts = re.split(r"(`[^`]+`)", text)
    rendered: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("`") and part.endswith("`"):
            rendered.append(f"<code>{html.escape(part[1:-1])}</code>")
            continue
        rendered.append(render_text(part))
    result = "".join(rendered)
    # Later stash entries (links) may contain earlier placeholders (bold-code)
    # in their rendered values, so expand in reverse insertion order.
    for key, val in reversed(_stash.items()):
        result = result.replace(key, val)
    return result


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w一-鿿-]+", "-", text.lower()).strip("-")
    return slug or "section"


def close_list(open_list: str | None, output: list[str]) -> str | None:
    if open_list:
        output.append(f"</{open_list}>")
    return None


def is_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_table_separator(line: str) -> bool:
    if not is_table_row(line):
        return False
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def render_table(table_lines: list[str], current_doc: Path, root: Path = ROOT) -> str:
    header = split_table_row(table_lines[0])
    rows = [split_table_row(line) for line in table_lines[2:]]
    column_count = len(header)
    table_class = f"table-cols-{column_count}"
    header_html = "".join(
        f"<th>{render_inline(cell, current_doc, root)}</th>" for cell in header
    )
    row_html = []
    for row in rows:
        cells = row + [""] * max(0, len(header) - len(row))
        rendered_cells = "".join(
            f"<td>{render_inline(cell, current_doc, root)}</td>" for cell in cells[: len(header)]
        )
        row_html.append(f"<tr>{rendered_cells}</tr>")
    body = "\n".join(row_html)
    return (
        f'<div class="table-wrap {table_class}"><table>'
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table></div>"
    )


def is_raw_html_block_start(line: str) -> bool:
    stripped = line.strip()
    return bool(
        re.match(r"^<figure\b", stripped)
        or re.match(r"^<table\b", stripped)
        or re.match(r"^<pre\b", stripped)
        or re.match(r"^<p\s+align=", stripped)
        or re.match(r'^<p\s+class="doc-figure-(title|subtitle)"', stripped)
        or re.match(r"^<span\s+id=", stripped)
        or re.match(r"^<div\s+align=", stripped)
        or stripped.startswith(
            (
                '<div class="concept-note',
                '<div class="image-caption',
                '<div class="code-explorer',
                '<div class="maniskill-demo-player',
            )
        )
    )


def html_block_delta(line: str) -> int:
    block_tags = r"div|figure|section|table|p|span|pre|code"
    opens = len(re.findall(rf"<({block_tags})\b", line))
    closes = len(re.findall(rf"</({block_tags})>", line))
    return opens - closes


PYTHON_BUILTINS = {
    "False",
    "None",
    "True",
    "dict",
    "float",
    "int",
    "len",
    "list",
    "max",
    "min",
    "print",
    "range",
    "round",
    "set",
    "str",
    "tuple",
}


def text_between(lines: list[str], start: tuple[int, int], end: tuple[int, int]) -> str:
    if start == end or not lines:
        return ""
    start_line, start_col = start
    end_line, end_col = end
    if start_line > len(lines):
        return ""
    if end_line > len(lines):
        end_line = len(lines)
        end_col = len(lines[-1])
    if start_line == end_line:
        return lines[start_line - 1][start_col:end_col]
    parts = [lines[start_line - 1][start_col:]]
    parts.extend(lines[start_line:end_line - 1])
    parts.append(lines[end_line - 1][:end_col])
    return "".join(parts)


def span(class_name: str, value: str) -> str:
    return f'<span class="syntax-{class_name}">{html.escape(value)}</span>'


def highlight_python(code: str) -> str:
    lines = code.splitlines(keepends=True)
    if not lines:
        return ""

    rendered: list[str] = []
    last = (1, 0)
    try:
        tokens = tokenize.generate_tokens(io.StringIO(code).readline)
        for token in tokens:
            token_type = token.type
            if token_type in {tokenize.ENCODING, tokenize.ENDMARKER}:
                continue
            rendered.append(html.escape(text_between(lines, last, token.start)))
            value = token.string
            if token_type == tokenize.COMMENT:
                rendered.append(span("comment", value))
            elif token_type == tokenize.STRING:
                rendered.append(span("string", value))
            elif token_type == tokenize.NUMBER:
                rendered.append(span("number", value))
            elif token_type == tokenize.NAME and keyword.iskeyword(value):
                rendered.append(span("keyword", value))
            elif token_type == tokenize.NAME and value in PYTHON_BUILTINS:
                rendered.append(span("builtin", value))
            else:
                rendered.append(html.escape(value))
            last = token.end
        rendered.append(html.escape(text_between(lines, last, (len(lines), len(lines[-1])))))
    except tokenize.TokenError:
        return html.escape(code)
    return "".join(rendered)


def highlight_markdown_code(code: str) -> str:
    escaped = html.escape(code)
    escaped = re.sub(r"(^|\n)(#{1,6})( .+)", r'\1<span class="syntax-heading">\2\3</span>', escaped)
    return escaped


_BASH_KEYWORDS = {
    "if", "then", "else", "elif", "fi", "for", "do", "done",
    "while", "until", "case", "esac", "in", "return", "exit",
    "export", "unset", "local", "source", "readonly", "continue",
    "break", "function",
}


def highlight_bash(code: str) -> str:
    result: list[str] = []
    for line in code.splitlines(keepends=True):
        eol = "\n" if line.endswith("\n") else ""
        s = line.rstrip("\n")

        if re.match(r"^\s*#", s):
            result.append(span("comment", s) + eol)
            continue

        buf: list[str] = []

        def flush(buf: list[str] = buf) -> None:
            if buf:
                result.append(html.escape("".join(buf)))
                buf.clear()

        i = 0
        while i < len(s):
            c = s[i]
            if c == "'":
                flush()
                j = s.find("'", i + 1)
                j = j if j != -1 else len(s) - 1
                result.append(span("string", s[i : j + 1]))
                i = j + 1
            elif c == '"':
                flush()
                j = i + 1
                while j < len(s):
                    if s[j] == "\\":
                        j += 2
                    elif s[j] == '"':
                        break
                    else:
                        j += 1
                result.append(span("string", s[i : j + 1]))
                i = j + 1
            elif c == "$":
                flush()
                m = re.match(
                    r"\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_]*|\$[0-9@#*?!\-]", s[i:]
                )
                if m:
                    result.append(span("builtin", m.group(0)))
                    i += len(m.group(0))
                else:
                    result.append(html.escape(c))
                    i += 1
            elif c == "#" and (i == 0 or s[i - 1] in " \t"):
                flush()
                result.append(span("comment", s[i:]))
                i = len(s)
            elif re.match(r"[A-Za-z_]", c):
                m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", s[i:])
                word = m.group(0)  # type: ignore[union-attr]
                prev = s[i - 1] if i > 0 else None
                at_boundary = prev is None or prev in " \t|;(&{"
                if word in _BASH_KEYWORDS and at_boundary:
                    flush()
                    result.append(span("keyword", word))
                else:
                    buf.append(word)
                i += len(word)
            else:
                buf.append(c)
                i += 1

        flush()
        result.append(eol)

    return "".join(result)


def render_code_block(code_lines: list[str], code_language: str) -> str:
    code = "\n".join(code_lines)
    language_key = code_language.lower()
    if language_key in {"python", "py"}:
        rendered = highlight_python(code)
    elif language_key in {"markdown", "md"}:
        rendered = highlight_markdown_code(code)
    elif language_key in {"bash", "sh", "shell", "zsh"}:
        rendered = highlight_bash(code)
    else:
        rendered = html.escape(code)

    language_class = f" language-{html.escape(language_key)}" if language_key else ""
    return (
        f'<pre class="code-block{language_class}">'
        f'<code class="{language_class.strip()}">{rendered}</code>'
        "</pre>"
    )


def render_markdown(
    markdown: str,
    current_doc: Path,
    root: Path = ROOT,
    page_number: str | None = None,
) -> str:
    output: list[str] = []
    _list_stack: list[tuple[str, int]] = []  # (tag, indent)
    _li_pending: bool = False  # True if last <li> needs </li> closure
    in_code = False
    code_lines: list[str] = []
    code_language = ""
    h1_injected = False
    lines = markdown.splitlines()
    index = 0

    def _close_pending_li() -> None:
        nonlocal _li_pending
        if _li_pending:
            output.append("</li>")
            _li_pending = False

    def _close_lists() -> None:
        nonlocal _list_stack
        _close_pending_li()
        while _list_stack:
            tag, _ = _list_stack.pop()
            output.append(f"</{tag}>")

    while index < len(lines):
        raw_line = lines[index]
        line = raw_line.rstrip()

        fence = re.match(r"^```([A-Za-z0-9_-]*)\s*$", line)
        if fence:
            if in_code:
                output.append(render_code_block(code_lines, code_language))
                in_code = False
                code_lines = []
                code_language = ""
            else:
                _close_lists()
                in_code = True
                code_language = fence.group(1)
            index += 1
            continue

        if in_code:
            code_lines.append(raw_line)
            index += 1
            continue

        if not line.strip():
            _close_lists()
            index += 1
            continue

        # Keep a display-math region in one DOM text node. Rendering each
        # Markdown source line as a separate <p> splits the opening/closing
        # ``$$`` delimiters across elements, so KaTeX auto-render cannot see
        # the complete expression and the browser shows the raw LaTeX.
        if line.strip() == "$$":
            _close_lists()
            math_lines: list[str] = []
            index += 1
            while index < len(lines) and lines[index].strip() != "$$":
                math_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            formula = html.escape("\n".join(math_lines))
            output.append(f'<div class="math-block">$$\n{formula}\n$$</div>')
            continue

        if line.strip() == "<!-- AUTO-TOC -->":
            _close_lists()
            output.append(render_auto_toc(current_doc, root))
            index += 1
            continue

        if is_raw_html_block_start(line):
            _close_lists()
            block_lines = [raw_line]
            depth = html_block_delta(raw_line)
            bi = index + 1
            while depth > 0 and bi < len(lines):
                block_line = lines[bi]
                bi += 1
                block_lines.append(block_line)
                depth += html_block_delta(block_line)
            index = bi
            output.append("\n".join(block_lines))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            _close_lists()
            level = len(heading.group(1))
            title = heading.group(2)
            if level == 1 and page_number and not h1_injected:
                title = f"{page_number} {strip_leading_number(title)}".strip()
                h1_injected = True
            output.append(
                f'<h{level} id="{slugify(title)}">{render_inline(title, current_doc, root)}</h{level}>'
            )
            index += 1
            continue

        if (
            is_table_row(line)
            and index + 1 < len(lines)
            and is_table_separator(lines[index + 1].rstrip())
        ):
            _close_lists()
            table_lines = [line, lines[index + 1].rstrip()]
            index += 2
            while index < len(lines) and is_table_row(lines[index].rstrip()):
                table_lines.append(lines[index].rstrip())
                index += 1
            output.append(render_table(table_lines, current_doc, root))
            continue

        unordered = re.match(r"^([ \t]*)[-*]\s+(.+)$", line)
        if unordered:
            indent = len(unordered.group(1))
            content = unordered.group(2)
            while _list_stack and _list_stack[-1][1] > indent:
                tag, _ = _list_stack.pop()
                _close_pending_li()
                output.append(f"</{tag}>")
            if _list_stack and _list_stack[-1][1] == indent:
                _close_pending_li()
            elif not _list_stack or (_list_stack and indent > _list_stack[-1][1]):
                output.append("<ul>")
                _list_stack.append(("ul", indent))
            output.append(f"<li>{render_inline(content, current_doc, root)}</li>")
            _li_pending = True
            index += 1
            continue

        ordered = re.match(r"^([ \t]*)\d+\.\s+(.+)$", line)
        if ordered:
            indent = len(ordered.group(1))
            content = ordered.group(2)
            while _list_stack and _list_stack[-1][1] > indent:
                tag, _ = _list_stack.pop()
                _close_pending_li()
                output.append(f"</{tag}>")
            if _list_stack and _list_stack[-1][1] == indent:
                _close_pending_li()
            elif not _list_stack or (_list_stack and indent > _list_stack[-1][1]):
                output.append("<ol>")
                _list_stack.append(("ol", indent))
            output.append(f"<li>{render_inline(content, current_doc, root)}</li>")
            _li_pending = True
            index += 1
            continue

        if re.match(r"^>\s?", line):
            _close_lists()
            bq_parts: list[str] = []
            while index < len(lines):
                bq_raw = lines[index].rstrip()
                m = re.match(r"^>\s?(.*)", bq_raw)
                if m:
                    bq_parts.append(m.group(1))
                    index += 1
                else:
                    break
            inner_parts: list[str] = []
            in_bq_list = False
            for part in bq_parts:
                li = re.match(r"^[-*]\s+(.+)$", part)
                if li:
                    if not in_bq_list:
                        inner_parts.append("<ul>")
                        in_bq_list = True
                    inner_parts.append(f"<li>{render_inline(li.group(1), current_doc, root)}</li>")
                elif part.strip():
                    if in_bq_list:
                        inner_parts.append("</ul>")
                        in_bq_list = False
                    inner_parts.append(f"<p>{render_inline(part, current_doc, root)}</p>")
            if in_bq_list:
                inner_parts.append("</ul>")
            output.append(f"<blockquote>{''.join(inner_parts)}</blockquote>")
            continue

        if re.match(r"^\s*<(img|video)\s", line):
            _close_lists()
            output.append(line.strip())
            index += 1
            continue

        _close_lists()
        output.append(f"<p>{render_inline(line, current_doc, root)}</p>")
        index += 1

    _close_lists()
    if in_code:
        output.append(render_code_block(code_lines, code_language))
    return "\n".join(output)


# --------------------------------------------------------------------------- #
# Filesystem-derived structure: chapters, ordered lessons, derived numbering.  #
# --------------------------------------------------------------------------- #


class Node:
    """A navigation/numbering node derived from one Markdown page."""

    __slots__ = ("path", "number", "title", "children")

    def __init__(self, path: Path, number: str, title: str, children: list["Node"]):
        self.path = path
        self.number = number
        self.title = title
        self.children = children

    @property
    def label(self) -> str:
        return f"{self.number} {self.title}".strip()


def chapter_dirs(root: Path = ROOT) -> Iterable[Path]:
    section_root = root / SECTION
    if not section_root.exists():
        return []
    return (
        path
        for path in sorted(section_root.iterdir())
        if path.is_dir() and (path / "README.md").is_file()
    )


def chapter_number(chapter_dir: Path) -> str:
    """Displayed chapter number = the directory's numeric prefix, e.g. '04', '10'."""
    prefix = chapter_dir.name.split("-", 1)[0]
    return prefix


def _chapter_int(chapter_dir: Path) -> int | str:
    prefix = chapter_number(chapter_dir)
    return int(prefix) if prefix.isdigit() else prefix


def _order_key(path: Path) -> tuple[int, str]:
    match = re.match(r"^(\d+)", path.name)
    return (int(match.group(1)) if match else 10_000, path.name)


def ordered_lesson_files(directory: Path) -> list[Path]:
    """Numbered lesson pages (NN-*.md) directly in `directory`, in prefix order.

    Files without a numeric prefix (e.g. improve.md / summary.md) are auxiliary
    notes, not lessons, so they are not surfaced or numbered in the navigation.
    """
    return sorted(
        (
            p
            for p in directory.glob("*.md")
            if p.name != "README.md" and re.match(r"^\d+-", p.name)
        ),
        key=_order_key,
    )


def child_lesson_pages(lesson: Path) -> list[Path]:
    """Pages in the child directory belonging to a lesson page (README first)."""
    child_dir = lesson.with_suffix("")
    if not child_dir.is_dir() or child_dir.name == "inventory":
        return []
    pages: list[Path] = []
    readme = child_dir / "README.md"
    if readme.is_file():
        pages.append(readme)
    pages.extend(ordered_lesson_files(child_dir))
    return pages


def _orphan_subdirs(directory: Path) -> list[Path]:
    """Sub-directories that hold pages but are not paired with a lesson `.md`.

    Example: `.../04-simplevla-rl/hands-on/` has no `hands-on.md` sibling, so its
    pages are folded into the parent's numbering (continuing after the NN-*.md).
    """
    result: list[Path] = []
    for sub in sorted(directory.iterdir(), key=_order_key):
        if not sub.is_dir() or sub.name in ("inventory", "assets"):
            continue
        if sub.with_suffix(".md").exists():
            continue  # paired directory -> reached through its lesson .md
        if any(sub.glob("*.md")):
            result.append(sub)
    return result


def _make_node(lesson_md: Path, number: str) -> Node:
    return Node(lesson_md, number, clean_title(lesson_md), _child_nodes(lesson_md, number))


def _ordered_child_nodes(directory: Path, parent_number: str) -> list[Node]:
    """README (导读, .0) + numbered pages + folded orphan-subdir pages, in order."""
    nodes: list[Node] = []
    readme = directory / "README.md"
    if readme.is_file():
        nodes.append(Node(readme, f"{parent_number}.0", clean_title(readme), []))
    counter = 0
    for child in ordered_lesson_files(directory):
        counter += 1
        nodes.append(_make_node(child, f"{parent_number}.{counter}"))
    for sub in _orphan_subdirs(directory):
        for page in ordered_lesson_files(sub):
            counter += 1
            nodes.append(_make_node(page, f"{parent_number}.{counter}"))
    return nodes


def _child_nodes(lesson_md: Path, parent_number: str) -> list[Node]:
    child_dir = lesson_md.with_suffix("")
    if not child_dir.is_dir() or child_dir.name == "inventory":
        return []
    return _ordered_child_nodes(child_dir, parent_number)


def build_chapter_nodes(chapter_dir: Path) -> list[Node]:
    chap_int = _chapter_int(chapter_dir)
    nodes: list[Node] = []
    counter = 0
    for lesson in ordered_lesson_files(chapter_dir):
        counter += 1
        nodes.append(_make_node(lesson, f"{chap_int}.{counter}"))
    for sub in _orphan_subdirs(chapter_dir):
        for page in ordered_lesson_files(sub):
            counter += 1
            nodes.append(_make_node(page, f"{chap_int}.{counter}"))
    return nodes


def _iter_nodes(nodes: list[Node]) -> Iterator[Node]:
    for node in nodes:
        yield node
        yield from _iter_nodes(node.children)


def chapter_of(doc: Path, root: Path = ROOT) -> Path | None:
    section_root = (root / SECTION).resolve()
    node = doc.resolve()
    if not is_under(node, section_root):
        return None
    while node.parent != section_root:
        node = node.parent
        if node == node.parent:
            return None
    return node if node.is_dir() else None


def number_for_doc(doc: Path, root: Path = ROOT) -> str | None:
    doc = doc.resolve()
    chapter = chapter_of(doc, root)
    if chapter is None:
        return None
    if doc == (chapter / "README.md").resolve():
        return chapter_number(chapter)
    for node in _iter_nodes(build_chapter_nodes(chapter)):
        if node.path.resolve() == doc:
            return node.number
    return None


def chapter_reading_order(chapter_dir: Path) -> list[Node]:
    return list(_iter_nodes(build_chapter_nodes(chapter_dir)))


# --------------------------------------------------------------------------- #
# Auto-generated table of contents (<!-- AUTO-TOC -->) and prev/next footer.   #
# --------------------------------------------------------------------------- #


def _render_toc_nodes(nodes: list[Node], root: Path) -> str:
    if not nodes:
        return ""
    items = []
    for node in nodes:
        href = link_for_doc(node.path, root)
        inner = _render_toc_nodes(node.children, root)
        items.append(
            f'<li><a href="{href}">{html.escape(node.label)}</a>{inner}</li>'
        )
    return '<ul class="auto-toc">' + "".join(items) + "</ul>"


def render_auto_toc(current_doc: Path, root: Path = ROOT) -> str:
    current_doc = current_doc.resolve()
    section_root = (root / SECTION).resolve()
    if current_doc == (section_root / "README.md").resolve():
        items = []
        for chapter in chapter_dirs(root):
            href = link_for_doc(chapter / "README.md", root)
            label = f"{chapter_number(chapter)} {clean_title(chapter / 'README.md')}".strip()
            items.append(f'<li><a href="{href}">{html.escape(label)}</a></li>')
        return '<ul class="auto-toc">' + "".join(items) + "</ul>"
    chapter = chapter_of(current_doc, root)
    if chapter and current_doc == (chapter / "README.md").resolve():
        return _render_toc_nodes(build_chapter_nodes(chapter), root)
    return ""


def _seq_label(number: str, path: Path) -> str:
    return f"{number} {clean_title(path)}".strip()


def render_prevnext(doc: Path, root: Path = ROOT) -> str:
    doc = doc.resolve()
    chapter = chapter_of(doc, root)
    if chapter is None:
        return ""
    chapter_readme = chapter / "README.md"
    sequence: list[tuple[str, Path]] = [("", chapter_readme)]
    sequence.extend((node.number, node.path) for node in chapter_reading_order(chapter))

    idx = next(
        (k for k, (_n, p) in enumerate(sequence) if p.resolve() == doc),
        None,
    )
    if idx is None:
        return ""

    parts: list[str] = []
    if idx > 0:
        pnum, ppath = sequence[idx - 1]
        plabel = clean_title(chapter_readme) if idx - 1 == 0 else _seq_label(pnum, ppath)
        parts.append(
            f'<a class="nav-prev" href="{link_for_doc(ppath, root)}">← 上一节：{html.escape(plabel)}</a>'
        )
    if doc != chapter_readme.resolve():
        parts.append(
            f'<a class="nav-up" href="{link_for_doc(chapter_readme, root)}">章节首页</a>'
        )
    if idx < len(sequence) - 1:
        nnum, npath = sequence[idx + 1]
        parts.append(
            f'<a class="nav-next" href="{link_for_doc(npath, root)}">下一节：{html.escape(_seq_label(nnum, npath))} →</a>'
        )
    if not parts:
        return ""
    return '<nav class="page-nav" aria-label="翻页">' + "".join(parts) + "</nav>"


# --------------------------------------------------------------------------- #
# Sidebar navigation (driven entirely by the derived node tree).              #
# --------------------------------------------------------------------------- #


def lesson_contains_doc(lesson: Path, current_doc: Path | None) -> bool:
    if current_doc is None:
        return False
    lesson = lesson.resolve()
    if current_doc == lesson:
        return True
    child_dir = lesson.with_suffix("")
    return child_dir.is_dir() and is_under(current_doc, child_dir)


def _render_nav_node(node: Node, current_doc: Path | None, root: Path, level: int) -> list[str]:
    selected = current_doc == node.path.resolve()
    active = selected or lesson_contains_doc(node.path, current_doc)
    label = html.escape(node.label)
    href = link_for_doc(node.path, root)

    if level == 0:
        details_cls = "subchapter-group"
        link_cls = "lesson-link subchapter-parent" + (" active" if selected else "")
        nested_cls = "nested-lesson-list"
    else:
        details_cls = f"lesson-tree-group level-{level}"
        link_cls = f"lesson-link nested tree-parent level-{level}" + (" active" if selected else "")
        nested_cls = f"nested-lesson-list level-{level + 1}"

    lines = [f'<details class="{details_cls}"{" open" if active else ""}>']
    lines.append(f'<summary><a class="{link_cls}" href="{href}">{label}</a></summary>')
    lines.append(f'<div class="{nested_cls}">')
    for child in node.children:
        lines.extend(_render_nav_node(child, current_doc, root, level + 1))
    lines.append("</div>")
    lines.append("</details>")
    return lines


def build_navigation(root: Path = ROOT, current_doc: Path | None = None) -> str:
    current_doc = current_doc.resolve() if current_doc else None
    root = root.resolve()
    items = [
        '<a class="home-link" href="/README.md">课程首页</a>',
        '<a class="home-link" href="/section/README.md">章节总览</a>',
    ]

    for chapter_dir in chapter_dirs(root):
        chapter_readme = chapter_dir / "README.md"
        active = bool(current_doc and is_under(current_doc, chapter_dir))
        details_attr = " open" if active else ""
        label = f"{chapter_number(chapter_dir)} {clean_title(chapter_readme)}".strip()
        items.append(f'<details class="chapter-group"{details_attr}>')
        items.append(
            f'<summary><a class="chapter-link" href="{link_for_doc(chapter_readme, root)}">{html.escape(label)}</a></summary>'
        )
        nodes = build_chapter_nodes(chapter_dir)
        if nodes:
            items.append('<div class="lesson-list">')
            for node in nodes:
                items.extend(_render_nav_node(node, current_doc, root, 0))
            items.append("</div>")
        items.append("</details>")
    return "\n".join(items)


# --------------------------------------------------------------------------- #
# Page assembly: fill the external template with rendered slots.              #
# --------------------------------------------------------------------------- #


def load_template(root: Path = ROOT) -> str:
    return (root / "templates" / "page.html").read_text(encoding="utf-8")


def render_page(doc_path: Path, root: Path = ROOT) -> str:
    root = root.resolve()
    doc_path = doc_path.resolve()
    number = number_for_doc(doc_path, root)
    raw_title = clean_title(doc_path)
    display_title = f"{number} {raw_title}".strip() if number else raw_title
    body = render_markdown(doc_path.read_text(encoding="utf-8"), doc_path, root, page_number=number)
    nav = build_navigation(root, doc_path)
    prevnext = render_prevnext(doc_path, root)
    rel_path = doc_path.relative_to(root).as_posix()

    template = load_template(root)
    return (
        template.replace("{{title}}", html.escape(display_title))
        .replace("{{breadcrumb}}", html.escape(rel_path))
        .replace("{{nav}}", nav)
        .replace("{{prevnext}}", prevnext)
        .replace("{{body}}", body)
    )


def compute_mtime(raw_path: str, root: Path = ROOT) -> float:
    """Newest mtime over the requested page's chapter subtree (for auto-reload)."""
    root = root.resolve()
    paths: list[Path] = []
    doc = resolve_doc_path(raw_path, root)
    if doc:
        paths.append(doc)
        chapter = chapter_of(doc, root)
        if chapter:
            paths.append(chapter)
            paths.extend(chapter.rglob("*.md"))
    section_root = root / SECTION
    if section_root.exists():
        paths.append(section_root)
    newest = 0.0
    for path in paths:
        try:
            newest = max(newest, path.stat().st_mtime)
        except OSError:
            continue
    return newest


class DocsRequestHandler(BaseHTTPRequestHandler):
    root = ROOT
    quiet = False

    def _send(self, status: HTTPStatus, content: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            self._send(HTTPStatus.OK, b"ok\n", "text/plain; charset=utf-8")
            return

        if parsed.path == "/__mtime":
            raw = parse_qs(parsed.query).get("path", ["/"])[0]
            payload = json.dumps({"mtime": compute_mtime(raw, self.root)}).encode("utf-8")
            self._send(HTTPStatus.OK, payload, "application/json; charset=utf-8")
            return

        doc_path = resolve_doc_path(parsed.path, self.root)
        if doc_path:
            content = render_page(doc_path, self.root).encode("utf-8")
            self._send(HTTPStatus.OK, content, "text/html; charset=utf-8")
            return

        static_path = resolve_static_path(parsed.path, self.root)
        if static_path:
            content = static_path.read_bytes()
            content_type = mimetypes.guess_type(static_path.name)[0] or "application/octet-stream"
            self._send(HTTPStatus.OK, content, content_type)
            return

        self._send(HTTPStatus.NOT_FOUND, b"not found\n", "text/plain; charset=utf-8")

    def log_message(self, format: str, *args: object) -> None:
        if not self.quiet:
            super().log_message(format, *args)


def make_handler(root: Path = ROOT, quiet: bool = False) -> type[DocsRequestHandler]:
    class ConfiguredDocsHandler(DocsRequestHandler):
        pass

    ConfiguredDocsHandler.root = root.resolve()
    ConfiguredDocsHandler.quiet = quiet
    return ConfiguredDocsHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Markdown course as a local HTML UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--root", default=ROOT, type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    handler = make_handler(args.root, args.quiet)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving Markdown docs at http://{args.host}:{args.port}/")
    print("Health check: /healthz")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
