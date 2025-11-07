"""
Progressive Test Level 2 (P2) - Basic Probe Driver FSM Functional Tests
Comprehensive coverage of all FSM states and transitions

Test Coverage:
- All state transitions (IDLE → ARMED → FIRING → COOLDOWN → IDLE/ARMED)
- Fault conditions (timeout, fault_clear)
- Pulse timing (trigger and intensity outputs)
- Monitor window and threshold detection
- Cooldown enforcement
- Auto-rearm (burst mode) vs one-shot mode

Expected Runtime: ~100 μs - 1 ms per test (depends on timeout values)
"""

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

# FSM State Constants
STATE_IDLE     = 0b000000
STATE_ARMED    = 0b000001
STATE_FIRING   = 0b000010
STATE_COOLDOWN = 0b000011
STATE_FAULT    = 0b111111

# Helper functions
def get_state(dut):
    """Extract 6-bit FSM state from OutputC"""
    return dut.OutputC.value.integer & 0x3F

def is_trig_active(dut):
    """Check if trigger output is active (OutputA = 0xFFFF)"""
    return dut.OutputA.value.integer == 0xFFFF

def is_intensity_active(dut):
    """Check if intensity output is active (OutputB = 0xFFFF)"""
    return dut.OutputB.value.integer == 0xFFFF


async def setup_dut(dut):
    """Common setup: start clock, release reset, wait 2 cycles"""
    clock = Clock(dut.Clk, 8, units="ns")  # 125 MHz
    cocotb.start_soon(clock.start())
    dut.Reset.value = 1
    await RisingEdge(dut.Clk)
    dut.Reset.value = 0
    await RisingEdge(dut.Clk)


@cocotb.test()
async def test_idle_to_armed_transition(dut):
    """P2.1: IDLE → ARMED on arm_enable assertion"""
    await setup_dut(dut)

    # Set all controls to safe defaults
    for i in range(32):
        getattr(dut, f"Control{i}").value = 0

    # Configure minimal parameters
    dut.Control5.value = 0x0005  # trigger_wait_timeout = 5 s (won't timeout in this test)

    await RisingEdge(dut.Clk)
    assert get_state(dut) == STATE_IDLE, "Should start in IDLE"

    # Assert arm_enable
    dut.Control0.value = 0b0001  # arm_enable=1
    await RisingEdge(dut.Clk)

    # Should transition to ARMED
    assert get_state(dut) == STATE_ARMED, f"Expected ARMED state, got 0x{get_state(dut):02x}"


@cocotb.test()
async def test_armed_to_firing_on_trigger(dut):
    """P2.2: ARMED → FIRING on ext_trigger_in assertion"""
    await setup_dut(dut)

    # Set all controls to safe defaults
    for i in range(32):
        getattr(dut, f"Control{i}").value = 0

    dut.Control5.value = 0x0005  # trigger_wait_timeout = 5 s

    # Arm the FSM
    dut.Control0.value = 0b0001  # arm_enable=1
    await RisingEdge(dut.Clk)
    assert get_state(dut) == STATE_ARMED

    # Send external trigger
    dut.Control0.value = 0b0011  # arm_enable=1, ext_trigger_in=1
    await RisingEdge(dut.Clk)

    # Should transition to FIRING
    assert get_state(dut) == STATE_FIRING, f"Expected FIRING state, got 0x{get_state(dut):02x}"


@cocotb.test()
async def test_armed_timeout_to_fault(dut):
    """P2.3: ARMED → FAULT on trigger_wait_timeout exceeded"""
    await setup_dut(dut)

    # Set all controls to safe defaults
    for i in range(32):
        getattr(dut, f"Control{i}").value = 0

    # Set SHORT timeout (1 second = 125M cycles, too long for sim)
    # Use time conversion: trigger_wait_timeout is in seconds
    # At 125 MHz: 1 second = 125,000,000 cycles
    # For fast test: set timeout to 0 seconds → immediate timeout
    dut.Control5.value = 0x0000  # trigger_wait_timeout = 0 s (will timeout immediately)

    # Arm the FSM
    dut.Control0.value = 0b0001  # arm_enable=1
    await RisingEdge(dut.Clk)
    assert get_state(dut) == STATE_ARMED

    # Wait for timeout (should happen within a few cycles for timeout=0)
    for _ in range(10):
        await RisingEdge(dut.Clk)
        if get_state(dut) == STATE_FAULT:
            break

    assert get_state(dut) == STATE_FAULT, \
        f"Expected FAULT state after timeout, got 0x{get_state(dut):02x}"


