# moku-instrument-forge-vhdl

Shared VHDL utilities for Moku custom instrument development using the forge framework.

## Overview

This library provides reusable VHDL components for building custom instruments on the Moku platform:

- **Packages** - Common data types, constants, and utilities (including voltage domain packages)
- **Debugging** - FSM observer for hardware debugging
- **Loader** - BRAM initialization utilities
- **Utilities** - Clock dividers, triggers, and other helpers

### Documentation

This project uses a **3-tier documentation system** optimized for AI agents and developers:
- **llms.txt** - Quick reference (~500 tokens): Component catalog, testing commands
- **CLAUDE.md** - Authoritative guide (~3.5k tokens): Complete testing standards, design patterns, coding standards
- **Source code** - Implementation details with inline documentation

See `CLAUDE.md` for comprehensive CocoTB progressive testing standards and VHDL coding guidelines.

## Repository Structure

```
moku-instrument-forge-vhdl/
├── vhdl/
│   ├── packages/           # VHDL packages
│   │   ├── forge_common_pkg.vhd
│   │   ├── forge_lut_pkg.vhd
│   │   ├── forge_voltage_3v3_pkg.vhd
│   │   ├── forge_voltage_5v0_pkg.vhd
│   │   └── forge_voltage_5v_bipolar_pkg.vhd
│   ├── debugging/          # Debug utilities
│   │   └── fsm_observer.vhd
│   ├── loader/             # Data loading utilities
│   │   └── forge_bram_loader.vhd
│   └── utilities/          # Generic utilities
│       ├── forge_util_clk_divider.vhd
│       └── forge_voltage_threshold_trigger_core.vhd
├── tests/                  # CocotB tests for utilities
└── README.md
```

## Usage

This library is typically used as a git submodule in projects like `moku-instrument-forge-mono-repo`:

```bash
# Add as submodule
git submodule add https://github.com/sealablab/moku-instrument-forge-vhdl.git libs/forge-vhdl

# Initialize submodule
git submodule update --init --recursive
```

## Components

### Packages

**Voltage Domain Packages (forge_voltage_*):**
- **forge_voltage_3v3_pkg** - 0-3.3V unipolar (TTL, GPIO, digital logic)
- **forge_voltage_5v0_pkg** - 0-5.0V unipolar (sensor supply, unipolar analog)
- **forge_voltage_5v_bipolar_pkg** - ±5.0V bipolar (Moku DAC/ADC, AC signals)

**Utility Packages:**
- **forge_common_pkg** - Common types and constants for Moku development
- **forge_lut_pkg** - Look-up table utilities (with CocoTB tests)

### Debugging

**fsm_observer** - Real-time FSM state observation via output registers
- Exports FSM state to Moku registers for oscilloscope debugging
- Enables hardware validation without simulation
- See `.claude/commands/debug.md` for usage patterns

### Loader

**forge_bram_loader** - BRAM initialization from external sources

### Utilities

**forge_util_clk_divider** - Programmable clock divider (with CocoTB tests)
**forge_voltage_threshold_trigger_core** - Voltage threshold detection

## Development

### Requirements

- GHDL (VHDL compiler)
- CocotB (for testing)
- Python 3.10+ with uv

### Running Tests

This library uses **CocoTB progressive testing** with GHDL output filtering for LLM-optimized output:

```bash
# Install dependencies
uv sync

# Run P1 tests (default, <20 lines output)
uv run python tests/run.py forge_util_clk_divider

# Run P2 tests (comprehensive validation)
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py forge_util_clk_divider

# List all available tests
uv run python tests/run.py --list

# Run all tests
uv run python tests/run.py --all
```

**Key Innovation:** 98% test output reduction (287 lines → 8 lines) through progressive test levels (P1/P2/P3/P4) and intelligent GHDL filtering. See `CLAUDE.md` for complete testing standards.

## Integration with Forge

This library is designed to work alongside `moku-instrument-forge`:

- **forge** generates probe interface code (shim + main template)
- **forge-vhdl** provides reusable utilities for implementing custom logic
- Together they provide a complete development environment

## Version History

**v2.1.0** - Complete forge-vhdl Unification (2025-11-04)
- Complete volo→forge namespace migration (5 components renamed)
- Intentional removal of legacy volo_voltage_pkg (fail-fast design)
- 3-tier documentation system (llms.txt, CLAUDE.md)
- Production-ready voltage type system (3v3, 5v0, 5v_bipolar)
- CocoTB progressive testing with 98% output reduction

**v1.0.0** - Initial release
- Extracted from EZ-EMFI project
- Includes forge utilities and fsm_observer
- CocotB test infrastructure

## License

MIT License - See LICENSE file

## Contributing

This library is part of the Moku custom instrument ecosystem. When adding new utilities:

1. Add VHDL source to appropriate `vhdl/` subdirectory
2. Add CocotB tests to `tests/`
3. Update this README
4. Document usage patterns in `.claude/commands/`

## Related Projects

- [moku-instrument-forge](https://github.com/sealablab/moku-instrument-forge) - Code generation framework
- [moku-instrument-forge-mono-repo](https://github.com/sealablab/moku-instrument-forge-mono-repo) - Example monorepo structure
- [moku-models](https://github.com/sealablab/moku-models) - Platform data models

## 🤖 AI Agent Integration

This repository implements a **3-tier documentation system** optimized for token efficiency:

- **Tier 1 (llms.txt)** - Quick reference (~500 tokens): Component catalog, testing commands, basic usage
- **Tier 2 (CLAUDE.md)** - Authoritative guide (~3.5k tokens): Complete testing standards, CocoTB progressive testing, VHDL coding standards, design patterns
- **Tier 3 (Source code)** - Implementation details: VHDL source with inline documentation, CocoTB tests

**Testing Innovation:** Progressive test levels (P1/P2/P3/P4) with GHDL output filtering achieve 98% output reduction, enabling rapid LLM-assisted VHDL development.

---

**Last Updated:** 2025-11-04
