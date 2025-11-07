# YAML Schema Reference

**Complete specification for moku-instrument-forge YAML v2.0 format.**

This document defines the structure and validation rules for instrument specification YAML files. These specs are validated by Pydantic and generate VHDL shims + Python control interfaces.

---

## Overview

**Purpose:** YAML files define the register interface for custom Moku instruments.

**Format:** YAML v2.0 (declarative, version-controlled, human-readable)

**Validation:** Pydantic models (`BasicAppsRegPackage`, `DataTypeSpec`)

**Outputs:**
- `manifest.json` - Package contract for deployment/docs/debug
- `*_shim.vhd` - VHDL entity with typed signal interface
- `*_main.vhd` - Template for user logic implementation

**See also:**
- [Type System Reference](type_system.md) for datatype details
- [Getting Started Guide](../guides/getting_started.md) for tutorial walkthrough
- [Examples](../examples/) for complete examples

---

## Top-Level Schema

```yaml
# Required fields
app_name: <string>
version: <string>
description: <string>
platform: <enum>
datatypes: <array>

# Optional fields
mapping_strategy: <enum>  # Default: type_clustering
```

### Required Fields

#### `app_name` (string)

Application name used for file generation and identification.

**Rules:**
- Must be 1-50 characters
- Snake_case recommended (e.g., `emfi_probe_v1`)
- Used as VHDL entity name prefix
- Used for output file naming (`<app_name>_shim.vhd`)

**Examples:**
```yaml
app_name: emfi_probe_v1     # Good: descriptive, versioned
app_name: my_instrument     # Good: clear, simple
app_name: DS1140_PD         # Good: follows naming convention
```

---

#### `version` (string)

Semantic version of the instrument spec.

**Rules:**
- Semver format recommended (e.g., `1.0.0`, `2.1.3`)
- String format (not numeric)
- Used for tracking changes over time

**Examples:**
```yaml
version: 1.0.0    # Initial release
version: 2.1.0    # Added new signals
version: 1.0.1    # Bug fix, no API change
```

---

#### `description` (string)

Human-readable description of the instrument's purpose.

**Rules:**
- Maximum 500 characters
- Used in manifest.json and generated documentation
- Should explain what the instrument does

**Examples:**
```yaml
description: EMFI probe driver with voltage and timing control

description: |
  Multi-channel pulse generator with independent timing control
  for each channel. Supports nanosecond-resolution glitch injection.

description: Power analysis probe controller for side-channel research
```

---

#### `platform` (enum)

Target Moku platform for deployment.

**Valid Values:**
- `moku_go` - Moku:Go (125 MHz, ±25V input, ±5V output)
- `moku_lab` - Moku:Lab (500 MHz, ±5V input, ±1V output)
- `moku_pro` - Moku:Pro (1.25 GHz, ±20V input, ±5V output)
- `moku_delta` - Moku:Delta (5 GHz, ±20V input, ±5V output)

**Platform-Specific Behavior:**
- Clock frequency constants injected into VHDL
- Time conversion formulas adjusted automatically
- Voltage ranges validated against platform capabilities

**Examples:**
```yaml
platform: moku_go     # For Moku:Go (most common)
platform: moku_pro    # For Moku:Pro (high-speed)
```

