"""
Core Markdown to HTML conversion logic.
"""

import os
import uuid

import markdown
from pathlib import Path
from typing import Optional


class MarkdownConverter:
    """Convert Markdown to HTML with various options."""

    def __init__(
        self,
        enable_toc: bool = False,
        enable_code_highlight: bool = True,
        theme: str = "default",
    ):
        self.enable_toc = enable_toc
        self.enable_code_highlight = enable_code_highlight
        self.theme = theme

    def _get_extensions(self) -> list:
        """Get markdown extensions based on options."""
        extensions = ["extra", "sane_lists"]

        if self.enable_toc:
            extensions.append("toc")

        if self.enable_code_highlight:
            extensions.append("codehilite")

        return extensions

    def convert_text(self, md_text: str) -> str:
        """Convert Markdown text to HTML string."""
        html_body = markdown.markdown(
            md_text,
            extensions=self._get_extensions(),
        )

        # Wrap in full HTML document
        html = self._wrap_html(html_body)
        return html

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
        """Convert top-level .md files, refusing existing output paths.

        Known collisions are checked before writing any output. A batch is not
        transactional: a later read/write failure can leave earlier new files.
        """
        input_p = Path(input_dir)
        output_p = Path(output_dir)
        if not input_p.is_dir():
            raise NotADirectoryError("Input is not a directory: {}".format(input_p))

        md_files = sorted(input_p.glob("*.md"))
        outputs = [output_p / (path.stem + ".html") for path in md_files]
        for output in outputs:
            self._check_output(output)
        for md_file, out_file in zip(md_files, outputs):
            self.convert_file(str(md_file), str(out_file))
        return len(md_files)

    def _wrap_html(self, body: str) -> str:
        """Wrap HTML body in a full HTML document with styling."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
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
    </style>
</head>
<body>
{body}
</body>
</html>"""
