# moku-instrument-forge Documentation

**Version:** 2.0
**Last Updated:** 2025-11-03

---

## 📍 Quick Links

**New Users:**
- [Getting Started (30-min tutorial)](guides/getting_started.md) ⭐ **START HERE**
- [User Guide (comprehensive)](guides/user_guide.md)
- [Troubleshooting](guides/troubleshooting.md)

**Reference:**
- [Type System Overview](reference/type_system.md)
- [YAML Schema](reference/yaml_schema.md)
- [Register Mapping](reference/register_mapping.md)
- [Python API](reference/python_api.md)

**Examples:**
- [Minimal Probe (3 signals)](examples/minimal_walkthrough.md)
- [Multi-Channel (6 signals)](examples/multi_channel_walkthrough.md)
- [Common Patterns](examples/common_patterns.md)

**Architecture:**
- [System Overview](architecture/overview.md)
- [Agent System](architecture/agent_system.md)
- [Submodule Integration](architecture/submodule_integration.md)

---

## What is moku-instrument-forge?

**moku-instrument-forge** is a YAML-to-VHDL code generation toolchain that transforms high-level instrument specifications into deployment-ready packages for Moku platforms (Go, Lab, Pro, Delta). It uses the **BasicAppDataTypes** type system (25 types: voltage, time, boolean) to provide type-safe register communication with automatic packing optimization, achieving **50-75% register savings** compared to manual approaches.

The forge automates YAML validation, VHDL code generation, register mapping, and deployment package creation, enabling hardware engineers and Python developers to build custom instruments **without manual register management**.

---

## Key Features

✅ **Type-Safe:** 25 predefined types with automatic validation
✅ **Efficient:** 50-75% register savings via automatic packing
✅ **Multi-Platform:** Supports Moku Go, Lab, Pro, Delta
✅ **Tested:** 69 tests passing, production-ready
✅ **Agent-Based:** 5 specialized agents for generation, deployment, documentation, debugging
✅ **Standards-Based:** YAML v2.0 schema, JSON manifests, Pydantic models

---

## Quick Start

**From zero to package in 3 commands:**

```bash
# 1. Validate your YAML spec
uv run python -m forge.validate_yaml specs/my_instrument.yaml

# 2. Generate VHDL + deployment package
uv run python -m forge.generate_package specs/my_instrument.yaml

# 3. Deploy to hardware (conceptual - requires CloudCompile integration)
# See deployment_guide.md for details
```

**New to forge?** Follow the [Getting Started Guide](guides/getting_started.md) for a complete 30-minute tutorial.

---

## Documentation Structure

```
docs/
├── README.md                    # 📍 You are here
│
├── guides/                      # USER-FACING GUIDES
│   ├── getting_started.md       # 30-min tutorial (zero → package)
│   ├── user_guide.md            # Comprehensive forge usage
│   ├── yaml_guide.md            # Writing YAML specs
│   ├── deployment_guide.md      # Hardware deployment
│   ├── migration_guide.md       # Manual registers → forge
│   └── troubleshooting.md       # Common issues + solutions
│
├── reference/                   # TECHNICAL REFERENCE
│   ├── type_system.md           # BasicAppDataTypes overview
│   ├── yaml_schema.md           # Complete YAML v2.0 spec
│   ├── register_mapping.md      # Packing algorithms
│   ├── manifest_schema.md       # manifest.json spec
│   ├── vhdl_generation.md       # Code generation pipeline
│   └── python_api.md            # Pydantic models API
│
├── architecture/                # DESIGN DOCUMENTS
│   ├── overview.md              # System architecture
│   ├── code_generation.md       # Generator internals
│   ├── agent_system.md          # 5 agents explained
│   ├── submodule_integration.md # Forge ↔ libs boundaries
│   └── design_decisions.md      # Design rationale
│
├── examples/                    # COMPLETE EXAMPLES
│   ├── minimal_probe.yaml       # Simplest spec (3 signals)
│   ├── minimal_walkthrough.md   # Line-by-line explanation
│   ├── multi_channel.yaml       # 6-signal example
│   ├── multi_channel_walkthrough.md  # Deep dive
│   └── common_patterns.md       # Best practices catalog
│
└── debugging/                   # DEBUGGING GUIDES
    ├── fsm_observer_pattern.md  # FSM debugging techniques
    ├── hardware_validation.md   # Oscilloscope workflows
    └── common_issues.md         # Debug cookbook
```

---

## Documentation Conventions

**Naming Conventions:**
- **Python/YAML:** `snake_case` (e.g., `output_voltage`, `pulse_width`)
- **Types:** `category_subcategory_bitwidth` (e.g., `voltage_output_05v_s16`, `time_milliseconds_u16`)
- **Classes:** `PascalCase` (e.g., `BasicAppsRegPackage`, `DataTypeSpec`)
- **Control Registers:** `CR6`-`CR15` (10 available registers, 32-bit each)

**File Formats:**
- **YAML v2.0:** Input specification format
- **JSON:** manifest.json, control_registers.json (generated outputs)
- **VHDL:** Generated hardware description files
- **Python:** Pydantic models, type converters

**Links:**
- All relative paths (e.g., `../reference/type_system.md`)
- Work from all documentation locations

---

## Submodule Documentation

The forge delegates to three specialized libraries (git submodules):

### 📚 **basic-app-datatypes** - Type System
**Location:** `libs/basic-app-datatypes/`
**Documentation:** [`llms.txt`](../libs/basic-app-datatypes/llms.txt), [`README.md`](../libs/basic-app-datatypes/README.md)
**Provides:** 25 types (voltage, time, boolean), type converters, registry

### 🔧 **moku-models** - Platform Specifications
**Location:** `libs/moku-models/`
**Documentation:** [`MOKU_PLATFORM_SPECIFICATIONS.md`](../libs/moku-models/docs/MOKU_PLATFORM_SPECIFICATIONS.md), [`routing_patterns.md`](../libs/moku-models/docs/routing_patterns.md)
**Provides:** Hardware specs (Go/Lab/Pro/Delta), MCC routing patterns

### ⚡ **riscure-models** - Probe Hardware
**Location:** `libs/riscure-models/`
**Documentation:** [`docs/probes/`](../libs/riscure-models/docs/probes/)
**Provides:** Probe specifications, datasheets

**See:** [Submodule Integration Guide](architecture/submodule_integration.md) for details on how forge uses these libraries.

---

## Support

**Questions or Issues?**
- Check [Troubleshooting Guide](guides/troubleshooting.md)
- Review [Examples](examples/)
- File GitHub issue: [moku-instrument-forge/issues](https://github.com/liquidinstruments/moku-instrument-forge/issues)

**Contributing:**
- See [Design Decisions](architecture/design_decisions.md) for architecture rationale
- Review [Agent System](architecture/agent_system.md) for workflow automation
- Follow existing patterns in [examples/](examples/)

---

## Version History

**v2.0.0** (2025-11-03)
- Complete documentation suite (28 files)
- BasicAppDataTypes type system (25 types)
- Automatic register packing (50-75% savings)
- 5-agent architecture (forge, deployment, docgen, hardware-debug, workflow-coordinator)
- Multi-platform support (Go, Lab, Pro, Delta)
- Production-ready (69 tests passing)

---

**Ready to begin?** Start with the [Getting Started Guide](guides/getting_started.md) →
