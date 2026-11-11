"""
Core Markdown to HTML conversion logic.
"""

import functools
import html
import os
import re
import uuid
from pathlib import Path
from typing import Optional

import markdown
from markdown.extensions.toc import slugify, slugify_unicode

_H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_DEFAULT_TITLE = "Document"
_TOC_CSS = """
        .toc {
            background: #f8f9fa;
            border: 1px solid #e5e5e5;
            border-radius: 4px;
            padding: 0.75rem 1.25rem;
            margin: 0 0 1.5rem;
        }
        .toc ul {
            margin: 0.3rem 0;
            padding-left: 1.25rem;
        }
        .toc a {
            text-decoration: none;
        }
        .toc a:hover {
            text-decoration: underline;
        }
""".strip("\n")


def _slugify(value, separator):
    """Preserve ASCII heading ids, and keep non-ASCII headings addressable.

    Python-Markdown's default slugify drops text that does not fold to ASCII,
    so a heading such as ``你好`` becomes an empty id (``_1``). Headings that
    already produce an ASCII slug, including accented Latin, stay the same.
    """
    basic = slugify(value, separator)
    if basic:
        return basic
    return slugify_unicode(value, separator)


@functools.lru_cache(maxsize=1)
def _highlight_stylesheet():
    """Token CSS for codehilite, without Pygments' global ``pre`` rules."""
    try:
        from pygments.formatters import HtmlFormatter
    except ImportError:
        return ""
    css = HtmlFormatter(style="default").get_style_defs(".codehilite")
    lines = [line for line in css.splitlines() if line.lstrip().startswith(".codehilite")]
    return "\n".join(lines)


def _first_heading_text(body):
    match = _H1_RE.search(body)
    if not match:
        return None
    # Strip tags before unescaping so a literal ``&lt;em&gt;`` stays text.
    text = html.unescape(_TAG_RE.sub("", match.group(1)))
    text = " ".join(text.split())
    return text or None


