# Python API Reference

**Programmatic access to moku-instrument-forge for advanced users.**

This document covers the key Python classes and methods for programmatically working with instrument specifications, register mapping, and code generation.

---

## Overview

### Who Should Use This API?

**Use the Python API when:**
- Building custom tooling around moku-instrument-forge
- Automating package generation in CI/CD pipelines
- Generating multiple instruments programmatically
- Integrating with other Python-based workflows
- Extending forge functionality with custom validators or generators

**For most users:** The command-line interface is sufficient. See [Getting Started Guide](../guides/getting_started.md).

### Core Modules

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `forge.models.package` | Package specification | `BasicAppsRegPackage`, `DataTypeSpec` |
| `forge.models.mapper` | Register mapping | `BADRegisterMapper`, `BADRegisterConfig` |
| `forge.generator.codegen` | Code generation | Functions for generating VHDL |
| `basic_app_datatypes` | Type system | `BasicAppDataTypes`, `TypeConverter`, `TYPE_REGISTRY` |

---

## Core Classes

### `BasicAppsRegPackage`

**Purpose:** Complete register interface specification for custom instruments.

**Location:** `forge/models/package.py`

**Description:** Pydantic model representing the entire instrument specification. This is the single source of truth for package generation.

#### Constructor

```python
from forge.models.package import BasicAppsRegPackage, DataTypeSpec
from basic_app_datatypes import BasicAppDataTypes

package = BasicAppsRegPackage(
    app_name="my_instrument",
    version="1.0.0",
    description="My custom instrument",
    platform="moku_pro",
    datatypes=[
        DataTypeSpec(
            name="voltage_out",
            datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
            description="Output voltage",
            default_value=0
        )
    ],
    mapping_strategy="type_clustering"  # Optional, default
)
```

#### Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `app_name` | `str` | Yes | - | Application name (1-50 chars) |
| `version` | `str` | No | `"1.0.0"` | Semantic version |
| `description` | `str` | No | `""` | Human-readable description (max 500 chars) |
| `platform` | `Literal` | No | `"moku_go"` | Target platform: `moku_go`, `moku_lab`, `moku_pro`, `moku_delta` |
| `datatypes` | `List[DataTypeSpec]` | Yes | - | Signal definitions (min 1) |
| `mapping_strategy` | `Literal` | No | `"type_clustering"` | Packing strategy: `first_fit`, `best_fit`, `type_clustering` |

#### Methods

##### `from_yaml(path: Path) -> BasicAppsRegPackage`

Load package from YAML file.

```python
from pathlib import Path
from forge.models.package import BasicAppsRegPackage

package = BasicAppsRegPackage.from_yaml(Path('specs/my_instrument.yaml'))

# Raises ValidationError if YAML is invalid
```

**Returns:** Validated `BasicAppsRegPackage` instance

**Raises:** `pydantic.ValidationError` if validation fails

---

##### `to_yaml(path: Path) -> None`

Save package to YAML file.

```python
from pathlib import Path

package.to_yaml(Path('output/my_instrument.yaml'))
```

**Note:** Useful for programmatically generating YAML specs.

---

##### `generate_mapping() -> List[RegisterMapping]`

Generate register mapping using configured strategy.

```python
from basic_app_datatypes import RegisterMapping

mappings = package.generate_mapping()

# mappings is List[RegisterMapping]
for mapping in mappings:
    print(f"{mapping.name}: CR{mapping.cr_number}, bits {mapping.bit_slice}")

# Example output:
# voltage_out: CR6, bits (31, 16)
# enable: CR6, bits (15, 15)
```

**Returns:** `List[RegisterMapping]` with CR assignments and bit slices

**Caching:** Results are cached internally. Subsequent calls return same result.

**See also:** [Register Mapping Reference](register_mapping.md) for algorithm details

---

##### `to_control_registers() -> dict[int, int]`

Export to MokuConfig.control_registers format.

