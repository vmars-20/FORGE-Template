# FSM Observer Integration for Basic Probe Driver

## Overview

This document describes the integration of the `fsm_observer` pattern with the Basic Probe Driver FSM for oscilloscope-based debugging.

## Pattern Summary

The **fsm_observer** is a non-invasive VHDL debugging pattern that:
- Converts binary FSM state to oscilloscope-visible voltage
- Uses voltage stairstep for normal states (0V → 2.5V)
- Uses sign-flip for fault states (negative voltage = fault)
- Preserves debugging context (magnitude shows previous state before fault)

## Files Created

### 1. CustomWrapper_bpd_with_observer.vhd
**Location:** `/Users/johnycsh/EZ-EMFI/libs/bpd-vhdl-tiny/`

Enhanced wrapper architecture that instantiates fsm_observer:
```vhdl
architecture bpd_wrapper_with_observer of CustomWrapper is
    ...
    FSM_DEBUG: entity WORK.fsm_observer
        generic map (
            NUM_STATES             => 5,
            V_MIN                  => 0.0,
            V_MAX                  => 2.5,
            FAULT_STATE_THRESHOLD  => 5,
            STATE_0_NAME           => "IDLE",
            STATE_1_NAME           => "ARMED",
            STATE_2_NAME           => "FIRING",
            STATE_3_NAME           => "COOLDOWN",
            STATE_4_NAME           => "UNUSED"
        )
        port map (
            clk          => Clk,
            reset        => Reset,
            state_vector => current_state_port,
            voltage_out  => fsm_observer_voltage
        );
```

**Key Changes from base wrapper:**
- OutputD now carries fsm_observer voltage (instead of tied to 0)
- Requires fsm_observer.vhd in compilation path
- Uses volo_voltage_pkg for voltage conversion

### 2. test_bpd_fsm_observer.py
**Location:** `/Users/johnycsh/EZ-EMFI/libs/bpd-vhdl-tiny/proposed_cocotb_test/`

Comprehensive CocotB test suite (10 tests) validating:
- Reset behavior (IDLE voltage = 0.0V)
- State transition tracking (voltage stairstep)
- Sign-flip fault indication (negative voltage)
- Voltage spreading (automatic interpolation)
- Fault recovery (return to IDLE voltage)
- Rapid state changes (no glitches)

## Voltage Encoding

### Normal States (Positive Voltage)
```
State       Binary    Voltage   Description
-------------------------------------------------
IDLE        000000    0.00V     Ground reference
ARMED       000001    0.625V    Linear interpolation
FIRING      000010    1.25V     Between ARMED and COOLDOWN
COOLDOWN    000011    1.875V    Near V_MAX
(unused)    000100    2.50V     V_MAX (spare state)
```

**Interpolation Formula:**
```
voltage = V_MIN + (state_index × voltage_step)
where voltage_step = (V_MAX - V_MIN) / (NUM_STATES - 1)
                   = (2.5 - 0.0) / (5 - 1)
                   = 0.625V
```

### Fault State (Negative Voltage - Sign-Flip)
```
FAULT       111111    -prev_voltage

Examples:
  - Fault from ARMED:    -0.625V  (preserves ARMED magnitude)
  - Fault from FIRING:   -1.25V   (preserves FIRING magnitude)
  - Fault from COOLDOWN: -1.875V  (preserves COOLDOWN magnitude)
  - Fault from IDLE:     ~0.0V    (sign-flip of 0 is 0)
```

**Why Sign-Flip?**
- **Magnitude** = debugging context (where did it fault from?)
- **Sign** = fault indicator (positive = normal, negative = fault)
- **Single output** = no additional ports needed

## Oscilloscope Debugging Workflow

### Setup
1. Connect Moku OutputD to oscilloscope channel
2. Set voltage scale: -3V to +3V
3. Set trigger: rising edge, threshold = 0.3V
4. Timebase: 1 μs/div (adjust for FSM speed)

### Reading the Scope
```
Positive Voltages (Normal States):
  0.0V     → IDLE      (waiting for arm signal)
  0.625V   → ARMED     (waiting for trigger)
  1.25V    → FIRING    (outputs active)
  1.875V   → COOLDOWN  (thermal safety delay)

Negative Voltages (Fault State):
  -0.625V  → Faulted from ARMED (timeout)
  -1.25V   → Faulted from FIRING (safety violation)
  -1.875V  → Faulted from COOLDOWN (unexpected)
```

