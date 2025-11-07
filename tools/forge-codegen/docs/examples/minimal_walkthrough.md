# Minimal Probe Walkthrough

**Purpose:** Deep dive into the simplest possible moku-instrument-forge specification

**Audience:** New users learning the system from first principles

**Time:** 20 minutes

---

## Overview

This walkthrough explains every line of `minimal_probe.yaml`, the simplest possible custom instrument specification. You'll learn:

- How to choose appropriate types for your signals
- How register mapping automatically optimizes bit packing
- What VHDL and metadata files are generated
- How to interpret the register efficiency metrics

**Prerequisites:** Read [Getting Started](../guides/getting_started.md) first.

---

## Complete Spec

**File:** `docs/examples/minimal_probe.yaml`

```yaml
app_name: minimal_probe
version: 1.0.0
description: My first custom instrument
platform: moku_go

datatypes:
  - name: output_voltage
    datatype: voltage_output_05v_s16
    description: Output voltage setpoint
    default_value: 0
    units: V

  - name: enable_output
    datatype: boolean
    description: Enable output driver
    default_value: false

  - name: pulse_width
    datatype: pulse_duration_ms_u16
    description: Pulse width in milliseconds
    default_value: 100
    units: ms
```

**What this spec defines:**
- **3 control signals** for a voltage output instrument
- **Automatic register packing** (3 signals → 2 registers)
- **Type-safe interface** using BasicAppDataTypes

---

## Line-by-Line Explanation

### Top-Level Fields

```yaml
app_name: minimal_probe
```
**Purpose:** Unique identifier for your instrument
**Rules:**
- Must be valid Python/VHDL identifier (alphanumeric + underscores)
- Used for file naming (`minimal_probe_shim.vhd`, `minimal_probe_main.vhd`)
- Appears in generated comments and manifests

**Example alternatives:** `voltage_controller`, `probe_v2`, `test_instrument`

---