```python
# Generate control register dictionary
control_regs = package.to_control_registers()

# Example output:
# {6: 0x00000960, 7: 0x3DCF0000, 8: 0x26660000}

# This format is compatible with moku-models SlotConfig:
from moku_models import SlotConfig

slot_config = SlotConfig(
    bitstream_id="custom_inst",
    control_registers=control_regs,
    # ...
)
```

**Returns:** `dict[int, int]` mapping CR number → 32-bit register value

**Use case:** Direct integration with moku-models deployment workflows

---

##### `to_manifest_json() -> dict`

Generate manifest.json dictionary.

```python
import json

manifest = package.to_manifest_json()

# Save to file
with open('output/manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)
```

**Returns:** Dictionary conforming to manifest.json schema

**See also:** [Manifest Schema Reference](manifest_schema.md)

---

### `DataTypeSpec`

**Purpose:** Rich specification for a single register data element.

**Location:** `forge/models/package.py`

**Description:** Extends basic register config with UI metadata for TUI/GUI generation.

#### Constructor

```python
from forge.models.package import DataTypeSpec
from basic_app_datatypes import BasicAppDataTypes

signal = DataTypeSpec(
    name="intensity",
    datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
    description="Output intensity voltage",
    default_value=0,
    units="V",
    display_name="Intensity",
    min_value=-5.0,
    max_value=5.0
)
```

#### Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | `str` | Yes | - | Variable name (VHDL signal name) |
| `datatype` | `BasicAppDataTypes` | Yes | - | Type from BasicAppDataTypes enum |
| `description` | `str` | No | `""` | Human-readable description (max 200 chars) |
| `default_value` | `int | bool` | No | `None` | Default value at reset |
| `units` | `str` | No | `None` | Physical units (e.g., "V", "ns") (max 10 chars) |
| `display_name` | `str` | No | `None` | UI-friendly name (max 50 chars) |
| `min_value` | `float` | No | `None` | Minimum allowed value (for UI sliders) |
| `max_value` | `float` | No | `None` | Maximum allowed value (for UI sliders) |

#### Methods

##### `get_bit_width() -> int`

Get bit width from TYPE_REGISTRY.

```python
signal = DataTypeSpec(
    name="voltage",
    datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
    description="Output voltage",
    default_value=0
)

width = signal.get_bit_width()  # Returns: 16
```

---

### `BADRegisterMapper`

**Purpose:** Pydantic wrapper for RegisterMapper with YAML integration.

**Location:** `forge/models/mapper.py`

**Description:** Provides Pydantic interface for the core register mapping algorithm.

#### Constructor

```python
from forge.models.mapper import BADRegisterMapper, BADRegisterConfig
from basic_app_datatypes import BasicAppDataTypes

mapper = BADRegisterMapper(
    registers=[
        BADRegisterConfig(
            name="voltage",
            datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
            description="Output voltage",
            default_value=0
        ),
        BADRegisterConfig(
            name="enable",
            datatype=BasicAppDataTypes.BOOLEAN,
            description="Enable output",
            default_value=0
        )
    ],
    strategy="type_clustering"
)
```

#### Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `registers` | `List[BADRegisterConfig]` | Yes | - | Register configurations (min 1) |
| `strategy` | `Literal` | No | `"type_clustering"` | Packing strategy |

#### Methods

##### `to_register_mappings() -> List[RegisterMapping]`

Apply core mapping algorithm.

```python
mappings = mapper.to_register_mappings()

# mappings is List[RegisterMapping]
for m in mappings:
    print(f"{m.name}: CR{m.cr_number}, bits {m.bit_slice}")
```

**Returns:** `List[RegisterMapping]` with CR assignments

**Raises:** `ValueError` if mapping fails (overflow, invalid types)

---

##### `generate_report() -> MappingReport`

Generate detailed mapping report with visualizations.

