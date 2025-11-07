# moku-models

Pydantic models for Moku device deployment, discovery, and configuration.

## Overview

Type-safe data models for Moku platform specifications, deployment configurations, and signal routing.

**Key features:**
- Single source of truth for platform specs (simulation AND hardware)
- Type-safe deployment configurations with Pydantic validation
- Signal routing validation for MCC (Moku Multi-instrument Connection)
- Platform models: Moku:Go, Moku:Lab, Moku:Pro, Moku:Delta

## Supported Platforms

| Platform | Slots | I/O | Clock | DIO | Status |
|----------|-------|-----|-------|-----|--------|
| Go | 2 | 2×2 | 125 MHz | 16 pins | ✅ |
| Lab | 2 | 2×2 | 500 MHz | None | ✅ |
| Pro | 4 | 4×4 | 1.25 GHz | None | ✅ |
| Delta | 3 | 8×8 | 5 GHz | 32 pins | ✅ |

## Quick Start

```bash
# Installation (development mode)
cd moku-models/
uv pip install -e .
```

```python
from moku_models import MokuConfig, SlotConfig, MokuConnection, MOKU_GO_PLATFORM

# Create deployment configuration
config = MokuConfig(
    platform=MOKU_GO_PLATFORM,
    slots={
        1: SlotConfig(instrument='CloudCompile', bitstream='path.tar'),
        2: SlotConfig(instrument='Oscilloscope', settings={'sample_rate': 125e6})
    },
    routing=[
        MokuConnection(source='IN1', destination='Slot1InA'),
        MokuConnection(source='Slot1OutA', destination='OUT1')
    ]
)
```

For complete usage examples, platform specifications, and routing patterns, see [llms.txt](llms.txt).

## Documentation

This library follows a **3-tier documentation system** optimized for progressive disclosure:

- **[llms.txt](llms.txt)** - Quick reference: Platform specs, deployment API, routing patterns
- **[CLAUDE.md](CLAUDE.md)** - Complete guide: Design patterns, integration with sibling libraries, development workflow
- **[docs/](docs/)** - Specialized references: Platform specifications (with datasheet links), routing patterns

## Development Status

**Current:**
- ✅ All 4 Moku platforms (Go, Lab, Pro, Delta)
- ✅ Complete platform specifications from datasheets
- ✅ MokuConfig deployment abstraction
- ✅ Routing validation

**Planned:**
- Instrument-specific configuration models
- Enhanced cross-platform validation

## Integration

**Works with:**
- [basic-app-datatypes](https://github.com/sealablab/basic-app-datatypes) - Voltage type validation
- [riscure-models](https://github.com/sealablab/riscure-models) - Platform-to-probe safety validation

**Used by:** [moku-instrument-forge](https://github.com/sealablab/moku-instrument-forge) (deployment), CocotB testbenches (simulation)

**Part of:** [moku-instrument-forge-mono-repo](https://github.com/sealablab/moku-instrument-forge-mono-repo) ecosystem

## License

MIT

---

**Version:** Current | **Last Updated:** 2025-11-04
