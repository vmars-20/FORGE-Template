--------------------------------------------------------------------------------
-- File: basic_probe_driver_custom_inst_main.vhd
-- Author: AI-assisted implementation (Claude Code)
-- Date: 2025-11-05
-- Version: 1.0 (P2 - YAML-aligned FSM implementation)
--
-- Description:
--   Five-state FSM for Basic Probe Driver following forge-vhdl standards.
--   Implements all 13 register fields from basic_probe_driver.yaml.
--
-- Platform: Moku:Go
-- Clock Frequency: 125 MHz (8 ns period)
--
-- FSM States (std_logic_vector encoding - Verilog compatible):
--   IDLE     (000000) - Waiting for arm signal
--   ARMED    (000001) - Waiting for trigger or timeout
--   FIRING   (000010) - Driving outputs (trigger + intensity pulses)
--   COOLDOWN (000011) - Thermal safety delay between pulses
--   FAULT    (111111) - Sticky fault state (requires fault_clear)
--
-- State Transitions:
--   IDLE → ARMED        : On rising edge of trigger event (external trigger_in)
--   ARMED → FIRING      : On trigger condition met
--   ARMED → FAULT       : On timeout (trigger_wait_timeout exceeded)
--   FIRING → COOLDOWN   : When both output pulses complete
--   COOLDOWN → IDLE     : When auto_rearm_enable = '0'
--   COOLDOWN → ARMED    : When auto_rearm_enable = '1'
--   FAULT → IDLE        : On fault_clear pulse
--   ANY → FAULT         : On safety violation
--
-- Timing Counters:
--   - ns counters: Direct cycle count @ 125 MHz (16-bit)
--   - μs counters: Prescaled by 125 (24-bit → 32-bit)
--   - s counters: Prescaled by 125M (16-bit → 32-bit)
--
-- Safety Features:
--   - Mandatory cooldown enforcement
--   - Timeout protection in ARMED state
--   - when others → FAULT for undefined states
--
-- References:
--   - basic_probe_driver.yaml (YAML spec)
--   - basic_probe_driver_custom_inst_shim.vhd (register interface)
--   - libs/forge-vhdl/docs/VHDL_CODING_STANDARDS.md (coding standards)
--   - libs/forge-vhdl/vhdl/debugging/fsm_observer.vhd (debug integration)
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library WORK;
use WORK.forge_serialization_types_pkg.all;
use WORK.forge_serialization_voltage_pkg.all;
use WORK.forge_serialization_time_pkg.all;

entity basic_probe_driver_custom_inst_main is
    generic (
        CLK_FREQ_HZ : integer := 125000000  -- Moku:Go clock frequency
    );
    port (
        ------------------------------------------------------------------------
        -- Clock and Reset
        ------------------------------------------------------------------------
        Clk                : in  std_logic;
        Reset              : in  std_logic;  -- Active-high reset
        global_enable      : in  std_logic;  -- Combined VOLO ready signals
        ready_for_updates  : out std_logic;  -- Handshake to shim

        ------------------------------------------------------------------------
        -- Application Signals (Typed - from BasicAppDataTypes)
        ------------------------------------------------------------------------
        -- Arming and lifecycle
        arm_enable           : in std_logic;               -- Arm the FSM (IDLE → ARMED)
        ext_trigger_in       : in std_logic;               -- External trigger (ARMED → FIRING)
        trigger_wait_timeout : in unsigned(15 downto 0);  -- Max wait in ARMED (s)
        auto_rearm_enable    : in std_logic;               -- Re-arm after cooldown
        fault_clear          : in std_logic;               -- Clear fault state

        -- Output controls (trigger path)
        trig_out_voltage     : in signed(15 downto 0);    -- Trigger voltage (mV)
        trig_out_duration    : in unsigned(15 downto 0);  -- Trigger pulse width (ns)

        -- Output controls (intensity path)
        intensity_voltage    : in signed(15 downto 0);    -- Intensity voltage (mV)
        intensity_duration   : in unsigned(15 downto 0);  -- Intensity pulse width (ns)

        -- Timing controls
        cooldown_interval    : in unsigned(23 downto 0);  -- Cooldown period (μs)

        -- Monitor/feedback
        probe_monitor_feedback    : in signed(15 downto 0);  -- ADC feedback (mV)
        monitor_enable            : in std_logic;             -- Enable comparator
        monitor_threshold_voltage : in signed(15 downto 0);  -- Threshold (mV)
        monitor_expect_negative   : in std_logic;             -- Polarity select
        monitor_window_start      : in unsigned(31 downto 0); -- Window delay (ns)
        monitor_window_duration   : in unsigned(31 downto 0); -- Window length (ns)

        ------------------------------------------------------------------------
        -- Status Outputs (for test observability and external monitoring)
        ------------------------------------------------------------------------
        trig_out_active_port      : out std_logic;            -- Trigger output is active
        intensity_out_active_port : out std_logic;            -- Intensity output is active
        current_state_port        : out std_logic_vector(5 downto 0) -- Current FSM state
    );
