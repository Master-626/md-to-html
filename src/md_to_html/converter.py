"""
Core Markdown to HTML conversion logic.
"""

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
            output_p.write_text(html, encoding="utf-8")

        return html

    def convert_directory(self, input_dir: str, output_dir: str) -> int:
        """Batch convert all Markdown files in a directory."""
        input_p = Path(input_dir)
        output_p = Path(output_dir)

        md_files = list(input_p.glob("*.md"))
        count = 0

        for md_file in md_files:
            out_file = output_p / (md_file.stem + ".html")
            self.convert_file(str(md_file), str(out_file))
            count += 1

        return count

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
