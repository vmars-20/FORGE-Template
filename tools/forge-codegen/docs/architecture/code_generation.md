# Code Generation Pipeline

**Deep dive into the forge code generation engine**

**Purpose:** Understand how YAML specifications are transformed into VHDL + metadata packages

---

## Table of Contents

1. [Pipeline Overview](#pipeline-overview)
2. [Stage 1: YAML Loading](#stage-1-yaml-loading)
3. [Stage 2: Pydantic Validation](#stage-2-pydantic-validation)
4. [Stage 3: Register Mapping](#stage-3-register-mapping)
5. [Stage 4: Template Context Preparation](#stage-4-template-context-preparation)
6. [Stage 5: VHDL Generation](#stage-5-vhdl-generation)
7. [Stage 6: Manifest Generation](#stage-6-manifest-generation)
8. [Mapping Strategies](#mapping-strategies)
9. [Template Rendering](#template-rendering)
10. [Error Handling](#error-handling)

---

## Pipeline Overview

### High-Level Flow

```
YAML file
    │
    ▼
┌──────────────────────┐
│ 1. Load YAML         │  load_yaml_spec()
│    (PyYAML)          │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 2. Validate Schema   │  create_register_package()
│    (Pydantic)        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 3. Map Registers     │  RegisterMapper.map()
│    (3 strategies)    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 4. Prepare Context   │  prepare_template_context()
│    (Template vars)   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 5. Render Templates  │  Jinja2 Environment
│    (shim + main)     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 6. Generate Manifest │  JSON output
│    (metadata)        │
└──────┬───────────────┘
       │
       ▼
Well-formed package
```

### Key Components

**Location:** `forge/generator/codegen.py`

**Dependencies:**
- `PyYAML` - YAML parsing
- `Pydantic` - Schema validation
- `Jinja2` - Template rendering
- `basic_app_datatypes` - Type system and register mapping

**Output:** Well-formed package directory with VHDL files and JSON metadata

---

## Stage 1: YAML Loading

### API: `load_yaml_spec(yaml_path: Path) -> Dict[str, Any]`

**Purpose:** Load YAML file and perform basic validation

**Implementation:**
```python
from forge.generator.codegen import load_yaml_spec
from pathlib import Path

# Load YAML specification
yaml_path = Path("apps/DS1140_PD/DS1140_PD.yaml")
spec = load_yaml_spec(yaml_path)

# Returns dict with structure:
# {
#   'app_name': 'DS1140_PD',
#   'version': '1.0.0',
#   'description': 'EMFI probe driver',
#   'platform': 'moku_go',
#   'datatypes': [...],
#   'mapping_strategy': 'type_clustering'
# }
```

**Validation performed:**
- Required fields present (`app_name`, `datatypes`)
- YAML syntax valid (PyYAML safe_load)
- Default values applied:
  - `platform`: defaults to `'moku_go'`
  - `mapping_strategy`: defaults to `'best_fit'`

**Error handling:**
```python
try:
    spec = load_yaml_spec(yaml_path)
except FileNotFoundError:
    print(f"YAML file not found: {yaml_path}")
except yaml.YAMLError as e:
    print(f"YAML syntax error: {e}")
except ValueError as e:
    print(f"Missing required field: {e}")
```

---

## Stage 2: Pydantic Validation

### API: `create_register_package(spec: Dict[str, Any]) -> BasicAppsRegPackage`

**Purpose:** Convert raw YAML dict to validated Pydantic model

**Implementation:**
```python
from forge.generator.codegen import create_register_package

# Create Pydantic package from spec dict
package = create_register_package(spec)

# Returns BasicAppsRegPackage instance with:
# - package.app_name: str
# - package.version: str
# - package.description: str
# - package.platform: str
# - package.datatypes: List[DataTypeSpec]
# - package.mapping_strategy: str
```

### Pydantic Models

**Location:** `forge/models/package.py`

**BasicAppsRegPackage model:**
```python
from forge.models.package import BasicAppsRegPackage, DataTypeSpec
from basic_app_datatypes import BasicAppDataTypes

class DataTypeSpec:
    """Single datatype specification."""
    name: str                      # Signal name (snake_case)
    datatype: BasicAppDataTypes    # Enum from basic-app-datatypes
    description: str               # Human-readable description
    default_value: int             # Raw integer default
    min_value: int                 # Minimum valid value
    max_value: int                 # Maximum valid value
    display_name: str              # UI-friendly name
    units: str                     # Physical units (V, ms, etc.)

class BasicAppsRegPackage:
    """Complete package specification."""
    app_name: str                  # Application name
    version: str                   # Semantic version (default: "1.0.0")
    description: str               # Application description
    platform: str                  # Target Moku platform
    datatypes: List[DataTypeSpec]  # List of signals
    mapping_strategy: str          # Packing strategy
```

### Validation Rules

**Automatic validation by Pydantic:**

1. **app_name format:**
   - Alphanumeric + underscores only
   - No spaces or special characters
   - ✅ `DS1140_PD` ✅ `minimal_probe`
   - ❌ `DS1140-PD` ❌ `minimal probe`

2. **Datatype enum lookup:**
   - Must exist in `BasicAppDataTypes` enum
   - Case-insensitive (converted to uppercase)
   - ✅ `voltage_output_05v_s16`
   - ❌ `voltage_10v_s16` (doesn't exist)

3. **Default value ranges:**
   - Must be within type's min/max range
   - Checked against `TYPE_REGISTRY` metadata
   - Example: `voltage_output_05v_s16` range is -32768 to 32767

4. **Signal name validation:**
   - Must be valid Python identifier (snake_case)
   - No VHDL reserved keywords
   - ✅ `trigger_threshold` ✅ `arm_probe`
   - ❌ `trigger-threshold` ❌ `signal` (VHDL keyword)

5. **Platform validation:**
   - Must be in `PLATFORM_MAP`
   - Valid values: `moku_go`, `moku_lab`, `moku_pro`, `moku_delta`

**Example validation error:**
```python
# Invalid default value
spec = {
    'app_name': 'test',
    'datatypes': [{
        'name': 'voltage',
        'datatype': 'voltage_output_05v_s16',
        'default_value': 100000  # Exceeds max (32767)
    }]
}

try:
    package = create_register_package(spec)
except ValueError as e:
    print(e)  # "default_value 100000 out of range for voltage_output_05v_s16"
```

---

## Stage 3: Register Mapping

### API: `RegisterMapper.map(items, strategy) -> List[RegisterMapping]`

**Purpose:** Allocate signals to control registers (CR6-CR15) with bit packing

**Implementation:**
```python
from basic_app_datatypes import RegisterMapper

# Create mapper
mapper = RegisterMapper()

# Prepare items list: (signal_name, datatype_enum)
items = [(dt.name, dt.datatype) for dt in package.datatypes]

# Execute mapping with strategy
mappings = mapper.map(items, strategy=package.mapping_strategy)

# Returns List[RegisterMapping] with:
# - mapping.name: str (signal name)
# - mapping.cr_number: int (6-15)
# - mapping.bit_high: int (31-0)
# - mapping.bit_low: int (31-0)
# - mapping.to_vhdl_slice() -> str (e.g., "app_reg_6(31 downto 16)")
```

### Register Mapping Output

**RegisterMapping objects provide:**

```python
for mapping in mappings:
    print(f"Signal: {mapping.name}")
    print(f"  CR: {mapping.cr_number}")
    print(f"  Bits: {mapping.bit_high}:{mapping.bit_low}")
    print(f"  Width: {mapping.bit_high - mapping.bit_low + 1}")
    print(f"  VHDL: {mapping.to_vhdl_slice()}")

# Example output:
# Signal: arm_timeout
#   CR: 6
#   Bits: 31:16
#   Width: 16
#   VHDL: app_reg_6(31 downto 16)
```

### Packing Example

**Input:** 8 signals from DS1140_PD
```yaml
datatypes:
  - name: intensity             # 16-bit voltage
  - name: arm_timeout           # 16-bit time
  - name: trigger_threshold     # 16-bit voltage
  - name: cooling_duration      # 8-bit time
  - name: firing_duration       # 8-bit time
  - name: arm_probe             # 1-bit boolean
  - name: force_fire            # 1-bit boolean
  - name: reset_fsm             # 1-bit boolean
```

**Output:** 3 registers with efficient packing (type_clustering strategy)
```
CR6 [31:16] arm_timeout          (16-bit, TIME_MILLISECONDS_U16)
CR6 [15:0]  intensity             (16-bit, VOLTAGE_OUTPUT_05V_S16)

CR7 [31:16] trigger_threshold     (16-bit, VOLTAGE_SIGNED_S16)
CR7 [15:8]  cooling_duration      (8-bit, TIME_CYCLES_U8)
CR7 [7:0]   firing_duration       (8-bit, TIME_CYCLES_U8)

CR8 [31]    arm_probe             (1-bit, BOOLEAN)
CR8 [30]    force_fire            (1-bit, BOOLEAN)
CR8 [29]    reset_fsm             (1-bit, BOOLEAN)
```

**Efficiency:** 67 bits used / 96 bits available = 69.8%

---

## Stage 4: Template Context Preparation

### API: `prepare_template_context(package, yaml_path, platform_info) -> Dict[str, Any]`

**Purpose:** Build context dictionary for Jinja2 template rendering

**Implementation:**
```python
from forge.generator.codegen import prepare_template_context, PLATFORM_MAP

# Get platform info
platform_info = PLATFORM_MAP[spec['platform']]

# Prepare template context
context = prepare_template_context(
    package=package,
    yaml_path=yaml_path,
    platform_info=platform_info
)

# Returns dict with:
# {
#   'app_name': 'DS1140_PD',
#   'platform': {...},
#   'signals': [...],       # List of signal metadata
#   'register_mappings': [...],
#   'has_voltage': bool,
#   'has_time': bool,
#   'generated_at': '2025-11-03 12:34:56',
#   ...
# }
```

### Context Dictionary Structure

**Platform info:**
```python
context['platform'] = {
    'name': 'Moku:Go',
    'clock_mhz': 125,
    'slots': 2,
}
```

**Signal metadata (used in templates):**
```python
context['signals'] = [
    {
        'name': 'intensity',
        'vhdl_type': 'voltage_output_05v_s16',
        'vhdl_base_type': 'signed',          # or 'unsigned'
        'description': 'Output intensity',
        'default_value': 2400,
        'bit_width': 16,
        'cr_number': 6,
        'bit_range': '(15 downto 0)',
        'bit_position': None,                 # Only for 1-bit booleans
        'is_boolean': False,
        'is_voltage': True,
        'is_time': False,
        'unit': 'mV',
        'direction': 'input',
    },
    # ... more signals
]
```

**Register mapping summaries:**
```python
context['register_mappings'] = {
    6: [
        RegisterMapping(name='arm_timeout', cr_number=6, bit_high=31, bit_low=16),
        RegisterMapping(name='intensity', cr_number=6, bit_high=15, bit_low=0),
    ],
    7: [...],
    8: [...],
}
```

**Type package flags:**
```python
context['has_voltage'] = True   # At least one voltage type present
context['has_time'] = True      # At least one time type present
```

---

## Stage 5: VHDL Generation

### Jinja2 Template Rendering

**Template files:**
- `forge/templates/shim.vhd.j2` - Shim layer (register extraction)
- `forge/templates/main.vhd.j2` - Main template (user logic)

**Rendering process:**
```python
from jinja2 import Environment, FileSystemLoader

# Create Jinja2 environment
jinja_env = Environment(
    loader=FileSystemLoader('forge/templates/'),
    trim_blocks=True,
    lstrip_blocks=True
)

# Render shim layer
shim_template = jinja_env.get_template('shim.vhd.j2')
shim_vhdl = shim_template.render(context)

# Render main template
main_template = jinja_env.get_template('main.vhd.j2')
main_vhdl = main_template.render(context)

# Write output files
output_dir = Path(f"apps/{package.app_name}")
output_dir.mkdir(parents=True, exist_ok=True)

shim_path = output_dir / f"{package.app_name}_custom_inst_shim.vhd"
main_path = output_dir / f"{package.app_name}_custom_inst_main.vhd"

shim_path.write_text(shim_vhdl)
main_path.write_text(main_vhdl)
```

### Shim Layer Template (`shim.vhd.j2`)

**Purpose:** Extract bit slices from control registers and convert to typed signals

**Key template blocks:**

1. **Library imports:**
```jinja2
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

{% if has_voltage %}
use work.basic_app_voltage_types_pkg.all;
{% endif %}

{% if has_time %}
use work.basic_app_time_types_pkg.all;
{% endif %}
```

2. **Signal declarations:**
```jinja2
{% for signal in signals %}
-- {{ signal.description }}
signal {{ signal.name }} : {{ signal.vhdl_type }};
{% endfor %}
```

3. **Bit extraction:**
```jinja2
{% for signal in signals %}
{% if signal.is_boolean %}
-- Boolean signal: extract single bit
{{ signal.name }} <= app_reg_{{ signal.cr_number }}{{ signal.bit_range }};
{% else %}
-- {{ signal.bit_width }}-bit signal: extract and convert
{{ signal.name }} <= {{ signal.vhdl_type }}(
    {{ signal.vhdl_base_type }}(app_reg_{{ signal.cr_number }}{{ signal.bit_range }})
);
{% endif %}
{% endfor %}
```

**Example generated VHDL:**
```vhdl
-- Output intensity (clamped to 3.0V)
signal intensity : voltage_output_05v_s16;

-- Bit extraction
intensity <= voltage_output_05v_s16(
    signed(app_reg_6(15 downto 0))
);
```

### Main Template (`main.vhd.j2`)

**Purpose:** Provide skeleton for user logic implementation

**Key sections:**

1. **Entity declaration with friendly signals:**
```vhdl
entity DS1140_PD_custom_inst_main is
    port (
        -- Clock and reset
        Clk         : in std_logic;
        Reset       : in std_logic;

        -- User signals (friendly names)
        intensity         : in voltage_output_05v_s16;
        arm_timeout       : in time_milliseconds_u16;
        arm_probe         : in std_logic;

        -- Outputs
        output_a          : out voltage_output_05v_s16;
        fsm_state_debug   : out std_logic_vector(2 downto 0)
    );
end entity;
```

2. **User implements architecture:**
```vhdl
architecture rtl of DS1140_PD_custom_inst_main is
    -- User defines FSM, processes, etc.
begin
    -- User logic here
end architecture;
```

---

## Stage 6: Manifest Generation

### manifest.json Creation

**Purpose:** Generate package metadata for downstream consumers

**Implementation:**
```python
import json
from datetime import datetime

# Build manifest dictionary
manifest = {
    "app_name": package.app_name,
    "version": package.version,
    "description": package.description,
    "platform": package.platform,
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "generator_version": "0.1.0",
    "datatypes": [
        {
            "name": dt.name,
            "datatype": dt.datatype.name.lower(),
            "description": dt.description,
            "default_value": dt.default_value,
            "display_name": dt.display_name,
            "units": dt.units,
            "min_value": dt.min_value,
            "max_value": dt.max_value,
        }
        for dt in package.datatypes
    ],
    "register_mappings": [
        {
            "signal_name": mapping.name,
            "cr_number": mapping.cr_number,
            "bit_slice": f"{mapping.bit_high}:{mapping.bit_low}",
            "bit_width": mapping.bit_high - mapping.bit_low + 1,
            "vhdl_type": TYPE_REGISTRY[
                next(dt.datatype for dt in package.datatypes if dt.name == mapping.name)
            ].vhdl_type,
        }
        for mapping in mappings
    ],
    "efficiency": {
        "bits_used": sum(m.bit_high - m.bit_low + 1 for m in mappings),
        "bits_available": 10 * 32,  # CR6-CR15
        "percent_used": (sum(m.bit_high - m.bit_low + 1 for m in mappings) / 320) * 100,
        "registers_used": len(set(m.cr_number for m in mappings)),
        "strategy": package.mapping_strategy,
    },
}

# Write manifest
manifest_path = output_dir / "manifest.json"
with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)
```

### control_registers.json Creation

**Purpose:** Provide initial register values with packed defaults

**Implementation:**
```python
# Build control registers dict with packed defaults
control_registers = {}

for cr_num in range(6, 16):
    # Initialize to 0
    cr_value = 0

    # Pack default values for signals in this CR
    for dt, mapping in zip(package.datatypes, mappings):
        if mapping.cr_number == cr_num:
            # Shift default value to correct bit position
            shifted_value = dt.default_value << mapping.bit_low
            cr_value |= shifted_value

    # Only include CRs that are actually used
    if any(m.cr_number == cr_num for m in mappings):
        control_registers[str(cr_num)] = f"0x{cr_value:08X}"

# Write control_registers.json
control_regs_path = output_dir / "control_registers.json"
with open(control_regs_path, "w") as f:
    json.dump(control_registers, f, indent=2)
```

**Example output:**
```json
{
  "6": "0x00FF0960",
  "7": "0xF8300820",
  "8": "0x00000000"
}
```

---

## Mapping Strategies

### 1. first_fit

**Algorithm:** Place each signal in the first CR with enough contiguous space

**Characteristics:**
- Simple, fast
- Sequential allocation
- Can fragment registers

**Best for:** Small specs (<5 signals)

**Example:**
```
Signal 1 (16-bit) → CR6[15:0]
Signal 2 (16-bit) → CR6[31:16]
Signal 3 (8-bit)  → CR7[7:0]
Signal 4 (1-bit)  → CR7[8:8]
```

### 2. best_fit

**Algorithm:** Place each signal in the CR that minimizes wasted space

**Characteristics:**
- Reduces fragmentation
- Considers all available gaps
- Slightly slower than first_fit

**Best for:** Medium specs (5-10 signals)

**Example:**
```
Signal 1 (16-bit) → CR6[31:16]
Signal 2 (8-bit)  → CR6[15:8]
Signal 3 (8-bit)  → CR6[7:0]    # Best fit in CR6
Signal 4 (1-bit)  → CR7[31:31]
```

### 3. type_clustering (default)

**Algorithm:** Group signals by type category (voltage, time, boolean), then pack each group

**Characteristics:**
- Best cache locality
- Clear register organization
- May use slightly more registers than best_fit

**Best for:** Large specs (>10 signals), production use

**Example:**
```
# Voltage signals grouped in CR6-CR7
CR6[31:16] voltage_1 (16-bit)
CR6[15:0]  voltage_2 (16-bit)
CR7[31:16] voltage_3 (16-bit)

# Time signals grouped in CR7-CR8
CR7[15:8]  time_1 (8-bit)
CR7[7:0]   time_2 (8-bit)
CR8[31:16] time_3 (16-bit)

# Boolean signals grouped in CR8
CR8[15]    bool_1 (1-bit)
CR8[14]    bool_2 (1-bit)
CR8[13]    bool_3 (1-bit)
```

**Recommendation:** Use `type_clustering` for production, `best_fit` for experimentation.

---

## Template Rendering

### Jinja2 Features Used

**1. Conditional blocks:**
```jinja2
{% if has_voltage %}
use work.basic_app_voltage_types_pkg.all;
{% endif %}
```

**2. Loops:**
```jinja2
{% for signal in signals %}
signal {{ signal.name }} : {{ signal.vhdl_type }};
{% endfor %}
```

**3. Filters:**
```jinja2
-- Generated on {{ generated_at | strftime('%Y-%m-%d %H:%M:%S') }}
```

**4. Comments:**
```jinja2
{# This is a template comment, won't appear in output #}
```

### Template Best Practices

1. **Whitespace control:**
   - Use `trim_blocks=True` and `lstrip_blocks=True` to avoid extra blank lines
   - Use `{%-` and `-%}` for explicit whitespace trimming

2. **Readability:**
   - Add comments explaining template logic
   - Use descriptive variable names in context
   - Group related template blocks

3. **Validation:**
   - Test templates with multiple example specs
   - Verify generated VHDL compiles with GHDL
   - Check edge cases (1-bit signals, max registers)

---

## Error Handling

### Common Errors and Solutions

**Error:** `Unknown datatype: 'voltage_10v_s16'`
```python
# Solution: Check BasicAppDataTypes enum
from basic_app_datatypes import BasicAppDataTypes
print(list(BasicAppDataTypes))  # List all valid types
```

**Error:** `default_value 40000 out of range for voltage_output_05v_s16 (max: 32767)`
```python
# Solution: Reduce default_value or use larger type
# voltage_output_05v_s16 is 16-bit signed: -32768 to 32767
# For larger values, consider unsigned type or 32-bit variant
```

**Error:** `Invalid signal name 'trigger-threshold' (must be snake_case)`
```python
# Solution: Rename to snake_case
# ✅ trigger_threshold
# ❌ trigger-threshold
# ❌ triggerThreshold
```

**Error:** `Cannot fit signals in 10 registers`
```python
# Solution: Reduce number of signals or use smaller types
# Available: 10 registers × 32 bits = 320 bits total
# Check: sum(signal.bit_width for all signals) <= 320
```

**Error:** `Template not found: shim.vhd.j2`
```python
# Solution: Verify forge/templates/ directory structure
ls forge/templates/
# Should contain: shim.vhd.j2, main.vhd.j2
```

---

## Complete Example

**End-to-end code generation:**

```python
from pathlib import Path
from forge.generator.codegen import (
    load_yaml_spec,
    create_register_package,
    prepare_template_context,
    PLATFORM_MAP
)
from basic_app_datatypes import RegisterMapper
from jinja2 import Environment, FileSystemLoader
import json

# Step 1: Load YAML
yaml_path = Path("apps/DS1140_PD/DS1140_PD.yaml")
spec = load_yaml_spec(yaml_path)

# Step 2: Create Pydantic package
package = create_register_package(spec)

# Step 3: Map registers
mapper = RegisterMapper()
items = [(dt.name, dt.datatype) for dt in package.datatypes]
mappings = mapper.map(items, strategy=package.mapping_strategy)

# Step 4: Prepare template context
platform_info = PLATFORM_MAP[spec['platform']]
context = prepare_template_context(package, yaml_path, platform_info)

# Step 5: Render templates
jinja_env = Environment(loader=FileSystemLoader('forge/templates/'))
shim_template = jinja_env.get_template('shim.vhd.j2')
main_template = jinja_env.get_template('main.vhd.j2')

shim_vhdl = shim_template.render(context)
main_vhdl = main_template.render(context)

# Step 6: Write outputs
output_dir = Path(f"apps/{package.app_name}")
output_dir.mkdir(parents=True, exist_ok=True)

(output_dir / f"{package.app_name}_custom_inst_shim.vhd").write_text(shim_vhdl)
(output_dir / f"{package.app_name}_custom_inst_main.vhd").write_text(main_vhdl)

# Generate manifest.json (simplified)
manifest = {
    "app_name": package.app_name,
    "version": package.version,
    # ... (full structure shown in Stage 6)
}
with open(output_dir / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

print(f"✅ Generated package: {output_dir}")
print(f"   Efficiency: {len(mappings)} signals → {len(set(m.cr_number for m in mappings))} registers")
```

---

## Performance Considerations

**Pipeline execution time:**
- YAML loading: ~10ms
- Pydantic validation: ~50ms
- Register mapping: ~100ms (type_clustering), ~50ms (first_fit)
- Template rendering: ~200ms
- File I/O: ~50ms
- **Total:** ~400-500ms for typical spec

**Optimization tips:**
1. Cache Pydantic models during iteration
2. Use `first_fit` for rapid prototyping
3. Skip validation with `--skip-validation` flag (development only)

---

**See also:**
- [overview.md](overview.md) - High-level architecture
- [agent_system.md](agent_system.md) - forge-context agent details
- [design_decisions.md](design_decisions.md) - Why these choices?
- `libs/basic-app-datatypes/llms.txt` - Type system documentation

---

**Last Updated:** 2025-11-03 (Phase 6D)
**Maintained By:** moku-instrument-forge team
