"""
Riscure DS1120A EM-FI Probe Platform Model

High-power unidirectional electromagnetic fault injection probe.
Designed for integration with Moku platforms via validated signal routing.

References:
- Datasheet: DS1120A_DS1121A_datasheet.pdf
- Markdown spec: riscure_ds1120a.md
"""

from typing import Literal
from pydantic import BaseModel, Field


class SignalPort(BaseModel):
    """
    Signal port specification for Riscure probes.

    Extends the port concept from moku-models with voltage range validation.
    Compatible with moku-models AnalogPort for cross-validation.

    Attributes:
        port_id: Port identifier (e.g., 'digital_glitch', 'coil_current')
        connector_type: Physical connector (e.g., 'SMA', 'barrel_jack')
        direction: Signal direction
        voltage_min: Minimum safe operating voltage
        voltage_max: Maximum safe operating voltage
        impedance: Port impedance (e.g., '50Ohm', '1MOhm')
        coupling: Signal coupling ('DC' or 'AC')
        signal_type: Signal classification ('digital', 'analog', 'monitor', 'power')
    """
    port_id: str = Field(..., description="Port identifier")
    connector_type: str = Field(..., description="Physical connector type")
    direction: Literal['input', 'output'] = Field(..., description="Signal direction")
    voltage_min: float = Field(..., description="Minimum safe voltage (V)")
    voltage_max: float = Field(..., description="Maximum safe voltage (V)")
    impedance: str = Field(..., description="Port impedance")
    coupling: Literal['DC', 'AC'] = Field(default='DC', description="Signal coupling")
    signal_type: Literal['digital', 'analog', 'monitor', 'power'] = Field(
        ..., description="Signal classification"
    )

    def is_voltage_compatible(self, voltage: float) -> bool:
        """
        Check if a given voltage is within safe operating range.

        Args:
            voltage: Voltage to check (V)

        Returns:
            True if voltage is safe for this port
        """
        return self.voltage_min <= voltage <= self.voltage_max

    def get_voltage_range_str(self) -> str:
        """Get human-readable voltage range string."""
        return f"{self.voltage_min}V to {self.voltage_max}V"


class ProbeTip(BaseModel):
    """
    Interchangeable probe tip specification.

    Probe tips affect field strength and spatial precision but do not
    change the electrical interface.

    Attributes:
        tip_id: Tip identifier (e.g., '4mm_positive', '1.5mm_negative')
        diameter_mm: Tip diameter in millimeters
        polarity: Magnetic polarity variant
        max_current_a: Maximum coil current for this tip
    """
    tip_id: str = Field(..., description="Tip identifier")
    diameter_mm: float = Field(..., description="Tip diameter (mm)")
    polarity: Literal['positive', 'negative', 'neutral'] = Field(
        ..., description="Magnetic polarity"
    )
    max_current_a: float = Field(..., description="Maximum coil current (A)")


