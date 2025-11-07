"""
Register interface package for BasicAppDataTypes.

Provides type-safe register interface specification with:
- DataTypeSpec: Rich type definition with UI metadata
- BasicAppsRegPackage: Complete register interface container
- Integration with Phase 2 mapper (BADRegisterMapper)
- Export to MokuConfig.control_registers format

Design:
- Platform-agnostic (no bitstream paths, no MCC routing)
- Focused on register interface only
- Integrates with moku-models via to_control_registers()
"""

from typing import List, Optional, Literal, Union
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, PrivateAttr
import yaml

from forge_codegen.basic_serialized_datatypes import (
    BasicAppDataTypes,
    TYPE_REGISTRY,
    RegisterMapper,
    RegisterMapping,
    TypeConverter,
)
from .mapper import BADRegisterMapper, BADRegisterConfig


class DataTypeSpec(BaseModel):
    """
    Rich specification for a single register data element.

    Extends BADRegisterConfig with UI metadata for TUI/GUI generation.

    Attributes:
        name: User-defined variable name (e.g., "intensity", "arm_probe")
        datatype: BasicAppDataTypes enum value
        description: Human-readable description
        default_value: Optional default value (must match type constraints)

        # UI metadata (Phase 3 addition)
        min_value: Minimum allowed value (for sliders, validation)
        max_value: Maximum allowed value (for sliders, validation)
        display_name: Human-friendly name for UI (e.g., "Intensity (mV)")
        units: Physical units (e.g., "mV", "ms", "ns")

    Example:
        >>> dt = DataTypeSpec(
        ...     name="intensity",
        ...     datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
        ...     description="Output intensity voltage",
        ...     default_value=2400,  # mV
        ...     min_value=0,
        ...     max_value=5000,
        ...     display_name="Intensity",
        ...     units="mV"
        ... )
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
    default_value: Optional[Union[int, bool]] = Field(
        default=None,
        description="Default value (must match type constraints)"
    )

    # UI metadata (all optional)
    min_value: Optional[Union[int, float]] = Field(
        default=None,
        description="Minimum allowed value (for UI sliders/validation)"
    )
    max_value: Optional[Union[int, float]] = Field(
        default=None,
        description="Maximum allowed value (for UI sliders/validation)"
    )
    display_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Human-friendly display name for UI"
    )
    units: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Physical units (e.g., 'mV', 'ms', 'ns')"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is VHDL-safe."""
        # Must start with letter
        if not v[0].isalpha():
            raise ValueError(f"Name must start with letter: '{v}'")

        # Only alphanumeric + underscore
        if not all(c.isalnum() or c == '_' for c in v):
            raise ValueError(f"Name must contain only alphanumeric and underscore: '{v}'")

        # VHDL reserved words (basic check)
        reserved = {
            'signal', 'entity', 'architecture', 'process', 'begin', 'end',
            'if', 'then', 'else', 'loop', 'for', 'while', 'case', 'when'
        }
        if v.lower() in reserved:
            raise ValueError(f"Name cannot be VHDL reserved word: '{v}'")

        return v

    @model_validator(mode='after')
    def validate_default_value(self) -> 'DataTypeSpec':
        """Validate default_value matches datatype constraints."""
        if self.default_value is None:
            return self

        metadata = TYPE_REGISTRY[self.datatype]

        # Boolean special case
        if self.datatype == BasicAppDataTypes.BOOLEAN:
            if not isinstance(self.default_value, bool):
                raise ValueError(
                    f"Boolean type requires bool default_value, got {type(self.default_value)}"
                )
            return self

        # Numeric types
        if not isinstance(self.default_value, int):
            raise ValueError(
                f"Numeric type requires int default_value, got {type(self.default_value)}"
            )

        # Range check (use TYPE_REGISTRY)
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

    @model_validator(mode='after')
    def validate_min_max_range(self) -> 'DataTypeSpec':
        """Validate min_value <= max_value and within type limits."""
        metadata = TYPE_REGISTRY[self.datatype]

        # Check min_value <= max_value
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(
                    f"min_value ({self.min_value}) cannot be greater than "
                    f"max_value ({self.max_value})"
                )

        # Strict validation: UI constraints must be within type limits
        if self.min_value is not None and metadata.min_value is not None:
            if self.min_value < metadata.min_value:
                raise ValueError(
                    f"min_value ({self.min_value}) below type minimum "
                    f"({metadata.min_value}) for {self.datatype.value}"
                )

        if self.max_value is not None and metadata.max_value is not None:
            if self.max_value > metadata.max_value:
                raise ValueError(
                    f"max_value ({self.max_value}) above type maximum "
                    f"({metadata.max_value}) for {self.datatype.value}"
                )

        return self

    def get_bit_width(self) -> int:
        """Get bit width from type registry."""
        return TYPE_REGISTRY[self.datatype].bit_width

    def to_bad_register_config(self) -> BADRegisterConfig:
        """Convert to Phase 2 BADRegisterConfig (for mapper integration)."""
        return BADRegisterConfig(
            name=self.name,
            datatype=self.datatype,
            description=self.description,
            default_value=self.default_value
        )


