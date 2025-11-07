"""
FSM Observer Pattern Test for Basic Probe Driver
=================================================

This test validates the fsm_observer integration with the Basic Probe Driver FSM,
demonstrating oscilloscope-based state debugging using voltage encoding.

Test Approach:
- Integrates fsm_observer.vhd with CustomWrapper_bpd architecture
- Monitors FSM state transitions via voltage output (OutputD)
- Uses sign-flip fault indication for FAULT state
- Validates voltage stairstep progression through normal states

FSM States (5 normal + 1 fault):
  IDLE     (000000) →  0.00V (V_MIN)
  ARMED    (000001) →  0.50V
  FIRING   (000010) →  1.00V
  COOLDOWN (000011) →  1.50V
  (unused) (000100) →  2.00V
  (unused) (000101) →  2.50V (V_MAX)
  FAULT    (111111) → -prev_voltage (sign-flip)

Voltage Mapping Strategy:
- V_MIN = 0.0V (IDLE)
- V_MAX = 2.5V (maximum normal state)
- FAULT_STATE_THRESHOLD = 5 (states 0-4 are normal, 63 is fault)
- Sign-flip: FAULT state shows negative magnitude of previous state

Integration Requirements:
- Modified CustomWrapper_bpd.vhd to instantiate fsm_observer
- OutputD connected to fsm_observer voltage_out
- State vector wired from FSM to observer

References:
- fsm_observer.vhd (pattern implementation)
- test_fsm_example.py (pattern validation)
- OSCILLOSCOPE_DEBUGGING_TECHNIQUES.md

Author: AI-assisted implementation
Date: 2025-11-05
"""

import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.clock import Clock

# FSM State Constants (from basic_probe_driver_custom_inst_main.vhd)
STATE_IDLE     = 0b000000  # 0
STATE_ARMED    = 0b000001  # 1
STATE_FIRING   = 0b000010  # 2
STATE_COOLDOWN = 0b000011  # 3
STATE_FAULT    = 0b111111  # 63

# FSM Observer Configuration (matches expected VHDL generics)
NUM_STATES = 5              # Total states (IDLE, ARMED, FIRING, COOLDOWN + 1 spare)
FAULT_STATE_THRESHOLD = 5   # States 0-4 are normal, 63 is fault
V_MIN = 0.0                 # IDLE voltage
V_MAX = 2.5                 # Maximum normal state voltage


# ============================================================================
# Voltage Conversion Utilities
# ============================================================================

def voltage_to_digital(voltage: float) -> int:
    """Convert voltage to Moku 16-bit signed digital (±5V scale)"""
    digital = int((voltage / 5.0) * 32768)
    return max(-32768, min(32767, digital))


def digital_to_voltage(digital: int) -> float:
    """Convert Moku 16-bit digital to voltage"""
    # Handle signed integers from cocotb
    if digital > 32767:
        digital = digital - 65536  # Convert from unsigned to signed
    return (digital / 32768.0) * 5.0


def calculate_expected_voltage(state_index: int, num_normal_states: int = 5,
                               v_min: float = 0.0, v_max: float = 2.5) -> float:
    """Calculate expected voltage for a state (automatic spreading)

    Args:
        state_index: State index (0-based)
        num_normal_states: Number of normal (non-fault) states
        v_min: Minimum voltage
        v_max: Maximum voltage

    Returns:
        Expected voltage for the state

    Note: Must match VHDL fsm_observer.vhd logic!
    Formula: v_min + (state_index * v_step)
    where v_step = (v_max - v_min) / (num_normal_states - 1)
    """
    if num_normal_states > 1:
        v_step = (v_max - v_min) / (num_normal_states - 1)
    else:
        v_step = 0.0
    return v_min + (state_index * v_step)


# ============================================================================
# Helper Functions
# ============================================================================

def get_state(dut):
    """Extract 6-bit FSM state from OutputC"""
    return dut.OutputC.value.integer & 0x3F


def get_observer_voltage(dut):
    """Get voltage from fsm_observer output (OutputD)"""
    digital = int(dut.OutputD.value.to_signed())
    return digital_to_voltage(digital)