```python
report = mapper.generate_report()

# ASCII art visualization
print(report.to_ascii_art())

# Markdown format
print(report.to_markdown())

# VHDL comments
print(report.to_vhdl_comments())

# JSON format
import json
print(json.dumps(report.to_json(), indent=2))
```

**Returns:** `MappingReport` with visualizations and statistics

---

##### `save_report(output_dir: Path, formats: List[str] = None) -> None`

Save mapping report in multiple formats.

```python
from pathlib import Path

mapper.save_report(
    output_dir=Path('output/reports'),
    formats=['ascii', 'markdown', 'vhdl', 'json']
)

# Generates:
# output/reports/mapping_report.txt
# output/reports/mapping_report.md
# output/reports/mapping_comments.vhd
# output/reports/mapping.json
```

---

### `TypeConverter`

**Purpose:** Physical ↔ raw conversion for voltage and time types.

**Location:** `libs/basic-app-datatypes/basic_app_datatypes/converters.py`

**Description:** Provides conversion methods for all BasicAppDataTypes.

**Authoritative Documentation:** See [`libs/basic-app-datatypes/llms.txt`](../../libs/basic-app-datatypes/llms.txt)

#### Usage Example

```python
from basic_app_datatypes import TypeConverter

converter = TypeConverter()

# Voltage conversion (volts → raw bits)
voltage = 2.5  # Volts
raw_value = converter.voltage_output_05v_s16_to_raw(voltage)
# Result: 16384 (0x4000) - 50% of signed 16-bit range

# Voltage conversion (raw bits → volts)
volts = converter.voltage_output_05v_s16_from_raw(16384)
# Result: 2.5
```

#### Methods

TypeConverter provides 24+ conversion methods. See [Type System Reference](type_system.md) for complete list.

**Naming Convention:**
- `{type_name}_to_raw(value)` - Physical → raw bits
- `{type_name}_from_raw(raw)` - Raw bits → physical

**Examples:**
- `voltage_output_05v_s16_to_raw(volts)` → int
- `voltage_output_05v_s16_from_raw(raw)` → float
- `voltage_input_20v_s16_to_raw(volts)` → int
- `voltage_input_20v_s16_from_raw(raw)` → float

**See also:** [`libs/basic-app-datatypes/llms.txt`](../../libs/basic-app-datatypes/llms.txt) for complete API

---

## Type System Integration

### `BasicAppDataTypes` Enum

**Purpose:** Enum defining all 23 built-in types.

**Location:** `libs/basic-app-datatypes/basic_app_datatypes/types.py`

```python
from basic_app_datatypes import BasicAppDataTypes

# Access enum values
voltage_type = BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
time_type = BasicAppDataTypes.PULSE_DURATION_NS_U16
bool_type = BasicAppDataTypes.BOOLEAN

# String representation
print(voltage_type.value)  # "voltage_output_05v_s16"

# Parse from string
datatype = BasicAppDataTypes("voltage_output_05v_s16")
```

**See also:** [Type System Reference](type_system.md) for all 23 types

---

### `TYPE_REGISTRY` Dictionary

**Purpose:** Metadata lookup for all types.

**Location:** `libs/basic-app-datatypes/basic_app_datatypes/metadata.py`

```python
from basic_app_datatypes import TYPE_REGISTRY, BasicAppDataTypes

# Query type metadata
metadata = TYPE_REGISTRY[BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16]

print(metadata.bit_width)      # 16
print(metadata.is_signed)      # True
print(metadata.voltage_range)  # "±5V"
print(metadata.description)    # "Output voltage, ±5V range, signed 16-bit"
print(metadata.min_value)      # -32768
print(metadata.max_value)      # 32767
print(metadata.python_type)    # <class 'int'>
print(metadata.vhdl_type)      # "signed"
```