class BasicAppsRegPackage(BaseModel):
    """
    Complete register interface specification for CustomInstrument applications.

    This is the single source of truth for application register interfaces.
    Platform-agnostic - does not include bitstream paths, MCC routing, or
    platform-specific configuration (those are handled by moku-models).

    Attributes:
        app_name: Application name (e.g., "DS1140_PD")
        description: Human-readable description
        datatypes: List of DataTypeSpec objects
        mapping_strategy: Packing strategy for register allocation

    Integration:
        - Uses BADRegisterMapper (Phase 2) for actual mapping
        - Exports to MokuConfig.control_registers via to_control_registers()

    Example:
        >>> package = BasicAppsRegPackage(
        ...     app_name="DS1140_PD",
        ...     description="EMFI probe driver",
        ...     datatypes=[
        ...         DataTypeSpec(name="arm_probe", datatype=BasicAppDataTypes.BOOLEAN),
        ...         DataTypeSpec(name="intensity", datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
        ...     ],
        ...     mapping_strategy="best_fit"
        ... )
        >>>
        >>> # Generate mapping
        >>> mappings = package.generate_mapping()
        >>>
        >>> # Export to MokuConfig format
        >>> control_regs = package.to_control_registers()
        >>> # Returns: {6: 0x00000000, 7: 0x09600000, ...}
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Package identity
    app_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Application name"
    )
    description: str = Field(
        default="",
        max_length=500,
        description="Human-readable description"
    )

    # Register interface
    datatypes: List[DataTypeSpec] = Field(
        ...,
        min_length=1,
        description="List of register data type specifications"
    )
    mapping_strategy: Literal["first_fit", "best_fit", "type_clustering"] = Field(
        default="best_fit",
        description="Register packing strategy"
    )

    # Internal cache (not serialized) - use PrivateAttr for Pydantic v2
    _mapping_cache: Optional[List[RegisterMapping]] = PrivateAttr(default=None)

    @field_validator('datatypes')
    @classmethod
    def validate_unique_names(cls, v: List[DataTypeSpec]) -> List[DataTypeSpec]:
        """Validate all datatype names are unique."""
        names = [dt.name for dt in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate datatype names found: {set(duplicates)}")
        return v

    @model_validator(mode='after')
    def validate_total_bits(self) -> 'BasicAppsRegPackage':
        """Validate total bits fit in 384-bit limit (12 registers × 32 bits)."""
        total_bits = sum(dt.get_bit_width() for dt in self.datatypes)
        if total_bits > 384:
            raise ValueError(
                f"Total bits ({total_bits}) exceeds 384-bit limit "
                f"(12 registers × 32 bits)"
            )
        return self

    def generate_mapping(self) -> List[RegisterMapping]:
        """
        Generate register mapping using Phase 2 mapper.

        Returns:
            List of RegisterMapping objects with CR assignments

        Caches result to avoid recomputation.
        """
        if self._mapping_cache is None:
            # Convert to BADRegisterMapper format
            mapper = BADRegisterMapper(
                registers=[dt.to_bad_register_config() for dt in self.datatypes],
                strategy=self.mapping_strategy
            )
            self._mapping_cache = mapper.to_register_mappings()

        return self._mapping_cache

    def _convert_to_raw(self, dt_spec: DataTypeSpec) -> int:
        """
        Convert typed value to raw bits based on datatype category.

        This dispatcher routes to appropriate conversion methods since
        TypeConverter doesn't have a generic to_raw() method.

        Args:
            dt_spec: DataTypeSpec with default_value to convert

        Returns:
            Raw integer value for register packing
        """
        if dt_spec.default_value is None:
            return 0

        # Boolean: direct conversion
        if dt_spec.datatype == BasicAppDataTypes.BOOLEAN:
            return 1 if dt_spec.default_value else 0

        # Voltage types: use TypeConverter with specific method
        if dt_spec.datatype.value.startswith('voltage_'):
            method_name = f"{dt_spec.datatype.value}_to_raw"
            converter_method = getattr(TypeConverter, method_name)
            return converter_method(dt_spec.default_value)

        # Time types (PULSE_DURATION_*): already in raw format (user provides nanoseconds/ms/etc)
        if dt_spec.datatype.value.startswith('pulse_duration_'):
            return dt_spec.default_value

        raise ValueError(f"Unknown datatype category: {dt_spec.datatype}")

    def to_control_registers(self) -> dict[int, int]:
        """
        Export to MokuConfig.control_registers format.

        Returns:
            Dictionary mapping CR number → raw 32-bit value
            Compatible with SlotConfig.control_registers in moku-models

        Example:
            >>> package.to_control_registers()
            {6: 0x00000960, 7: 0x3DCF0000, 8: 0x26660000}
        """
        mappings = self.generate_mapping()

        # Build CR → raw value mapping
        result = {}

        for mapping in mappings:
            # Get DataTypeSpec for this mapping
            dt_spec = next(dt for dt in self.datatypes if dt.name == mapping.name)

            if dt_spec.default_value is not None:
                # Convert typed value to raw bits
                raw_value = self._convert_to_raw(dt_spec)

                # Initialize CR if not present
                if mapping.cr_number not in result:
                    result[mapping.cr_number] = 0

                # Shift raw value to correct bit position and OR into register
                msb, lsb = mapping.bit_slice
                bit_width = msb - lsb + 1

                # Mask raw value to bit width
                mask = (1 << bit_width) - 1
                raw_value &= mask

                # Shift and pack
                result[mapping.cr_number] |= (raw_value << lsb)

        return result

    def to_yaml(self, path: Path) -> None:
        """
        Save register interface to YAML file.

        Args:
            path: Output YAML file path

        Format:
            app_name: DS1140_PD
            description: "..."
            mapping_strategy: best_fit
            datatypes:
              - name: intensity
                datatype: voltage_output_05v_s16
                description: "..."
                default_value: 2400
                min_value: 0
                max_value: 5000
                display_name: "Intensity"
                units: "mV"
        """
        data = {
            'app_name': self.app_name,
            'description': self.description,
            'mapping_strategy': self.mapping_strategy,
            'datatypes': []
        }

        for dt in self.datatypes:
            dt_dict = {
                'name': dt.name,
                'datatype': dt.datatype.value,  # Serialize enum as string
                'description': dt.description,
                'default_value': dt.default_value,
            }

            # Only include optional fields if they're not None
            if dt.min_value is not None:
                dt_dict['min_value'] = dt.min_value
            if dt.max_value is not None:
                dt_dict['max_value'] = dt.max_value
            if dt.display_name is not None:
                dt_dict['display_name'] = dt.display_name
            if dt.units is not None:
                dt_dict['units'] = dt.units

            data['datatypes'].append(dt_dict)

        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, path: Path) -> 'BasicAppsRegPackage':
        """
        Load register interface from YAML file.

        Args:
            path: Input YAML file path

        Returns:
            BasicAppsRegPackage instance
        """
        with open(path) as f:
            data = yaml.safe_load(f)

        # Parse datatypes
        datatypes = []
        for dt_dict in data.get('datatypes', []):
            datatypes.append(DataTypeSpec(
                name=dt_dict['name'],
                datatype=BasicAppDataTypes(dt_dict['datatype']),  # Parse enum from string
                description=dt_dict.get('description', ''),
                default_value=dt_dict.get('default_value'),
                min_value=dt_dict.get('min_value'),
                max_value=dt_dict.get('max_value'),
                display_name=dt_dict.get('display_name'),
                units=dt_dict.get('units'),
            ))

        return cls(
            app_name=data['app_name'],
            description=data.get('description', ''),
            datatypes=datatypes,
            mapping_strategy=data.get('mapping_strategy', 'best_fit')
        )