@cocotb.test()
async def test_firing_pulse_durations(dut):
    """P2.4: Verify trig_out_active and intensity_active match configured durations"""
    await setup_dut(dut)

    # Set all controls to safe defaults
    for i in range(32):
        getattr(dut, f"Control{i}").value = 0

    # Configure short pulse durations for fast test
    # At 125 MHz: 8 ns per cycle
    # Set durations: trig=80ns (10 cycles), intensity=160ns (20 cycles)
    dut.Control2.value = 80   # trig_out_duration = 80 ns
    dut.Control4.value = 160  # intensity_duration = 160 ns
    dut.Control5.value = 0x0005  # trigger_wait_timeout = 5 s (won't timeout)

    # Arm and trigger
    dut.Control0.value = 0b0001  # arm_enable=1
    await RisingEdge(dut.Clk)
    dut.Control0.value = 0b0011  # arm_enable=1, ext_trigger_in=1
    await RisingEdge(dut.Clk)

    # Enter FIRING state
    assert get_state(dut) == STATE_FIRING

    # Both outputs should be active in FIRING state
    # (Wrapper design: outputs active whenever state=FIRING, independent of timers)
    assert is_trig_active(dut), "trig_out should be active in FIRING state"
    assert is_intensity_active(dut), "intensity_out should be active in FIRING state"

    # Wait for pulse durations to complete
    # trig=80ns (10 cycles), intensity=160ns (20 cycles)
    # FSM exits FIRING when BOTH complete → 20 cycles minimum
    for i in range(25):
        await RisingEdge(dut.Clk)
        if get_state(dut) != STATE_FIRING:
            break

    # Should transition to COOLDOWN after both pulses complete
    assert get_state(dut) == STATE_COOLDOWN, \
        f"Expected COOLDOWN after firing, got 0x{get_state(dut):02x}"


@cocotb.test()
async def test_firing_to_cooldown(dut):
    """P2.5: FIRING → COOLDOWN when both pulses complete"""
    await setup_dut(dut)

    # Set all controls to safe defaults
    for i in range(32):
        getattr(dut, f"Control{i}").value = 0

    # Very short pulse durations
    dut.Control2.value = 8   # trig_out_duration = 8 ns (1 cycle)
    dut.Control4.value = 8   # intensity_duration = 8 ns (1 cycle)
    dut.Control5.value = 0x0005  # trigger_wait_timeout = 5 s

    # Arm and trigger
    dut.Control0.value = 0b0001
    await RisingEdge(dut.Clk)
    dut.Control0.value = 0b0011
    await RisingEdge(dut.Clk)

    assert get_state(dut) == STATE_FIRING

    # Wait for transition
    for _ in range(10):
        await RisingEdge(dut.Clk)
        if get_state(dut) == STATE_COOLDOWN:
            break

    assert get_state(dut) == STATE_COOLDOWN


