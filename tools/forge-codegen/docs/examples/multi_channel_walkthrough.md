# Multi-Channel Probe Walkthrough

**Purpose:** Demonstrate type variety and register packing efficiency with a 6-signal spec

**Audience:** Users ready to build more complex instruments

**Time:** 30 minutes

---

## Overview

This walkthrough shows how to build a **2-channel probe controller** with:
- ✅ Multiple voltage channels (DAC outputs)
- ✅ Mixed timing types (milliseconds + nanoseconds)
- ✅ Per-channel enable flags
- ✅ **90.6% register efficiency** (exceptional!)

**What you'll learn:**
- Type selection rationale (when to use which type)
- How `best_fit` packing achieves 90.6% efficiency
- Constraints (`min_value`/`max_value`) for safety
- Python control patterns for multi-channel instruments

**Prerequisites:** Complete [Minimal Walkthrough](minimal_walkthrough.md) first.

---

## Requirements

**Building a 2-channel probe controller:**

| Feature | Requirement | Type Choice |
|---------|-------------|-------------|
| **Voltage control** | ±5V per channel | `voltage_output_05v_s16` |
| **Pulse timing** | 10ms - 10s (human-scale) | `pulse_duration_ms_u16` |
| **Settling time** | 1-255 ns (FPGA-scale) | `pulse_duration_ns_u8` |
| **Channel enables** | On/Off per channel | `boolean` |

**Platform:** Moku:Pro (1.25 GHz, 4 slots)

**Why Moku:Pro?** Demonstrates platform-agnostic types (same YAML works on all platforms, only clock frequency differs).

---

## Complete Spec

**File:** `docs/examples/multi_channel.yaml`

```yaml
app_name: multi_channel_probe
version: 1.0.0
description: Multi-channel probe controller with type variety
platform: moku_pro

datatypes:
  # Voltage outputs (DAC)
  - name: dac_voltage_ch1
    datatype: voltage_output_05v_s16
    description: Channel 1 DAC output
    default_value: 0
    units: V

  - name: dac_voltage_ch2
    datatype: voltage_output_05v_s16
    description: Channel 2 DAC output
    default_value: 0
    units: V

  # Timing parameters
  - name: pulse_width
    datatype: pulse_duration_ms_u16
    description: Pulse width
    default_value: 100
    units: ms
    min_value: 10
    max_value: 10000

  - name: settling_time
    datatype: pulse_duration_ns_u8
    description: ADC settling time in nanoseconds
    default_value: 10
    units: ns
    min_value: 1
    max_value: 255

  # Channel enables
  - name: enable_ch1
    datatype: boolean
    description: Enable channel 1
    default_value: false

  - name: enable_ch2
    datatype: boolean
    description: Enable channel 2
    default_value: false
```

**Signals:** 6 (2 voltage + 2 time + 2 boolean)
**Registers:** 2 (CR6, CR7)
**Efficiency:** 90.6% (58/64 bits used)

---

## Type Selection Rationale

### Voltage Types

**Chose:** `voltage_output_05v_s16`

**Why this type?**
1. **Output range:** Moku:Pro DAC range is ±5V
2. **Signed:** Need both positive and negative voltages
3. **16-bit resolution:** 5V / 32768 ≈ 0.15 mV/step (adequate)

**Alternatives considered:**
- `voltage_output_05v_s8` - Only 256 steps → 39 mV/step (too coarse)
- `voltage_output_05v_u15` - Unsigned (0 to +5V only) → no negative voltages
- `voltage_output_025v_s16` - Smaller range (±2.5V) → higher precision (0.08 mV/step)

**Decision:** `s16` provides best balance of range and resolution.

---

### Time Types

#### Pulse Width: Human-Scale Timing

**Chose:** `pulse_duration_ms_u16`

**Why milliseconds?**
- **Range:** 0-65535 ms (0-65.5 seconds)
- **Resolution:** 1 ms per step
- **Use case:** Pulse durations controlled by user (buttons, UI sliders)

**Constraints:**
```yaml
min_value: 10      # Minimum 10 ms (prevent too-short pulses)
max_value: 10000   # Maximum 10 seconds (prevent runaway)
```

**Alternative:** `pulse_duration_s_u16` - Seconds (0-65535 s ≈ 18 hours)
- **Rejected:** Too coarse (1-second resolution), excessive range

---

#### Settling Time: FPGA-Scale Timing

**Chose:** `pulse_duration_ns_u8`

**Why nanoseconds?**
- **Range:** 1-255 ns
- **Platform:** Moku:Pro @ 1.25 GHz → 0.8 ns/cycle
- **Use case:** ADC settling time (clock-synchronized, FPGA internal)

