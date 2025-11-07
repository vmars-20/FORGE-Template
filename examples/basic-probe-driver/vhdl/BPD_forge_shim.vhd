--------------------------------------------------------------------------------
-- File: BPD_forge_shim.vhd
-- Generated: 2025-11-05
-- Generator: Manual (will be automated via forge-codegen in future)
--
-- Description:
--   Register mapping shim for Basic Probe Driver (BPD) ForgeApp.
--   Maps raw Control Registers (CR20-CR30) to friendly signal names
--   and instantiates the application main entity.
--
-- Layer 2 of 3-Layer Forge Architecture:
--   Layer 1: MCC_TOP_forge_loader.vhd (static, shared)
--   Layer 2: BPD_forge_shim.vhd (THIS FILE - register mapping)
--   Layer 3: BPD_forge_main.vhd (hand-written app logic)
--
-- Register Mapping:
--   CR1[3:0]   : Lifecycle control (arm_enable, ext_trigger_in, auto_rearm, fault_clear)
--   CR2[15:0]  : Trigger output voltage (mV)
--   CR3[15:0]  : Trigger pulse duration (ns)
--   CR4[15:0]  : Intensity output voltage (mV)
--   CR5[15:0]  : Intensity pulse duration (ns)
--   CR6[15:0]  : Trigger wait timeout (s)
--   CR7[23:0]  : Cooldown interval (μs)
--   CR8[1:0]   : Monitor control (enable, expect_negative)
--   CR9[15:0]  : Monitor threshold voltage (mV)
--   CR10[31:0] : Monitor window start delay (ns)
--   CR11[31:0] : Monitor window duration (ns)
--
-- References:
--   - forge_common_pkg.vhd (FORGE_READY control scheme)
--   - external_Example/DS1140_polo_shim.vhd (pattern reference)
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library WORK;
use WORK.forge_common_pkg.all;

entity BPD_forge_shim is
    port (
        ------------------------------------------------------------------------
        -- Clock and Reset
        ------------------------------------------------------------------------
        Clk         : in  std_logic;
        Reset       : in  std_logic;  -- Active-high reset

        ------------------------------------------------------------------------
        -- FORGE Control Signals (from MCC_TOP_forge_loader or CustomWrapper)
        ------------------------------------------------------------------------
        forge_ready  : in  std_logic;  -- CR0[31] - Set by loader
        user_enable  : in  std_logic;  -- CR0[30] - User control
        clk_enable   : in  std_logic;  -- CR0[29] - Clock gating
        loader_done  : in  std_logic;  -- BRAM loader FSM done signal

        ------------------------------------------------------------------------
        -- Application Registers (from MCC_TOP_forge_loader)
        -- Raw Control Registers CR1-CR11 (MCC provides CR0-CR15)
        ------------------------------------------------------------------------
        app_reg_1 : in  std_logic_vector(31 downto 0);
        app_reg_2 : in  std_logic_vector(31 downto 0);
        app_reg_3 : in  std_logic_vector(31 downto 0);
        app_reg_4 : in  std_logic_vector(31 downto 0);
        app_reg_5 : in  std_logic_vector(31 downto 0);
        app_reg_6 : in  std_logic_vector(31 downto 0);
        app_reg_7 : in  std_logic_vector(31 downto 0);
        app_reg_8 : in  std_logic_vector(31 downto 0);
        app_reg_9 : in  std_logic_vector(31 downto 0);
        app_reg_10 : in  std_logic_vector(31 downto 0);
        app_reg_11 : in  std_logic_vector(31 downto 0);

        ------------------------------------------------------------------------
        -- BRAM Interface (from forge_bram_loader FSM)
        ------------------------------------------------------------------------
        bram_addr   : in  std_logic_vector(11 downto 0);  -- 4KB address space
        bram_data   : in  std_logic_vector(31 downto 0);  -- 32-bit data
        bram_we     : in  std_logic;                      -- Write enable

        ------------------------------------------------------------------------
        -- MCC I/O (from CustomWrapper)
        -- Native MCC types: signed(15 downto 0) for all ADC/DAC channels
        ------------------------------------------------------------------------
        InputA      : in  signed(15 downto 0);
        InputB      : in  signed(15 downto 0);
        OutputA     : out signed(15 downto 0);
        OutputB     : out signed(15 downto 0);
        OutputC     : out signed(15 downto 0);
        OutputD     : out signed(15 downto 0)
    );
end entity BPD_forge_shim;

