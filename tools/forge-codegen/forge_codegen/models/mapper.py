"""
Pydantic integration layer for BasicAppDataTypes RegisterMapper.

This module bridges the pure Python RegisterMapper (libs/basic-app-datatypes)
with the Pydantic-based CustomInstrumentApp system for YAML configuration and
integration with existing deployment workflows.

Architecture:
- BADRegisterConfig: Pydantic model for single register definition in YAML
- BADRegisterMapper: Wrapper that applies core mapping algorithm
- Integration with CustomInstrumentApp (backward compatibility)

Design References:
- Core mapper: libs/basic-app-datatypes/basic_app_datatypes/mapper.py
- Spec: docs/BasicAppDataTypes/BAD_Phase2_RegisterMapping.md
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
import json

# Core mapping algorithm (pure Python, no Pydantic)
from forge_codegen.basic_serialized_datatypes import (
    BasicAppDataTypes,
    RegisterMapper,
    RegisterMapping,
    MappingReport,
    TYPE_REGISTRY,
)

# Legacy system (for backward compatibility)
from .register import AppRegister


class BADRegisterConfig(BaseModel):
    """
    Pydantic model for BAD register configuration in YAML.

    This represents a single typed register that will be automatically
    mapped to a Control Register by the RegisterMapper.

    Attributes:
        name: User-defined variable name (e.g., "intensity", "arm_probe")
        datatype: BasicAppDataTypes enum value
        description: Human-readable description
        default_value: Optional default value (must match type constraints)

    Example YAML:
        registers:
          - name: intensity
            datatype: voltage_output_05v_s16
            description: "EMFI probe intensity control"
            default_value: 0

          - name: arm_probe
            datatype: boolean
            description: "Arm the EMFI probe"
            default_value: false
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Variable name (becomes VHDL signal)"
    )
    datatype: BasicAppDataTypes = Field(
        ...,
        description="BasicAppDataTypes enum value"
    )
    description: str = Field(
        default="",
        max_length=200,
        description="Human-readable description"
    )
    default_value: Optional[int | bool] = Field(
        default=None,
        description="Default value (must match type constraints)"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is a valid VHDL signal name."""
        # Must start with letter, contain only alphanumeric + underscore
        if not v[0].isalpha():
            raise ValueError(f"Name must start with letter: '{v}'")

        if not all(c.isalnum() or c == '_' for c in v):
            raise ValueError(f"Name must contain only alphanumeric and underscore: '{v}'")

        # VHDL reserved words (basic check)
        reserved = {'signal', 'entity', 'architecture', 'process', 'begin', 'end', 'if', 'then', 'else'}
        if v.lower() in reserved:
            raise ValueError(f"Name cannot be VHDL reserved word: '{v}'")

        return v

    @model_validator(mode='after')
    def validate_default_value(self) -> 'BADRegisterConfig':
        """Validate default_value matches datatype constraints."""
        if self.default_value is None:
            return self

        metadata = TYPE_REGISTRY[self.datatype]

        # Boolean special case
        if self.datatype == BasicAppDataTypes.BOOLEAN:
            if not isinstance(self.default_value, bool):
                raise ValueError(f"Boolean type requires bool default_value, got {type(self.default_value)}")
            return self

        # Numeric types
        if not isinstance(self.default_value, int):
            raise ValueError(f"Numeric type requires int default_value, got {type(self.default_value)}")

        # Range check
        if metadata.min_value is not None and self.default_value < metadata.min_value:
            raise ValueError(
                f"default_value {self.default_value} below min {metadata.min_value} "
                f"for type {self.datatype.value}"
            )

        if metadata.max_value is not None and self.default_value > metadata.max_value:
            raise ValueError(
                f"default_value {self.default_value} above max {metadata.max_value} "
                f"for type {self.datatype.value}"
            )

        return self


class BADRegisterMapper(BaseModel):
    """
    Pydantic wrapper for RegisterMapper with YAML integration.

    This class provides the Pydantic interface for the core RegisterMapper,
    enabling YAML-based configuration and integration with CustomInstrumentApp.

    Attributes:
        registers: List of BADRegisterConfig objects
        strategy: Packing strategy ('first_fit', 'best_fit', 'type_clustering')

    Example Usage:
        >>> from pathlib import Path
        >>> import yaml
        >>>
        >>> # Load from YAML
        >>> with open("app_config.yaml") as f:
        >>>     data = yaml.safe_load(f)
        >>>
        >>> mapper = BADRegisterMapper(**data['bad_registers'])
        >>> mappings = mapper.to_register_mappings()
        >>> report = mapper.generate_report()
        >>> print(report.to_ascii_art())
    """
    registers: List[BADRegisterConfig] = Field(
        ...,
        min_length=1,
        description="List of register configurations"
    )
    strategy: Literal["first_fit", "best_fit", "type_clustering"] = Field(
        default="best_fit",
        description="Packing strategy for register allocation"
    )

    @field_validator('registers')
    @classmethod
    def validate_unique_names(cls, v: List[BADRegisterConfig]) -> List[BADRegisterConfig]:
        """Validate all register names are unique."""
        names = [r.name for r in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate register names found: {set(duplicates)}")
        return v

    def to_register_mappings(self) -> List[RegisterMapping]:
        """
        Apply core mapping algorithm.

        Returns:
            List of RegisterMapping objects with CR assignments

        Raises:
            ValueError: If mapping fails (overflow, invalid types, etc.)
        """
        # Convert to core mapper format
        mapper = RegisterMapper()
        items = [(r.name, r.datatype) for r in self.registers]

        # Apply mapping algorithm
        return mapper.map(items, strategy=self.strategy)

    def generate_report(self) -> MappingReport:
        """
        Generate detailed mapping report.

        Returns:
            MappingReport with visualizations and statistics
        """
        mappings = self.to_register_mappings()
        mapper = RegisterMapper()
        return mapper.generate_report(mappings)

    def save_report(self, output_dir: Path, formats: Optional[List[str]] = None) -> None:
        """
        Save mapping report in multiple formats.

        Args:
            output_dir: Directory to save reports
            formats: List of formats ('ascii', 'markdown', 'vhdl', 'json')
                    If None, saves all formats
        """
        if formats is None:
            formats = ['ascii', 'markdown', 'vhdl', 'json']

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        report = self.generate_report()

        if 'ascii' in formats:
            with open(output_dir / 'mapping_report.txt', 'w') as f:
                f.write(report.to_ascii_art())

        if 'markdown' in formats:
            with open(output_dir / 'mapping_report.md', 'w') as f:
                f.write(report.to_markdown())

        if 'vhdl' in formats:
            with open(output_dir / 'mapping_comments.vhd', 'w') as f:
                f.write(report.to_vhdl_comments())

        if 'json' in formats:
            with open(output_dir / 'mapping.json', 'w') as f:
                json.dump(report.to_json(), f, indent=2)

    def to_app_registers(self) -> List[AppRegister]:
        """
        Convert to legacy AppRegister format (backward compatibility).

        This allows BAD register configs to integrate with existing
        CustomInstrumentApp deployment workflows.

        Returns:
            List of AppRegister objects (legacy format)

        Note:
            This is a compatibility shim. Future versions should use
            RegisterMapping directly for VHDL generation.
        """
        mappings = self.to_register_mappings()

        # Build lookup table: name -> mapping
        mapping_by_name = {m.name: m for m in mappings}

        # Build lookup table: name -> config
        config_by_name = {c.name: c for c in self.registers}

        app_registers = []
        for mapping in mappings:
            # Get corresponding config
            config = config_by_name[mapping.name]

            # Map BAD type to legacy RegisterType (approximate)
            from .register import RegisterType

            metadata = TYPE_REGISTRY[mapping.datatype]

            # Approximate mapping (BAD types are richer)
            if mapping.datatype == BasicAppDataTypes.BOOLEAN:
                reg_type = RegisterType.BUTTON
            elif metadata.bit_width == 8:
                reg_type = RegisterType.COUNTER_8BIT
            elif metadata.bit_width == 16:
                reg_type = RegisterType.COUNTER_16BIT
            else:
                # Fallback for non-standard widths
                reg_type = RegisterType.COUNTER_16BIT

            # Create AppRegister (legacy)
            app_reg = AppRegister(
                name=config.name,
                description=config.description or f"{mapping.datatype.value}",
                reg_type=reg_type,
                cr_number=mapping.cr_number,
                default_value=config.default_value if isinstance(config.default_value, int) else 0,
                min_value=metadata.min_value,
                max_value=metadata.max_value,
            )
            app_registers.append(app_reg)

        return app_registers

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'BADRegisterMapper':
        """
        Load BAD register mapper from YAML file.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            BADRegisterMapper instance

        Example YAML:
            bad_registers:
              strategy: best_fit
              registers:
                - name: intensity
                  datatype: voltage_output_05v_s16
                  description: "Probe intensity"
                  default_value: 0
        """
        import yaml

        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        # Extract bad_registers section
        if 'bad_registers' not in data:
            raise ValueError(f"YAML must contain 'bad_registers' section: {yaml_path}")

        return cls(**data['bad_registers'])
