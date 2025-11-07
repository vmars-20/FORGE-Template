"""
P2 - Intermediate Tests for BPD FSM Observer

Standard validation tests covering fault detection and recovery.
Tests verify sign-flip fault indication and state recovery behavior.

Test Coverage:
4. Sign-flip fault from IDLE
5. Sign-flip fault from ARMED
6. Sign-flip fault from FIRING (documentation test)
7. Fault clear recovery

Expected Output: <50 lines (with GHDL aggressive filter)
Expected Runtime: <30 seconds

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


class BpdFsmObserverIntermediateTests(TestBase):
    """P2 - Intermediate tests for BPD FSM Observer"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        await setup_clock(self.dut, period_ns=CLK_PERIOD_NS)

        # Initialize all control registers
        for i in range(32):
            getattr(self.dut, f"Control{i}").value = 0

        await reset_active_high(self.dut, rst_signal="Reset")

    async def run_p2_intermediate(self):
        """Run all P2 intermediate tests"""
        await self.setup()

        # Test 4: Sign-flip fault from IDLE
        await self.test("Sign-flip fault from IDLE", self.test_fault_from_idle)

        # Reset between tests
        await reset_active_low(self.dut)

        # Test 5: Sign-flip fault from ARMED
        await self.test("Sign-flip fault from ARMED", self.test_fault_from_armed)

        # Reset between tests
        await reset_active_low(self.dut)

        # Test 6: Sign-flip fault from FIRING (documentation)
        await self.test("Sign-flip fault from FIRING (doc)", self.test_fault_from_firing_doc)

        # Reset between tests
        await reset_active_low(self.dut)

        # Test 7: Fault clear recovery
        await self.test("Fault clear recovery", self.test_fault_recovery)

    async def test_fault_from_idle(self):
        """Test 4: Observer shows sign-flip when faulting from IDLE (0.0V → ~0.0V)"""
        # Capture IDLE voltage
        voltage_idle = get_observer_voltage(self.dut)

        # Force immediate timeout to trigger FAULT
        self.dut.Control5.value = TestValues.P2_TIMEOUT_S  # trigger_wait_timeout = 0 s
        self.dut.Control0.value = 0b0001  # arm_enable=1
        await RisingEdge(self.dut.Clk)

        # Wait for FAULT state
        for _ in range(10):
            await RisingEdge(self.dut.Clk)
            if get_state(self.dut) == STATE_FAULT:
                break

        state = get_state(self.dut)
        assert state == STATE_FAULT, ErrorMessages.WRONG_STATE.format("FAULT", hex(state))

        # Check observer sign-flip (special case: -0.0V is still ~0.0V)
        await ClockCycles(self.dut.Clk, 1)  # Wait for observer to update
        voltage_fault = get_observer_voltage(self.dut)

        self.log(f"FAULT from IDLE: {voltage_fault:+.3f}V (sign-flip of 0V ≈ 0V)",
                VerbosityLevel.VERBOSE)

        # From IDLE (0.0V), fault should show near 0V (sign-flip of 0 is 0)
        assert abs(voltage_fault) < 0.2, \
            f"FAULT from IDLE should be ~0V (sign-flip of 0V), got {voltage_fault:+.3f}V"

    async def test_fault_from_armed(self):
        """Test 5: Observer shows sign-flip when faulting from ARMED"""
        # Configure and arm
        self.dut.Control5.value = TestValues.P2_TIMEOUT_S  # trigger_wait_timeout = 0 s
        self.dut.Control0.value = 0b0001  # arm_enable=1
        await RisingEdge(self.dut.Clk)
        await ClockCycles(self.dut.Clk, 1)

        # Capture ARMED voltage before fault
        state = get_state(self.dut)
        assert state == STATE_ARMED, ErrorMessages.WRONG_STATE.format("ARMED", hex(state))
        voltage_armed = get_observer_voltage(self.dut)
        expected_armed = calculate_expected_voltage(STATE_ARMED)

        # Wait for timeout → FAULT
        for _ in range(10):
            await RisingEdge(self.dut.Clk)
            if get_state(self.dut) == STATE_FAULT:
                break

        state = get_state(self.dut)
        assert state == STATE_FAULT, ErrorMessages.WRONG_STATE.format("FAULT", hex(state))

        # Check sign-flip
        await ClockCycles(self.dut.Clk, 1)
        voltage_fault = get_observer_voltage(self.dut)

        self.log(f"Sign-flip: {voltage_armed:+.3f}V → {voltage_fault:+.3f}V (magnitude preserved)",
                VerbosityLevel.VERBOSE)

        # Verify sign-flip
        assert voltage_fault < 0, ErrorMessages.FAULT_SHOULD_BE_NEGATIVE.format(voltage_fault)
        assert abs(abs(voltage_fault) - abs(voltage_armed)) < 0.2, \
            ErrorMessages.MAGNITUDE_MISMATCH.format(abs(voltage_armed), abs(voltage_fault))

    async def test_fault_from_firing_doc(self):
        """Test 6: Observer shows sign-flip when faulting from FIRING state (documentation)"""
        # Configure short durations
        self.dut.Control2.value = TestValues.P2_PULSE_DURATION_NS  # trig_out_duration
        self.dut.Control4.value = TestValues.P2_PULSE_DURATION_NS  # intensity_duration
        self.dut.Control5.value = TestValues.P1_TIMEOUT_S          # trigger_wait_timeout

        # Arm and trigger
        self.dut.Control0.value = 0b0001
        await RisingEdge(self.dut.Clk)
        self.dut.Control0.value = 0b0011  # + ext_trigger_in
        await RisingEdge(self.dut.Clk)
        await ClockCycles(self.dut.Clk, 2)

        # Should be in FIRING
        state = get_state(self.dut)
        assert state == STATE_FIRING, ErrorMessages.WRONG_STATE.format("FIRING", hex(state))
        voltage_firing = get_observer_voltage(self.dut)
        expected_firing = calculate_expected_voltage(STATE_FIRING)

        self.log(f"FIRING state: {voltage_firing:+.3f}V (expected {expected_firing:+.3f}V)",
                VerbosityLevel.VERBOSE)
        self.log("NOTE: Fault injection from FIRING requires additional FSM inputs",
                VerbosityLevel.NORMAL)
        self.log("Expected behavior: FIRING voltage → negative magnitude in FAULT state",
                VerbosityLevel.NORMAL)

    async def test_fault_recovery(self):
        """Test 7: Observer returns to IDLE voltage (0.0V) after fault_clear"""
        # Force fault via timeout
        self.dut.Control5.value = TestValues.P2_TIMEOUT_S
        self.dut.Control0.value = 0b0001
        await RisingEdge(self.dut.Clk)

        # Wait for FAULT
        for _ in range(10):
            await RisingEdge(self.dut.Clk)
            if get_state(self.dut) == STATE_FAULT:
                break

        state = get_state(self.dut)
        assert state == STATE_FAULT, ErrorMessages.WRONG_STATE.format("FAULT", hex(state))
        voltage_fault = get_observer_voltage(self.dut)

        # Clear fault
        self.dut.Control0.value = 0b1000  # fault_clear=1
        await RisingEdge(self.dut.Clk)
        await ClockCycles(self.dut.Clk, 1)

        # Should return to IDLE
        state = get_state(self.dut)
        assert state == STATE_IDLE, ErrorMessages.WRONG_STATE.format("IDLE", hex(state))
        voltage_recovered = get_observer_voltage(self.dut)
        expected_idle = calculate_expected_voltage(STATE_IDLE)

        self.log(f"Recovered: {voltage_fault:+.3f}V → {voltage_recovered:+.3f}V",
                VerbosityLevel.VERBOSE)

        assert abs(voltage_recovered - expected_idle) < 0.1, \
            ErrorMessages.VOLTAGE_MISMATCH.format(expected_idle, voltage_recovered)


@cocotb.test()
async def test_bpd_fsm_observer_p2(dut):
    """P2 test entry point"""
    tester = BpdFsmObserverIntermediateTests(dut)
    await tester.run_p2_intermediate()
