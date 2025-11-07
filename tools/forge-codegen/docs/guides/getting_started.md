# Getting Started with moku-instrument-forge

**Goal:** Go from zero to deployed hardware package in 30 minutes

**Audience:** Complete beginners (hardware engineers OR Python developers)

---

## Prerequisites

Before starting, ensure you have:

- ✅ **Python 3.10+** (`python --version`)
- ✅ **uv** package manager ([install guide](https://github.com/astral-sh/uv))
- ✅ **git** with submodule support
- ✅ **Moku device** (Go, Lab, Pro, or Delta) - optional for initial learning
- ✅ **Basic YAML knowledge** (or willingness to learn by example)

**Platform Support:**
- macOS, Linux, Windows (WSL recommended)
- No VHDL toolchain required (CloudCompile handles synthesis)

---

## Step 1: Installation

Clone the repository with submodules:

```bash
# Clone with all submodules (required!)
git clone --recursive https://github.com/liquidinstruments/moku-instrument-forge.git
cd moku-instrument-forge

# If you forgot --recursive, fetch submodules now:
git submodule update --init --recursive

# Install dependencies with uv
uv sync

# Verify installation
uv run python -c "from forge.models.package import BasicAppsRegPackage; print('✅ Forge installed!')"
```

**Expected output:** `✅ Forge installed!`

---

## Step 2: Your First Spec

Create a minimal YAML specification. This is the simplest possible instrument: a voltage output with pulse control.

**Create:** `specs/minimal_probe.yaml`

```yaml
app_name: minimal_probe
version: 1.0.0
description: My first custom instrument
platform: moku_go

datatypes:
  - name: output_voltage
    datatype: voltage_output_05v_s16
    description: Output voltage setpoint
    default_value: 0
    units: V

  - name: enable_output
    datatype: boolean
    description: Enable output driver
    default_value: false

  - name: pulse_width
    datatype: pulse_duration_ms_u16
    description: Pulse width in milliseconds
    default_value: 100
    units: ms
```

**What's happening here?**

| Field | Value | Meaning |
|-------|-------|---------|
| `app_name` | `minimal_probe` | Your instrument name (snake_case) |
| `version` | `1.0.0` | Semantic version |
| `platform` | `moku_go` | Target hardware (go/lab/pro/delta) |
| `datatypes` | Array | List of control signals |

**Each signal has:**
- **`name`**: Your variable name (e.g., `output_voltage`)
- **`datatype`**: Type from BasicAppDataTypes (e.g., `voltage_output_05v_s16`)
- **`description`**: Human-readable explanation
- **`default_value`**: Initial value on boot
- **`units`**: Display units (optional, for documentation)

**Type Selection:**
- `voltage_output_05v_s16`: 16-bit signed voltage (±5V range, DAC output)
- `boolean`: 1-bit flag (true or false)
- `pulse_duration_ms_u16`: 16-bit unsigned milliseconds (0-65535 ms)

**See:** [Type System Overview](../reference/type_system.md) for all 25 types.

---

## Step 3: Validate Your Spec

Before generating code, validate the YAML:

```bash
uv run python -m forge.validate_yaml specs/minimal_probe.yaml
```

**Expected output:**
```
✅ YAML syntax valid
✅ All datatypes recognized (3/3)
✅ Default values in range
✅ Platform 'moku_go' supported
✅ Validation passed!
```

**If you see errors:**
- Check YAML syntax (indentation, colons)
- Verify datatype names match exactly (case-sensitive)
- Ensure default values are within type ranges
- See [Troubleshooting Guide](troubleshooting.md)

---

## Step 4: Generate Package

Generate VHDL and deployment artifacts:

```bash
uv run python -m forge.generate_package specs/minimal_probe.yaml
```

**Expected output:**
```
🔍 Loading YAML spec...
✅ Validated 3 datatypes
📊 Mapping to control registers...
   Strategy: type_clustering (default)
   Signals: 3
   Registers: 2 (33 bits / 64 bits = 52% efficient)
📝 Generating VHDL...
   ✅ minimal_probe_shim.vhd
   ✅ minimal_probe_main.vhd
📦 Writing manifest.json
📋 Writing control_registers.json
✅ Package generated: output/minimal_probe/
```

**Generated files:**
```
output/minimal_probe/
├── manifest.json              # Deployment metadata
├── control_registers.json     # Register mapping
├── minimal_probe_shim.vhd     # Control register interface
└── minimal_probe_main.vhd     # Your instrument logic (template)
```

---

## Step 5: Inspect Outputs

### 5.1 Register Mapping

Open `output/minimal_probe/control_registers.json`:

```json
{
  "registers": [
    {
      "register_number": 6,
      "signals": [
        {
          "name": "output_voltage",
          "datatype": "voltage_output_05v_s16",
          "bit_range": "15:0",
          "bits_used": 16
        },
        {
          "name": "pulse_width",
          "datatype": "pulse_duration_ms_u16",
          "bit_range": "31:16",
          "bits_used": 16
        }
      ],
      "bits_used": 32
    },
    {
      "register_number": 7,
      "signals": [
        {
          "name": "enable_output",
          "datatype": "boolean",
          "bit_range": "0:0",
          "bits_used": 1
        }
      ],
      "bits_used": 1
    }
  ],
  "total_registers": 2,
  "efficiency": 0.52
}
```

**Key insights:**
- **CR6**: Packs `output_voltage` (16 bits) + `pulse_width` (16 bits) = 32/32 bits (100% full!)
- **CR7**: `enable_output` (1 bit) = 1/32 bits
- **Total**: 2 registers instead of 3 (33% register savings)
- **Efficiency**: 52% overall (33 bits used / 64 bits allocated)

**Why is this efficient?**
The `type_clustering` strategy groups signals of similar size together, minimizing wasted bits. See [Register Mapping](../reference/register_mapping.md) for algorithm details.

### 5.2 VHDL Shim

Open `output/minimal_probe/minimal_probe_shim.vhd` (excerpt):

```vhdl
-- Auto-generated control register interface
-- DO NOT EDIT: Regenerate from YAML

entity minimal_probe_shim is
  port (
    -- Control register inputs (from Moku framework)
    control_6_in  : in  std_logic_vector(31 downto 0);
    control_7_in  : in  std_logic_vector(31 downto 0);

    -- Unpacked signals (to your instrument logic)
    output_voltage : out signed(15 downto 0);      -- ±5V
    enable_output  : out std_logic;                -- 0/1
    pulse_width    : out unsigned(15 downto 0);    -- 0-65535 ms

    -- ... clock, reset, etc.
  );
end entity;
```

**This shim:**
- Reads CR6 and CR7 from the Moku framework
- Unpacks bits into typed VHDL signals
- Handles type conversion (voltage scaling happens in your logic or Python)

### 5.3 Manifest

Open `output/minimal_probe/manifest.json` (excerpt):

```json
{
  "app_name": "minimal_probe",
  "version": "1.0.0",
  "platform": "moku_go",
  "datatypes": [
    {
      "name": "output_voltage",
      "datatype": "voltage_output_05v_s16",
      "description": "Output voltage setpoint",
      "default_value": 0,
      "units": "V",
      "register_number": 6,
      "bit_range": "15:0"
    },
    ...
  ],
  "efficiency": {
    "total_bits_used": 33,
    "total_bits_allocated": 64,
    "percentage": 0.52,
    "registers_used": 2,
    "registers_saved": 1
  }
}
```

**This manifest is the source of truth** for deployment, documentation, and control software. See [Manifest Schema](../reference/manifest_schema.md).

---

## Step 6: Deploy to Hardware (Conceptual)

**Note:** Automated deployment requires CloudCompile integration (work in progress). This section shows the conceptual workflow.

```bash
# 1. Connect to your Moku device
# (Use Moku desktop app or Python moku module)

# 2. Upload VHDL to CloudCompile
# CloudCompile synthesizes VHDL → bitstream for your platform

# 3. Deploy bitstream to Moku
# Moku loads bitstream into FPGA

# 4. Initialize control registers from manifest
# Python: write default_value to each CR6, CR7
```

**For now, you have:**
- ✅ Valid VHDL ready for synthesis
- ✅ Deployment metadata (manifest.json)
- ✅ Register mapping (control_registers.json)

**See:** [Deployment Guide](deployment_guide.md) for detailed workflow when CloudCompile is integrated.

---

## Step 7: Verify (Simulation)

While automated deployment is pending, you can verify the package structure:

```bash
# Check all files generated
ls -R output/minimal_probe/

# Validate manifest against package contract
uv run python -c "
from forge.models.package import BasicAppsRegPackage
pkg = BasicAppsRegPackage.from_yaml('specs/minimal_probe.yaml')
print(f'✅ Package valid: {pkg.app_name} v{pkg.version}')
print(f'📊 Signals: {len(pkg.datatypes)}')
print(f'📦 Registers: {len(pkg.register_mappings)}')
"
```

**Expected output:**
```
✅ Package valid: minimal_probe v1.0.0
📊 Signals: 3
📦 Registers: 2
```

**Python Control (Future):**

When deployed, you'll control the instrument via Python:

```python
from moku.instruments import CustomInstrument

# Connect to deployed instrument
instr = CustomInstrument('192.168.1.100', 'minimal_probe')

# Write control registers (values in physical units)
instr.set_parameter('output_voltage', 2.5)    # 2.5V
instr.set_parameter('enable_output', True)    # Enable
instr.set_parameter('pulse_width', 500)       # 500ms

# Read back (verify)
print(instr.get_parameter('output_voltage'))  # 2.5
```

**See:** [Python API Reference](../reference/python_api.md) for details.

---

## Step 8: Next Steps

🎉 **Congratulations!** You've generated your first instrument package.

**Where to go from here:**

### Learn More
- **[User Guide](user_guide.md)** - Comprehensive forge usage
- **[YAML Guide](yaml_guide.md)** - Writing specs in depth
- **[Type System](../reference/type_system.md)** - All 25 types explained

### Explore Examples
- **[Minimal Walkthrough](../examples/minimal_walkthrough.md)** - Line-by-line explanation of this example
- **[Multi-Channel Example](../examples/multi_channel_walkthrough.md)** - 6-signal spec with register packing
- **[Common Patterns](../examples/common_patterns.md)** - Best practices catalog

### Advanced Topics
- **[Register Mapping Algorithms](../reference/register_mapping.md)** - first_fit vs type_clustering
- **[VHDL Generation Pipeline](../reference/vhdl_generation.md)** - Template internals
- **[Agent System](../architecture/agent_system.md)** - Automated workflows

### Troubleshooting
- **[Common Issues](troubleshooting.md)** - Validation errors, generation failures
- **[FSM Debugging](../debugging/fsm_observer_pattern.md)** - Hardware debug techniques

---

## Summary

**What you learned:**

1. ✅ **Install forge** with uv and submodules
2. ✅ **Write YAML spec** with 3 signals (voltage, boolean, time)
3. ✅ **Validate spec** using forge tools
4. ✅ **Generate package** (VHDL + manifest + register mapping)
5. ✅ **Inspect outputs** (understand register packing)
6. ✅ **Conceptual deployment** (ready for CloudCompile integration)

**Key takeaways:**

- 🎯 **Type-safe:** BasicAppDataTypes prevents type errors
- 📦 **Efficient:** Automatic packing (2 registers instead of 3)
- 🚀 **Simple:** YAML → VHDL in seconds
- 🔧 **Ready:** Deployment-ready package with metadata

**Time invested:** ~30 minutes

**What you built:** A complete voltage output instrument with pulse control, ready for deployment.

---

**Questions?** See [Troubleshooting](troubleshooting.md) or file a [GitHub issue](https://github.com/liquidinstruments/moku-instrument-forge/issues).

**Ready for more?** Continue to the [User Guide](user_guide.md) →
