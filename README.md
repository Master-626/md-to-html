# md-to-html

## 简介

`md-to-html` 把 Markdown 转成带样式的独立 HTML，可作为命令行工具或 Python 库使用。

- 支持单个文件和目录批量转换。批量模式只处理当前目录中的 Markdown 文件，后缀 `.md` 不区分大小写，并且会跳过名为 `*.md` 的目录。
- `--toc` 会生成可点击的目录；正文里单独一段的 `[TOC]` 仍表示目录插入位置。
- 默认用 Pygments 为代码块着色，并把对应 CSS 写进 HTML。`--title` 和 `--title-from-heading` 用来设置网页标题。
- 已存在的输出文件、目录或链接不会被覆盖。

安装、全部选项、示例和测试方法见下面的英文说明。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

Convert Markdown into a self-contained HTML document. The result includes a small stylesheet, so it can be opened directly in a browser. Use it as the `md-to-html` / `md2html` commands, or call `MarkdownConverter` from Python.

## Installation

Python 3.8 or newer is required.

```bash
git clone https://github.com/Master-626/md-to-html.git
cd md-to-html
pip install .
```

Runtime dependencies are [click](https://click.palletsprojects.com/), [Python-Markdown](https://python-markdown.github.io/), and [Pygments](https://pygments.org/). Install the development extra to run the tests and the linter:

```bash
pip install -e ".[dev]"
```

## Command-line usage

Convert one file. Omit `-o` to print the HTML.

```bash
md-to-html convert -i README.md -o README.html
md-to-html convert -i README.md -o README.html --toc --title-from-heading
md-to-html convert -i notes.md --no-highlight --title "Notes"
```

`md2html` is the same program:

```bash
md2html convert -i README.md
```

Convert every top-level Markdown file in a directory. `docs/guide.md` becomes `site/guide.html`. Files in subdirectories are left alone.

```bash
md-to-html batch -i docs -o site --toc --title-from-heading
md-to-html batch -i docs -o site --no-highlight
```

### Options

| Option | Command | Description |
| --- | --- | --- |
| `-i`, `--input PATH` | `convert` | Input Markdown file. Required. |
| `-o`, `--output PATH` | `convert` | Output HTML file. Omit to write HTML to stdout. |
| `-i`, `--input-dir PATH` | `batch` | Directory to read. Required. |
| `-o`, `--output-dir PATH` | `batch` | Directory to write. Required. Created when a file is written. |
| `--toc` | both | Add heading ids and a table of contents. |
| `--no-highlight` | both | Leave fenced code as a plain `<pre><code>` block. |
| `--title TEXT` | both | HTML `<title>`. Default: `Document`. Overrides `--title-from-heading`. |
| `--title-from-heading` | both | Use the first level-1 heading as `<title>` when `--title` is omitted. |
| `--version` | top-level | Print the package version. |
| `--help` | any | Show help. |

`convert -i` reads the file as UTF-8. A missing file, a directory, or text that is not UTF-8 is an error. The command exits non-zero and does not print a traceback for those failures.

### Table of contents

`--toc` gives each heading an `id` and inserts a linked list. Without a `[TOC]` paragraph, the list is placed at the top of the document. A paragraph whose only text is `[TOC]` is replaced where it stands and is not repeated. `[TOC]` inside a code span or code fence stays as text, and the contents list is still added at the top. Documents with no headings do not get an empty list.

Heading ids follow Python-Markdown's usual ASCII slugs, so `Héllo` is still `hello`. A heading that would otherwise get an empty id, such as `你好`, keeps a Unicode id instead of `_1`.

### Syntax highlighting

Fenced code blocks are highlighted with Pygments through Python-Markdown's `codehilite` extension. The matching CSS is embedded in the page, so colors work when the file is opened by itself. `--no-highlight` keeps the `language-...` class and does not add the highlighter stylesheet. Inline `` `code` `` is not highlighted.

### Document title

The default `<title>` is `Document`, including when the page has a heading. `--title` sets that text and escapes `<`, `>`, and `&`. `--title-from-heading` uses the plain text of the first `<h1>` (markup is removed). If the document has no level-1 heading, the title stays `Document`. In a batch, each file is titled from its own first heading.

### Other markup

Python-Markdown's `extra` and `sane_lists` extensions are always on, so tables, fenced code, footnotes, and definition lists are available. Tables, blockquotes, and images get a few layout rules: tables have borders, blockquotes have a left bar, and images stay within the page width.

## Python API

```python
from md_to_html import MarkdownConverter

converter = MarkdownConverter(
    enable_toc=True,
    enable_code_highlight=True,
    title_from_heading=True,
)

html = converter.convert_text("# Hello\n\n```python\nprint('hi')\n```\n")
converter.convert_file("README.md", "README.html")
written = converter.convert_directory("docs", "site")
```

`convert_text` and `convert_file` return the HTML string. `convert_file` writes a file only when an output path is given. `convert_directory` returns how many files were converted.

`title` sets the document title. `None` means `Document`, unless `title_from_heading=True` and the body has a level-1 heading. `title=""` produces an empty `<title>`.

`theme` is accepted for compatibility and does not change the stylesheet. The built-in stylesheet is the one shown above.

## Output safety

Output files must be new. The API raises `FileExistsError` for any existing output entry, including a directory, symlink (even dangling), or hard link. The CLI reports the error and exits nonzero. This also prevents accidentally replacing the Markdown source. Choose a different output name, or move an existing output aside yourself before converting again. Omitting the output path still returns HTML through the API and prints HTML through the CLI.

Each output is fully written to a temporary file beside its destination, then published with an atomic, no-replacement hard link. Temporary files are cleaned up on ordinary failures. Creation permissions honor the process umask. The filesystem must support hard links; unsupported filesystems fail safely rather than falling back to an overwrite-prone operation. A process crash can leave a temporary file. This is not a durability guarantee (files are not fsynced), or a sandbox against an adversary replacing parent directories during conversion.

Batch conversion checks all known output collisions before writing, then converts matching files in sorted order. A file matches when its suffix is `.md` in any letter case (`README.MD` included). Directories and links to directories are skipped, even when the name ends in `.md`. Other suffixes, including `.markdown`, are not converted, and subdirectories are not walked. If two files would publish the same HTML name (`a.md` and `a.MD` both become `a.html` on a case-sensitive filesystem), the batch raises `FileExistsError` before creating any output. Invalid input directories raise `NotADirectoryError`. Batches are not transactions: a later conversion failure or concurrent collision leaves earlier new outputs intact, but never overwrites the conflicting entry. Empty input directories produce zero files and do not create the output directory.

## Running tests

```bash
pip install -e ".[dev]"
python -m ruff check .
python -m pytest
```

GitHub Actions runs Ruff and pytest on Python 3.8 through 3.14 on Linux, and on Python 3.13 on Windows and macOS. A separate job installs the minimum declared versions (`click==8.0.0`, `markdown==3.5`, `pygments==2.14.0`, `pytest==7.0.0`) and runs the tests. Another job builds the sdist and wheel and checks both console scripts. These are the configured jobs, not a claim that unpublished changes passed hosted CI.

## License

MIT License. Copyright (c) 2026 Xu Jiaqi.
