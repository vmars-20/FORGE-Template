# CLAUDE.md

## Project Overview

**riscure-models** is a standalone Pydantic library defining type-safe data models for Riscure FI/SCA probe specifications and integration with Moku platforms.

**Purpose**: Hardware specification models that enable voltage-safe wiring validation between Moku platforms and Riscure probes:
- **Probe Specifications**: Electrical characteristics of Riscure FI/SCA probes
- **Voltage Validation**: Safety checking before physical connections
- **Moku Integration**: Compatible with moku-models for cross-platform validation

**Part of:** [moku-instrument-forge-mono-repo](https://github.com/sealablab/moku-instrument-forge-mono-repo) (monorepo orchestrator)
**Used by:** [moku-instrument-forge](https://github.com/sealablab/moku-instrument-forge) (forge code generation)

**Design Mirror**: Follows moku-models architecture patterns for consistency

---

## Quick Start

```bash
# Install (development mode)
cd riscure-models/
uv pip install -e .

# Format code
black riscure_models/
ruff check riscure_models/
```

---

## Core Models

### `DS1120APlatform` - Primary Probe Model
Complete electrical specification for DS1120A high-power EM-FI probe:
- **Signal ports**: digital_glitch, pulse_amplitude, coil_current (SMA, 50Ω)
- **Power port**: 24-450V DC external PSU input
- **Probe tips**: Interchangeable 1.5mm/4mm variants
- **Timing**: Fixed 50ns pulse, ~40ns propagation delay

**Use this for wiring validation with Moku platforms**.

### `SignalPort`
Port specification with voltage safety validation:
- `port_id`: Port identifier (e.g., 'digital_glitch')
- `direction`: 'input' or 'output'
- `voltage_min` / `voltage_max`: Safe operating voltage range
- `impedance`: Port impedance (e.g., '50Ohm')
- `coupling`: 'DC' or 'AC'
- `signal_type`: 'digital', 'analog', 'monitor', 'power'

**Key Method**: `is_voltage_compatible(voltage: float) -> bool`

### `ProbeTip`
Interchangeable probe tip specification:
- `tip_id`: Identifier (e.g., '4mm_positive')
- `diameter_mm`: Physical tip size
- `polarity`: Magnetic polarity variant
- `max_current_a`: Maximum coil current rating

**Note**: Tip selection affects field strength but NOT electrical interface.

---

## File Structure

```
riscure_models/
├── __init__.py              # Public API exports
└── probes/
    ├── __init__.py
    ├── ds1120a.py          # DS1120APlatform, SignalPort, ProbeTip
    └── ds1121a.py          # (Future) DS1121A bidirectional probe
```

---

## Usage Examples

### Basic Probe Specification Query
```python
from riscure_models import DS1120A_PLATFORM

probe = DS1120A_PLATFORM

# Query port specifications
trigger = probe.get_port_by_id('digital_glitch')
print(f"{trigger.port_id}: {trigger.get_voltage_range_str()}")
# Output: "digital_glitch: 0.0V to 3.3V"

# Check voltage safety
safe = trigger.is_voltage_compatible(3.3)  # True
unsafe = trigger.is_voltage_compatible(5.0)  # False

# List all input ports
for port in probe.get_input_ports():
    print(f"{port.port_id} ({port.signal_type}): {port.impedance}")
```

### Probe Tip Selection
```python
from riscure_models import DS1120A_PLATFORM

probe = DS1120A_PLATFORM

# Query available tips
for tip in probe.available_tips:
    print(f"{tip.tip_id}: {tip.diameter_mm}mm, {tip.max_current_a}A max")

# Select specific tip for deployment
tip = probe.get_tip_by_id('4mm_positive')
print(f"Using {tip.tip_id} with {tip.max_current_a}A capability")
```

### Integration with Moku Platform
```python
from moku_models import MOKU_GO_PLATFORM
from riscure_models import DS1120A_PLATFORM

moku = MOKU_GO_PLATFORM
probe = DS1120A_PLATFORM

# Get corresponding ports
moku_output = moku.get_analog_output_by_id('OUT1')
probe_input = probe.get_port_by_id('digital_glitch')

# Manual voltage validation (automated validation coming soon)
print(f"Moku OUT1: {moku_output.voltage_range_vpp}Vpp")
print(f"Probe digital_glitch: {probe_input.get_voltage_range_str()}")

# Check Moku TTL output (3.3V) against probe input
if probe_input.is_voltage_compatible(3.3):
    print("✓ Safe to connect Moku OUT1 (TTL) → DS1120A digital_glitch")
```

---

## Design Principles

1. **Voltage Safety First**: Explicit voltage_min/voltage_max for safety validation
2. **Moku Integration**: Mirror moku-models patterns for seamless compatibility
3. **Pure Specifications**: No control logic, just validated hardware specs
4. **Extensible**: Template for DS1121A, laser probes, and future devices

---

## Integration with Sibling Libraries

### With moku-models

**Use case:** Voltage safety validation before physical wiring

```python
from moku_models import MOKU_GO_PLATFORM
from riscure_models import DS1120A_PLATFORM

# Get Moku platform output specifications
moku = MOKU_GO_PLATFORM
moku_output = moku.get_analog_output_by_id('OUT1')
# → Can output ±5V analog or 3.3V TTL

# Get probe input specifications
probe = DS1120A_PLATFORM
probe_input = probe.get_port_by_id('digital_glitch')
# → voltage_min=0V, voltage_max=3.3V (TTL input only)

# Validate: Moku TTL output compatible with probe input
ttl_voltage = 3.3
if probe_input.is_voltage_compatible(ttl_voltage):
    print("✓ Safe: Moku:Go OUT1 (TTL) → DS1120A digital_glitch")
else:
    raise ValueError("⚠ Unsafe voltage for probe input!")

# WARNING: Direct analog output (±5V) would damage probe!
if not probe_input.is_voltage_compatible(5.0):
    print("⚠ NEVER connect Moku OUT1 (analog) directly to digital_glitch!")
```

**Integration point:** Deployment tools perform this validation automatically before suggesting wire connections.

**Critical safety check:** Always validate voltage ranges to prevent probe damage (DS1120A digital inputs are NOT 5V tolerant).

### With basic-app-datatypes

**Use case:** Type compatibility with probe specifications

```python
from basic_app_datatypes import BasicAppDataTypes, TYPE_REGISTRY
from riscure_models import DS1120A_PLATFORM

# User specifies output voltage type for probe driver
output_type = BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
metadata = TYPE_REGISTRY[output_type]
# → voltage_range: "±5V"

# Check probe input requirements
probe = DS1120A_PLATFORM
trigger_port = probe.get_port_by_id('digital_glitch')
# → voltage_min=0V, voltage_max=3.3V (TTL only)

# Validate: ±5V type range exceeds probe input limit
# Need to ensure Moku output configured for TTL mode, not raw DAC
if trigger_port.is_voltage_compatible(3.3):
    print("✓ Compatible if Moku output uses TTL mode")
    print("⚠ Configure Moku OUT1 for TTL, not analog ±5V!")
```

**Integration point:** forge generator can cross-check output types against probe input requirements during YAML validation.

---

## Common Tasks

### Add New Probe Model
1. Create `riscure_models/probes/ds1121a.py`
2. Define `DS1121APlatform(BaseModel)` with appropriate signal ports
3. Export `DS1121A_PLATFORM` constant
4. Add to `probes/__init__.py` and main `__init__.py`

### Validate Wiring Connection
```python
from riscure_models import DS1120A_PLATFORM

probe = DS1120A_PLATFORM
port = probe.get_port_by_id('digital_glitch')

# Check if voltage is safe
moku_ttl_voltage = 3.3
if not port.is_voltage_compatible(moku_ttl_voltage):
    raise ValueError(f"Unsafe voltage {moku_ttl_voltage}V for {port.port_id}")
```

---

## Integration with forge Code Generation

**Import alongside moku-models in forge generators**:
```python
from moku_models import MokuConfig, MOKU_GO_PLATFORM
from riscure_models import DS1120A_PLATFORM
```

**Use cases:**
- Validate Moku output voltage ranges against probe input requirements
- Generate wiring diagrams with correct port connections
- Document probe specifications in deployment configs
- Safety checking before hardware connection

---

## Development Workflow

```bash
# Make changes to models
vim riscure_models/probes/ds1120a.py

# Validate
ruff check riscure_models/

# Format
black riscure_models/

# Commit
git add riscure_models/
git commit -m "Add DS1120A voltage validation"
```

---

## Supported Probes

| Probe | Status | Pulse Width | Max Voltage | Max Current | Type |
|-------|--------|-------------|-------------|-------------|------|
| DS1120A | ✅ Implemented | 50ns (fixed) | 450V | 64A | Unidirectional |
| DS1121A | 🚧 Planned | 4-200ns | 100V | TBD | Bidirectional |
| Laser probes | 🚧 Future | Variable | TBD | N/A | Optical FI |

---

## DS1120A Port Reference

### Input Ports (Driven by Moku/Controller)

| Port ID | Voltage Range | Impedance | Type | Description |
|---------|---------------|-----------|------|-------------|
| `digital_glitch` | 0-3.3V | 50Ω | Digital | Rising edge trigger |
| `pulse_amplitude` | 0-3.3V | 50Ω | Analog | Linear power control (5-100%) |
| `power_24vdc` | 24-450V | N/A | Power | External high-voltage PSU |

### Output Ports (Read by Moku/Scope)

| Port ID | Voltage Range | Impedance | Coupling | Description |
|---------|---------------|-----------|----------|-------------|
| `coil_current` | -1.4V to 0V | 50Ω | AC | Real-time coil current monitor |

**Typical Wiring**:
```
[Moku OUT1] → [digital_glitch] → [DS1120A] → [Target DUT]
[Moku OUT2] → [pulse_amplitude] ↗
[Moku IN1]  ← [coil_current]   ↙
[External PSU] → [power_24vdc] ↗
```

---

## Future Enhancements

- [ ] DS1121A bidirectional probe model
- [ ] Laser probe models (LS1110A, etc.)
- [ ] Automated cross-validation with moku-models
- [ ] Wiring diagram SVG generation
- [ ] Probe calibration data models
- [ ] PyPI package publication

---

**Last Updated**: 2025-11-03
**Maintainer**: Sealab Team
**License**: MIT
