# Register Mapping Algorithms

**Automatic register packing strategies for optimal bit usage.**

moku-instrument-forge provides 3 algorithms for packing typed signals into Control Registers (CR6-CR15). Automatic packing achieves **50-75% space savings** compared to naive one-signal-per-register allocation.

---

## Overview

### Why Automatic Packing Matters

**Problem:** Moku platforms provide 12 control registers (CR4-CR15) for custom instruments. Each register is 32 bits. Naive allocation (one signal per register) wastes significant space.

**Example:**
- 3 signals: 16-bit voltage, 16-bit time, 1-bit boolean
- Naive allocation: 3 registers, 33/96 bits used (34% efficient)
- Optimized packing: 2 registers, 33/64 bits used (52% efficient)
- **Savings:** 1 register saved (18% reduction)

**Benefits:**
- **More signals:** Fit more typed values in 12-register limit
- **Reduced errors:** No manual bit-slicing math
- **Maintainability:** Change signal types without recalculating offsets

**See also:** [Type System Reference](type_system.md) for signal type details.

---

## Available Strategies

moku-instrument-forge provides 3 packing strategies, selectable via `mapping_strategy` in YAML:

| Strategy | Time Complexity | Use Case | Efficiency |
|----------|----------------|----------|-----------|
| `first_fit` | O(n) | Testing only | Low (naive) |
| `best_fit` | O(n²) | Maximum density needed | High |
| `type_clustering` | O(n log n) | **Default (recommended)** | High |

### Choosing a Strategy

**Use `type_clustering` (default) for:**
- Most applications (best balance of efficiency and predictability)
- When register order predictability matters (groups same-width types)
- Standard use cases

**Use `best_fit` for:**
- Applications with many mixed bit widths
- When maximum packing density is critical
- Research/experimentation with packing efficiency

**Use `first_fit` for:**
- Testing and debugging only (not recommended for production)
- Understanding baseline packing behavior

**Specify in YAML:**
```yaml
app_name: my_instrument
platform: moku_pro
mapping_strategy: type_clustering  # Optional, this is the default
datatypes:
  # ...
```

---

## Strategy 1: `first_fit` (Naive)

### Algorithm

1. Initialize 12 empty registers (CR4-CR15), each with 32 bits available
2. For each signal (in YAML order):
   - Find first register with enough space
   - Allocate signal in that register (MSB-aligned packing)
   - Update remaining space
3. If no register has space, raise overflow error

**Time Complexity:** O(n) - single pass through signals

**Characteristics:**
- Simple, predictable behavior
- Poor packing efficiency (similar to manual allocation)
- Large wasted space with mixed bit widths

### Example

**Input (3 signals):**
```yaml
datatypes:
  - name: voltage_16bit
    datatype: voltage_output_05v_s16  # 16 bits
  - name: time_16bit
    datatype: pulse_duration_ns_u16   # 16 bits
  - name: flag
    datatype: boolean                 # 1 bit
```

**Register Layout (first_fit):**
```
CR6: [voltage_16bit................] 16/32 bits used (50% efficient)
     |<--- 16 bits --->|<--unused-->|
     MSB              LSB

CR7: [time_16bit...................] 16/32 bits used (50% efficient)
     |<--- 16 bits --->|<--unused-->|

CR8: [flag.........................] 1/32 bits used (3% efficient)
     |1|<----- unused ------------>|

Total: 3 registers used
Total bits: 33 bits used / 96 bits allocated = 34% efficient
Wasted: 63 bits (66%)
```

**Problems:**
- Each signal gets its own register despite available space
- 1-bit boolean wastes an entire 32-bit register
- Poor utilization with small signals

---

## Strategy 2: `best_fit` (Optimized)

### Algorithm

1. Initialize 12 empty registers (CR4-CR15), each with 32 bits available
2. For each signal (in YAML order):
   - Find register with **smallest remaining space** that fits signal
   - Allocate signal in that register (MSB-aligned packing)
   - Update remaining space
3. If no register has space, raise overflow error

