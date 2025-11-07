# User Guide: moku-instrument-forge

**Comprehensive reference for forge workflows**

**Audience:** Users who completed [Getting Started](getting_started.md) and want deeper knowledge

---

## Table of Contents

1. [Overview](#overview)
2. [Workflow](#workflow)
3. [YAML Specification](#yaml-specification)
4. [Type System](#type-system)
5. [Register Mapping](#register-mapping)
6. [Code Generation](#code-generation)
7. [Deployment](#deployment)
8. [Python Control](#python-control)
9. [Best Practices](#best-practices)
10. [Common Patterns](#common-patterns)

---

## Overview

**moku-instrument-forge** transforms YAML instrument specifications into deployment-ready VHDL packages for Moku platforms. The toolchain handles:

- ✅ **Validation:** YAML syntax, type checking, range validation
- ✅ **Register Mapping:** Automatic packing (50-75% savings)
- ✅ **Code Generation:** VHDL shim + template, manifest.json, control_registers.json
- ✅ **Type Safety:** 25 predefined types with converters
- ✅ **Multi-Platform:** Go (125 MHz), Lab (125 MHz), Pro (1 GHz), Delta (5 GHz)

**Design Philosophy:**
- **Type-safe:** Prevent runtime errors with compile-time validation
- **Efficient:** Maximize register utilization automatically
- **Simple:** YAML in, VHDL out, no intermediate steps
- **Maintainable:** Regenerate from YAML, never edit generated code

---

## Workflow

```
┌─────────────┐
│ YAML Spec   │  (Your instrument definition)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Validate   │  (Syntax, types, ranges)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Generate  │  (VHDL + manifest.json)
└──────┬──────┘
       │
       ├─────► manifest.json           (Deployment metadata)
       ├─────► control_registers.json  (Register mapping)
       ├─────► *_shim.vhd              (Control register interface)
       └─────► *_main.vhd              (Instrument logic template)

       ▼
┌─────────────┐
│   Deploy    │  (CloudCompile → Moku FPGA)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Control   │  (Python/C++ control software)
└─────────────┘
```

**Key Principle:** `manifest.json` is the **source of truth** for deployment. Downstream tools (deployment, docgen, control software) read manifest.json, NOT the YAML.

See [Architecture Overview](../architecture/overview.md) for system design.

---

## YAML Specification

### Basic Structure

```yaml
app_name: my_instrument        # Required: snake_case
version: 1.0.0                 # Required: semantic versioning
description: Brief description # Required: human-readable
platform: moku_go              # Required: go/lab/pro/delta

datatypes:                     # Required: array of signals
  - name: signal_name          # Required: snake_case
    datatype: type_name        # Required: from BasicAppDataTypes
    description: What it does  # Required: human-readable
    default_value: 0           # Required: must be in range
    units: V                   # Optional: display units
    display_name: Voltage      # Optional: UI label
    min_value: -5.0            # Optional: runtime constraint
    max_value: 5.0             # Optional: runtime constraint

mapping_strategy: type_clustering  # Optional: first_fit/best_fit/type_clustering
```

### Field Details

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `app_name` | string | ✅ | Instrument name (snake_case, alphanumeric + underscore) |
| `version` | string | ✅ | Semantic version (major.minor.patch) |
| `description` | string | ✅ | Brief description for users |
| `platform` | string | ✅ | Target hardware: `moku_go`, `moku_lab`, `moku_pro`, `moku_delta` |
| `datatypes` | array | ✅ | List of control signals (see below) |
| `mapping_strategy` | string | ❌ | Packing strategy (default: `type_clustering`) |

### Datatype Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Signal name (snake_case, unique within spec) |
| `datatype` | string | ✅ | Type from BasicAppDataTypes (25 types available) |
| `description` | string | ✅ | Human-readable explanation |
| `default_value` | number | ✅ | Initial value (must be within type range) |
| `units` | string | ❌ | Display units (V, mV, ms, µs, cycles, etc.) |
| `display_name` | string | ❌ | UI-friendly label (defaults to name) |
| `min_value` | number | ❌ | Runtime minimum (validation constraint) |
| `max_value` | number | ❌ | Runtime maximum (validation constraint) |

**See:** [YAML Schema Reference](../reference/yaml_schema.md) for complete specification.

---

## Type System

### Overview

**BasicAppDataTypes** provides 25 fixed-width types across 3 categories:

**Voltage (12 types):**
- Output ranges: ±5V, ±2.5V, ±1V, ±0.5V
- Input ranges: ±10V, ±5V
- Encodings: 16-bit signed, millivolts, raw ADC/DAC codes

**Time (12 types):**
- Units: milliseconds, microseconds, nanoseconds, cycles
- Widths: 8-bit, 16-bit, 32-bit
- Signed/unsigned variants

**Boolean (1 type):**
- 1-bit flag (0/1)

### Quick Reference

| Type | Bits | Range | Use Case |
|------|------|-------|----------|
| `voltage_output_05v_s16` | 16 | ±5V | DAC output (scaled) |
| `voltage_signed_s16` | 16 | ±32767 | Generic voltage (unscaled) |
| `voltage_millivolts_s16` | 16 | ±32767 mV | Millivolt precision |
| `pulse_duration_ms_u16` | 16 | 0-65535 ms | Durations (ms) |
| `pulse_duration_us_u32` | 32 | 0-4294967295 µs | Durations (µs) |
| `pulse_duration_ns_u8` | 8 | 0-255 ns | Short delays |
| `boolean` | 1 | true/false | Flags, enables |

**See:** [Type System Reference](../reference/type_system.md) for all 25 types.

**Authoritative Source:** [`libs/basic-app-datatypes/llms.txt`](../../libs/basic-app-datatypes/llms.txt)

### Type Selection Guidelines

**Voltage:**
- Use `voltage_output_*` for DAC outputs (physical units)
- Use `voltage_signed_*` for ADC inputs or generic values
- Use `voltage_millivolts_*` for millivolt-level precision
- Match range to your hardware (±5V most common)

**Time:**
- Use `pulse_duration_ms_*` for human-scale timing (delays, timeouts)
- Use `pulse_duration_us_*` for fast control loops
- Use `pulse_duration_ns_*` for FPGA-scale timing (settling times, delays)
- Choose bit width based on max value needed

**Boolean:**
- Use `boolean` for all flags (enables, triggers, mode switches)

### Platform Compatibility

All 25 types work on **all 4 platforms** (Go, Lab, Pro, Delta). The type system is platform-agnostic.

**Platform differences:**
- **Clock frequency** (injected into VHDL automatically)
- **Available I/O** (DACs, ADCs, digital I/O)
- **MCC routing** (see [Routing Patterns](../../libs/moku-models/docs/routing_patterns.md))

---

## Register Mapping

### Control Registers

**Moku platforms provide:**
- **10 control registers** (CR6-CR15)
- **32 bits per register**
- **320 bits total**

**Mapping challenge:** Pack variable-width signals (1-32 bits) into 32-bit registers efficiently.

### Mapping Strategies

**1. `first_fit` (Naive)**
- Assign each signal to the first register with space
- Fast but inefficient
- Example: 3×16-bit signals → 3 registers (50% efficient)

**2. `best_fit` (Optimized)**
- Assign each signal to the register with the smallest remaining space
- Better packing, slower
- Example: 3×16-bit signals → 2 registers (75% efficient)

**3. `type_clustering` (Default, Recommended)**
- Group signals by bit width before packing
- Best balance of speed and efficiency
- Example: 3×16-bit signals → 2 registers (75% efficient with clustering)

**See:** [Register Mapping Algorithms](../reference/register_mapping.md) for detailed comparison with visual examples.

### Efficiency Metrics

**manifest.json includes:**

```json
"efficiency": {
  "total_bits_used": 33,
  "total_bits_allocated": 64,
  "percentage": 0.52,
  "registers_used": 2,
  "registers_saved": 1
}
```

**Typical savings:** 50-75% compared to "one signal per register" approach.

### Manual Override

To force a specific strategy:

```yaml
app_name: my_instrument
# ... other fields ...
mapping_strategy: best_fit  # Override default (type_clustering)
```

**When to override:**
- `first_fit`: Never recommended (testing only)
- `best_fit`: Maximum packing density needed
- `type_clustering`: Default (recommended for most cases)

---

## Code Generation

### Pipeline Overview

```
YAML → Pydantic Validation → Register Mapper → Template Engine → VHDL + JSON
```

**Steps:**

1. **Parse YAML:** Load and validate syntax
2. **Pydantic Validation:** Type checking, range validation, platform validation
3. **Register Mapping:** Run packing algorithm (first_fit/best_fit/type_clustering)
4. **Template Rendering:** Jinja2 templates generate VHDL
5. **Manifest Generation:** Create manifest.json and control_registers.json
6. **Write Outputs:** Save files to `output/<app_name>/`

**See:** [VHDL Generation Pipeline](../reference/vhdl_generation.md) for internals.

### Generated Files

**1. `manifest.json`**
- Deployment metadata (app_name, version, platform)
- Signal definitions with register mappings
- Efficiency metrics
- **Used by:** deployment-context, docgen-context, control software

**2. `control_registers.json`**
- Register-centric view of mappings
- Bit ranges for each signal in each register
- **Used by:** Debugging, visualization tools

**3. `<app_name>_shim.vhd`**
- VHDL entity that unpacks control registers
- Converts CR6-CR15 → typed signals
- **DO NOT EDIT:** Regenerated from YAML

**4. `<app_name>_main.vhd`**
- Template for your instrument logic
- Includes typed signals from shim
- **EDIT THIS:** Implement your algorithm

### Command-Line Usage

```bash
# Validate only
uv run python -m forge.validate_yaml specs/my_instrument.yaml

# Generate package
uv run python -m forge.generate_package specs/my_instrument.yaml

# Custom output directory
uv run python -m forge.generate_package specs/my_instrument.yaml --output-dir custom/path/

# Verbose output
uv run python -m forge.generate_package specs/my_instrument.yaml --verbose
```

### Agent Commands (Alternative)

If using the Claude Code agent system:

```bash
/validate specs/my_instrument.yaml
/generate specs/my_instrument.yaml
/map-registers specs/my_instrument.yaml  # Show mapping without generating
```

**See:** [Agent System](../architecture/agent_system.md) for agent-based workflows.

---

## Deployment

**Note:** Automated deployment requires CloudCompile integration (work in progress).

### Conceptual Workflow

1. **Generate Package** (forge)
   ```bash
   uv run python -m forge.generate_package specs/my_instrument.yaml
   ```

2. **Upload to CloudCompile** (manual for now)
   - Upload `*_shim.vhd` and `*_main.vhd`
   - Select platform (Go/Lab/Pro/Delta)
   - CloudCompile synthesizes → bitstream

3. **Deploy to Moku** (moku-python or desktop app)
   ```python
   from moku.instruments import CustomInstrument
   instr = CustomInstrument('192.168.1.100')
   instr.deploy_bitstream('path/to/bitstream.bit', 'my_instrument')
   ```

4. **Initialize Registers** (from manifest.json)
   ```python
   import json
   with open('output/my_instrument/manifest.json') as f:
       manifest = json.load(f)

   for signal in manifest['datatypes']:
       instr.set_control_register(
           signal['register_number'],
           signal['default_value']
       )
   ```

**See:** [Deployment Guide](deployment_guide.md) for detailed workflow (when available).

---

## Python Control

### Reading Registers

```python
from moku.instruments import CustomInstrument

# Connect to deployed instrument
instr = CustomInstrument('192.168.1.100', 'my_instrument')

# Read control register (returns 32-bit unsigned)
cr6_value = instr.get_control_register(6)

# Decode using manifest.json
import json
with open('output/my_instrument/manifest.json') as f:
    manifest = json.load(f)

# Find signal in CR6, bits 15:0
# Convert raw bits → physical units (voltage, time, etc.)
```

### Writing Registers

```python
# Write physical value (voltage in volts)
voltage_v = 2.5  # 2.5V

# Convert using BasicAppDataTypes converter
from forge.types.converters import TypeConverter
converter = TypeConverter()

# Get type metadata
from forge.types.registry import TYPE_REGISTRY
voltage_type = TYPE_REGISTRY.get_type('voltage_output_05v_s16')

# Convert physical → raw bits
raw_value = converter.physical_to_raw(2.5, voltage_type)

# Pack into CR6 (assuming bits 15:0)
cr6_value = raw_value & 0xFFFF  # Extract 16 bits

# Write to Moku
instr.set_control_register(6, cr6_value)
```

### Helper Functions (Future)

The `docgen-context` agent can auto-generate high-level Python APIs:

```python
# Auto-generated from manifest.json
class MyInstrumentAPI:
    def set_output_voltage(self, volts: float):
        """Set output voltage in volts (±5V range)"""
        # Handles conversion + register packing internally

    def get_output_voltage(self) -> float:
        """Read output voltage in volts"""
        # Handles register read + conversion
```

**See:** [Python API Reference](../reference/python_api.md) for Pydantic model details.

---

## Best Practices

### Naming Conventions

**YAML:**
- `app_name`: `snake_case` (e.g., `em_probe_controller`)
- `signal names`: `snake_case` (e.g., `output_voltage`, `enable_dac`)
- Avoid abbreviations unless universally known (e.g., `dac` ok, `opv` bad)

**VHDL:**
- Signals: `snake_case` (auto-generated from YAML)
- Entities: `<app_name>_shim`, `<app_name>_main`

**Python:**
- Classes: `PascalCase` (e.g., `BasicAppsRegPackage`)
- Functions: `snake_case` (e.g., `generate_package`)

### Type Selection

**Choose the narrowest type that fits your range:**

| Need | Type | Rationale |
|------|------|-----------|
| ±5V output | `voltage_output_05v_s16` | Matches DAC range exactly |
| 0-1000 ms delay | `pulse_duration_ms_u16` | Fits in 16 bits (max 65535) |
| Enable flag | `boolean` | 1 bit, not 8 or 16 |

**Avoid:**
- Using 32-bit types when 16-bit suffices (wastes registers)
- Using signed types for inherently unsigned values (time durations)

### Safety Constraints

**Use `min_value` and `max_value` for runtime validation:**

```yaml
- name: output_voltage
  datatype: voltage_output_05v_s16
  default_value: 0
  min_value: -3.0    # Hardware limit: ±3V, not ±5V
  max_value: 3.0
```

**This prevents:**
- Out-of-range values in control software
- Hardware damage from excessive voltages
- Timing violations (e.g., pulses too short)

### Default Values

**Always provide safe defaults:**

```yaml
- name: enable_high_voltage
  datatype: boolean
  default_value: false  # OFF by default (safe)
```

**Never:**
- Default to maximum voltage/current
- Default to enabled for dangerous features
- Omit default_value (required field)

### Register Optimization

**Tips for maximizing efficiency:**

1. **Group similar widths:** Place 16-bit signals together, 8-bit together
2. **Use boolean:** 1-bit flags (most efficient)
3. **Check efficiency:** Aim for >50% in manifest.json
4. **Avoid waste:** If you need 0-100, use u8 (not u16)

**Example:**

```yaml
# Inefficient (4 registers, 33 bits used / 128 allocated = 26%)
- name: voltage_a
  datatype: voltage_output_05v_s16  # 16 bits
- name: voltage_b
  datatype: voltage_output_05v_s16  # 16 bits
- name: enable
  datatype: boolean                  # 1 bit

# Efficient (2 registers, 33 bits used / 64 allocated = 52%)
# (Same signals, type_clustering packs voltage_a + voltage_b in CR6)
```

---

## Common Patterns

### FSM Control Signals

**Pattern:** Group FSM state and control flags together

```yaml
- name: fsm_state
  datatype: pulse_duration_ns_u8  # Repurpose: 8 bits = 256 states
  description: Current FSM state
  default_value: 0  # IDLE state

- name: fsm_trigger
  datatype: boolean
  description: Trigger FSM transition
  default_value: false

- name: fsm_reset
  datatype: boolean
  description: Reset FSM to IDLE
  default_value: false
```

**See:** [FSM Observer Pattern](../debugging/fsm_observer_pattern.md) for debugging FSMs.

### Voltage Parameters

**Pattern:** Separate output setpoints from input thresholds

```yaml
# DAC output
- name: output_voltage
  datatype: voltage_output_05v_s16
  description: DAC output voltage
  default_value: 0
  units: V

# ADC threshold
- name: trigger_threshold
  datatype: voltage_signed_s16
  description: ADC trigger threshold
  default_value: 1000  # Raw ADC counts
```

### Timing Configuration

**Pattern:** Use appropriate time units for each use case

```yaml
# Long delays (human-scale)
- name: pulse_duration
  datatype: pulse_duration_ms_u16
  description: Pulse duration
  default_value: 100
  units: ms

# Short delays (FPGA-scale)
- name: settling_time
  datatype: pulse_duration_ns_u8
  description: ADC settling time in nanoseconds
  default_value: 10
  units: ns
```

### Multi-Channel Control

**Pattern:** Use suffixes for channel indexing

```yaml
- name: voltage_ch1
  datatype: voltage_output_05v_s16
  default_value: 0

- name: voltage_ch2
  datatype: voltage_output_05v_s16
  default_value: 0

- name: enable_ch1
  datatype: boolean
  default_value: false

- name: enable_ch2
  datatype: boolean
  default_value: false
```

**See:** [Multi-Channel Walkthrough](../examples/multi_channel_walkthrough.md) for complete example.

---

## Summary

**You now know:**

- ✅ **Complete workflow:** YAML → Validate → Generate → Deploy → Control
- ✅ **YAML schema:** Required fields, datatypes, mapping strategies
- ✅ **Type system:** 25 types, selection guidelines, platform compatibility
- ✅ **Register mapping:** 3 strategies, efficiency metrics
- ✅ **Code generation:** Pipeline, generated files, command usage
- ✅ **Best practices:** Naming, type selection, safety, optimization
- ✅ **Common patterns:** FSM, voltage, timing, multi-channel

**Next steps:**

- **Deep dive:** [YAML Schema](../reference/yaml_schema.md), [Register Mapping](../reference/register_mapping.md)
- **Examples:** [Minimal Walkthrough](../examples/minimal_walkthrough.md), [Common Patterns](../examples/common_patterns.md)
- **Troubleshooting:** [Common Issues](troubleshooting.md)

---

**Questions?** See [Troubleshooting](troubleshooting.md) or [Architecture Docs](../architecture/overview.md).
