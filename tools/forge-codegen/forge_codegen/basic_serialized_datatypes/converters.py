"""
Conversion utilities for BasicAppDataTypes.

Handles bidirectional conversion between user-friendly units
(millivolts, nanoseconds) and raw binary values for serialization.

Design References:
- Voltage conversions: docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md
- Time conversions: docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md
"""

import math
from typing import Literal


class TypeConverter:
    """
    Conversion utilities for BasicAppDataTypes.

    Provides static methods for converting between user-friendly units
    and raw binary values suitable for FPGA register serialization.

    All voltage conversions work in millivolts (mV).
    All time conversions work in platform-specific clock cycles.
    """

    # ========================================================================
    # VOLTAGE OUTPUT CONVERSIONS (+-5V, all platforms)
    # ========================================================================

    @staticmethod
    def voltage_output_05v_s8_to_raw(millivolts: int) -> int:
        """
        Convert millivolts to 8-bit signed raw value (+-5V range).

        Args:
            millivolts: Voltage in millivolts (-5000 to +5000)

        Returns:
            8-bit signed raw value (-128 to +127)

        Raises:
            ValueError: If millivolts out of range
        """
        if not (-5000 <= millivolts <= 5000):
            raise ValueError(f"Voltage {millivolts}mV out of +-5V range")

        # Scale: (mV / 5000.0) * 127
        raw = int((millivolts / 5000.0) * 127)
        return max(-128, min(127, raw))  # Clamp to 8-bit signed range

    @staticmethod
    def raw_to_voltage_output_05v_s8(raw: int) -> int:
        """
        Convert 8-bit signed raw to millivolts (+-5V range).

        Args:
            raw: 8-bit signed raw value (-128 to +127)

        Returns:
            Voltage in millivolts
        """
        if not (-128 <= raw <= 127):
            raise ValueError(f"Raw value {raw} out of 8-bit signed range")

        # Scale: (raw / 127.0) * 5000
        return int((raw / 127.0) * 5000)

    @staticmethod
    def voltage_output_05v_s16_to_raw(millivolts: int) -> int:
        """
        Convert millivolts to 16-bit signed raw value (+-5V range).

        Args:
            millivolts: Voltage in millivolts (-5000 to +5000)

        Returns:
            16-bit signed raw value (-32768 to +32767)

        Raises:
            ValueError: If millivolts out of range
        """
        if not (-5000 <= millivolts <= 5000):
            raise ValueError(f"Voltage {millivolts}mV out of +-5V range")

        # Scale: (mV / 5000.0) * 32767
        raw = int((millivolts / 5000.0) * 32767)
        return max(-32768, min(32767, raw))  # Clamp to 16-bit signed range

    @staticmethod
    def raw_to_voltage_output_05v_s16(raw: int) -> int:
        """
        Convert 16-bit signed raw to millivolts (+-5V range).

        Args:
            raw: 16-bit signed raw value (-32768 to +32767)

        Returns:
            Voltage in millivolts
        """
        if not (-32768 <= raw <= 32767):
            raise ValueError(f"Raw value {raw} out of 16-bit signed range")

        # Scale: (raw / 32767.0) * 5000
        return int((raw / 32767.0) * 5000)

    @staticmethod
    def voltage_output_05v_u7_to_raw(millivolts: int) -> int:
        """
        Convert millivolts to 7-bit unsigned raw value (0 to +5V range).

        Args:
            millivolts: Voltage in millivolts (0 to +5000)

        Returns:
            7-bit unsigned raw value (0 to 127)

        Raises:
            ValueError: If millivolts out of range
        """
        if not (0 <= millivolts <= 5000):
            raise ValueError(f"Voltage {millivolts}mV out of 0 to +5V range")

        # Scale: (mV / 5000.0) * 127
        raw = int((millivolts / 5000.0) * 127)
        return max(0, min(127, raw))  # Clamp to 7-bit unsigned range

    @staticmethod
    def raw_to_voltage_output_05v_u7(raw: int) -> int:
        """
        Convert 7-bit unsigned raw to millivolts (0 to +5V range).

        Args:
            raw: 7-bit unsigned raw value (0 to 127)

        Returns:
            Voltage in millivolts
        """
        if not (0 <= raw <= 127):
            raise ValueError(f"Raw value {raw} out of 7-bit unsigned range")

        # Scale: (raw / 127.0) * 5000
        return int((raw / 127.0) * 5000)

    @staticmethod
    def voltage_output_05v_u15_to_raw(millivolts: int) -> int:
        """
        Convert millivolts to 15-bit unsigned raw value (0 to +5V range).

        Args:
            millivolts: Voltage in millivolts (0 to +5000)

        Returns:
            15-bit unsigned raw value (0 to 32767)

        Raises:
            ValueError: If millivolts out of range
        """
        if not (0 <= millivolts <= 5000):
            raise ValueError(f"Voltage {millivolts}mV out of 0 to +5V range")

        # Scale: (mV / 5000.0) * 32767
        raw = int((millivolts / 5000.0) * 32767)
        return max(0, min(32767, raw))  # Clamp to 15-bit unsigned range

    @staticmethod
    def raw_to_voltage_output_05v_u15(raw: int) -> int:
        """
        Convert 15-bit unsigned raw to millivolts (0 to +5V range).

        Args:
            raw: 15-bit unsigned raw value (0 to 32767)

        Returns:
            Voltage in millivolts
        """
        if not (0 <= raw <= 32767):
            raise ValueError(f"Raw value {raw} out of 15-bit unsigned range")

        # Scale: (raw / 32767.0) * 5000
        return int((raw / 32767.0) * 5000)

    # ========================================================================
    # VOLTAGE INPUT CONVERSIONS (+-20V, Moku:Delta)
    # ========================================================================

    @staticmethod
    def voltage_input_20v_s8_to_raw(millivolts: int) -> int:
        """Convert millivolts to 8-bit signed raw value (+-20V range)."""
        if not (-20000 <= millivolts <= 20000):
            raise ValueError(f"Voltage {millivolts}mV out of +-20V range")

        raw = int((millivolts / 20000.0) * 127)
        return max(-128, min(127, raw))

    @staticmethod
    def raw_to_voltage_input_20v_s8(raw: int) -> int:
        """Convert 8-bit signed raw to millivolts (+-20V range)."""
        if not (-128 <= raw <= 127):
            raise ValueError(f"Raw value {raw} out of 8-bit signed range")

        return int((raw / 127.0) * 20000)

    @staticmethod
    def voltage_input_20v_s16_to_raw(millivolts: int) -> int:
        """Convert millivolts to 16-bit signed raw value (+-20V range)."""
        if not (-20000 <= millivolts <= 20000):
            raise ValueError(f"Voltage {millivolts}mV out of +-20V range")

        raw = int((millivolts / 20000.0) * 32767)
        return max(-32768, min(32767, raw))

    @staticmethod
    def raw_to_voltage_input_20v_s16(raw: int) -> int:
        """Convert 16-bit signed raw to millivolts (+-20V range)."""
        if not (-32768 <= raw <= 32767):
            raise ValueError(f"Raw value {raw} out of 16-bit signed range")

        return int((raw / 32767.0) * 20000)

    @staticmethod
    def voltage_input_20v_u7_to_raw(millivolts: int) -> int:
        """Convert millivolts to 7-bit unsigned raw value (0 to +20V range)."""
        if not (0 <= millivolts <= 20000):
            raise ValueError(f"Voltage {millivolts}mV out of 0 to +20V range")

        raw = int((millivolts / 20000.0) * 127)
        return max(0, min(127, raw))

    @staticmethod
    def raw_to_voltage_input_20v_u7(raw: int) -> int:
        """Convert 7-bit unsigned raw to millivolts (0 to +20V range)."""
        if not (0 <= raw <= 127):
            raise ValueError(f"Raw value {raw} out of 7-bit unsigned range")

        return int((raw / 127.0) * 20000)

    @staticmethod
    def voltage_input_20v_u15_to_raw(millivolts: int) -> int:
        """Convert millivolts to 15-bit unsigned raw value (0 to +20V range)."""
        if not (0 <= millivolts <= 20000):
            raise ValueError(f"Voltage {millivolts}mV out of 0 to +20V range")

        raw = int((millivolts / 20000.0) * 32767)
        return max(0, min(32767, raw))

    @staticmethod
    def raw_to_voltage_input_20v_u15(raw: int) -> int:
        """Convert 15-bit unsigned raw to millivolts (0 to +20V range)."""
        if not (0 <= raw <= 32767):
            raise ValueError(f"Raw value {raw} out of 15-bit unsigned range")

        return int((raw / 32767.0) * 20000)

    # ========================================================================
    # VOLTAGE INPUT CONVERSIONS (+-25V, Go/Lab/Pro)
    # ========================================================================

    @staticmethod
    def voltage_input_25v_s8_to_raw(millivolts: int) -> int:
        """Convert millivolts to 8-bit signed raw value (+-25V range)."""
        if not (-25000 <= millivolts <= 25000):
            raise ValueError(f"Voltage {millivolts}mV out of +-25V range")

        raw = int((millivolts / 25000.0) * 127)
        return max(-128, min(127, raw))

    @staticmethod
    def raw_to_voltage_input_25v_s8(raw: int) -> int:
        """Convert 8-bit signed raw to millivolts (+-25V range)."""
        if not (-128 <= raw <= 127):
            raise ValueError(f"Raw value {raw} out of 8-bit signed range")

        return int((raw / 127.0) * 25000)

    @staticmethod
    def voltage_input_25v_s16_to_raw(millivolts: int) -> int:
        """Convert millivolts to 16-bit signed raw value (+-25V range)."""
        if not (-25000 <= millivolts <= 25000):
            raise ValueError(f"Voltage {millivolts}mV out of +-25V range")

        raw = int((millivolts / 25000.0) * 32767)
        return max(-32768, min(32767, raw))

    @staticmethod
    def raw_to_voltage_input_25v_s16(raw: int) -> int:
        """Convert 16-bit signed raw to millivolts (+-25V range)."""
        if not (-32768 <= raw <= 32767):
            raise ValueError(f"Raw value {raw} out of 16-bit signed range")

        return int((raw / 32767.0) * 25000)

    @staticmethod
    def voltage_input_25v_u7_to_raw(millivolts: int) -> int:
        """Convert millivolts to 7-bit unsigned raw value (0 to +25V range)."""
        if not (0 <= millivolts <= 25000):
            raise ValueError(f"Voltage {millivolts}mV out of 0 to +25V range")

        raw = int((millivolts / 25000.0) * 127)
        return max(0, min(127, raw))

    @staticmethod
    def raw_to_voltage_input_25v_u7(raw: int) -> int:
        """Convert 7-bit unsigned raw to millivolts (0 to +25V range)."""
        if not (0 <= raw <= 127):
            raise ValueError(f"Raw value {raw} out of 7-bit unsigned range")

        return int((raw / 127.0) * 25000)

    @staticmethod
    def voltage_input_25v_u15_to_raw(millivolts: int) -> int:
        """Convert millivolts to 15-bit unsigned raw value (0 to +25V range)."""
        if not (0 <= millivolts <= 25000):
            raise ValueError(f"Voltage {millivolts}mV out of 0 to +25V range")

        raw = int((millivolts / 25000.0) * 32767)
        return max(0, min(32767, raw))

    @staticmethod
    def raw_to_voltage_input_25v_u15(raw: int) -> int:
        """Convert 15-bit unsigned raw to millivolts (0 to +25V range)."""
        if not (0 <= raw <= 32767):
            raise ValueError(f"Raw value {raw} out of 15-bit unsigned range")

        return int((raw / 32767.0) * 25000)

    # ========================================================================
    # TIME CONVERSIONS (platform-aware)
    # ========================================================================

    @staticmethod
    def time_to_cycles(
        value: int,
        unit: Literal['ns', 'us', 'ms', 's'],
        clock_period_ns: float,
        rounding: Literal['ROUND_UP', 'ROUND_DOWN', 'EXACT']
    ) -> int:
        """
        Convert time value to clock cycles (platform-aware).

        Args:
            value: Time value in specified unit
            unit: Time unit ('ns', 'us', 'ms', 's')
            clock_period_ns: Platform clock period in nanoseconds
            rounding: Rounding strategy

        Returns:
            Number of clock cycles

        Raises:
            ValueError: If rounding='EXACT' and not evenly divisible
        """
        # Convert to nanoseconds
        if unit == 'ns':
            duration_ns = value
        elif unit == 'us':
            duration_ns = value * 1000
        elif unit == 'ms':
            duration_ns = value * 1_000_000
        elif unit == 's':
            duration_ns = value * 1_000_000_000
        else:
            raise ValueError(f"Invalid unit: {unit}")

        # Convert to cycles
        exact_cycles = duration_ns / clock_period_ns

        if rounding == 'EXACT':
            if exact_cycles != int(exact_cycles):
                raise ValueError(
                    f"{value}{unit} not evenly divisible by "
                    f"clock period {clock_period_ns}ns"
                )
            return int(exact_cycles)
        elif rounding == 'ROUND_UP':
            return math.ceil(exact_cycles)
        elif rounding == 'ROUND_DOWN':
            return math.floor(exact_cycles)
        else:
            raise ValueError(f"Invalid rounding mode: {rounding}")

    @staticmethod
    def cycles_to_time(
        cycles: int,
        unit: Literal['ns', 'us', 'ms', 's'],
        clock_period_ns: float
    ) -> int:
        """
        Convert clock cycles to time value (platform-aware).

        Args:
            cycles: Number of clock cycles
            unit: Desired time unit
            clock_period_ns: Platform clock period in nanoseconds

        Returns:
            Time value in specified unit
        """
        duration_ns = cycles * clock_period_ns

        if unit == 'ns':
            return int(duration_ns)
        elif unit == 'us':
            return int(duration_ns / 1000)
        elif unit == 'ms':
            return int(duration_ns / 1_000_000)
        elif unit == 's':
            return int(duration_ns / 1_000_000_000)
        else:
            raise ValueError(f"Invalid unit: {unit}")