**See also:** [Type System - Platform Compatibility](type_system.md#platform-compatibility)

---

#### `datatypes` (array)

Array of signal definitions. Each element is a `DataTypeSpec` object.

**Rules:**
- Must contain at least 1 signal
- Maximum total bits: 384 bits (12 registers × 32 bits)
- All signal names must be unique
- Array order determines default packing order

**See:** [Datatypes Array Specification](#datatypes-array) below.

---

### Optional Fields

#### `mapping_strategy` (enum)

Register packing strategy for optimizing bit usage.

**Valid Values:**
- `first_fit` - Assign each signal to first register with space (naive, testing only)
- `best_fit` - Assign to register with smallest remaining space (maximum density)
- `type_clustering` - **Default.** Group by bit width, then pack (best balance)

**Default:** `type_clustering` (recommended for most applications)

**Examples:**
```yaml
mapping_strategy: type_clustering  # Default (explicit)
mapping_strategy: best_fit         # Maximum packing density
# Omit field to use default
```

**See also:** [Register Mapping Reference](register_mapping.md) for detailed algorithm explanations.

---

## Datatypes Array

Each element in the `datatypes` array defines a single signal (register field).

### Schema

```yaml
datatypes:
  - name: <string>              # Required
    datatype: <enum>            # Required
    description: <string>       # Required
    default_value: <number>     # Required

    # Optional UI metadata
    units: <string>             # Optional
    display_name: <string>      # Optional
    min_value: <number>         # Optional
    max_value: <number>         # Optional
```

### Required Per Signal

#### `name` (string)

Variable name for this signal (becomes VHDL signal name).

**Rules:**
- Must be 1-50 characters
- Must start with letter (a-z, A-Z)
- Only alphanumeric and underscore allowed (a-z, A-Z, 0-9, _)
- Cannot be VHDL reserved word (`signal`, `entity`, `process`, `begin`, `end`, `if`, `then`, `else`, etc.)
- Must be unique within `datatypes` array

**Examples:**
```yaml
name: output_voltage    # Good: descriptive, snake_case
name: enable_ch1        # Good: clear, numbered
name: glitch_width_ns   # Good: includes units in name
name: arm_probe         # Good: action + target

name: 2nd_channel       # BAD: starts with number
name: my-signal         # BAD: hyphen not allowed
name: signal            # BAD: VHDL reserved word
```

---

#### `datatype` (enum)

BasicAppDataTypes type for this signal.

**Valid Values:** Any of the 23 BasicAppDataTypes (see [Type System Reference](type_system.md#quick-reference-table))

**Most Common:**
- `voltage_output_05v_s16` - ±5V DAC output, 16-bit
- `pulse_duration_ns_u16` - Nanosecond timing, 16-bit
- `pulse_duration_us_u16` - Microsecond timing, 16-bit
- `pulse_duration_ms_u16` - Millisecond timing, 16-bit
- `boolean` - Single bit flag

**Examples:**
```yaml
datatype: voltage_output_05v_s16   # Standard voltage output
datatype: pulse_duration_ns_u16    # Nanosecond timing
datatype: boolean                  # Flag/enable
```

**See also:** [Type System Reference](type_system.md) for complete type catalog.

---

#### `description` (string)

Human-readable description of this signal's purpose.

**Rules:**
- Maximum 200 characters
- Used in manifest.json, VHDL comments, generated documentation
- Should explain what the signal controls or represents

**Examples:**
```yaml
description: Output voltage setpoint for probe driver
description: Glitch pulse width in nanoseconds
description: Enable channel 1 output driver
description: Arm the EMFI probe for triggered operation
```

---

#### `default_value` (number | boolean)

Default value for this signal at reset/initialization.

**Rules:**
- **Boolean types:** Must be `0` (false) or `1` (true), or `false`/`true` (YAML boolean)
- **Numeric types:** Must be integer within type's min/max range
- **Validation:** Checked against `TYPE_REGISTRY` constraints at parse time

**Type-Specific Ranges:**
- Voltage types: Depends on bit width and signedness (e.g., -32768 to 32767 for S16)
- Time types: Unsigned, 0 to max (e.g., 0 to 65535 for U16)
- Boolean: 0 or 1

**Examples:**
```yaml
# Voltage (signed 16-bit: -32768 to 32767)
default_value: 0        # 0V

# Time (unsigned 16-bit: 0 to 65535)
default_value: 500      # 500 nanoseconds

# Boolean
default_value: 0        # false (disabled)
default_value: false    # YAML boolean format also works
```

---

### Optional Per Signal

Optional fields provide UI metadata for TUI/GUI generation and runtime validation.

#### `units` (string)

Physical units for display (e.g., in Textual TUI or web UI).

**Rules:**
- Maximum 10 characters
- For display only (does not affect VHDL generation)
- Recommended for voltage and time types

**Examples:**
```yaml
units: V        # Volts
units: mV       # Millivolts
units: ns       # Nanoseconds
units: us       # Microseconds (note: us, not µs)
units: ms       # Milliseconds
units: cycles   # Clock cycles
```

---

#### `display_name` (string)

Human-friendly name for UI display.

**Rules:**
- Maximum 50 characters
- Falls back to `name` if not provided
- Used in TUI/GUI labels

**Examples:**
```yaml
name: output_voltage
display_name: Output Voltage    # Title case for UI

name: glitch_width_ns
display_name: Glitch Width (ns) # Includes units
```

---

#### `min_value` (number)

Minimum allowed value for runtime validation/UI sliders.

**Rules:**
- Must be <= `max_value` if both provided
- Must be within type's intrinsic range (from `TYPE_REGISTRY`)
- Used for:
  - UI slider ranges
  - Runtime validation (future)
  - Documentation generation

**Examples:**
```yaml
# Voltage: constrain to positive only
datatype: voltage_output_05v_s16  # Type allows -5V to +5V
min_value: 0.0                    # But restrict to 0V to +5V
max_value: 5.0

# Time: reasonable operational range
datatype: pulse_duration_ns_u16   # Type allows 0-65535 ns
min_value: 10                     # But restrict to 10-1000 ns
max_value: 1000
```

---

#### `max_value` (number)

Maximum allowed value for runtime validation/UI sliders.

**Rules:**
- Must be >= `min_value` if both provided
- Must be within type's intrinsic range (from `TYPE_REGISTRY`)
- Used for:
  - UI slider ranges
  - Runtime validation (future)
  - Documentation generation

**Examples:**
```yaml
# Limit voltage range
max_value: 3.3                    # Limit to 3.3V max (even though type allows 5V)

# Limit timing range
max_value: 10000                  # 10 microseconds max
```

---

## Validation Rules

YAML files are validated by Pydantic models at parse time. Validation failures produce clear error messages.

### Top-Level Validation

1. **Required fields present:** `app_name`, `version`, `description`, `platform`, `datatypes`
2. **`app_name`:** 1-50 characters
3. **`description`:** Max 500 characters
4. **`platform`:** One of: `moku_go`, `moku_lab`, `moku_pro`, `moku_delta`
5. **`datatypes`:** At least 1 element
6. **`mapping_strategy`:** One of: `first_fit`, `best_fit`, `type_clustering` (if provided)

### Datatypes Array Validation

1. **Unique names:** All `name` fields must be unique
2. **Valid names:** Must start with letter, only alphanumeric + underscore, no VHDL reserved words
3. **Valid datatypes:** Must be one of 23 BasicAppDataTypes enum values
4. **Total bits:** Sum of all bit widths must be <= 384 bits (12 registers × 32 bits)

### Per-Signal Validation

1. **`default_value` type match:**
   - Boolean types require `bool` or `int` (0/1)
   - Numeric types require `int`

2. **`default_value` range:**
   - Must be within `TYPE_REGISTRY[datatype].min_value` to `max_value`

3. **`min_value` <= `max_value`:**
   - If both provided, min must be less than or equal to max

4. **UI constraints within type limits:**
   - `min_value` must be >= `TYPE_REGISTRY[datatype].min_value`
   - `max_value` must be <= `TYPE_REGISTRY[datatype].max_value`

### Common Validation Errors

```yaml
# ERROR: Name starts with number
datatypes:
  - name: 2nd_channel    # ValidationError: Name must start with letter

# ERROR: Invalid datatype
datatypes:
  - name: my_signal
    datatype: voltage_invalid_type    # ValidationError: Unknown type

# ERROR: default_value out of range
datatypes:
  - name: voltage
    datatype: voltage_output_05v_s16  # Range: -32768 to 32767
    default_value: 100000             # ValidationError: Above max

# ERROR: min_value > max_value
datatypes:
  - name: voltage
    min_value: 5.0
    max_value: 0.0                    # ValidationError: min > max

# ERROR: Total bits exceed limit
datatypes:
  - name: signal1
    datatype: voltage_output_05v_s16  # 16 bits
  # ... 23 more 16-bit signals ...
  # Total: 24 × 16 = 384 bits (OK)
  - name: signal25
    datatype: boolean                 # +1 bit = 385 bits
    # ValidationError: Exceeds 384-bit limit
```

---

## Complete Example

This example demonstrates all top-level fields and signal metadata:

```yaml
# Complete 6-signal example showing all field types
app_name: multi_channel_probe
version: 2.1.0
description: |
  Multi-channel EMFI probe controller with independent voltage
  and timing control for each channel. Supports glitch injection
  with nanosecond resolution.
platform: moku_pro
mapping_strategy: type_clustering  # Optional, this is the default

datatypes:
  # Channel 1 voltage output
  - name: dac_voltage_ch1
    datatype: voltage_output_05v_s16
    description: Channel 1 DAC output voltage
    default_value: 0
    units: V
    display_name: CH1 Voltage
    min_value: -5.0
    max_value: 5.0

  # Channel 2 voltage output
  - name: dac_voltage_ch2
    datatype: voltage_output_05v_s16
    description: Channel 2 DAC output voltage
    default_value: 0
    units: V
    display_name: CH2 Voltage
    min_value: -5.0
    max_value: 5.0

  # Glitch timing (nanoseconds)
  - name: glitch_width
    datatype: pulse_duration_ns_u16
    description: Glitch pulse width in nanoseconds
    default_value: 500
    units: ns
    display_name: Glitch Width
    min_value: 10       # Minimum 10ns
    max_value: 10000    # Maximum 10µs

  # Recovery delay (microseconds)
  - name: recovery_delay
    datatype: pulse_duration_us_u16
    description: Recovery delay between glitch attempts
    default_value: 1000
    units: us
    display_name: Recovery Delay
    min_value: 100      # Minimum 100µs
    max_value: 50000    # Maximum 50ms

  # Channel 1 enable
  - name: enable_ch1
    datatype: boolean
    description: Enable channel 1 output driver
    default_value: 0    # Disabled by default
    display_name: Enable CH1

  # Channel 2 enable
  - name: enable_ch2
    datatype: boolean
    description: Enable channel 2 output driver
    default_value: 0    # Disabled by default
    display_name: Enable CH2
```

**Register Mapping Result:**
- **Total signals:** 6
- **Total bits:** 16 + 16 + 16 + 16 + 1 + 1 = 66 bits
- **Registers used:** 3 registers (CR6, CR7, CR8)
- **Efficiency:** 66/96 bits = 69% (with type_clustering)

**Generated Files:**
- `manifest.json` - Package contract with register assignments
- `multi_channel_probe_shim.vhd` - VHDL entity with typed signals
- `multi_channel_probe_main.vhd` - Template for user logic

**See also:** [Examples - Multi-Channel Walkthrough](../examples/multi_channel_walkthrough.md) for detailed breakdown.

---

## Related Documentation

- **[Type System Reference](type_system.md)** - Complete type catalog and usage guide
- **[Register Mapping Reference](register_mapping.md)** - How signals are packed into registers
- **[Manifest Schema Reference](manifest_schema.md)** - Output format (manifest.json)
- **[Getting Started Guide](../guides/getting_started.md)** - Tutorial with minimal example
- **[Examples](../examples/)** - Complete YAML examples with walkthroughs
- **[Troubleshooting - YAML Validation](../guides/troubleshooting.md#yaml-validation-errors)** - Common errors and fixes

---

## Quick Validation

Test your YAML file:

```bash
# Validate YAML syntax and schema
uv run python -m forge.validate_yaml specs/my_instrument.yaml

# Generate package to test full pipeline
uv run python -m forge.generate_package \
    specs/my_instrument.yaml \
    --output-dir output/my_instrument
```

---

**Key Takeaway:** YAML files define the register interface declaratively. Pydantic validates all fields, and the forge pipeline generates VHDL + manifest.json automatically. Use `type_clustering` strategy for optimal register packing (50-75% savings vs manual allocation).

---

*Last Updated: 2025-11-03*
