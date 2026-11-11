"""
CLI interface for md-to-html.
"""

import click

from .converter import MarkdownConverter


def _make_converter(toc, no_highlight, title, title_from_heading):
    return MarkdownConverter(
        enable_toc=toc,
        enable_code_highlight=not no_highlight,
        title=title,
        title_from_heading=title_from_heading,
    )


@click.group()
@click.version_option()
def main():
    """md-to-html - Markdown to HTML converter with TOC and batch support."""


@main.command()
@click.option("-i", "--input", required=True, help="Input Markdown file")
@click.option("-o", "--output", help="Output HTML file")
@click.option("--toc", is_flag=True, help="Generate table of contents")
@click.option("--no-highlight", is_flag=True, help="Disable code syntax highlighting")
@click.option("--title", default=None, help='HTML document title. Default: "Document".')
@click.option(
    "--title-from-heading",
    is_flag=True,
    help="Use the first heading as the title when --title is omitted.",
)
def convert(input, output, toc, no_highlight, title, title_from_heading):
    """Convert a single Markdown file to HTML."""
    converter = _make_converter(toc, no_highlight, title, title_from_heading)

    try:
        html = converter.convert_file(input, output)
    except (OSError, UnicodeError) as exc:
        raise click.ClickException(str(exc)) from exc

    if output:
        click.echo(f"✅ Converted: {input} -> {output}")
    else:
        click.echo(html)


@main.command()
@click.option("-i", "--input-dir", required=True, help="Input directory with Markdown files")
@click.option("-o", "--output-dir", required=True, help="Output directory for HTML files")
@click.option("--toc", is_flag=True, help="Generate table of contents")
@click.option("--no-highlight", is_flag=True, help="Disable code syntax highlighting")
@click.option("--title", default=None, help='HTML document title. Default: "Document".')
@click.option(
    "--title-from-heading",
    is_flag=True,
    help="Use the first heading as the title when --title is omitted.",
)
def batch(input_dir, output_dir, toc, no_highlight, title, title_from_heading):
    """Batch convert Markdown files in a directory."""
    converter = _make_converter(toc, no_highlight, title, title_from_heading)
    try:
        count = converter.convert_directory(input_dir, output_dir)
    except (OSError, UnicodeError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"✅ Converted {count} files -> {output_dir}")


if __name__ == "__main__":
    main()
