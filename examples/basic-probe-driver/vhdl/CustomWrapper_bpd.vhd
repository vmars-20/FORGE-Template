--------------------------------------------------------------------------------
-- File: CustomWrapper_bpd.vhd
-- Author: AI-assisted implementation (Claude Code)
-- Date: 2025-11-05
-- Version: 1.0
--
-- Description:
--   CustomWrapper architecture for Basic Probe Driver FSM.
--   Wraps basic_probe_driver_custom_inst_main.vhd for Moku platform integration.
--
-- Entity: CustomWrapper (defined in CustomWrapper_test_stub.vhd)
--
-- Signal Mapping:
--   Control Registers → FSM Inputs:
--     Control0[3:0]    → arm_enable, ext_trigger_in, auto_rearm_enable, fault_clear
--     Control1[15:0]   → trig_out_voltage (signed, mV)
--     Control2[15:0]   → trig_out_duration (unsigned, ns)
--     Control3[15:0]   → intensity_voltage (signed, mV)
--     Control4[15:0]   → intensity_duration (unsigned, ns)
--     Control5[15:0]   → trigger_wait_timeout (unsigned, s)
--     Control6[23:0]   → cooldown_interval (unsigned, μs)
--     Control7[1:0]    → monitor_enable, monitor_expect_negative
--     Control8[15:0]   → monitor_threshold_voltage (signed, mV)
--     Control9[31:0]   → monitor_window_start (unsigned, ns)
--     Control10[31:0]  → monitor_window_duration (unsigned, ns)
--
--   Inputs/Outputs:
--     InputA[15:0]     → probe_monitor_feedback (signed, mV)
--     OutputA[15:0]    → trig_out_active (extended for scope visibility)
--     OutputB[15:0]    → intensity_out_active (extended for scope visibility)
--     OutputC[15:0]    → current_state (6-bit state + padding)
--
-- Platform: Moku:Go
-- Clock Frequency: 125 MHz
--
-- References:
--   - CustomWrapper_test_stub.vhd (entity declaration)
--   - basic_probe_driver_custom_inst_main.vhd (FSM core)
--   - basic_probe_driver.yaml (register specification)
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library WORK;
use WORK.basic_app_types_pkg.all;
use WORK.basic_app_voltage_pkg.all;
use WORK.basic_app_time_pkg.all;

architecture bpd_wrapper of CustomWrapper is

    ----------------------------------------------------------------------------
    -- Constants
    ----------------------------------------------------------------------------
    constant CLK_FREQ_HZ : integer := 125000000;  -- Moku:Go clock frequency
    constant GLOBAL_ENABLE : std_logic := '1';    -- Always enabled (no VOLO handshaking in wrapper)

    ----------------------------------------------------------------------------
    -- Internal Signals - FSM Control Interface
    ----------------------------------------------------------------------------
    signal arm_enable           : std_logic;
    signal ext_trigger_in       : std_logic;
    signal trigger_wait_timeout : unsigned(15 downto 0);
    signal auto_rearm_enable    : std_logic;
    signal fault_clear          : std_logic;

    signal trig_out_voltage     : signed(15 downto 0);
    signal trig_out_duration    : unsigned(15 downto 0);

    signal intensity_voltage    : signed(15 downto 0);
    signal intensity_duration   : unsigned(15 downto 0);

    signal cooldown_interval    : unsigned(23 downto 0);

    signal probe_monitor_feedback    : signed(15 downto 0);
    signal monitor_enable            : std_logic;
    signal monitor_threshold_voltage : signed(15 downto 0);
    signal monitor_expect_negative   : std_logic;
    signal monitor_window_start      : unsigned(31 downto 0);
    signal monitor_window_duration   : unsigned(31 downto 0);

    ----------------------------------------------------------------------------
    -- Internal Signals - FSM Status Interface
    ----------------------------------------------------------------------------
    signal trig_out_active_port      : std_logic;
    signal intensity_out_active_port : std_logic;
    signal current_state_port        : std_logic_vector(5 downto 0);
    signal ready_for_updates         : std_logic;  -- Not used in wrapper (no VOLO)

