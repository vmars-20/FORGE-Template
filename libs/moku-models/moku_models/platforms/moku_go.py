"""
Moku:Go Physical Platform Model

This module defines the physical hardware characteristics of the Moku:Go platform.
Based on official specifications and the moku library's conventions.

References:
- Serena memory: platform_models.md
- Moku library: moku.instruments._mim.MultiInstrument
"""

from typing import Literal
from pydantic import BaseModel, Field


class AnalogPort(BaseModel):
    """
    Physical analog I/O port (BNC connector).

    Attributes:
        port_id: Port identifier (e.g., 'IN1', 'OUT1')
        connector_type: Physical connector (always 'BNC' for Moku:Go)
        direction: Signal direction
        resolution_bits: ADC/DAC bit depth
        sample_rate_msa: Sample rate in MSa/s
        voltage_range_vpp: Peak-to-peak voltage range
        impedance: Input impedance
    """
    port_id: str = Field(..., description="Port identifier (e.g., 'IN1', 'OUT1')")
    connector_type: Literal['BNC'] = Field(default='BNC', description="Physical connector type")
    direction: Literal['input', 'output'] = Field(..., description="Signal direction")
    resolution_bits: int = Field(..., description="ADC/DAC bit depth")
    sample_rate_msa: int = Field(..., description="Sample rate in MSa/s")
    voltage_range_vpp: float = Field(..., description="Peak-to-peak voltage range in volts")
    impedance: str = Field(..., description="Input impedance (e.g., '50Ohm', '1MOhm')")


class DIOPort(BaseModel):
    """
    Digital I/O header specification.

    The Moku:Go has a 16-pin bidirectional DIO header accessible via ribbon cable.
    Individual pins can be configured as inputs or outputs.

    Attributes:
        num_pins: Total number of DIO pins (16 for Moku:Go)
        logic_level: Nominal logic level voltage
        voltage_tolerant: Maximum tolerated input voltage
        sample_rate_msa: Sample rate in MSa/s (same as ADC/DAC clock)
        connector_type: Physical connector type
    """
    num_pins: int = Field(default=16, description="Total number of DIO pins")
    logic_level: str = Field(default='3.3V', description="Nominal logic level")
    voltage_tolerant: str = Field(default='5V', description="Maximum tolerated input voltage")
    sample_rate_msa: int = Field(default=125, description="Sample rate in MSa/s")
    connector_type: str = Field(default='ribbon_cable', description="Physical connector type")


class MokuGoPlatform(BaseModel):
    """
    Moku:Go Physical Platform Model.

    Represents the complete physical interface of the Moku:Go device including:
    - Analog inputs/outputs (BNC connectors)
    - Digital I/O header (16 pins)
    - Multi-instrument slot architecture
    - Electrical characteristics

    This model captures the PHYSICAL hardware layer, independent of MCC routing
    or CustomWrapper virtual I/O abstraction.

    Attributes:
        name: Platform name
        hardware_id: Hardware identifier (from moku library)
        ip_address: Device IP address (optional, set at runtime)
        device_name: User-assigned device name (e.g., 'MokuB106')
        slots: Number of CustomWrapper instrument slots
        analog_inputs: Physical analog input ports (BNC)
        analog_outputs: Physical analog output ports (BNC)
        dio: Digital I/O header specification
        clock_mhz: System clock frequency

    Example:
        >>> moku = MokuGoPlatform(
        ...     ip_address='192.168.73.1',
        ...     device_name='MokuB106'
        ... )
        >>> print(f"{moku.name}: {len(moku.analog_inputs)} analog inputs")
        Moku:Go: 2 analog inputs
    """

    # Platform identification
    name: str = Field(default='Moku:Go', description="Platform name")
    hardware_id: str = Field(default='mokugo', description="Hardware identifier (moku library)")
    ip_address: str | None = Field(default=None, description="Device IP address")
    device_name: str | None = Field(default=None, description="User-assigned device name")

    # Slot architecture
    slots: int = Field(default=2, description="Number of CustomWrapper instrument slots")

    # Physical analog I/O (BNC connectors)
    analog_inputs: list[AnalogPort] = Field(
        default_factory=lambda: [
            AnalogPort(
                port_id='IN1',
                direction='input',
                resolution_bits=12,
                sample_rate_msa=125,
                voltage_range_vpp=50.0,  # ±25V range
                impedance='1MOhm'
            ),
            AnalogPort(
                port_id='IN2',
                direction='input',
                resolution_bits=12,
                sample_rate_msa=125,
                voltage_range_vpp=50.0,
                impedance='1MOhm'
            ),
        ],
        description="Physical analog input ports (BNC)"
    )

    analog_outputs: list[AnalogPort] = Field(
        default_factory=lambda: [
            AnalogPort(
                port_id='OUT1',
                direction='output',
                resolution_bits=12,
                sample_rate_msa=125,
                voltage_range_vpp=10.0,  # ±5V range
                impedance='50Ohm'
            ),
            AnalogPort(
                port_id='OUT2',
                direction='output',
                resolution_bits=12,
                sample_rate_msa=125,
                voltage_range_vpp=10.0,
                impedance='50Ohm'
            ),
        ],
        description="Physical analog output ports (BNC)"
    )

    # Digital I/O
    dio: DIOPort = Field(
        default_factory=DIOPort,
        description="Digital I/O header specification"
    )

    # Clock
    clock_mhz: int = Field(default=125, description="System clock frequency in MHz")

    @property
    def clock_period_ns(self) -> float:
        """Clock period in nanoseconds."""
        return 1000.0 / self.clock_mhz

    def get_analog_input_by_id(self, port_id: str) -> AnalogPort | None:
        """Get analog input port by ID (e.g., 'IN1')."""
        return next((p for p in self.analog_inputs if p.port_id == port_id), None)

    def get_analog_output_by_id(self, port_id: str) -> AnalogPort | None:
        """Get analog output port by ID (e.g., 'OUT1')."""
        return next((p for p in self.analog_outputs if p.port_id == port_id), None)

    def __str__(self) -> str:
        """Human-readable representation."""
        name_str = f" ({self.device_name})" if self.device_name else ""
        ip_str = f" @ {self.ip_address}" if self.ip_address else ""
        return f"{self.name}{name_str}{ip_str}: {len(self.analog_inputs)}IN/{len(self.analog_outputs)}OUT, {self.dio.num_pins}DIO"


# Convenience constant for use in tests/configs
MOKU_GO_PLATFORM = MokuGoPlatform()
