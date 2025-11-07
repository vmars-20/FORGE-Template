"""
Type metadata and registry for BasicAppDataTypes.

This module defines the metadata structure for all types and provides
the central TYPE_REGISTRY dictionary.

Design References:
- Voltage specs: docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md
- Time specs: docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md
"""

from dataclasses import dataclass
from typing import Optional, Union, Literal
from .types import BasicAppDataTypes


@dataclass(frozen=True)  # Immutable for safety
class TypeMetadata:
    """
    Metadata specification for a BasicAppDataType.

    The frozen=True ensures bit_width is immutable, which is critical
    for Phase 2 register packing (bit widths must be known a priori).

    Attributes:
        type_name: BasicAppDataTypes enum value
        bit_width: Fixed bit width (immutable)
        vhdl_type: VHDL type string (e.g., "signed(15 downto 0)")
        python_type: Python type (int, bool)
        min_value: Minimum allowed value (None for boolean)
        max_value: Maximum allowed value (None for boolean)
        default_value: Default value for this type
        direction: 'input', 'output', or None (for time/boolean)
        signedness: 'signed', 'unsigned', or None (for boolean)
        unit: Unit string ('mV', 'ns', 'us', 'ms', 's', None)
    """
    type_name: BasicAppDataTypes
    bit_width: int
    vhdl_type: str
    python_type: type
    min_value: Optional[int]
    max_value: Optional[int]
    default_value: Union[int, bool]
    direction: Optional[Literal['input', 'output']] = None
    signedness: Optional[Literal['signed', 'unsigned']] = None
    unit: Optional[str] = None


# ============================================================================
# TYPE_REGISTRY - Central metadata for all 25 types
# ============================================================================

