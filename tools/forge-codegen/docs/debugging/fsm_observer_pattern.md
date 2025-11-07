# FSM Observer Pattern

**Purpose:** Non-invasive FSM debugging using voltage-encoded state observation via oscilloscope

**Use Case:** Debug state machines in deployed VHDL modules without internal signal access

---

## Overview

The **FSM Observer Pattern** makes FSM state visible through an analog output by encoding the state vector as a voltage. An oscilloscope connected to this output shows real-time state transitions.

**Key Advantages:**
- ✅ **Non-invasive** - No VHDL changes to production FSM logic
- ✅ **Zero overhead** - LUT calculated at elaboration time
- ✅ **Works with any oscilloscope** - Just analog voltage monitoring
- ✅ **Fault detection** - Negative voltages indicate HARDFAULT states
- ✅ **Platform-agnostic** - Same pattern works on Go/Lab/Pro/Delta

---

## Core Concept

```
FSM State Register (3-bit) → Voltage Encoder → DAC Output → Oscilloscope
   state = 0 (READY)   →   0.0V
   state = 1 (ARMED)   →   0.5V
   state = 2 (FIRING)  →   1.0V
   state = 7 (FAULT)   →  -2.5V (negative indicates fault!)
```

**Voltage encoding provides:**
- Human-readable state on oscilloscope display
- Real-time transition monitoring
- Fault detection via sign-flip

---

## VHDL Implementation Pattern

### Minimal Example

```vhdl
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

entity fsm_observer is
    generic (
        NUM_STATES : positive := 8;    -- Number of states
        V_MIN      : real := 0.0;      -- Minimum voltage
        V_MAX      : real := 2.5;      -- Maximum voltage
        FAULT_STATE_THRESHOLD : natural := 7  -- States >= this value show negative voltage
    );
    port (
        clk          : in  std_logic;
        reset        : in  std_logic;
        state_vector : in  std_logic_vector(5 downto 0);  -- Max 64 states (fixed width)
        voltage_out  : out signed(15 downto 0)  -- ±5V range (Moku platform)
    );
end entity;

architecture rtl of fsm_observer is
    -- LUT calculated at elaboration
    type voltage_lut_t is array (0 to NUM_STATES-1) of signed(15 downto 0);

    function calculate_voltage_lut return voltage_lut_t is
        variable lut : voltage_lut_t;
        variable voltage : real;
        variable digital : integer;
    begin
        for i in 0 to NUM_STATES-1 loop
            if i >= FAULT_STATE_THRESHOLD then
                -- Fault states: Negative voltage (sign-flip)
                voltage := -V_MAX;
            else
                -- Normal states: Linear spacing from V_MIN to V_MAX
                voltage := V_MIN + (real(i) / real(NUM_STATES - 1)) * (V_MAX - V_MIN);
            end if;

            -- Convert voltage to 16-bit signed digital (Moku: ±5V full-scale)
            digital := integer((voltage / 5.0) * 32767.0);
            lut(i) := to_signed(digital, 16);
        end loop;
        return lut;
    end function;

    constant VOLTAGE_LUT : voltage_lut_t := calculate_voltage_lut;

begin
    process(clk, reset)
        variable state_index : natural;
    begin
        if reset = '1' then
            voltage_out <= (others => '0');
        elsif rising_edge(clk) then
            state_index := to_integer(unsigned(state_vector));
            if state_index < NUM_STATES then
                voltage_out <= VOLTAGE_LUT(state_index);
            else
                voltage_out <= (others => '0');  -- Out of bounds
            end if;
        end if;
    end process;
end architecture;
```

### Integration with Your FSM

```vhdl
-- Your FSM (example: 3-bit state)
signal fsm_state : std_logic_vector(2 downto 0);

-- Pad to 6-bit for observer
signal state_padded : std_logic_vector(5 downto 0);
state_padded <= "000" & fsm_state;  -- Zero-pad to fixed width

-- Instantiate observer
U_FSM_OBSERVER: entity work.fsm_observer
    generic map (
        NUM_STATES => 8,           -- Your FSM has 8 states
        V_MIN => 0.0,
        V_MAX => 2.5,
        FAULT_STATE_THRESHOLD => 7 -- State 7 = HARDFAULT
    )
    port map (
        clk          => Clk,
        reset        => Reset,
        state_vector => state_padded,
        voltage_out  => OutputC     -- Connect to CustomWrapper OutputC
    );
```

---

## Voltage Scaling (⚠️ CRITICAL)

### Moku Platform Full-Scale Range

**IMPORTANT:** Moku platforms use **±5.0V full-scale**, not ±1V!

- **Digital range:** -32768 to +32767 (16-bit signed)
- **Analog range:** -5.0V to +5.0V
- **Conversion formula:**

```python
# Voltage → Digital
digital = int((voltage / 5.0) * 32768)

# Digital → Voltage
voltage = (digital / 32768.0) * 5.0
```

