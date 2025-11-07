------------------------------------------------------------------------------
-- forge_serialization_types_pkg.vhd
--
-- Core types and constants for register serialization
--
-- Migrated from: tools/forge-codegen/forge_codegen/vhdl/basic_app_types_pkg.vhd
-- Version: 1.0.0 (FROZEN - DO NOT REGENERATE)
-- Date: 2025-11-06
--
-- This package provides type utilities for serializing application data
-- to/from control registers for MCC communication.
--
-- Part of: moku-instrument-forge-vhdl
------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

package forge_serialization_types_pkg is

    ------------------------------------------------------------------------------
    -- Type Categories
    ------------------------------------------------------------------------------

    -- Boolean types: Direct mapping to std_logic
    -- Voltage types: Fixed-point representations of analog voltages
    -- Time types: Durations requiring clock frequency for conversion
    -- Count types: Integer counts with configurable ranges

    ------------------------------------------------------------------------------
    -- Constants
    ------------------------------------------------------------------------------

    -- Version identifier
    constant FORGE_SERIALIZATION_VERSION : string := "1.0.0";

    ------------------------------------------------------------------------------
    -- Utility Functions
    ------------------------------------------------------------------------------

    -- Convert boolean to std_logic
    function bool_to_sl(b : boolean) return std_logic;

    -- Convert std_logic to boolean
    function sl_to_bool(sl : std_logic) return boolean;

end package forge_serialization_types_pkg;

package body forge_serialization_types_pkg is

    function bool_to_sl(b : boolean) return std_logic is
    begin
        if b then
            return '1';
        else
            return '0';
        end if;
    end function;

    function sl_to_bool(sl : std_logic) return boolean is
    begin
        return sl = '1';
    end function;

end package body forge_serialization_types_pkg;
