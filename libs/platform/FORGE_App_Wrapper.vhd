--------------------------------------------------------------------------------
-- File: FORGE_App_Wrapper.vhd
-- Author: Moku Instrument Forge Team
-- Date: 2025-11-06
-- Version: 1.0.0
-- Status: TEMPLATE / REFERENCE IMPLEMENTATION
--
-- Description:
--   Template for FORGE 3-layer architecture wrapper implementation.
--   This file codifies the naming conventions and structure for integrating
--   FORGE applications with MCC CustomInstrument interface.
--
-- FORGE 3-Layer Architecture:
--   Layer 1: BRAM Loader (future - sets forge_ready flag)
--   Layer 2: Shim (register mapping + synchronization + FORGE control)
--   Layer 3: Main App (application FSM/logic - Control Register agnostic!)
--
-- Key Architectural Principles:
--   1. Main app uses 'app_reg_*' signals - NO knowledge of Control Registers
--   2. Shim transparently maps app_reg_* ↔ Control Registers (network settable)
--   3. 'ready_for_updates' handshaking protects main from async register changes
--   4. Clock enable support for divided/gated clocking
--
-- Naming Conventions:
--   Entity: <AppName>_CustomInstrument (matches MCC expectations)
--   Architecture: forge_app (standard FORGE architecture name)
--   Shim Entity: <AppName>_forge_shim (Layer 2)
--   Main Entity: <AppName>_forge_main (Layer 3)
--   App Signals: app_reg_<name> (typed application registers)
--
-- Usage:
--   1. Copy this template
--   2. Replace <AppName> with your application name
--   3. Define app_reg_* signals for your application
--   4. Implement Layer 2 (shim) - register mapping + synchronization
--   5. Implement Layer 3 (main) - application logic
--   6. Wire FORGE control scheme (CR0[31:29])
--
-- Production Reference:
--   See: bpd-tiny-vhdl/CustomWrapper_bpd_forge.vhd
--        bpd-tiny-vhdl/BPD_forge_shim.vhd
--        bpd-tiny-vhdl/src/basic_probe_driver_custom_inst_main.vhd
--
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library WORK;
use WORK.forge_common_pkg.ALL;                   -- FORGE_READY control scheme
use WORK.forge_serialization_types_pkg.ALL;      -- Core serialization types
use WORK.forge_serialization_voltage_pkg.ALL;    -- Voltage serialization
use WORK.forge_serialization_time_pkg.ALL;       -- Time serialization

--------------------------------------------------------------------------------
-- <AppName>_CustomInstrument Entity
--
-- Replace <AppName> with your application name (e.g., basic_probe_driver)
-- Entity name MUST match MCC expectations for deployment
--
-- NEW: Added clk_en for clock division/gating support
--------------------------------------------------------------------------------

entity AppName_CustomInstrument is
    generic (
        CLK_FREQ_HZ : integer := 125000000  -- Platform clock frequency (Go: 125 MHz, Lab/Pro: 200 MHz)
    );
    port (
        -- Clock and Reset
        Clk    : in std_logic;
        Reset  : in std_logic;
        clk_en : in std_logic := '1';  -- Clock enable for divided/gated clocking

        -- ADC Inputs
        InputA : in signed(15 downto 0);
        InputB : in signed(15 downto 0);
        InputC : in signed(15 downto 0);
        InputD : in signed(15 downto 0);

        -- DAC Outputs
        OutputA : out signed(15 downto 0);
        OutputB : out signed(15 downto 0);
        OutputC : out signed(15 downto 0);
        OutputD : out signed(15 downto 0);

        -- Control Registers (CR0[31:29] reserved for FORGE)
        Control0  : in std_logic_vector(31 downto 0);
        Control1  : in std_logic_vector(31 downto 0);
        Control2  : in std_logic_vector(31 downto 0);
        Control3  : in std_logic_vector(31 downto 0);
        Control4  : in std_logic_vector(31 downto 0);
        Control5  : in std_logic_vector(31 downto 0);
        Control6  : in std_logic_vector(31 downto 0);
        Control7  : in std_logic_vector(31 downto 0);
        Control8  : in std_logic_vector(31 downto 0);
        Control9  : in std_logic_vector(31 downto 0);
        Control10 : in std_logic_vector(31 downto 0);
        Control11 : in std_logic_vector(31 downto 0);
        Control12 : in std_logic_vector(31 downto 0);
        Control13 : in std_logic_vector(31 downto 0);
        Control14 : in std_logic_vector(31 downto 0);
        Control15 : in std_logic_vector(31 downto 0);

        -- Status Registers
        Status0  : out std_logic_vector(31 downto 0);
        Status1  : out std_logic_vector(31 downto 0);
        Status2  : out std_logic_vector(31 downto 0);
        Status3  : out std_logic_vector(31 downto 0);
        Status4  : out std_logic_vector(31 downto 0);
        Status5  : out std_logic_vector(31 downto 0);
        Status6  : out std_logic_vector(31 downto 0);
        Status7  : out std_logic_vector(31 downto 0);
        Status8  : out std_logic_vector(31 downto 0);
        Status9  : out std_logic_vector(31 downto 0);
        Status10 : out std_logic_vector(31 downto 0);
        Status11 : out std_logic_vector(31 downto 0);
        Status12 : out std_logic_vector(31 downto 0);
        Status13 : out std_logic_vector(31 downto 0);
        Status14 : out std_logic_vector(31 downto 0);
        Status15 : out std_logic_vector(31 downto 0)
    );
