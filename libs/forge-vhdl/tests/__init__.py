"""
CocotB Progressive Testing Framework

This package contains the test infrastructure and examples for
LLM-optimized progressive VHDL testing with CocotB.

Key components:
- test_base.py: Progressive test framework (P1/P2/P3/P4)
- conftest.py: Shared test utilities
- run.py: Test runner with GHDL output filtering
- test_configs.py: Test registry

Example tests:
- test_volo_clk_divider_progressive.py
- test_volo_voltage_pkg_progressive.py
- test_volo_lut_pkg_progressive.py

Usage:
    python tests/run.py <module_name>
    python tests/run.py --list
    python tests/run.py --all

Environment variables:
    TEST_LEVEL: P1_BASIC (default), P2_INTERMEDIATE, P3_COMPREHENSIVE, P4_EXHAUSTIVE
    COCOTB_VERBOSITY: SILENT, MINIMAL (default), NORMAL, VERBOSE, DEBUG
    GHDL_FILTER_LEVEL: aggressive, normal (default), minimal, none

Author: EZ-EMFI Team
"""

# Package metadata
__version__ = "1.0.0"
__author__ = "EZ-EMFI Team"

# Note: This file can remain empty if you prefer.
# It exists primarily to make Python treat 'tests/' as a package,
# which some Python environments require.
#
# The actual imports are handled via sys.path.insert() in run.py
# to avoid circular dependencies and make the test runner work
# when invoked from any directory.