**Common error:** Assuming ±1V scale causes **5× voltage error** in state decoding!

**Example:**
```python
# ❌ WRONG (assumes ±1V):
digital = int((voltage / 1.0) * 32768)  # 5× too large!

# ✅ CORRECT (Moku uses ±5V):
digital = int((voltage / 5.0) * 32768)
```

---

## Voltage Guard Bands

**Problem:** Adjacent state values (e.g., state=3 vs state=4) differ by ~0.8mV in voltage, easily corrupted by ADC noise.

**Solution:** Multiply state values by 4 or 8 to increase voltage spacing.

### Without Guard Band
```vhdl
-- state=3 → 0x0003 → 0.46mV
debug_out <= to_signed(to_integer(state_reg), 16);
```

**Problem:** 0.46mV spacing is below ADC noise floor (~1mV)

### With 2-bit Guard Band (×4)
```vhdl
-- state=3 → 0x000C → 1.83mV (4× spacing)
debug_out <= to_signed(to_integer(state_reg) * 4, 16);
```

**Benefit:** 1.83mV spacing is above noise floor

### With 3-bit Guard Band (×8)
```vhdl
-- state=3 → 0x0018 → 3.66mV (8× spacing)
debug_out <= shift_left(to_signed(to_integer(state_reg), 13), 3);
```

**Benefit:** 3.66mV spacing provides robust noise margin

**Recommendation:**
- Use **2-bit (×4)** for most cases
- Use **3-bit (×8)** for very noisy environments
- Already built into FSM observer LUT calculation

---

## Python Decoding

### State Map Example (8-state FSM)

```python
# DS1140_PD probe driver states (example)
STATE_MAP = {
    0.0: "READY",      # Idle state
    0.5: "ARMED",      # Waiting for trigger
    1.0: "FIRING",     # Pulse active
    1.5: "COOLING",    # Dead time
    2.0: "DONE",       # Operation complete
    2.5: "TIMEDOUT",   # Arm timeout expired
}

TOLERANCE = 0.15  # ±0.15V for DAC quantization

def decode_fsm_voltage(voltage: float) -> str:
    """Decode FSM observer voltage to state name.

    Args:
        voltage: Measured voltage from oscilloscope

    Returns:
        State name string
    """
    # Check for HARDFAULT (negative voltage)
    if voltage < 0:
        return "HARDFAULT"

    # Find closest matching state
    for expected_v, name in STATE_MAP.items():
        if abs(voltage - expected_v) < TOLERANCE:
            return name

    return f"UNKNOWN({voltage:.3f}V)"
```

### Usage with Oscilloscope

```python
from moku.instruments import MultiInstrument, Oscilloscope
import time

# Connect to Moku device
m = MultiInstrument('192.168.1.100', platform_id=2)
osc = m.set_instrument(1, Oscilloscope)

# Configure oscilloscope
osc.set_timebase(-5e-3, 5e-3)  # ±5ms window

def read_fsm_state(num_polls=5, delay=0.1):
    """Read FSM state with polling to handle latency.

    Args:
        num_polls: Number of polling iterations
        delay: Delay between polls (seconds)

    Returns:
        Decoded state name
    """
    for i in range(num_polls):
        time.sleep(delay)
        data = osc.get_data()

        if data and 'ch1' in data:
            samples = data['ch1']
            if len(samples) > 0:
                # Use midpoint sample (most stable)
                midpoint = len(samples) // 2
                voltage = samples[midpoint]
                state = decode_fsm_voltage(voltage)

                print(f"  Poll {i}: {voltage:.3f}V → {state}")

                if state != "UNKNOWN":
                    return state

    return "UNKNOWN"

# Read current state
current_state = read_fsm_state()
print(f"Current FSM state: {current_state}")
```

---

## Oscilloscope Techniques

### 1. Polling with Latency Handling

**Problem:** Oscilloscope readings have ~100ms latency. Single reads may return stale data.

**Solution:** Poll multiple times with delays.

```python
def read_stable_voltage(osc, channel='ch1', polls=5, delay=0.1):
    """Read voltage with multiple polls for stability."""
    for _ in range(polls):
        time.sleep(delay)
        data = osc.get_data()

        if data and channel in data:
            samples = data[channel]
            if len(samples) > 0:
                midpoint = len(samples) // 2
                return samples[midpoint]

    raise RuntimeError(f"Failed to get stable reading on {channel}")
```

**Timing:** 10 polls × 100ms = 1 second (sufficient for most transitions)

---

### 2. Midpoint Sampling

**Why midpoint?** Most stable sample in captured window, avoids edge effects.

```python
data = osc.get_data()
ch1_samples = data['ch1']  # NumPy array, typically 1024 samples

# Use midpoint sample (index 512 for 1024 samples)
midpoint_idx = len(ch1_samples) // 2
voltage = ch1_samples[midpoint_idx]
```

**Avoid:** First/last samples may have trigger artifacts

---

### 3. Timebase Configuration

