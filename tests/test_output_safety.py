import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from md_to_html import MarkdownConverter
from md_to_html.cli import main


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "source.md"
    path.write_text("# Héllo\n", encoding="utf-8")
    return path


def assert_no_temporary_files(path):
    assert not list(path.glob(".md-to-html-*"))


def test_returns_html_without_writing(source):
    before = sorted(source.parent.iterdir())
    assert "Héllo" in MarkdownConverter().convert_file(source)
    assert sorted(source.parent.iterdir()) == before


def test_nested_output_and_utf8(source):
    target = source.parent / "nested" / "out.html"
    html = MarkdownConverter().convert_file(source, target)
    assert target.read_text(encoding="utf-8") == html
    assert_no_temporary_files(target.parent)


@pytest.mark.parametrize("kind", ["file", "directory", "self", "symlink", "dangling", "hardlink"])
def test_refuses_existing_paths(source, kind):
    target = source.parent / "target"
    if kind == "file":
        target.write_bytes(b"keep me")
    elif kind == "directory":
        target.mkdir()
    elif kind == "self":
        target = source
    elif kind == "symlink":
        target.symlink_to(source)
    elif kind == "dangling":
        target.symlink_to(source.parent / "absent")
    else:
        os.link(str(source), str(target))
    with pytest.raises(FileExistsError):
        MarkdownConverter().convert_file(source, target)
    assert source.read_text(encoding="utf-8") == "# Héllo\n"
    if kind == "file":
        assert target.read_bytes() == b"keep me"
    if kind in ("symlink", "dangling"):
        assert target.is_symlink()
    assert_no_temporary_files(source.parent)


def test_parent_symlink_alias(source):
    alias = source.parent / "alias"
    alias.symlink_to(source.parent, target_is_directory=True)
    with pytest.raises(FileExistsError):
        MarkdownConverter().convert_file(source, alias / source.name)
    assert source.read_text(encoding="utf-8") == "# Héllo\n"


@pytest.mark.parametrize("kind", ["file", "symlink", "hardlink"])
def test_late_output_creation_never_clobbers(source, monkeypatch, kind):
    target = source.with_suffix(".html")
    original_link = os.link

    def race(src, dst):
        if kind == "file":
            Path(dst).write_bytes(b"concurrent writer")
        elif kind == "symlink":
            Path(dst).symlink_to(source)
        else:
            original_link(str(source), dst)
        original_link(src, dst)

    monkeypatch.setattr(os, "link", race)
    with pytest.raises(FileExistsError):
        MarkdownConverter().convert_file(source, target)
    assert source.read_text(encoding="utf-8") == "# Héllo\n"
    assert target.read_bytes() == (b"concurrent writer" if kind == "file" else source.read_bytes())
    assert_no_temporary_files(source.parent)


def test_publish_failure_cleans_temporary(source, monkeypatch):
    target = source.with_suffix(".html")

    def fail(*args):
        raise OSError("hard links unavailable")

    monkeypatch.setattr(os, "link", fail)
    with pytest.raises(OSError, match="hard links unavailable"):
        MarkdownConverter().convert_file(source, target)
    assert not target.exists()
    assert_no_temporary_files(source.parent)


def test_failed_render_does_not_create_output(source, monkeypatch):
    target = source.with_suffix(".html")

    def fail(*args):
        raise ValueError("render failed")

    converter = MarkdownConverter()
    monkeypatch.setattr(converter, "convert_text", fail)
    with pytest.raises(ValueError, match="render failed"):
        converter.convert_file(source, target)
    assert not target.exists()


def test_failed_encoding_does_not_publish(source, monkeypatch):
    converter = MarkdownConverter()
    monkeypatch.setattr(converter, "convert_text", lambda _: "\ud800")
    with pytest.raises(UnicodeError):
        converter.convert_file(source, source.with_suffix(".html"))
    assert not source.with_suffix(".html").exists()
    assert_no_temporary_files(source.parent)