end entity AppName_CustomInstrument;

--------------------------------------------------------------------------------
-- FORGE Application Wrapper Architecture
--
-- This architecture implements the FORGE 3-layer pattern with key features:
--   1. Extract FORGE control signals from CR0[31:29]
--   2. Instantiate shim layer (register mapping + synchronization)
--   3. Wire to application main layer via app_reg_* signals
--   4. Main app is completely Control Register agnostic!
--------------------------------------------------------------------------------

architecture forge_app of AppName_CustomInstrument is

    ----------------------------------------------------------------------------
    -- FORGE Control Scheme Signals
    --
    -- Extract from CR0[31:29] as per FORGE specification
    ----------------------------------------------------------------------------
    signal forge_ready  : std_logic;  -- CR0[31] - Loader handshaking
    signal user_enable  : std_logic;  -- CR0[30] - User control
    signal clk_enable   : std_logic;  -- CR0[29] - Clock gating
    signal loader_done  : std_logic;  -- Internal - BRAM loader completion

    ----------------------------------------------------------------------------
    -- Global Enable Signal
    --
    -- Combined from 4 conditions (FORGE control scheme)
    ----------------------------------------------------------------------------
    signal global_enable : std_logic;

    ----------------------------------------------------------------------------
    -- Application Register Update Handshaking
    --
    -- Protects main app from asynchronous Control Register changes
    -- Shim latches new values only when main signals 'ready_for_updates'
    ----------------------------------------------------------------------------
    signal ready_for_updates : std_logic;  -- Main → Shim: "Safe to update app_reg_* now"

    ----------------------------------------------------------------------------
    -- Application Register Signals (app_reg_*)
    --
    -- These signals carry TYPED data between shim and main
    -- Main app ONLY sees these - NO knowledge of Control Registers!
    --
    -- CRITICAL: Replace these with your application-specific registers
    --
    -- Naming Convention: app_reg_<descriptive_name>
    -- Types: Use forge_serialization types (see libs/forge-vhdl/vhdl/packages/)
    --
    -- Example types:
    --   - std_logic (for single-bit controls - future: std_logic_reg)
    --   - unsigned(N downto 0) (for counts, durations)
    --   - signed(15 downto 0) (for voltage values, ADC/DAC data)
    ----------------------------------------------------------------------------

    -- EXAMPLE: Replace with your application registers
    -- signal app_reg_enable           : std_logic;
    -- signal app_reg_trigger_voltage  : signed(15 downto 0);      -- Voltage type
    -- signal app_reg_pulse_duration   : unsigned(15 downto 0);    -- Time type
    -- signal app_reg_threshold        : signed(15 downto 0);      -- Voltage type
    -- signal app_reg_mode             : std_logic_vector(2 downto 0);  -- Enum/mode

    -- EXAMPLE: Status signals from main app
    -- signal app_status_busy          : std_logic;
    -- signal app_status_state         : std_logic_vector(5 downto 0);
    -- signal app_status_error_flags   : std_logic_vector(7 downto 0);