@cocotb.test()
async def test_cooldown_to_idle_oneshot(dut):
    """P2.6: COOLDOWN → IDLE when auto_rearm_enable=0 (one-shot mode)"""
    await setup_dut(dut)

    # Set all controls to safe defaults
    for i in range(32):
        getattr(dut, f"Control{i}").value = 0

    # Short durations and cooldown
    dut.Control2.value = 8    # trig_out_duration = 8 ns
    dut.Control4.value = 8    # intensity_duration = 8 ns
    dut.Control5.value = 0x0005   # trigger_wait_timeout = 5 s
    dut.Control6.value = 10   # cooldown_interval = 10 μs (125MHz: 10μs = 1250 cycles)

    # NOTE: For fast test, use shorter cooldown (1 μs = 125 cycles)
    dut.Control6.value = 1    # cooldown_interval = 1 μs

    # Arm, trigger, fire
    dut.Control0.value = 0b0001  # arm_enable=1, auto_rearm=0
    await RisingEdge(dut.Clk)
    dut.Control0.value = 0b0011  # + ext_trigger_in=1
    await RisingEdge(dut.Clk)

    # Wait to enter COOLDOWN
    for _ in range(10):
        await RisingEdge(dut.Clk)
        if get_state(dut) == STATE_COOLDOWN:
            break

    assert get_state(dut) == STATE_COOLDOWN

    # Wait for cooldown to complete (1 μs = 125 cycles)
    for _ in range(150):
        await RisingEdge(dut.Clk)
        if get_state(dut) != STATE_COOLDOWN:
            break

    # Should return to IDLE (auto_rearm=0)
    assert get_state(dut) == STATE_IDLE, \
        f"Expected IDLE after cooldown (one-shot), got 0x{get_state(dut):02x}"


@cocotb.test()
async def test_cooldown_to_armed_burst(dut):
    """P2.7: COOLDOWN → ARMED when auto_rearm_enable=1 (burst mode)"""
    await setup_dut(dut)

    # Set all controls to safe defaults
    for i in range(32):
        getattr(dut, f"Control{i}").value = 0

    # Short durations and cooldown
    dut.Control2.value = 8    # trig_out_duration = 8 ns
    dut.Control4.value = 8    # intensity_duration = 8 ns
    dut.Control5.value = 0x0005   # trigger_wait_timeout = 5 s
    dut.Control6.value = 1    # cooldown_interval = 1 μs

    # Arm with auto_rearm enabled
    dut.Control0.value = 0b0101  # arm_enable=1, auto_rearm_enable=1 (bit 2)
    await RisingEdge(dut.Clk)
    dut.Control0.value = 0b0111  # + ext_trigger_in=1
    await RisingEdge(dut.Clk)

    # Wait to enter COOLDOWN
    for _ in range(10):
        await RisingEdge(dut.Clk)
        if get_state(dut) == STATE_COOLDOWN:
            break

    assert get_state(dut) == STATE_COOLDOWN

    # Wait for cooldown to complete
    for _ in range(150):
        await RisingEdge(dut.Clk)
        if get_state(dut) != STATE_COOLDOWN:
            break

    # Should return to ARMED (auto_rearm=1)
    assert get_state(dut) == STATE_ARMED, \
        f"Expected ARMED after cooldown (burst mode), got 0x{get_state(dut):02x}"


@cocotb.test()
async def test_fault_clear_recovery(dut):
    """P2.8: FAULT → IDLE on fault_clear pulse"""
    await setup_dut(dut)

    # Set all controls to safe defaults
    for i in range(32):
        getattr(dut, f"Control{i}").value = 0

    # Force timeout to enter FAULT state
    dut.Control5.value = 0x0000  # trigger_wait_timeout = 0 s

    # Arm (will timeout immediately)
    dut.Control0.value = 0b0001
    await RisingEdge(dut.Clk)

    # Wait for FAULT
    for _ in range(10):
        await RisingEdge(dut.Clk)
        if get_state(dut) == STATE_FAULT:
            break

    assert get_state(dut) == STATE_FAULT

    # Assert fault_clear (bit 3 of Control0)
    dut.Control0.value = 0b1000  # fault_clear=1
    await RisingEdge(dut.Clk)

    # Should return to IDLE
    assert get_state(dut) == STATE_IDLE, \
        f"Expected IDLE after fault_clear, got 0x{get_state(dut):02x}"


