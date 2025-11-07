"""
Progressive CocoTB Testbench for BPD FSM Observer

Uses TestBase framework for progressive testing (P1/P2/P3).
Test level controlled by TEST_LEVEL environment variable:
- P1_BASIC (default): Minimal tests, <20 lines output
- P2_INTERMEDIATE: Standard validation tests
- P3_COMPREHENSIVE: Full test suite with edge cases

Usage:
    # P1 only (minimal output, LLM-optimized)
    uv run python ../forge-vhdl/tests/run.py bpd_fsm_observer

    # P2 (standard validation)
    TEST_LEVEL=P2_INTERMEDIATE uv run python ../forge-vhdl/tests/run.py bpd_fsm_observer

    # P3 (comprehensive)
    TEST_LEVEL=P3_COMPREHENSIVE uv run python ../forge-vhdl/tests/run.py bpd_fsm_observer

Author: Adapted from proposed_cocotb_test/test_bpd_fsm_observer.py
Date: 2025-11-05
"""

import cocotb
import sys
import os
from pathlib import Path

# Add test infrastructure to path
FORGE_VHDL_TESTS = Path(__file__).parent.parent.parent / "libs" / "forge-vhdl" / "tests"
sys.path.insert(0, str(FORGE_VHDL_TESTS))
sys.path.insert(0, str(Path(__file__).parent))

from test_base import TestBase, TestLevel


# Determine which test level to run
def get_test_level() -> TestLevel:
    """Get test level from environment variable"""
    level_str = os.environ.get("TEST_LEVEL", "P1_BASIC")
    return TestLevel[level_str]


@cocotb.test()
async def test_bpd_fsm_observer_progressive(dut):
    """
    Progressive test entry point.
    Imports and runs appropriate test level based on TEST_LEVEL environment variable.
    """
    test_level = get_test_level()

    if test_level == TestLevel.P1_BASIC:
        # Import and run P1 tests
        from bpd_fsm_observer_tests.P1_bpd_fsm_observer_basic import BpdFsmObserverBasicTests
        tester = BpdFsmObserverBasicTests(dut)
        await tester.run_p1_basic()

    elif test_level == TestLevel.P2_INTERMEDIATE:
        # Import and run P2 tests
        from bpd_fsm_observer_tests.P2_bpd_fsm_observer_intermediate import BpdFsmObserverIntermediateTests
        tester = BpdFsmObserverIntermediateTests(dut)
        await tester.run_p2_intermediate()

    elif test_level == TestLevel.P3_COMPREHENSIVE:
        # Import and run P3 tests
        from bpd_fsm_observer_tests.P3_bpd_fsm_observer_comprehensive import BpdFsmObserverComprehensiveTests
        tester = BpdFsmObserverComprehensiveTests(dut)
        await tester.run_p3_comprehensive()

    elif test_level == TestLevel.P4_EXHAUSTIVE:
        # P4 not implemented yet
        dut._log.warning("P4_EXHAUSTIVE not implemented for bpd_fsm_observer")
        from bpd_fsm_observer_tests.P3_bpd_fsm_observer_comprehensive import BpdFsmObserverComprehensiveTests
        tester = BpdFsmObserverComprehensiveTests(dut)
        await tester.run_p3_comprehensive()
