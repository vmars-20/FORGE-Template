# Type System Reference

**moku-instrument-forge** uses the **BasicAppDataTypes** type system for type-safe register communication between Python control applications and VHDL FPGA logic.

## Overview

BasicAppDataTypes solves the problem of manual, error-prone bit-slicing by providing:

- **Automatic register packing** - 50-75% space savings by packing multiple values into minimal registers
- **User-friendly units** - Volts, nanoseconds, milliseconds (not raw bits or clock cycles)
- **Platform-aware conversions** - Handles 125 MHz to 5 GHz clock rates automatically
- **Type safety** - Prevents range mismatches (e.g., ±5V output vs ±20V input)

**Key Design Principle:** Fixed bit widths with explicit type selection. No dynamic sizing.

**Authoritative Documentation:** For complete type definitions, conversion formulas, and implementation details, see:
- [`libs/basic-app-datatypes/llms.txt`](../../libs/basic-app-datatypes/llms.txt)
- [`libs/basic-app-datatypes/README.md`](../../libs/basic-app-datatypes/README.md)

---

## Type Categories

BasicAppDataTypes provides **23 built-in types** organized into 3 categories:

### 1. Voltage Types (12 types)

Fixed voltage ranges with signed/unsigned variants to optimize register packing.

**Output Ranges:**
- `±5V` - DAC output range (S8, S16, U7, U15)

**Input Ranges:**
- `±20V` - ADC input range for Moku:Pro/Delta (S8, S16, U7, U15)
- `±25V` - ADC input range for Moku:Go (S8, S16, U7, U15)

**Unsigned Types (U7, U15):** Save 1 bit when only positive voltages are needed (0 to +5V instead of -5V to +5V). Enables better register packing.

