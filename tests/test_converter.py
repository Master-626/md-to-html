import re

import pytest

from md_to_html.converter import MarkdownConverter


def test_convert_text_basic():
    """Headings and paragraphs become a complete document."""
    html = MarkdownConverter().convert_text("# Heading 1\nThis is a paragraph.")
    assert html.startswith("<!DOCTYPE html>")
    assert "<h1>Heading 1</h1>" in html
    assert "<p>This is a paragraph.</p>" in html
    assert "<title>Document</title>" in html
    assert 'class="toc"' not in html
    assert "codehilite" not in html


def test_lists_links_and_blockquote():
    html = MarkdownConverter().convert_text(
        "See [site](https://example.com).\n\n- a\n- b\n\n> quoted\n"
    )
    assert 'href="https://example.com"' in html
    assert "<li>a</li>" in html
    assert "<li>b</li>" in html
    assert "<blockquote>" in html
    assert "border-left: 4px solid #ddd" in html


def test_tables_and_images_are_styled():
    html = MarkdownConverter().convert_text(
        "| A | B |\n| --- | --- |\n| 1 | 2 |\n\n![alt](pic.png)\n"
    )
    assert "<td>1</td>" in html
    assert "border-collapse: collapse" in html
    assert 'src="pic.png"' in html
    assert "max-width: 100%" in html


def test_convert_text_toc():
    """--toc inserts a linked table of contents, not only heading ids."""
    html = MarkdownConverter(enable_toc=True).convert_text("# Section 1\n\n## Subsection\n")
    assert html.count('class="toc"') == 1
    assert 'href="#section-1"' in html
    assert 'href="#subsection"' in html
    assert html.index('class="toc"') < html.index("<h1")
    assert ".toc {" in html


def test_toc_marker_is_not_duplicated():
    html = MarkdownConverter(enable_toc=True).convert_text("# Title\n\n[TOC]\n\n## Sub\n")
    assert html.count('class="toc"') == 1
    assert html.index("<h1") < html.index('class="toc"')
    assert 'href="#sub"' in html


def test_toc_marker_inside_code_does_not_suppress_contents():
    html = MarkdownConverter(enable_toc=True).convert_text("```\n[TOC]\n```\n\n# Real\n")
    assert html.count('class="toc"') == 1
    assert 'href="#real"' in html
    # Highlighting splits the fence, but the marker text is still code.
    assert "TOC" in html.split('class="codehilite"', 1)[1]


def test_inline_toc_text_still_generates_contents():
    html = MarkdownConverter(enable_toc=True).convert_text("See [TOC] inline\n\n# A\n")
    assert "See [TOC] inline" in html
    assert 'href="#a"' in html


def test_toc_without_headings_is_omitted():
    html = MarkdownConverter(enable_toc=True).convert_text("Just text.\n")
    assert 'class="toc"' not in html
    assert "<p>Just text.</p>" in html


def test_toc_ids_keep_ascii_slugs_and_unicode_fallbacks():
    accented = MarkdownConverter(enable_toc=True).convert_text("# Héllo\n")
    assert 'id="hello"' in accented
    assert 'href="#hello"' in accented

    mixed = MarkdownConverter(enable_toc=True).convert_text("# 你好 Hello\n")
    assert 'id="hello"' in mixed

    chinese = MarkdownConverter(enable_toc=True).convert_text("# 你好\n\n## 世界\n\n# 你好\n")
    assert 'id="你好"' in chinese
    assert 'href="#你好"' in chinese
    assert 'href="#世界"' in chinese
    assert 'href="#你好_1"' in chinese
    assert 'id="_1"' not in chinese


def test_code_highlight_embeds_matching_colors():
    html = MarkdownConverter().convert_text("```python\nprint('hi')\nx < y\n```\n")
    assert "print" in html
    assert "&lt;" in html
    assert "< y" not in html
    classes = re.findall(r'<span class="([a-z][a-z0-9]*)"', html)
    assert classes
    assert any(".codehilite .{}".format(name) in html for name in classes)
    # Pygments' unscoped `pre { line-height: 125% }` must not override our CSS.
    assert "line-height: 125%" not in html


def test_highlight_can_be_disabled():
    html = MarkdownConverter(enable_code_highlight=False).convert_text(
        "```python\nprint('hi')\n```\n"
    )
    assert 'class="language-python"' in html
    assert "codehilite" not in html
    assert "print" in html


def test_unlabeled_and_empty_fences_do_not_crash():
    unlabeled = MarkdownConverter().convert_text("```\nprint('hi')\n```\n")
    assert "print" in unlabeled
    empty = MarkdownConverter().convert_text("```\n```\n")
    assert empty.startswith("<!DOCTYPE html>")
    blank = MarkdownConverter().convert_text("")
    assert "<title>Document</title>" in blank
    assert "<body>" in blank