```yaml
version: 1.0.0
```
**Purpose:** Semantic version for your instrument
**Format:** `MAJOR.MINOR.PATCH` (follows [semver](https://semver.org/))
**Use cases:**
- Track changes across iterations
- CloudCompile bitstream versioning (future feature)
- Deployment management

---

```yaml
description: My first custom instrument
```
**Purpose:** Human-readable description
**Usage:**
- Appears in generated VHDL comments
- Included in manifest.json
- Helps document the instrument's purpose

**Best practice:** Be specific! Good: "2-channel EMFI probe controller with safety interlocks"
Bad: "My app"

---

```yaml
platform: moku_go
```
**Purpose:** Target hardware platform
**Valid values:**
- `moku_go` - Moku:Go (125 MHz, 2 slots)
- `moku_lab` - Moku:Lab (500 MHz, 2 slots)
- `moku_pro` - Moku:Pro (1.25 GHz, 4 slots)
- `moku_delta` - Moku:Delta (5 GHz, 3 slots)

**Impact:**
- Clock frequency for time conversions (nanoseconds → cycles)
- Platform-specific VHDL generics
- Available ADC/DAC ranges

**Note:** BasicAppDataTypes are platform-agnostic (same types work on all platforms), but time/voltage conversions are platform-aware.

---

### Signal 1: output_voltage

```yaml
  - name: output_voltage
```
**Purpose:** Variable name for this signal
**Rules:**
- Snake_case convention (Python/VHDL compatible)
- Must be unique within the spec
- Becomes VHDL signal name: `signal output_voltage : signed(15 downto 0);`

**Why `output_voltage` not `voltage`?** Be descriptive! If you add input voltage later, `voltage` becomes ambiguous.

---

```yaml
    datatype: voltage_output_05v_s16
```
**Purpose:** Type from BasicAppDataTypes type system
**Breakdown:**
- `voltage` - Category (voltage, not time/boolean)
- `output` - Output range (DAC, not ADC input)
- `05v` - ±5V range (Moku:Go DAC output range)
- `s16` - Signed 16-bit integer

**Range:** -32768 to +32767 → maps to -5.0V to +5.0V
**Resolution:** 5.0V / 32768 ≈ 0.15 mV per step

**Alternatives:**
- `voltage_output_025v_s16` - Smaller range (±2.5V), same resolution
- `voltage_output_05v_u15` - Unsigned (0 to +5V), saves 1 bit

**See:** [Type System Reference](../reference/type_system.md) for all 23 types

---

```yaml
    description: Output voltage setpoint
```
**Purpose:** Human-readable explanation
**Usage:**
- VHDL comments
- Generated documentation
- Python API docstrings (future feature)

---

```yaml
    default_value: 0
```
**Purpose:** Initial value on FPGA boot/reset
**Type:** Integer (millivolts for voltage types)
**Value:** `0` = 0 mV = 0.0V (safe default)

**Why 0?** Safe defaults prevent hardware damage on boot. For a high-voltage output, defaulting to 5V could be dangerous!

**Type constraints:** Must be within type range (-5000 to +5000 mV for this type)

---

```yaml
    units: V
```
**Purpose:** Display units for UI/documentation
**Optional:** If omitted, uses type default (`mV` for voltage types)
**Override:** We specify `V` for cleaner display (2.5 V vs 2500 mV)

**Usage:**
- TUI/GUI sliders
- Generated documentation
- Python API hints

---

### Signal 2: enable_output

```yaml
  - name: enable_output
    datatype: boolean
    description: Enable output driver
    default_value: false
```

**Type:** `boolean` - Single-bit flag (0 or 1)
**Why boolean?** Unlike some systems with `boolean8` (wastes 7 bits), BasicAppDataTypes has only 1-bit boolean.

**Default:** `false` (0) = Output disabled on boot (safe!)

**Best practice:** For safety-critical signals (high voltage, lasers, etc.), always default to OFF/false.

---

### Signal 3: pulse_width

```yaml
  - name: pulse_width
    datatype: pulse_duration_ms_u16
    description: Pulse width in milliseconds
    default_value: 100
    units: ms
```

**Type:** `pulse_duration_ms_u16` - Time duration in milliseconds
**Breakdown:**
- `pulse_duration` - Time category
- `ms` - Milliseconds (not ns/us/s)
- `u16` - Unsigned 16-bit integer

**Range:** 0 to 65535 ms (0 to 65.5 seconds)
**Default:** 100 ms (0.1 seconds)

**Why milliseconds?** Human-scale timing. For FPGA-scale timing (ADC settling), use nanoseconds (`pulse_duration_ns_u8`).

**Alternatives:**
- `pulse_duration_us_u16` - Microseconds (0-65 ms range)
- `pulse_duration_s_u16` - Seconds (0-65535 seconds ≈ 18 hours!)

---

## Register Mapping

Running `best_fit` strategy (default):

```
CR6: [output_voltage(16) | pulse_width(16)] = 32/32 bits (100% full)
CR7: [enable_output(1)]                     = 1/32 bits (3% used)

Total: 2 registers
Bits used: 33/64 bits = 51.6% efficiency
Registers saved: 1 (vs 3 registers with one-per-signal)
```

### Mapping Strategy

**Algorithm:** `best_fit` packs signals to minimize wasted space

**Step 1:** Sort signals by size (largest first)
1. `output_voltage` - 16 bits
2. `pulse_width` - 16 bits
3. `enable_output` - 1 bit

**Step 2:** Pack into registers (32 bits each)
- **CR6:** `output_voltage` (16) + `pulse_width` (16) = 32 bits (perfect fit!)
- **CR7:** `enable_output` (1) = 1 bit (31 bits wasted)

**Result:** 2 registers instead of 3 (33% savings)

### Why Not 100% Efficient?

**CR7 wastes 31 bits** because:
1. Boolean is only 1 bit
2. No other signals to pack with it
3. Cannot split signals across registers (architectural constraint)

**How to improve?** Add more signals! If you had 31 more booleans, they'd pack into CR7 for free.

### Bit Layout (Little-Endian)

```
CR6 (32 bits):
┌────────────────┬────────────────┐
│ output_voltage │  pulse_width   │
│    [31:16]     │     [15:0]     │
│    16 bits     │    16 bits     │
└────────────────┴────────────────┘

CR7 (32 bits):
┌─┬──────────────────────────────┐
│1│       (unused)               │
│ │                              │
│ │           30 bits            │
└─┴──────────────────────────────┘
 ^
 enable_output [31]
```

**Note:** Boolean is MSB-aligned (bit 31), not LSB (bit 0). This is Moku architecture convention.

---

## Generated VHDL

### Shim Entity

**File:** `output/minimal_probe/minimal_probe_shim.vhd`

```vhdl
-- Auto-generated control register interface
-- DO NOT EDIT: Regenerate from YAML spec
--
-- Generated: 2025-11-03
-- Platform: Moku:Go (125 MHz)
-- Registers: 2 (CR6-CR7)
-- Efficiency: 51.6%

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

-- Type packages (from basic-app-datatypes submodule)
use WORK.basic_app_types_pkg.all;
use WORK.basic_app_voltage_pkg.all;
use WORK.basic_app_time_pkg.all;

entity minimal_probe_shim is
  generic (
    CLK_FREQ_HZ : integer := 125000000  -- Moku:Go @ 125 MHz
  );
  port (
    -- System
    clk : in std_logic;
    rst : in std_logic;

    -- Control register inputs (from Moku framework)
    control_6_in : in std_logic_vector(31 downto 0);
    control_7_in : in std_logic_vector(31 downto 0);

    -- Unpacked signals (to your instrument logic)
    output_voltage : out signed(15 downto 0);      -- ±5V (mV)
    enable_output  : out std_logic;                -- Boolean
    pulse_width    : out unsigned(15 downto 0);    -- 0-65535 ms

    -- ... additional ports for data streams, triggers, etc.
  );
end entity;

architecture rtl of minimal_probe_shim is
begin
  -- Unpack control registers (combinatorial)
  output_voltage <= signed(control_6_in(31 downto 16));
  pulse_width    <= unsigned(control_6_in(15 downto 0));
  enable_output  <= control_7_in(31);

  -- TODO: Add synchronizers for clock domain crossing (if needed)
  -- TODO: Add type converters (if scaling required)
end architecture;
```

**Key points:**
1. **Do not edit shim!** Regenerate from YAML if you change types
2. **Unpacking is simple bit-slicing** - No complex logic
3. **Type conversion happens elsewhere** (Python or VHDL main logic)

### Main Template

**File:** `output/minimal_probe/minimal_probe_main.vhd`

```vhdl
-- Custom instrument logic (USER EDITABLE)
--
-- This is YOUR code. Implement your instrument behavior here.

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity minimal_probe_main is
  generic (
    CLK_FREQ_HZ : integer := 125000000
  );
  port (
    clk : in std_logic;
    rst : in std_logic;

    -- Control signals (from shim)
    output_voltage : in signed(15 downto 0);
    enable_output  : in std_logic;
    pulse_width    : in unsigned(15 downto 0);

    -- DAC output (to Moku hardware)
    dac_out : out signed(15 downto 0)
  );
end entity;

architecture rtl of minimal_probe_main is
  -- Your internal signals here
  signal pulse_active : std_logic := '0';
  signal pulse_counter : unsigned(31 downto 0) := (others => '0');
begin

  -- Example: Simple pulse generator
  process(clk)
  begin
    if rising_edge(clk) then
      if rst = '1' then
        pulse_active <= '0';
        pulse_counter <= (others => '0');
        dac_out <= (others => '0');
      else
        -- TODO: Implement pulse logic using pulse_width
        -- TODO: Drive DAC based on output_voltage and enable_output

        if enable_output = '1' then
          dac_out <= output_voltage;  -- Direct passthrough (example)
        else
          dac_out <= (others => '0');  -- Output disabled
        end if;
      end if;
    end if;
  end process;

end architecture;
```

**Key points:**
1. **Main is YOUR code** - Implement custom logic here
2. **Shim provides typed signals** - No manual bit-slicing needed
3. **Platform constants available** - `CLK_FREQ_HZ` for time calculations

---

## Generated manifest.json

**File:** `output/minimal_probe/manifest.json`

```json
{
  "app_name": "minimal_probe",
  "version": "1.0.0",
  "description": "My first custom instrument",
  "platform": "moku_go",
  "generated_at": "2025-11-03T10:30:00Z",

  "datatypes": [
    {
      "name": "output_voltage",
      "datatype": "VOLTAGE_OUTPUT_05V_S16",
      "description": "Output voltage setpoint",
      "default_value": 0,
      "units": "V",
      "register_number": 6,
      "bit_range": "31:16",
      "vhdl_type": "signed(15 downto 0)"
    },
    {
      "name": "pulse_width",
      "datatype": "PULSE_DURATION_MS_U16",
      "description": "Pulse width in milliseconds",
      "default_value": 100,
      "units": "ms",
      "register_number": 6,
      "bit_range": "15:0",
      "vhdl_type": "unsigned(15 downto 0)"
    },
    {
      "name": "enable_output",
      "datatype": "BOOLEAN",
      "description": "Enable output driver",
      "default_value": false,
      "register_number": 7,
      "bit_range": "31",
      "vhdl_type": "std_logic"
    }
  ],

  "register_mapping": {
    "strategy": "best_fit",
    "registers": [
      {
        "register_number": 6,
        "signals": ["output_voltage", "pulse_width"],
        "bits_used": 32
      },
      {
        "register_number": 7,
        "signals": ["enable_output"],
        "bits_used": 1
      }
    ]
  },

  "efficiency": {
    "total_bits_used": 33,
    "total_bits_allocated": 64,
    "percentage": 51.6,
    "registers_used": 2,
    "registers_saved": 1,
    "comment": "2 registers instead of 3 (one-per-signal)"
  }
}
```

**Usage:**
- **deployment-context**: Reads this to initialize control registers
- **docgen-context**: Uses this to generate documentation
- **hardware-debug-context**: References this for FSM state decoding

**This manifest is the source of truth** for all downstream consumers.

**See:** [Manifest Schema Reference](../reference/manifest_schema.md)

---

## Deployment (Conceptual)

**Note:** Automated deployment via CloudCompile is in progress. This shows the conceptual workflow.

```python
from moku.instruments import CustomInstrument
import json

# 1. Connect to Moku device
instr = CustomInstrument('192.168.1.100', 'minimal_probe')

# 2. Load manifest (deployment-context would do this automatically)
with open('output/minimal_probe/manifest.json') as f:
    manifest = json.load(f)

# 3. Initialize control registers with default values
for signal in manifest['datatypes']:
    reg_num = signal['register_number']
    default_val = signal['default_value']
    # Write to control register (conceptual API)
    # instr.set_control_register(reg_num, value)

# 4. Set runtime values (Python API - conceptual)
instr.set_parameter('output_voltage', 2.5)   # 2.5V
instr.set_parameter('enable_output', True)   # Enable
instr.set_parameter('pulse_width', 500)      # 500 ms

# 5. Read back parameters
voltage = instr.get_parameter('output_voltage')
print(f"Output voltage: {voltage} V")  # 2.5 V
```

**See:** [Deployment Guide](../guides/deployment_guide.md) (when available)

---

## Variations

### What if we used different types?

#### Variation 1: Unsigned voltage (0 to +5V only)

```yaml
  - name: output_voltage
    datatype: voltage_output_05v_u15  # Changed: s16 → u15
    description: Output voltage (0 to +5V only)
    default_value: 0
    units: V
```

**Impact:**
- **Bit width:** 15 bits (not 16)
- **Register layout:** CR6 still has 32 bits, but now 17 bits used (voltage 15 + pulse 16)
- **Range:** 0 to +5V (no negative voltages)
- **Efficiency:** Slightly worse (need to handle 1 unused bit)

**When to use:** If your circuit only needs positive voltages, saves 1 bit.

#### Variation 2: Shorter pulse width (microseconds)

```yaml
  - name: pulse_width
    datatype: pulse_duration_us_u16  # Changed: ms → us
    description: Pulse width in microseconds
    default_value: 100000  # 100ms = 100,000 us
    units: us
```

**Impact:**
- **Bit width:** Still 16 bits
- **Range:** 0-65535 µs (0-65.5 ms) - Much shorter!
- **Resolution:** 1 µs per step (finer control)
- **Register layout:** Unchanged

**When to use:** Fast pulses (ADC sampling, trigger delays)

---

## Lessons Learned

### Type Selection

✅ **DO:**
- Use narrowest type that fits your range (`u8` for 0-255, not `u16`)
- Choose units that match your domain (ms for human-scale, ns for FPGA-scale)
- Use signed types only if you need negative values

❌ **DON'T:**
- Use oversized types (wastes bits)
- Mix units carelessly (milliseconds for nanosecond timing)
- Forget about default values (safety!)

### Register Efficiency

- **51.6% efficiency** is typical for small specs (few signals)
- **To improve:** Add more signals (fill CR7's 31 unused bits)
- **Diminishing returns:** Beyond 6-8 signals, efficiency plateaus at 70-90%

### Safety

- **Default to OFF:** `enable_output = false` (not true)
- **Default to zero:** `output_voltage = 0` (not 5V)
- **Add constraints:** Use `min_value`/`max_value` to prevent dangerous values

---

## Next Steps

**You've mastered the basics!** Now explore:

1. **[Multi-Channel Walkthrough](multi_channel_walkthrough.md)** - 6 signals, 90.6% efficiency
2. **[Common Patterns](common_patterns.md)** - Reusable design patterns catalog
3. **[Type System Reference](../reference/type_system.md)** - All 23 types explained
4. **[Register Mapping](../reference/register_mapping.md)** - Algorithm deep dive

**Build something!** Try modifying this spec:
- Add a trigger threshold (`voltage_input_25v_s16`)
- Add a timeout (`pulse_duration_s_u8`)
- Add a safety flag (`boolean`)

**Questions?** See [Troubleshooting Guide](../guides/troubleshooting.md)

---

**Generated with:** moku-instrument-forge v0.1.0
**Last updated:** 2025-11-03