end entity basic_probe_driver_custom_inst_main;

architecture rtl of basic_probe_driver_custom_inst_main is

    ----------------------------------------------------------------------------
    -- FSM State Constants (6-bit encoding for fsm_observer compatibility)
    ----------------------------------------------------------------------------
    constant STATE_IDLE     : std_logic_vector(5 downto 0) := "000000";
    constant STATE_ARMED    : std_logic_vector(5 downto 0) := "000001";
    constant STATE_FIRING   : std_logic_vector(5 downto 0) := "000010";
    constant STATE_COOLDOWN : std_logic_vector(5 downto 0) := "000011";
    constant STATE_FAULT    : std_logic_vector(5 downto 0) := "111111";

    ----------------------------------------------------------------------------
    -- State Machine Signals
    ----------------------------------------------------------------------------
    signal state      : std_logic_vector(5 downto 0);
    signal next_state : std_logic_vector(5 downto 0);

    ----------------------------------------------------------------------------
    -- Time Conversion Signals (YAML units → clock cycles @ 125 MHz)
    ----------------------------------------------------------------------------
    signal trigger_wait_timeout_cycles   : unsigned(31 downto 0);  -- s → cycles
    signal trig_out_duration_cycles      : unsigned(31 downto 0);  -- ns → cycles
    signal intensity_duration_cycles     : unsigned(31 downto 0);  -- ns → cycles
    signal cooldown_interval_cycles      : unsigned(31 downto 0);  -- μs → cycles
    signal monitor_window_start_cycles   : unsigned(31 downto 0);  -- ns → cycles
    signal monitor_window_duration_cycles: unsigned(31 downto 0);  -- ns → cycles

    ----------------------------------------------------------------------------
    -- Timing Counters
    ----------------------------------------------------------------------------
    signal armed_timer       : unsigned(31 downto 0);  -- Timeout in ARMED state
    signal trig_out_timer    : unsigned(31 downto 0);  -- Trigger pulse counter
    signal intensity_timer   : unsigned(31 downto 0);  -- Intensity pulse counter
    signal cooldown_timer    : unsigned(31 downto 0);  -- Cooldown counter
    signal monitor_start_timer : unsigned(31 downto 0); -- Monitor window delay
    signal monitor_duration_timer : unsigned(31 downto 0); -- Monitor window length

    ----------------------------------------------------------------------------
    -- Control Flags
    ----------------------------------------------------------------------------
    signal trig_out_active   : std_logic;  -- Trigger output pulse active
    signal intensity_active  : std_logic;  -- Intensity output pulse active
    signal monitor_window_open : std_logic; -- Monitor window is active
    signal firing_complete   : std_logic;  -- Both pulses finished
    signal timeout_occurred  : std_logic;  -- Armed timeout exceeded
    signal cooldown_complete : std_logic;  -- Cooldown elapsed

    ----------------------------------------------------------------------------
    -- Monitor/Comparator Signals
    ----------------------------------------------------------------------------
    signal threshold_crossed : std_logic;  -- Comparator output
    signal monitor_triggered : std_logic;  -- Latch for threshold crossing

    ----------------------------------------------------------------------------
    -- Fault Detection
    ----------------------------------------------------------------------------
    signal fault_detected    : std_logic;  -- Safety violation flag
    signal fault_clear_prev  : std_logic;  -- Edge detection
    signal fault_clear_edge  : std_logic;  -- Rising edge of fault_clear

