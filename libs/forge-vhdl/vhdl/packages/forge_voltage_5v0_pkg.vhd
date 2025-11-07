--------------------------------------------------------------------------------
-- Package: forge_voltage_5v0_pkg
-- Purpose: 0-5.0V unipolar voltage domain utilities
-- Domain: Sensor supply, unipolar DAC outputs
-- Author: Moku Instrument Forge Team
-- Date: 2025-11-04
--
-- VOLTAGE DOMAIN: 0-5.0V unipolar (sensor supply, unipolar analog)
--
-- VOLTAGE SPECIFICATION:
-- - Digital range: 0 to +32767 (0x0000 to 0x7FFF)
-- - Voltage range: 0.0V to +5.0V (unipolar)
-- - Resolution: ~152.59 µV per digital step (5.0V / 32767)
-- - Scale factor: 6553.4 digital units per volt
--
-- USE CASES:
-- - Sensor power supply control
-- - 0-5V DAC outputs
-- - Unipolar analog signal generation
-- - Reference voltage generation
-- - Power management
--
-- VERILOG COMPATIBILITY:
-- - Uses only standard VHDL types (real, signed, natural)
-- - No records, physical types, or enums
-- - All functions use simple parameter types
-- - Direct translation to Verilog possible
--
-- DESIGN PHILOSOPHY:
-- - Explicit package selection enforces voltage domain
-- - Function-based conversions (not language types)
-- - Runtime validation with clamping
-- - Self-documenting through package name
--
-- PYTHON MIRROR:
-- - See: docs/migration/voltage_types_reference.py
-- - Class: Voltage_5V0
-- - 1:1 function mapping with VHDL
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

package forge_voltage_5v0_pkg is

    -- =============================================================================
    -- VOLTAGE DOMAIN CONSTANTS (0-5.0V unipolar)
    -- =============================================================================

    -- Voltage range constants (real values in volts)
    constant V_MIN : real := 0.0;
    constant V_MAX : real := 5.0;
    constant V_ZERO : real := 0.0;

    -- Digital range constants (16-bit signed, unipolar mapping)
    constant DIGITAL_MIN : signed(15 downto 0) := to_signed(0, 16);      -- 0x0000
    constant DIGITAL_MAX : signed(15 downto 0) := to_signed(32767, 16);  -- 0x7FFF
    constant DIGITAL_ZERO : signed(15 downto 0) := to_signed(0, 16);     -- 0x0000

    -- Resolution and scaling constants
    constant VOLTAGE_RESOLUTION : real := 5.0 / 32767.0;  -- ~152.59 µV per step
    constant SCALE_FACTOR : real := 32767.0 / 5.0;        -- 6553.4 digital units per volt

    -- Common voltage reference points (digital values)
    constant DIGITAL_1V0 : signed(15 downto 0) := to_signed(6553, 16);   -- 0x1999 (1.0V)
    constant DIGITAL_1V8 : signed(15 downto 0) := to_signed(11796, 16);  -- 0x2E14 (1.8V)
    constant DIGITAL_2V5 : signed(15 downto 0) := to_signed(16384, 16);  -- 0x4000 (2.5V)
    constant DIGITAL_3V0 : signed(15 downto 0) := to_signed(19660, 16);  -- 0x4CCC (3.0V)
    constant DIGITAL_3V3 : signed(15 downto 0) := to_signed(21627, 16);  -- 0x54AB (3.3V)
    constant DIGITAL_5V0 : signed(15 downto 0) := to_signed(32767, 16);  -- 0x7FFF (5.0V)

    -- =============================================================================
    -- CONVERSION FUNCTIONS
    -- =============================================================================

    -- Convert voltage (real) to digital value (signed 16-bit)
    -- Clamps to valid range [0.0, 5.0]V automatically
    function to_digital(voltage : real) return signed;

    -- Convert digital value (signed 16-bit) to voltage (real)
    function from_digital(digital : signed(15 downto 0)) return real;

    -- Convert digital value (std_logic_vector) to voltage (real)
    function from_digital(digital : std_logic_vector(15 downto 0)) return real;

    -- Convert voltage (real) to digital value (std_logic_vector)
    function to_digital_vector(voltage : real) return std_logic_vector;

    -- =============================================================================
    -- VALIDATION FUNCTIONS
    -- =============================================================================

    -- Check if voltage is within valid domain [0.0, 5.0]V
    function is_valid(voltage : real) return boolean;

    -- Check if digital value is within valid range [0, 32767]
    function is_valid_digital(digital : signed(15 downto 0)) return boolean;
    function is_valid_digital(digital : std_logic_vector(15 downto 0)) return boolean;

    -- Clamp voltage to valid domain [0.0, 5.0]V
    function clamp(voltage : real) return real;

    -- Clamp digital value to valid range [0, 32767]
    function clamp_digital(digital : signed(15 downto 0)) return signed;
    function clamp_digital(digital : std_logic_vector(15 downto 0)) return std_logic_vector;

    -- =============================================================================
    -- TESTBENCH CONVENIENCE FUNCTIONS
    -- =============================================================================

    -- Check if digital value represents expected voltage within tolerance
    function is_voltage_equal(
        digital : signed(15 downto 0);
        expected_voltage : real;
        tolerance_volts : real := 0.001
    ) return boolean;

    function is_voltage_equal(
        digital : std_logic_vector(15 downto 0);
        expected_voltage : real;
        tolerance_volts : real := 0.001
    ) return boolean;

    -- Get voltage error between expected and actual
    function get_voltage_error(
        digital : signed(15 downto 0);
        expected_voltage : real
    ) return real;

    function get_voltage_error(
        digital : std_logic_vector(15 downto 0);
        expected_voltage : real
    ) return real;