@pytest.mark.parametrize("kind", ["file", "symlink", "dangling", "hardlink", "directory"])
def test_batch_preflights_later_collision(tmp_path, kind):
    inputs = tmp_path / "in"
    inputs.mkdir()
    for name in ["a.md", "z.md"]:
        (inputs / name).write_text("# original", encoding="utf-8")
    outputs = tmp_path / "out"
    outputs.mkdir()
    target = outputs / "z.html"
    if kind == "file":
        target.write_bytes(b"keep")
    elif kind == "directory":
        target.mkdir()
    elif kind == "hardlink":
        os.link(str(inputs / "z.md"), str(target))
    else:
        target.symlink_to(inputs / ("z.md" if kind == "symlink" else "absent"))
    with pytest.raises(FileExistsError):
        MarkdownConverter().convert_directory(inputs, outputs)
    assert not (outputs / "a.html").exists()
    assert (inputs / "z.md").read_text(encoding="utf-8") == "# original"
    assert os.path.lexists(str(target))


def test_batch_late_collision_preserves_existing_and_source(tmp_path, monkeypatch):
    for name in ["a.md", "z.md"]:
        (tmp_path / name).write_text("# original", encoding="utf-8")
    output = tmp_path / "out"
    original_link = os.link

    def race(src, dst):
        if Path(dst).name == "z.html":
            original_link(str(tmp_path / "z.md"), dst)
        original_link(src, dst)

    monkeypatch.setattr(os, "link", race)
    with pytest.raises(FileExistsError):
        MarkdownConverter().convert_directory(tmp_path, output)
    assert (output / "a.html").exists()  # Earlier results are deliberately retained.
    assert (output / "z.html").read_text(encoding="utf-8") == "# original"
    assert (tmp_path / "z.md").read_text(encoding="utf-8") == "# original"
    assert_no_temporary_files(output)


def test_batch_same_directory_and_nonrecursive(tmp_path):
    (tmp_path / "one.md").write_text("# One", encoding="utf-8")
    (tmp_path / "other.txt").write_text("unchanged", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "two.md").write_text("# Two", encoding="utf-8")
    assert MarkdownConverter().convert_directory(tmp_path, tmp_path) == 1
    assert (tmp_path / "one.md").read_text(encoding="utf-8") == "# One"
    assert not (nested / "two.html").exists()


def test_empty_batch_does_not_create_output(tmp_path):
    assert MarkdownConverter().convert_directory(tmp_path, tmp_path / "out") == 0
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("kind", ["missing", "file"])
def test_invalid_input_directory(tmp_path, kind):
    source = tmp_path / "input"
    if kind == "file":
        source.touch()
    with pytest.raises(NotADirectoryError):
        MarkdownConverter().convert_directory(source, tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("command", ["convert", "batch"])
def test_cli_collision_is_clean_error(source, command):
    target = source.with_suffix(".html")
    target.write_bytes(b"keep")
    args = (["convert", "-i", str(source), "-o", str(target)] if command == "convert"
            else ["batch", "-i", str(source.parent), "-o", str(source.parent)])
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "Converted" not in result.output
    assert "Traceback" not in result.output
    assert target.read_bytes() == b"keep"


def test_cli_stdout(source):
    result = CliRunner().invoke(main, ["convert", "-i", str(source)])
    assert result.exit_code == 0
    assert "<!DOCTYPE html>" in result.output
    assert not source.with_suffix(".html").exists()


def test_cli_success(source):
    target = source.with_suffix(".html")
    result = CliRunner().invoke(main, ["convert", "-i", str(source), "-o", str(target)])
    assert result.exit_code == 0
    assert "Converted:" in result.output
    assert "Héllo" in target.read_text(encoding="utf-8")


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits and umask")
@pytest.mark.parametrize("mask", [0o022, 0o077])
def test_output_permissions_respect_umask(source, mask):
    import stat
    old_mask = os.umask(mask)
    try:
        target = source.with_suffix(".html")
        MarkdownConverter().convert_file(source, target)
    finally:
        os.umask(old_mask)
    assert stat.S_IMODE(target.stat().st_mode) == (0o666 & ~mask)