**Time Complexity:** O(n²) - for each signal, scan all registers

**Characteristics:**
- Maximizes packing density
- Fills gaps efficiently
- Less predictable register assignments (depends on signal order)

### Example

**Input (same 3 signals):**
```yaml
datatypes:
  - name: voltage_16bit
    datatype: voltage_output_05v_s16  # 16 bits
  - name: time_16bit
    datatype: pulse_duration_ns_u16   # 16 bits
  - name: flag
    datatype: boolean                 # 1 bit
```

**Register Layout (best_fit):**
```
CR6: [voltage_16bit|time_16bit.....] 32/32 bits used (100% efficient)
     |<--- 16 --->|<--- 16 --->|
     MSB                      LSB

CR7: [flag.........................] 1/32 bits used (3% efficient)
     |1|<----- unused ------------>|

Total: 2 registers used
Total bits: 33 bits used / 64 bits allocated = 52% efficient
Savings: 1 register saved (33% reduction vs first_fit)
```

**How it works:**
1. `voltage_16bit` → CR6 (empty, 32 bits available)
2. `time_16bit` → CR6 (smallest fit: 16 bits remaining in CR6)
3. `flag` → CR7 (no space in CR6, use next register)

**Advantages:**
- Fills gaps efficiently (packed 2 × 16-bit into one register)
- Good density for mixed bit widths

**Disadvantages:**
- Register assignments less predictable (depends on signal order and prior allocations)

---

## Strategy 3: `type_clustering` (Default)

### Algorithm

1. **Group signals by bit width** (16-bit together, 8-bit together, etc.)
2. **Sort groups by bit width** (descending: 32-bit, 24-bit, 16-bit, 8-bit, 1-bit)
3. **Pack each group using best_fit** within that group
4. Move to next register when current register full or no more signals in group fit

**Time Complexity:** O(n log n) - sorting dominates

**Characteristics:**
- Predictable grouping (same-width types together)
- High packing efficiency (comparable to best_fit)
- Easier to debug (signals grouped by type)

### Example

**Input (6 signals, mixed widths):**
```yaml
datatypes:
  - name: dac_ch1
    datatype: voltage_output_05v_s16  # 16 bits
  - name: dac_ch2
    datatype: voltage_output_05v_s16  # 16 bits
  - name: glitch_width
    datatype: pulse_duration_ns_u16   # 16 bits
  - name: delay
    datatype: pulse_duration_us_u8    # 8 bits
  - name: enable_ch1
    datatype: boolean                 # 1 bit
  - name: enable_ch2
    datatype: boolean                 # 1 bit
```

**Register Layout (type_clustering):**
```
Grouping:
  16-bit group: dac_ch1, dac_ch2, glitch_width
  8-bit group:  delay
  1-bit group:  enable_ch1, enable_ch2

CR6: [dac_ch1|dac_ch2..............] 32/32 bits used (100% efficient)
     |<- 16 ->|<- 16 ->|
     MSB              LSB

CR7: [glitch_width|delay|en_ch1|en_ch2|....] 26/32 bits used (81% efficient)
     |<--- 16 --->|<8>|1|1|<-unused->|
     MSB                            LSB

Total: 2 registers used
Total bits: 58 bits used / 64 bits allocated = 91% efficient
Savings: Highly efficient packing with predictable grouping
```

**How it works:**
1. **Group by width:** {16: [dac_ch1, dac_ch2, glitch_width], 8: [delay], 1: [enable_ch1, enable_ch2]}
2. **Process 16-bit group:**
   - dac_ch1 → CR6 (empty)
   - dac_ch2 → CR6 (16 bits remaining, perfect fit)
   - glitch_width → CR7 (no space in CR6)
3. **Process 8-bit group:**
   - delay → CR7 (16 bits remaining, fits)
4. **Process 1-bit group:**
   - enable_ch1 → CR7 (8 bits remaining, fits)
   - enable_ch2 → CR7 (7 bits remaining, fits)