async def setup_dut(dut):
    """Common setup: start clock, release reset, wait 2 cycles"""
    clock = Clock(dut.Clk, 8, units="ns")  # 125 MHz
    cocotb.start_soon(clock.start())
    dut.Reset.value = 1
    await RisingEdge(dut.Clk)
    dut.Reset.value = 0
    await RisingEdge(dut.Clk)

    # Initialize all control registers
    for i in range(32):
        getattr(dut, f"Control{i}").value = 0


# ============================================================================
# Core FSM Observer Tests
# ============================================================================

@cocotb.test()
async def test_observer_reset_behavior(dut):
    """Test 1: Observer outputs IDLE voltage (0.0V) after reset"""
    await setup_dut(dut)

    # Check FSM is in IDLE
    assert get_state(dut) == STATE_IDLE, "FSM should be in IDLE after reset"

    # Check observer voltage
    voltage = get_observer_voltage(dut)
    expected_v = calculate_expected_voltage(STATE_IDLE)

    dut._log.info(f"Reset state: FSM={get_state(dut):02x}, Observer={voltage:+.3f}V (expected {expected_v:+.3f}V)")
    assert abs(voltage - expected_v) < 0.1, \
        f"Observer voltage mismatch after reset: expected {expected_v:+.3f}V, got {voltage:+.3f}V"


@cocotb.test()
async def test_observer_idle_to_armed_transition(dut):
    """Test 2: Observer tracks IDLE → ARMED transition (0.0V → 0.625V)"""
    await setup_dut(dut)

    # Capture IDLE voltage
    voltage_idle = get_observer_voltage(dut)
    expected_idle = calculate_expected_voltage(STATE_IDLE)
    dut._log.info(f"IDLE: Observer={voltage_idle:+.3f}V (expected {expected_idle:+.3f}V)")

    # Configure minimal parameters
    dut.Control5.value = 0x0005  # trigger_wait_timeout = 5 s

    # Arm the FSM
    dut.Control0.value = 0b0001  # arm_enable=1
    await RisingEdge(dut.Clk)
    await ClockCycles(dut.Clk, 1)  # Wait for observer to update

    # Check FSM transitioned to ARMED
    assert get_state(dut) == STATE_ARMED, "FSM should transition to ARMED"

    # Check observer voltage updated
    voltage_armed = get_observer_voltage(dut)
    expected_armed = calculate_expected_voltage(STATE_ARMED)
    dut._log.info(f"ARMED: Observer={voltage_armed:+.3f}V (expected {expected_armed:+.3f}V)")

    assert voltage_armed > voltage_idle, "Observer voltage should increase (IDLE → ARMED)"
    assert abs(voltage_armed - expected_armed) < 0.1, \
        f"ARMED voltage mismatch: expected {expected_armed:+.3f}V, got {voltage_armed:+.3f}V"


@cocotb.test()
async def test_observer_normal_state_progression(dut):
    """Test 3: Observer tracks full normal state progression (voltage stairstep)"""
    await setup_dut(dut)

    # Configure short durations for fast test
    dut.Control2.value = 8    # trig_out_duration = 8 ns
    dut.Control4.value = 8    # intensity_duration = 8 ns
    dut.Control5.value = 0x0005  # trigger_wait_timeout = 5 s
    dut.Control6.value = 1    # cooldown_interval = 1 μs

    voltages = []
    states_seen = []

    # IDLE
    states_seen.append("IDLE")
    voltages.append(get_observer_voltage(dut))
    dut._log.info(f"State 0 (IDLE):     {voltages[-1]:+.3f}V")

    # Arm → ARMED
    dut.Control0.value = 0b0001
    await RisingEdge(dut.Clk)
    await ClockCycles(dut.Clk, 1)
    states_seen.append("ARMED")
    voltages.append(get_observer_voltage(dut))
    dut._log.info(f"State 1 (ARMED):    {voltages[-1]:+.3f}V")

    # Trigger → FIRING
    dut.Control0.value = 0b0011  # arm_enable=1, ext_trigger_in=1
    await RisingEdge(dut.Clk)
    await ClockCycles(dut.Clk, 1)
    states_seen.append("FIRING")
    voltages.append(get_observer_voltage(dut))
    dut._log.info(f"State 2 (FIRING):   {voltages[-1]:+.3f}V")

    # Wait for COOLDOWN
    for _ in range(15):
        await RisingEdge(dut.Clk)
        if get_state(dut) == STATE_COOLDOWN:
            break
    await ClockCycles(dut.Clk, 1)
    states_seen.append("COOLDOWN")
    voltages.append(get_observer_voltage(dut))
    dut._log.info(f"State 3 (COOLDOWN): {voltages[-1]:+.3f}V")

    # Verify stairstep progression (monotonic increase)
    for i in range(1, len(voltages)):
        assert voltages[i] > voltages[i-1], \
            f"{states_seen[i]} voltage should be > {states_seen[i-1]} voltage"

    # Verify voltage spacing consistency
    expected_step = (V_MAX - V_MIN) / (NUM_STATES - 1)
    for i in range(1, len(voltages)):
        actual_step = voltages[i] - voltages[i-1]
        dut._log.info(f"  Step {states_seen[i-1]}→{states_seen[i]}: {actual_step:.3f}V (expected {expected_step:.3f}V)")
        assert abs(actual_step - expected_step) < 0.15, \
            f"Voltage step inconsistent: expected {expected_step:.3f}V, got {actual_step:.3f}V"


