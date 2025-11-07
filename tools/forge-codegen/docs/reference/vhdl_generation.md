# VHDL Generation Pipeline

**Complete documentation of the code generation pipeline from YAML to VHDL.**

This document explains how moku-instrument-forge transforms YAML specifications into type-safe VHDL code with automatic register packing.

---

## Overview

### Pipeline Architecture

```
┌──────────────┐
│ YAML File    │  User-authored specification
└──────┬───────┘
       │
       ├─> 1. YAML Parsing (PyYAML)
       │
       ▼
┌──────────────┐
│ Pydantic     │  Schema validation, type checking
│ Validation   │  (BasicAppsRegPackage model)
└──────┬───────┘
       │
       ├─> 2. Pydantic Models
       │
       ▼
┌──────────────┐
│ Register     │  Automatic bit packing
│ Mapping      │  (BADRegisterMapper)
└──────┬───────┘
       │
       ├─> 3. Register Assignments (CR6-CR15)
       │
       ▼
┌──────────────┐
│ Template     │  Jinja2 rendering
│ Rendering    │  (VHDL templates + manifest)
└──────┬───────┘
       │
       ├─> 4. File Generation
       │
       ▼
┌──────────────────────────────────────────┐
│ Generated Artifacts:                     │
│ • <app>_shim.vhd                        │
│ • <app>_main.vhd                        │
│ • manifest.json                         │
│ • control_registers.json                │
└──────────────────────────────────────────┘
```

**Key Components:**
- **YAML Parser:** PyYAML for safe parsing
- **Validation:** Pydantic models for type safety
- **Mapper:** BADRegisterMapper for optimal packing
- **Templates:** Jinja2 for VHDL generation
- **Outputs:** VHDL files + JSON metadata

---

## Pipeline Stages

### Stage 1: YAML Parsing

**Tool:** PyYAML (`yaml.safe_load()`)

**Input:** YAML specification file (e.g., `specs/my_instrument.yaml`)

**Process:**
1. Load YAML file using `yaml.safe_load()`
2. Parse into Python dictionary
3. Set defaults for optional fields
4. Validate required fields exist

**Example:**
```python
import yaml

with open('specs/my_instrument.yaml', 'r') as f:
    spec = yaml.safe_load(f)

# spec is now a Python dict:
# {
#   'app_name': 'emfi_probe_v1',
#   'version': '1.0.0',
#   'platform': 'moku_pro',
#   'datatypes': [...]
# }
```

**Defaults Applied:**
- `platform` → `'moku_go'` if not specified
- `mapping_strategy` → `'type_clustering'` if not specified
- `version` → `'1.0.0'` if not specified

**Errors at This Stage:**
- YAML syntax errors (malformed YAML)
- Missing required fields (`app_name`, `datatypes`)

**See also:** [YAML Schema Reference](yaml_schema.md) for complete format specification.

---

### Stage 2: Pydantic Validation

**Tool:** Pydantic models (`BasicAppsRegPackage`, `DataTypeSpec`)

**Input:** Python dictionary from YAML parsing

**Process:**
1. Create `DataTypeSpec` objects for each signal in `datatypes` array
2. Validate each field against Pydantic schema:
   - Field types (string, int, enum)
   - Field constraints (min_length, max_length, ranges)
   - Enum values (platform, datatype, mapping_strategy)
   - Cross-field validation (min_value <= max_value)
3. Create `BasicAppsRegPackage` object containing all validated signals
4. Validate package-level constraints:
   - Unique signal names
   - Total bits <= 384 bits (12 registers × 32 bits)

**Example:**
```python
from forge.models.package import BasicAppsRegPackage

# Load and validate YAML
package = BasicAppsRegPackage.from_yaml('specs/my_instrument.yaml')

# If validation passes, package contains:
# - package.app_name: str
# - package.version: str
# - package.platform: Literal["moku_go", "moku_lab", "moku_pro", "moku_delta"]
# - package.datatypes: List[DataTypeSpec]
# - package.mapping_strategy: Literal["first_fit", "best_fit", "type_clustering"]
```

