"""
BasicAppDataTypes enum definitions.

This module contains ONLY the type enum definitions.
For metadata and conversions, see metadata.py and converters.py.

Design References:
- Voltage types: docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md
- Time types: docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md
"""

from enum import Enum


class BasicAppDataTypes(str, Enum):
    """
    Fixed-width data types for BasicAppDataTypes system.

    Design principles:
    - Fixed, immutable bit widths
    - Platform-agnostic definitions
    - Self-documenting type names
    - No endianness (MSB-aligned packing)

    Total types: 25 (12 voltage + 12 time + 1 boolean)
    """

    # ========================================================================
    # VOLTAGE TYPES (12 total)
    # See: docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md
    # ========================================================================

    # Output voltage types (DAC) - All platforms support +-5V
    VOLTAGE_OUTPUT_05V_S8 = "voltage_output_05v_s8"      # 8-bit signed, +-5V
    VOLTAGE_OUTPUT_05V_S16 = "voltage_output_05v_s16"    # 16-bit signed, +-5V
    VOLTAGE_OUTPUT_05V_U7 = "voltage_output_05v_u7"      # 7-bit unsigned, 0 to +5V
    VOLTAGE_OUTPUT_05V_U15 = "voltage_output_05v_u15"    # 15-bit unsigned, 0 to +5V

    # Input voltage types (ADC) - Delta: +-20V
    VOLTAGE_INPUT_20V_S8 = "voltage_input_20v_s8"        # 8-bit signed, +-20V
    VOLTAGE_INPUT_20V_S16 = "voltage_input_20v_s16"      # 16-bit signed, +-20V
    VOLTAGE_INPUT_20V_U7 = "voltage_input_20v_u7"        # 7-bit unsigned, 0 to +20V
    VOLTAGE_INPUT_20V_U15 = "voltage_input_20v_u15"      # 15-bit unsigned, 0 to +20V

    # Input voltage types (ADC) - Go/Lab/Pro: +-25V
    VOLTAGE_INPUT_25V_S8 = "voltage_input_25v_s8"        # 8-bit signed, +-25V
    VOLTAGE_INPUT_25V_S16 = "voltage_input_25v_s16"      # 16-bit signed, +-25V
    VOLTAGE_INPUT_25V_U7 = "voltage_input_25v_u7"        # 7-bit unsigned, 0 to +25V
    VOLTAGE_INPUT_25V_U15 = "voltage_input_25v_u15"      # 15-bit unsigned, 0 to +25V

    # ========================================================================
    # TIME TYPES (12 total)
    # See: docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md
    # ========================================================================

    # Nanosecond-based durations
    PULSE_DURATION_NS_U8 = "pulse_duration_ns_u8"        # 8-bit, 0-255 ns
    PULSE_DURATION_NS_U16 = "pulse_duration_ns_u16"      # 16-bit, 0-65,535 ns
    PULSE_DURATION_NS_U32 = "pulse_duration_ns_u32"      # 32-bit, 0-4.29 sec

    # Microsecond-based durations
    PULSE_DURATION_US_U8 = "pulse_duration_us_u8"        # 8-bit, 0-255 us
    PULSE_DURATION_US_U16 = "pulse_duration_us_u16"      # 16-bit, 0-65,535 us
    PULSE_DURATION_US_U24 = "pulse_duration_us_u24"      # 24-bit, 0-16.7 sec

    # Millisecond-based durations
    PULSE_DURATION_MS_U8 = "pulse_duration_ms_u8"        # 8-bit, 0-255 ms
    PULSE_DURATION_MS_U16 = "pulse_duration_ms_u16"      # 16-bit, 0-65,535 ms

    # Second-based durations
    PULSE_DURATION_S_U8 = "pulse_duration_s_u8"          # 8-bit, 0-255 seconds
    PULSE_DURATION_S_U16 = "pulse_duration_s_u16"        # 16-bit, 0-65,535 seconds

    # ========================================================================
    # BOOLEAN TYPE (1 total)
    # ========================================================================

    BOOLEAN = "boolean"  # 1-bit, True/False