class MarkdownConverter:
    """Convert Markdown to HTML with various options."""

    def __init__(
        self,
        enable_toc: bool = False,
        enable_code_highlight: bool = True,
        theme: str = "default",
        title: Optional[str] = None,
        title_from_heading: bool = False,
    ):
        self.enable_toc = enable_toc
        self.enable_code_highlight = enable_code_highlight
        self.theme = theme
        self.title = title
        self.title_from_heading = title_from_heading

    def _get_extensions(self) -> list:
        """Get markdown extensions based on options."""
        extensions = ["extra", "sane_lists"]

        if self.enable_toc:
            extensions.append("toc")

        if self.enable_code_highlight:
            extensions.append("codehilite")

        return extensions

    def _extension_configs(self) -> dict:
        configs = {}
        if self.enable_toc:
            configs["toc"] = {"slugify": _slugify}
        return configs

    def convert_text(self, md_text: str) -> str:
        """Convert Markdown text to a complete HTML document."""
        renderer = markdown.Markdown(
            extensions=self._get_extensions(),
            extension_configs=self._extension_configs(),
        )
        html_body = renderer.convert(md_text)
        if self.enable_toc and getattr(renderer, "toc_tokens", None):
            toc_html = renderer.toc
            # A [TOC] paragraph is already replaced in place. Prepend otherwise.
            if toc_html and toc_html not in html_body:
                if not toc_html.endswith("\n"):
                    toc_html += "\n"
                html_body = toc_html + html_body
        return self._wrap_html(html_body, self._resolve_title(html_body))

    def _resolve_title(self, body: str) -> str:
        if self.title is not None:
            return self.title
        if self.title_from_heading:
            heading = _first_heading_text(body)
            if heading:
                return heading
        return _DEFAULT_TITLE

    def convert_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """Convert Markdown file to HTML file."""
        input_p = Path(input_path)
        md_text = input_p.read_text(encoding="utf-8")

        html = self.convert_text(md_text)

        if output_path:
            output_p = Path(output_path)
            output_p.parent.mkdir(parents=True, exist_ok=True)
            self._write_new_file(output_p, html)

        return html

    @staticmethod
    def _check_output(output_path: Path) -> None:
        # lexists includes dangling symlinks; neither links nor files are replaced.
        if os.path.lexists(str(output_path)):
            raise FileExistsError("Output already exists: {}".format(output_path))

    @staticmethod
    def _write_new_file(output_path: Path, html: str) -> None:
        """Publish a complete file without ever replacing an existing entry."""
        MarkdownConverter._check_output(output_path)
        # A same-directory temporary file makes linking local to one filesystem.
        # Unlike replace/rename, link fails atomically if the destination exists.
        temporary = None
        try:
            candidate = output_path.parent / (".md-to-html-" + uuid.uuid4().hex)
            # Match ordinary file creation permissions, respecting the umask.
            fd = os.open(str(candidate), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
            temporary = str(candidate)
            try:
                stream = os.fdopen(fd, "w", encoding="utf-8")
            except BaseException:
                os.close(fd)
                raise
            with stream:
                stream.write(html)
            os.link(temporary, str(output_path))
        finally:
            if temporary is not None:
                os.unlink(temporary)

    def convert_directory(self, input_dir: str, output_dir: str) -> int:
        """Convert top-level Markdown files, refusing existing output paths.

        The suffix match is case-insensitive. Directories whose names end in
        ``.md`` are skipped. Two files that share an output name fail before
        anything is written. Known collisions are checked before writing. A
        batch is not transactional: a later read/write failure can leave
        earlier new files.
        """
        input_p = Path(input_dir)
        output_p = Path(output_dir)
        if not input_p.is_dir():
            raise NotADirectoryError("Input is not a directory: {}".format(input_p))

        md_files = self._markdown_sources(input_p)
        outputs = []
        seen = {}
        for path in md_files:
            output = output_p / (path.stem + ".html")
            previous = seen.get(output.name)
            if previous is not None:
                raise FileExistsError(
                    "Multiple Markdown files map to {}: {} and {}".format(
                        output.name, previous, path.name
                    )
                )
            seen[output.name] = path.name
            outputs.append(output)
        for output in outputs:
            self._check_output(output)
        for md_file, out_file in zip(md_files, outputs):
            self.convert_file(str(md_file), str(out_file))
        return len(md_files)

    @staticmethod
    def _markdown_sources(input_dir: Path) -> list:
        sources = []
        for path in input_dir.iterdir():
            # ``README.MD`` is Markdown. A directory named ``notes.md`` is not;
            # reading it used to abort the batch after earlier files were written.
            if path.suffix.lower() != ".md" or path.is_dir():
                continue
            sources.append(path)
        return sorted(sources)

    def _wrap_html(self, body: str, title: str) -> str:
        """Wrap HTML body in a full HTML document with styling."""
        extra_parts = []
        if self.enable_code_highlight and 'class="codehilite"' in body:
            highlight_css = _highlight_stylesheet()
            if highlight_css:
                extra_parts.append(highlight_css)
        if self.enable_toc:
            extra_parts.append(_TOC_CSS)
        style_extra = ""
        if extra_parts:
            style_extra = "\n" + "\n".join(extra_parts) + "\n"
        safe_title = html.escape(title, quote=False)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
            color: #333;
        }}
        pre {{
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
        }}
        code {{
            background: #f5f5f5;
            padding: 0.2em 0.4em;
            border-radius: 3px;
        }}
        pre code {{
            background: none;
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 0.4rem 0.6rem;
            text-align: left;
        }}
        th {{
            background: #f5f5f5;
        }}
        blockquote {{
            margin: 1rem 0;
            padding-left: 1rem;
            border-left: 4px solid #ddd;
            color: #555;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
{style_extra}    </style>
</head>
<body>
{body}
</body>
</html>"""
