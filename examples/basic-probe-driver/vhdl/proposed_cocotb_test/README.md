# Basic Probe Driver CocotB Test Suite

## Overview
Progressive test suite for `CustomWrapper_bpd` architecture wrapping `basic_probe_driver_custom_inst_main.vhd`.

## Test Structure

### P1 Tests (Fast Smoke Tests)
**File:** `test_bpd_wrapper_p1.py`
**Runtime:** <1 ms per test
**Coverage:**
- `test_reset` - Reset behavior and initial state
- `test_control_register_mapping` - Control0-10 unpacking
- `test_output_mapping` - OutputA/B/C signal verification

### P2 Tests (Comprehensive Functional Tests)
**File:** `test_bpd_wrapper_p2.py`
**Runtime:** ~100 μs - 1 ms per test
**Coverage:**
- `test_idle_to_armed_transition` - IDLE → ARMED on arm_enable
- `test_armed_to_firing_on_trigger` - ARMED → FIRING on ext_trigger_in
- `test_armed_timeout_to_fault` - ARMED → FAULT on timeout
- `test_firing_pulse_durations` - Verify pulse timing accuracy
- `test_firing_to_cooldown` - FIRING → COOLDOWN transition
- `test_cooldown_to_idle_oneshot` - One-shot mode (auto_rearm=0)
- `test_cooldown_to_armed_burst` - Burst mode (auto_rearm=1)
- `test_fault_clear_recovery` - FAULT → IDLE on fault_clear
- `test_monitor_threshold_positive` - Positive threshold crossing
- `test_monitor_threshold_negative` - Negative threshold crossing
- `test_cooldown_interval_enforcement` - Verify cooldown timing

### P3 Tests (Advanced Scenarios)
**File:** `test_bpd_wrapper_p3.py`
**Runtime:** Variable (10 μs - 1 ms per test)
**Coverage:**
- `test_burst_mode_multi_cycle` - Auto-rearm through 3 cycles
- `test_zero_duration_pulses` - Edge case: 0 ns durations
- `test_max_timeout_value` - Stress test: timeout=65535 s
- `test_simultaneous_pulse_completion` - Both pulses finish same cycle
- `test_monitor_latch_persistence` - Threshold latch behavior

### FSM Observer Tests (Oscilloscope Debugging)
**File:** `test_bpd_fsm_observer.py`
**Runtime:** ~1-10 ms per test
**Architecture:** `CustomWrapper_bpd_with_observer.vhd` (includes fsm_observer)
**Coverage:**
- `test_observer_reset_behavior` - IDLE voltage (0.0V) after reset
- `test_observer_idle_to_armed_transition` - Voltage stairstep (0.0V → 0.625V)
- `test_observer_normal_state_progression` - Full stairstep through all states
- `test_observer_sign_flip_fault_from_idle` - Sign-flip from IDLE (0.0V → ~0.0V)
- `test_observer_sign_flip_fault_from_armed` - Sign-flip from ARMED (positive → negative)
- `test_observer_sign_flip_fault_from_firing` - Sign-flip from FIRING state
- `test_observer_fault_clear_recovery` - Return to IDLE voltage after fault_clear
- `test_observer_voltage_spreading` - Verify automatic voltage interpolation
- `test_observer_rapid_state_changes` - Track rapid transitions without glitches
- `test_observer_documentation` - Configuration and usage documentation

## Signal Mapping Reference

### Control Register Allocation
```
Control0[3:0]   → arm_enable, ext_trigger_in, auto_rearm_enable, fault_clear
Control1[15:0]  → trig_out_voltage (signed, mV)
Control2[15:0]  → trig_out_duration (unsigned, ns)
Control3[15:0]  → intensity_voltage (signed, mV)
Control4[15:0]  → intensity_duration (unsigned, ns)
Control5[15:0]  → trigger_wait_timeout (unsigned, s)
Control6[23:0]  → cooldown_interval (unsigned, μs)
Control7[1:0]   → monitor_enable, monitor_expect_negative
Control8[15:0]  → monitor_threshold_voltage (signed, mV)
Control9[31:0]  → monitor_window_start (unsigned, ns)
Control10[31:0] → monitor_window_duration (unsigned, ns)
Control11-31    → Reserved (unused)
```

### Input/Output Mapping
```
InputA[15:0]    → probe_monitor_feedback (signed, mV)
InputB-D        → Unused

OutputA[15:0]   → trig_out_active (0x0000 or 0xFFFF)
OutputB[15:0]   → intensity_out_active (0x0000 or 0xFFFF)
OutputC[5:0]    → current_state (6-bit FSM state)
OutputD         → Unused (tied to 0) in CustomWrapper_bpd.vhd
                → fsm_observer voltage_out in CustomWrapper_bpd_with_observer.vhd
```

