"""
P1 - Basic Tests for BPD FSM Observer

Minimal, fast tests with reduced verbosity for LLM-friendly output.
These tests verify core FSM observer functionality with small values and minimal logging.

Test Coverage:
1. Reset behavior (IDLE voltage = 0.0V)
2. IDLE → ARMED transition (voltage increase)
3. Normal state progression (voltage stairstep)

Expected Output: <20 lines (with GHDL aggressive filter)
Expected Runtime: <5 seconds

Author: Adapted from proposed_cocotb_test/test_bpd_fsm_observer.py
Date: 2025-11-05
"""

import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "forge-vhdl" / "tests"))

from conftest import setup_clock, reset_active_high
from test_base import TestBase, VerbosityLevel
from bpd_fsm_observer_tests.bpd_fsm_observer_constants import *


class BpdFsmObserverBasicTests(TestBase):
    """P1 - Basic tests for BPD FSM Observer"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        await setup_clock(self.dut, period_ns=CLK_PERIOD_NS)

        # Initialize all control registers
        for i in range(32):
            getattr(self.dut, f"Control{i}").value = 0

        await reset_active_high(self.dut, rst_signal="Reset")

    async def run_p1_basic(self):
        """Run all P1 basic tests"""
        await self.setup()

        # Test 1: Reset behavior
        await self.test("Reset behavior", self.test_reset_behavior)

        # Test 2: IDLE → ARMED transition
        await self.test("IDLE → ARMED transition", self.test_idle_to_armed)

        # Test 3: Basic state progression
        await self.test("State voltage stairstep", self.test_state_progression)

    async def test_reset_behavior(self):
        """Test 1: Observer outputs IDLE voltage (0.0V) after reset"""
        # Check FSM is in IDLE
        state = get_state(self.dut)
        assert state == STATE_IDLE, ErrorMessages.WRONG_STATE.format("IDLE", hex(state))

        # Check observer voltage
        voltage = get_observer_voltage(self.dut)
        expected_v = calculate_expected_voltage(STATE_IDLE)

        self.log(f"IDLE: {voltage:+.3f}V (expected {expected_v:+.3f}V)", VerbosityLevel.VERBOSE)

        assert abs(voltage - expected_v) < 0.1, \
            ErrorMessages.VOLTAGE_MISMATCH.format(expected_v, voltage)

    async def test_idle_to_armed(self):
        """Test 2: Observer tracks IDLE → ARMED transition (0.0V → 0.625V)"""
        # Capture IDLE voltage
        voltage_idle = get_observer_voltage(self.dut)
        expected_idle = calculate_expected_voltage(STATE_IDLE)

        # Configure minimal parameters
        self.dut.Control5.value = TestValues.P1_TIMEOUT_S  # trigger_wait_timeout

        # Arm the FSM
        self.dut.Control0.value = 0b0001  # arm_enable=1
        await RisingEdge(self.dut.Clk)
        await ClockCycles(self.dut.Clk, 1)  # Wait for observer to update

        # Check FSM transitioned to ARMED
        state = get_state(self.dut)
        assert state == STATE_ARMED, ErrorMessages.WRONG_STATE.format("ARMED", hex(state))

        # Check observer voltage updated
        voltage_armed = get_observer_voltage(self.dut)
        expected_armed = calculate_expected_voltage(STATE_ARMED)

        self.log(f"ARMED: {voltage_armed:+.3f}V (expected {expected_armed:+.3f}V)",
                VerbosityLevel.VERBOSE)

        assert voltage_armed > voltage_idle, \
            ErrorMessages.VOLTAGE_NOT_INCREASING.format("ARMED", "IDLE")
        assert abs(voltage_armed - expected_armed) < 0.1, \
            ErrorMessages.VOLTAGE_MISMATCH.format(expected_armed, voltage_armed)

    async def test_state_progression(self):
        """Test 3: Observer tracks state progression (voltage stairstep)"""
        # Return to IDLE: If ARMED from previous test, wait for timeout→FAULT, then clear
        current_state = get_state(self.dut)
        if current_state == STATE_ARMED:
            # Wait for timeout to FAULT (Control5 should already be set to short timeout)
            for _ in range(20):
                await RisingEdge(self.dut.Clk)
                if get_state(self.dut) == STATE_FAULT:
                    break
            # Clear fault to return to IDLE
            self.dut.Control0.value = 0b1000  # fault_clear=1
            await RisingEdge(self.dut.Clk)
            await ClockCycles(self.dut.Clk, 1)
            self.dut.Control0.value = 0b0000  # Clear all
            await RisingEdge(self.dut.Clk)
            await ClockCycles(self.dut.Clk, 1)

        # Configure short durations for fast test
        self.dut.Control2.value = TestValues.P1_PULSE_DURATION_NS  # trig_out_duration
        self.dut.Control4.value = TestValues.P1_PULSE_DURATION_NS  # intensity_duration
        self.dut.Control5.value = TestValues.P1_TIMEOUT_S          # trigger_wait_timeout
        self.dut.Control6.value = TestValues.P1_COOLDOWN_US        # cooldown_interval

        voltages = []
        states_seen = []

        # IDLE
        voltages.append(get_observer_voltage(self.dut))
        states_seen.append("IDLE")

        # Arm → ARMED
        self.dut.Control0.value = 0b0001
        await RisingEdge(self.dut.Clk)
        await ClockCycles(self.dut.Clk, 1)
        voltages.append(get_observer_voltage(self.dut))
        states_seen.append("ARMED")

        # Trigger → FIRING
        self.dut.Control0.value = 0b0011  # arm_enable=1, ext_trigger_in=1
        await RisingEdge(self.dut.Clk)
        await ClockCycles(self.dut.Clk, 1)
        voltages.append(get_observer_voltage(self.dut))
        states_seen.append("FIRING")

        # Wait for COOLDOWN
        for _ in range(15):
            await RisingEdge(self.dut.Clk)
            if get_state(self.dut) == STATE_COOLDOWN:
                break
        await ClockCycles(self.dut.Clk, 1)
        voltages.append(get_observer_voltage(self.dut))
        states_seen.append("COOLDOWN")

        # Verify stairstep progression (monotonic increase)
        for i in range(1, len(voltages)):
            assert voltages[i] > voltages[i-1], \
                ErrorMessages.VOLTAGE_NOT_INCREASING.format(states_seen[i], states_seen[i-1])

        self.log(f"Stairstep: IDLE→ARMED→FIRING→COOLDOWN voltage progression OK",
                VerbosityLevel.NORMAL)


@cocotb.test()
async def test_bpd_fsm_observer_p1(dut):
    """P1 test entry point"""
    tester = BpdFsmObserverBasicTests(dut)
    await tester.run_p1_basic()
