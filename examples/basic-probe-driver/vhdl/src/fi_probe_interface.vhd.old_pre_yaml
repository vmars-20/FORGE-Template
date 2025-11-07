--------------------------------------------------------------------------------
-- FI Probe Interface (Vendor-Agnostic)
--
-- Standard interface for fault injection probe control.
-- Design inspired by Riscure DS1120A (de facto standard) but generic enough
-- for other vendors (laser FI, EM probes, voltage glitching, etc.)
--
-- Interface Philosophy:
-- - Simple control signals (trigger, pulse width, voltage level)
-- - Status feedback (ready, fault detection)
-- - Configurable bit widths for different probe capabilities
--
-- Typical Usage:
-- 1. Configure pulse_width and voltage_level
-- 2. Wait for ready = '1'
-- 3. Assert trigger_in to fire probe
-- 4. Monitor fault signal for hardware errors
--
-- Author: BPD Project
-- License: MIT
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity fi_probe_interface is
    generic (
        -- Configurability for different probe types
        PULSE_WIDTH_BITS : integer := 16;  -- 16-bit = 0-65535ns range
        VOLTAGE_BITS     : integer := 16   -- 16-bit signed for ±voltage
    );
    port (
        -- Clock and Reset
        clk              : in  std_logic;
        rst_n            : in  std_logic;  -- Active-low reset

        -- Control from Moku (register interface)
        trigger_in       : in  std_logic;  -- Trigger probe (pulse)
        arm              : in  std_logic;  -- Arm probe (must be high to trigger)
        pulse_width      : in  unsigned(PULSE_WIDTH_BITS-1 downto 0);  -- Pulse width in ns
        voltage_level    : in  signed(VOLTAGE_BITS-1 downto 0);        -- Target voltage (DAC value)

        -- Output to probe hardware
        probe_trigger    : out std_logic;  -- Trigger signal to probe
        probe_pulse_ctrl : out std_logic;  -- Pulse control signal (high during pulse)
        probe_voltage    : out signed(VOLTAGE_BITS-1 downto 0);  -- Voltage control to probe DAC

        -- Status feedback
        ready            : out std_logic;  -- Probe ready for trigger
        busy             : out std_logic;  -- Probe busy (pulse in progress)
        fault            : out std_logic   -- Hardware fault detected
    );
end entity fi_probe_interface;

architecture rtl of fi_probe_interface is

    -- State machine for probe control
    type state_t is (IDLE, ARMED, PULSE_ACTIVE, COOLDOWN, FAULT_STATE);
    signal state : state_t;

    -- Internal signals
    signal pulse_counter : unsigned(PULSE_WIDTH_BITS-1 downto 0);
    signal cooldown_counter : unsigned(7 downto 0);  -- Fixed 256-cycle cooldown

    -- Edge detection for trigger
    signal trigger_prev : std_logic;
    signal trigger_edge : std_logic;

    -- Constants
    constant COOLDOWN_CYCLES : unsigned(7 downto 0) := to_unsigned(255, 8);

begin

    -- Edge detector for trigger input
    trigger_edge <= trigger_in and not trigger_prev;

    -- Main state machine
    process(clk, rst_n)
    begin
        if rst_n = '0' then
            state <= IDLE;
            pulse_counter <= (others => '0');
            cooldown_counter <= (others => '0');
            trigger_prev <= '0';
            probe_trigger <= '0';
            probe_pulse_ctrl <= '0';
            probe_voltage <= (others => '0');
            ready <= '0';
            busy <= '0';
            fault <= '0';

        elsif rising_edge(clk) then
            trigger_prev <= trigger_in;

            case state is

                when IDLE =>
                    -- Waiting for arm signal
                    probe_pulse_ctrl <= '0';
                    probe_trigger <= '0';
                    busy <= '0';

                    if arm = '1' then
                        state <= ARMED;
                        ready <= '1';
                        probe_voltage <= voltage_level;  -- Set voltage when armed
                    else
                        ready <= '0';
                    end if;

                when ARMED =>
                    -- Armed and ready for trigger
                    ready <= '1';
                    busy <= '0';
                    probe_voltage <= voltage_level;  -- Update voltage if changed

                    if arm = '0' then
                        -- Disarmed
                        state <= IDLE;
                        ready <= '0';
                    elsif trigger_edge = '1' then
                        -- Trigger detected!
                        state <= PULSE_ACTIVE;
                        pulse_counter <= pulse_width;
                        probe_trigger <= '1';  -- Single-cycle trigger pulse
                        probe_pulse_ctrl <= '1';
                        ready <= '0';
                        busy <= '1';
                    end if;

                when PULSE_ACTIVE =>
                    -- Generate pulse of specified width
                    probe_trigger <= '0';  -- Trigger is single-cycle
                    busy <= '1';

                    if pulse_counter > 0 then
                        pulse_counter <= pulse_counter - 1;
                        probe_pulse_ctrl <= '1';
                    else
                        -- Pulse complete
                        probe_pulse_ctrl <= '0';
                        state <= COOLDOWN;
                        cooldown_counter <= COOLDOWN_CYCLES;
                    end if;

                when COOLDOWN =>
                    -- Cooldown period after pulse (prevents rapid re-triggering)
                    busy <= '1';
                    probe_pulse_ctrl <= '0';

                    if cooldown_counter > 0 then
                        cooldown_counter <= cooldown_counter - 1;
                    else
                        busy <= '0';
                        if arm = '1' then
                            state <= ARMED;  -- Return to armed if still armed
                        else
                            state <= IDLE;   -- Otherwise go idle
                        end if;
                    end if;

                when FAULT_STATE =>
                    -- Hardware fault detected (future implementation)
                    ready <= '0';
                    busy <= '0';
                    fault <= '1';
                    probe_pulse_ctrl <= '0';
                    probe_trigger <= '0';

                    -- Exit fault state on reset or disarm
                    if arm = '0' then
                        state <= IDLE;
                        fault <= '0';
                    end if;

            end case;
        end if;
    end process;

end architecture rtl;
