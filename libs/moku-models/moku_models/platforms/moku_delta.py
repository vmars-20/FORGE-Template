"""
Moku:Delta Physical Platform Model

This module defines the physical hardware characteristics of the Moku:Delta platform.
Based on official specifications and the moku library's conventions.

Key Features (Simplified 3-Slot Mode):
- 3 instrument slots (better sampling rates vs 8-slot advanced mode)
- 8 analog inputs/outputs (BNC connectors)
- 5 GHz native sampling rate (ignoring 10 GHz interpolation)
- 14-bit ADC/DAC (ignoring 20-bit blended mode)
- 2 GHz bandwidth
- 2 separate DIO headers (32 pins total)

This is the flagship Moku platform with the highest performance specifications.

Advanced Features (Not Yet Modeled):
- 8-slot Multi-Instrument Mode (lower sampling rates)
- 10 GHz DAC interpolation mode
- 20-bit ADC blending for ultra-low noise
- 100 Gb/s QSFP networking
- GPS timing reference

References:
- Datasheet: Datasheet-MokuDelta.pdf (v25-0820)
- Moku library: moku.instruments._mim.MultiInstrument
- Official specs: https://www.liquidinstruments.com/products/moku-delta/
"""

from typing import Literal
from pydantic import BaseModel, Field


class AnalogPort(BaseModel):
    """
    Physical analog I/O port (BNC connector).

    Attributes:
        port_id: Port identifier (e.g., 'IN1', 'OUT1')
        connector_type: Physical connector (always 'BNC' for Moku:Delta)
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

    The Moku:Delta has 2 separate 16-pin bidirectional DIO headers.
    Individual pins can be configured as inputs or outputs.

    Attributes:
        header_id: Header identifier (e.g., 'DIO1', 'DIO2')
        num_pins: Total number of DIO pins (16 per header)
        logic_level: Nominal logic level voltage
        voltage_tolerant: Maximum tolerated input voltage
        sample_rate_msa: Sample rate in MSa/s (same as ADC/DAC clock)
        connector_type: Physical connector type
    """
    header_id: str = Field(..., description="Header identifier (e.g., 'DIO1', 'DIO2')")
    num_pins: int = Field(default=16, description="Total number of DIO pins per header")
    logic_level: str = Field(default='3.3V', description="Nominal logic level")
    voltage_tolerant: str = Field(default='5V', description="Maximum tolerated input voltage")
    sample_rate_msa: int = Field(default=5000, description="Sample rate in MSa/s (5 GHz)")
    connector_type: str = Field(default='ribbon_cable', description="Physical connector type")


