------------------------------------------------------------------------------
-- forge_serialization_voltage_pkg.vhd
--
-- Voltage serialization utilities for control register communication
--
-- Migrated from: tools/forge-codegen/forge_codegen/vhdl/basic_app_voltage_pkg.vhd
-- Version: 1.0.0 (FROZEN - DO NOT REGENERATE)
-- Date: 2025-11-06
--
-- This package provides conversion functions between raw register values and
-- VHDL types for voltage-based serialized data.
--
-- Voltage ranges and scaling factors are embedded in function names to ensure
-- type safety and prevent unit confusion.
--
-- Part of: moku-instrument-forge-vhdl
------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library WORK;
use WORK.forge_serialization_types_pkg.ALL;

package forge_serialization_voltage_pkg is

    ------------------------------------------------------------------------------
    -- Voltage Type Conversions
    ------------------------------------------------------------------------------

    -- Convert raw register bits to voltage_input_20v_s16
    -- Range: ±20.0V, Bits: 16, Type: signed
    function voltage_input_20v_s16_from_raw(
        raw : std_logic_vector(15 downto 0)
    ) return signed;

    -- Convert voltage_input_20v_s16 to raw register bits
    function voltage_input_20v_s16_to_raw(
        value : signed(15 downto 0)
    ) return std_logic_vector;

    -- Convert raw register bits to voltage_input_20v_s8
    -- Range: ±20.0V, Bits: 8, Type: signed
    function voltage_input_20v_s8_from_raw(
        raw : std_logic_vector(7 downto 0)
    ) return signed;

    -- Convert voltage_input_20v_s8 to raw register bits
    function voltage_input_20v_s8_to_raw(
        value : signed(7 downto 0)
    ) return std_logic_vector;

    -- Convert raw register bits to voltage_input_20v_u15
    -- Range: ±20.0V, Bits: 15, Type: unsigned
    function voltage_input_20v_u15_from_raw(
        raw : std_logic_vector(14 downto 0)
    ) return unsigned;

    -- Convert voltage_input_20v_u15 to raw register bits
    function voltage_input_20v_u15_to_raw(
        value : unsigned(14 downto 0)
    ) return std_logic_vector;

    -- Convert raw register bits to voltage_input_20v_u7
    -- Range: ±20.0V, Bits: 7, Type: unsigned
    function voltage_input_20v_u7_from_raw(
        raw : std_logic_vector(6 downto 0)
    ) return unsigned;

    -- Convert voltage_input_20v_u7 to raw register bits
    function voltage_input_20v_u7_to_raw(
        value : unsigned(6 downto 0)
    ) return std_logic_vector;

    -- Convert raw register bits to voltage_input_25v_s16
    -- Range: ±25.0V, Bits: 16, Type: signed
    function voltage_input_25v_s16_from_raw(
        raw : std_logic_vector(15 downto 0)
    ) return signed;

    -- Convert voltage_input_25v_s16 to raw register bits
    function voltage_input_25v_s16_to_raw(
        value : signed(15 downto 0)
    ) return std_logic_vector;

    -- Convert raw register bits to voltage_input_25v_s8
    -- Range: ±25.0V, Bits: 8, Type: signed
    function voltage_input_25v_s8_from_raw(
        raw : std_logic_vector(7 downto 0)
    ) return signed;

    -- Convert voltage_input_25v_s8 to raw register bits
    function voltage_input_25v_s8_to_raw(
        value : signed(7 downto 0)
    ) return std_logic_vector;

    -- Convert raw register bits to voltage_input_25v_u15
    -- Range: ±25.0V, Bits: 15, Type: unsigned
    function voltage_input_25v_u15_from_raw(
        raw : std_logic_vector(14 downto 0)
    ) return unsigned;

    -- Convert voltage_input_25v_u15 to raw register bits
    function voltage_input_25v_u15_to_raw(
        value : unsigned(14 downto 0)
    ) return std_logic_vector;

    -- Convert raw register bits to voltage_input_25v_u7
    -- Range: ±25.0V, Bits: 7, Type: unsigned
    function voltage_input_25v_u7_from_raw(
        raw : std_logic_vector(6 downto 0)
    ) return unsigned;

    -- Convert voltage_input_25v_u7 to raw register bits
    function voltage_input_25v_u7_to_raw(
        value : unsigned(6 downto 0)
    ) return std_logic_vector;

    -- Convert raw register bits to voltage_output_05v_s16
    -- Range: ±0.5V, Bits: 16, Type: signed
    function voltage_output_05v_s16_from_raw(
        raw : std_logic_vector(15 downto 0)
    ) return signed;

    -- Convert voltage_output_05v_s16 to raw register bits
    function voltage_output_05v_s16_to_raw(
        value : signed(15 downto 0)
    ) return std_logic_vector;

    -- Convert raw register bits to voltage_output_05v_s8
    -- Range: ±0.5V, Bits: 8, Type: signed
    function voltage_output_05v_s8_from_raw(
        raw : std_logic_vector(7 downto 0)
    ) return signed;

    -- Convert voltage_output_05v_s8 to raw register bits
    function voltage_output_05v_s8_to_raw(
        value : signed(7 downto 0)
    ) return std_logic_vector;

    -- Convert raw register bits to voltage_output_05v_u15
    -- Range: ±0.5V, Bits: 15, Type: unsigned
    function voltage_output_05v_u15_from_raw(
        raw : std_logic_vector(14 downto 0)
    ) return unsigned;

    -- Convert voltage_output_05v_u15 to raw register bits
    function voltage_output_05v_u15_to_raw(
        value : unsigned(14 downto 0)
    ) return std_logic_vector;

    -- Convert raw register bits to voltage_output_05v_u7
    -- Range: ±0.5V, Bits: 7, Type: unsigned
    function voltage_output_05v_u7_from_raw(
        raw : std_logic_vector(6 downto 0)
    ) return unsigned;

    -- Convert voltage_output_05v_u7 to raw register bits
    function voltage_output_05v_u7_to_raw(
        value : unsigned(6 downto 0)
    ) return std_logic_vector;