begin

    ----------------------------------------------------------------------------
    -- Control Register Unpacking
    --
    -- Extract FSM control signals from 32-bit Control registers
    ----------------------------------------------------------------------------

    -- Control0: Lifecycle control bits
    arm_enable        <= Control0(0);
    ext_trigger_in    <= Control0(1);
    auto_rearm_enable <= Control0(2);
    fault_clear       <= Control0(3);

    -- Control1: Trigger output voltage (signed, mV)
    trig_out_voltage  <= signed(Control1(15 downto 0));

    -- Control2: Trigger pulse duration (unsigned, ns)
    trig_out_duration <= unsigned(Control2(15 downto 0));

    -- Control3: Intensity output voltage (signed, mV)
    intensity_voltage <= signed(Control3(15 downto 0));

    -- Control4: Intensity pulse duration (unsigned, ns)
    intensity_duration <= unsigned(Control4(15 downto 0));

    -- Control5: Trigger wait timeout (unsigned, s)
    trigger_wait_timeout <= unsigned(Control5(15 downto 0));

    -- Control6: Cooldown interval (unsigned, μs)
    cooldown_interval <= unsigned(Control6(23 downto 0));

    -- Control7: Monitor control bits
    monitor_enable          <= Control7(0);
    monitor_expect_negative <= Control7(1);

    -- Control8: Monitor threshold voltage (signed, mV)
    monitor_threshold_voltage <= signed(Control8(15 downto 0));

    -- Control9: Monitor window start delay (unsigned, ns)
    monitor_window_start <= unsigned(Control9);

    -- Control10: Monitor window duration (unsigned, ns)
    monitor_window_duration <= unsigned(Control10);

    ----------------------------------------------------------------------------
    -- Input Mapping
    --
    -- Map CustomWrapper inputs to FSM ports
    ----------------------------------------------------------------------------
    probe_monitor_feedback <= InputA;

    ----------------------------------------------------------------------------
    -- Output Packing
    --
    -- Convert FSM status signals to 16-bit outputs for oscilloscope visibility
    ----------------------------------------------------------------------------

    -- OutputA: Trigger active flag (extended to 16-bit: 0x0000 or 0xFFFF)
    OutputA <= (others => trig_out_active_port);

    -- OutputB: Intensity active flag (extended to 16-bit: 0x0000 or 0xFFFF)
    OutputB <= (others => intensity_out_active_port);

    -- OutputC: FSM state (6-bit state in lower bits, zero-padded)
    OutputC <= signed("0000000000" & current_state_port);

    -- OutputD: Unused (drive to zero)
    OutputD <= (others => '0');

    ----------------------------------------------------------------------------
    -- FSM Instantiation
    --
    -- Connect basic_probe_driver_custom_inst_main to wrapper signals
    ----------------------------------------------------------------------------
    BPD_FSM: entity WORK.basic_probe_driver_custom_inst_main
        generic map (
            CLK_FREQ_HZ => CLK_FREQ_HZ
        )
        port map (
            -- Clock and Reset
            Clk                => Clk,
            Reset              => Reset,
            global_enable      => GLOBAL_ENABLE,
            ready_for_updates  => ready_for_updates,  -- Not used in this wrapper

            -- Application Signals (Typed)
            arm_enable                => arm_enable,
            ext_trigger_in            => ext_trigger_in,
            trigger_wait_timeout      => trigger_wait_timeout,
            auto_rearm_enable         => auto_rearm_enable,
            fault_clear               => fault_clear,

            trig_out_voltage          => trig_out_voltage,
            trig_out_duration         => trig_out_duration,

            intensity_voltage         => intensity_voltage,
            intensity_duration        => intensity_duration,

            cooldown_interval         => cooldown_interval,

            probe_monitor_feedback    => probe_monitor_feedback,
            monitor_enable            => monitor_enable,
            monitor_threshold_voltage => monitor_threshold_voltage,
            monitor_expect_negative   => monitor_expect_negative,
            monitor_window_start      => monitor_window_start,
            monitor_window_duration   => monitor_window_duration,

            -- Status Outputs
            trig_out_active_port      => trig_out_active_port,
            intensity_out_active_port => intensity_out_active_port,
            current_state_port        => current_state_port
        );

end architecture bpd_wrapper;