**Validation Rules:**

1. **Field Type Validation:**
   - `app_name`: string, 1-50 characters
   - `datatype`: must be valid BasicAppDataTypes enum value
   - `default_value`: must match type constraints (boolean for boolean, int for numeric)

2. **Range Validation:**
   - `default_value` must be within type's min/max from TYPE_REGISTRY
   - `min_value` must be <= `max_value` if both provided
   - UI constraints must be within type intrinsic limits

3. **Name Validation:**
   - Must start with letter
   - Only alphanumeric + underscore
   - No VHDL reserved words (`signal`, `entity`, `process`, etc.)
   - Unique across all signals

4. **Package-Level Validation:**
   - Total bits: sum(signal.bit_width) <= 384 bits
   - At least 1 signal defined

**Errors at This Stage:**
- Invalid field types
- Out-of-range values
- Duplicate signal names
- Unknown datatype enum values
- Bit limit exceeded

**See also:**
- `forge/models/package.py` - Pydantic model implementation
- [YAML Schema - Validation Rules](yaml_schema.md#validation-rules)

---

### Stage 3: Register Mapping

**Tool:** `BADRegisterMapper` (wraps core `RegisterMapper` from basic-app-datatypes)

**Input:** Validated `BasicAppsRegPackage` with list of typed signals

**Process:**
1. Extract signal list with types: `[(name, datatype), ...]`
2. Call `RegisterMapper.map(items, strategy=mapping_strategy)`
3. Mapper applies selected packing algorithm:
   - **first_fit:** Assign to first register with space (O(n))
   - **best_fit:** Assign to register with smallest remaining space (O(n²))
   - **type_clustering:** Group by bit width, then pack (O(n log n))
4. Mapper returns `List[RegisterMapping]` with CR assignments:
   - `cr_number`: 6-15 (which control register)
   - `bit_slice`: [MSB, LSB] bit range within register
   - `name`: signal name
   - `datatype`: BasicAppDataTypes enum

**Example:**
```python
# Generate mapping
mappings = package.generate_mapping()

# mappings is List[RegisterMapping]:
# [
#   RegisterMapping(name='output_voltage', datatype=..., cr_number=6, bit_slice=(31, 16)),
#   RegisterMapping(name='enable_output', datatype=..., cr_number=6, bit_slice=(15, 15)),
#   RegisterMapping(name='pulse_width', datatype=..., cr_number=7, bit_slice=(31, 16)),
# ]
```

**Packing Strategies:** See [Register Mapping Reference](register_mapping.md) for detailed algorithm explanations.

**Output:**
- **CR assignments:** Which register (6-15) each signal is assigned to
- **Bit slices:** Exact bit range [MSB, LSB] within each register
- **Efficiency metrics:** Total bits used, registers saved, packing efficiency %

**Errors at This Stage:**
- Register overflow (total bits > 384)
- Invalid type (not in TYPE_REGISTRY)

---

### Stage 4: Template Rendering

**Tool:** Jinja2 template engine

**Input:**
- Validated package with register mappings
- Platform specifications (clock frequency, name)
- Template files (`*_template.vhd`)

**Process:**

1. **Prepare Template Context:**
   ```python
   context = {
       'app_name': 'emfi_probe_v1',
       'platform_name': 'Moku:Pro',
       'clock_mhz': 1250,
       'signals': [...],  # List of signal dicts with metadata
       'register_map': {...},  # CR number -> signals mapping
       'generation_timestamp': '2025-11-03 12:00:00',
   }
   ```

2. **Render Shim Template:**
   - Template: `templates/custom_inst_shim_template.vhd`
   - Generates entity declaration
   - Generates signal unpacking logic (CR → typed signals)
   - Injects platform constants (clock frequency)

3. **Render Main Template:**
   - Template: `templates/custom_inst_main_template.vhd`
   - Generates entity declaration (matches shim outputs)
   - Generates skeleton user logic with TODO markers
   - Includes signal descriptions in comments

4. **Generate JSON Metadata:**
   - `manifest.json` - Package contract (see [Manifest Schema](manifest_schema.md))
   - `control_registers.json` - Register-centric view

**Template Variables:**

Key variables available in Jinja2 templates:

| Variable | Type | Description |
|----------|------|-------------|
| `app_name` | string | Application name (e.g., `"emfi_probe_v1"`) |
| `platform_name` | string | Human-readable platform (e.g., `"Moku:Pro"`) |
| `clock_mhz` | int | Clock frequency in MHz (125, 500, 1250, 5000) |
| `signals` | list | List of signal dicts with metadata |
| `register_map` | dict | CR number → signals mapping |
| `generation_timestamp` | string | ISO timestamp of generation |
| `has_voltage` | bool | True if any voltage types used |
| `has_time` | bool | True if any time types used |

**Signal Dict Structure:**
```python
{
    'name': 'output_voltage',
    'vhdl_type': 'signed',
    'vhdl_base_type': 'signed',
    'description': 'Output voltage setpoint',
    'default_value': 0,
    'bit_width': 16,
    'cr_number': 6,
    'bit_range': '(31 downto 16)',  # VHDL slice notation
    'bit_position': None,  # For single-bit signals only
    'is_boolean': False,
    'is_voltage': True,
    'is_time': False,
    'unit': 'mV',
}
```

**Template Syntax Example:**
```jinja2
-- Generate entity declaration
entity {{ app_name }}_shim is
  port (
    clk : in std_logic;
    control_registers : in control_registers_t;
    {% for signal in signals %}
    {{ signal.name }}_out : out {{ signal.vhdl_type }}({{ signal.bit_width - 1 }} downto 0);
    {% endfor %}
  );
end entity {{ app_name }}_shim;

-- Generate signal unpacking
architecture rtl of {{ app_name }}_shim is
begin
  {% for signal in signals %}
  -- {{ signal.description }}
  {{ signal.name }}_out <= {{ signal.vhdl_base_type }}(control_registers.reg{{ signal.cr_number }}{{ signal.bit_range }});
  {% endfor %}
end architecture rtl;
```

---

### Stage 5: Artifact Generation

**Output Directory Structure:**
```
output/<app_name>/
├── <app_name>_shim.vhd          # VHDL shim entity
├── <app_name>_main.vhd          # VHDL main template (user logic)
├── manifest.json                 # Package contract
└── control_registers.json        # Register-centric view
```

---

## VHDL File Structure

### Shim File (`<app>_shim.vhd`)

**Purpose:** Interface layer between control registers and typed signals.

**Contents:**

1. **Library Declarations:**
   ```vhdl
   library ieee;
   use ieee.std_logic_1164.all;
   use ieee.numeric_std.all;
   use work.basic_types_pkg.all;  -- Type definitions
   ```

2. **Entity Declaration:**
   ```vhdl
   entity emfi_probe_v1_shim is
     port (
       clk : in std_logic;
       reset : in std_logic;

       -- Control registers input (from network)
       control_registers : in control_registers_t;

       -- Typed signal outputs (to main logic)
       output_voltage_out : out signed(15 downto 0);
       enable_output_out : out std_logic;
       pulse_width_out : out unsigned(15 downto 0)
     );
   end entity emfi_probe_v1_shim;
   ```

3. **Signal Unpacking Architecture:**
   ```vhdl
   architecture rtl of emfi_probe_v1_shim is
   begin
     -- Extract typed signals from control registers

     -- output_voltage: CR6, bits 31-16 (voltage_output_05v_s16)
     output_voltage_out <= signed(control_registers.reg6(31 downto 16));

     -- enable_output: CR6, bit 15 (boolean)
     enable_output_out <= control_registers.reg6(15);

     -- pulse_width: CR7, bits 31-16 (pulse_duration_ns_u16)
     pulse_width_out <= unsigned(control_registers.reg7(31 downto 16));

   end architecture rtl;
   ```

**Key Features:**
- **Type-safe conversions:** `signed()`, `unsigned()` casts based on type metadata
- **MSB-aligned packing:** Signals packed from MSB downward
- **Comments:** Each signal includes description and type information
- **Platform constants:** Clock frequency available as constant

---

### Main File (`<app>_main.vhd`)

**Purpose:** Template for user logic implementation.

**Contents:**

1. **Entity Declaration (matches shim outputs):**
   ```vhdl
   entity emfi_probe_v1_main is
     port (
       clk : in std_logic;
       reset : in std_logic;

       -- Typed signals from shim
       output_voltage : in signed(15 downto 0);  -- ±5V, 16-bit
       enable_output : in std_logic;             -- boolean flag
       pulse_width : in unsigned(15 downto 0);   -- nanoseconds, 16-bit

       -- Hardware interface (user-defined)
       dac_out : out signed(15 downto 0);
       trigger_out : out std_logic
     );
   end entity emfi_probe_v1_main;
   ```

2. **Architecture Template:**
   ```vhdl
   architecture rtl of emfi_probe_v1_main is
     -- TODO: Add internal signals here

   begin

     -- TODO: Implement user logic here
     --
     -- Example:
     --   dac_out <= output_voltage when enable_output = '1' else (others => '0');

   end architecture rtl;
   ```

**User Workflow:**
1. Modify `_main.vhd` to implement application logic
2. Use typed signals from shim (no manual bit-slicing)
3. Connect to hardware interfaces (DACs, ADCs, etc.)
4. Compile and synthesize for target platform

**DO NOT MODIFY `_shim.vhd`** - Regenerate if YAML changes.

---

## Platform-Specific Constants

### Clock Frequency Injection

Each platform has a different clock frequency. The generator injects platform-specific constants:

```vhdl
-- Platform: Moku:Pro (1.25 GHz)
constant CLOCK_FREQ_MHZ : integer := 1250;
constant CLOCK_PERIOD_NS : real := 0.8;
```

**Platform Specifications:**

| Platform | Clock Freq | Period | Constant Injected |
|----------|-----------|--------|-------------------|
| Moku:Go | 125 MHz | 8.0 ns | `CLOCK_FREQ_MHZ := 125` |
| Moku:Lab | 500 MHz | 2.0 ns | `CLOCK_FREQ_MHZ := 500` |
| Moku:Pro | 1.25 GHz | 0.8 ns | `CLOCK_FREQ_MHZ := 1250` |
| Moku:Delta | 5 GHz | 0.2 ns | `CLOCK_FREQ_MHZ := 5000` |

**Usage in User Logic:**
```vhdl
-- Convert pulse width (nanoseconds) to clock cycles
-- pulse_width is in nanoseconds (from user)
-- CLOCK_PERIOD_NS is platform-specific
cycles <= pulse_width / CLOCK_PERIOD_NS;
```

**Note:** Platform-aware conversions are automatic when using BasicAppDataTypes. The Python `TypeConverter` and VHDL constants ensure correct behavior across all platforms.

---

## Generated Artifacts

### 1. `<app>_shim.vhd`

- **Purpose:** Control register → typed signal interface
- **Size:** ~100-200 lines (depends on signal count)
- **Regenerate:** Yes, whenever YAML changes
- **User edits:** NO (auto-generated)

### 2. `<app>_main.vhd`

- **Purpose:** User logic template
- **Size:** ~50-100 lines (skeleton)
- **Regenerate:** Only if missing (preserves user edits)
- **User edits:** YES (implement application logic here)

### 3. `manifest.json`

- **Purpose:** Package contract for deployment/docs/debug
- **Size:** ~100-500 lines (depends on signal count)
- **Format:** JSON
- **Consumers:** deployment-context, docgen-context, hardware-debug-context

**See:** [Manifest Schema Reference](manifest_schema.md)

### 4. `control_registers.json`

- **Purpose:** Register-centric view for debugging
- **Size:** ~50-200 lines
- **Format:** JSON
- **Consumers:** Hardware debugging tools, register inspection

**Example:**
```json
{
  "control_registers": {
    "6": {
      "signals": ["output_voltage", "enable_output"],
      "bit_map": {
        "31-16": "output_voltage (voltage_output_05v_s16)",
        "15": "enable_output (boolean)"
      }
    }
  }
}
```

---

## Customizing Templates

### Template Locations

**Default templates:**
```
forge/templates/
├── custom_inst_shim_template.vhd
└── custom_inst_main_template.vhd
```

### Modifying Templates

**For advanced users:**

1. **Copy templates:**
   ```bash
   cp forge/templates/custom_inst_shim_template.vhd my_templates/
   ```

2. **Edit Jinja2 syntax:**
   - Use `{{ variable }}` for substitution
   - Use `{% for ... %}` for loops
   - Use `{% if ... %}` for conditionals

3. **Specify custom template directory:**
   ```bash
   python -m forge.generate_package \
       specs/my_instrument.yaml \
       --template-dir my_templates/ \
       --output-dir output/
   ```

**Warning:** Custom templates may break with forge updates. Use at your own risk.

---

## Command-Line Usage

### Generate Package

```bash
# Basic usage
uv run python -m forge.generate_package specs/my_instrument.yaml

# Specify output directory
uv run python -m forge.generate_package \
    specs/my_instrument.yaml \
    --output-dir output/my_instrument

# Verbose mode
uv run python -m forge.generate_package \
    specs/my_instrument.yaml \
    --verbose
```

### Validation Only

```bash
# Validate YAML without generating files
uv run python -m forge.validate_yaml specs/my_instrument.yaml
```

---

## Error Handling

### Common Generation Errors

**1. YAML Syntax Errors:**
```
yaml.scanner.ScannerError: while scanning a simple key
  in "specs/my_instrument.yaml", line 5, column 1
```
**Fix:** Check YAML syntax (indentation, colons, quotes)

**2. Validation Errors:**
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for BasicAppsRegPackage
datatypes.0.default_value
  default_value 100000 above max 32767 for type voltage_output_05v_s16
```
**Fix:** Adjust default_value to be within type's valid range

**3. Register Overflow:**
```
ValueError: Total bits (400) exceeds 384-bit limit (12 registers × 32 bits)
```
**Fix:** Reduce signal count or use smaller bit widths

**See also:** [Troubleshooting - Code Generation Issues](../guides/troubleshooting.md#code-generation-issues)

---

## Related Documentation

- **[YAML Schema Reference](yaml_schema.md)** - Input format specification
- **[Type System Reference](type_system.md)** - Available datatypes
- **[Register Mapping Reference](register_mapping.md)** - Packing algorithms
- **[Manifest Schema Reference](manifest_schema.md)** - Output format
- **[Python API Reference](python_api.md)** - Programmatic generation
- **[Getting Started Guide](../guides/getting_started.md)** - Tutorial walkthrough
- **[Troubleshooting](../guides/troubleshooting.md)** - Common issues and fixes

---

## Implementation Files

**Pipeline Implementation:**
- `forge/generator/codegen.py` - Main generation pipeline
- `forge/models/package.py` - Pydantic models
- `forge/models/mapper.py` - Register mapper wrapper
- `forge/generator/type_utilities.py` - Type conversion helpers

**Templates:**
- `forge/templates/custom_inst_shim_template.vhd` - Shim template
- `forge/templates/custom_inst_main_template.vhd` - Main template

**Core Mapping:**
- `libs/basic-app-datatypes/basic_app_datatypes/mapper.py` - Core algorithm

---

**Key Takeaway:** The VHDL generation pipeline transforms YAML specs into type-safe VHDL code automatically. The process is: YAML → Pydantic validation → Register mapping → Jinja2 rendering → VHDL files + manifest.json. Users only need to author YAML and implement logic in `_main.vhd`—all register packing and type conversions are automatic.

---

*Last Updated: 2025-11-03*
