------------------------------------------------------------------------------
-- forge_serialization_time_pkg.vhd
--
-- Time serialization utilities for control register communication
--
-- Migrated from: tools/forge-codegen/forge_codegen/vhdl/basic_app_time_pkg.vhd
-- Version: 1.0.0 (FROZEN - DO NOT REGENERATE)
-- Date: 2025-11-06
--
-- This package provides conversion functions between time durations and clock
-- cycles for serialized time-based data.
--
-- All functions are clock-frequency aware and accept CLK_FREQ_HZ as a parameter.
--
-- Part of: moku-instrument-forge-vhdl
------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library WORK;
use WORK.forge_serialization_types_pkg.ALL;

package forge_serialization_time_pkg is

    ------------------------------------------------------------------------------
    -- Time Unit Conversions
    ------------------------------------------------------------------------------

    -- Convert nanoseconds to clock cycles
    function ns_to_cycles(
        ns_value : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned;

    -- Convert clock cycles to nanoseconds
    function cycles_to_ns(
        cycles : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned;

    -- Convert microseconds to clock cycles
    function us_to_cycles(
        us_value : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned;

    -- Convert clock cycles to microseconds
    function cycles_to_us(
        cycles : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned;

    -- Convert milliseconds to clock cycles
    function ms_to_cycles(
        ms_value : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned;

    -- Convert clock cycles to milliseconds
    function cycles_to_ms(
        cycles : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned;

    -- Convert seconds to clock cycles
    function s_to_cycles(
        s_value : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned;

    -- Convert clock cycles to seconds
    function cycles_to_s(
        cycles : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned;

end package forge_serialization_time_pkg;

package body forge_serialization_time_pkg is

    function ns_to_cycles(
        ns_value : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned is
        variable cycles_per_ns : real;
        variable result : unsigned(ns_value'length-1 downto 0);
    begin
        cycles_per_ns := real(CLK_FREQ_HZ) / 1.0e9;
        result := to_unsigned(integer(real(to_integer(ns_value)) * cycles_per_ns), ns_value'length);
        return result;
    end function;

    function cycles_to_ns(
        cycles : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned is
        variable ns_per_cycle : real;
        variable result : unsigned(cycles'length-1 downto 0);
    begin
        ns_per_cycle := 1.0e9 / real(CLK_FREQ_HZ);
        result := to_unsigned(integer(real(to_integer(cycles)) * ns_per_cycle), cycles'length);
        return result;
    end function;

    function us_to_cycles(
        us_value : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned is
        variable cycles_per_us : real;
        variable result : unsigned(us_value'length-1 downto 0);
    begin
        cycles_per_us := real(CLK_FREQ_HZ) / 1.0e6;
        result := to_unsigned(integer(real(to_integer(us_value)) * cycles_per_us), us_value'length);
        return result;
    end function;

    function cycles_to_us(
        cycles : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned is
        variable us_per_cycle : real;
        variable result : unsigned(cycles'length-1 downto 0);
    begin
        us_per_cycle := 1.0e6 / real(CLK_FREQ_HZ);
        result := to_unsigned(integer(real(to_integer(cycles)) * us_per_cycle), cycles'length);
        return result;
    end function;

    function ms_to_cycles(
        ms_value : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned is
        variable cycles_per_ms : real;
        variable result : unsigned(ms_value'length-1 downto 0);
    begin
        cycles_per_ms := real(CLK_FREQ_HZ) / 1.0e3;
        result := to_unsigned(integer(real(to_integer(ms_value)) * cycles_per_ms), ms_value'length);
        return result;
    end function;

    function cycles_to_ms(
        cycles : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned is
        variable ms_per_cycle : real;
        variable result : unsigned(cycles'length-1 downto 0);
    begin
        ms_per_cycle := 1.0e3 / real(CLK_FREQ_HZ);
        result := to_unsigned(integer(real(to_integer(cycles)) * ms_per_cycle), cycles'length);
        return result;
    end function;

    function s_to_cycles(
        s_value : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned is
        variable result : unsigned(s_value'length-1 downto 0);
    begin
        result := to_unsigned(to_integer(s_value) * CLK_FREQ_HZ, s_value'length);
        return result;
    end function;

    function cycles_to_s(
        cycles : unsigned;
        CLK_FREQ_HZ : integer
    ) return unsigned is
        variable result : unsigned(cycles'length-1 downto 0);
    begin
        result := to_unsigned(to_integer(cycles) / CLK_FREQ_HZ, cycles'length);
        return result;
    end function;

end package body forge_serialization_time_pkg;
