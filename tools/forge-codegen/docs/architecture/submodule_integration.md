# Submodule Integration Architecture

**How moku-instrument-forge delegates to specialized libraries**

**Goal:** Maintain clear boundaries, avoid duplication, ensure single source of truth

---

## Table of Contents

1. [Submodule Philosophy](#submodule-philosophy)
2. [basic-app-datatypes](#basic-app-datatypes)
3. [moku-models](#moku-models)
4. [riscure-models](#riscure-models)
5. [Documentation Strategy](#documentation-strategy)
6. [Git Submodule Workflow](#git-submodule-workflow)
7. [Dependency Graph](#dependency-graph)
8. [Design Rationale](#design-rationale)

---

## Submodule Philosophy

### Core Principle: Single Source of Truth

**moku-instrument-forge** is a **code generation toolchain**, not a platform specification repository. It delegates all domain-specific knowledge to specialized libraries via git submodules.

**Why submodules?**
- ✅ **Reusability:** Libraries can be used by other projects
- ✅ **Versioning:** Each library has independent release cycle
- ✅ **Clarity:** Clear ownership of each knowledge domain
- ✅ **Maintainability:** Update specs without touching forge code
- ✅ **No Duplication:** One canonical source for each concept

**Mandate:** **Link, don't duplicate.** Forge documentation references submodule docs, never copies them.

---

## basic-app-datatypes

**Location:** `libs/basic-app-datatypes/`

**Repository:** [basic-app-datatypes](https://github.com/liquidinstruments/basic-app-datatypes)

### What It Provides

**Type System:**
- 25 predefined types (voltage, time, boolean)
- Fixed bit widths (1-32 bits)
- Physical unit mappings (volts, milliseconds, etc.)
- Platform-agnostic (125 MHz to 5 GHz)

**Python Implementation:**
- `TYPE_REGISTRY`: Central type registry
- `TypeConverter`: Physical ↔ raw conversion
- `TypeMetadata`: Bit width, range, signedness
- Pydantic models for validation

**Documentation:**
- [`llms.txt`](../../libs/basic-app-datatypes/llms.txt) - Complete type reference
- [`README.md`](../../libs/basic-app-datatypes/README.md) - User guide

### How Forge Uses It

**Direct Imports:**
```python
from basic_app_datatypes.registry import TYPE_REGISTRY
from basic_app_datatypes.converters import TypeConverter
from basic_app_datatypes.types import TypeMetadata
```

**Usage in Forge:**
1. **YAML Validation:** Check datatype names against TYPE_REGISTRY
2. **Range Validation:** Verify default_value within type's range
3. **Register Mapping:** Query bit_width for packing algorithm
4. **VHDL Generation:** Use type metadata for signal declarations
5. **Manifest Generation:** Include type metadata in manifest.json

**Example:**
```python
# In forge/models/package.py
from basic_app_datatypes.registry import TYPE_REGISTRY

def validate_datatype(datatype_name: str) -> TypeMetadata:
    """Validate datatype exists and return metadata"""
    type_obj = TYPE_REGISTRY.get_type(datatype_name)
    if type_obj is None:
        raise ValueError(f"Unknown datatype: {datatype_name}")
    return type_obj
```

### Documentation Boundaries

**✅ Forge Documents:**
- How to use types in YAML (`datatype: voltage_output_05v_s16`)
- Type selection guidelines (which type for which use case)
- Quick reference table (name, bits, range, use case)

**❌ Forge Does NOT Document:**
- Type implementation details (scaling formulas, conversion logic)
- Type metadata structure (bit_width, signed, range fields)
- How to add new types

**🔗 Forge References:**
- [Type System Overview](../reference/type_system.md) → Links to `libs/basic-app-datatypes/llms.txt`
- [Getting Started](../guides/getting_started.md) → Links to type reference
- [User Guide](../guides/user_guide.md) → Links to authoritative docs

---

## moku-models

**Location:** `libs/moku-models/`

**Repository:** [moku-models](https://github.com/liquidinstruments/moku-models)

### What It Provides

**Platform Specifications:**
- Hardware capabilities (DACs, ADCs, digital I/O)
- Clock frequencies (125 MHz, 1 GHz, 5 GHz)
- Memory sizes, FPGA resources
- Platform-specific constraints

**MCC Routing Patterns:**
- Common routing configurations
- Allowed vs forbidden connections
- Platform-specific routing tables
- Best practices for signal routing

**Documentation:**
- [`MOKU_PLATFORM_SPECIFICATIONS.md`](../../libs/moku-models/docs/MOKU_PLATFORM_SPECIFICATIONS.md) - Hardware specs
- [`routing_patterns.md`](../../libs/moku-models/docs/routing_patterns.md) - MCC routing
- [`datasheets/`](../../libs/moku-models/datasheets/) - Official platform PDFs

### How Forge Uses It

**Direct Imports:**
```python
from moku_models.platform import PlatformSpec
from moku_models.control_registers import ControlRegister
```

**Usage in Forge:**
1. **Platform Validation:** Verify `platform` field in YAML (go/lab/pro/delta)
2. **Clock Injection:** Inject platform-specific clock frequency into VHDL
3. **Register Export:** Convert forge mappings to moku-models `ControlRegister` format
4. **Manifest Generation:** Include platform metadata

**Example:**
```python
# In forge/models/package.py
from moku_models.platform import PlatformSpec

class BasicAppsRegPackage(BaseModel):
    platform: Literal["moku_go", "moku_lab", "moku_pro", "moku_delta"]

    def get_platform_spec(self) -> PlatformSpec:
        """Get platform specifications from moku-models"""
        return PlatformSpec.from_name(self.platform)

    def get_clock_frequency(self) -> int:
        """Get platform clock frequency for VHDL generation"""
        return self.get_platform_spec().clock_frequency
```

### Documentation Boundaries

**✅ Forge Documents:**
- How to specify platform in YAML (`platform: moku_go`)
- Platform compatibility (all types work on all platforms)
- Conceptual deployment workflow

**❌ Forge Does NOT Document:**
- Platform hardware specifications (DAC resolution, sample rates)
- MCC routing configuration details
- Platform-specific FPGA resources

**🔗 Forge References:**
- [User Guide](../guides/user_guide.md) → Links to platform specs
- [Deployment Guide](../guides/deployment_guide.md) → Links to routing patterns
- [Hardware Validation](../debugging/hardware_validation.md) → Links to platform docs

---

## riscure-models

**Location:** `libs/riscure-models/`

**Repository:** [riscure-models](https://github.com/liquidinstruments/riscure-models)

### What It Provides

**Probe Hardware Specifications:**
- DS1120A, DS1121A probe specs
- Electrical characteristics
- Pin assignments
- Operating ranges

**Datasheets:**
- Official probe datasheets (PDFs)
- Application notes
- Integration guides

**Documentation:**
- [`docs/probes/`](../../libs/riscure-models/docs/probes/) - Probe specifications
- [`datasheets/`](../../libs/riscure-models/datasheets/) - Official PDFs

### How Forge Uses It

**Usage in Forge:**
- **Reference Only:** Probe specs inform YAML design (voltage ranges, timing)
- **No Direct Imports:** Forge doesn't import riscure-models Python code
- **Documentation Links:** Forge docs link to probe specs for context

**Example Use Case:**
```yaml
# User designs probe controller for DS1120A
# References libs/riscure-models/docs/probes/DS1120A.md for specs
# Creates YAML with appropriate voltage ranges

datatypes:
  - name: probe_voltage
    datatype: voltage_output_05v_s16  # DS1120A range: ±5V
    default_value: 0
```

### Documentation Boundaries

**✅ Forge Documents:**
- How to design instrument specs for probes
- Example probe controllers (YAML specs)
- Debugging probe-based instruments

**❌ Forge Does NOT Document:**
- Probe hardware specifications
- Probe electrical characteristics
- Probe datasheets

**🔗 Forge References:**
- [Examples](../examples/) → May include probe controller examples
- [Common Patterns](../examples/common_patterns.md) → Probe control patterns
- [Hardware Validation](../debugging/hardware_validation.md) → Links to probe docs

---

## Documentation Strategy

### Clear Delegation

**Forge documentation lives in:**
- `docs/` - User guides, reference, architecture, examples
- `.claude/` - Agent system, shared knowledge
- `llms.txt` (root) - Quick reference with links to submodules

**Submodule documentation lives in:**
- `libs/basic-app-datatypes/llms.txt` - Type system reference
- `libs/moku-models/docs/` - Platform specs, routing patterns
- `libs/riscure-models/docs/` - Probe specs

### Documentation Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│ FORGE DOCUMENTS (docs/)                                     │
├─────────────────────────────────────────────────────────────┤
│ ✅ YAML schema and examples                                 │
│ ✅ Code generation pipeline internals                       │
│ ✅ Agent system workflows                                   │
│ ✅ Debugging forge-generated VHDL (FSM observer pattern)    │
│ ✅ How to use types/platforms (overview + selection guide)  │
│ ✅ Register mapping algorithms                              │
│ ✅ Deployment workflow (forge → CloudCompile → Moku)        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ FORGE DOES NOT DOCUMENT (delegates to libs/)                │
├─────────────────────────────────────────────────────────────┤
│ ❌ Type system internals → libs/basic-app-datatypes/        │
│ ❌ Platform specifications → libs/moku-models/              │
│ ❌ Probe hardware specs → libs/riscure-models/              │
│ ❌ Scaling formulas, conversion logic (types)               │
│ ❌ MCC routing tables (platforms)                           │
│ ❌ Electrical characteristics (probes)                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ FORGE REFERENCES (links to authoritative sources)           │
├─────────────────────────────────────────────────────────────┤
│ 🔗 [Type System](../reference/type_system.md)               │
│    → Links to libs/basic-app-datatypes/llms.txt             │
│                                                              │
│ 🔗 [User Guide](../guides/user_guide.md)                    │
│    → Links to libs/moku-models/docs/MOKU_PLATFORM_SPECS.md  │
│                                                              │
│ 🔗 [Hardware Validation](../debugging/hardware_validation.md)│
│    → Links to libs/riscure-models/docs/probes/              │
└─────────────────────────────────────────────────────────────┘
```

### Link Format

**Use relative paths from doc location:**

```markdown
<!-- In docs/guides/user_guide.md -->
See [Type System](../reference/type_system.md) for type overview.
See [Complete Type Reference](../../libs/basic-app-datatypes/llms.txt) for all 25 types.

<!-- In docs/reference/type_system.md -->
**Authoritative Source:** [`libs/basic-app-datatypes/llms.txt`](../../libs/basic-app-datatypes/llms.txt)

<!-- In docs/debugging/hardware_validation.md -->
**Platform Specs:** [Moku Platform Specifications](../../libs/moku-models/docs/MOKU_PLATFORM_SPECIFICATIONS.md)
**Routing Patterns:** [MCC Routing](../../libs/moku-models/docs/routing_patterns.md)
```

**Benefits:**
- ✅ Links work from all doc locations
- ✅ Links work in GitHub rendering
- ✅ Links work in local file browser
- ✅ No broken links when submodules update

---

## Git Submodule Workflow

### Initial Clone

```bash
# Clone with all submodules
git clone --recursive https://github.com/liquidinstruments/moku-instrument-forge.git

# If you forgot --recursive
git submodule update --init --recursive
```

### Update Submodules

```bash
# Update all submodules to latest commits
git submodule update --remote

# Update specific submodule
git submodule update --remote libs/basic-app-datatypes

# Commit updated submodule references
git add libs/basic-app-datatypes
git commit -m "Update basic-app-datatypes to latest"
```

### Check Submodule Status

```bash
# Show submodule commit SHAs
git submodule status

# Show submodule branches
git submodule foreach git branch

# Show submodule remotes
git submodule foreach git remote -v
```

### Working on Submodules

```bash
# Enter submodule
cd libs/basic-app-datatypes

# Make changes
git checkout -b feature/new-type
# ... edit files ...
git commit -m "Add new type"

# Push to submodule repo
git push origin feature/new-type

# Return to forge repo
cd ../..

# Update submodule reference
git add libs/basic-app-datatypes
git commit -m "Update basic-app-datatypes: new type support"
```

### Submodule Best Practices

**1. Pin to specific commits (default behavior):**
- Forge repo tracks specific submodule commits
- Ensures reproducible builds
- Update explicitly with `git submodule update --remote`

**2. Don't modify submodules in-place:**
- Work on submodule in separate clone
- Update forge's submodule reference after merge

**3. Document submodule versions:**
- Use `git submodule status` in CI/CD
- Include submodule SHAs in release notes

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│ moku-instrument-forge (this repo)                           │
│                                                              │
│  ┌──────────────┐      ┌──────────────────┐                │
│  │ YAML Spec    │─────▶│ Package Model    │                │
│  └──────────────┘      │ (Pydantic)       │                │
│                        └────────┬─────────┘                │
│                                 │                           │
│                                 ▼                           │
│                        ┌──────────────────┐                │
│                        │ Register Mapper  │                │
│                        └────────┬─────────┘                │
│                                 │                           │
│                                 ▼                           │
│                        ┌──────────────────┐                │
│                        │ VHDL Generator   │                │
│                        └────────┬─────────┘                │
│                                 │                           │
│                                 ▼                           │
│  ┌──────────────┐      ┌──────────────────┐                │
│  │ manifest.json│◀─────│ Package Output   │                │
│  │ VHDL files   │      └──────────────────┘                │
│  └──────────────┘                                           │
│                                                              │
│  Dependencies (git submodules):                             │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ libs/basic-app-datatypes/                          │    │
│  │  • TYPE_REGISTRY (25 types)                        │    │
│  │  • TypeConverter (physical ↔ raw)                  │    │
│  │  • TypeMetadata (bit_width, range, signed)         │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                     │
│                       │ Used by: Package validation,        │
│                       │          Register mapping,          │
│                       │          VHDL generation            │
│                       │                                     │
│  ┌────────────────────┴───────────────────────────────┐    │
│  │ libs/moku-models/                                  │    │
│  │  • PlatformSpec (Go/Lab/Pro/Delta)                 │    │
│  │  • ControlRegister (CR6-CR15)                      │    │
│  │  • Platform docs (specs, routing)                  │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                     │
│                       │ Used by: Platform validation,       │
│                       │          Clock injection,           │
│                       │          Register export            │
│                       │                                     │
│  ┌────────────────────┴───────────────────────────────┐    │
│  │ libs/riscure-models/                               │    │
│  │  • Probe specs (DS1120A, etc.)                     │    │
│  │  • Datasheets (PDFs)                               │    │
│  │  • (Reference only, no code imports)               │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Data Flow:
  YAML → Package (uses TYPE_REGISTRY for validation)
       → Mapper (uses TypeMetadata.bit_width for packing)
       → Generator (uses PlatformSpec for clock frequency)
       → Output (manifest.json, VHDL, control_registers.json)
```

---

## Design Rationale

### Why Submodules Over Monorepo?

**Pros:**
- ✅ **Reusability:** basic-app-datatypes used by other projects (not just forge)
- ✅ **Independent Versioning:** Types, platforms, probes have separate release cycles
- ✅ **Clear Ownership:** Each library has dedicated maintainers
- ✅ **Smaller Clone Size:** Main repo doesn't bloat with platform PDFs

**Cons:**
- ⚠️ **Setup Complexity:** `git clone --recursive` required
- ⚠️ **Update Friction:** Must explicitly update submodule refs
- ⚠️ **Version Skew:** Submodules can get out of sync

**Verdict:** Pros outweigh cons for this architecture. Reusability and clarity are critical.

### Why basic-app-datatypes Is a Library

**Rationale:**
- Used by **multiple projects** (forge, manual register tools, control software)
- **Stable API:** Types rarely change (voltage, time, boolean are universal)
- **Testable:** Independent test suite for type system
- **Documented:** Own llms.txt and README

**Benefits:**
- ✅ Update type definitions once, all projects benefit
- ✅ Control software uses same converters as forge
- ✅ Type system can evolve independently

### Why moku-models Is a Library

**Rationale:**
- Platform specs are **hardware facts**, not forge-specific
- Used by **deployment tools, control software, documentation**
- **Frequent Updates:** New platforms, routing patterns
- **Large Assets:** PDFs, datasheets shouldn't bloat forge repo

**Benefits:**
- ✅ Single source of truth for platform capabilities
- ✅ Easy to update specs without forge code changes
- ✅ Routing patterns reusable across tools

### Why riscure-models Is a Library

**Rationale:**
- Probe specs are **hardware facts**, not forge-specific
- Used by **probe control tools, documentation, test fixtures**
- **Separate Domain:** Probes ≠ platforms (different concern)
- **Large Assets:** PDFs shouldn't bloat forge repo

**Benefits:**
- ✅ Probe specs reusable across projects (not just forge)
- ✅ Clear separation: forge = code gen, riscure-models = hardware
- ✅ Easy to add new probes without touching forge

---

## Summary

**Forge's role:**
- 🎯 **Code generation toolchain:** YAML → VHDL + manifest.json
- 📖 **Documents:** Toolchain usage, agent workflows, debugging

**Submodule roles:**
- 📚 **basic-app-datatypes:** Type system (25 types, converters)
- 🔧 **moku-models:** Platform specs, MCC routing
- ⚡ **riscure-models:** Probe hardware specs

**Key Principle:**
- **Link, don't duplicate.** Forge references authoritative sources in submodules.

**Benefits:**
- ✅ Clear boundaries, no duplication
- ✅ Reusable libraries across projects
- ✅ Independent versioning and releases
- ✅ Single source of truth for each domain

**Workflow:**
1. Clone with `--recursive` (get all submodules)
2. Update submodules explicitly (`git submodule update --remote`)
3. Commit submodule refs when updating
4. Always link to submodule docs, never copy

**See Also:**
- [System Architecture](overview.md) - Overall forge design
- [Agent System](agent_system.md) - Agent boundaries
- [Type System Reference](../reference/type_system.md) - Type usage in forge

---

**Last Updated:** 2025-11-03
**Forge Version:** 2.0.0
