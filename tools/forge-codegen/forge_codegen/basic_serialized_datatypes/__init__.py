"""
BasicAppDataTypes - Type-safe data serialization for Moku FPGA applications.

Provides fixed-width types with platform-aware serialization:
- Voltage types (INPUT/OUTPUT, range-specific)
- Time/duration types (user-friendly units -> clock cycles)
- Boolean type

Design Documentation:
- Voltage specs: docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md
- Time specs: docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md
- Implementation: docs/BasicAppDataTypes/BAD_Phase1_Implementation_Plan.md

Example:
    >>> from models.custom_inst.datatypes import PulseDuration_ns, BasicAppDataTypes
    >>>
    >>> # User-friendly API
    >>> firing_duration = PulseDuration_ns(500, width=16)
    >>>
    >>> # Get type enum
    >>> type_enum = firing_duration.to_basic_type()
    >>> # Returns: BasicAppDataTypes.PULSE_DURATION_NS_U16
    >>>
    >>> # Convert to platform-specific cycles
    >>> cycles = firing_duration.to_cycles(
    ...     clock_period_ns=8.0,  # Moku:Go @ 125 MHz
    ...     rounding='ROUND_UP'
    ... )
    >>> # Returns: 63 cycles (500ns / 8ns = 62.5 -> 63)
"""

# Core types and metadata
from .types import BasicAppDataTypes
from .metadata import TypeMetadata, TYPE_REGISTRY

# User-friendly duration classes
from .time import (
    PulseDuration_ns,
    PulseDuration_us,
    PulseDuration_ms,
    PulseDuration_sec,
)

# Conversion utilities
from .converters import TypeConverter

# Register mapping (Phase 2)
from .mapper import RegisterMapper, RegisterMapping, MappingReport

__all__ = [
    # Enums and metadata
    'BasicAppDataTypes',
    'TypeMetadata',
    'TYPE_REGISTRY',

    # Duration classes
    'PulseDuration_ns',
    'PulseDuration_us',
    'PulseDuration_ms',
    'PulseDuration_sec',

    # Converters
    'TypeConverter',

    # Register mapping (Phase 2)
    'RegisterMapper',
    'RegisterMapping',
    'MappingReport',
]

__version__ = '1.0.0'
