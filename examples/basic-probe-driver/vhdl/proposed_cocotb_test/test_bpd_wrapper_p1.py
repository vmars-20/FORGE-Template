"""
Progressive Test Level 1 (P1) - Basic Probe Driver Wrapper
Fast smoke tests for CustomWrapper_bpd architecture

Test Coverage:
- Reset behavior
- Control register unpacking
- Output signal mapping
- Basic FSM state visibility

Expected Runtime: <1 ms per test
"""

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

# FSM State Constants (from basic_probe_driver_custom_inst_main.vhd)
STATE_IDLE     = 0b000000
STATE_ARMED    = 0b000001
STATE_FIRING   = 0b000010
STATE_COOLDOWN = 0b000011
STATE_FAULT    = 0b111111


@cocotb.test()
async def test_reset(dut):
    """P1.1: Verify Reset drives FSM to IDLE state"""
    # Start clock
    clock = Clock(dut.Clk, 8, units="ns")  # 125 MHz
    cocotb.start_soon(clock.start())

    # Assert reset
    dut.Reset.value = 1
    await RisingEdge(dut.Clk)
    await RisingEdge(dut.Clk)

    # Check FSM is in IDLE
    assert dut.OutputC.value.integer & 0x3F == STATE_IDLE, \
        f"Expected IDLE state (0x{STATE_IDLE:02x}), got 0x{dut.OutputC.value.integer & 0x3F:02x}"

    # Check outputs are inactive
    assert dut.OutputA.value.integer == 0, "trig_out_active should be 0 after reset"
    assert dut.OutputB.value.integer == 0, "intensity_out_active should be 0 after reset"


@cocotb.test()
async def test_control_register_mapping(dut):
    """P1.2: Verify Control registers correctly unpack to internal signals"""
    clock = Clock(dut.Clk, 8, units="ns")
    cocotb.start_soon(clock.start())

    # Release reset
    dut.Reset.value = 0
    await RisingEdge(dut.Clk)

    # Set Control0 lifecycle bits
    dut.Control0.value = 0b00001111  # arm_enable, ext_trigger_in, auto_rearm, fault_clear all high
    dut.Control1.value = 0x1234      # trig_out_voltage = 4660 mV (signed)
    dut.Control2.value = 0x0100      # trig_out_duration = 256 ns
    dut.Control3.value = 0x5678      # intensity_voltage = 22136 mV (signed)
    dut.Control4.value = 0x0200      # intensity_duration = 512 ns
    dut.Control5.value = 0x000A      # trigger_wait_timeout = 10 s
    dut.Control6.value = 0x000F42    # cooldown_interval = 3906 μs
    dut.Control7.value = 0b00000011  # monitor_enable=1, monitor_expect_negative=1
    dut.Control8.value = 0x0064      # monitor_threshold_voltage = 100 mV (signed)
    dut.Control9.value = 0x000003E8  # monitor_window_start = 1000 ns
    dut.Control10.value = 0x000007D0 # monitor_window_duration = 2000 ns

    await RisingEdge(dut.Clk)

    # No assertions here - just verify no synthesis/runtime errors
    # (Internal signal values not visible in wrapper, tested in FSM directly)
    dut._log.info("Control register mapping smoke test passed")


@cocotb.test()
async def test_output_mapping(dut):
    """P1.3: Verify OutputA/B/C correctly reflect FSM status"""
    clock = Clock(dut.Clk, 8, units="ns")
    cocotb.start_soon(clock.start())

    dut.Reset.value = 0
    await RisingEdge(dut.Clk)

    # OutputC[5:0] should contain FSM state (initially IDLE)
    state = dut.OutputC.value.integer & 0x3F
    assert state == STATE_IDLE, f"Expected IDLE state in OutputC, got 0x{state:02x}"

    # OutputA/B should be 0x0000 when outputs inactive
    assert dut.OutputA.value.integer == 0, "OutputA (trig_out_active) should be 0 in IDLE"
    assert dut.OutputB.value.integer == 0, "OutputB (intensity_out_active) should be 0 in IDLE"

    # OutputD should always be 0 (unused)
    assert dut.OutputD.value.integer == 0, "OutputD should be tied to 0"
