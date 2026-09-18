"""
CLI interface for md-to-html.
"""

import click
from pathlib import Path

from .converter import MarkdownConverter


@click.group()
@click.version_option()
def main():
    """md-to-html - Markdown to HTML converter with TOC and batch support."""
    pass


@main.command()
@click.option("-i", "--input", required=True, help="Input Markdown file")
@click.option("-o", "--output", help="Output HTML file")
@click.option("--toc", is_flag=True, help="Generate table of contents")
@click.option("--no-highlight", is_flag=True, help="Disable code syntax highlighting")
def convert(input, output, toc, no_highlight):
    """Convert a single Markdown file to HTML."""
    converter = MarkdownConverter(
        enable_toc=toc,
        enable_code_highlight=not no_highlight,
    )

    html = converter.convert_file(input, output)

    if output:
        click.echo(f"✅ Converted: {input} -> {output}")
    else:
        click.echo(html)


@main.command()
@click.option("-i", "--input-dir", required=True, help="Input directory with Markdown files")
@click.option("-o", "--output-dir", required=True, help="Output directory for HTML files")
@click.option("--toc", is_flag=True, help="Generate table of contents")
def batch(input_dir, output_dir, toc):
    """Batch convert all Markdown files in a directory."""
    converter = MarkdownConverter(enable_toc=toc)
    count = converter.convert_directory(input_dir, output_dir)
    click.echo(f"✅ Converted {count} files -> {output_dir}")


if __name__ == "__main__":
    main()
