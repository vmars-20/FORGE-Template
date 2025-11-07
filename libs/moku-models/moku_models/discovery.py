"""
Moku Device Discovery Models

Models for network device discovery and caching using zeroconf.
Supports name-based device lookup for CLI convenience.

References:
- Moku-Go CLI: Device discovery and caching implementation
- Zeroconf: _moku._tcp.local. service discovery
"""

from pydantic import BaseModel, Field
from typing import Optional


class MokuDeviceInfo(BaseModel):
    """
    Discovered Moku device information for caching.

    This model captures device metadata from network discovery (zeroconf)
    and subsequent connection attempts. Used for device name → IP resolution
    and caching recently seen devices.

    Attributes:
        ip: Device IP address
        port: Network port (typically 80)
        canonical_name: User-assigned device name (e.g., 'Lilo', 'MokuB106')
        serial_number: Device serial number (e.g., 'MG106B')
        zeroconf_name: Original zeroconf service name
        last_seen: ISO format timestamp of last discovery

    Example:
        >>> device = MokuDeviceInfo(
        ...     ip='192.168.1.100',
        ...     canonical_name='Lilo',
        ...     serial_number='MG106B',
        ...     last_seen='2025-10-24T23:30:00'
        ... )
        >>> device.to_cache_dict()
        {'ip': '192.168.1.100', 'canonical_name': 'Lilo', ...}
    """

    ip: str = Field(..., description="Device IP address")
    port: int = Field(default=80, description="Network port")
    canonical_name: Optional[str] = Field(default=None, description="User-assigned device name")
    serial_number: Optional[str] = Field(default=None, description="Device serial number")
    zeroconf_name: Optional[str] = Field(default=None, description="Zeroconf service name")
    last_seen: str = Field(..., description="ISO format timestamp of last discovery")

    def to_cache_dict(self) -> dict:
        """
        Export as dictionary for JSON cache storage.

        Returns:
            Dictionary with all fields for serialization
        """
        return self.model_dump()

    @classmethod
    def from_cache_dict(cls, data: dict) -> 'MokuDeviceInfo':
        """
        Create from cached dictionary.

        Args:
            data: Dictionary from JSON cache

        Returns:
            MokuDeviceInfo instance
        """
        return cls(**data)

    def matches_identifier(self, identifier: str) -> bool:
        """
        Check if this device matches a user-provided identifier.

        Supports matching by:
        - IP address (exact match)
        - Device name (case-insensitive)
        - Serial number (case-insensitive)

        Args:
            identifier: IP address, device name, or serial number

        Returns:
            True if identifier matches this device
        """
        # Check IP address (exact match)
        if identifier == self.ip:
            return True

        # Check canonical name (case-insensitive)
        if self.canonical_name and identifier.lower() == self.canonical_name.lower():
            return True

        # Check serial number (case-insensitive)
        if self.serial_number and identifier.lower() == self.serial_number.lower():
            return True

        return False


class MokuDeviceCache(BaseModel):
    """
    Cache of discovered Moku devices.

    Maintains a dictionary of devices keyed by IP address for fast lookup.
    Supports saving/loading from JSON file (~/.moku-deploy/device_cache.json).

    Attributes:
        devices: Dictionary mapping IP address to device info

    Example:
        >>> cache = MokuDeviceCache()
        >>> cache.add_device(MokuDeviceInfo(ip='192.168.1.100', ...))
        >>> device = cache.find_by_name('Lilo')
    """

    devices: dict[str, MokuDeviceInfo] = Field(
        default_factory=dict,
        description="Devices keyed by IP address"
    )

    def add_device(self, device: MokuDeviceInfo) -> None:
        """Add or update device in cache."""
        self.devices[device.ip] = device

    def find_by_identifier(self, identifier: str) -> Optional[MokuDeviceInfo]:
        """
        Find device by IP address, name, or serial number.

        Args:
            identifier: IP, device name, or serial number

        Returns:
            MokuDeviceInfo if found, None otherwise
        """
        for device in self.devices.values():
            if device.matches_identifier(identifier):
                return device
        return None

    def get_by_ip(self, ip: str) -> Optional[MokuDeviceInfo]:
        """Get device by IP address."""
        return self.devices.get(ip)

    def clear(self) -> None:
        """Clear all cached devices."""
        self.devices.clear()

    def to_cache_dict(self) -> dict:
        """Export as dictionary for JSON storage."""
        return {ip: device.to_cache_dict() for ip, device in self.devices.items()}

    @classmethod
    def from_cache_dict(cls, data: dict) -> 'MokuDeviceCache':
        """Load from cached dictionary."""
        devices = {ip: MokuDeviceInfo.from_cache_dict(dev_data) for ip, dev_data in data.items()}
        return cls(devices=devices)
