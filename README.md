# endstone-stubgen

[![PyPI version](https://img.shields.io/pypi/v/endstone-stubgen.svg)](https://pypi.org/project/endstone-stubgen/)
[![Python versions](https://img.shields.io/pypi/pyversions/endstone-stubgen.svg)](https://pypi.org/project/endstone-stubgen/)
[![License](https://img.shields.io/pypi/l/endstone-stubgen.svg)](https://github.com/EndstoneMC/stubgen/blob/main/LICENSE)
[![Build](https://github.com/EndstoneMC/stubgen/actions/workflows/ci.yml/badge.svg)](https://github.com/EndstoneMC/stubgen/actions/workflows/ci.yml)

A stub generator for pybind11 modules, built with [Griffe](https://github.com/mkdocstrings/griffe)
and [Jinja2](https://jinja.palletsprojects.com/).

Generates precise `.pyi` type stubs for C++/pybind11 codebases. Originally built to support
[Endstone](https://github.com/EndstoneMC/endstone)'s pybind11 bindings, it works equally well
for any pybind11 project.

## Features

- Griffe-based introspection for robust parsing of pybind11 extensions
- Jinja2 templating with fully customizable `.pyi` templates
- Accurate handling of overloads, enums, default values, and pybind11-bound C++ types
- Deterministic, reproducible output for large codebases
- PEP 561 compliant (works with mypy, pyright, and other type checkers)

## Installation

```bash
pip install endstone-stubgen
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add endstone-stubgen
```

## Usage

Generate stubs for a module:

```bash
stubgen <module_name>
```

Specify an output directory:

```bash
stubgen <module_name> -o stubs/
```

Dry run (parse and report errors without writing files):

```bash
stubgen <module_name> --dry-run
```

## Example

```bash
stubgen endstone -o stubs/
```

Produces:

```
stubs/
  endstone/
    __init__.pyi
    command.pyi
    event.pyi
    ...
```

## Development

```bash
git clone https://github.com/EndstoneMC/stubgen.git
cd stubgen
uv sync
uv run ruff check src/
```

## Releasing

1. Add changes under `## [Unreleased]` in `CHANGELOG.md`
2. Go to **Actions > Release > Run workflow**
3. Enter the version (e.g. `0.2.0`) and run

The workflow validates the version, updates pyproject.toml and CHANGELOG.md, creates a git tag
and GitHub release, builds, publishes to PyPI, and attaches artifacts.

Use **dry run** to preview without making changes.

## License

[MIT License](LICENSE)