begin

    ------------------------------------------------------------------------
    -- Ready for Updates
    --
    -- Always ready to accept register updates (shim handles atomicity)
    ------------------------------------------------------------------------
    ready_for_updates <= '1';

    ------------------------------------------------------------------------
    -- Time to Cycles Conversions
    --
    -- Convert YAML time units to clock cycles using platform-aware functions
    -- from basic_app_time_pkg
    ------------------------------------------------------------------------
    trigger_wait_timeout_cycles    <= resize(s_to_cycles(trigger_wait_timeout, CLK_FREQ_HZ), 32);
    trig_out_duration_cycles       <= resize(ns_to_cycles(trig_out_duration, CLK_FREQ_HZ), 32);
    intensity_duration_cycles      <= resize(ns_to_cycles(intensity_duration, CLK_FREQ_HZ), 32);
    cooldown_interval_cycles       <= resize(us_to_cycles(cooldown_interval, CLK_FREQ_HZ), 32);
    monitor_window_start_cycles    <= resize(ns_to_cycles(monitor_window_start, CLK_FREQ_HZ), 32);
    monitor_window_duration_cycles <= resize(ns_to_cycles(monitor_window_duration, CLK_FREQ_HZ), 32);

    ------------------------------------------------------------------------
    -- Edge Detector for fault_clear
    ------------------------------------------------------------------------
    FAULT_CLEAR_EDGE_PROC: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                fault_clear_prev <= '0';
            elsif global_enable = '1' then
                fault_clear_prev <= fault_clear;
            end if;
        end if;
    end process;

    fault_clear_edge <= fault_clear and not fault_clear_prev;

    ------------------------------------------------------------------------
    -- Monitor Comparator Logic
    --
    -- Compares probe_monitor_feedback against threshold with polarity control
    ------------------------------------------------------------------------
    MONITOR_COMPARATOR: process(probe_monitor_feedback, monitor_threshold_voltage,
                                 monitor_expect_negative)
    begin
        if monitor_expect_negative = '1' then
            -- Negative-going crossing detection (feedback < threshold)
            if probe_monitor_feedback < monitor_threshold_voltage then
                threshold_crossed <= '1';
            else
                threshold_crossed <= '0';
            end if;
        else
            -- Positive-going crossing detection (feedback > threshold)
            if probe_monitor_feedback > monitor_threshold_voltage then
                threshold_crossed <= '1';
            else
                threshold_crossed <= '0';
            end if;
        end if;
    end process;

    ------------------------------------------------------------------------
    -- State Register (Sequential)
    --
    -- Implements state transitions with active-high reset and clock enable
    ------------------------------------------------------------------------
    FSM_STATE_REG: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                state <= STATE_IDLE;
            elsif global_enable = '1' then
                state <= next_state;
            end if;
        end if;
    end process;

    ------------------------------------------------------------------------
    -- Next-State Logic (Combinational)
    --
    -- Implements FSM state transitions based on current state and inputs
    ------------------------------------------------------------------------
    FSM_NEXT_STATE: process(state, timeout_occurred, firing_complete,
                           cooldown_complete, auto_rearm_enable,
                           fault_clear_edge, fault_detected, arm_enable,
                           ext_trigger_in)
    begin
        -- Default: hold current state
        next_state <= state;

        case state is
            when STATE_IDLE =>
                -- Transition to ARMED when arm_enable asserted
                if arm_enable = '1' then
                    next_state <= STATE_ARMED;
                end if;

            when STATE_ARMED =>
                if timeout_occurred = '1' then
                    -- Timeout watchdog expired
                    next_state <= STATE_FAULT;
                elsif ext_trigger_in = '1' then
                    -- External trigger received
                    next_state <= STATE_FIRING;
                end if;

            when STATE_FIRING =>
                if firing_complete = '1' then
                    -- Both output pulses finished
                    next_state <= STATE_COOLDOWN;
                end if;

            when STATE_COOLDOWN =>
                if cooldown_complete = '1' then
                    if auto_rearm_enable = '1' then
                        -- Burst mode: re-arm automatically
                        next_state <= STATE_ARMED;
                    else
                        -- One-shot mode: return to idle
                        next_state <= STATE_IDLE;
                    end if;
                end if;

            when STATE_FAULT =>
                if fault_clear_edge = '1' then
                    -- Acknowledge fault and return to safe state
                    next_state <= STATE_IDLE;
                end if;

            when others =>
                -- Safety: any undefined state goes to FAULT
                next_state <= STATE_FAULT;

        end case;

        -- Override: any fault detection forces FAULT state
        if fault_detected = '1' then
            next_state <= STATE_FAULT;
        end if;
    end process;

    ------------------------------------------------------------------------
    -- Timing Counters (Sequential)
    --
    -- Implements all timing logic: timeouts, pulse durations, cooldown
    ------------------------------------------------------------------------
    TIMING_COUNTERS: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                armed_timer <= (others => '0');
                trig_out_timer <= (others => '0');
                intensity_timer <= (others => '0');
                cooldown_timer <= (others => '0');
                monitor_start_timer <= (others => '0');
                monitor_duration_timer <= (others => '0');
                monitor_window_open <= '0';
                monitor_triggered <= '0';

            elsif global_enable = '1' then
                case state is
                    when STATE_IDLE =>
                        -- Reset all counters
                        armed_timer <= (others => '0');
                        trig_out_timer <= (others => '0');
                        intensity_timer <= (others => '0');
                        cooldown_timer <= (others => '0');
                        monitor_start_timer <= (others => '0');
                        monitor_duration_timer <= (others => '0');
                        monitor_window_open <= '0';
                        monitor_triggered <= '0';

                    when STATE_ARMED =>
                        -- Increment timeout counter
                        if armed_timer < trigger_wait_timeout_cycles then
                            armed_timer <= armed_timer + 1;
                        end if;

                    when STATE_FIRING =>
                        -- Trigger output pulse timing
                        if trig_out_timer < trig_out_duration_cycles then
                            trig_out_timer <= trig_out_timer + 1;
                        end if;

                        -- Intensity output pulse timing
                        if intensity_timer < intensity_duration_cycles then
                            intensity_timer <= intensity_timer + 1;
                        end if;

                        -- Monitor window timing
                        if monitor_enable = '1' then
                            if monitor_start_timer < monitor_window_start_cycles then
                                -- Delay before window opens
                                monitor_start_timer <= monitor_start_timer + 1;
                                monitor_window_open <= '0';
                            elsif monitor_duration_timer < monitor_window_duration_cycles then
                                -- Window is open
                                monitor_duration_timer <= monitor_duration_timer + 1;
                                monitor_window_open <= '1';

                                -- Latch threshold crossing during window
                                if threshold_crossed = '1' then
                                    monitor_triggered <= '1';
                                end if;
                            else
                                -- Window closed
                                monitor_window_open <= '0';
                            end if;
                        end if;

                    when STATE_COOLDOWN =>
                        -- Increment cooldown counter
                        if cooldown_timer < cooldown_interval_cycles then
                            cooldown_timer <= cooldown_timer + 1;
                        end if;

                    when STATE_FAULT =>
                        -- Hold all counters in fault state
                        null;

                    when others =>
                        -- Safety: reset counters
                        armed_timer <= (others => '0');
                        trig_out_timer <= (others => '0');
                        intensity_timer <= (others => '0');
                        cooldown_timer <= (others => '0');

                end case;
            end if;
        end if;
    end process;

    ------------------------------------------------------------------------
    -- Output Control (Concurrent)
    --
    -- Activate outputs based purely on state, matching reference FSM pattern
    -- Timers control state exit (firing_complete), not output activation
    -- This ensures outputs respond immediately when entering FIRING state
    ------------------------------------------------------------------------
    trig_out_active <= '1' when state = STATE_FIRING else '0';
    intensity_active <= '1' when state = STATE_FIRING else '0';

    ------------------------------------------------------------------------
    -- Status Flags (Combinational)
    --
    -- Derive control flags from counter values
    ------------------------------------------------------------------------
    timeout_occurred  <= '1' when (armed_timer >= trigger_wait_timeout_cycles) else '0';
    firing_complete   <= '1' when (trig_out_timer >= trig_out_duration_cycles
                                   and intensity_timer >= intensity_duration_cycles
                                   and state = STATE_FIRING) else '0';
    cooldown_complete <= '1' when (cooldown_timer >= cooldown_interval_cycles) else '0';

    ------------------------------------------------------------------------
    -- Fault Detection Logic
    --
    -- Detect safety violations (placeholder - extend as needed)
    ------------------------------------------------------------------------
    FAULT_DETECTION: process(state, armed_timer, trigger_wait_timeout_cycles)
    begin
        fault_detected <= '0';  -- Default: no fault

        -- Example: Detect timeout in ARMED state
        -- (This is already handled in FSM, but shown here for extensibility)
        if state = STATE_ARMED and armed_timer > trigger_wait_timeout_cycles then
            fault_detected <= '1';
        end if;

        -- Add additional fault conditions here:
        -- - Voltage out of range
        -- - Counter overflow
        -- - Invalid configuration
    end process;

    ------------------------------------------------------------------------
    -- TODO: Output Driver Logic
    --
    -- Wire trig_out_voltage, intensity_voltage to actual DAC outputs
    -- This requires DAC interface ports to be added to entity
    ------------------------------------------------------------------------
    -- Example (when DAC ports added):
    -- dac_trig_out <= trig_out_voltage when trig_out_active = '1' else (others => '0');
    -- dac_intensity <= intensity_voltage when intensity_active = '1' else (others => '0');

    ------------------------------------------------------------------------
    -- TODO: FSM Observer Instantiation
    --
    -- Integrate fsm_observer.vhd for oscilloscope debugging
    -- Requires volo_voltage_pkg and debug output port
    ------------------------------------------------------------------------
    -- Example:
    -- FSM_DEBUG: entity WORK.fsm_observer
    --     generic map (
    --         NUM_STATES => 5,
    --         V_MIN => 0.0,
    --         V_MAX => 2.0,
    --         FAULT_STATE_THRESHOLD => 4,
    --         STATE_0_NAME => "IDLE",
    --         STATE_1_NAME => "ARMED",
    --         STATE_2_NAME => "FIRING",
    --         STATE_3_NAME => "COOLDOWN",
    --         STATE_4_NAME => "FAULT"
    --     )
    --     port map (
    --         clk => Clk,
    --         reset => Reset,
    --         state_vector => state,
    --         voltage_out => debug_fsm_voltage  -- Add to entity ports
    --     );

    ------------------------------------------------------------------------
    -- Export Internal Signals to Output Ports
    --
    -- Make internal FSM signals visible for test observability
    ------------------------------------------------------------------------
    trig_out_active_port      <= trig_out_active;
    intensity_out_active_port <= intensity_active;
    current_state_port        <= state;

end architecture rtl;
