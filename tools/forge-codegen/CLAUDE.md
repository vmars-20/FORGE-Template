# CLAUDE.md

## Project Overview

**moku-instrument-forge-codegen** is a YAML→VHDL code generation framework for Moku FPGA custom instruments with integrated type-safe register serialization.

**Purpose:** Automate the creation of production-ready VHDL firmware from human-friendly YAML specifications, eliminating manual register management and reducing development time from weeks to hours.

**Repository:** https://github.com/sealablab/moku-instrument-forge-codegen

**Part of:** [moku-instrument-forge-mono-repo](https://github.com/sealablab/moku-instrument-forge-mono-repo) (monorepo orchestrator)

---

## Quick Start

```bash
# Install
cd moku-instrument-forge-codegen/
pip install -e .

# Generate VHDL
python -m forge_codegen.generator.codegen spec.yaml --output-dir generated/

# Run tests
pytest tests/
```

---

## Architecture

### Package Structure

```
forge_codegen/
├── basic_serialized_datatypes/  # Type system & register packing (internal)
│   ├── types.py                 # BasicAppDataTypes enum (23 types)
│   ├── metadata.py              # TYPE_REGISTRY (bit widths, ranges)
│   ├── mapper.py                # RegisterMapper (packing algorithm)
│   ├── converters.py            # TypeConverter (Python ↔ VHDL)
│   ├── time.py                  # PulseDuration classes
│   └── voltage.py               # Voltage utilities
├── generator/                   # YAML → VHDL code generation
│   ├── codegen.py               # Main generator entry point
│   └── type_utilities.py        # VHDL package generator (frozen)
├── models/                      # Pydantic data models
│   ├── app_spec.py              # CustomInstrumentApp (YAML parser)
│   ├── mapper.py                # BADRegisterMapper (Pydantic wrapper)
│   ├── package.py               # BasicAppsRegPackage (register bundle)
│   └── register.py              # AppRegister (legacy compatibility)
├── templates/                   # Jinja2 VHDL templates
│   ├── main.vhd.j2              # Application logic template
│   └── shim.vhd.j2              # Register interface template
└── vhdl/                        # Frozen VHDL type packages (v1.0.0)
    ├── basic_app_types_pkg.vhd
    ├── basic_app_voltage_pkg.vhd
    └── basic_app_time_pkg.vhd
```

### Key Design Decision: Flattened basic_serialized_datatypes

**Why internal, not a separate library?**

The `basic_serialized_datatypes` package is tightly coupled serialization internals, not a standalone library:

1. **Tight coupling:** Version-locked with code generator (breaking changes must stay in sync)
2. **No external users:** Only used by forge-codegen
3. **Complexity encapsulation:** Application developers work with volts/nanoseconds, not serialization bits
4. **Simplified maintenance:** Single repo, single version, no git submodule overhead

**What it provides:**
- 23-type system (voltage, time, boolean)
- Automatic register packing algorithm (50-75% space savings)
- Python ↔ VHDL conversions
- Type metadata registry

---

## Core Concepts

### 1. Type System (23 Types)

**Voltage Types (12):**
- Output: `voltage_output_05v_s16` (±5V, 16-bit signed)
- Input: `voltage_input_20v_s16` (±20V), `voltage_input_25v_s16` (±25V)

**Time Types (10):**
- `pulse_duration_ns_u16` (nanoseconds, 16-bit unsigned)
- `pulse_duration_us_u16` (microseconds)
- `pulse_duration_ms_u16` (milliseconds)
- `pulse_duration_s_u16` (seconds)

**Boolean Types (1):**
- `boolean` (1-bit)

**Design principle:** Fixed bit widths for deterministic register packing. User-friendly units (volts, nanoseconds) instead of raw bits.

### 2. Automatic Register Packing

**Problem:** Moku custom instruments have 12 control registers (CR0-CR11), each 32-bit. Manually packing signals is error-prone.

**Solution:** `RegisterMapper` automatically packs typed signals into minimal register space.

**Example:**
```python
items = [
    ("intensity", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),  # 16 bits
    ("arm_probe", BasicAppDataTypes.BOOLEAN),                 # 1 bit
    ("duration", BasicAppDataTypes.PULSE_DURATION_NS_U16),    # 16 bits
]
mapper = RegisterMapper()
mappings, report = mapper.map_registers(items)
# Result: Packed into 2 registers (vs 3 manual)
# Efficiency: 43.75% (vs 25% manual)
```

**Algorithm:** First-Fit Decreasing bin packing with 32-bit register bins.

### 3. YAML → VHDL Generation

**Pipeline:**
1. **Parse YAML** → `CustomInstrumentApp` Pydantic model
2. **Validate types** → Check against TYPE_REGISTRY
3. **Pack registers** → RegisterMapper creates bit assignments
4. **Render templates** → Jinja2 generates VHDL (shim + main)
5. **Write files** → Output production-ready VHDL

**Generated files:**
- `<app_name>_custom_inst_shim.vhd` - Register interface (MCC ↔ custom logic)
- `<app_name>_custom_inst_main.vhd` - Application logic template (user fills in)

### 4. Frozen VHDL Packages

**Critical design decision:** VHDL type packages are **FROZEN** (v1.0.0, committed, NEVER regenerated).

**Why frozen?**
- Stability: Applications depend on consistent type definitions
- Version control: VHDL is committed, not generated at build time
- Compatibility: Old apps continue to work without regeneration

**Packages:**
- `basic_app_types_pkg.vhd` - Type constants and bit widths
- `basic_app_voltage_pkg.vhd` - Voltage conversion functions
- `basic_app_time_pkg.vhd` - Time conversion functions

---

## Usage Examples

### Complete YAML → VHDL Workflow

**1. Create YAML spec:**
```yaml
app_name: DS1140_PD
platform: moku_go

registers:
  - name: arm_probe
    datatype: boolean
    description: Arm the EMFI probe
    default_value: false

  - name: intensity
    datatype: voltage_output_05v_s16
    description: Pulse intensity
    default_value: 2.5  # volts

  - name: duration
    datatype: pulse_duration_ns_u16
    description: Pulse duration
    default_value: 500  # nanoseconds
```

**2. Generate VHDL:**
```bash
python -m forge_codegen.generator.codegen DS1140_PD_spec.yaml --output-dir generated/
```

**3. Review generated files:**
```
generated/
├── DS1140_PD_custom_inst_shim.vhd    # Register interface (ready to use)
└── DS1140_PD_custom_inst_main.vhd    # Application logic (fill in FSM)
```

### Programmatic Usage

```python
from forge_codegen.basic_serialized_datatypes import (
    BasicAppDataTypes,
    TYPE_REGISTRY,
    RegisterMapper
)
from forge_codegen.models.package import BasicAppsRegPackage, DataTypeSpec

# Define register interface
datatypes = [
    DataTypeSpec(
        name="arm_probe",
        datatype=BasicAppDataTypes.BOOLEAN,
        description="Arm EMFI probe",
        default_value=False
    ),
    DataTypeSpec(
        name="intensity",
        datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
        description="Pulse intensity (volts)",
        default_value=2.5,
        min_value=0.0,
        max_value=5.0
    ),
]

# Create package (auto-packs registers)
package = BasicAppsRegPackage(
    name="DS1140_PD",
    datatypes=datatypes
)

# Get register mapping report
print(f"Registers used: {package.mapping_report.registers_used}/12")
print(f"Efficiency: {package.mapping_report.efficiency_percent:.1f}%")

# Export to control registers (for MokuConfig)
control_regs = package.to_control_registers()
```

---

## Adding New Types

**When to add a new type:**
- New hardware with different voltage ranges
- Need for different bit widths (e.g., 8-bit, 24-bit)
- New physical units (frequency, phase, etc.)

**Steps:**

1. **Add to enum** (`basic_serialized_datatypes/types.py`):
```python
class BasicAppDataTypes(str, Enum):
    FREQUENCY_MHZ_U16 = "frequency_mhz_u16"
```

2. **Add metadata** (`basic_serialized_datatypes/metadata.py`):
```python
TYPE_REGISTRY[BasicAppDataTypes.FREQUENCY_MHZ_U16] = TypeMetadata(
    bit_width=16,
    signed=False,
    category="frequency",
    description="Frequency in MHz (0-65535 MHz)",
    voltage_range=None,
    time_unit=None,
    units="MHz"
)
```

3. **Add converter** (`basic_serialized_datatypes/converters.py`):
```python
def frequency_mhz_u16_to_bits(self, freq_mhz: float) -> int:
    if not (0 <= freq_mhz <= 65535):
        raise ValueError(f"Frequency {freq_mhz} MHz out of range [0, 65535]")
    return int(freq_mhz)
```

4. **Add VHDL function** (if needed, to frozen package):
```vhdl
-- In basic_app_types_pkg.vhd
function convert_frequency_mhz_u16(freq_raw : std_logic_vector(15 downto 0))
    return real;
```

5. **Add tests** (`tests/test_integration.py`):
```python
def test_frequency_type():
    converter = TypeConverter()
    raw = converter.frequency_mhz_u16_to_bits(125.0)
    assert raw == 125
```

---

## Integration

### With moku-models (Platform Validation)

```python
from forge_codegen.basic_serialized_datatypes import BasicAppDataTypes, TYPE_REGISTRY
from moku_models import MOKU_GO_PLATFORM

# Get type metadata
voltage_type = BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
metadata = TYPE_REGISTRY[voltage_type]

# Get platform DAC specs
platform = MOKU_GO_PLATFORM
dac_output = platform.get_analog_output_by_id('OUT1')

# Validate compatibility
assert metadata.voltage_range == "±5V"
assert dac_output.voltage_range_vpp == 10.0
print("✓ Type compatible with platform")
```

### With riscure-models (Probe Safety)

```python
from moku_models import MOKU_GO_PLATFORM
from riscure_models import DS1120A_PLATFORM

# Get Moku output spec
moku_out = MOKU_GO_PLATFORM.get_analog_output_by_id('OUT1')

# Get probe input spec
probe_in = DS1120A_PLATFORM.get_port_by_id('digital_glitch')

# Validate voltage safety
ttl_voltage = 3.3
if probe_in.is_voltage_compatible(ttl_voltage):
    print("✓ Safe to connect Moku OUT1 (TTL) → DS1120A digital_glitch")
```

### With forge-vhdl (Reusable Components)

forge-codegen generates the register interface; forge-vhdl provides reusable VHDL components (FSMs, counters, pulse generators).

**Workflow:**
1. forge-codegen generates shim + main template
2. User fills in main template using forge-vhdl components
3. User synthesizes complete design

---

## Testing

**Test suite:** 69 tests covering:
- YAML parsing and validation
- Register mapping algorithm
- VHDL template rendering
- End-to-end pipeline
- Platform integration

**Run tests:**
```bash
pytest tests/                    # All tests
pytest tests/test_mapper.py      # Register mapping only
pytest tests/test_integration.py # End-to-end tests
```

**Coverage areas:**
- Type system validation
- Register packing efficiency
- VHDL syntax correctness
- Platform constant injection
- Error handling

---

## Development Workflow

```bash
# Clone and install
git clone https://github.com/sealablab/moku-instrument-forge-codegen.git
cd moku-instrument-forge-codegen/
pip install -e .

# Make changes
vim forge_codegen/basic_serialized_datatypes/types.py

# Run tests
pytest tests/

# Format code
black forge_codegen/
ruff check forge_codegen/

# Commit
git add .
git commit -m "Add frequency_mhz_u16 type"
git push origin main
```

---

## Common Tasks

### Query Type Metadata

```python
from forge_codegen.basic_serialized_datatypes import BasicAppDataTypes, TYPE_REGISTRY

for type_enum in BasicAppDataTypes:
    metadata = TYPE_REGISTRY[type_enum]
    print(f"{type_enum.value}: {metadata.bit_width} bits")
```

### Validate YAML Before Generation

```python
from forge_codegen.generator.codegen import load_yaml_spec

try:
    spec = load_yaml_spec("spec.yaml")
    print(f"✓ Valid spec: {spec['app_name']}")
except Exception as e:
    print(f"✗ Invalid spec: {e}")
```

### Get Register Efficiency Report

```python
from forge_codegen.models.package import BasicAppsRegPackage, DataTypeSpec
from forge_codegen.basic_serialized_datatypes import BasicAppDataTypes

datatypes = [
    DataTypeSpec(name="sig1", datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
    DataTypeSpec(name="sig2", datatype=BasicAppDataTypes.BOOLEAN),
]

package = BasicAppsRegPackage(name="Test", datatypes=datatypes)
report = package.mapping_report

print(f"Registers: {report.registers_used}/12")
print(f"Bits used: {report.bits_used}/{report.total_bits}")
print(f"Efficiency: {report.efficiency_percent:.1f}%")
```

---

## Platform Support

| Platform | Clock | ADC Range | DAC Range | Slots | Status |
|----------|-------|-----------|-----------|-------|--------|
| Moku:Go | 125 MHz | ±25V | ±5V | 2 | ✅ Supported |
| Moku:Lab | 500 MHz | ±5V | ±1V | 2 | ✅ Supported |
| Moku:Pro | 1.25 GHz | ±20V | ±5V | 4 | ✅ Supported |
| Moku:Delta | 5 GHz | ±20V | ±5V | 3 | ✅ Supported |

---

## Documentation Hierarchy

**3-tier system:**
1. **llms.txt** (~500-1000 tokens) - Quick reference for common tasks
2. **CLAUDE.md** (this file, ~3-5k tokens) - Authoritative guide
3. **docs/** - Specialized guides (getting started, troubleshooting, API reference)

**Progressive disclosure:** Start with llms.txt, escalate to CLAUDE.md, dive into docs/ as needed.

---

**Last Updated:** 2025-11-04
**Maintainer:** Sealab Team
**License:** MIT
**Repository:** https://github.com/sealablab/moku-instrument-forge-codegen