end package forge_voltage_5v0_pkg;

package body forge_voltage_5v0_pkg is

    -- =============================================================================
    -- CONVERSION FUNCTIONS
    -- =============================================================================

    function to_digital(voltage : real) return signed is
        variable digital_real : real;
        variable digital_int : integer;
    begin
        -- Clamp voltage to valid range [0.0, 5.0]V
        if voltage > V_MAX then
            digital_real := V_MAX * SCALE_FACTOR;
        elsif voltage < V_MIN then
            digital_real := V_MIN * SCALE_FACTOR;
        else
            digital_real := voltage * SCALE_FACTOR;
        end if;

        -- Round to nearest integer
        if digital_real >= 0.0 then
            digital_int := integer(digital_real + 0.5);
        else
            digital_int := integer(digital_real - 0.5);
        end if;

        -- Clamp to 16-bit signed range [0, 32767] (unipolar)
        if digital_int > 32767 then
            digital_int := 32767;
        elsif digital_int < 0 then
            digital_int := 0;
        end if;

        return to_signed(digital_int, 16);
    end function;

    function from_digital(digital : signed(15 downto 0)) return real is
    begin
        return real(to_integer(digital)) / SCALE_FACTOR;
    end function;

    function from_digital(digital : std_logic_vector(15 downto 0)) return real is
    begin
        return from_digital(signed(digital));
    end function;

    function to_digital_vector(voltage : real) return std_logic_vector is
    begin
        return std_logic_vector(to_digital(voltage));
    end function;

    -- =============================================================================
    -- VALIDATION FUNCTIONS
    -- =============================================================================

    function is_valid(voltage : real) return boolean is
    begin
        return (voltage >= V_MIN) and (voltage <= V_MAX);
    end function;

    function is_valid_digital(digital : signed(15 downto 0)) return boolean is
    begin
        return (digital >= DIGITAL_MIN) and (digital <= DIGITAL_MAX);
    end function;

    function is_valid_digital(digital : std_logic_vector(15 downto 0)) return boolean is
    begin
        return is_valid_digital(signed(digital));
    end function;

    function clamp(voltage : real) return real is
    begin
        if voltage > V_MAX then
            return V_MAX;
        elsif voltage < V_MIN then
            return V_MIN;
        else
            return voltage;
        end if;
    end function;

    function clamp_digital(digital : signed(15 downto 0)) return signed is
    begin
        if digital > DIGITAL_MAX then
            return DIGITAL_MAX;
        elsif digital < DIGITAL_MIN then
            return DIGITAL_MIN;
        else
            return digital;
        end if;
    end function;

    function clamp_digital(digital : std_logic_vector(15 downto 0)) return std_logic_vector is
    begin
        return std_logic_vector(clamp_digital(signed(digital)));
    end function;

    -- =============================================================================
    -- TESTBENCH CONVENIENCE FUNCTIONS
    -- =============================================================================

    function is_voltage_equal(
        digital : signed(15 downto 0);
        expected_voltage : real;
        tolerance_volts : real := 0.001
    ) return boolean is
        variable actual_voltage : real;
        variable voltage_diff : real;
    begin
        actual_voltage := from_digital(digital);
        voltage_diff := abs(actual_voltage - expected_voltage);
        return (voltage_diff <= tolerance_volts);
    end function;

    function is_voltage_equal(
        digital : std_logic_vector(15 downto 0);
        expected_voltage : real;
        tolerance_volts : real := 0.001
    ) return boolean is
    begin
        return is_voltage_equal(signed(digital), expected_voltage, tolerance_volts);
    end function;

    function get_voltage_error(
        digital : signed(15 downto 0);
        expected_voltage : real
    ) return real is
        variable actual_voltage : real;
    begin
        actual_voltage := from_digital(digital);
        return actual_voltage - expected_voltage;
    end function;

    function get_voltage_error(
        digital : std_logic_vector(15 downto 0);
        expected_voltage : real
    ) return real is
    begin
        return get_voltage_error(signed(digital), expected_voltage);
    end function;

end package body forge_voltage_5v0_pkg;