TYPE_REGISTRY: dict[BasicAppDataTypes, TypeMetadata] = {
    # ========================================================================
    # VOLTAGE OUTPUT TYPES (+-5V, all platforms)
    # See: VOLTAGE_TYPE_SYSTEM.md
    # ========================================================================
    BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S8: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S8,
        bit_width=8,
        vhdl_type="signed(7 downto 0)",
        python_type=int,
        min_value=-5000,  # -5V in mV
        max_value=5000,   # +5V in mV
        default_value=0,
        direction='output',
        signedness='signed',
        unit='mV'
    ),
    BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
        bit_width=16,
        vhdl_type="signed(15 downto 0)",
        python_type=int,
        min_value=-5000,  # -5V in mV
        max_value=5000,   # +5V in mV
        default_value=0,
        direction='output',
        signedness='signed',
        unit='mV'
    ),
    BasicAppDataTypes.VOLTAGE_OUTPUT_05V_U7: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_U7,
        bit_width=7,
        vhdl_type="unsigned(6 downto 0)",
        python_type=int,
        min_value=0,      # 0V in mV
        max_value=5000,   # +5V in mV
        default_value=0,
        direction='output',
        signedness='unsigned',
        unit='mV'
    ),
    BasicAppDataTypes.VOLTAGE_OUTPUT_05V_U15: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_U15,
        bit_width=15,
        vhdl_type="unsigned(14 downto 0)",
        python_type=int,
        min_value=0,      # 0V in mV
        max_value=5000,   # +5V in mV
        default_value=0,
        direction='output',
        signedness='unsigned',
        unit='mV'
    ),

    # ========================================================================
    # VOLTAGE INPUT TYPES (+-20V, Moku:Delta)
    # See: VOLTAGE_TYPE_SYSTEM.md
    # ========================================================================
    BasicAppDataTypes.VOLTAGE_INPUT_20V_S8: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_INPUT_20V_S8,
        bit_width=8,
        vhdl_type="signed(7 downto 0)",
        python_type=int,
        min_value=-20000,  # -20V in mV
        max_value=20000,   # +20V in mV
        default_value=0,
        direction='input',
        signedness='signed',
        unit='mV'
    ),
    BasicAppDataTypes.VOLTAGE_INPUT_20V_S16: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_INPUT_20V_S16,
        bit_width=16,
        vhdl_type="signed(15 downto 0)",
        python_type=int,
        min_value=-20000,  # -20V in mV
        max_value=20000,   # +20V in mV
        default_value=0,
        direction='input',
        signedness='signed',
        unit='mV'
    ),
    BasicAppDataTypes.VOLTAGE_INPUT_20V_U7: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_INPUT_20V_U7,
        bit_width=7,
        vhdl_type="unsigned(6 downto 0)",
        python_type=int,
        min_value=0,       # 0V in mV
        max_value=20000,   # +20V in mV
        default_value=0,
        direction='input',
        signedness='unsigned',
        unit='mV'
    ),
    BasicAppDataTypes.VOLTAGE_INPUT_20V_U15: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_INPUT_20V_U15,
        bit_width=15,
        vhdl_type="unsigned(14 downto 0)",
        python_type=int,
        min_value=0,       # 0V in mV
        max_value=20000,   # +20V in mV
        default_value=0,
        direction='input',
        signedness='unsigned',
        unit='mV'
    ),

    # ========================================================================
    # VOLTAGE INPUT TYPES (+-25V, Go/Lab/Pro)
    # See: VOLTAGE_TYPE_SYSTEM.md
    # ========================================================================
    BasicAppDataTypes.VOLTAGE_INPUT_25V_S8: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_INPUT_25V_S8,
        bit_width=8,
        vhdl_type="signed(7 downto 0)",
        python_type=int,
        min_value=-25000,  # -25V in mV
        max_value=25000,   # +25V in mV
        default_value=0,
        direction='input',
        signedness='signed',
        unit='mV'
    ),
    BasicAppDataTypes.VOLTAGE_INPUT_25V_S16: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_INPUT_25V_S16,
        bit_width=16,
        vhdl_type="signed(15 downto 0)",
        python_type=int,
        min_value=-25000,  # -25V in mV
        max_value=25000,   # +25V in mV
        default_value=0,
        direction='input',
        signedness='signed',
        unit='mV'
    ),
    BasicAppDataTypes.VOLTAGE_INPUT_25V_U7: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_INPUT_25V_U7,
        bit_width=7,
        vhdl_type="unsigned(6 downto 0)",
        python_type=int,
        min_value=0,       # 0V in mV
        max_value=25000,   # +25V in mV
        default_value=0,
        direction='input',
        signedness='unsigned',
        unit='mV'
    ),
    BasicAppDataTypes.VOLTAGE_INPUT_25V_U15: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_INPUT_25V_U15,
        bit_width=15,
        vhdl_type="unsigned(14 downto 0)",
        python_type=int,
        min_value=0,       # 0V in mV
        max_value=25000,   # +25V in mV
        default_value=0,
        direction='input',
        signedness='unsigned',
        unit='mV'
    ),

    # ========================================================================
    # TIME TYPES (nanoseconds)
    # See: TIME_TYPE_SYSTEM.md
    # ========================================================================
    BasicAppDataTypes.PULSE_DURATION_NS_U8: TypeMetadata(
        type_name=BasicAppDataTypes.PULSE_DURATION_NS_U8,
        bit_width=8,
        vhdl_type="unsigned(7 downto 0)",
        python_type=int,
        min_value=0,
        max_value=255,  # nanoseconds
        default_value=0,
        direction=None,
        signedness='unsigned',
        unit='ns'
    ),
    BasicAppDataTypes.PULSE_DURATION_NS_U16: TypeMetadata(
        type_name=BasicAppDataTypes.PULSE_DURATION_NS_U16,
        bit_width=16,
        vhdl_type="unsigned(15 downto 0)",
        python_type=int,
        min_value=0,
        max_value=65535,  # nanoseconds
        default_value=0,
        direction=None,
        signedness='unsigned',
        unit='ns'
    ),
    BasicAppDataTypes.PULSE_DURATION_NS_U32: TypeMetadata(
        type_name=BasicAppDataTypes.PULSE_DURATION_NS_U32,
        bit_width=32,
        vhdl_type="unsigned(31 downto 0)",
        python_type=int,
        min_value=0,
        max_value=4294967295,  # nanoseconds (~4.29 sec)
        default_value=0,
        direction=None,
        signedness='unsigned',
        unit='ns'
    ),

    # ========================================================================
    # TIME TYPES (microseconds)
    # See: TIME_TYPE_SYSTEM.md
    # ========================================================================
    BasicAppDataTypes.PULSE_DURATION_US_U8: TypeMetadata(
        type_name=BasicAppDataTypes.PULSE_DURATION_US_U8,
        bit_width=8,
        vhdl_type="unsigned(7 downto 0)",
        python_type=int,
        min_value=0,
        max_value=255,  # microseconds
        default_value=0,
        direction=None,
        signedness='unsigned',
        unit='us'
    ),
    BasicAppDataTypes.PULSE_DURATION_US_U16: TypeMetadata(
        type_name=BasicAppDataTypes.PULSE_DURATION_US_U16,
        bit_width=16,
        vhdl_type="unsigned(15 downto 0)",
        python_type=int,
        min_value=0,
        max_value=65535,  # microseconds
        default_value=0,
        direction=None,
        signedness='unsigned',
        unit='us'
    ),
    BasicAppDataTypes.PULSE_DURATION_US_U24: TypeMetadata(
        type_name=BasicAppDataTypes.PULSE_DURATION_US_U24,
        bit_width=24,
        vhdl_type="unsigned(23 downto 0)",
        python_type=int,
        min_value=0,
        max_value=16777215,  # microseconds (~16.7 sec)
        default_value=0,
        direction=None,
        signedness='unsigned',
        unit='us'
    ),

    # ========================================================================
    # TIME TYPES (milliseconds)
    # See: TIME_TYPE_SYSTEM.md
    # ========================================================================
    BasicAppDataTypes.PULSE_DURATION_MS_U8: TypeMetadata(
        type_name=BasicAppDataTypes.PULSE_DURATION_MS_U8,
        bit_width=8,
        vhdl_type="unsigned(7 downto 0)",
        python_type=int,
        min_value=0,
        max_value=255,  # milliseconds
        default_value=0,
        direction=None,
        signedness='unsigned',
        unit='ms'
    ),
    BasicAppDataTypes.PULSE_DURATION_MS_U16: TypeMetadata(
        type_name=BasicAppDataTypes.PULSE_DURATION_MS_U16,
        bit_width=16,
        vhdl_type="unsigned(15 downto 0)",
        python_type=int,
        min_value=0,
        max_value=65535,  # milliseconds (~65 sec)
        default_value=0,
        direction=None,
        signedness='unsigned',
        unit='ms'
    ),

    # ========================================================================
    # TIME TYPES (seconds)
    # See: TIME_TYPE_SYSTEM.md
    # ========================================================================
    BasicAppDataTypes.PULSE_DURATION_S_U8: TypeMetadata(
        type_name=BasicAppDataTypes.PULSE_DURATION_S_U8,
        bit_width=8,
        vhdl_type="unsigned(7 downto 0)",
        python_type=int,
        min_value=0,
        max_value=255,  # seconds
        default_value=0,
        direction=None,
        signedness='unsigned',
        unit='s'
    ),
    BasicAppDataTypes.PULSE_DURATION_S_U16: TypeMetadata(
        type_name=BasicAppDataTypes.PULSE_DURATION_S_U16,
        bit_width=16,
        vhdl_type="unsigned(15 downto 0)",
        python_type=int,
        min_value=0,
        max_value=65535,  # seconds (~18 hours)
        default_value=0,
        direction=None,
        signedness='unsigned',
        unit='s'
    ),

    # ========================================================================
    # BOOLEAN TYPE
    # ========================================================================
    BasicAppDataTypes.BOOLEAN: TypeMetadata(
        type_name=BasicAppDataTypes.BOOLEAN,
        bit_width=1,
        vhdl_type="std_logic",
        python_type=bool,
        min_value=None,
        max_value=None,
        default_value=False,
        direction=None,
        signedness=None,
        unit=None
    ),
}