**Conversion to cycles:**
```
10 ns @ 1.25 GHz = 10 / 0.8 = 12.5 cycles → rounds to 13 cycles
```

**Why u8 (not u16)?**
- **Range:** 255 ns is plenty for ADC settling (typical: 5-20 ns)
- **Bit savings:** 8 bits vs 16 bits → saves 8 bits for packing

**Alternative:** `pulse_duration_us_u8` - Microseconds (0-255 µs)
- **Rejected:** Too coarse for ADC timing (need sub-100 ns precision)

---

### Boolean Types

**Chose:** `boolean` (1-bit flag)

**Why separate enables?**
- **Safety:** Disable individual channels independently
- **Flexibility:** Ch1 ON, Ch2 OFF (or vice versa)
- **Register efficiency:** 2 booleans = 2 bits (not 16 bits with separate registers)

**Default:** `false` (both channels OFF on boot - safe!)

---

## Register Mapping

Running `best_fit` strategy:

```
CR6: [dac_voltage_ch1(16) | dac_voltage_ch2(16)] = 32/32 bits (100% full)
CR7: [pulse_width(16) | settling_time(8) | enable_ch1(1) | enable_ch2(1)] = 26/32 bits (81%)

Total: 2 registers
Bits used: 58/64 bits = 90.6% efficiency (exceptional!)
Registers saved: 4 (vs 6 registers with one-per-signal)
```

### Packing Algorithm

**Step 1: Sort signals by size**

| Signal | Type | Bits |
|--------|------|------|
| `dac_voltage_ch1` | `voltage_output_05v_s16` | 16 |
| `dac_voltage_ch2` | `voltage_output_05v_s16` | 16 |
| `pulse_width` | `pulse_duration_ms_u16` | 16 |
| `settling_time` | `pulse_duration_ns_u8` | 8 |
| `enable_ch1` | `boolean` | 1 |
| `enable_ch2` | `boolean` | 1 |

**Total:** 58 bits

**Step 2: Pack into registers (best-fit)**

1. **CR6:** Fit two 16-bit signals
   - `dac_voltage_ch1` (16) + `dac_voltage_ch2` (16) = 32 bits ✅ **Perfect fit!**

2. **CR7:** Pack remaining signals
   - `pulse_width` (16) + `settling_time` (8) + `enable_ch1` (1) + `enable_ch2` (1) = 26 bits
   - **6 bits unused** (not bad!)

**Result:** 2 registers, 90.6% efficiency

### Why So Efficient?

1. **Multiple 16-bit signals:** Two pairs fit perfectly in CR6 (100% full)
2. **Mixed widths in CR7:** 16 + 8 + 1 + 1 = 26 bits (good packing)
3. **Minimal waste:** Only 6 bits unused (vs 31 bits in minimal_probe example)

**Key insight:** More signals → better packing efficiency!

---

### Bit Layout Diagram

```
CR6 (32 bits): 100% full
┌──────────────────┬──────────────────┐
│ dac_voltage_ch1  │ dac_voltage_ch2  │
│     [31:16]      │      [15:0]      │
│     16 bits      │     16 bits      │
└──────────────────┴──────────────────┘

CR7 (32 bits): 81% full
┌──────────────┬─────────────┬──┬──┬────────┐
│ pulse_width  │settling_time│c1│c2│(unused)│
│   [31:16]    │   [15:8]    │ │ │        │
│   16 bits    │   8 bits    │1│1│ 6 bits │
└──────────────┴─────────────┴──┴──┴────────┘
                              ^  ^
                           enable_ch1/ch2
                           [7] [6]
```

**Note:** Boolean flags are packed together at lower bit positions.

---

## Generated VHDL Excerpts

### Shim Entity

**File:** `output/multi_channel_probe/multi_channel_probe_shim.vhd`

```vhdl
entity multi_channel_probe_shim is
  generic (
    CLK_FREQ_HZ : integer := 1250000000  -- Moku:Pro @ 1.25 GHz
  );
  port (
    clk : in std_logic;
    rst : in std_logic;

    -- Control register inputs
    control_6_in : in std_logic_vector(31 downto 0);
    control_7_in : in std_logic_vector(31 downto 0);

    -- Unpacked signals
    dac_voltage_ch1 : out signed(15 downto 0);     -- ±5V
    dac_voltage_ch2 : out signed(15 downto 0);     -- ±5V
    pulse_width     : out unsigned(15 downto 0);   -- 0-65535 ms
    settling_time   : out unsigned(7 downto 0);    -- 0-255 ns
    enable_ch1      : out std_logic;               -- Boolean
    enable_ch2      : out std_logic;               -- Boolean

    -- ... additional ports ...
  );
end entity;

architecture rtl of multi_channel_probe_shim is
begin
  -- Unpack CR6 (voltage channels)
  dac_voltage_ch1 <= signed(control_6_in(31 downto 16));
  dac_voltage_ch2 <= signed(control_6_in(15 downto 0));

  -- Unpack CR7 (timing + enables)
  pulse_width   <= unsigned(control_7_in(31 downto 16));
  settling_time <= unsigned(control_7_in(15 downto 8));
  enable_ch1    <= control_7_in(7);
  enable_ch2    <= control_7_in(6);

end architecture;
```

