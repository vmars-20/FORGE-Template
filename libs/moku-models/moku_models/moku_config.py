"""
MokuConfig - THE Core Deployment Abstraction

Single source of truth for Moku MultiInstrument deployment specifications.
Works for BOTH simulation (behavioral models) and hardware (real Moku).

This is the central Python abstraction for the entire project.
"""

from typing import Any
from pydantic import BaseModel, Field, field_validator
from moku_models.platforms.moku_go import MokuGoPlatform
from moku_models.routing import MokuConnection


class SlotConfig(BaseModel):
    """
    Configuration for a single instrument slot.

    Attributes:
        instrument: Instrument type name (e.g., 'CloudCompile', 'Oscilloscope')
        settings: Instrument-specific settings dictionary
        control_registers: Optional register values for CloudCompile slots
        bitstream: Optional bitstream path for CloudCompile slots
    """
    instrument: str = Field(..., description="Instrument type name")
    settings: dict[str, Any] = Field(default_factory=dict, description="Instrument-specific settings")
    control_registers: dict[int, int] | None = Field(default=None, description="Control register values (CloudCompile)")
    bitstream: str | None = Field(default=None, description="Bitstream path (CloudCompile)")

    @field_validator('instrument')
    @classmethod
    def validate_instrument_name(cls, v: str) -> str:
        """Validate instrument name is non-empty."""
        if not v or not v.strip():
            raise ValueError("Instrument name cannot be empty")
        return v.strip()


class MokuConfig(BaseModel):
    """
    THE core deployment abstraction for Moku platform.

    This is the single source of truth for multi-instrument deployment specifications.
    It bridges VHDL hardware, CocotB simulation, and real Moku device deployment.

    Specifies which instruments to deploy to which slots and how to route
    signals between them. Works for BOTH simulation and hardware backends.

    Simulation: Creates behavioral instrument models in CocotB
    Hardware: Deploys to real Moku device via MCC API

    Attributes:
        platform: Moku platform model (Go, Lab, Pro, etc.)
        slots: Slot configurations (slot number → SlotConfig)
        routing: MCC signal routing between slots/ports
        metadata: Optional metadata (test campaign, version, etc.)

    Example:
        >>> config = MokuConfig(
        ...     platform=MOKU_GO_PLATFORM,
        ...     slots={
        ...         1: SlotConfig(instrument='CloudCompile', bitstream='emfi_seq.bit'),
        ...         2: SlotConfig(instrument='Oscilloscope', settings={'sample_rate': 1e6})
        ...     },
        ...     routing=[
        ...         MokuConnection(source='Input1', destination='Slot1InA'),
        ...         MokuConnection(source='Slot1OutA', destination='Slot2InA')
        ...     ]
        ... )
    """

    platform: MokuGoPlatform = Field(..., description="Moku platform specification")
    slots: dict[int, SlotConfig] = Field(..., description="Slot configurations")
    routing: list[MokuConnection] = Field(default_factory=list, description="MCC signal routing")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional metadata")

    @field_validator('slots')
    @classmethod
    def validate_slots(cls, v: dict[int, SlotConfig], info) -> dict[int, SlotConfig]:
        """Validate slot numbers are within platform limits."""
        if not v:
            raise ValueError("At least one slot must be configured")

        platform = info.data.get('platform')
        if platform:
            max_slots = platform.slots
            for slot_num in v.keys():
                if slot_num < 1 or slot_num > max_slots:
                    raise ValueError(f"Slot {slot_num} out of range for platform (1-{max_slots})")

        return v

    def validate_routing(self) -> list[str]:
        """
        Validate all routing connections reference valid ports.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Build list of valid port names
        valid_ports = set()

        # Add platform physical ports
        for inp in self.platform.analog_inputs:
            valid_ports.add(inp.port_id)  # IN1, IN2
        for out in self.platform.analog_outputs:
            valid_ports.add(out.port_id)  # OUT1, OUT2

        # Add slot virtual ports (SlotNInA, SlotNOutA, etc.)
        for slot_num in self.slots.keys():
            for port_type in ['InA', 'InB', 'InC', 'InD', 'OutA', 'OutB', 'OutC', 'OutD']:
                valid_ports.add(f'Slot{slot_num}{port_type}')

        # Validate each connection
        for idx, conn in enumerate(self.routing):
            if conn.source not in valid_ports:
                errors.append(f"Connection {idx}: Invalid source port '{conn.source}'")
            if conn.destination not in valid_ports:
                errors.append(f"Connection {idx}: Invalid destination port '{conn.destination}'")

        return errors

    def get_slot(self, slot_num: int) -> SlotConfig | None:
        """Get configuration for specific slot number."""
        return self.slots.get(slot_num)

    def get_instrument_slots(self, instrument_type: str) -> list[int]:
        """Get list of slot numbers containing specified instrument type."""
        return [
            slot_num
            for slot_num, config in self.slots.items()
            if config.instrument == instrument_type
        ]

    def to_dict(self) -> dict:
        """Export configuration as dictionary for serialization."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'MokuConfig':
        """Create configuration from dictionary."""
        return cls(**data)


# Backward compatibility alias (deprecated - use MokuConfig)
MokuPlatformConfig = MokuConfig