### Example Debug Session
```
Timeline:
  t=0ms:     +0.0V    → IDLE (reset complete)
  t=1ms:     +0.625V  → ARMED (user armed system)
  t=5ms:     +1.25V   → FIRING (trigger received)
  t=5.2ms:   +1.875V  → COOLDOWN (pulses complete)
  t=10ms:    +0.0V    → IDLE (cooldown finished, one-shot mode)

Fault scenario:
  t=0ms:     +0.0V    → IDLE
  t=1ms:     +0.625V  → ARMED (waiting for trigger)
  t=6ms:     -0.625V  → FAULT (timeout occurred in ARMED state)
                         ↑ Negative voltage indicates fault
                         ↑ Magnitude (0.625V) shows it faulted from ARMED
```

## Test Coverage

### Core Functionality (Tests 1-7)
- ✓ Reset behavior (IDLE voltage)
- ✓ State transition tracking (IDLE → ARMED → FIRING → COOLDOWN)
- ✓ Sign-flip fault indication (from IDLE, ARMED, FIRING)
- ✓ Fault recovery (return to IDLE voltage)

### Edge Cases (Tests 8-10)
- ✓ Voltage spreading (automatic interpolation)
- ✓ Rapid state changes (no glitches)
- ✓ Configuration documentation

## Integration Requirements

### Compilation Dependencies
To compile `CustomWrapper_bpd_with_observer.vhd`, ensure the following files are in the VHDL search path:

1. **Required libraries:**
   - `basic_app_types_pkg.vhd`
   - `basic_app_voltage_pkg.vhd`
   - `basic_app_time_pkg.vhd`
   - `volo_voltage_pkg.vhd` (for fsm_observer)

2. **Required entities:**
   - `basic_probe_driver_custom_inst_main` (FSM core)
   - `fsm_observer` (from `/Users/johnycsh/EZ-EMFI/VHDL/fsm_observer.vhd`)

3. **Test stub:**
   - `CustomWrapper` entity (from `CustomWrapper_test_stub.vhd`)

### GHDL Compilation Order
```bash
# 1. Compile packages
ghdl -a volo_voltage_pkg.vhd
ghdl -a basic_app_types_pkg.vhd
ghdl -a basic_app_voltage_pkg.vhd
ghdl -a basic_app_time_pkg.vhd

# 2. Compile entities
ghdl -a fsm_observer.vhd
ghdl -a basic_probe_driver_custom_inst_main.vhd

# 3. Compile wrapper
ghdl -a CustomWrapper_test_stub.vhd
ghdl -a CustomWrapper_bpd_with_observer.vhd

# 4. Elaborate
ghdl -e CustomWrapper
```

## Comparison: Base vs Observer Wrapper

| Feature                    | CustomWrapper_bpd.vhd | CustomWrapper_bpd_with_observer.vhd |
|---------------------------|----------------------|-------------------------------------|
| OutputA                   | trig_out_active      | trig_out_active                    |
| OutputB                   | intensity_out_active | intensity_out_active               |
| OutputC                   | current_state (6-bit)| current_state (6-bit)              |
| OutputD                   | Tied to 0            | **fsm_observer voltage**           |
| Dependencies              | Basic packages       | + volo_voltage_pkg, fsm_observer   |
| Oscilloscope debugging    | No                   | **Yes**                            |
| Production use            | Yes                  | Yes (debug channel always-on)      |

**Recommendation:** Use `CustomWrapper_bpd_with_observer.vhd` for:
- Initial hardware validation
- Debugging FSM behavior on Moku platform
- Production (OutputD unused → free for debug)

## Future Enhancements

1. **Python Decoder Utility:**
   - Read OutputD voltage from Moku API
   - Decode state name from voltage
   - Log state transitions to CSV

2. **Trigger Tables:**
   - Pre-calculate voltage thresholds for oscilloscope triggers
   - Example: "Trigger when entering FIRING state (>1.0V, <1.5V)"

3. **Multi-FSM Observers:**
   - Use multiple output channels (OutputC, OutputD) for multiple FSMs
   - Cross-correlate state transitions

## References

- **Pattern Source:** `/Users/johnycsh/EZ-EMFI/VHDL/fsm_observer.vhd`
- **Pattern Validation:** `/Users/johnycsh/EZ-EMFI/examples/test_fsm_example.py`
- **VHDL Coding Standards:** `libs/forge-vhdl/docs/VHDL_CODING_STANDARDS.md`
- **Oscilloscope Techniques:** `docs/OSCILLOSCOPE_DEBUGGING_TECHNIQUES.md`

---

**Author:** Claude Code (AI-assisted implementation)
**Date:** 2025-11-05
**Version:** 1.0