**Key observations:**
1. **Simple bit-slicing** - No complex logic
2. **Type-safe outputs** - `signed` for voltage, `unsigned` for time
3. **Platform constant** - `CLK_FREQ_HZ = 1.25 GHz` for time conversions

---

### Main Template Excerpt

**File:** `output/multi_channel_probe/multi_channel_probe_main.vhd`

```vhdl
architecture rtl of multi_channel_probe_main is
  -- Convert ns to cycles (platform-aware)
  constant CYCLES_PER_NS : real := real(CLK_FREQ_HZ) / 1.0e9;

  signal settling_cycles : unsigned(15 downto 0);
begin

  -- Convert settling time from nanoseconds to clock cycles
  -- settling_time is unsigned(7 downto 0) = 0-255 ns
  -- At 1.25 GHz (0.8 ns/cycle): 10 ns → 13 cycles
  settling_cycles <= to_unsigned(
    integer(real(to_integer(settling_time)) * CYCLES_PER_NS),
    16
  );

  -- Example: 2-channel DAC controller
  process(clk)
  begin
    if rising_edge(clk) then
      if rst = '1' then
        dac1_out <= (others => '0');
        dac2_out <= (others => '0');
      else
        -- Channel 1
        if enable_ch1 = '1' then
          dac1_out <= dac_voltage_ch1;
        else
          dac1_out <= (others => '0');
        end if;

        -- Channel 2
        if enable_ch2 = '1' then
          dac2_out <= dac_voltage_ch2;
        else
          dac2_out <= (others => '0');
        end if;

        -- Use pulse_width and settling_cycles for timing logic
        -- ... (your custom logic here) ...
      end if;
    end if;
  end process;

end architecture;
```

**Key features:**
1. **Platform-aware conversion:** `settling_time` (ns) → `settling_cycles` (clock ticks)
2. **Per-channel control:** Independent enable flags
3. **Type-safe arithmetic:** VHDL compiler enforces types

---

## Python Control Example

```python
from moku.instruments import CustomInstrument
import json

# Connect and deploy (conceptual - actual API may differ)
instr = CustomInstrument('192.168.1.100', 'multi_channel_probe')

# Load manifest for metadata
with open('output/multi_channel_probe/manifest.json') as f:
    manifest = json.load(f)

print(f"Loaded: {manifest['app_name']} v{manifest['version']}")
print(f"Efficiency: {manifest['efficiency']['percentage']}%")

# === Set parameters (conceptual API) ===

# Channel 1: 2.5V output
instr.set_parameter('dac_voltage_ch1', 2.5)   # Volts (converted to mV internally)
instr.set_parameter('enable_ch1', True)

# Channel 2: -1.0V output
instr.set_parameter('dac_voltage_ch2', -1.0)
instr.set_parameter('enable_ch2', True)

# Timing parameters
instr.set_parameter('pulse_width', 500)      # 500 ms
instr.set_parameter('settling_time', 20)     # 20 ns

# === Read back parameters ===
ch1_voltage = instr.get_parameter('dac_voltage_ch1')
ch1_enabled = instr.get_parameter('enable_ch1')

print(f"Channel 1: {ch1_voltage} V, {'ON' if ch1_enabled else 'OFF'}")
# Output: Channel 1: 2.5 V, ON

# === Batch parameter updates ===
instr.set_parameters({
    'dac_voltage_ch1': 1.0,
    'dac_voltage_ch2': -2.0,
    'pulse_width': 1000,
})

# === Safety: Disable all channels ===
instr.set_parameters({
    'enable_ch1': False,
    'enable_ch2': False,
})
```

**Best practices:**
1. **Disable channels before changing voltage** (prevent glitches)
2. **Use batch updates** for atomicity (all-or-nothing)
3. **Read back critical parameters** to verify

---

## Comparison: One-Per-Signal vs Packed

### Naive Approach (One Signal Per Register)