**For state monitoring (slow FSM transitions):**
```python
osc.set_timebase(-5e-3, 5e-3)  # ±5ms window
```

**For timing analysis (fast transitions):**
```python
osc.set_timebase(-1e-6, 1e-6)  # ±1µs window (captures cycle-level timing)
```

---

## Common State Machine Patterns

### Pattern 1: Trigger-Armed FSM

**Sequence:** READY → ARMED → FIRING → COOLING → DONE → READY

**Voltages (example 8-state, 0-2.5V):**
- READY: 0.0V
- ARMED: ~0.5V
- FIRING: ~1.0V
- COOLING: ~1.5V
- DONE: ~2.0V
- TIMEDOUT: ~2.5V (if timeout occurs instead of trigger)
- HARDFAULT: -2.5V (fault condition)

**Debug focus:**
- ARMED duration (should match configured timeout if no trigger)
- FIRING → COOLING transition timing (< 1µs typically)
- COOLING duration matches configuration

---

### Pattern 2: Timeout Behavior

**Expected:** ARMED → TIMEDOUT if no trigger within timeout period

**Test:**
```python
# Set short timeout (e.g., 100ms)
mcc.set_control(6, 0x00640000)  # 100ms timeout in upper 16 bits

# Arm probe
mcc.set_control(8, 0x80000000)  # Arm bit

# Monitor state
start_time = time.time()
for i in range(50):  # Poll for 5 seconds
    time.sleep(0.1)
    voltage = read_stable_voltage(osc)
    state = decode_fsm_voltage(voltage)

    if state == "TIMEDOUT":
        elapsed = time.time() - start_time
        print(f"✅ Timeout detected after {elapsed:.3f}s (expected ~0.1s)")
        break
else:
    print("❌ Timeout not detected - possible FSM issue")
```

---

### Pattern 3: Fault Detection

**Negative voltages indicate HARDFAULT state.**

```python
voltage = read_stable_voltage(osc)

if voltage < 0:
    print(f"❌ HARDFAULT detected (voltage: {voltage:.3f}V)")
    print("Possible causes:")
    print("  - Invalid control register value")
    print("  - Safety constraint violated (e.g., intensity > 3.0V)")
    print("  - VHDL assertion failure")
    print("\nRecommendation: Reset FSM via reset_fsm control register")
else:
    state = decode_fsm_voltage(voltage)
    print(f"✅ FSM in state: {state} ({voltage:.3f}V)")
```

---

## Platform-Specific Timing

### Moku:Go (125 MHz clock)
- **Clock period:** 8ns
- **32 cycles:** 256ns
- **255 cycles:** 2.04µs

### Moku:Lab (500 MHz clock)
- **Clock period:** 2ns
- **32 cycles:** 64ns
- **255 cycles:** 510ns

### Moku:Pro (1.25 GHz clock)
- **Clock period:** 0.8ns
- **32 cycles:** 25.6ns
- **255 cycles:** 204ns

**Use platform clock frequency from `manifest.json` or `moku-models` for accurate timing calculations.**

---

## Troubleshooting

### Issue: "Voltage readings unstable, jumping between states"

**Causes:**
1. Insufficient voltage guard bands
2. ADC noise
3. Ground loop issues

**Solutions:**
- Increase guard band multiplier (×4 → ×8)
- Use averaging over multiple samples
- Check oscilloscope ground connection

---

### Issue: "Negative voltage but FSM should be in normal state"

**Causes:**
1. HARDFAULT state active (FSM detected error condition)
2. Wrong state threshold configuration
3. Voltage scaling error

**Solutions:**
- Check FSM logic for fault conditions
- Verify `FAULT_STATE_THRESHOLD` generic matches FSM state count
- Reset FSM via control register

---

### Issue: "State stuck in UNKNOWN"

**Causes:**
1. Voltage doesn't match any state in STATE_MAP
2. DAC quantization different than expected
3. Incorrect voltage scaling (±1V vs ±5V)

**Solutions:**
- Print actual voltage values to see what's being read
- Adjust TOLERANCE (±0.15V → ±0.20V)
- Verify using ±5V scaling, not ±1V

---

## Best Practices

1. **Always use ±5V voltage scaling** (Moku platform standard)
2. **Poll with delays** to handle oscilloscope latency
3. **Use midpoint samples** for most stable readings
4. **Include guard bands** (×4 or ×8 multiplier)
5. **Reserve highest state for HARDFAULT** (negative voltage detection)
6. **Test voltage encoding in simulation** before hardware deployment
7. **Document state map** in manifest.json for downstream tools

---

## References

- **Moku Platform Specs:** `libs/moku-models/docs/MOKU_PLATFORM_SPECIFICATIONS.md`
- **Hardware Debug Agent:** `.claude/agents/hardware-debug-context/agent.md`
- **Original Pattern:** EZ-EMFI project `oscilloscope_debugging_techniques.md`

---

**Last Updated:** 2025-11-03
**Recommended for:** All custom VHDL instruments with state machines