**Metadata Fields:**
- `bit_width`: `int` - Number of bits
- `is_signed`: `bool` - Signed vs unsigned
- `voltage_range`: `str` - Human-readable range (e.g., "±5V")
- `description`: `str` - Human-readable description
- `min_value`: `int | None` - Minimum integer value
- `max_value`: `int | None` - Maximum integer value
- `python_type`: `type` - Python type (int, bool)
- `vhdl_type`: `str` - VHDL type ("signed", "unsigned", "std_logic")
- `unit`: `str` - Physical unit ("mV", "ns", "us", "ms", "s", or None for boolean)

---

## File I/O

### Loading YAML

```python
from pathlib import Path
from forge.models.package import BasicAppsRegPackage

# Load from YAML
package = BasicAppsRegPackage.from_yaml(Path('specs/my_instrument.yaml'))

# Access fields
print(package.app_name)
print(package.platform)
for dt in package.datatypes:
    print(f"{dt.name}: {dt.datatype.value}")
```

---

### Saving YAML

```python
from pathlib import Path

# Modify package
package.description = "Updated description"

# Save to YAML
package.to_yaml(Path('output/my_instrument_v2.yaml'))
```

---

### Exporting manifest.json

```python
import json
from pathlib import Path

# Generate manifest
manifest = package.to_manifest_json()

# Save to file
output_file = Path('output/manifest.json')
with open(output_file, 'w') as f:
    json.dump(manifest, f, indent=2)

print(f"Manifest saved to {output_file}")
```

---

## Code Generation Pipeline

### Programmatic Generation

```python
from pathlib import Path
from forge.models.package import BasicAppsRegPackage
from forge.generator.codegen import generate_vhdl_package

# Load YAML
yaml_path = Path('specs/my_instrument.yaml')
package = BasicAppsRegPackage.from_yaml(yaml_path)

# Generate all artifacts
output_dir = Path('output/my_instrument')
output_dir.mkdir(parents=True, exist_ok=True)

# Generate VHDL + manifest
generate_vhdl_package(
    package=package,
    output_dir=output_dir,
    yaml_path=yaml_path
)

# Files generated:
# output/my_instrument/my_instrument_shim.vhd
# output/my_instrument/my_instrument_main.vhd
# output/my_instrument/manifest.json
# output/my_instrument/control_registers.json
```

**See also:** [VHDL Generation Reference](vhdl_generation.md) for pipeline details

---

## Integration with moku-models

### Exporting Control Registers

```python
from forge.models.package import BasicAppsRegPackage
from moku_models import MokuConfig, SlotConfig

# Load package
package = BasicAppsRegPackage.from_yaml('specs/my_instrument.yaml')

# Convert to moku-models format
control_regs = package.to_control_registers()

# Create SlotConfig
slot_config = SlotConfig(
    slot_id=1,
    bitstream_id="custom_inst",
    control_registers=control_regs,
)

# Create MokuConfig
moku_config = MokuConfig(
    platform="moku_pro",
    slots=[slot_config],
)

# Deploy to hardware
# ... (use moku-models deployment API)
```

**See also:**
- [`libs/moku-models/README.md`](../../libs/moku-models/README.md) - Moku-models documentation
- [Architecture - Submodule Integration](../architecture/submodule_integration.md)

---

## Advanced Usage

### Custom Validation

Add custom validators using Pydantic decorators:

```python
from forge.models.package import BasicAppsRegPackage
from pydantic import model_validator

class MyCustomPackage(BasicAppsRegPackage):
    @model_validator(mode='after')
    def validate_custom_constraints(self) -> 'MyCustomPackage':
        # Custom validation logic
        if self.app_name.startswith('test_'):
            raise ValueError("Production packages cannot start with 'test_'")
        return self

# Use custom package
package = MyCustomPackage.from_yaml('specs/my_instrument.yaml')
```

---

### Programmatic Package Creation

Build packages entirely in Python (no YAML):

