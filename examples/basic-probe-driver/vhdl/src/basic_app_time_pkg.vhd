--------------------------------------------------------------------------------
-- File: basic_app_time_pkg.vhd
-- Author: Stub package for P2 FSM compilation test
-- Date: 2025-11-05
-- Version: 0.1 (STUB)
--
-- Description:
--   Minimal stub package for basic_app_time_pkg.
--   Provides time-to-cycles conversion functions for Basic Probe Driver.
--
-- Status: STUB - Will be replaced by forge-codegen generated code
--
-- Note: This is a minimal stub to satisfy dependency checking during
--       initial FSM compilation. The real package will be generated from
--       basic_probe_driver.yaml using forge-codegen tools.
--
-- Functions:
--   - s_to_cycles()  : seconds → clock cycles
--   - us_to_cycles() : microseconds → clock cycles
--   - ns_to_cycles() : nanoseconds → clock cycles
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

package basic_app_time_pkg is

    ----------------------------------------------------------------------------
    -- Time to Cycles Conversion Functions
    ----------------------------------------------------------------------------

    -- Convert seconds to clock cycles
    -- input: time in seconds (16-bit unsigned from YAML)
    -- clk_freq_hz: clock frequency in Hz
    -- returns: number of clock cycles (32-bit)
    function s_to_cycles(
        time_s      : unsigned(15 downto 0);
        clk_freq_hz : integer
    ) return unsigned;

    -- Convert microseconds to clock cycles
    -- input: time in microseconds (24-bit unsigned from YAML)
    -- clk_freq_hz: clock frequency in Hz
    -- returns: number of clock cycles (32-bit)
    function us_to_cycles(
        time_us     : unsigned(23 downto 0);
        clk_freq_hz : integer
    ) return unsigned;

    -- Convert nanoseconds to clock cycles (16-bit input)
    -- input: time in nanoseconds (16-bit unsigned from YAML)
    -- clk_freq_hz: clock frequency in Hz
    -- returns: number of clock cycles (32-bit)
    function ns_to_cycles(
        time_ns     : unsigned(15 downto 0);
        clk_freq_hz : integer
    ) return unsigned;

    -- Convert nanoseconds to clock cycles (32-bit input - overloaded)
    -- input: time in nanoseconds (32-bit unsigned from YAML)
    -- clk_freq_hz: clock frequency in Hz
    -- returns: number of clock cycles (32-bit)
    function ns_to_cycles_32(
        time_ns     : unsigned(31 downto 0);
        clk_freq_hz : integer
    ) return unsigned;

end package basic_app_time_pkg;

package body basic_app_time_pkg is

    ----------------------------------------------------------------------------
    -- s_to_cycles: seconds → clock cycles
    ----------------------------------------------------------------------------
    function s_to_cycles(
        time_s      : unsigned(15 downto 0);
        clk_freq_hz : integer
    ) return unsigned is
    begin
        -- cycles = time_s * clk_freq_hz
        -- Use simple cast - let VHDL handle it
        -- For typical values (time_s up to 65535 s, clk_freq_hz = 125 MHz),
        -- result fits in 47 bits, well within unsigned capacity
        if time_s = 0 then
            return to_unsigned(0, 32);
        else
            -- Convert to integer, multiply, convert back
            -- This avoids GHDL bound checking issues with unsigned*integer
            return to_unsigned(to_integer(time_s) * clk_freq_hz, 32);
        end if;
    end function s_to_cycles;

    ----------------------------------------------------------------------------
    -- us_to_cycles: microseconds → clock cycles
    ----------------------------------------------------------------------------
    function us_to_cycles(
        time_us     : unsigned(23 downto 0);
        clk_freq_hz : integer
    ) return unsigned is
    begin
        -- cycles = (time_us * clk_freq_hz) / 1_000_000
        -- Simplified: time_us * (clk_freq_hz / 1_000_000)
        if time_us = 0 then
            return to_unsigned(0, 32);
        else
            return to_unsigned(to_integer(time_us) * (clk_freq_hz / 1000000), 32);
        end if;
    end function us_to_cycles;

    ----------------------------------------------------------------------------
    -- ns_to_cycles: nanoseconds → clock cycles (16-bit input)
    ----------------------------------------------------------------------------
    function ns_to_cycles(
        time_ns     : unsigned(15 downto 0);
        clk_freq_hz : integer
    ) return unsigned is
    begin
        -- cycles = (time_ns * clk_freq_hz) / 1_000_000_000
        -- At 125 MHz: 1 cycle = 8 ns, so ns / 8 = cycles
        if time_ns = 0 then
            return to_unsigned(0, 32);
        else
            return to_unsigned((to_integer(time_ns) * clk_freq_hz) / 1000000000, 32);
        end if;
    end function ns_to_cycles;

    ----------------------------------------------------------------------------
    -- ns_to_cycles_32: nanoseconds → clock cycles (32-bit input)
    ----------------------------------------------------------------------------
    function ns_to_cycles_32(
        time_ns     : unsigned(31 downto 0);
        clk_freq_hz : integer
    ) return unsigned is
    begin
        -- cycles = (time_ns * clk_freq_hz) / 1_000_000_000
        if time_ns = 0 then
            return to_unsigned(0, 32);
        else
            return to_unsigned((to_integer(time_ns) * clk_freq_hz) / 1000000000, 32);
        end if;
    end function ns_to_cycles_32;

end package body basic_app_time_pkg;