end package forge_serialization_voltage_pkg;

package body forge_serialization_voltage_pkg is


    function voltage_input_20v_s16_from_raw(
        raw : std_logic_vector(15 downto 0)
    ) return signed is
    begin
        return signed(raw);
    end function;

    function voltage_input_20v_s16_to_raw(
        value : signed(15 downto 0)
    ) return std_logic_vector is
    begin
        return std_logic_vector(value);
    end function;

    function voltage_input_20v_s8_from_raw(
        raw : std_logic_vector(7 downto 0)
    ) return signed is
    begin
        return signed(raw);
    end function;

    function voltage_input_20v_s8_to_raw(
        value : signed(7 downto 0)
    ) return std_logic_vector is
    begin
        return std_logic_vector(value);
    end function;

    function voltage_input_20v_u15_from_raw(
        raw : std_logic_vector(14 downto 0)
    ) return unsigned is
    begin
        return unsigned(raw);
    end function;

    function voltage_input_20v_u15_to_raw(
        value : unsigned(14 downto 0)
    ) return std_logic_vector is
    begin
        return std_logic_vector(value);
    end function;

    function voltage_input_20v_u7_from_raw(
        raw : std_logic_vector(6 downto 0)
    ) return unsigned is
    begin
        return unsigned(raw);
    end function;

    function voltage_input_20v_u7_to_raw(
        value : unsigned(6 downto 0)
    ) return std_logic_vector is
    begin
        return std_logic_vector(value);
    end function;

    function voltage_input_25v_s16_from_raw(
        raw : std_logic_vector(15 downto 0)
    ) return signed is
    begin
        return signed(raw);
    end function;

    function voltage_input_25v_s16_to_raw(
        value : signed(15 downto 0)
    ) return std_logic_vector is
    begin
        return std_logic_vector(value);
    end function;

    function voltage_input_25v_s8_from_raw(
        raw : std_logic_vector(7 downto 0)
    ) return signed is
    begin
        return signed(raw);
    end function;

    function voltage_input_25v_s8_to_raw(
        value : signed(7 downto 0)
    ) return std_logic_vector is
    begin
        return std_logic_vector(value);
    end function;

    function voltage_input_25v_u15_from_raw(
        raw : std_logic_vector(14 downto 0)
    ) return unsigned is
    begin
        return unsigned(raw);
    end function;

    function voltage_input_25v_u15_to_raw(
        value : unsigned(14 downto 0)
    ) return std_logic_vector is
    begin
        return std_logic_vector(value);
    end function;

    function voltage_input_25v_u7_from_raw(
        raw : std_logic_vector(6 downto 0)
    ) return unsigned is
    begin
        return unsigned(raw);
    end function;

    function voltage_input_25v_u7_to_raw(
        value : unsigned(6 downto 0)
    ) return std_logic_vector is
    begin
        return std_logic_vector(value);
    end function;

    function voltage_output_05v_s16_from_raw(
        raw : std_logic_vector(15 downto 0)
    ) return signed is
    begin
        return signed(raw);
    end function;

    function voltage_output_05v_s16_to_raw(
        value : signed(15 downto 0)
    ) return std_logic_vector is
    begin
        return std_logic_vector(value);
    end function;

    function voltage_output_05v_s8_from_raw(
        raw : std_logic_vector(7 downto 0)
    ) return signed is
    begin
        return signed(raw);
    end function;

    function voltage_output_05v_s8_to_raw(
        value : signed(7 downto 0)
    ) return std_logic_vector is
    begin
        return std_logic_vector(value);
    end function;

    function voltage_output_05v_u15_from_raw(
        raw : std_logic_vector(14 downto 0)
    ) return unsigned is
    begin
        return unsigned(raw);
    end function;

    function voltage_output_05v_u15_to_raw(
        value : unsigned(14 downto 0)
    ) return std_logic_vector is
    begin
        return std_logic_vector(value);
    end function;

    function voltage_output_05v_u7_from_raw(
        raw : std_logic_vector(6 downto 0)
    ) return unsigned is
    begin
        return unsigned(raw);
    end function;

    function voltage_output_05v_u7_to_raw(
        value : unsigned(6 downto 0)
    ) return std_logic_vector is
    begin
        return std_logic_vector(value);
    end function;

end package body forge_serialization_voltage_pkg;
