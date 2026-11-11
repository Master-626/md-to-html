import pytest
from click.testing import CliRunner

from md_to_html.cli import main


def test_help_lists_options():
    runner = CliRunner()
    for command in ("convert", "batch"):
        result = runner.invoke(main, [command, "--help"])
        assert result.exit_code == 0
        assert "--toc" in result.output
        assert "--no-highlight" in result.output
        assert "--title" in result.output
        assert "--title-from-heading" in result.output


def test_cli_title_from_heading(tmp_path):
    source = tmp_path / "note.md"
    source.write_text("# Héllo *there*\n", encoding="utf-8")
    target = tmp_path / "note.html"
    result = CliRunner().invoke(
        main,
        ["convert", "-i", str(source), "-o", str(target), "--title-from-heading", "--toc"],
    )
    assert result.exit_code == 0
    text = target.read_text(encoding="utf-8")
    assert "<title>Héllo there</title>" in text
    assert 'href="#héllo-there"' in text or 'href="#hello-there"' in text
    assert "Converted:" in result.output


def test_cli_explicit_title_on_stdout(tmp_path):
    source = tmp_path / "note.md"
    source.write_text("# Ignored\n", encoding="utf-8")
    result = CliRunner().invoke(
        main, ["convert", "-i", str(source), "--title", "Custom <T>"]
    )
    assert result.exit_code == 0
    assert "<title>Custom &lt;T&gt;</title>" in result.output
    assert not (tmp_path / "note.html").exists()


def test_cli_batch_title_and_no_highlight(tmp_path):
    src = tmp_path / "in"
    src.mkdir()
    (src / "a.md").write_text("# Alpha\n\n```python\nprint('hi')\n```\n", encoding="utf-8")
    (src / "b.MD").write_text("# Beta\n", encoding="utf-8")
    out = tmp_path / "out"
    result = CliRunner().invoke(
        main,
        [
            "batch",
            "-i",
            str(src),
            "-o",
            str(out),
            "--no-highlight",
            "--title-from-heading",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Converted 2 files" in result.output
    alpha = (out / "a.html").read_text(encoding="utf-8")
    assert "<title>Alpha</title>" in alpha
    assert "codehilite" not in alpha
    assert 'class="language-python"' in alpha
    assert "<title>Beta</title>" in (out / "b.html").read_text(encoding="utf-8")


def test_cli_batch_duplicate_names_are_a_clean_error(tmp_path):
    probe_dir = tmp_path / "case-probe"
    probe_dir.mkdir()
    (probe_dir / "CaseProbe.md").write_text("a", encoding="utf-8")
    if (probe_dir / "caseprobe.md").exists():
        pytest.skip("filesystem is case-insensitive")
    (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "a.MD").write_text("# Other\n", encoding="utf-8")
    out = tmp_path / "out"
    result = CliRunner().invoke(main, ["batch", "-i", str(tmp_path), "-o", str(out)])
    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "Multiple Markdown files" in result.output
    assert "Traceback" not in result.output
    assert not out.exists()