### FSM Observer Voltage Mapping (CustomWrapper_bpd_with_observer.vhd only)
```
OutputD voltage encoding:
  IDLE     (0x00) →  0.00V  (V_MIN)
  ARMED    (0x01) →  0.625V (linear interpolation)
  FIRING   (0x02) →  1.25V
  COOLDOWN (0x03) →  1.875V
  (unused) (0x04) →  2.50V  (V_MAX)
  FAULT    (0x3F) → -prev_voltage (sign-flip indicates fault)

Configuration:
  V_MIN = 0.0V, V_MAX = 2.5V
  FAULT_STATE_THRESHOLD = 5 (states 0-4 are normal)
  Sign-flip: Negative voltage = FAULT, magnitude = previous state
```

### FSM State Encoding
```
IDLE     = 0b000000
ARMED    = 0b000001
FIRING   = 0b000010
COOLDOWN = 0b000011
FAULT    = 0b111111
```

## Running Tests

### Prerequisites
```bash
# Ensure GHDL and CocotB are installed
# From EZ-EMFI root:
uv sync
```

### Run Individual Test Levels
```bash
# P1 tests only (fast smoke tests)
pytest proposed_cocotb_test/test_bpd_wrapper_p1.py

# P2 tests only (comprehensive functional)
pytest proposed_cocotb_test/test_bpd_wrapper_p2.py

# P3 tests only (advanced scenarios)
pytest proposed_cocotb_test/test_bpd_wrapper_p3.py

# FSM Observer tests (requires CustomWrapper_bpd_with_observer.vhd)
pytest proposed_cocotb_test/test_bpd_fsm_observer.py

# All tests
pytest proposed_cocotb_test/
```

### Run Specific Test
```bash
pytest proposed_cocotb_test/test_bpd_wrapper_p2.py::test_idle_to_armed_transition -v
```

## Test Configuration Notes

1. **Clock Frequency:** All tests assume 125 MHz (8 ns period) matching Moku:Go platform
2. **Time Unit Conversions:**
   - ns durations: Direct cycle count @ 125 MHz
   - μs intervals: 125 cycles per μs
   - s timeouts: 125,000,000 cycles per second
3. **Timeout Handling:** Tests use short timeout values (0-5 s) to avoid long simulations
4. **Pulse Durations:** Tests use 8-160 ns pulses (1-20 cycles) for fast execution

## Known Limitations

1. **Monitor Latch:** `monitor_triggered` is internal to FSM - not observable via wrapper outputs
2. **Voltage Outputs:** DAC outputs not yet wired (TODO in main FSM)
3. **Fault Injection:** Tests in P3 cannot directly inject faults from FIRING state (requires FSM modification)

## FSM Observer Integration

The `test_bpd_fsm_observer.py` test suite requires the enhanced wrapper architecture:

**Architecture:** `CustomWrapper_bpd_with_observer.vhd`
- Instantiates `fsm_observer.vhd` from `/Users/johnycsh/EZ-EMFI/VHDL/`
- Outputs FSM state as voltage on OutputD
- Uses sign-flip pattern: negative voltage = FAULT state
- Magnitude preserves debugging context (shows previous state before fault)

**Oscilloscope Usage:**
1. Connect OutputD to oscilloscope channel
2. Set voltage scale: -3V to +3V (covers full range)
3. Trigger on voltage transitions (state changes)
4. Positive voltage = normal state progression (0V → 2.5V)
5. Negative voltage = FAULT state (magnitude shows previous state)

**Example Debug Session:**
```
Scope reading: +0.625V → FSM in ARMED state
Scope reading: +1.25V  → FSM in FIRING state
Scope reading: -1.25V  → FSM FAULTED from FIRING state
```

## Future Test Additions

- DAC output verification once wired to entity ports
- Fault condition stress tests (voltage range violations, counter overflow)
- Multi-threaded trigger scenarios (rapid re-arming)
- Hardware validation on Moku:Go platform

## References
- `CustomWrapper_bpd.vhd` - Base wrapper implementation
- `CustomWrapper_bpd_with_observer.vhd` - Wrapper with fsm_observer integration
- `basic_probe_driver_custom_inst_main.vhd` - FSM core
- `basic_probe_driver.yaml` - Register specification
- `CustomWrapper_test_stub.vhd` - Entity declaration
- `/Users/johnycsh/EZ-EMFI/VHDL/fsm_observer.vhd` - FSM Observer pattern implementation
- `/Users/johnycsh/EZ-EMFI/examples/test_fsm_example.py` - FSM Observer pattern validation
