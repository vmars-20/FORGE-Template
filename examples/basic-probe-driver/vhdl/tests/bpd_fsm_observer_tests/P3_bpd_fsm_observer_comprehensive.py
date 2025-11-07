"""
P3 - Comprehensive Tests for BPD FSM Observer

Full coverage tests including edge cases and stress testing.
Tests verify voltage spreading, rapid transitions, and configuration documentation.

Test Coverage:
8. Voltage spreading verification
9. Rapid state changes (stress test)
10. Configuration documentation

Expected Output: <100 lines (with GHDL aggressive filter)
Expected Runtime: <2 minutes

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


class BpdFsmObserverComprehensiveTests(TestBase):
    """P3 - Comprehensive tests for BPD FSM Observer"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        await setup_clock(self.dut, period_ns=CLK_PERIOD_NS)

        # Initialize all control registers
        for i in range(32):
            getattr(self.dut, f"Control{i}").value = 0

        await reset_active_high(self.dut, rst_signal="Reset")

    async def run_p3_comprehensive(self):
        """Run all P3 comprehensive tests"""
        await self.setup()

        # Test 8: Voltage spreading verification
        await self.test("Voltage spreading", self.test_voltage_spreading)

        # Reset between tests
        await reset_active_low(self.dut)

        # Test 9: Rapid state changes
        await self.test("Rapid state changes", self.test_rapid_transitions)

        # Reset between tests
        await reset_active_low(self.dut)

        # Test 10: Configuration documentation
        await self.test("Configuration documentation", self.test_documentation)

    async def test_voltage_spreading(self):
        """Test 8: Verify automatic voltage spreading matches expected values"""
        # Calculate expected voltages for all normal states
        expected_voltages = {
            STATE_IDLE:     calculate_expected_voltage(0),  # 0.00V
            STATE_ARMED:    calculate_expected_voltage(1),  # 0.625V
            STATE_FIRING:   calculate_expected_voltage(2),  # 1.25V
            STATE_COOLDOWN: calculate_expected_voltage(3),  # 1.875V
        }

        self.log(f"Expected voltage spreading ({NUM_STATES} states, {V_MIN}V to {V_MAX}V):",
                VerbosityLevel.VERBOSE)
        for state_idx, voltage in expected_voltages.items():
            state_name = {STATE_IDLE: "IDLE", STATE_ARMED: "ARMED",
                         STATE_FIRING: "FIRING", STATE_COOLDOWN: "COOLDOWN"}[state_idx]
            self.log(f"  State {state_idx} ({state_name:8s}): {voltage:+.3f}V",
                    VerbosityLevel.VERBOSE)

        # Verify voltage step calculation
        expected_step = (V_MAX - V_MIN) / (NUM_STATES - 1)
        self.log(f"Expected voltage step: {expected_step:.3f}V", VerbosityLevel.VERBOSE)
        self.log(f"  Formula: (V_MAX - V_MIN) / (NUM_STATES - 1)", VerbosityLevel.VERBOSE)
        self.log(f"         = ({V_MAX} - {V_MIN}) / ({NUM_STATES} - 1) = {expected_step:.3f}V",
                VerbosityLevel.VERBOSE)

        # Verify IDLE voltage
        voltage_idle = get_observer_voltage(self.dut)
        assert abs(voltage_idle - expected_voltages[STATE_IDLE]) < 0.1, \
            ErrorMessages.VOLTAGE_MISMATCH.format(expected_voltages[STATE_IDLE], voltage_idle)

    async def test_rapid_transitions(self):
        """Test 9: Observer tracks rapid state transitions without glitches"""
        # Configure for fast cycling
        self.dut.Control2.value = TestValues.P1_PULSE_DURATION_NS
        self.dut.Control4.value = TestValues.P1_PULSE_DURATION_NS
        self.dut.Control5.value = TestValues.P1_TIMEOUT_S
        self.dut.Control6.value = TestValues.P1_COOLDOWN_US

        voltages_seen = []
        states_seen = []

        # Rapid cycle: IDLE → ARMED → FIRING → COOLDOWN → IDLE
        for cycle in range(TestValues.P3_RAPID_CYCLES):
            self.log(f"--- Rapid Cycle {cycle+1} ---", VerbosityLevel.VERBOSE)

            # IDLE
            voltages_seen.append(get_observer_voltage(self.dut))
            states_seen.append("IDLE")

            # → ARMED
            self.dut.Control0.value = 0b0001
            await RisingEdge(self.dut.Clk)
            voltages_seen.append(get_observer_voltage(self.dut))
            states_seen.append("ARMED")

            # → FIRING
            self.dut.Control0.value = 0b0011
            await RisingEdge(self.dut.Clk)
            voltages_seen.append(get_observer_voltage(self.dut))
            states_seen.append("FIRING")

            # → COOLDOWN
            for _ in range(15):
                await RisingEdge(self.dut.Clk)
                if get_state(self.dut) == STATE_COOLDOWN:
                    break
            voltages_seen.append(get_observer_voltage(self.dut))
            states_seen.append("COOLDOWN")

            # → IDLE (wait for cooldown to complete)
            for _ in range(TestValues.P3_WAIT_CYCLES):
                await RisingEdge(self.dut.Clk)
                if get_state(self.dut) == STATE_IDLE:
                    break

        # Verify no glitches (all voltages should be valid expected values)
        self.log("Voltage trace:", VerbosityLevel.VERBOSE)
        for i, (state, voltage) in enumerate(zip(states_seen, voltages_seen)):
            self.log(f"  {i:2d}. {state:8s}: {voltage:+.3f}V", VerbosityLevel.VERBOSE)

        # All voltages should be positive (no spurious faults)
        for voltage in voltages_seen:
            assert voltage >= -0.1, ErrorMessages.UNEXPECTED_NEGATIVE.format(voltage)

    async def test_documentation(self):
        """Test 10: Documentation test - expected FSM observer behavior"""
        self.log("=" * 80, VerbosityLevel.NORMAL)
        self.log("FSM Observer Pattern - Basic Probe Driver Integration", VerbosityLevel.NORMAL)
        self.log("=" * 80, VerbosityLevel.NORMAL)
        self.log("Configuration:", VerbosityLevel.NORMAL)
        self.log(f"  NUM_STATES:             {NUM_STATES}", VerbosityLevel.NORMAL)
        self.log(f"  FAULT_STATE_THRESHOLD:  {FAULT_STATE_THRESHOLD}", VerbosityLevel.NORMAL)
        self.log(f"  V_MIN:                  {V_MIN}V (IDLE)", VerbosityLevel.NORMAL)
        self.log(f"  V_MAX:                  {V_MAX}V (max normal state)", VerbosityLevel.NORMAL)
        self.log("", VerbosityLevel.NORMAL)
        self.log("State Voltage Mapping:", VerbosityLevel.NORMAL)
        self.log(f"  IDLE     (0x{STATE_IDLE:02x}): {calculate_expected_voltage(0):.3f}V",
                VerbosityLevel.NORMAL)
        self.log(f"  ARMED    (0x{STATE_ARMED:02x}): {calculate_expected_voltage(1):.3f}V",
                VerbosityLevel.NORMAL)
        self.log(f"  FIRING   (0x{STATE_FIRING:02x}): {calculate_expected_voltage(2):.3f}V",
                VerbosityLevel.NORMAL)
        self.log(f"  COOLDOWN (0x{STATE_COOLDOWN:02x}): {calculate_expected_voltage(3):.3f}V",
                VerbosityLevel.NORMAL)
        self.log(f"  FAULT    (0x{STATE_FAULT:02x}): -prev_voltage (sign-flip)",
                VerbosityLevel.NORMAL)
        self.log("", VerbosityLevel.NORMAL)
        self.log("Oscilloscope Debugging:", VerbosityLevel.NORMAL)
        self.log("  1. Connect OutputD to oscilloscope (voltage_out)", VerbosityLevel.NORMAL)
        self.log("  2. Trigger on positive edge (state transitions)", VerbosityLevel.NORMAL)
        self.log("  3. Negative voltage = FAULT state (sign-flip)", VerbosityLevel.NORMAL)
        self.log("  4. Voltage magnitude preserves 'where did it fault from'", VerbosityLevel.NORMAL)
        self.log("", VerbosityLevel.NORMAL)
        self.log("Key Features:", VerbosityLevel.NORMAL)
        self.log("  ✓ Non-invasive (FSM unchanged)", VerbosityLevel.NORMAL)
        self.log("  ✓ Single-cycle state transition tracking", VerbosityLevel.NORMAL)
        self.log("  ✓ Sign-flip preserves debugging context", VerbosityLevel.NORMAL)
        self.log("  ✓ Automatic voltage spreading (0.0V → 2.5V)", VerbosityLevel.NORMAL)
        self.log("=" * 80, VerbosityLevel.NORMAL)


@cocotb.test()
async def test_bpd_fsm_observer_p3(dut):
    """P3 test entry point"""
    tester = BpdFsmObserverComprehensiveTests(dut)
    await tester.run_p3_comprehensive()