begin

    ----------------------------------------------------------------------------
    -- FORGE Control Scheme Extraction
    --
    -- Extract 3-bit control scheme from CR0[31:29]
    -- These bits are RESERVED by FORGE - DO NOT use in application logic
    ----------------------------------------------------------------------------
    forge_ready  <= Control0(31);  -- Loader handshaking
    user_enable  <= Control0(30);  -- User enable/disable
    clk_enable   <= Control0(29);  -- Clock gating

    ----------------------------------------------------------------------------
    -- BRAM Loader Status
    --
    -- FUTURE: Wire to actual BRAM loader FSM completion signal
    -- CURRENT: Hardcoded to '1' (no BRAM loader integrated yet)
    --
    -- When BRAM loader integrated (Layer 1):
    --   loader_done <= bram_loader_done_signal;
    ----------------------------------------------------------------------------
    loader_done <= '1';  -- TODO: Replace with actual loader_done signal

    ----------------------------------------------------------------------------
    -- Compute Global Enable
    --
    -- Combines 4 conditions as per FORGE specification
    -- Uses combine_forge_ready() from forge_common_pkg
    ----------------------------------------------------------------------------
    global_enable <= combine_forge_ready(
        forge_ready  => forge_ready,
        user_enable  => user_enable,
        clk_enable   => clk_enable,
        loader_done  => loader_done
    );

    ----------------------------------------------------------------------------
    -- Layer 2: Shim Instantiation
    --
    -- RESPONSIBILITIES:
    --   1. Unpack Control Registers → app_reg_* signals (typed)
    --   2. Pack app_status_* signals → Status Registers
    --   3. Synchronize register updates with ready_for_updates handshaking
    --   4. Compute global_enable (FORGE control scheme)
    --
    -- TRANSPARENCY:
    --   Main app (Layer 3) has NO knowledge of Control Registers
    --   All it sees are app_reg_* signals with proper types
    --
    -- SYNCHRONIZATION:
    --   Shim latches new app_reg_* values ONLY when ready_for_updates='1'
    --   Protects main app FSM from mid-cycle register changes
    --
    -- Replace <AppName>_forge_shim with your shim entity name
    ----------------------------------------------------------------------------
    SHIM: entity WORK.AppName_forge_shim
        generic map (
            CLK_FREQ_HZ => CLK_FREQ_HZ  -- Platform clock frequency
        )
        port map (
            -- Clock and Reset
            Clk   => Clk,
            Reset => Reset,
            clk_en => clk_en,  -- Clock enable for divided/gated clocking

            -- FORGE Control
            global_enable => global_enable,

            -- Update Handshaking (Main → Shim)
            ready_for_updates => ready_for_updates,  -- From main app

            -- MCC Control Registers (CR0-CR15)
            -- NOTE: CR0[31:29] already extracted above
            Control0  => Control0,
            Control1  => Control1,
            Control2  => Control2,
            Control3  => Control3,
            Control4  => Control4,
            Control5  => Control5,
            Control6  => Control6,
            Control7  => Control7,
            Control8  => Control8,
            Control9  => Control9,
            Control10 => Control10,
            Control11 => Control11,
            Control12 => Control12,
            Control13 => Control13,
            Control14 => Control14,
            Control15 => Control15,

            -- MCC Status Registers (SR0-SR15)
            Status0  => Status0,
            Status1  => Status1,
            Status2  => Status2,
            Status3  => Status3,
            Status4  => Status4,
            Status5  => Status5,
            Status6  => Status6,
            Status7  => Status7,
            Status8  => Status8,
            Status9  => Status9,
            Status10 => Status10,
            Status11 => Status11,
            Status12 => Status12,
            Status13 => Status13,
            Status14 => Status14,
            Status15 => Status15

            -- Application Register Interface (Shim ↔ Main)
            -- REPLACE WITH YOUR APPLICATION REGISTERS
            --
            -- Example:
            -- app_reg_enable          => app_reg_enable,
            -- app_reg_trigger_voltage => app_reg_trigger_voltage,
            -- app_reg_pulse_duration  => app_reg_pulse_duration,
            -- app_reg_threshold       => app_reg_threshold,
            -- app_status_busy         => app_status_busy,
            -- app_status_state        => app_status_state
        );

    ----------------------------------------------------------------------------
    -- Layer 3: Main Application Instantiation
    --
    -- RESPONSIBILITIES:
    --   1. Application FSM/logic
    --   2. Generate outputs based on app_reg_* inputs
    --   3. Report status via app_status_* outputs
    --   4. Signal ready_for_updates when safe to latch new registers
    --
    -- ISOLATION:
    --   Main app is COMPLETELY Control Register agnostic
    --   Sees ONLY app_reg_* signals with proper types
    --   No knowledge of CR0[31:29] FORGE control scheme
    --   No knowledge of network settable registers
    --
    -- PORTABILITY:
    --   Can be reused across platforms (Moku, Red Pitaya, etc.)
    --   Only requires: Clk, Reset, global_enable, app_reg_* signals
    --
    -- Replace <AppName>_forge_main with your main entity name
    ----------------------------------------------------------------------------
    MAIN: entity WORK.AppName_forge_main
        generic map (
            CLK_FREQ_HZ => CLK_FREQ_HZ  -- Platform clock frequency
        )
        port map (
            -- Clock and Reset
            Clk   => Clk,
            Reset => Reset,

            -- Enable (from FORGE control scheme)
            global_enable => global_enable,

            -- Update Handshaking (Main → Shim)
            ready_for_updates => ready_for_updates,

            -- ADC Inputs (if needed by application)
            -- OPTIONAL: Remove if not used
            InputA => InputA,
            InputB => InputB,
            InputC => InputC,
            InputD => InputD,

            -- DAC Outputs (if needed by application)
            -- OPTIONAL: Remove if not used
            OutputA => OutputA,
            OutputB => OutputB,
            OutputC => OutputC,
            OutputD => OutputD

            -- Application Register Interface (Main ↔ Shim)
            -- REPLACE WITH YOUR APPLICATION REGISTERS
            --
            -- Example:
            -- app_reg_enable          => app_reg_enable,
            -- app_reg_trigger_voltage => app_reg_trigger_voltage,
            -- app_reg_pulse_duration  => app_reg_pulse_duration,
            -- app_reg_threshold       => app_reg_threshold,
            -- app_status_busy         => app_status_busy,
            -- app_status_state        => app_status_state
        );

