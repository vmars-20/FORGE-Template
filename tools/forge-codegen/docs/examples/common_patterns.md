# Common Patterns

**Purpose:** Reusable design patterns for YAML instrument specifications

**Audience:** Users building custom instruments

**Contents:** 6 battle-tested patterns with examples and rationale

---

## How to Use This Guide

Each pattern includes:
- **Use Case:** When to apply this pattern
- **Pattern:** YAML snippet (copy-paste ready)
- **Why:** Design rationale and benefits
- **Variations:** Alternative approaches
- **See Also:** Related documentation

**Tip:** Combine multiple patterns in one spec! For example, Pattern 1 (FSM) + Pattern 5 (Safety) + Pattern 6 (Optimization).

---

## Pattern 1: FSM Control Signals

**Use Case:** Controlling a finite state machine (FSM) with states, triggers, and resets

### Pattern

```yaml
datatypes:
  # FSM state (for debugging/monitoring)
  - name: fsm_state
    datatype: pulse_duration_ns_u8  # Repurpose: 8 bits = 256 states
    description: Current FSM state (read-only via status register)
    default_value: 0  # IDLE state

  # FSM control
  - name: fsm_trigger
    datatype: boolean
    description: Trigger FSM transition (edge-sensitive)
    default_value: false

  - name: fsm_reset
    datatype: boolean
    description: Reset FSM to IDLE state
    default_value: false
```

### Why This Works

**State encoding:**
- Use `u8` (8 bits) for state → supports up to 256 states
- Default value 0 → IDLE state
- **Not boolean!** FSMs typically have 3+ states (IDLE, ARMED, FIRING, COOLING, ERROR, etc.)

**Trigger vs Reset:**
- **Trigger:** Advances FSM to next state (edge-sensitive in VHDL)
- **Reset:** Returns to IDLE (safety escape hatch)
- **Both boolean:** Single-bit flags (efficient packing)

**Alternative types:**
- `pulse_duration_ns_u16` - Supports 65,536 states (overkill for most FSMs)
- `pulse_duration_ns_u8` - Sweet spot (256 states, only 8 bits)

### VHDL Implementation Snippet

```vhdl
type fsm_state_t is (IDLE, ARMED, FIRING, COOLING, ERROR);
signal current_state : fsm_state_t := IDLE;
signal fsm_state_int : unsigned(7 downto 0);

-- Convert enum to integer for status register
fsm_state_int <= to_unsigned(fsm_state_t'pos(current_state), 8);

-- FSM logic
process(clk)
begin
  if rising_edge(clk) then
    if fsm_reset = '1' then
      current_state <= IDLE;
    elsif fsm_trigger = '1' then
      case current_state is
        when IDLE => current_state <= ARMED;
        when ARMED => current_state <= FIRING;
        when FIRING => current_state <= COOLING;
        when COOLING => current_state <= IDLE;
        when ERROR => current_state <= IDLE;
      end case;
    end if;
  end if;
end process;
```

### See Also

