"""
Moku Signal Routing Models

This module provides Pydantic models for Moku signal routing that align with
the 1st-party moku library's connection conventions while adding type safety
and validation.

The moku library uses simple dict-based connections:
    connections = [
        {'source': 'Input1', 'destination': 'Slot1InA'},
        {'source': 'Slot1OutA', 'destination': 'Output1'}
    ]

These models provide the same interface with validation.

References:
- Moku library: moku.instruments._mim.MultiInstrument.set_connections()
- Serena memory: platform_models.md (MCC routing concepts)
"""

from pydantic import BaseModel, Field, field_validator


class MokuConnection(BaseModel):
    """
    Signal routing connection within Moku platform.

    Represents a connection between two points in the Moku routing matrix.
    This can be:
    - Physical input → Slot virtual input (e.g., 'Input1' → 'Slot1InA')
    - Slot virtual output → Physical output (e.g., 'Slot1OutA' → 'Output1')
    - Slot output → Slot input (e.g., 'Slot1OutA' → 'Slot2InB')

    Port Naming Conventions (from moku library):
    - Physical inputs: 'Input1', 'Input2', 'Input3', 'Input4'
    - Physical outputs: 'Output1', 'Output2', 'Output3', 'Output4'
    - Slot virtual inputs: 'Slot1InA', 'Slot1InB', 'Slot1InC', 'Slot1InD'
    - Slot virtual outputs: 'Slot1OutA', 'Slot1OutB', 'Slot1OutC', 'Slot1OutD'
    - Alternative naming: 'InputA', 'OutputA', etc. (also valid)

    Attributes:
        source: Source port identifier
        destination: Destination port identifier

    Example:
        >>> conn = MokuConnection(source='Input1', destination='Slot1InA')
        >>> print(conn.to_dict())
        {'source': 'Input1', 'destination': 'Slot1InA'}
    """

    source: str = Field(..., description="Source port identifier")
    destination: str = Field(..., description="Destination port identifier")

    @field_validator('source', 'destination')
    @classmethod
    def validate_port_name(cls, v: str) -> str:
        """Validate port name is non-empty and properly formatted."""
        if not v or not v.strip():
            raise ValueError("Port name cannot be empty")
        return v.strip()

    def to_dict(self) -> dict[str, str]:
        """
        Export as dict compatible with moku library's set_connections() API.

        Returns:
            Dictionary with 'source' and 'destination' keys
        """
        return {'source': self.source, 'destination': self.destination}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> 'MokuConnection':
        """
        Create connection from moku library dict format.

        Args:
            data: Dictionary with 'source' and 'destination' keys

        Returns:
            MokuConnection instance
        """
        return cls(source=data['source'], destination=data['destination'])


class MokuConnectionList(BaseModel):
    """
    Collection of MokuConnections with validation and conversion utilities.

    Provides a typed wrapper around the moku library's connection list format
    with batch validation and conversion methods.

    Attributes:
        connections: List of MokuConnection objects

    Example:
        >>> conn_list = MokuConnectionList(connections=[
        ...     MokuConnection(source='Input1', destination='Slot1InA'),
        ...     MokuConnection(source='Slot1OutA', destination='Output1')
        ... ])
        >>> dict_list = conn_list.to_dict_list()  # For moku library API
    """

    connections: list[MokuConnection] = Field(
        default_factory=list,
        description="List of signal routing connections"
    )

    def to_dict_list(self) -> list[dict[str, str]]:
        """
        Convert to list of dicts for moku library's set_connections() API.

        Returns:
            List of dicts with 'source' and 'destination' keys
        """
        return [conn.to_dict() for conn in self.connections]

    @classmethod
    def from_dict_list(cls, data: list[dict[str, str]]) -> 'MokuConnectionList':
        """
        Create from moku library's connection list format.

        Args:
            data: List of dicts with 'source' and 'destination' keys

        Returns:
            MokuConnectionList instance
        """
        connections = [MokuConnection.from_dict(d) for d in data]
        return cls(connections=connections)

    def add(self, source: str, destination: str) -> None:
        """Add a new connection to the list."""
        self.connections.append(MokuConnection(source=source, destination=destination))

    def __len__(self) -> int:
        return len(self.connections)

    def __iter__(self):
        return iter(self.connections)
