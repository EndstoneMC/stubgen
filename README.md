# StubGen

**endstone-stubgen** is a next-generation stub generator built with **Griffe** and **Jinja**, designed to produce
*precise* `.pyi` type stubs for large C++/pybind11 codebases, including the entire Endstone ecosystem.

This project replaces the legacy `pybind11-stubgen` workflow with a modern, modular, and more accurate architecture.

## Features

- **Griffe-based introspection**  
  Robust parsing of Python modules, pybind11 extensions, and custom metadata.

- **Jinja2 templating engine**  
  Clean, extensible rendering logic with fully customizable `.pyi` templates.

- **High-accuracy type inference**  
  Better handling of overloads, enums, default values, constructors, and pybind11-bound C++ types.

- **Designed for large codebases**  
  Incremental processing, stable output, and deterministic generation.

## Quick Start

Install:

```bash
pip install endstone-stubgen
````

Generate stubs for a module:

```bash
stubgen endstone
```

Specify output directory:

```bash
stubgen endstone --out stubs/
```

## Why This Exists

`pybind11-stubgen` was useful but increasingly brittle for producing accurate stubs for large C++ bindings.
This project introduces:

* A real AST model
* Deterministic rendering
* Stronger extension support
* Better handling of overloads and native enums
* A templated architecture you can extend safely

It is specifically built to support Endstone's pybind11 bindings, but works equally well for any project using pybind11.