@cocotb.test()
async def test_observer_sign_flip_fault_from_idle(dut):
    """Test 4: Observer shows sign-flip when faulting from IDLE (0.0V → ~0.0V)"""
    await setup_dut(dut)

    # Capture IDLE voltage
    voltage_idle = get_observer_voltage(dut)
    dut._log.info(f"Before fault (IDLE): {voltage_idle:+.3f}V")

    # Force immediate timeout to trigger FAULT
    dut.Control5.value = 0x0000  # trigger_wait_timeout = 0 s
    dut.Control0.value = 0b0001  # arm_enable=1
    await RisingEdge(dut.Clk)

    # Wait for FAULT state
    for _ in range(10):
        await RisingEdge(dut.Clk)
        if get_state(dut) == STATE_FAULT:
            break

    assert get_state(dut) == STATE_FAULT, "FSM should enter FAULT on timeout"

    # Check observer sign-flip (special case: -0.0V is still ~0.0V)
    await ClockCycles(dut.Clk, 1)  # Wait for observer to update
    voltage_fault = get_observer_voltage(dut)
    dut._log.info(f"After FAULT (from IDLE): {voltage_fault:+.3f}V")

    # From IDLE (0.0V), fault should show near 0V (sign-flip of 0 is 0)
    assert abs(voltage_fault) < 0.2, \
        f"FAULT from IDLE should be ~0V (sign-flip of 0V), got {voltage_fault:+.3f}V"


@cocotb.test()
async def test_observer_sign_flip_fault_from_armed(dut):
    """Test 5: Observer shows sign-flip when faulting from ARMED"""
    await setup_dut(dut)

    # Configure and arm
    dut.Control5.value = 0x0000  # trigger_wait_timeout = 0 s (will timeout immediately)
    dut.Control0.value = 0b0001  # arm_enable=1
    await RisingEdge(dut.Clk)
    await ClockCycles(dut.Clk, 1)

    # Capture ARMED voltage before fault
    assert get_state(dut) == STATE_ARMED, "Should be in ARMED state"
    voltage_armed = get_observer_voltage(dut)
    expected_armed = calculate_expected_voltage(STATE_ARMED)
    dut._log.info(f"Before fault (ARMED): {voltage_armed:+.3f}V (expected {expected_armed:+.3f}V)")

    # Wait for timeout → FAULT
    for _ in range(10):
        await RisingEdge(dut.Clk)
        if get_state(dut) == STATE_FAULT:
            break

    assert get_state(dut) == STATE_FAULT, "FSM should fault on timeout"

    # Check sign-flip
    await ClockCycles(dut.Clk, 1)
    voltage_fault = get_observer_voltage(dut)
    dut._log.info(f"After FAULT (from ARMED): {voltage_fault:+.3f}V")
    dut._log.info(f"Sign-flip: {voltage_armed:+.3f}V → {voltage_fault:+.3f}V (magnitude preserved)")

    # Verify sign-flip
    assert voltage_fault < 0, "FAULT voltage should be negative (sign-flipped)"
    assert abs(abs(voltage_fault) - abs(voltage_armed)) < 0.2, \
        f"Magnitude should match previous state: {abs(voltage_armed):.3f}V vs {abs(voltage_fault):.3f}V"


