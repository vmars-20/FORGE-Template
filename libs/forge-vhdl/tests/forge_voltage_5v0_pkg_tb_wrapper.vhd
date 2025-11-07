--------------------------------------------------------------------------------
-- Test wrapper for forge_voltage_5v0_pkg
-- Purpose: Expose package functions as testable ports for CocoTB
--
-- IMPORTANT: CocoTB cannot access 'real' or 'boolean' types!
-- This wrapper uses only digital types (signed, std_logic) at the entity
-- boundary and converts internally.
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library work;
use work.forge_voltage_5v0_pkg.all;

entity forge_voltage_5v0_pkg_tb_wrapper is
    port (
        -- Clock and reset
        clk : in std_logic;
        reset : in std_logic;

        -- Test inputs (digital types only!)
        test_voltage_digital : in signed(15 downto 0);  -- Scaled voltage (0-32767)
        test_digital : in signed(15 downto 0);

        -- Function selects (one-hot)
        sel_to_digital : in std_logic;
        sel_from_digital : in std_logic;
        sel_is_valid : in std_logic;
        sel_clamp : in std_logic;

        -- Conversion outputs (digital types only!)
        digital_result : out signed(15 downto 0);
        voltage_result : out signed(15 downto 0);      -- Scaled voltage output

        -- Validation outputs (std_logic, not boolean!)
        is_valid_result : out std_logic;
        clamped_result : out signed(15 downto 0)       -- Scaled voltage output
    );
end entity forge_voltage_5v0_pkg_tb_wrapper;

architecture rtl of forge_voltage_5v0_pkg_tb_wrapper is
    -- Internal real values (only used inside wrapper)
    signal voltage_real : real;
    signal voltage_out_real : real;
    signal clamped_real : real;
begin

    -- Convert digital input to real voltage for package functions
    -- Scale: 0x0000 → 0.0V, 0x7FFF (32767) → 5.0V
    voltage_real <= (real(to_integer(test_voltage_digital)) / 32767.0) * 5.0;

    -- Registered outputs for timing stability
    process(clk, reset)
    begin
        if reset = '1' then
            digital_result <= (others => '0');
            voltage_result <= (others => '0');
            is_valid_result <= '0';
            clamped_result <= (others => '0');

        elsif rising_edge(clk) then
            -- Test to_digital function
            if sel_to_digital = '1' then
                digital_result <= to_digital(voltage_real);
            end if;

            -- Test from_digital function (convert back to digital for output)
            if sel_from_digital = '1' then
                -- Direct conversion (no intermediate signal to avoid delta cycle issues)
                voltage_result <= to_signed(integer((from_digital(test_digital) / 5.0) * 32767.0), 16);
            end if;

            -- Test is_valid (convert boolean to std_logic for CocoTB)
            if sel_is_valid = '1' then
                if is_valid(voltage_real) then
                    is_valid_result <= '1';
                else
                    is_valid_result <= '0';
                end if;
            end if;

            -- Test clamp function
            if sel_clamp = '1' then
                -- Direct conversion (no intermediate signal to avoid delta cycle issues)
                clamped_result <= to_signed(integer((clamp(voltage_real) / 5.0) * 32767.0), 16);
            end if;
        end if;
    end process;

end architecture rtl;
