"""Debug test to see what CocoTB can access."""

import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def test_debug(dut):
    """Debug: List all accessible attributes."""
    await Timer(1, unit='ns')

    print("\n=== DUT Attributes ===")
    for attr in dir(dut):
        if not attr.startswith('_'):
            print(f"  - {attr}")

    print("\n=== Done ===")