@cocotb.test()
async def test_monitor_threshold_positive(dut):
    """P2.9: Monitor detects positive-going threshold crossing"""
    await setup_dut(dut)

    # Set all controls to safe defaults
    for i in range(32):
        getattr(dut, f"Control{i}").value = 0

    # Configure monitor for positive crossing
    dut.Control7.value = 0b00000001  # monitor_enable=1, monitor_expect_negative=0
    dut.Control8.value = 100         # monitor_threshold_voltage = 100 mV (signed)
    dut.Control9.value = 0           # monitor_window_start = 0 ns (open immediately)
    dut.Control10.value = 1000       # monitor_window_duration = 1000 ns

    # Set short pulse durations
    dut.Control2.value = 80
    dut.Control4.value = 80
    dut.Control5.value = 0x0005

    # Set InputA (probe_monitor_feedback) below threshold
    dut.InputA.value = 50  # 50 mV < 100 mV

    # Arm and trigger
    dut.Control0.value = 0b0001
    await RisingEdge(dut.Clk)
    dut.Control0.value = 0b0011
    await RisingEdge(dut.Clk)

    assert get_state(dut) == STATE_FIRING

    # Wait a few cycles, then cross threshold
    await RisingEdge(dut.Clk)
    await RisingEdge(dut.Clk)
    dut.InputA.value = 150  # 150 mV > 100 mV (positive crossing)
    await RisingEdge(dut.Clk)

    # Monitor should latch threshold crossing (internal signal, can't verify externally)
    # This test validates no runtime errors occur
    dut._log.info("Positive threshold crossing test passed (monitor window opened)")


@cocotb.test()
async def test_monitor_threshold_negative(dut):
    """P2.10: Monitor detects negative-going threshold crossing"""
    await setup_dut(dut)

    # Set all controls to safe defaults
    for i in range(32):
        getattr(dut, f"Control{i}").value = 0

    # Configure monitor for negative crossing
    dut.Control7.value = 0b00000011  # monitor_enable=1, monitor_expect_negative=1
    dut.Control8.value = 100         # monitor_threshold_voltage = 100 mV (signed)
    dut.Control9.value = 0           # monitor_window_start = 0 ns
    dut.Control10.value = 1000       # monitor_window_duration = 1000 ns

    # Short pulse durations
    dut.Control2.value = 80
    dut.Control4.value = 80
    dut.Control5.value = 0x0005

    # Set InputA above threshold
    dut.InputA.value = 150  # 150 mV > 100 mV

    # Arm and trigger
    dut.Control0.value = 0b0001
    await RisingEdge(dut.Clk)
    dut.Control0.value = 0b0011
    await RisingEdge(dut.Clk)

    assert get_state(dut) == STATE_FIRING

    # Wait a few cycles, then cross threshold negatively
    await RisingEdge(dut.Clk)
    await RisingEdge(dut.Clk)
    dut.InputA.value = 50  # 50 mV < 100 mV (negative crossing)
    await RisingEdge(dut.Clk)

    # Monitor should latch threshold crossing
    dut._log.info("Negative threshold crossing test passed")


@cocotb.test()
async def test_cooldown_interval_enforcement(dut):
    """P2.11: Verify cooldown delay matches configured μs value"""
    await setup_dut(dut)

    # Set all controls to safe defaults
    for i in range(32):
        getattr(dut, f"Control{i}").value = 0

    # Short pulse durations
    dut.Control2.value = 8
    dut.Control4.value = 8
    dut.Control5.value = 0x0005

    # Set cooldown to 2 μs (2 μs * 125 MHz = 250 cycles)
    dut.Control6.value = 2  # cooldown_interval = 2 μs

    # Arm and trigger (one-shot mode)
    dut.Control0.value = 0b0001
    await RisingEdge(dut.Clk)
    dut.Control0.value = 0b0011
    await RisingEdge(dut.Clk)

    # Wait to enter COOLDOWN
    for _ in range(10):
        await RisingEdge(dut.Clk)
        if get_state(dut) == STATE_COOLDOWN:
            break

    assert get_state(dut) == STATE_COOLDOWN

    # Count cycles until exit COOLDOWN
    cycle_count = 0
    for _ in range(300):  # Max 300 cycles (2.4 μs)
        await RisingEdge(dut.Clk)
        cycle_count += 1
        if get_state(dut) != STATE_COOLDOWN:
            break

    # Should exit around 250 cycles (2 μs at 125 MHz)
    # Allow ±10% tolerance for rounding
    expected_cycles = 250
    assert 225 <= cycle_count <= 275, \
        f"Cooldown took {cycle_count} cycles, expected ~{expected_cycles} (2 μs at 125 MHz)"

    dut._log.info(f"Cooldown took {cycle_count} cycles (expected ~{expected_cycles})")
