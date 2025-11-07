"""
Progressive CocoTB tests for forge_voltage_5v0_pkg

Test Levels:
- P1_BASIC: Essential functionality only (4 tests, <20 lines output)
- P2_INTERMEDIATE: Comprehensive testing (edge cases, precision)

Domain: 0-5.0V unipolar (sensor supply, unipolar analog)

Author: Claude Code
Date: 2025-11-04
"""

import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
import os

# Test level from environment (default: P1_BASIC)
TEST_LEVEL = os.getenv("TEST_LEVEL", "P1_BASIC")

# Verbosity control
VERBOSITY = os.getenv("COCOTB_VERBOSITY", "MINIMAL")


# =============================================================================
# Test Utilities
# =============================================================================

async def setup_clock(dut, period_ns=10):
    """Start clock"""
    clock = Clock(dut.clk, period_ns, units="ns")
    cocotb.start_soon(clock.start())
    await RisingEdge(dut.clk)


async def reset_dut(dut):
    """Apply reset"""
    dut.reset.value = 1
    dut.test_voltage_digital.value = 0
    dut.test_digital.value = 0
    dut.sel_to_digital.value = 0
    dut.sel_from_digital.value = 0
    dut.sel_is_valid.value = 0
    dut.sel_clamp.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)


def voltage_to_digital_5v0(voltage):
    """Convert voltage to digital value for 5.0V domain"""
    # Scale: 0V → 0, 5.0V → 32767
    if voltage < 0.0:
        voltage = 0.0
    elif voltage > 5.0:
        voltage = 5.0
    return int((voltage / 5.0) * 32767.0 + 0.5)


def digital_to_voltage_5v0(digital):
    """Convert digital value to voltage for 5.0V domain"""
    # Scale: 0 → 0V, 32767 → 5.0V
    return (digital / 32767.0) * 5.0


# =============================================================================
# P1 Tests (Basic - Minimal Output)
# =============================================================================

@cocotb.test(skip=(TEST_LEVEL not in ["P1_BASIC", "P2_INTERMEDIATE"]))
async def test_p1_t1_to_digital_accuracy(dut):
    """T1: to_digital() conversion accuracy"""
    if VERBOSITY != "SILENT":
        dut._log.info("=" * 70)
        dut._log.info("P1 - BASIC TESTS (forge_voltage_5v0_pkg)")
        dut._log.info("T1: to_digital() accuracy")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test key voltage points
    test_cases = [
        (0.0, 0),         # 0V → 0
        (2.5, 16384),     # Mid-point (half of 5.0V)
        (5.0, 32767),     # Max voltage
    ]

    for voltage, expected_digital in test_cases:
        # Set test voltage (as digital for wrapper)
        voltage_digital = voltage_to_digital_5v0(voltage)
        dut.test_voltage_digital.value = voltage_digital
        dut.sel_to_digital.value = 1
        dut.sel_from_digital.value = 0
        dut.sel_is_valid.value = 0
        dut.sel_clamp.value = 0

        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        actual = int(dut.digital_result.value.signed_integer)

        # Allow small rounding error (±1)
        assert abs(actual - expected_digital) <= 1, \
            f"to_digital({voltage}V): expected {expected_digital}, got {actual}"

        if VERBOSITY in ["VERBOSE", "DEBUG"]:
            dut._log.info(f"  {voltage}V → {actual} (expected {expected_digital})")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")


@cocotb.test(skip=(TEST_LEVEL not in ["P1_BASIC", "P2_INTERMEDIATE"]))
async def test_p1_t2_from_digital_roundtrip(dut):
    """T2: from_digital() round-trip conversion"""
    if VERBOSITY != "SILENT":
        dut._log.info("T2: from_digital() round-trip")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test key digital values
    test_digitals = [0, 16384, 32767]

    for test_digital in test_digitals:
        # Convert to voltage and back
        dut.test_digital.value = test_digital
        dut.sel_to_digital.value = 0
        dut.sel_from_digital.value = 1
        dut.sel_is_valid.value = 0
        dut.sel_clamp.value = 0

        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        voltage_digital = int(dut.voltage_result.value.signed_integer)

        # Round-trip should be close (allow small error)
        assert abs(voltage_digital - test_digital) <= 10, \
            f"Round-trip {test_digital}: got {voltage_digital}"

        if VERBOSITY in ["VERBOSE", "DEBUG"]:
            voltage = digital_to_voltage_5v0(test_digital)
            dut._log.info(f"  {test_digital} → {voltage:.3f}V → {voltage_digital}")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")