architecture rtl of BPD_forge_shim is

    ----------------------------------------------------------------------------
    -- Friendly Signal Declarations (MCC-Agnostic Interface)
    ----------------------------------------------------------------------------

    -- Lifecycle control
    signal arm_enable           : std_logic;  -- Arm FSM (IDLE→ARMED transition)
    signal ext_trigger_in       : std_logic;  -- External trigger input
    signal auto_rearm_enable    : std_logic;  -- Re-arm after cooldown
    signal fault_clear          : std_logic;  -- Clear fault state

    -- Trigger output control
    signal trig_out_voltage     : signed(15 downto 0);    -- Voltage (mV)
    signal trig_out_duration    : unsigned(15 downto 0);  -- Duration (ns)

    -- Intensity output control
    signal intensity_voltage    : signed(15 downto 0);    -- Voltage (mV)
    signal intensity_duration   : unsigned(15 downto 0);  -- Duration (ns)

    -- Timing control
    signal trigger_wait_timeout : unsigned(15 downto 0);  -- Timeout (s)
    signal cooldown_interval    : unsigned(23 downto 0);  -- Cooldown (μs)

    -- Monitor/feedback
    signal monitor_enable            : std_logic;              -- Enable comparator
    signal monitor_expect_negative   : std_logic;              -- Polarity select
    signal monitor_threshold_voltage : signed(15 downto 0);    -- Threshold (mV)
    signal monitor_window_start      : unsigned(31 downto 0);  -- Window delay (ns)
    signal monitor_window_duration   : unsigned(31 downto 0);  -- Window length (ns)

    ----------------------------------------------------------------------------
    -- Global Enable Signal
    -- Combines all FORGE_READY control bits for safe operation
    ----------------------------------------------------------------------------
    signal global_enable : std_logic;

begin

    ----------------------------------------------------------------------------
    -- Global Enable Computation
    --
    -- All 4 conditions must be met for app to operate:
    --   1. forge_ready  = 1  (loader has deployed bitstream)
    --   2. user_enable  = 1  (user has enabled module)
    --   3. clk_enable   = 1  (clock gating enabled)
    --   4. loader_done  = 1  (BRAM loading complete)
    ----------------------------------------------------------------------------
    global_enable <= combine_forge_ready(forge_ready, user_enable, clk_enable, loader_done);

    ----------------------------------------------------------------------------
    -- Register Mapping: Control Registers → Friendly Signals
    --
    -- Extract appropriate bit ranges from raw Control Registers
    ----------------------------------------------------------------------------

    -- CR1: Lifecycle control bits (4 bits)
    arm_enable        <= app_reg_1(0);  -- Arm probe
    ext_trigger_in    <= app_reg_1(1);  -- External trigger
    auto_rearm_enable <= app_reg_1(2);  -- Auto re-arm
    fault_clear       <= app_reg_1(3);  -- Clear fault

    -- CR2: Trigger output voltage (16-bit signed, mV)
    trig_out_voltage  <= signed(app_reg_2(15 downto 0));

    -- CR3: Trigger pulse duration (16-bit unsigned, ns)
    trig_out_duration <= unsigned(app_reg_3(15 downto 0));

    -- CR4: Intensity output voltage (16-bit signed, mV)
    intensity_voltage <= signed(app_reg_4(15 downto 0));

    -- CR5: Intensity pulse duration (16-bit unsigned, ns)
    intensity_duration <= unsigned(app_reg_5(15 downto 0));

    -- CR6: Trigger wait timeout (16-bit unsigned, s)
    trigger_wait_timeout <= unsigned(app_reg_6(15 downto 0));

    -- CR7: Cooldown interval (24-bit unsigned, μs)
    cooldown_interval <= unsigned(app_reg_7(23 downto 0));

    -- CR8: Monitor control bits (2 bits)
    monitor_enable          <= app_reg_8(0);  -- Enable monitor
    monitor_expect_negative <= app_reg_8(1);  -- Polarity

    -- CR9: Monitor threshold voltage (16-bit signed, mV)
    monitor_threshold_voltage <= signed(app_reg_9(15 downto 0));

    -- CR10: Monitor window start delay (32-bit unsigned, ns)
    monitor_window_start <= unsigned(app_reg_10);

    -- CR11: Monitor window duration (32-bit unsigned, ns)
    monitor_window_duration <= unsigned(app_reg_11);

    ----------------------------------------------------------------------------
    -- Instantiate Application Main Entity
    --
    -- MCC-agnostic interface using friendly signal names only
    ----------------------------------------------------------------------------
    BPD_MAIN_INST: entity WORK.BPD_forge_main
        generic map (
            CLK_FREQ_HZ => 125000000  -- Moku:Go clock frequency
        )
        port map (
            -- Standard Control Signals
            Clk    => Clk,
            Reset  => Reset,
            Enable => global_enable,
            ClkEn  => clk_enable,

            -- Friendly Application Signals (Lifecycle)
            arm_enable                => arm_enable,
            ext_trigger_in            => ext_trigger_in,
            trigger_wait_timeout      => trigger_wait_timeout,
            auto_rearm_enable         => auto_rearm_enable,
            fault_clear               => fault_clear,

            -- Trigger output control
            trig_out_voltage          => trig_out_voltage,
            trig_out_duration         => trig_out_duration,

            -- Intensity output control
            intensity_voltage         => intensity_voltage,
            intensity_duration        => intensity_duration,

            -- Timing control
            cooldown_interval         => cooldown_interval,

            -- Monitor/feedback
            probe_monitor_feedback    => InputA,
            monitor_enable            => monitor_enable,
            monitor_threshold_voltage => monitor_threshold_voltage,
            monitor_expect_negative   => monitor_expect_negative,
            monitor_window_start      => monitor_window_start,
            monitor_window_duration   => monitor_window_duration,

            -- BRAM Interface (always exposed for consistency)
            bram_addr => bram_addr,
            bram_data => bram_data,
            bram_we   => bram_we,

            -- MCC I/O
            OutputA => OutputA,
            OutputB => OutputB,
            OutputC => OutputC,
            OutputD => OutputD
        );

end architecture rtl;