end architecture forge_app;

--------------------------------------------------------------------------------
-- CUSTOMIZATION CHECKLIST
--
-- [ ] Rename entity: AppName_CustomInstrument → YourApp_CustomInstrument
-- [ ] Set CLK_FREQ_HZ generic (125 MHz for Go, 200 MHz for Lab/Pro)
-- [ ] Define app_reg_* signals for your application:
--       - Use forge_serialization types (see libs/forge-vhdl/vhdl/packages/)
--       - Name: app_reg_<descriptive_name>
--       - Examples: app_reg_enable, app_reg_trigger_voltage, app_reg_pulse_duration
-- [ ] Define app_status_* signals for status reporting
-- [ ] Update SHIM instantiation:
--       - Change entity name to your shim
--       - Wire app_reg_* and app_status_* signals
-- [ ] Update MAIN instantiation:
--       - Change entity name to your main
--       - Wire app_reg_* and app_status_* signals
-- [ ] Implement Layer 2 (shim) entity:
--       - Control Register unpacking → app_reg_* (typed signals)
--       - app_status_* packing → Status Registers
--       - Synchronization logic (latch on ready_for_updates)
--       - Reference: bpd-tiny-vhdl/BPD_forge_shim.vhd
-- [ ] Implement Layer 3 (main) entity:
--       - Application FSM/logic
--       - Use app_reg_* as inputs (NO Control Register knowledge!)
--       - Generate ready_for_updates signal (handshaking)
--       - Reference: bpd-tiny-vhdl/src/basic_probe_driver_custom_inst_main.vhd
-- [ ] Update loader_done signal when BRAM loader integrated
--
-- PRODUCTION REFERENCE:
--   Wrapper: bpd-tiny-vhdl/CustomWrapper_bpd_forge.vhd
--   Shim:    bpd-tiny-vhdl/BPD_forge_shim.vhd
--   Main:    bpd-tiny-vhdl/src/basic_probe_driver_custom_inst_main.vhd
--
-- KEY ARCHITECTURAL PRINCIPLE:
--   Main app thinks in terms of 'app_reg_enable', 'app_reg_voltage', etc.
--   NOT in terms of 'Control0', 'Control1', 'CR0[5]', etc.
--   Shim provides complete abstraction and synchronization!
--------------------------------------------------------------------------------