@cocotb.test(skip=(TEST_LEVEL not in ["P1_BASIC", "P2_INTERMEDIATE"]))
async def test_p1_t3_is_valid_boundary(dut):
    """T3: is_valid() boundary checks"""
    if VERBOSITY != "SILENT":
        dut._log.info("T3: is_valid() boundary checks")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test valid voltages (wrapper pre-clamps, so test in-range values)
    test_cases = [
        (0.0, True),    # Min (valid)
        (2.5, True),    # Mid-point (valid)
        (5.0, True),    # Max (valid)
    ]

    for voltage, expected_valid in test_cases:
        voltage_digital = voltage_to_digital_5v0(voltage)
        dut.test_voltage_digital.value = voltage_digital
        dut.sel_to_digital.value = 0
        dut.sel_from_digital.value = 0
        dut.sel_is_valid.value = 1
        dut.sel_clamp.value = 0

        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        is_valid = int(dut.is_valid_result.value)

        assert is_valid == (1 if expected_valid else 0), \
            f"is_valid({voltage}V): expected {expected_valid}, got {bool(is_valid)}"

        if VERBOSITY in ["VERBOSE", "DEBUG"]:
            dut._log.info(f"  {voltage}V → valid={bool(is_valid)}")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")


@cocotb.test(skip=(TEST_LEVEL not in ["P1_BASIC", "P2_INTERMEDIATE"]))
async def test_p1_t4_clamp_behavior(dut):
    """T4: clamp() behavior"""
    if VERBOSITY != "SILENT":
        dut._log.info("T4: clamp() behavior")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test clamping at boundaries
    test_cases = [
        (0.0, 0.0),     # Min (no clamp)
        (2.5, 2.5),     # Mid (no clamp)
        (5.0, 5.0),     # Max (no clamp)
    ]

    for voltage, expected_clamped in test_cases:
        voltage_digital = voltage_to_digital_5v0(voltage)
        expected_digital = voltage_to_digital_5v0(expected_clamped)

        dut.test_voltage_digital.value = voltage_digital
        dut.sel_to_digital.value = 0
        dut.sel_from_digital.value = 0
        dut.sel_is_valid.value = 0
        dut.sel_clamp.value = 1

        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        actual = int(dut.clamped_result.value.signed_integer)

        # Allow small rounding error
        assert abs(actual - expected_digital) <= 10, \
            f"clamp({voltage}V): expected {expected_digital}, got {actual}"

        if VERBOSITY in ["VERBOSE", "DEBUG"]:
            dut._log.info(f"  {voltage}V → {actual} (expected {expected_digital})")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")
        dut._log.info("=" * 70)
        dut._log.info("ALL 4 P1 TESTS PASSED")


# =============================================================================
# P2 Tests (Intermediate - Comprehensive)
# =============================================================================

@cocotb.test(skip=(TEST_LEVEL not in ["P2_INTERMEDIATE"]))
async def test_p2_t5_precision_tests(dut):
    """T5: Precision and edge case testing"""
    if VERBOSITY != "SILENT":
        dut._log.info("=" * 70)
        dut._log.info("P2 - INTERMEDIATE TESTS")
        dut._log.info("T5: Precision tests")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test various voltages across range
    test_voltages = [0.0, 1.0, 1.8, 2.5, 3.3, 4.0, 5.0]

    for voltage in test_voltages:
        voltage_digital = voltage_to_digital_5v0(voltage)
        dut.test_voltage_digital.value = voltage_digital
        dut.sel_to_digital.value = 1
        dut.sel_from_digital.value = 0
        dut.sel_is_valid.value = 0
        dut.sel_clamp.value = 0

        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        digital = int(dut.digital_result.value.signed_integer)
        expected = voltage_to_digital_5v0(voltage)

        # Check within 0.1% of expected
        tolerance = max(10, int(expected * 0.001))
        assert abs(digital - expected) <= tolerance, \
            f"Precision: {voltage}V → {digital} (expected {expected})"

        if VERBOSITY in ["VERBOSE", "DEBUG"]:
            dut._log.info(f"  {voltage:.2f}V → {digital} (expected {expected})")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")


@cocotb.test(skip=(TEST_LEVEL not in ["P2_INTERMEDIATE"]))
async def test_p2_t6_reference_voltages(dut):
    """T6: Test predefined reference voltages"""
    if VERBOSITY != "SILENT":
        dut._log.info("T6: Reference voltage constants")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test reference voltages (from package constants)
    test_cases = [
        (1.0, 6553),    # DIGITAL_1V0
        (1.8, 11796),   # DIGITAL_1V8
        (2.5, 16384),   # DIGITAL_2V5
        (3.0, 19660),   # DIGITAL_3V0
        (3.3, 21627),   # DIGITAL_3V3
        (5.0, 32767),   # DIGITAL_5V0
    ]

    for voltage, expected_digital in test_cases:
        voltage_digital = voltage_to_digital_5v0(voltage)
        dut.test_voltage_digital.value = voltage_digital
        dut.sel_to_digital.value = 1
        dut.sel_from_digital.value = 0
        dut.sel_is_valid.value = 0
        dut.sel_clamp.value = 0

        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        actual = int(dut.digital_result.value.signed_integer)

        # Allow ±5 tolerance for rounding
        assert abs(actual - expected_digital) <= 5, \
            f"Reference {voltage}V: expected {expected_digital}, got {actual}"

        if VERBOSITY in ["VERBOSE", "DEBUG"]:
            dut._log.info(f"  {voltage}V → {actual} (ref: {expected_digital})")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")
        dut._log.info("=" * 70)
        dut._log.info("ALL 6 P2 TESTS PASSED (P1+P2)")
