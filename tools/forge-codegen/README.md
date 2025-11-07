# moku-instrument-forge-codegen

YAML→VHDL code generator for Moku custom instruments with type-safe register serialization.

## Overview

Automated code generation framework that transforms human-friendly YAML specifications into production-ready VHDL firmware for Moku FPGA platforms. Includes integrated type system with automatic register packing for 50-75% register space savings.

**Key features:**
- YAML → VHDL generation with Jinja2 templating
- Type-safe register serialization (23 built-in types)
- Automatic register packing algorithm
- Platform-agnostic (Go/Lab/Pro/Delta)
- Frozen VHDL type packages for stability

## Quick Start

```bash
# Installation (development mode)
cd moku-instrument-forge-codegen/
pip install -e .

# Generate VHDL from YAML spec
python -m forge_codegen.generator.codegen path/to/spec.yaml --output-dir generated/
```

For complete usage examples, type catalog, and generation patterns, see [llms.txt](llms.txt).

## Documentation

This project follows a **3-tier documentation system** optimized for progressive disclosure:

- **[llms.txt](llms.txt)** - Quick reference: Type catalog, generation workflow, common tasks
- **[CLAUDE.md](CLAUDE.md)** - Complete guide: Architecture, design rationale, adding new types
- **[docs/](docs/)** - Specialized guides: Getting started, troubleshooting, API reference

## Architecture

```
forge_codegen/
├── basic_serialized_datatypes/  # Type system & register packing (internal)
├── generator/                   # YAML → VHDL code generation
├── models/                      # Pydantic data models
├── templates/                   # Jinja2 VHDL templates
└── vhdl/                        # Frozen type packages (v1.0.0)
```

**Key concept:** `basic_serialized_datatypes` is an internal serialization engine (not a separate library). It provides the 23-type system and register packing algorithm used by the generator.

## Development Status

**Current (v1.0.0):**
- ✅ 23 types (voltage, time, boolean)
- ✅ Automatic register packing (50-75% savings)
- ✅ YAML → VHDL generation
- ✅ 69 test suite
- ✅ Frozen VHDL packages (stable)

**Planned:**
- Compound types (atomic multi-value updates)
- Enhanced error messages
- Interactive TUI for spec creation

## Integration

**Works with:**
- [moku-models](https://github.com/sealablab/moku-models) - Platform specifications (optional)
- [riscure-models](https://github.com/sealablab/riscure-models) - Probe specifications (optional)
- [forge-vhdl](https://github.com/sealablab/forge-vhdl) - Reusable VHDL components (optional)

**Part of:** [moku-instrument-forge-mono-repo](https://github.com/sealablab/moku-instrument-forge-mono-repo) ecosystem

## License

MIT

---

**Version:** 1.0.0 | **Last Updated:** 2025-11-04