class MokuDeltaPlatform(BaseModel):
    """
    Moku:Delta Physical Platform Model (3-Slot Standard Mode).

    Represents the complete physical interface of the Moku:Delta device including:
    - 8 analog inputs/outputs (BNC connectors)
    - 2 separate digital I/O headers (32 pins total)
    - 3 Multi-instrument slots (standard mode for better sampling rates)
    - 5 GHz native sampling rate
    - 14-bit ADC/DAC resolution
    - 2 GHz bandwidth

    This is the flagship Moku platform with exceptional performance:
    - Ultra-low noise: < 10 nV/√Hz
    - Ultra-stable clock: ±1 ppb OCXO
    - Ultra-fast latency: 127 ns input to output
    - Massive storage: 1 TB internal SSD

    This model represents the SIMPLIFIED 3-slot mode, ignoring advanced features:
    - 8-slot Multi-Instrument Mode (use 3 slots for better performance)
    - 10 GHz DAC interpolation (use 5 GHz native for consistency)
    - 20-bit ADC blending (use 14-bit primary ADC)
    - 100 Gb/s QSFP networking (standard Ethernet modeled)

    Attributes:
        name: Platform name
        hardware_id: Hardware identifier (from moku library)
        ip_address: Device IP address (optional, set at runtime)
        device_name: User-assigned device name (e.g., 'MokuDelta-001')
        slots: Number of CustomWrapper instrument slots (3 in standard mode)
        analog_inputs: Physical analog input ports (BNC)
        analog_outputs: Physical analog output ports (BNC)
        dio_headers: List of 2 separate digital I/O headers
        clock_mhz: System clock frequency (5000 MHz = 5 GHz)

    Example:
        >>> moku = MokuDeltaPlatform(
        ...     ip_address='192.168.1.200',
        ...     device_name='MokuDelta-001'
        ... )
        >>> print(f"{moku.name}: {len(moku.analog_inputs)}IN/{len(moku.analog_outputs)}OUT @ {moku.clock_mhz} MHz")
        Moku:Delta: 8IN/8OUT @ 5000 MHz
    """

    # Platform identification
    name: str = Field(default='Moku:Delta', description="Platform name")
    hardware_id: str = Field(default='mokudelta', description="Hardware identifier (moku library)")
    ip_address: str | None = Field(default=None, description="Device IP address")
    device_name: str | None = Field(default=None, description="User-assigned device name")

    # Slot architecture (3-slot standard mode for better sampling rates)
    slots: int = Field(default=3, description="Number of CustomWrapper instrument slots (standard mode)")

    # Physical analog I/O (BNC connectors) - 8 inputs, 8 outputs
    analog_inputs: list[AnalogPort] = Field(
        default_factory=lambda: [
            AnalogPort(
                port_id='IN1',
                direction='input',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=40.0,  # Max range: 100mV, 1V, 10V, or 40Vpp (±20V)
                impedance='1MOhm'  # Switchable 50Ω or 1MΩ, default to 1MΩ
            ),
            AnalogPort(
                port_id='IN2',
                direction='input',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=40.0,
                impedance='1MOhm'
            ),
            AnalogPort(
                port_id='IN3',
                direction='input',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=40.0,
                impedance='1MOhm'
            ),
            AnalogPort(
                port_id='IN4',
                direction='input',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=40.0,
                impedance='1MOhm'
            ),
            AnalogPort(
                port_id='IN5',
                direction='input',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=40.0,
                impedance='1MOhm'
            ),
            AnalogPort(
                port_id='IN6',
                direction='input',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=40.0,
                impedance='1MOhm'
            ),
            AnalogPort(
                port_id='IN7',
                direction='input',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=40.0,
                impedance='1MOhm'
            ),
            AnalogPort(
                port_id='IN8',
                direction='input',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=40.0,
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
                resolution_bits=14,
                sample_rate_msa=5000,  # Native 5 GHz (ignoring 10 GHz interpolation)
                voltage_range_vpp=10.0,  # ±5V up to 100 MHz, ±500mV up to 2 GHz (use max)
                impedance='50Ohm'
            ),
            AnalogPort(
                port_id='OUT2',
                direction='output',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=10.0,
                impedance='50Ohm'
            ),
            AnalogPort(
                port_id='OUT3',
                direction='output',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=10.0,
                impedance='50Ohm'
            ),
            AnalogPort(
                port_id='OUT4',
                direction='output',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=10.0,
                impedance='50Ohm'
            ),
            AnalogPort(
                port_id='OUT5',
                direction='output',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=10.0,
                impedance='50Ohm'
            ),
            AnalogPort(
                port_id='OUT6',
                direction='output',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=10.0,
                impedance='50Ohm'
            ),
            AnalogPort(
                port_id='OUT7',
                direction='output',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=10.0,
                impedance='50Ohm'
            ),
            AnalogPort(
                port_id='OUT8',
                direction='output',
                resolution_bits=14,
                sample_rate_msa=5000,
                voltage_range_vpp=10.0,
                impedance='50Ohm'
            ),
        ],
        description="Physical analog output ports (BNC)"
    )

    # Digital I/O - 2 separate 16-pin headers (32 pins total)
    dio_headers: list[DIOPort] = Field(
        default_factory=lambda: [
            DIOPort(header_id='DIO1', num_pins=16, sample_rate_msa=5000),
            DIOPort(header_id='DIO2', num_pins=16, sample_rate_msa=5000)
        ],
        description="Digital I/O headers (2 separate 16-pin headers)"
    )

    # Clock
    clock_mhz: int = Field(default=5000, description="System clock frequency in MHz (5 GHz)")

    @property
    def clock_period_ns(self) -> float:
        """Clock period in nanoseconds."""
        return 1000.0 / self.clock_mhz

    @property
    def total_dio_pins(self) -> int:
        """Total number of DIO pins across all headers."""
        return sum(header.num_pins for header in self.dio_headers)

    def get_analog_input_by_id(self, port_id: str) -> AnalogPort | None:
        """Get analog input port by ID (e.g., 'IN1')."""
        return next((p for p in self.analog_inputs if p.port_id == port_id), None)

    def get_analog_output_by_id(self, port_id: str) -> AnalogPort | None:
        """Get analog output port by ID (e.g., 'OUT1')."""
        return next((p for p in self.analog_outputs if p.port_id == port_id), None)

    def get_dio_header_by_id(self, header_id: str) -> DIOPort | None:
        """Get DIO header by ID (e.g., 'DIO1')."""
        return next((h for h in self.dio_headers if h.header_id == header_id), None)

    def __str__(self) -> str:
        """Human-readable representation."""
        name_str = f" ({self.device_name})" if self.device_name else ""
        ip_str = f" @ {self.ip_address}" if self.ip_address else ""
        return f"{self.name}{name_str}{ip_str}: {len(self.analog_inputs)}IN/{len(self.analog_outputs)}OUT, {self.total_dio_pins}DIO"


# Convenience constant for use in configs
MOKU_DELTA_PLATFORM = MokuDeltaPlatform()
