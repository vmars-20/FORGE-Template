"""
User-friendly duration classes for BasicAppDataTypes.

Provides PulseDuration_* classes that abstract time durations with
platform-aware clock cycle conversion.

Design Reference: docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md
"""

import math
from typing import Literal
from .types import BasicAppDataTypes


class PulseDuration_ns:
    """
    Nanosecond-based time duration.

    Example:
        >>> firing_duration = PulseDuration_ns(500, width=16)
        >>> firing_duration.value
        500
        >>> firing_duration.to_basic_type()
        BasicAppDataTypes.PULSE_DURATION_NS_U16
        >>>
        >>> # Convert to clock cycles (Moku:Go @ 125 MHz, 8ns period)
        >>> cycles = firing_duration.to_cycles(
        ...     clock_period_ns=8.0,
        ...     rounding='ROUND_UP'
        ... )
        >>> cycles
        63  # 500ns / 8ns = 62.5 -> 63 (rounded up)
    """

    def __init__(self, nanoseconds: int, width: Literal[8, 16, 32] = 16):
        """
        Create a nanosecond duration.

        Args:
            nanoseconds: Duration in nanoseconds
            width: Bit width for serialization (8, 16, or 32)

        Raises:
            ValueError: If nanoseconds exceeds max for chosen width
            ValueError: If nanoseconds is negative
        """
        if nanoseconds < 0:
            raise ValueError("Duration cannot be negative")

        max_value = (2 ** width) - 1
        if nanoseconds > max_value:
            raise ValueError(
                f"{nanoseconds}ns exceeds max for U{width} ({max_value}ns)"
            )

        self.value = nanoseconds
        self.unit = 'ns'
        self.width = width

    def to_basic_type(self) -> BasicAppDataTypes:
        """Convert to explicit BasicAppDataTypes enum."""
        if self.width == 8:
            return BasicAppDataTypes.PULSE_DURATION_NS_U8
        elif self.width == 16:
            return BasicAppDataTypes.PULSE_DURATION_NS_U16
        elif self.width == 32:
            return BasicAppDataTypes.PULSE_DURATION_NS_U32
        else:
            raise ValueError(f"Unsupported width: {self.width}")

    def to_nanoseconds(self) -> int:
        """Get value in nanoseconds."""
        return self.value

    def to_cycles(self, clock_period_ns: float,
                   rounding: Literal['ROUND_UP', 'ROUND_DOWN', 'EXACT']) -> int:
        """
        Convert to clock cycles for target platform.

        Args:
            clock_period_ns: Platform clock period (from platform.clock_period_ns)
            rounding: Rounding strategy (global configuration)

        Returns:
            Number of clock cycles

        Raises:
            ValueError: If rounding='EXACT' and not evenly divisible
        """
        exact_cycles = self.value / clock_period_ns

        if rounding == 'EXACT':
            if exact_cycles != int(exact_cycles):
                raise ValueError(
                    f"{self.value}ns not evenly divisible by "
                    f"clock period {clock_period_ns}ns. "
                    "Use ROUND_UP or ROUND_DOWN."
                )
            return int(exact_cycles)
        elif rounding == 'ROUND_UP':
            return math.ceil(exact_cycles)
        elif rounding == 'ROUND_DOWN':
            return math.floor(exact_cycles)
        else:
            raise ValueError(f"Invalid rounding mode: {rounding}")


class PulseDuration_us:
    """
    Microsecond-based time duration.

    Example:
        >>> duration = PulseDuration_us(100, width=16)
        >>> duration.to_nanoseconds()
        100000
        >>> cycles = duration.to_cycles(clock_period_ns=8.0, rounding='EXACT')
        >>> cycles
        12500  # 100us = 100,000ns / 8ns = 12,500 cycles
    """

    def __init__(self, microseconds: int, width: Literal[8, 16, 24] = 16):
        """
        Create a microsecond duration.

        Args:
            microseconds: Duration in microseconds
            width: Bit width for serialization (8, 16, or 24)

        Raises:
            ValueError: If microseconds exceeds max for chosen width
            ValueError: If microseconds is negative
        """
        if microseconds < 0:
            raise ValueError("Duration cannot be negative")

        max_value = (2 ** width) - 1
        if microseconds > max_value:
            raise ValueError(
                f"{microseconds}us exceeds max for U{width} ({max_value}us)"
            )

        self.value = microseconds
        self.unit = 'us'
        self.width = width

    def to_basic_type(self) -> BasicAppDataTypes:
        """Convert to explicit BasicAppDataTypes enum."""
        if self.width == 8:
            return BasicAppDataTypes.PULSE_DURATION_US_U8
        elif self.width == 16:
            return BasicAppDataTypes.PULSE_DURATION_US_U16
        elif self.width == 24:
            return BasicAppDataTypes.PULSE_DURATION_US_U24
        else:
            raise ValueError(f"Unsupported width: {self.width}")

    def to_nanoseconds(self) -> int:
        """Get value in nanoseconds."""
        return self.value * 1000

    def to_cycles(self, clock_period_ns: float,
                   rounding: Literal['ROUND_UP', 'ROUND_DOWN', 'EXACT']) -> int:
        """
        Convert to clock cycles for target platform.

        Args:
            clock_period_ns: Platform clock period (from platform.clock_period_ns)
            rounding: Rounding strategy (global configuration)

        Returns:
            Number of clock cycles

        Raises:
            ValueError: If rounding='EXACT' and not evenly divisible
        """
        duration_ns = self.to_nanoseconds()
        exact_cycles = duration_ns / clock_period_ns

        if rounding == 'EXACT':
            if exact_cycles != int(exact_cycles):
                raise ValueError(
                    f"{self.value}us not evenly divisible by "
                    f"clock period {clock_period_ns}ns. "
                    "Use ROUND_UP or ROUND_DOWN."
                )
            return int(exact_cycles)
        elif rounding == 'ROUND_UP':
            return math.ceil(exact_cycles)
        elif rounding == 'ROUND_DOWN':
            return math.floor(exact_cycles)
        else:
            raise ValueError(f"Invalid rounding mode: {rounding}")


