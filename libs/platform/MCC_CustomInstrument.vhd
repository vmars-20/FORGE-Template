--------------------------------------------------------------------------------
-- File: MCC_CustomInstrument.vhd
-- Author: Moku Instrument Forge Team
-- Date: 2025-11-06
-- Version: 1.0.0
-- Status: AUTHORITATIVE
--
-- Description:
--   Simplified MCC CustomInstrument entity definition for Moku platforms.
--   This is the vendor-defined interface that all custom instruments must
--   implement to integrate with the Moku Control Computer (MCC).
--
-- CRITICAL NOTES:
--   - This is a SIMPLIFIED version (removed interlacing, Sync, ExtTrig)
--   - Based on upstream MCC specifications (2025-11-06 revision)
--   - 16 Control Registers (CR0-CR15) - Network settable
--   - 16 Status Registers (SR0-SR15) - Network readable (future release)
--   - CR0[31:29] RESERVED for FORGE control scheme (DO NOT USE in app logic!)
--
-- Vendor Changes (2025-11-06):
--   - Reduced from 32 control regs → 16 control regs
--   - Status registers planned for future network readability
--   - Removed interlacing support (future feature, unstable)
--
-- FORGE Simplifications:
--   - Removed Sync signal (not commonly supported across platforms)
--   - Removed ExtTrig signal (not commonly supported across platforms)
--   - Focus on universally available: Clk, Reset, ADC, DAC, Control, Status
--
-- Network Capabilities:
--   - Control registers: Network settable (via MCC API)
--   - Status registers: Network readable (FUTURE - not yet implemented)
--
-- Upstream Reference:
--   - Original entity: CustomWrapper.vhd (with interlacing, Sync, ExtTrig)
--   - Simplified for FORGE ecosystem (platform-agnostic subset)
--
-- Usage:
--   DO NOT modify this file. This entity definition must match MCC expectations.
--   Implement this entity with architecture 'forge_app' (see FORGE_App_Wrapper.vhd)
--
-- Integration:
--   entity MyApp_CustomInstrument is
--   end entity;
--
--   architecture forge_app of MyApp_CustomInstrument is
--       -- Your FORGE wrapper implementation here
--   end architecture;
--
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

--------------------------------------------------------------------------------
-- MCC CustomInstrument Entity (Simplified for FORGE)
--
-- This is the interface between Moku Control Computer (MCC) and your
-- custom FPGA instrument. All ports are MANDATORY and must be implemented
-- exactly as specified.
--
-- Platform Support: Moku:Go, Moku:Lab, Moku:Pro (universal subset)
--------------------------------------------------------------------------------

entity MCC_CustomInstrument is
    port (
        ------------------------------------------------------------------------
        -- Clock and Reset
        ------------------------------------------------------------------------
        Clk   : in std_logic;  -- System clock (platform-specific: 125 MHz Go, 200 MHz Lab/Pro)
        Reset : in std_logic;  -- Active-high reset

        ------------------------------------------------------------------------
        -- ADC Inputs (4 channels, 16-bit signed)
        --
        -- Moku ADC inputs, typically ±5V or ±10V range scaled to signed 16-bit
        -- InputA-D map to physical ADC channels (platform-specific mapping)
        --
        -- Voltage ranges (platform-dependent):
        --   Moku:Go  - Typically ±5V
        --   Moku:Lab - Typically ±10V
        --   Moku:Pro - Typically ±10V or ±50V
        ------------------------------------------------------------------------
        InputA : in signed(15 downto 0);
        InputB : in signed(15 downto 0);
        InputC : in signed(15 downto 0);
        InputD : in signed(15 downto 0);

        ------------------------------------------------------------------------
        -- DAC Outputs (4 channels, 16-bit signed)
        --
        -- Moku DAC outputs, typically ±5V or ±10V range scaled from signed 16-bit
        -- OutputA-D map to physical DAC channels (platform-specific mapping)
        --
        -- Voltage ranges (platform-dependent):
        --   Moku:Go  - Typically ±5V
        --   Moku:Lab - Typically ±10V
        --   Moku:Pro - Typically ±10V
        ------------------------------------------------------------------------
        OutputA : out signed(15 downto 0);
        OutputB : out signed(15 downto 0);
        OutputC : out signed(15 downto 0);
        OutputD : out signed(15 downto 0);

        ------------------------------------------------------------------------
        -- Control Registers (16 registers, network settable)
        --
        -- CR0[31:29] RESERVED for FORGE control scheme:
        --   CR0[31] = forge_ready  (loader handshaking)
        --   CR0[30] = user_enable  (user control)
        --   CR0[29] = clk_enable   (clock gating)
        --
        -- CR0[28:0]  Available for application use
        -- CR1-CR15   Available for application use
        --
        -- Network Capability: Writable via MCC API (Python/GUI)
        ------------------------------------------------------------------------
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

        ------------------------------------------------------------------------
        -- Status Registers (16 registers, future network readable)
        --
        -- Status0-Status15 available for application status reporting
        --
        -- Network Capability: Readable via MCC API (FUTURE - not yet implemented)
        -- Current Status: Local readback only (no network transport yet)
        --
        -- Typical uses:
        --   - FSM state export (for debugging)
        --   - Error/fault flags
        --   - Counters (pulses fired, triggers received, etc.)
        --   - Configuration readback verification
        ------------------------------------------------------------------------
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
end entity MCC_CustomInstrument;

--------------------------------------------------------------------------------
-- ARCHITECTURE IMPLEMENTATIONS
--
-- This entity is typically implemented with architecture 'forge_app'
-- See: FORGE_App_Wrapper.vhd for standard implementation pattern
--
-- Example:
--   architecture forge_app of MCC_CustomInstrument is
--       -- FORGE wrapper signals and components
--   end architecture;
--
--------------------------------------------------------------------------------