```python
from forge.models.package import BasicAppsRegPackage, DataTypeSpec
from basic_app_datatypes import BasicAppDataTypes

# Create signals
signals = []
for i in range(4):
    signals.append(DataTypeSpec(
        name=f"channel_{i}_voltage",
        datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
        description=f"Channel {i} output voltage",
        default_value=0,
        units="V"
    ))

# Create package
package = BasicAppsRegPackage(
    app_name="multi_channel_gen",
    version="1.0.0",
    description="Auto-generated multi-channel instrument",
    platform="moku_pro",
    datatypes=signals,
    mapping_strategy="type_clustering"
)

# Generate mapping
mappings = package.generate_mapping()
print(f"Generated {len(mappings)} mappings")

# Save to YAML
package.to_yaml(Path('output/multi_channel_gen.yaml'))
```

---

### Batch Generation

Generate multiple instruments programmatically:

```python
from pathlib import Path
from forge.models.package import BasicAppsRegPackage
from forge.generator.codegen import generate_vhdl_package

# List of instrument specs
specs = [
    'specs/instrument_a.yaml',
    'specs/instrument_b.yaml',
    'specs/instrument_c.yaml',
]

# Generate all
for spec_path in specs:
    yaml_path = Path(spec_path)
    package = BasicAppsRegPackage.from_yaml(yaml_path)

    output_dir = Path('output') / package.app_name
    output_dir.mkdir(parents=True, exist_ok=True)

    generate_vhdl_package(
        package=package,
        output_dir=output_dir,
        yaml_path=yaml_path
    )

    print(f"Generated: {package.app_name}")
```

---

## Error Handling

### Validation Errors

```python
from pydantic import ValidationError
from forge.models.package import BasicAppsRegPackage

try:
    package = BasicAppsRegPackage.from_yaml('specs/invalid.yaml')
except ValidationError as e:
    print("Validation failed:")
    for error in e.errors():
        print(f"  - {error['loc']}: {error['msg']}")
```

**Example Error Output:**
```
Validation failed:
  - ('datatypes', 0, 'default_value'): default_value 100000 above max 32767
  - ('datatypes', 1, 'name'): Name must start with letter
```

---

### Register Overflow

```python
try:
    mappings = package.generate_mapping()
except ValueError as e:
    print(f"Mapping failed: {e}")
```

**Example Error:**
```
Mapping failed: Total bits (400) exceeds 384-bit limit (12 registers × 32 bits)
```

---

## Related Documentation

- **[Type System Reference](type_system.md)** - All 23 BasicAppDataTypes
- **[YAML Schema Reference](yaml_schema.md)** - YAML format specification
- **[Register Mapping Reference](register_mapping.md)** - Mapping algorithms
- **[Manifest Schema Reference](manifest_schema.md)** - Output format
- **[VHDL Generation Reference](vhdl_generation.md)** - Code generation pipeline
- **[BasicAppDataTypes API](../../libs/basic-app-datatypes/llms.txt)** - Complete type system documentation

---

## Key Files

**Forge Implementation:**
- `forge/models/package.py` - Package and DataTypeSpec models
- `forge/models/mapper.py` - BADRegisterMapper wrapper
- `forge/generator/codegen.py` - Code generation pipeline

**BasicAppDataTypes Library:**
- `libs/basic-app-datatypes/basic_app_datatypes/types.py` - BasicAppDataTypes enum
- `libs/basic-app-datatypes/basic_app_datatypes/metadata.py` - TYPE_REGISTRY
- `libs/basic-app-datatypes/basic_app_datatypes/converters.py` - TypeConverter
- `libs/basic-app-datatypes/basic_app_datatypes/mapper.py` - RegisterMapper core

---

**Key Takeaway:** The Python API provides programmatic access to all forge functionality. Use `BasicAppsRegPackage` for package management, `BADRegisterMapper` for register allocation, and `TypeConverter` for value conversions. Most users should use the command-line interface; the API is for advanced tooling and automation.

---

*Last Updated: 2025-11-03*
