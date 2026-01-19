# endstone-stubgen

[![PyPI version](https://img.shields.io/pypi/v/endstone-stubgen.svg)](https://pypi.org/project/endstone-stubgen/)
[![Python versions](https://img.shields.io/pypi/pyversions/endstone-stubgen.svg)](https://pypi.org/project/endstone-stubgen/)
[![License](https://img.shields.io/pypi/l/endstone-stubgen.svg)](https://github.com/EndstoneMC/stubgen/blob/main/LICENSE)
[![CI](https://github.com/EndstoneMC/stubgen/actions/workflows/ci.yml/badge.svg)](https://github.com/EndstoneMC/stubgen/actions/workflows/ci.yml)

A next-generation stub generator for pybind11 modules, built with [Griffe](https://github.com/mkdocstrings/griffe)
and [Jinja2](https://jinja.palletsprojects.com/).

## Overview

**endstone-stubgen** generates precise `.pyi` type stubs for C++/pybind11 codebases. It replaces the legacy
`pybind11-stubgen` workflow with a modern, modular, and more accurate architecture.

Originally built to support [Endstone](https://github.com/EndstoneMC/endstone)'s pybind11 bindings, it works equally
well for any pybind11 project.

## Features

- **Griffe-based introspection** — Robust parsing of Python modules, pybind11 extensions, and custom metadata
- **Jinja2 templating** — Clean, extensible rendering with fully customizable `.pyi` templates
- **High-accuracy type inference** — Better handling of overloads, enums, default values, and pybind11-bound C++ types
- **Deterministic output** — Stable, reproducible stub generation for large codebases
- **PEP 561 compliant** — Generated stubs work seamlessly with mypy, pyright, and other type checkers

## Installation

```bash
pip install endstone-stubgen
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add endstone-stubgen
```

## Usage

### Basic Usage

Generate stubs for a module:

```bash
stubgen <module_name>
```

### Specify Output Directory

```bash
stubgen <module_name> -o stubs/
```

### Dry Run

Parse the module and report errors without writing files:

```bash
stubgen <module_name> --dry-run
```

### CLI Reference

```
usage: stubgen [-h] [-o OUTPUT_DIR] [--dry-run] MODULE_NAME

positional arguments:
  MODULE_NAME           Module name to generate stubs for

options:
  -h, --help            Show this help message and exit
  -o, --output-dir      The root directory for output stubs (default: current directory)
  --dry-run             Parse module and report errors without writing stubs
```

## Example

Generate stubs for the `endstone` module:

```bash
stubgen endstone -o stubs/
```

This creates a `stubs/` directory with `.pyi` files mirroring the module structure:

```
stubs/
└── endstone/
    ├── __init__.pyi
    ├── command.pyi
    ├── event.pyi
    └── ...
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
