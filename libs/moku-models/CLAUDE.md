# CLAUDE.md

## Project Overview

**moku-models** is a standalone Pydantic library defining type-safe data models for Moku device deployment and configuration.

**Purpose**: Single source of truth for Moku platform specifications that works across multiple contexts:
- **Hardware Deployment**: Real Moku devices via MCC API
- **CocotB Simulation**: Behavioral instrument models in test environments
- **YAML Configuration**: Human-friendly deployment specs

**Part of:** [moku-instrument-forge-mono-repo](https://github.com/sealablab/moku-instrument-forge-mono-repo) (monorepo orchestrator)
**Used by:** [moku-instrument-forge](https://github.com/sealablab/moku-instrument-forge) (forge code generation)

**Platform Specifications**: See `docs/MOKU_PLATFORM_SPECIFICATIONS.md` for detailed hardware specs and datasheet references

---

## Quick Start

```bash
# Install (development mode from parent project)
cd moku-models/
uv pip install -e .

# Format code
black moku_models/
ruff check moku_models/
```

---

## Core Models

### `MokuConfig` - THE Central Abstraction
Multi-instrument deployment specification:
- **Platform**: Which hardware (Go/Lab/Pro)
- **Slots**: What instruments go where (slot number → SlotConfig)
- **Routing**: How signals flow between slots and physical ports
- **Metadata**: Test campaign info, version tags, etc.

**Use this for all deployments** (hardware and simulation).

### `SlotConfig`
Per-slot instrument configuration:
- `instrument`: Type name ('CloudCompile', 'Oscilloscope', etc.)
- `bitstream`: Path to `.tar` bitstream (CloudCompile only)
- `control_registers`: CR0-CR31 initial values (CloudCompile only)
- `settings`: Instrument-specific settings dict

### `MokuConnection`
Signal routing between:
- Physical ports: `IN1`, `IN2`, `OUT1`, `OUT2` (4 max)
- Slot virtual ports: `Slot1InA`, `Slot2OutB`, etc.

### Platform Models
Physical hardware specifications:
- `MokuGoPlatform`: 2 slots, 2 analog I/O, 125 MHz
- `MokuLabPlatform`: 2 slots, 2 analog I/O, 500 MHz (Note: Lab only supports 2 slots despite having 4 I/O)
- `MokuProPlatform`: 4 slots, 4 analog I/O, 1.25 GHz
- `MokuDeltaPlatform`: 3 slots, 8 analog I/O, 5 GHz (flagship platform)

Each platform defines:
- Analog I/O specs (BNC connectors)
- Digital I/O (optional, varies by platform)
- Slot count
- Clock characteristics

---

## File Structure

```
moku_models/
├── __init__.py              # Public API exports
├── moku_config.py           # MokuConfig, SlotConfig
├── routing.py               # MokuConnection, MokuConnectionList
├── discovery.py             # MokuDeviceInfo, MokuDeviceCache
└── platforms/
    ├── __init__.py
    ├── moku_go.py           # MokuGoPlatform, MOKU_GO_PLATFORM
    ├── moku_lab.py          # MokuLabPlatform, MOKU_LAB_PLATFORM
    └── moku_pro.py          # MokuProPlatform, MOKU_PRO_PLATFORM
```

---

## Usage Examples

### Basic Deployment Config (Moku:Go)
```python
from moku_models import MokuConfig, SlotConfig, MokuConnection, MOKU_GO_PLATFORM

config = MokuConfig(
    platform=MOKU_GO_PLATFORM,
    slots={
        1: SlotConfig(
            instrument='CloudCompile',
            bitstream='emfi_probe.tar',
            control_registers={0: 0xE0000000}  # Enable probe
        ),
        2: SlotConfig(
            instrument='Oscilloscope',
            settings={'sample_rate': 125e6}
        )
    },
    routing=[
        MokuConnection(source='IN1', destination='Slot1InA'),
        MokuConnection(source='Slot1OutA', destination='OUT1'),
        MokuConnection(source='Slot1OutA', destination='Slot2InA')
    ]
)

# Validate before deployment
errors = config.validate_routing()
if errors:
    print(f"Validation errors: {errors}")
```

### Multi-Slot Config (Moku:Lab)
```python
from moku_models import MOKU_LAB_PLATFORM

config = MokuConfig(
    platform=MOKU_LAB_PLATFORM,  # 4 slots available
    slots={
        1: SlotConfig(instrument='WaveformGenerator'),
        2: SlotConfig(instrument='CloudCompile', bitstream='custom.tar'),
        3: SlotConfig(instrument='Oscilloscope'),
        4: SlotConfig(instrument='SpectrumAnalyzer')
    },
    routing=[
        MokuConnection(source='Slot1OutA', destination='Slot2InA'),
        MokuConnection(source='Slot2OutA', destination='Slot3InA'),
        MokuConnection(source='Slot2OutB', destination='OUT1')
    ]
)
```

### Platform Queries
```python
from moku_models import MOKU_GO_PLATFORM, MOKU_LAB_PLATFORM, MOKU_PRO_PLATFORM

# Compare platforms
for platform in [MOKU_GO_PLATFORM, MOKU_LAB_PLATFORM, MOKU_PRO_PLATFORM]:
    print(f"{platform.name}: {platform.slots} slots @ {platform.clock_mhz} MHz")

# Check port specs
in1 = MOKU_GO_PLATFORM.get_analog_input_by_id('IN1')
print(f"IN1: {in1.resolution_bits}-bit @ {in1.sample_rate_msa} MSa/s")
```

---

## Design Principles

1. **Type Safety**: Pydantic validation catches config errors before deployment
2. **Moku API Alignment**: Port naming matches 1st-party `moku` library conventions
3. **Platform Agnostic**: Same `MokuConfig` works for Go/Lab/Pro (different platform instances)
4. **Simulation-Ready**: CocotB tests use identical configs as hardware deployment
5. **Pure Data Models**: No deployment logic, just validated data structures

---

## Integration with Sibling Libraries

### With basic-app-datatypes

**Use case:** Platform-aware voltage type validation

```python
from basic_app_datatypes import BasicAppDataTypes, TYPE_REGISTRY
from moku_models import MOKU_GO_PLATFORM

# Get type metadata
voltage_type = BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
metadata = TYPE_REGISTRY[voltage_type]
# → voltage_range: "±5V"

# Get platform DAC output specs
platform = MOKU_GO_PLATFORM
dac_output = platform.get_analog_output_by_id('OUT1')
# → voltage_range_vpp: 10.0 (±5V)

# Cross-validate: voltage type compatible with platform
assert metadata.voltage_range == "±5V"
assert dac_output.voltage_range_vpp == 10.0
print("✓ VOLTAGE_OUTPUT_05V_S16 compatible with Moku:Go OUT1")
```

**Integration point:** forge generator uses both libraries to validate YAML specs against platform hardware constraints.

### With riscure-models

**Use case:** Probe input voltage safety validation

```python
from moku_models import MOKU_GO_PLATFORM
from riscure_models import DS1120A_PLATFORM

# Get Moku output specification
moku = MOKU_GO_PLATFORM
moku_out = moku.get_analog_output_by_id('OUT1')
# → voltage_range_vpp = 10.0 (±5V), can output 0-3.3V in TTL mode

# Get probe input specification
probe = DS1120A_PLATFORM
probe_in = probe.get_port_by_id('digital_glitch')
# → voltage_min=0V, voltage_max=3.3V (TTL input)

# Validate: Moku TTL output (3.3V) within probe input range (0-3.3V)
ttl_voltage = 3.3
if probe_in.is_voltage_compatible(ttl_voltage):
    print("✓ Safe connection: Moku:Go OUT1 (TTL) → DS1120A digital_glitch")
else:
    print("⚠ Voltage incompatibility detected!")
```

**Integration point:** Deployment validation checks voltage safety before suggesting physical wire connections.

**Safety principle:** Always validate Moku output voltages against probe input limits to prevent hardware damage.

---

## Common Tasks

### Add New Platform
1. Create `moku_models/platforms/moku_xxx.py`
2. Define `MokuXxxPlatform(BaseModel)` with appropriate specs
3. Export `MOKU_XXX_PLATFORM` constant
4. Add to `platforms/__init__.py` and main `__init__.py`

### Export to YAML
```python
import yaml
config_dict = config.to_dict()
with open('deployment.yaml', 'w') as f:
    yaml.dump(config_dict, f, default_flow_style=False)
```

### Load from YAML
```python
import yaml
from moku_models import MokuConfig

with open('deployment.yaml', 'r') as f:
    data = yaml.safe_load(f)
config = MokuConfig.from_dict(data)
```

---

## Integration with forge Code Generation

**Import in forge generators and parent monorepo:**
```python
from moku_models import MokuConfig, MOKU_GO_PLATFORM
```

**Use cases:**
- VHDL build scripts query platform specs (clock frequency, I/O count)
- CocotB tests import `MokuConfig` for behavioral models
- Python TUI apps use `MokuConnection` for routing visualization
- forge code generation uses platform specs for validation

**Git Submodule Workflow:**
```bash
# From forge/libs/moku-models (nested submodule)
cd forge/libs/moku-models/
git checkout -b add-feature
# Make changes
git commit -m "Add feature"
git push origin add-feature

# Update parent forge to use new commit
cd ../..
git add libs/moku-models/
git commit -m "Update moku-models submodule"
```

---

## Development Workflow

```bash
# Make changes to models
vim moku_models/moku_config.py

# Validate
ruff check moku_models/

# Format
black moku_models/

# Commit (in submodule)
git add moku_models/
git commit -m "Add validation for routing cycles"
```

---

## Available Platforms

| Platform | Slots | Analog I/O | Clock | DIO Pins | Constant |
|----------|-------|------------|-------|----------|----------|
| Moku:Go | 2 | 2 IN / 2 OUT | 125 MHz | 16 | `MOKU_GO_PLATFORM` |
| Moku:Lab | 2 | 2 IN / 2 OUT | 500 MHz | None | `MOKU_LAB_PLATFORM` |
| Moku:Pro | 4 | 4 IN / 4 OUT | 1.25 GHz | None | `MOKU_PRO_PLATFORM` |
| Moku:Delta | 3 | 8 IN / 8 OUT | 5 GHz | 32 (2×16) | `MOKU_DELTA_PLATFORM` |

**Notes**:
- Lab/Pro do NOT have DIO headers (only Go and Delta)
- Delta has 2 separate 16-pin DIO headers (32 pins total)
- Delta specs shown are for 3-slot standard mode (8-slot advanced mode available but not modeled)

---

**Last Updated**: 2025-01-28
**Maintainer**: Sealab Team
**License**: MIT
