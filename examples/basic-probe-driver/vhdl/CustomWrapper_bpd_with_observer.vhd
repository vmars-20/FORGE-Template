--------------------------------------------------------------------------------
-- File: CustomWrapper_bpd_with_observer.vhd
-- Author: AI-assisted implementation (Claude Code)
-- Date: 2025-11-05
-- Version: 1.1 (with FSM Observer integration)
--
-- Description:
--   CustomWrapper architecture for Basic Probe Driver FSM with integrated
--   fsm_observer for oscilloscope-based state debugging.
--
-- Changes from CustomWrapper_bpd.vhd:
--   - Added fsm_observer instantiation
--   - OutputD now carries FSM state as voltage (for scope debugging)
--   - Supports sign-flip fault indication
--
-- FSM State Voltage Mapping:
--   IDLE     (000000) →  0.00V  (V_MIN)
--   ARMED    (000001) →  0.625V (linear interpolation)
--   FIRING   (000010) →  1.25V
--   COOLDOWN (000011) →  1.875V
--   (unused) (000100) →  2.50V  (V_MAX)
--   FAULT    (111111) → -prev_voltage (sign-flip)
--
-- Oscilloscope Usage:
--   1. Connect OutputD to oscilloscope
--   2. Trigger on voltage transitions (state changes)
--   3. Positive voltage = normal state progression
--   4. Negative voltage = FAULT state (magnitude shows previous state)
--
-- Entity: CustomWrapper (defined in CustomWrapper_test_stub.vhd)
--
-- Platform: Moku:Go
-- Clock Frequency: 125 MHz
--
-- References:
--   - CustomWrapper_bpd.vhd (base wrapper)
--   - fsm_observer.vhd (observer pattern)
--   - test_bpd_fsm_observer.py (validation tests)
--   - OSCILLOSCOPE_DEBUGGING_TECHNIQUES.md
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library WORK;
use WORK.forge_serialization_types_pkg.all;
use WORK.forge_serialization_voltage_pkg.all;
use WORK.forge_serialization_time_pkg.all;
use WORK.forge_voltage_5v_bipolar_pkg.all;  -- For fsm_observer

architecture bpd_wrapper_with_observer of CustomWrapper is

    ----------------------------------------------------------------------------
    -- Constants
    ----------------------------------------------------------------------------
    constant CLK_FREQ_HZ : integer := 125000000;  -- Moku:Go clock frequency
    constant GLOBAL_ENABLE : std_logic := '1';    -- Always enabled (no VOLO handshaking)

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
    signal ready_for_updates         : std_logic;  -- Not used in wrapper

    ----------------------------------------------------------------------------
    -- FSM Observer Signals
    ----------------------------------------------------------------------------
    signal fsm_observer_voltage : signed(15 downto 0);  -- Voltage output from observer

begin

    ----------------------------------------------------------------------------
    -- Control Register Unpacking
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
    ----------------------------------------------------------------------------
    probe_monitor_feedback <= InputA;

    ----------------------------------------------------------------------------
    -- Output Packing
    ----------------------------------------------------------------------------

    -- OutputA: Trigger active flag (0x0000 or 0xFFFF)
    OutputA <= (others => trig_out_active_port);

    -- OutputB: Intensity active flag (0x0000 or 0xFFFF)
    OutputB <= (others => intensity_out_active_port);

    -- OutputC: FSM state (6-bit state in lower bits, zero-padded)
    OutputC <= signed("0000000000" & current_state_port);

    -- OutputD: FSM Observer voltage (for oscilloscope debugging)
    OutputD <= fsm_observer_voltage;

    ----------------------------------------------------------------------------
    -- FSM Instantiation
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
            ready_for_updates  => ready_for_updates,

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

    ----------------------------------------------------------------------------
    -- FSM Observer Instantiation
    --
    -- Converts binary FSM state to oscilloscope-visible voltage
    -- - Normal states: 0.0V (IDLE) to 2.5V (linear interpolation)
    -- - FAULT state: Sign-flip of previous normal state voltage
    ----------------------------------------------------------------------------
    FSM_DEBUG: entity WORK.fsm_observer
        generic map (
            NUM_STATES             => 5,        -- Total normal states (IDLE, ARMED, FIRING, COOLDOWN + 1 spare)
            V_MIN                  => 0.0,      -- IDLE voltage
            V_MAX                  => 2.5,      -- Maximum normal state voltage
            FAULT_STATE_THRESHOLD  => 5,        -- States 0-4 are normal, 63 is fault
            STATE_0_NAME           => "IDLE",
            STATE_1_NAME           => "ARMED",
            STATE_2_NAME           => "FIRING",
            STATE_3_NAME           => "COOLDOWN",
            STATE_4_NAME           => "UNUSED"
        )
        port map (
            clk          => Clk,
            reset        => Reset,           -- Active-high reset (matches FSM)
            state_vector => current_state_port,
            voltage_out  => fsm_observer_voltage
        );

end architecture bpd_wrapper_with_observer;
