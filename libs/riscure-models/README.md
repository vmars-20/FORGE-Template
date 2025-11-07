# riscure-models

Pydantic models for Riscure FI/SCA probe specifications and Moku integration.

## Overview

Type-safe data models for Riscure electromagnetic fault injection (EM-FI) and side-channel analysis (SCA) probes, enabling voltage-safe wiring validation with Moku platforms.

**Key features:**
- Electrical specifications for Riscure probes (ports, voltage ranges, impedances)
- Voltage compatibility checking before hardware connection
- Seamless integration with moku-models

## Supported Probes

- **DS1120A**: High-power unidirectional EM-FI probe (450V, 64A, fixed 50ns pulse) - ✅ Implemented
- **DS1121A**: Bidirectional EM-FI probe with sensing capability - 🚧 Planned

## Quick Start

```bash
# Installation (development mode)
cd riscure-models/
uv pip install -e .
```

```python
from riscure_models import DS1120A_PLATFORM

# Load probe specification
probe = DS1120A_PLATFORM

# Check port specs
trigger = probe.get_port_by_id('digital_glitch')
print(f"Trigger: {trigger.get_voltage_range_str()}")  # "0.0V to 3.3V"
```

For complete usage examples, port specifications, and integration patterns, see [llms.txt](llms.txt).

## Documentation

This library follows a **3-tier documentation system** optimized for progressive disclosure:

- **[llms.txt](llms.txt)** - Quick reference: Probe specs, port specifications, usage examples
- **[CLAUDE.md](CLAUDE.md)** - Complete guide: Design patterns, safety validation, integration with sibling libraries
- **Source code** - Implementation details with inline documentation

## Development Status

**Current (v0.1.0):**
- ✅ DS1120A complete electrical specification
- ✅ Port-level voltage compatibility validation
- ✅ Integration patterns with moku-models

**Planned:**
- DS1121A bidirectional probe support
- Cross-platform automated validation
- Wiring diagram generation

## Integration

**Works with:**
- [moku-models](https://github.com/sealablab/moku-models) - Platform specifications for voltage compatibility
- [basic-app-datatypes](https://github.com/sealablab/basic-app-datatypes) - Type system integration

**Part of:** [moku-instrument-forge](https://github.com/sealablab/moku-instrument-forge) ecosystem

## License

MIT

---

**Version:** 0.1.0 | **Last Updated:** 2025-11-04
