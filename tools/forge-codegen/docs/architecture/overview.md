# Architecture Overview

**moku-instrument-forge system architecture**

**Purpose:** Understand the system's high-level design, data flow, and component boundaries

---

## Table of Contents

1. [System Purpose](#system-purpose)
2. [Data Flow](#data-flow)
3. [Component Architecture](#component-architecture)
4. [Agent System](#agent-system)
5. [Package Contract](#package-contract)
6. [Type System Integration](#type-system-integration)
7. [Architectural Patterns](#architectural-patterns)

---

## System Purpose

**moku-instrument-forge** is a **code generation toolchain** that transforms declarative YAML specifications into deployable Moku custom instruments.

**Core workflow:**
```
YAML spec → Package generation → Hardware deployment → Documentation/Debug
```

**Key goals:**
- **Safety:** Type-safe specifications with automatic validation
- **Efficiency:** Automatic register packing (50-75% space savings)
- **Simplicity:** Declarative YAML instead of manual VHDL/register allocation
- **Reusability:** Platform-agnostic design via type system abstraction

---

## Data Flow

### High-Level Pipeline

```
┌─────────────────┐
│  User YAML Spec │
│  (apps/*.yaml)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  forge-context  │ ──────► manifest.json (package contract)
│ (code generator)│         │
└─────────────────┘         ├─► control_registers.json
         │                  │
         ├─ VHDL files      │
         └─ Package dir     │
                            │
         ┌──────────────────┴──────────────────┐
         │                                     │
         ▼                                     ▼
┌──────────────────┐                  ┌──────────────────┐
│ deployment-      │                  │ docgen-context   │
│ context          │                  │ (docs/APIs)      │
│ (hardware)       │                  └──────────────────┘
└─────────┬────────┘                           │
          │                                    ▼
          ▼                         Markdown docs, TUIs,
  Moku Device                       Python API classes
          │
          │
          ▼
┌──────────────────┐
│ hardware-debug-  │
│ context          │
│ (FSM debugging)  │
└──────────────────┘
```

**Key insight:** `manifest.json` serves as the **source of truth** for all downstream consumers. No consumer parses YAML directly—they all read the canonical package metadata.

### Data Flow Details

**Stage 1: Specification**
- **Input:** User-authored YAML file (`apps/<app_name>/<app_name>.yaml`)
- **Content:** Signal definitions, types, defaults, mapping strategy
- **Validation:** Pydantic schema validation

**Stage 2: Generation (forge-context)**
- **Input:** Validated YAML specification
- **Processing:** Type resolution, register mapping, template rendering
- **Output:** Well-formed package
  - `manifest.json` - Complete metadata (datatypes, register mappings, efficiency)
  - `control_registers.json` - Initial CR values (CR6-CR15)
  - VHDL files - Shim layer + main template

**Stage 3a: Deployment (deployment-context)**
- **Input:** Package metadata (`manifest.json`, `control_registers.json`)
- **Processing:** Device discovery, bitstream upload, register initialization, routing configuration
- **Output:** Deployed hardware with configured instrument

**Stage 3b: Documentation (docgen-context)**
- **Input:** Package metadata (`manifest.json`)
- **Processing:** Template-based doc generation
- **Output:** Markdown docs, TUI apps, Python control classes

**Stage 4: Hardware Debug (hardware-debug-context)**
- **Input:** Deployed instrument, FSM state definitions (from `manifest.json`)
- **Processing:** Oscilloscope monitoring, voltage-to-state decoding
- **Output:** Debug reports, timing analysis, state traces

---

## Component Architecture

### Layer 1: Forge Toolchain (Core)

**Location:** `forge/`

**Responsibilities:**
- YAML loading and Pydantic validation
- Register mapping (via `basic-app-datatypes.RegisterMapper`)
- VHDL code generation (Jinja2 templates)
- Package manifest creation

**Key modules:**
- `forge/generator/codegen.py` - Code generation engine
- `forge/models/package.py` - Pydantic models for YAML specs
- `forge/templates/*.j2` - VHDL Jinja2 templates

**See:** [code_generation.md](code_generation.md) for pipeline internals

---

### Layer 2: Submodules (Domain Knowledge)

**Location:** `libs/`

**Philosophy:** **Link, don't duplicate.** Submodules are the single source of truth for domain-specific knowledge.

#### basic-app-datatypes
- **What:** Type system (25 types: voltage, time, boolean)
- **Provides:** Type metadata, register mapping algorithm, VHDL type packages
- **Used by:** forge-context (code generation)
- **Docs:** `libs/basic-app-datatypes/llms.txt`

#### moku-models
- **What:** Moku platform specifications and routing validation
- **Provides:** Platform specs (clock, voltage range), MCC routing rules, Pydantic models for deployment configs
- **Used by:** deployment-context (hardware deployment)
- **Docs:** `libs/moku-models/docs/`

**See:** [submodule_integration.md](submodule_integration.md) for complete delegation strategy

---

### Layer 3: Platform (Moku Devices)

**Target platforms:**
- **Moku:Go** - 2 slots, 125 MHz, development
- **Moku:Lab** - 2 slots, 500 MHz, lab instrumentation
- **Moku:Pro** - 4 slots, 1.25 GHz, high-performance
- **Moku:Delta** - 3 slots, 5 GHz, RF applications

**Platform abstraction:** All platform-specific details delegated to `moku-models` submodule. Forge remains platform-agnostic by operating on abstract datatypes.

---

## Agent System

**Architecture:** Hub-and-spoke with specialized context agents

### 5 Specialized Agents

1. **workflow-coordinator** - Orchestrates multi-stage pipelines, delegates to specialized contexts
2. **forge-context** - YAML → Well-formed package (VHDL + metadata)
3. **deployment-context** - Package → Deployed hardware
4. **docgen-context** - Package → Documentation/UIs/APIs
5. **hardware-debug-context** - FSM debugging and hardware validation

### Key Principles

**Separation of concerns:**
- Each agent has defined input/output contracts
- No overlapping responsibilities
- Clean handoffs via `manifest.json`

**Hub-and-spoke:**
- `forge-context` at center produces canonical package
- Multiple consumers (deployment, docgen, debug) operate independently
- `workflow-coordinator` provides end-to-end orchestration

**Context isolation:**
- deployment-context doesn't know about YAML parsing
- docgen-context doesn't know about hardware deployment
- hardware-debug-context doesn't know about code generation

**See:** [agent_system.md](agent_system.md) for complete agent boundaries and workflows

---

## Package Contract

### Well-Formed Package Structure

```
apps/<app_name>/
├── <app_name>_custom_inst_shim.vhd     # Generated VHDL shim layer
├── <app_name>_custom_inst_main.vhd     # Generated VHDL main template
├── manifest.json                        # Package metadata (REQUIRED)
├── control_registers.json               # Initial CR values (REQUIRED)
└── <app_name>.yaml                      # Original specification
```

### The Package Contract

**Core principle:** `manifest.json` is the **source of truth** for all downstream consumers.

**What it provides:**
- Application metadata (name, version, platform, description)
- Datatype specifications (types, defaults, ranges, units)
- Register mappings (CR assignments, bit slices)
- Efficiency metrics (packing statistics)
- Optional FSM state definitions

**Why this matters:**
- Downstream contexts don't parse YAML
- Clear API boundary between generation and consumption
- Versioned, validated JSON schema
- Enables parallel workflows (deploy + docgen can run simultaneously)

**Example manifest.json snippet:**
```json
{
  "app_name": "DS1140_PD",
  "version": "1.0.0",
  "platform": "moku_go",
  "datatypes": [
    {
      "name": "intensity",
      "datatype": "voltage_output_05v_s16",
      "default_value": 2400,
      "display_name": "Intensity",
      "units": "V"
    }
  ],
  "register_mappings": [
    {
      "signal_name": "intensity",
      "cr_number": 6,
      "bit_slice": "15:0",
      "vhdl_type": "voltage_output_05v_s16"
    }
  ],
  "efficiency": {
    "bits_used": 67,
    "bits_available": 96,
    "percent_used": 69.8,
    "strategy": "type_clustering"
  }
}
```

**See:** [.claude/shared/package_contract.md](../../.claude/shared/package_contract.md) for complete JSON schemas

---

## Type System Integration

### BasicAppDataTypes

**Purpose:** Platform-agnostic type system with physical unit awareness

**25 types across 3 categories:**

**Voltage types (12):**
- `voltage_output_05v_s16` - ±5V signed DAC output
- `voltage_signed_s16` - Generic ±5V signed
- `voltage_millivolts_u16` - Millivolt-based unsigned
- ... and 9 more

**Time types (12):**
- `time_milliseconds_u16` - Milliseconds (0-65535 ms)
- `time_cycles_u8` - Clock cycles (0-255 cycles)
- `pulse_duration_ms_u16` - Pulse duration in ms
- `pulse_duration_ns_u8` - Pulse duration in ns
- ... and 8 more

**Boolean type (1):**
- `boolean` - 1-bit true/false

**Key features:**
- Fixed bit widths (1, 8, 16, 32 bits)
- Min/max range validation
- Physical unit metadata (V, ms, cycles)
- VHDL type package generation
- Platform-agnostic (converted to raw bits at deployment)

**Integration points:**
- **Forge:** Uses type metadata for VHDL generation
- **Mapper:** Uses bit widths for register packing
- **Deployment:** Converts logical values to raw register bits
- **Docgen:** Uses units/ranges for UI generation

**See:** `libs/basic-app-datatypes/llms.txt` for complete type catalog

---

## Architectural Patterns

### Pattern 1: Declarative Configuration

**Problem:** Manual VHDL + register allocation is error-prone

**Solution:** YAML-based declarative specs with automatic code generation

**Benefits:**
- Version control friendly (plain text)
- Human-readable specifications
- Validation before generation
- Consistent code style

### Pattern 2: Automatic Register Packing

**Problem:** Manual register allocation wastes space (one signal per register)

**Solution:** Automatic bit packing with 3 strategies (first_fit, best_fit, type_clustering)

**Benefits:**
- 50-75% register space savings
- Eliminates bit-slicing errors
- Optimal allocation without manual work

**Example:** DS1140_PD spec
- 8 signals → 3 registers (vs 8 without packing)
- 67/96 bits used (69.8% efficiency)

### Pattern 3: Contract-Based Interfaces

**Problem:** Tight coupling between generation and deployment

**Solution:** `manifest.json` as canonical contract, consumed by all downstream agents

**Benefits:**
- Parallel workflows (deploy + docgen simultaneously)
- No YAML parsing in consumers
- Clear API boundaries
- Versioned schema

### Pattern 4: Delegation to Submodules

**Problem:** Duplication of platform specs across projects

**Solution:** Git submodules for domain-specific knowledge

**Benefits:**
- Single source of truth
- Reusable across projects
- Independent versioning
- Clear ownership

**Examples:**
- Platform specs → `moku-models`
- Type system → `basic-app-datatypes`
- MCC routing rules → `moku-models/docs/routing_patterns.md`

### Pattern 5: Hub-and-Spoke Agent Architecture

**Problem:** Monolithic tools become complex and hard to maintain

**Solution:** Specialized agents with defined boundaries, coordinated by meta-agent

**Benefits:**
- Separation of concerns
- Parallel execution
- Focused expertise
- Clear handoffs

**Agent boundaries:**
- forge-context: Generation domain expert
- deployment-context: Hardware domain expert
- docgen-context: Documentation domain expert
- hardware-debug-context: FSM debugging domain expert
- workflow-coordinator: Pipeline orchestration

---

## Cross-Component Communication

### forge-context → deployment-context

**Interface:** `manifest.json` + `control_registers.json`

**Data flow:**
1. forge generates package with manifest
2. deployment reads platform from manifest
3. deployment reads CR initial values from control_registers.json
4. deployment uploads bitstream and configures hardware

### forge-context → docgen-context

**Interface:** `manifest.json`

**Data flow:**
1. forge generates package with manifest
2. docgen reads datatypes for API generation
3. docgen reads register_mappings for documentation
4. docgen generates UIs with correct units/ranges

### deployment-context → hardware-debug-context

**Interface:** Deployed hardware + `manifest.json`

**Data flow:**
1. deployment configures hardware
2. hardware-debug reads FSM states from manifest (if present)
3. hardware-debug monitors oscilloscope for state transitions
4. hardware-debug decodes voltage to state name using manifest

---

## Design Philosophy

### Core Tenets

1. **Declarative over Imperative**
   - YAML specs describe *what*, not *how*
   - Forge handles *how* (register allocation, VHDL generation)

2. **Type Safety First**
   - Pydantic validation at every layer
   - Catch errors before hardware deployment
   - Physical units prevent conversion mistakes

3. **Single Source of Truth**
   - Platform specs in `moku-models`
   - Type system in `basic-app-datatypes`
   - Generated metadata in `manifest.json`
   - Never duplicate knowledge

4. **Clear Boundaries**
   - Each agent has defined scope
   - Contracts enforced via JSON schemas
   - No hidden dependencies

5. **Optimize for Humans**
   - Readable YAML over raw JSON
   - Friendly signal names over register numbers
   - Automatic packing over manual allocation
   - Clear error messages with actionable fixes

---

## File Organization

```
moku-instrument-forge/
├── .claude/
│   ├── agents/               # Agent system (5 agents)
│   └── shared/               # Package contract schemas
├── apps/                     # Generated packages
│   └── <app_name>/
│       ├── manifest.json
│       └── control_registers.json
├── docs/
│   ├── architecture/         # This document
│   ├── guides/               # User guides
│   ├── reference/            # API reference
│   └── examples/             # Walkthroughs
├── forge/
│   ├── generator/            # Code generation engine
│   ├── models/               # Pydantic models
│   └── templates/            # Jinja2 templates
└── libs/                     # Git submodules
    ├── basic-app-datatypes/  # Type system
    └── moku-models/          # Platform specs
```

---

## Next Steps

**For new users:**
1. Read [Getting Started](../guides/getting_started.md) - Your first probe
2. Read [code_generation.md](code_generation.md) - Understand the pipeline
3. Read [agent_system.md](agent_system.md) - Learn agent workflows

**For contributors:**
1. Read [design_decisions.md](design_decisions.md) - Understand architectural choices
2. Read [submodule_integration.md](submodule_integration.md) - Submodule philosophy
3. Read [.claude/shared/package_contract.md](../../.claude/shared/package_contract.md) - Package schema

**For troubleshooting:**
1. Check [docs/reference/troubleshooting.md](../reference/troubleshooting.md)
2. Review agent logs in `.claude/logs/`
3. Validate manifest with JSON schema

---

**Last Updated:** 2025-11-03 (Phase 6D)
**Maintained By:** moku-instrument-forge team