def test_explicit_title_overrides_heading_and_is_escaped():
    html = MarkdownConverter(title="Custom <T> &", title_from_heading=True).convert_text(
        "# Ignored\n"
    )
    assert "<title>Custom &lt;T&gt; &amp;</title>" in html
    assert "<title>Custom <T>" not in html


def test_title_from_heading():
    html = MarkdownConverter(enable_toc=True, title_from_heading=True).convert_text(
        "# Hello *world*\n\n## Detail\n"
    )
    assert "<title>Hello world</title>" in html
    assert 'href="#hello-world"' in html

    named = MarkdownConverter(title_from_heading=True).convert_text("# Tom & Jerry\n")
    assert "<title>Tom &amp; Jerry</title>" in named

    script = MarkdownConverter(title_from_heading=True).convert_text(
        "# Hello <script>alert(1)</script>\n"
    )
    assert "<title>Hello alert(1)</title>" in script

    fallback = MarkdownConverter(title_from_heading=True).convert_text("No heading\n")
    assert "<title>Document</title>" in fallback

    empty = MarkdownConverter(title="").convert_text("# Hello\n")
    assert "<title></title>" in empty


def test_convert_file(tmp_path):
    """Test file conversion."""
    input_file = tmp_path / "test.md"
    input_file.write_text("# Test\nHello World", encoding="utf-8")

    converter = MarkdownConverter()
    converter.convert_file(str(input_file), str(tmp_path / "test.html"))

    assert (tmp_path / "test.html").exists()
    written = (tmp_path / "test.html").read_text(encoding="utf-8")
    assert "<h1>Test</h1>" in written
    assert "<title>Document</title>" in written


def test_batch_skips_directories_and_reads_case_variants(tmp_path):
    (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "notes.md").mkdir()
    linked = tmp_path / "linked-dir"
    linked.mkdir()
    (linked / "keep.txt").write_text("keep", encoding="utf-8")
    (tmp_path / "skip.md").symlink_to(linked, target_is_directory=True)
    (tmp_path / "README.MD").write_text("# Readme\n", encoding="utf-8")
    (tmp_path / "notes.markdown").write_text("# Not markdown suffix\n", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "inner.md").write_text("# Inner\n", encoding="utf-8")

    out = tmp_path / "out"
    count = MarkdownConverter().convert_directory(tmp_path, out)

    assert count == 2
    assert "<h1>A</h1>" in (out / "a.html").read_text(encoding="utf-8")
    assert "<h1>Readme</h1>" in (out / "README.html").read_text(encoding="utf-8")
    assert not (out / "notes.html").exists()
    assert not (out / "skip.html").exists()
    assert not (out / "notes.markdown.html").exists()
    assert not (nested / "inner.html").exists()
    assert (linked / "keep.txt").read_text(encoding="utf-8") == "keep"
    assert not list(out.glob(".md-to-html-*"))


def _case_sensitive(directory):
    probe_dir = directory / "case-probe"
    probe_dir.mkdir()
    (probe_dir / "CaseProbe.md").write_text("a", encoding="utf-8")
    return not (probe_dir / "caseprobe.md").exists()


def test_batch_duplicate_output_names_write_nothing(tmp_path):
    if not _case_sensitive(tmp_path):
        pytest.skip("filesystem is case-insensitive")
    (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "a.MD").write_text("# Other\n", encoding="utf-8")
    out = tmp_path / "out"
    with pytest.raises(FileExistsError, match="Multiple Markdown files map to a.html"):
        MarkdownConverter().convert_directory(tmp_path, out)
    assert not out.exists()


def test_batch_titles_are_per_file(tmp_path):
    src = tmp_path / "in"
    src.mkdir()
    (src / "a.md").write_text("# Alpha\n", encoding="utf-8")
    (src / "b.md").write_text("No heading\n", encoding="utf-8")
    out = tmp_path / "out"
    assert MarkdownConverter(title_from_heading=True).convert_directory(src, out) == 2
    assert "<title>Alpha</title>" in (out / "a.html").read_text(encoding="utf-8")
    assert "<title>Document</title>" in (out / "b.html").read_text(encoding="utf-8")

    shared = tmp_path / "shared"
    MarkdownConverter(title="Site <docs>").convert_directory(src, shared)
    for name in ("a.html", "b.html"):
        text = (shared / name).read_text(encoding="utf-8")
        assert "<title>Site &lt;docs&gt;</title>" in text
