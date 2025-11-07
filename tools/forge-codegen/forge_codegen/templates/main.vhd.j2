--------------------------------------------------------------------------------
-- File: {{ app_name }}_custom_inst_main.vhd
-- Generated: {{ timestamp }}
-- Generator: tools/generate_custom_inst_v2.py
-- Template Version: 2.0 (BasicAppDataTypes)
--
-- ⚠️  GENERATED TEMPLATE - CUSTOMIZE FOR YOUR APPLICATION ⚠️
-- This is a starting point template. Implement your application logic here.
--
-- Description:
--   Main application logic for {{ app_name }}.
--   Receives typed signals from shim, implements application behavior.
--
-- Platform: {{ platform_name }}
-- Clock Frequency: {{ platform_clock_mhz }} MHz
--
-- Application Signals (from register mapping):
{% for signal in signals %}
--   {{ signal.name }}: {{ signal.vhdl_type }} - {{ signal.description }}
{% endfor %}
--
-- References:
--   - {{ yaml_file }}
--   - {{ app_name }}_custom_inst_shim.vhd (auto-generated register mapping)
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library WORK;
use WORK.basic_app_types_pkg.all;
{% if has_voltage_types %}use WORK.basic_app_voltage_pkg.all;
{% endif %}{% if has_time_types %}use WORK.basic_app_time_pkg.all;
{% endif %}
entity {{ app_name }}_custom_inst_main is
    generic (
        CLK_FREQ_HZ : integer := {{ platform_clock_hz }}  -- {{ platform_name }} clock frequency
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
{% for signal in signals %}
        {{ signal.name }}{% if signal.direction == 'output' %}_out{% endif %} : {% if signal.direction == 'output' %}out{% else %}in{% endif %} {{ signal.vhdl_type }}{% if not loop.last %};{% endif %}
{% endfor %}
    );
end entity {{ app_name }}_custom_inst_main;

architecture rtl of {{ app_name }}_custom_inst_main is

    ----------------------------------------------------------------------------
    -- Internal Signals
    ----------------------------------------------------------------------------
    -- TODO: Add your application-specific signals here

    -- Example state machine (customize for your application)
    type state_t is (IDLE, ACTIVE, DONE);
    signal state : state_t;

    ----------------------------------------------------------------------------
    -- Time Conversion Signals (if needed for time-based datatypes)
    ----------------------------------------------------------------------------
{% for signal in signals %}
{% if signal.is_time %}
    signal {{ signal.name }}_cycles : unsigned(31 downto 0);  -- {{ signal.name }} converted to clock cycles
{% endif %}
{% endfor %}

begin

    ------------------------------------------------------------------------
    -- Ready for Updates
    --
    -- Drive this signal based on your application's update policy:
    --   '1' = Safe to update registers (typical: always ready)
    --   '0' = Hold current values (use during critical operations)
    ------------------------------------------------------------------------
    ready_for_updates <= '1';  -- TODO: Customize based on your application

{% if has_time_types %}
    ------------------------------------------------------------------------
    -- Time to Cycles Conversions
    --
    -- Convert time durations to clock cycles using platform-aware functions
    ------------------------------------------------------------------------
{% for signal in signals %}
{% if signal.is_time %}
    -- Convert {{ signal.name }} ({{ signal.unit }}) to clock cycles
    {{ signal.name }}_cycles <= {{ signal.unit }}_to_cycles({{ signal.name }}, CLK_FREQ_HZ);
{% endif %}
{% endfor %}
{% endif %}

    ------------------------------------------------------------------------
    -- Main Application Logic
    --
    -- TODO: Implement your application behavior here
    --
    -- Available inputs:
{% for signal in signals %}
{% if signal.direction == 'input' %}
    --   - {{ signal.name }}: {{ signal.vhdl_type }} - {{ signal.description }}
{% if signal.is_time %}
    --     ({{ signal.name }}_cycles contains clock-cycle equivalent)
{% endif %}
{% endif %}
{% endfor %}
    --
    -- Outputs to drive:
{% for signal in signals %}
{% if signal.direction == 'output' %}
    --   - {{ signal.name }}_out: {{ signal.vhdl_type }} - {{ signal.description }}
{% endif %}
{% endfor %}
    ------------------------------------------------------------------------
    MAIN_PROC: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                state <= IDLE;
                -- TODO: Initialize output signals
{% for signal in signals %}
{% if signal.direction == 'output' %}
    {% if signal.is_boolean %}
                {{ signal.name }}_out <= '0';
    {% else %}
                {{ signal.name }}_out <= (others => '0');
    {% endif %}
{% endif %}
{% endfor %}
            elsif global_enable = '1' then
                -- TODO: Implement your state machine / application logic
                case state is
                    when IDLE =>
                        -- Example: Wait for trigger condition
                        state <= IDLE;

                    when ACTIVE =>
                        -- Example: Perform main operation
                        state <= DONE;

                    when DONE =>
                        -- Example: Return to idle
                        state <= IDLE;

                    when others =>
                        state <= IDLE;
                end case;
            end if;
        end if;
    end process MAIN_PROC;

end architecture rtl;