class PulseDuration_ms:
    """
    Millisecond-based time duration.

    Example:
        >>> cooling_time = PulseDuration_ms(100, width=16)
        >>> cooling_time.to_nanoseconds()
        100000000
        >>> cycles = cooling_time.to_cycles(clock_period_ns=8.0, rounding='EXACT')
        >>> cycles
        12500000  # 100ms @ 125 MHz
    """

    def __init__(self, milliseconds: int, width: Literal[8, 16] = 16):
        """
        Create a millisecond duration.

        Args:
            milliseconds: Duration in milliseconds
            width: Bit width for serialization (8 or 16)

        Raises:
            ValueError: If milliseconds exceeds max for chosen width
            ValueError: If milliseconds is negative
        """
        if milliseconds < 0:
            raise ValueError("Duration cannot be negative")

        max_value = (2 ** width) - 1
        if milliseconds > max_value:
            raise ValueError(
                f"{milliseconds}ms exceeds max for U{width} ({max_value}ms)"
            )

        self.value = milliseconds
        self.unit = 'ms'
        self.width = width

    def to_basic_type(self) -> BasicAppDataTypes:
        """Convert to explicit BasicAppDataTypes enum."""
        if self.width == 8:
            return BasicAppDataTypes.PULSE_DURATION_MS_U8
        elif self.width == 16:
            return BasicAppDataTypes.PULSE_DURATION_MS_U16
        else:
            raise ValueError(f"Unsupported width: {self.width}")

    def to_nanoseconds(self) -> int:
        """Get value in nanoseconds."""
        return self.value * 1_000_000

    def to_cycles(self, clock_period_ns: float,
                   rounding: Literal['ROUND_UP', 'ROUND_DOWN', 'EXACT']) -> int:
        """
        Convert to clock cycles for target platform.

        Args:
            clock_period_ns: Platform clock period (from platform.clock_period_ns)
            rounding: Rounding strategy (global configuration)

        Returns:
            Number of clock cycles

        Raises:
            ValueError: If rounding='EXACT' and not evenly divisible
        """
        duration_ns = self.to_nanoseconds()
        exact_cycles = duration_ns / clock_period_ns

        if rounding == 'EXACT':
            if exact_cycles != int(exact_cycles):
                raise ValueError(
                    f"{self.value}ms not evenly divisible by "
                    f"clock period {clock_period_ns}ns. "
                    "Use ROUND_UP or ROUND_DOWN."
                )
            return int(exact_cycles)
        elif rounding == 'ROUND_UP':
            return math.ceil(exact_cycles)
        elif rounding == 'ROUND_DOWN':
            return math.floor(exact_cycles)
        else:
            raise ValueError(f"Invalid rounding mode: {rounding}")


class PulseDuration_sec:
    """
    Second-based time duration.

    Example:
        >>> timeout = PulseDuration_sec(10, width=8)
        >>> timeout.to_nanoseconds()
        10000000000
        >>> cycles = timeout.to_cycles(clock_period_ns=8.0, rounding='EXACT')
        >>> cycles
        1250000000  # 10 seconds @ 125 MHz
    """

    def __init__(self, seconds: int, width: Literal[8, 16] = 16):
        """
        Create a second duration.

        Args:
            seconds: Duration in seconds
            width: Bit width for serialization (8 or 16)

        Raises:
            ValueError: If seconds exceeds max for chosen width
            ValueError: If seconds is negative
        """
        if seconds < 0:
            raise ValueError("Duration cannot be negative")

        max_value = (2 ** width) - 1
        if seconds > max_value:
            raise ValueError(
                f"{seconds}s exceeds max for U{width} ({max_value}s)"
            )

        self.value = seconds
        self.unit = 's'
        self.width = width

    def to_basic_type(self) -> BasicAppDataTypes:
        """Convert to explicit BasicAppDataTypes enum."""
        if self.width == 8:
            return BasicAppDataTypes.PULSE_DURATION_S_U8
        elif self.width == 16:
            return BasicAppDataTypes.PULSE_DURATION_S_U16
        else:
            raise ValueError(f"Unsupported width: {self.width}")

    def to_nanoseconds(self) -> int:
        """Get value in nanoseconds."""
        return self.value * 1_000_000_000

    def to_cycles(self, clock_period_ns: float,
                   rounding: Literal['ROUND_UP', 'ROUND_DOWN', 'EXACT']) -> int:
        """
        Convert to clock cycles for target platform.

        Args:
            clock_period_ns: Platform clock period (from platform.clock_period_ns)
            rounding: Rounding strategy (global configuration)

        Returns:
            Number of clock cycles

        Raises:
            ValueError: If rounding='EXACT' and not evenly divisible
        """
        duration_ns = self.to_nanoseconds()
        exact_cycles = duration_ns / clock_period_ns

        if rounding == 'EXACT':
            if exact_cycles != int(exact_cycles):
                raise ValueError(
                    f"{self.value}s not evenly divisible by "
                    f"clock period {clock_period_ns}ns. "
                    "Use ROUND_UP or ROUND_DOWN."
                )
            return int(exact_cycles)
        elif rounding == 'ROUND_UP':
            return math.ceil(exact_cycles)
        elif rounding == 'ROUND_DOWN':
            return math.floor(exact_cycles)
        else:
            raise ValueError(f"Invalid rounding mode: {rounding}")
