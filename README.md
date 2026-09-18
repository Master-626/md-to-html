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
