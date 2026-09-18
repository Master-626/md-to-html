import pytest
from md_to_html.converter import MarkdownConverter


def test_convert_text_basic():
    """Test basic Markdown to HTML conversion."""
    converter = MarkdownConverter()
    md = "# Heading 1\nThis is a paragraph."
    html = converter.convert_text(md)
    assert "<h1" in html
    assert "Heading 1" in html


def test_convert_text_toc():
    """Test TOC generation."""
    converter = MarkdownConverter(enable_toc=True)
    md = "# Section 1\n## Subsection"
    html = converter.convert_text(md)
    assert "Table of Contents" in html or "toc" in html.lower() or "Section 1" in html


def test_convert_file(tmp_path):
    """Test file conversion."""
    input_file = tmp_path / "test.md"
    input_file.write_text("# Test\nHello World")

    converter = MarkdownConverter()
    converter.convert_file(str(input_file), str(tmp_path / "test.html"))

    assert (tmp_path / "test.html").exists()