**Advantages:**
- **Predictable:** Same-width signals grouped together
- **Efficient:** Fills registers well (81-100% per register)
- **Debuggable:** Easy to find signals (all voltage types in same registers)

**Why it's the default:**
- Best balance of efficiency and predictability
- Works well for typical signal distributions
- Easier to debug (groups are logical)

---

## Visual Comparison

**Same 6-signal example with all 3 strategies:**

### Input Signals

```
dac_ch1       (16 bits) - voltage_output_05v_s16
dac_ch2       (16 bits) - voltage_output_05v_s16
glitch_width  (16 bits) - pulse_duration_ns_u16
delay         (8 bits)  - pulse_duration_us_u8
enable_ch1    (1 bit)   - boolean
enable_ch2    (1 bit)   - boolean

Total: 58 bits
```

### first_fit (naive)

```
CR6: [dac_ch1..................] 16/32 bits (50%)
CR7: [dac_ch2..................] 16/32 bits (50%)
CR8: [glitch_width.............] 16/32 bits (50%)
CR9: [delay....................] 8/32 bits  (25%)
CR10:[enable_ch1...............] 1/32 bits  (3%)
CR11:[enable_ch2...............] 1/32 bits  (3%)

Registers used: 6
Total allocated: 192 bits
Efficiency: 58/192 = 30%
```

### best_fit (maximum density)

```
CR6: [dac_ch1|dac_ch2..........] 32/32 bits (100%)
CR7: [glitch_width|delay|e1|e2.] 26/32 bits (81%)

Registers used: 2
Total allocated: 64 bits
Efficiency: 58/64 = 91%
```

### type_clustering (default)

```
CR6: [dac_ch1|dac_ch2..........] 32/32 bits (100%)
CR7: [glitch_width|delay|e1|e2.] 26/32 bits (81%)

Registers used: 2
Total allocated: 64 bits
Efficiency: 58/64 = 91%
```

**Result:** type_clustering achieves same efficiency as best_fit, but with more predictable grouping.

---

## Efficiency Metrics

The generated `manifest.json` includes packing efficiency metrics:

```json
{
  "efficiency": {
    "total_bits_used": 58,
    "total_bits_allocated": 64,
    "registers_used": 2,
    "packing_efficiency_percent": 90.6,
    "registers_saved": 4
  }
}
```

**Metrics Explained:**
- **`total_bits_used`** - Sum of all signal bit widths (58 bits)
- **`total_bits_allocated`** - Registers used × 32 bits (2 × 32 = 64 bits)
- **`registers_used`** - Number of CRs consumed (2 registers: CR6, CR7)
- **`packing_efficiency_percent`** - (bits_used / bits_allocated) × 100 (90.6%)
- **`registers_saved`** - Registers saved vs one-per-signal (6 signals - 2 used = 4 saved)

**Typical Efficiency Ranges:**
- `first_fit`: 25-40% (poor)
- `best_fit`: 70-95% (excellent)
- `type_clustering`: 70-95% (excellent)

**See also:** [Manifest Schema Reference](manifest_schema.md) for complete manifest.json format.

---

## Register Assignment

### Control Register Range

Moku platforms provide **12 control registers** for custom instruments:

- **Available:** CR4, CR5, CR6, CR7, CR8, CR9, CR10, CR11, CR12, CR13, CR14, CR15
- **Each register:** 32 bits
- **Total capacity:** 12 × 32 = 384 bits

**Note:** CR0-CR3 are reserved by the platform and cannot be used for custom signals.

### Bit Ordering (MSB-Aligned Packing)

Signals are packed MSB-aligned within each register:

```
Register (32 bits):
┌─────────────────────────────────┐
│ MSB                        LSB  │
│ Bit 31 ← ← ← ← ← ← ← ← → Bit 0 │
└─────────────────────────────────┘

First signal starts at MSB (bit 31)
Next signal follows immediately
Unused bits remain at LSB (bit 0)
```