class DS1120APlatform(BaseModel):
    """
    Riscure DS1120A EM-FI Probe Platform Model.

    Complete electrical specification for the DS1120A high-power unidirectional
    EM-FI probe. Designed for validation against Moku platform configurations.

    Key Characteristics:
    - Fixed 50ns pulse width (not adjustable)
    - 450V, 64A capability
    - 3 signal ports (2 inputs, 1 output)
    - 1 power input (external PSU)

    Attributes:
        name: Probe model name
        vendor: Manufacturer name
        hardware_id: Hardware identifier
        signal_ports: SMA signal port specifications
        power_port: High-voltage power input specification
        available_tips: Interchangeable probe tip options
        pulse_width_ns: Fixed pulse width
        max_pulse_frequency_mhz: Maximum pulse repetition rate

    Example:
        >>> probe = DS1120APlatform()
        >>> trigger = probe.get_port_by_id('digital_glitch')
        >>> print(f"Trigger: {trigger.get_voltage_range_str()}")
        Trigger: 0.0V to 3.3V
    """

    # Platform identification
    name: str = Field(default='DS1120A', description="Probe model name")
    vendor: str = Field(default='Riscure', description="Manufacturer")
    hardware_id: str = Field(default='riscure_ds1120a', description="Hardware identifier")

    # Signal ports (SMA connectors)
    signal_ports: list[SignalPort] = Field(
        default_factory=lambda: [
            # Trigger input
            SignalPort(
                port_id='digital_glitch',
                connector_type='SMA',
                direction='input',
                voltage_min=0.0,
                voltage_max=3.3,
                impedance='50Ohm',
                coupling='DC',
                signal_type='digital'
            ),
            # Power control input
            SignalPort(
                port_id='pulse_amplitude',
                connector_type='SMA',
                direction='input',
                voltage_min=0.0,
                voltage_max=3.3,
                impedance='50Ohm',
                coupling='DC',
                signal_type='analog'
            ),
            # Current monitor output
            SignalPort(
                port_id='coil_current',
                connector_type='SMA',
                direction='output',
                voltage_min=-1.4,
                voltage_max=0.0,
                impedance='50Ohm',
                coupling='AC',
                signal_type='monitor'
            ),
        ],
        description="SMA signal port specifications"
    )

    # Power input (external PSU)
    power_port: SignalPort = Field(
        default_factory=lambda: SignalPort(
            port_id='power_24vdc',
            connector_type='barrel_jack',
            direction='input',
            voltage_min=24.0,
            voltage_max=450.0,
            impedance='N/A',
            coupling='DC',
            signal_type='power'
        ),
        description="High-voltage power input"
    )

    # Probe tips (interchangeable)
    available_tips: list[ProbeTip] = Field(
        default_factory=lambda: [
            ProbeTip(
                tip_id='1.5mm_positive',
                diameter_mm=1.5,
                polarity='positive',
                max_current_a=48.0
            ),
            ProbeTip(
                tip_id='1.5mm_negative',
                diameter_mm=1.5,
                polarity='negative',
                max_current_a=48.0
            ),
            ProbeTip(
                tip_id='4mm_positive',
                diameter_mm=4.0,
                polarity='positive',
                max_current_a=56.0
            ),
            ProbeTip(
                tip_id='4mm_negative',
                diameter_mm=4.0,
                polarity='negative',
                max_current_a=56.0
            ),
        ],
        description="Available probe tip options"
    )

    # Timing specifications
    pulse_width_ns: float = Field(default=50.0, description="Fixed pulse width (ns)")
    propagation_delay_ns: float = Field(
        default=40.0,
        description="Trigger to EM output delay (ns)"
    )
    max_pulse_frequency_mhz: float = Field(
        default=1.0,
        description="Maximum pulse repetition rate (MHz)"
    )

    def get_port_by_id(self, port_id: str) -> SignalPort | None:
        """
        Get port specification by ID.

        Args:
            port_id: Port identifier (e.g., 'digital_glitch')

        Returns:
            SignalPort if found, None otherwise
        """
        # Check signal ports
        for port in self.signal_ports:
            if port.port_id == port_id:
                return port

        # Check power port
        if self.power_port.port_id == port_id:
            return self.power_port

        return None

    def get_input_ports(self) -> list[SignalPort]:
        """Get all input ports (signal + power)."""
        inputs = [p for p in self.signal_ports if p.direction == 'input']
        inputs.append(self.power_port)
        return inputs

    def get_output_ports(self) -> list[SignalPort]:
        """Get all output ports."""
        return [p for p in self.signal_ports if p.direction == 'output']

    def get_tip_by_id(self, tip_id: str) -> ProbeTip | None:
        """Get probe tip specification by ID."""
        return next((tip for tip in self.available_tips if tip.tip_id == tip_id), None)

    def __str__(self) -> str:
        """Human-readable representation."""
        num_inputs = len(self.get_input_ports())
        num_outputs = len(self.get_output_ports())
        return f"{self.name}: {num_inputs}IN/{num_outputs}OUT, {self.pulse_width_ns}ns pulse"


# Convenience constant for use in configs
DS1120A_PLATFORM = DS1120APlatform()