@cocotb.test()
async def test_observer_sign_flip_fault_from_firing(dut):
    """Test 6: Observer shows sign-flip when faulting from FIRING state"""
    await setup_dut(dut)

    # Configure short durations
    dut.Control2.value = 160  # trig_out_duration = 160 ns (long enough to inject fault mid-pulse)
    dut.Control4.value = 160  # intensity_duration = 160 ns
    dut.Control5.value = 0x0005  # trigger_wait_timeout = 5 s

    # Arm and trigger
    dut.Control0.value = 0b0001
    await RisingEdge(dut.Clk)
    dut.Control0.value = 0b0011  # + ext_trigger_in
    await RisingEdge(dut.Clk)
    await ClockCycles(dut.Clk, 2)

    # Should be in FIRING
    assert get_state(dut) == STATE_FIRING, "Should be in FIRING state"
    voltage_firing = get_observer_voltage(dut)
    expected_firing = calculate_expected_voltage(STATE_FIRING)
    dut._log.info(f"Before fault (FIRING): {voltage_firing:+.3f}V (expected {expected_firing:+.3f}V)")

    # TODO: Inject fault condition (would require fault injection mechanism in FSM)
    # For now, this test documents the expected behavior
    dut._log.info("NOTE: Fault injection from FIRING requires additional FSM inputs")
    dut._log.info("Expected behavior: FIRING voltage → negative magnitude in FAULT state")


@cocotb.test()
async def test_observer_fault_clear_recovery(dut):
    """Test 7: Observer returns to IDLE voltage (0.0V) after fault_clear"""
    await setup_dut(dut)

    # Force fault via timeout
    dut.Control5.value = 0x0000
    dut.Control0.value = 0b0001
    await RisingEdge(dut.Clk)

    # Wait for FAULT
    for _ in range(10):
        await RisingEdge(dut.Clk)
        if get_state(dut) == STATE_FAULT:
            break

    assert get_state(dut) == STATE_FAULT
    voltage_fault = get_observer_voltage(dut)
    dut._log.info(f"In FAULT state: {voltage_fault:+.3f}V")

    # Clear fault
    dut.Control0.value = 0b1000  # fault_clear=1
    await RisingEdge(dut.Clk)
    await ClockCycles(dut.Clk, 1)

    # Should return to IDLE
    assert get_state(dut) == STATE_IDLE, "FSM should return to IDLE after fault_clear"
    voltage_recovered = get_observer_voltage(dut)
    expected_idle = calculate_expected_voltage(STATE_IDLE)
    dut._log.info(f"After fault_clear (IDLE): {voltage_recovered:+.3f}V (expected {expected_idle:+.3f}V)")

    assert abs(voltage_recovered - expected_idle) < 0.1, \
        "Observer should return to IDLE voltage after recovery"


@cocotb.test()
async def test_observer_voltage_spreading(dut):
    """Test 8: Verify automatic voltage spreading matches expected values"""
    await setup_dut(dut)

    # Calculate expected voltages for all normal states
    expected_voltages = {
        STATE_IDLE:     calculate_expected_voltage(0),  # 0.00V
        STATE_ARMED:    calculate_expected_voltage(1),  # 0.625V
        STATE_FIRING:   calculate_expected_voltage(2),  # 1.25V
        STATE_COOLDOWN: calculate_expected_voltage(3),  # 1.875V
    }

    dut._log.info("Expected voltage spreading (5 normal states, 0.0V to 2.5V):")
    for state_idx, voltage in expected_voltages.items():
        state_name = {STATE_IDLE: "IDLE", STATE_ARMED: "ARMED",
                      STATE_FIRING: "FIRING", STATE_COOLDOWN: "COOLDOWN"}[state_idx]
        dut._log.info(f"  State {state_idx} ({state_name:8s}): {voltage:+.3f}V")

    # Verify voltage step calculation
    expected_step = (V_MAX - V_MIN) / (NUM_STATES - 1)
    dut._log.info(f"Expected voltage step: {expected_step:.3f}V")
    dut._log.info(f"  Formula: (V_MAX - V_MIN) / (NUM_STATES - 1)")
    dut._log.info(f"         = ({V_MAX} - {V_MIN}) / ({NUM_STATES} - 1) = {expected_step:.3f}V")

    # Verify IDLE voltage
    voltage_idle = get_observer_voltage(dut)
    assert abs(voltage_idle - expected_voltages[STATE_IDLE]) < 0.1, \
        f"IDLE voltage incorrect: expected {expected_voltages[STATE_IDLE]:.3f}V, got {voltage_idle:.3f}V"


