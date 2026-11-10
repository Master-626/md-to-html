# md-to-html

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

A Markdown to HTML converter with batch support, table of contents generation, and syntax highlighting.

## 🌟 Features

- 📝 **Single File** - Convert individual Markdown files to HTML
- 📁 **Batch Mode** - Convert entire directories of Markdown files
- 📑 **TOC Generation** - Automatically generate table of contents
- 🎨 **Code Highlighting** - Syntax highlighting for code blocks
- 🎨 **Styled Output** - Clean, responsive HTML output with built-in CSS
- 🐍 **Python API** - Use as a library in your code

## 📦 Installation

```bash
git clone https://github.com/Master-626/md-to-html.git
cd md-to-html
pip install .
```

## 🚀 Usage

### Convert Single File
```bash
# Basic conversion
md-to-html convert -i README.md -o README.html

# With table of contents
md-to-html convert -i README.md -o README.html --toc

# Without code highlighting
md-to-html convert -i README.md -o README.html --no-highlight
```

### Batch Convert Directory
```bash
# Convert all .md files in docs/ to HTML in output/
md-to-html batch -i docs/ -o output/ --toc
```

## 🐍 Python API

```python
from md_to_html import MarkdownConverter

# Create converter with options
converter = MarkdownConverter(
    enable_toc=True,
    enable_code_highlight=True,
)

# Convert text
html = converter.convert_text("# Hello\nWorld")

# Convert file
converter.convert_file("input.md", "output.html")

# Batch convert
count = converter.convert_directory("docs/", "output/")
```

## 🧪 Testing

```bash
pip install -e ".[dev]"
pytest
```

## 📄 License

MIT License

## Output safety

Output files must be new. The API raises `FileExistsError` for any existing
output entry, including a directory, symlink (even dangling), or hard link.
The CLI reports the error and exits nonzero. This also prevents accidentally
replacing the Markdown source. Choose a different output name, or move an
existing output aside yourself before converting again. Omitting the output
path still returns HTML through the API and prints HTML through the CLI.

Each output is fully written to a temporary file beside its destination, then
published with an atomic, no-replacement hard link. Temporary files are cleaned
up on ordinary failures. Creation permissions honor the process umask. The
filesystem must support hard links; unsupported filesystems fail safely rather
than falling back to an overwrite-prone operation. A process crash can leave a
temporary file. This is not a durability guarantee (files are not fsynced), or
a sandbox against an adversary replacing parent directories during conversion.

Batch conversion checks all known output collisions before writing, then
converts top-level `*.md` files in sorted order. Invalid input directories raise
`NotADirectoryError`. Batches are not transactions: a later conversion failure
or concurrent collision leaves earlier new outputs intact, but never overwrites
the conflicting entry. Empty input directories produce zero files.

CI covers Python 3.8–3.14 on Linux, plus Python 3.13 on Windows and macOS,
minimum runtime dependencies, distribution builds and both CLI entry points.
These are configured jobs, not a claim that unpublished changes passed hosted CI.
