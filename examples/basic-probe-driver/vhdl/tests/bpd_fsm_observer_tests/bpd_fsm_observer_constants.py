"""
BPD FSM Observer Test Constants

Shared constants and configurations for all bpd_fsm_observer tests.
Single source of truth for test parameters.

Author: Adapted from proposed_cocotb_test/test_bpd_fsm_observer.py
Date: 2025-11-05
"""

from pathlib import Path


# Module identification
MODULE_NAME = "bpd_fsm_observer"

# HDL sources (relative to tests/ directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
WRAPPER_DIR = PROJECT_ROOT

# External dependencies (aligned with test_configs.py)
FORGE_VHDL = PROJECT_ROOT.parent / "libs" / "forge-vhdl"
FORGE_VHDL_PKG = FORGE_VHDL / "vhdl" / "packages"
FORGE_VHDL_DEBUG = FORGE_VHDL / "vhdl" / "debugging"

HDL_SOURCES = [
    # Serialization packages (forge-vhdl) - MIGRATED from basic_app_*
    FORGE_VHDL_PKG / "forge_serialization_types_pkg.vhd",
    FORGE_VHDL_PKG / "forge_serialization_voltage_pkg.vhd",
    FORGE_VHDL_PKG / "forge_serialization_time_pkg.vhd",

    # FSM Observer dependencies (forge-vhdl)
    FORGE_VHDL_PKG / "forge_voltage_5v_bipolar_pkg.vhd",
    FORGE_VHDL_DEBUG / "fsm_observer.vhd",

    # Core FSM
    SRC_DIR / "basic_probe_driver_custom_inst_main.vhd",

    # Wrapper with observer
    WRAPPER_DIR / "CustomWrapper_test_stub.vhd",
    WRAPPER_DIR / "CustomWrapper_bpd_with_observer.vhd",
]

# Top-level entity name (must be lowercase for GHDL)
HDL_TOPLEVEL = "customwrapper"


# FSM State Constants (from basic_probe_driver_custom_inst_main.vhd)
STATE_IDLE     = 0b000000  # 0
STATE_ARMED    = 0b000001  # 1
STATE_FIRING   = 0b000010  # 2
STATE_COOLDOWN = 0b000011  # 3
STATE_FAULT    = 0b111111  # 63


# FSM Observer Configuration
NUM_STATES = 5              # Total normal states (IDLE, ARMED, FIRING, COOLDOWN + 1 spare)
FAULT_STATE_THRESHOLD = 5   # States 0-4 are normal, 63 is fault
V_MIN = 0.0                 # IDLE voltage
V_MAX = 2.5                 # Maximum normal state voltage


# Clock configuration
CLK_PERIOD_NS = 8  # 125 MHz (Moku:Go)


# Test value sets for different phases
class TestValues:
    """Test value sets for different test phases"""

    # P1 - Basic test values (small, fast)
    P1_TIMEOUT_S = 5            # Short timeout for basic tests
    P1_PULSE_DURATION_NS = 8    # Minimal pulse duration (1 clock cycle)
    P1_COOLDOWN_US = 1          # Minimal cooldown

    # P2 - Intermediate test values
    P2_TIMEOUT_S = 0            # Force immediate timeout for fault tests
    P2_PULSE_DURATION_NS = 160  # Longer pulse for mid-pulse fault injection
    P2_COOLDOWN_US = 1

    # P3 - Comprehensive test values
    P3_RAPID_CYCLES = 2         # Number of rapid FSM cycles to stress test
    P3_WAIT_CYCLES = 150        # Max cycles to wait for state transition


# Voltage conversion utilities
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


def calculate_expected_voltage(state_index: int,
                               num_normal_states: int = NUM_STATES,
                               v_min: float = V_MIN,
                               v_max: float = V_MAX) -> float:
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


# Helper functions for test utilities
def get_state(dut):
    """Extract 6-bit FSM state from OutputC"""
    return dut.OutputC.value.integer & 0x3F


def get_observer_voltage(dut):
    """Get voltage from fsm_observer output (OutputD)"""
    digital = int(dut.OutputD.value.to_signed())
    return digital_to_voltage(digital)


# Error messages for assertions
class ErrorMessages:
    """Standardized error messages for test assertions"""

    WRONG_STATE = "Expected FSM state {}, got {}"
    VOLTAGE_MISMATCH = "Observer voltage mismatch: expected {:.3f}V, got {:.3f}V"
    VOLTAGE_NOT_INCREASING = "{} voltage should be > {} voltage"
    FAULT_SHOULD_BE_NEGATIVE = "FAULT voltage should be negative (sign-flipped), got {:.3f}V"
    MAGNITUDE_MISMATCH = "Magnitude should match previous state: {:.3f}V vs {:.3f}V"
    VOLTAGE_STEP_INCONSISTENT = "Voltage step inconsistent: expected {:.3f}V, got {:.3f}V"
    UNEXPECTED_NEGATIVE = "Unexpected negative voltage during normal operation: {:.3f}V"