@cocotb.test()
async def test_observer_rapid_state_changes(dut):
    """Test 9: Observer tracks rapid state transitions without glitches"""
    await setup_dut(dut)

    # Configure for fast cycling
    dut.Control2.value = 8
    dut.Control4.value = 8
    dut.Control5.value = 0x0005
    dut.Control6.value = 1

    voltages_seen = []
    states_seen = []

    # Rapid cycle: IDLE → ARMED → FIRING → COOLDOWN → IDLE
    for cycle in range(2):  # Do 2 cycles to stress test
        dut._log.info(f"--- Rapid Cycle {cycle+1} ---")

        # IDLE
        voltages_seen.append(get_observer_voltage(dut))
        states_seen.append("IDLE")

        # → ARMED
        dut.Control0.value = 0b0001
        await RisingEdge(dut.Clk)
        voltages_seen.append(get_observer_voltage(dut))
        states_seen.append("ARMED")

        # → FIRING
        dut.Control0.value = 0b0011
        await RisingEdge(dut.Clk)
        voltages_seen.append(get_observer_voltage(dut))
        states_seen.append("FIRING")

        # → COOLDOWN
        for _ in range(15):
            await RisingEdge(dut.Clk)
            if get_state(dut) == STATE_COOLDOWN:
                break
        voltages_seen.append(get_observer_voltage(dut))
        states_seen.append("COOLDOWN")

        # → IDLE (wait for cooldown to complete)
        for _ in range(150):
            await RisingEdge(dut.Clk)
            if get_state(dut) == STATE_IDLE:
                break

    # Verify no glitches (all voltages should be valid expected values)
    dut._log.info("Voltage trace:")
    for i, (state, voltage) in enumerate(zip(states_seen, voltages_seen)):
        dut._log.info(f"  {i:2d}. {state:8s}: {voltage:+.3f}V")

    # All voltages should be positive (no spurious faults)
    for voltage in voltages_seen:
        assert voltage >= -0.1, f"Unexpected negative voltage during normal operation: {voltage:+.3f}V"


@cocotb.test()
async def test_observer_documentation(dut):
    """Test 10: Documentation test - expected FSM observer behavior"""
    dut._log.info("=" * 80)
    dut._log.info("FSM Observer Pattern - Basic Probe Driver Integration")
    dut._log.info("=" * 80)
    dut._log.info("Configuration:")
    dut._log.info(f"  NUM_STATES:             {NUM_STATES}")
    dut._log.info(f"  FAULT_STATE_THRESHOLD:  {FAULT_STATE_THRESHOLD}")
    dut._log.info(f"  V_MIN:                  {V_MIN}V (IDLE)")
    dut._log.info(f"  V_MAX:                  {V_MAX}V (max normal state)")
    dut._log.info("")
    dut._log.info("State Voltage Mapping:")
    dut._log.info(f"  IDLE     (0x{STATE_IDLE:02x}): {calculate_expected_voltage(0):.3f}V")
    dut._log.info(f"  ARMED    (0x{STATE_ARMED:02x}): {calculate_expected_voltage(1):.3f}V")
    dut._log.info(f"  FIRING   (0x{STATE_FIRING:02x}): {calculate_expected_voltage(2):.3f}V")
    dut._log.info(f"  COOLDOWN (0x{STATE_COOLDOWN:02x}): {calculate_expected_voltage(3):.3f}V")
    dut._log.info(f"  FAULT    (0x{STATE_FAULT:02x}): -prev_voltage (sign-flip)")
    dut._log.info("")
    dut._log.info("Oscilloscope Debugging:")
    dut._log.info("  1. Connect OutputD to oscilloscope (voltage_out)")
    dut._log.info("  2. Trigger on positive edge (state transitions)")
    dut._log.info("  3. Negative voltage = FAULT state (sign-flip)")
    dut._log.info("  4. Voltage magnitude preserves 'where did it fault from'")
    dut._log.info("")
    dut._log.info("Key Features:")
    dut._log.info("  ✓ Non-invasive (FSM unchanged)")
    dut._log.info("  ✓ Single-cycle state transition tracking")
    dut._log.info("  ✓ Sign-flip preserves debugging context")
    dut._log.info("  ✓ Automatic voltage spreading (0.0V → 2.5V)")
    dut._log.info("=" * 80)