```
CR6: [dac_voltage_ch1(16)] = 16/32 bits (50%)
CR7: [dac_voltage_ch2(16)] = 16/32 bits (50%)
CR8: [pulse_width(16)]     = 16/32 bits (50%)
CR9: [settling_time(8)]    = 8/32 bits (25%)
CR10: [enable_ch1(1)]      = 1/32 bits (3%)
CR11: [enable_ch2(1)]      = 1/32 bits (3%)

Total: 6 registers, 58/192 bits = 30.2% efficiency
```

**Waste:** 134 bits unused!

### Optimized Approach (best_fit packing)

```
CR6: [dac_voltage_ch1(16) | dac_voltage_ch2(16)] = 32/32 bits (100%)
CR7: [pulse_width(16) | settling_time(8) | enable_ch1(1) | enable_ch2(1)] = 26/32 bits (81%)

Total: 2 registers, 58/64 bits = 90.6% efficiency
```

**Savings:**
- **4 registers saved** (6 → 2)
- **67% reduction** in register usage
- **128 bits freed** for future expansion

---

## Lessons Learned

### Type Selection

✅ **DO:**
- **Use narrowest type that fits range:** `u8` for 0-255, not `u16`
- **Match units to time scale:** milliseconds (human), nanoseconds (FPGA)
- **Use signed only if needed:** `s16` for ±5V, `u15` for 0-5V

❌ **DON'T:**
- **Oversized types:** `u32` when `u16` suffices (wastes 16 bits!)
- **Wrong time scale:** milliseconds for ADC settling (use nanoseconds)
- **Forget signedness:** Unsigned voltage types can't go negative

### Register Efficiency

- **Small specs (2-3 signals):** ~50% efficiency (acceptable)
- **Medium specs (4-6 signals):** 70-90% efficiency (good)
- **Large specs (8+ signals):** 80-95% efficiency (excellent)

**This spec:** 90.6% efficiency with only 6 signals (exceptional!)

**Why?** Good mix of widths (16, 16, 16, 8, 1, 1) packs well.

### Safety Constraints

```yaml
min_value: 10       # Prevent pulses shorter than 10 ms (dangerous)
max_value: 10000    # Prevent runaway (> 10 seconds)
```

**Benefits:**
1. **Runtime validation:** Reject out-of-range values before hardware
2. **UI hints:** Sliders automatically clamped to safe ranges
3. **Documentation:** Clear operating limits

**Best practice:** Always add constraints for safety-critical parameters!

---

## Optimization Tips

### How to Improve Efficiency Further

**Current waste:** 6 bits unused in CR7

**Options:**

1. **Add 6 more boolean flags:**
   ```yaml
   - name: flag_1
     datatype: boolean
   - name: flag_2
     datatype: boolean
   # ... (4 more flags)
   ```
   **Result:** CR7 becomes 100% full (32/32 bits)

2. **Add an 8-bit parameter:**
   ```yaml
   - name: gain_setting
     datatype: pulse_duration_ns_u8  # Reuse u8 type for 0-255 range
     description: Gain setting (0-255)
   ```
   **Problem:** Would overflow CR7 (26 + 8 = 34 bits > 32 bits)
   **Solution:** Mapper would create CR8 (1 register overhead)

**Verdict:** Leave 6 bits unused. Marginal gains don't justify complexity.

---

## Platform Portability

**Same YAML works on all platforms!**

```yaml
# Change platform: moku_pro → moku_go
platform: moku_go  # 125 MHz (was 1.25 GHz)
```

**Impact:**
1. **Clock frequency changes:** 1.25 GHz → 125 MHz
2. **Time conversions change:**
   - 10 ns @ 1.25 GHz → 13 cycles
   - 10 ns @ 125 MHz  → 2 cycles (rounded up)
3. **Types unchanged:** All 6 signals use same datatypes
4. **Register mapping unchanged:** CR6/CR7 layout identical

**Why it works:** BasicAppDataTypes are platform-agnostic (fixed bit widths, platform-aware converters).

---

## Next Steps

**You've mastered type variety and packing!** Now explore:

1. **[Common Patterns](common_patterns.md)** - Reusable design patterns catalog
2. **[Type System Reference](../reference/type_system.md)** - Deep dive into all 23 types
3. **[Register Mapping Algorithms](../reference/register_mapping.md)** - first_fit vs best_fit vs type_clustering

**Build something more complex:**
- Add trigger inputs (`voltage_input_25v_s16`)
- Add status LEDs (`boolean` flags)
- Add calibration parameters (`voltage_signed_s16` for offsets)

**Challenge:** Can you reach 95% efficiency with 8 signals?

**Questions?** See [Troubleshooting Guide](../guides/troubleshooting.md)

---

**Generated with:** moku-instrument-forge v0.1.0
**Last updated:** 2025-11-03