**Example (2 signals: 16-bit + 8-bit):**
```
CR6:
┌────────────────────────────────┐
│ signal1 (16) │ signal2 (8) │ unused (8) │
│ bits 31-16   │ bits 15-8   │ bits 7-0   │
└────────────────────────────────┘
```

**VHDL Bit Slicing:**
```vhdl
signal1 <= control_register_6(31 downto 16);  -- 16 bits
signal2 <= control_register_6(15 downto 8);   -- 8 bits
-- bits 7-0 unused
```

---

## Manual Override

### Specifying Strategy in YAML

Override the default `type_clustering` strategy:

```yaml
app_name: my_instrument
version: 1.0.0
platform: moku_pro
mapping_strategy: best_fit  # Override default

datatypes:
  # ...
```

### When to Override

**Use `best_fit` when:**
- Maximizing register density is critical
- You have many signals with varied bit widths
- Predictability of register layout is not important

**Use `first_fit` when:**
- Debugging packing behavior
- Comparing against naive allocation
- Not recommended for production

**Use `type_clustering` (default) when:**
- Standard use case (recommended 95% of the time)
- You want predictable grouping by type
- High efficiency with clear organization

---

## Limitations and Constraints

### Hard Limits

1. **Maximum 12 registers:** CR4-CR15 (384 bits total)
2. **Maximum signal width:** 32 bits (one full register)
3. **Minimum signal width:** 1 bit (boolean)

### Validation

The Pydantic validator checks:
- **Total bits <= 384 bits** (12 registers × 32 bits)
- **Each signal <= 32 bits** (enforced by BasicAppDataTypes type system)

**Validation Error Example:**
```python
# 25 × 16-bit signals = 400 bits
ValidationError: Total bits (400) exceeds 384-bit limit
```

### Overflow Handling

If signals don't fit in 12 registers:
1. **Validation fails** at YAML parse time
2. **Error message** shows total bits and limit
3. **Solution:** Reduce signal count or use smaller bit widths

---

## Implementation Details

### Python API

Mapping is handled by the `BADRegisterMapper` class:

```python
from forge.models.mapper import BADRegisterMapper
from forge.models.package import BasicAppsRegPackage

# Load YAML
package = BasicAppsRegPackage.from_yaml('specs/my_instrument.yaml')

# Generate mapping (uses strategy from YAML)
mappings = package.generate_mapping()

# Inspect results
for mapping in mappings:
    print(f"{mapping.name}: CR{mapping.cr_number}, bits {mapping.bit_slice}")

# Example output:
# dac_ch1: CR6, bits (31, 16)
# dac_ch2: CR6, bits (15, 0)
# glitch_width: CR7, bits (31, 16)
```

**See also:** [Python API Reference](python_api.md) for programmatic access.

### Core Algorithm

The core mapping algorithm is in `basic-app-datatypes` library:

- **Location:** `libs/basic-app-datatypes/basic_app_datatypes/mapper.py`
- **Class:** `RegisterMapper`
- **Methods:**
  - `map(items, strategy)` - Apply packing algorithm
  - `generate_report(mappings)` - Produce efficiency report

**Integration:**
- `forge/models/mapper.py` - Pydantic wrapper (`BADRegisterMapper`)
- `forge/models/package.py` - YAML integration (`BasicAppsRegPackage`)

---

## Related Documentation

- **[Type System Reference](type_system.md)** - Signal types and bit widths
- **[YAML Schema Reference](yaml_schema.md)** - How to specify `mapping_strategy`
- **[Manifest Schema Reference](manifest_schema.md)** - Output format with efficiency metrics
- **[Python API Reference](python_api.md)** - Programmatic access to mapper
- **[Examples - Register Packing](../examples/common_patterns.md#register-optimization)** - Practical packing patterns

---

**Key Takeaway:** moku-instrument-forge provides 3 automatic packing strategies. Use `type_clustering` (default) for best balance of efficiency (70-95%) and predictability. Manual bit-slicing is eliminated, and space savings are typically 50-75% compared to naive allocation.

---

*Last Updated: 2025-11-03*
