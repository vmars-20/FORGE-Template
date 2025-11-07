"""
Test configurations for forge-vhdl CocoTB tests.
Auto-discovered by run.py - no Makefile needed!

Module categories:
- utilities: Reusable VHDL utility components
- packages: VHDL packages with functions/constants
- debugging: Debug infrastructure components
- loaders: Memory initialization components

Author: Moku Instrument Forge Team (adapted from EZ-EMFI)
Date: 2025-11-04
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
VHDL = PROJECT_ROOT / "vhdl"
VHDL_PKG = VHDL / "packages"
VHDL_UTIL = VHDL / "utilities"
VHDL_DEBUG = VHDL / "debugging"
VHDL_LOADER = VHDL / "loader"
TESTS = PROJECT_ROOT / "tests"


@dataclass
class TestConfig:
    """Configuration for a single CocoTB test"""
    name: str
    sources: List[Path]
    toplevel: str
    test_module: str
    category: str = "misc"
    ghdl_args: List[str] = field(default_factory=lambda: ["--std=08"])


# ==================================================================================
# Test Configurations
# ==================================================================================

TESTS_CONFIG = {
    # === Utilities (forge_util_*) ===

    "forge_util_clk_divider": TestConfig(
        name="forge_util_clk_divider",
        sources=[
            VHDL_UTIL / "forge_util_clk_divider.vhd",
        ],
        toplevel="forge_util_clk_divider",
        test_module="test_forge_util_clk_divider_progressive",
        category="utilities",
    ),

    # === Packages ===

    "forge_lut_pkg": TestConfig(
        name="forge_lut_pkg",
        sources=[
            VHDL_PKG / "forge_lut_pkg.vhd",              # LUT package
            TESTS / "forge_lut_pkg_tb_wrapper.vhd",      # Testbench wrapper
        ],
        toplevel="forge_lut_pkg_tb_wrapper",
        test_module="test_forge_lut_pkg_progressive",
        category="packages",
    ),

    "forge_voltage_3v3_pkg": TestConfig(
        name="forge_voltage_3v3_pkg",
        sources=[
            VHDL_PKG / "forge_voltage_3v3_pkg.vhd",
            TESTS / "forge_voltage_3v3_pkg_tb_wrapper.vhd",
        ],
        toplevel="forge_voltage_3v3_pkg_tb_wrapper",
        test_module="test_forge_voltage_3v3_pkg_progressive",
        category="packages",
    ),

    "forge_voltage_5v0_pkg": TestConfig(
        name="forge_voltage_5v0_pkg",
        sources=[
            VHDL_PKG / "forge_voltage_5v0_pkg.vhd",
            TESTS / "forge_voltage_5v0_pkg_tb_wrapper.vhd",
        ],
        toplevel="forge_voltage_5v0_pkg_tb_wrapper",
        test_module="test_forge_voltage_5v0_pkg_progressive",
        category="packages",
    ),

    "forge_voltage_5v_bipolar_pkg": TestConfig(
        name="forge_voltage_5v_bipolar_pkg",
        sources=[
            VHDL_PKG / "forge_voltage_5v_bipolar_pkg.vhd",
            TESTS / "forge_voltage_5v_bipolar_pkg_tb_wrapper.vhd",
        ],
        toplevel="forge_voltage_5v_bipolar_pkg_tb_wrapper",
        test_module="test_forge_voltage_5v_bipolar_pkg_progressive",
        category="packages",
    ),

    # Note: Additional components that can have tests added:
    # - forge_voltage_threshold_trigger_core (utilities)
    # - fsm_observer (debugging)
    # - forge_bram_loader (loaders)
    # - forge_common_pkg (packages)
}


# ==================================================================================
# Helper Functions
# ==================================================================================

def get_test_names() -> List[str]:
    """Get sorted list of all test names"""
    return sorted(TESTS_CONFIG.keys())


def get_tests_by_category(category: str) -> dict:
    """Get tests filtered by category"""
    return {
        name: config
        for name, config in TESTS_CONFIG.items()
        if config.category == category
    }


def get_categories() -> List[str]:
    """Get sorted list of all unique categories"""
    return sorted(set(config.category for config in TESTS_CONFIG.values()))


def validate_test_files() -> dict:
    """
    Validate that all configured test files exist.
    Returns dict of {test_name: missing_files}
    """
    issues = {}

    for test_name, config in TESTS_CONFIG.items():
        missing = []

        # Check VHDL sources
        for source in config.sources:
            if not source.exists():
                missing.append(str(source))

        # Check Python test module
        test_file = TESTS / f"{config.test_module}.py"
        if not test_file.exists():
            missing.append(str(test_file))

        if missing:
            issues[test_name] = missing

    return issues


if __name__ == "__main__":
    # CLI for validating configuration
    print("forge-vhdl CocoTB Test Configuration")
    print("=" * 70)
    print(f"Total tests: {len(TESTS_CONFIG)}")
    print(f"\nCategories: {', '.join(get_categories())}")
    print(f"\nTests by category:")
    for category in get_categories():
        tests = get_tests_by_category(category)
        print(f"  {category}: {len(tests)} tests")
        for test_name in sorted(tests.keys()):
            print(f"    - {test_name}")

    # Validate files
    print("\nValidating test files...")
    issues = validate_test_files()
    if issues:
        print(f"\n⚠️  Found {len(issues)} tests with missing files:")
        for test_name, missing_files in issues.items():
            print(f"\n  {test_name}:")
            for file in missing_files:
                print(f"    - {file}")
    else:
        print("✅ All test files validated successfully!")