- **[FSM Observer Pattern](../debugging/fsm_observer_pattern.md)** - Debugging FSMs with voltage-encoded states
- **[Troubleshooting: FSM stuck in state](../guides/troubleshooting.md#fsm-stuck)**

---

## Pattern 2: Voltage Parameters

**Use Case:** Controlling DAC outputs and ADC trigger thresholds

### Pattern

```yaml
datatypes:
  # DAC output (physical units)
  - name: output_voltage
    datatype: voltage_output_05v_s16
    description: DAC output voltage
    default_value: 0  # 0 mV = 0.0 V
    units: V
    min_value: -5.0
    max_value: 5.0

  # ADC threshold (for comparisons)
  - name: trigger_threshold
    datatype: voltage_input_25v_s16
    description: ADC trigger threshold
    default_value: 1000  # 1000 mV = 1.0 V
    units: V
    min_value: -25.0
    max_value: 25.0
```

### Why Different Types?

**Output vs Input:**
- **`voltage_output_*`**: DAC output ranges (Moku:Go ±5V, Moku:Lab ±1V, Moku:Pro ±5V)
- **`voltage_input_*`**: ADC input ranges (Moku:Go ±25V, Moku:Lab ±5V, Moku:Pro ±20V)

**Type mismatch prevention:**
Using distinct types prevents errors like:
- ❌ Setting DAC to ±25V (would damage hardware!)
- ✅ Type system enforces correct ranges

**Platform-specific ranges:**

| Platform | DAC Output | ADC Input |
|----------|------------|-----------|
| Moku:Go | ±5V | ±25V |
| Moku:Lab | ±1V | ±5V |
| Moku:Pro | ±5V | ±20V |
| Moku:Delta | ±5V | ±20V |

**Choose type based on your platform!**

### Safety Constraints

```yaml
min_value: 0.0      # Prevent negative voltages (if circuit can't handle)
max_value: 3.3      # Hardware limit (not full ±5V range!)
```

**When to use:**
- Circuits with limited voltage tolerance (e.g., 3.3V logic)
- Safety interlocks (prevent operator errors)
- Calibration boundaries

### Variations

**High-precision output (smaller range):**
```yaml
- name: precision_output
  datatype: voltage_output_025v_s16  # ±2.5V (not ±5V)
  description: High-precision output
  # Resolution: 2.5V / 32768 ≈ 0.08 mV (2x better than ±5V)
```

**Unsigned output (0 to +5V only):**
```yaml
- name: positive_output
  datatype: voltage_output_05v_u15  # 0 to +5V (15 bits)
  description: Positive-only output
  # Saves 1 bit (no sign bit)
```

### See Also

- **[Type System: Voltage Types](../reference/type_system.md#voltage-types)**
- **[Platform Specifications](../../libs/moku-models/docs/platform_specs.md)**

---

## Pattern 3: Timing Configuration

**Use Case:** Different time scales for human vs FPGA timing

### Pattern

```yaml
datatypes:
  # Long delays (human-scale)
  - name: pulse_duration
    datatype: pulse_duration_ms_u16
    description: Pulse duration in milliseconds
    default_value: 100
    units: ms
    min_value: 10      # Minimum 10 ms
    max_value: 10000   # Maximum 10 seconds

  # Short delays (FPGA-scale)
  - name: settling_time
    datatype: pulse_duration_ns_u8
    description: ADC settling time in nanoseconds
    default_value: 10
    units: ns
    min_value: 1
    max_value: 255

  # Very short delays (precision timing)
  - name: trigger_delay
    datatype: pulse_duration_ns_u16
    description: Trigger delay in nanoseconds
    default_value: 100
    units: ns
    min_value: 0
    max_value: 65535
```

### Why Different Time Scales?

**Milliseconds (ms):**
- **Use for:** User-controlled durations (buttons, timeouts, pulse widths)
- **Range:** `u8` (0-255 ms), `u16` (0-65 seconds)
- **Resolution:** 1 ms per step

**Microseconds (µs):**
- **Use for:** Medium-speed timing (ADC sampling rates, serial protocols)
- **Range:** `u8` (0-255 µs), `u16` (0-65 ms), `u24` (0-16 seconds)
- **Resolution:** 1 µs per step

**Nanoseconds (ns):**
- **Use for:** FPGA-scale timing (settling times, clock delays, trigger edges)
- **Range:** `u8` (0-255 ns), `u16` (0-65 µs), `u32` (0-4 seconds)
- **Resolution:** 1 ns per step

**Platform conversion (automatic in VHDL):**

```vhdl
-- Moku:Pro @ 1.25 GHz (0.8 ns/cycle)
constant CYCLES_PER_NS : real := 1.25;  -- 1 ns = 1.25 cycles

settling_cycles <= to_unsigned(
  integer(real(to_integer(settling_time)) * CYCLES_PER_NS),
  16
);

-- Example: 10 ns → 13 cycles (rounded up)
```

### Choosing Bit Width

| Width | Milliseconds | Microseconds | Nanoseconds |
|-------|--------------|--------------|-------------|
| `u8` | 0-255 ms (0.26 s) | 0-255 µs | 0-255 ns |
| `u16` | 0-65 s (1 min) | 0-65 ms | 0-65 µs |
| `u24` | 0-16,777 s (4.7 hrs) | 0-16 s | 0-16 ms |
| `u32` | 0-49 days | 0-1.2 hrs | 0-4 s |

**Rule of thumb:**
- **Human-scale:** `ms_u16` (0-65 seconds)
- **FPGA-scale:** `ns_u8` or `ns_u16` (0-255 ns or 0-65 µs)

### See Also

- **[Type System: Time Types](../reference/type_system.md#time-types)**

---

## Pattern 4: Multi-Channel Control

**Use Case:** Multiple identical channels (ADCs, DACs, triggers)

### Pattern

```yaml
datatypes:
  # Channel 1
  - name: voltage_ch1
    datatype: voltage_output_05v_s16
    description: Channel 1 voltage
    default_value: 0
    units: V

  - name: enable_ch1
    datatype: boolean
    description: Enable channel 1
    default_value: false

  # Channel 2
  - name: voltage_ch2
    datatype: voltage_output_05v_s16
    description: Channel 2 voltage
    default_value: 0
    units: V

  - name: enable_ch2
    datatype: boolean
    description: Enable channel 2
    default_value: false

  # Shared timing (all channels)
  - name: pulse_width
    datatype: pulse_duration_ms_u16
    description: Pulse width (shared across channels)
    default_value: 100
    units: ms
```

### Naming Conventions

**Use consistent suffixes:**
- `_ch1`, `_ch2`, `_ch3` - Channel-specific parameters
- No suffix - Shared/global parameters

**Alternatives:**
- `_a`, `_b`, `_c` - Short form (less readable)
- `_1`, `_2`, `_3` - Numeric only (not recommended, conflicts with Python)

### Grouping in YAML

**Best practice:** Group related signals together
```yaml
datatypes:
  # === Channel 1 ===
  - name: voltage_ch1
  - name: gain_ch1
  - name: enable_ch1

  # === Channel 2 ===
  - name: voltage_ch2
  - name: gain_ch2
  - name: enable_ch2

  # === Shared ===
  - name: trigger_source
```

**Why?** Easier to read, maintain, and extend (add CH3, CH4, etc.)

### Register Packing Efficiency

**Example:** 4 channels with voltage + enable

```yaml
# 4 channels × (16-bit voltage + 1-bit enable) = 68 bits
# Packing: CR6 (32) + CR7 (32) + CR8 (4) = 3 registers
# Efficiency: 68/96 = 70.8%
```

**If separate registers:** 8 signals → 8 registers (wasteful!)

### Python Control Pattern

```python
# Control all channels in a loop
for ch in [1, 2, 3, 4]:
    instr.set_parameter(f'voltage_ch{ch}', voltages[ch-1])
    instr.set_parameter(f'enable_ch{ch}', True)

# Or batch update
instr.set_parameters({
    'voltage_ch1': 2.5,
    'voltage_ch2': -1.0,
    'voltage_ch3': 0.0,
    'voltage_ch4': 3.3,
    'enable_ch1': True,
    'enable_ch2': True,
    'enable_ch3': False,
    'enable_ch4': True,
})
```

### See Also

- **[Multi-Channel Walkthrough](multi_channel_walkthrough.md)**

---

## Pattern 5: Safety Constraints

**Use Case:** Preventing hardware damage and operator errors

### Pattern

```yaml
datatypes:
  # High-voltage output with safety limits
  - name: high_voltage_output
    datatype: voltage_output_05v_s16
    description: High voltage output (use with caution!)
    default_value: 0                # SAFE: 0V
    units: V
    min_value: 0.0                  # Prevent negative (if circuit can't handle)
    max_value: 3.3                  # Hardware limit (not full ±5V!)

  # Pulse width with runaway prevention
  - name: pulse_duration
    datatype: pulse_duration_ms_u16
    description: Pulse duration
    default_value: 100
    units: ms
    min_value: 10                   # Minimum 10 ms (prevent glitches)
    max_value: 5000                 # Maximum 5 seconds (prevent runaway)

  # Safety interlock
  - name: safety_override
    datatype: boolean
    description: Safety override (requires key switch)
    default_value: false            # SAFE: Override disabled
```

### Safety Checklist

✅ **DO:**
1. **Default to OFF/0:** `default_value: 0` or `false` for dangerous features
2. **Add min/max:** Constrain runtime values to safe operating ranges
3. **Document constraints:** Explain WHY limits exist (hardware protection)
4. **Test failure modes:** What happens if user tries to exceed limits?

❌ **DON'T:**
1. **Default to ON:** Never default to dangerous states (high voltage, lasers, etc.)
2. **Rely on software only:** Hardware interlocks > software safety
3. **Forget edge cases:** What if user disconnects mid-pulse?

### Constraint Examples

**Voltage protection:**
```yaml
min_value: -3.3   # Prevent exceeding logic supply voltage
max_value: 3.3
```

**Timing protection:**
```yaml
min_value: 1      # Prevent zero-length pulses (glitches)
max_value: 1000   # Prevent runaway (1-second max)
```

**Rate limiting:**
```yaml
- name: max_pulse_rate
  datatype: pulse_duration_ms_u16
  description: Minimum time between pulses (rate limit)
  default_value: 100  # 100 ms = 10 Hz max
  min_value: 50       # 50 ms = 20 Hz absolute max
```

### See Also

- **[Troubleshooting: Hardware protection](../guides/troubleshooting.md#hardware-damage)**

---

## Pattern 6: Register Optimization

**Use Case:** Maximizing register efficiency for large specs

### Pattern (Inefficient ❌)

```yaml
# ❌ Inefficient: 4 signals, 4 registers, 13% efficiency
datatypes:
  - name: flag1
    datatype: pulse_duration_ns_u8  # Uses u8 (8 bits) for 1-bit flag (wastes 7 bits!)
    description: Flag 1
    default_value: 0

  - name: flag2
    datatype: pulse_duration_ns_u8
    description: Flag 2
    default_value: 0

  - name: flag3
    datatype: pulse_duration_ns_u8
    description: Flag 3
    default_value: 0

  - name: flag4
    datatype: pulse_duration_ns_u8
    description: Flag 4
    default_value: 0

# Result: 4 signals × 8 bits = 32 bits → 4 registers (only 4/128 bits used!)
```

### Pattern (Efficient ✅)

```yaml
# ✅ Efficient: 4 signals, 1 register, 13% bit usage BUT only 1 register!
datatypes:
  - name: flag1
    datatype: boolean  # 1 bit
    description: Flag 1
    default_value: false

  - name: flag2
    datatype: boolean  # 1 bit
    description: Flag 2
    default_value: false

  - name: flag3
    datatype: boolean  # 1 bit
    description: Flag 3
    default_value: false

  - name: flag4
    datatype: boolean  # 1 bit
    description: Flag 4
    default_value: false

# Result: 4 signals × 1 bit = 4 bits → 1 register (4/32 bits = 13%, but only 1 register used!)
```

### Optimization Rules

1. **Use narrowest type that fits:**
   - ✅ `boolean` for 0/1 flags (1 bit)
   - ❌ `pulse_duration_ns_u8` for flags (8 bits)

2. **Group signals by bit width:**
   ```yaml
   # Order: All 16-bit, then 8-bit, then 1-bit
   - name: voltage1       # 16 bits
   - name: voltage2       # 16 bits
   - name: time1          # 8 bits
   - name: flag1          # 1 bit
   - name: flag2          # 1 bit
   ```

3. **Let mapper optimize:**
   - Don't manually assign registers
   - Let `best_fit` or `type_clustering` find optimal packing

4. **Check efficiency in manifest.json:**
   ```json
   "efficiency": {
     "percentage": 90.6,  // Aim for >70%
     "registers_saved": 4
   }
   ```

### Type Width Reference

| Type | Bits | When to Use |
|------|------|-------------|
| `boolean` | 1 | Flags, enables, states (0/1) |
| `pulse_duration_ns_u8` | 8 | 0-255 range |
| `voltage_output_05v_u15` | 15 | 0 to +5V (unsigned) |
| `voltage_output_05v_s16` | 16 | ±5V (signed) |
| `pulse_duration_us_u24` | 24 | 0-16 seconds |
| `pulse_duration_ns_u32` | 32 | 0-4 seconds (high precision) |

### Efficiency Targets

| Signals | Target Efficiency | Typical Result |
|---------|-------------------|----------------|
| 1-3 | 40-60% | Acceptable (small specs) |
| 4-6 | 70-90% | Good |
| 7-10 | 80-95% | Excellent |
| 11+ | 85-98% | Exceptional |

**This guide's examples:**
- `minimal_probe` (3 signals): 51.6% ✅
- `multi_channel` (6 signals): 90.6% ✅✅

### See Also

- **[Register Mapping Reference](../reference/register_mapping.md)**

---

## Summary: Design Workflow

**When designing a new instrument spec:**

1. **Start with requirements**
   - What voltages/ranges do I need?
   - What time scales? (human vs FPGA)
   - How many channels?

2. **Choose types (narrowest that fit)**
   - Voltage: `voltage_output_*` for DAC, `voltage_input_*` for ADC
   - Time: `ms` for human, `ns` for FPGA
   - Flags: `boolean` (not `u8`!)

3. **Group by function**
   - Channel 1 signals together
   - Channel 2 signals together
   - Shared/global at end

4. **Add safety constraints**
   - `default_value: 0` or `false` for dangerous features
   - `min_value`/`max_value` for hardware limits

5. **Validate and generate**
   ```bash
   uv run python -m forge.validate_yaml your_spec.yaml
   uv run python -m forge.generate_package your_spec.yaml
   ```

6. **Check efficiency**
   - Open `output/your_app/manifest.json`
   - Look at `efficiency.percentage`
   - Aim for >70% (for specs with 4+ signals)

7. **Iterate**
   - Add signals to fill unused bits
   - Adjust types if needed
   - Regenerate and check efficiency

---

## Pattern Combinations

**Example: FSM-controlled multi-channel voltage output with safety**

```yaml
app_name: safe_multi_channel_fsm
platform: moku_pro

datatypes:
  # FSM control (Pattern 1)
  - name: fsm_state
    datatype: pulse_duration_ns_u8
    default_value: 0

  - name: fsm_trigger
    datatype: boolean
    default_value: false

  # Multi-channel voltages (Pattern 2 + Pattern 4)
  - name: voltage_ch1
    datatype: voltage_output_05v_s16
    default_value: 0
    min_value: 0.0     # Pattern 5: Safety
    max_value: 3.3

  - name: voltage_ch2
    datatype: voltage_output_05v_s16
    default_value: 0
    min_value: 0.0
    max_value: 3.3

  # Timing (Pattern 3)
  - name: pulse_duration
    datatype: pulse_duration_ms_u16
    default_value: 100
    min_value: 10      # Pattern 5: Safety
    max_value: 5000

  # Channel enables (Pattern 4 + Pattern 6: booleans for efficiency)
  - name: enable_ch1
    datatype: boolean
    default_value: false

  - name: enable_ch2
    datatype: boolean
    default_value: false

# Result: 7 signals, 3 registers, ~75% efficiency
```

**Patterns used:** 1, 2, 3, 4, 5, 6 (all combined!)

---

## Additional Resources

**Examples:**
- [Minimal Walkthrough](minimal_walkthrough.md) - 3 signals, basic patterns
- [Multi-Channel Walkthrough](multi_channel_walkthrough.md) - 6 signals, advanced packing

**Reference:**
- [Type System](../reference/type_system.md) - All 23 types
- [YAML Schema](../reference/yaml_schema.md) - Complete YAML format
- [Register Mapping](../reference/register_mapping.md) - Packing algorithms

**Guides:**
- [User Guide](../guides/user_guide.md) - Complete workflow
- [Troubleshooting](../guides/troubleshooting.md) - Common issues

---

**Generated with:** moku-instrument-forge v0.1.0
**Last updated:** 2025-11-03
