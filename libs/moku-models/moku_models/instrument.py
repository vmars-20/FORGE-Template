"""
Moku Instrument Packaging Model

Simple Pydantic model for first-class 3rd party instruments.
Just enough metadata to make a VHDL module feel like a "real" instrument.

Design Goals:
- Minimal but sufficient
- Machine-readable for tooling
- Easy to create and maintain

Author: Claude Code
Date: 2025-10-24
"""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import yaml


class InstrumentManifest(BaseModel):
    """
    Instrument packaging manifest.

    Minimal metadata to turn a VHDL module into a deployable instrument.
    By definition, all instruments use CustomWrapper.

    Attributes:
        name: Instrument identifier (e.g., "pulsestar")
        display_name: Human-readable name (e.g., "PulseStar")
        description: One-line description
        author: Author/organization name
        version: Version string (e.g., "1.0.0")
        num_inputs: Number of CustomWrapper inputs used (0-4)
        num_outputs: Number of CustomWrapper outputs used (0-4)
        bitstream_path: Path to synthesized bitstream (optional)
    """

    # Basic metadata
    name: str = Field(..., description="Instrument identifier (e.g., 'pulsestar')")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="One-line description")
    author: str = Field(..., description="Author/organization")
    version: str = Field(default="1.0.0", description="Version string")

    # I/O specification
    num_inputs: int = Field(default=0, ge=0, le=4, description="Number of inputs (0-4)")
    num_outputs: int = Field(default=4, ge=0, le=4, description="Number of outputs (0-4)")

    # Build artifacts
    bitstream_path: Optional[str] = Field(None, description="Path to bitstream .tar file")

    @classmethod
    def from_yaml(cls, yaml_path: Path | str) -> 'InstrumentManifest':
        """Load manifest from YAML file."""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, yaml_path: Path | str) -> None:
        """Save manifest to YAML file."""
        with open(yaml_path, 'w') as f:
            yaml.dump(self.model_dump(exclude_none=True), f, sort_keys=False)

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.display_name} v{self.version}: {self.num_inputs}IN/{self.num_outputs}OUT"