**See also:** [Platform Compatibility](#platform-compatibility) for voltage range details per platform.

### 2. Time Types (10 types)

User-friendly time units with multiple bit widths for different range requirements.

**Available Units:**
- **Nanoseconds** (U8, U16, U32) - Fine-grained timing, glitch widths
- **Microseconds** (U8, U16, U24) - Medium timing, delays, pulse widths
- **Milliseconds** (U8, U16) - Long delays, timeouts
- **Seconds** (U8, U16) - Very long delays, measurement windows

**Design Rationale:** Multiple units for convenience. Writing `PulseDuration_ms(100)` is clearer than `PulseDuration_ns(100_000_000)`.

### 3. Boolean Type (1 type)

- **`BOOLEAN`** (1 bit) - Flags, enables, arm signals

Single bit for maximum register packing efficiency. Values: `0` (false) or `1` (true).

---

## Quick Reference Table

This table covers all 23 BasicAppDataTypes. For detailed specifications, see [`libs/basic-app-datatypes/llms.txt`](../../libs/basic-app-datatypes/llms.txt).

### Voltage Types (12)

| Type | Bits | Signed | Range | Use Case |
|------|------|--------|-------|----------|
| `voltage_output_05v_s8` | 8 | Yes | -5V to +5V | Low-res DAC output |
| `voltage_output_05v_s16` | 16 | Yes | -5V to +5V | **DAC output (standard)** |
| `voltage_output_05v_u7` | 7 | No | 0V to +5V | Positive-only DAC output |
| `voltage_output_05v_u15` | 15 | No | 0V to +5V | Positive-only, high-res |
| `voltage_input_20v_s8` | 8 | Yes | -20V to +20V | Low-res ADC input (Pro/Delta) |
| `voltage_input_20v_s16` | 16 | Yes | -20V to +20V | ADC input (Pro/Delta) |
| `voltage_input_20v_u7` | 7 | No | 0V to +20V | Positive-only input |
| `voltage_input_20v_u15` | 15 | No | 0V to +20V | Positive-only, high-res |
| `voltage_input_25v_s8` | 8 | Yes | -25V to +25V | Low-res ADC input (Go) |
| `voltage_input_25v_s16` | 16 | Yes | -25V to +25V | ADC input (Go) |
| `voltage_input_25v_u7` | 7 | No | 0V to +25V | Positive-only input |
| `voltage_input_25v_u15` | 15 | No | 0V to +25V | Positive-only, high-res |

### Time Types (10)

| Type | Bits | Range (unsigned) | Use Case |
|------|------|------------------|----------|
| `pulse_duration_ns_u8` | 8 | 0-255 ns | Very short pulses |
| `pulse_duration_ns_u16` | 16 | 0-65,535 ns | **Glitch widths (standard)** |
| `pulse_duration_ns_u32` | 32 | 0-4.3B ns (~4.3s) | Long timing in ns resolution |
| `pulse_duration_us_u8` | 8 | 0-255 µs | Short delays |
| `pulse_duration_us_u16` | 16 | 0-65,535 µs (~65ms) | **Delays, pulses (standard)** |
| `pulse_duration_us_u24` | 24 | 0-16.7M µs (~16s) | Very long delays |
| `pulse_duration_ms_u8` | 8 | 0-255 ms | Medium timeouts |
| `pulse_duration_ms_u16` | 16 | 0-65,535 ms (~65s) | **Long timeouts (standard)** |
| `pulse_duration_sec_u8` | 8 | 0-255 s | Very long delays |
| `pulse_duration_sec_u16` | 16 | 0-65,535 s (~18hr) | Measurement windows |

### Boolean Type (1)

| Type | Bits | Values | Use Case |
|------|------|--------|----------|
| `boolean` | 1 | 0 or 1 | Flags, enables, arm signals |

---

## Common Use Cases

### When to Use Each Type Category

#### Voltage Types

**Use Output Types (`voltage_output_05v_*`) when:**
- Controlling DAC outputs
- Setting probe intensities
- Configuring analog outputs
- Output range: ±5V (all platforms) or ±1V (Moku:Lab)

**Use Input Types when:**
- Configuring ADC thresholds
- Setting trigger levels
- Defining measurement ranges
- Input range: ±20V (Pro/Delta) or ±25V (Go)

**Choose Signed vs Unsigned:**
- **Signed (S8, S16):** Default choice, supports negative voltages
- **Unsigned (U7, U15):** Only when positive voltages needed, saves 1 bit for better packing

**Choose Bit Width:**
- **8-bit:** Low resolution (~40mV per step on ±5V), use when coarse control is acceptable
- **16-bit:** Standard resolution (~150µV per step on ±5V), use for most applications

#### Time Types

**Choose Units Based on Application:**
- **Nanoseconds:** Glitch widths (10-1000ns), fast gate delays, high-speed triggers
- **Microseconds:** Pulse widths (1-10000µs), settling times, ADC delays
- **Milliseconds:** Debounce delays (10-500ms), timeouts, slow ramp times
- **Seconds:** Measurement windows, very long delays

**Choose Bit Width:**
- **U8:** Limited range (0-255), use when range is constrained
- **U16:** Standard choice, good balance of range and space
- **U24/U32:** Extended range, use when long durations needed

**Platform Conversion:** All time types are platform-aware. The `TypeConverter` automatically converts user-friendly units (ns, µs, ms) to platform-specific clock cycles.

#### Boolean Types

**Use `boolean` for:**
- Feature enables (`enable_output`)
- Arm/trigger signals (`arm_probe`, `trigger_now`)
- Mode selection when only 2 states needed (`high_speed_mode`)
- State flags (`calibration_complete`)

**Not recommended for:** Multi-option selection (use smallest adequate numeric type instead).

---

## Platform Compatibility

All 23 types work across all 4 Moku platforms. The `TypeConverter` handles platform-specific conversions automatically.

| Platform | Clock | Period | ADC/DAC | Input Range | Output Range |
|----------|-------|--------|---------|-------------|--------------|
| **Moku:Go** | 125 MHz | 8.0 ns | 12-bit | ±25V | ±5V |
| **Moku:Lab** | 500 MHz | 2.0 ns | 12-bit | ±5V | ±1V |
| **Moku:Pro** | 1.25 GHz | 0.8 ns | 10-bit | ±20V | ±5V |
| **Moku:Delta** | 5 GHz | 0.2 ns | 14-bit | ±20V | ±5V |

**Note:** Input/output voltage range types are platform-agnostic. The `voltage_input_20v_*` types work on all platforms but match the physical ranges of Moku:Pro/Delta. Choose types that match your target platform's capabilities.

**See also:** [`libs/basic-app-datatypes/llms.txt`](../../libs/basic-app-datatypes/llms.txt) for detailed platform conversion formulas.

---

## Type Metadata

Query type properties at runtime using the `TYPE_REGISTRY`:

```python
from basic_app_datatypes import TYPE_REGISTRY, BasicAppDataTypes

# Query type properties
voltage_type = BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
metadata = TYPE_REGISTRY[voltage_type]

print(metadata.bit_width)      # 16
print(metadata.voltage_range)  # "±5V"
print(metadata.is_signed)      # True
print(metadata.description)    # "Output voltage, ±5V range, signed 16-bit"
print(metadata.min_value)      # -32768
print(metadata.max_value)      # 32767
```

**Available Metadata Fields:**
- `bit_width` - Number of bits (1-32)
- `is_signed` - Boolean flag
- `voltage_range` - Human-readable range (e.g., "±5V")
- `description` - Human-readable description
- `min_value` - Minimum integer value (if applicable)
- `max_value` - Maximum integer value (if applicable)

**See also:** [`libs/basic-app-datatypes/basic_app_datatypes/metadata.py`](../../libs/basic-app-datatypes/basic_app_datatypes/metadata.py) for complete TYPE_REGISTRY implementation.

---

## Examples

### Example 1: Voltage Control (EMFI Probe)

```yaml
# specs/emfi_probe.yaml
app_name: emfi_probe_v1
version: 1.0.0
description: EMFI probe driver with voltage control
platform: moku_pro

datatypes:
  - name: output_voltage
    datatype: voltage_output_05v_s16  # ±5V, 16-bit (~150µV resolution)
    description: Probe output voltage
    default_value: 0
    units: V
    min_value: -5.0
    max_value: 5.0
```

**Why `voltage_output_05v_s16`?**
- DAC output (use output type, not input type)
- Bipolar voltage needed (use signed, not unsigned)
- Standard 16-bit resolution adequate (~150µV per step)

### Example 2: Timing Control (Pulse Generator)

```yaml
# specs/pulse_gen.yaml
app_name: pulse_generator
version: 1.0.0
platform: moku_go

datatypes:
  - name: glitch_width
    datatype: pulse_duration_ns_u16  # 0-65535 ns, fine control
    description: Glitch pulse width
    default_value: 500  # 500 nanoseconds
    units: ns

  - name: recovery_delay
    datatype: pulse_duration_us_u16  # 0-65535 µs, coarser control
    description: Recovery delay between pulses
    default_value: 1000  # 1000 microseconds (1ms)
    units: us
```

**Why different time units?**
- Glitch width needs fine control (nanoseconds)
- Recovery delay is longer, microseconds are more natural
- Avoids large numbers: `1000 µs` clearer than `1000000 ns`

### Example 3: Boolean Flags (Multi-Channel Control)

```yaml
# specs/multi_channel.yaml
app_name: multi_channel_controller
version: 1.0.0
platform: moku_pro

datatypes:
  - name: enable_ch1
    datatype: boolean  # 1 bit
    description: Enable channel 1 output
    default_value: 0  # false

  - name: enable_ch2
    datatype: boolean  # 1 bit
    description: Enable channel 2 output
    default_value: 0  # false

  - name: high_speed_mode
    datatype: boolean  # 1 bit
    description: Enable high-speed acquisition mode
    default_value: 1  # true
```

**Why boolean?**
- Only 2 states needed (on/off, enabled/disabled)
- Minimal register space (1 bit each)
- Clear semantic meaning

### Example 4: Type Conversion (Python)

```python
from basic_app_datatypes import TypeConverter, BasicAppDataTypes

converter = TypeConverter()

# Convert voltage to register bits
voltage = 2.5  # Volts
register_value = converter.voltage_output_05v_s16_to_raw(voltage)
# Result: 16384 (0x4000) - 50% of signed 16-bit range

# Convert time to clock cycles (platform-aware)
from basic_app_datatypes import PulseDuration_ns

duration = PulseDuration_ns(500, width=16)  # 500 nanoseconds
cycles = duration.to_cycles(clock_period_ns=8.0)  # Moku:Go @ 125 MHz
# Result: 63 cycles (500ns / 8.0ns per cycle, rounded)

# Query type information
metadata = TYPE_REGISTRY[BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16]
print(f"Bit width: {metadata.bit_width}")  # 16
print(f"Range: {metadata.voltage_range}")  # ±5V
```

**See also:**
- [YAML Schema Reference](yaml_schema.md) for complete YAML specification
- [Getting Started Guide](../guides/getting_started.md) for tutorial walkthrough
- [Examples](../examples/) for more complete examples

---

## Detailed Documentation

For complete details on type definitions, conversion algorithms, and implementation:

**Authoritative Sources:**
- [`libs/basic-app-datatypes/llms.txt`](../../libs/basic-app-datatypes/llms.txt) - Complete type system documentation
- [`libs/basic-app-datatypes/README.md`](../../libs/basic-app-datatypes/README.md) - User documentation with examples
- [`libs/basic-app-datatypes/basic_app_datatypes/types.py`](../../libs/basic-app-datatypes/basic_app_datatypes/types.py) - Enum definitions
- [`libs/basic-app-datatypes/basic_app_datatypes/metadata.py`](../../libs/basic-app-datatypes/basic_app_datatypes/metadata.py) - TYPE_REGISTRY implementation
- [`libs/basic-app-datatypes/basic_app_datatypes/converters.py`](../../libs/basic-app-datatypes/basic_app_datatypes/converters.py) - TypeConverter with 24+ conversion methods

**Related Documentation:**
- [YAML Schema Reference](yaml_schema.md) - How to specify types in YAML
- [Register Mapping Reference](register_mapping.md) - How types are packed into registers
- [Python API Reference](python_api.md) - Programmatic access to types
- [User Guide](../guides/user_guide.md) - High-level type system overview

---

**Key Takeaway:** BasicAppDataTypes provides 23 fixed-width types (12 voltage, 10 time, 1 boolean) that work across all 4 Moku platforms. The type system trades manual bit-slicing for automatic type-safe register packing with 50-75% space savings.

---

*Last Updated: 2025-11-03*
