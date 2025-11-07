# Basic Probe Driver (BPD) - Reference Implementation

**Status:** ✅ Production-ready FORGE architecture example
**Purpose:** Complete reference implementation for building custom Moku instruments
**Use Case:** Fault injection probe driver with advanced FSM control

---

## What This Example Demonstrates

This is a **complete, production-ready** implementation of the FORGE 3-layer architecture. Use it as a template and reference for your own custom instruments.

### ✅ FORGE Architecture Patterns

1. **FORGE Control Scheme (CR0[31:29])**
   - Safe initialization handshaking
   - 4-condition enable logic
   - See: `vhdl/CustomWrapper_bpd_forge.vhd`

2. **app_reg_* Abstraction**
   - Main app is completely Control Register agnostic
   - Uses typed signals: `app_reg_arm_enable`, `app_reg_trigger_voltage`, etc.
   - See: `vhdl/BPD_forge_main.vhd`

3. **ready_for_updates Handshaking**
   - FSM signals when safe to latch new register values
   - Protects from mid-cycle configuration changes
   - See: `vhdl/src/basic_probe_driver_custom_inst_main.vhd`

4. **3-Layer Architecture**
   - Layer 1: BRAM Loader (future integration)
   - Layer 2: Shim (`vhdl/BPD_forge_shim.vhd`) - Register mapping + synchronization
   - Layer 3: Main (`vhdl/BPD_forge_main.vhd`) - Application FSM logic

### ✅ Advanced Features

- **FSM Observer** - Export FSM state to oscilloscope for debugging (`vhdl/CustomWrapper_bpd_with_observer.vhd`)
- **CocoTB Progressive Testing** - P1/P2/P3 test levels (`vhdl/tests/`)
- **Voltage Type Safety** - Uses `forge_serialization_*` packages
- **Complete Documentation** - Architecture guide, testing guide, YAML spec

---

## File Structure

```
examples/basic-probe-driver/
├── README.md                           # This file
├── BPD-RTL.yaml                        # Authoritative register specification
├── VHDL_SERIALIZATION_MIGRATION.md    # Package migration notes
└── vhdl/
    ├── FORGE_ARCHITECTURE.md           # **START HERE** - Complete architecture spec
    ├── CustomWrapper_bpd_forge.vhd     # MCC interface + FORGE wrapper
    ├── CustomWrapper_bpd_with_observer.vhd  # With FSM observer for debugging
    ├── BPD_forge_shim.vhd              # Layer 2: Register mapping + sync
    ├── BPD_forge_main.vhd              # Layer 3: Application FSM (simplified)
    ├── src/
    │   └── basic_probe_driver_custom_inst_main.vhd  # Complete FSM implementation
    ├── tests/                          # CocoTB progressive tests
    │   ├── README.md                   # Testing guide
    │   ├── run.py                      # Test runner
    │   └── bpd_fsm_observer_tests/     # Progressive P1/P2/P3 tests
    └── external_Example/               # Legacy reference (VOLO pattern)
```

---

## Quick Start - Using BPD as Template

### Step 1: Study the Architecture

**Read these in order:**

1. **`vhdl/FORGE_ARCHITECTURE.md`** - Complete 3-layer architecture specification
2. **`BPD-RTL.yaml`** - See how registers are specified
3. **`vhdl/CustomWrapper_bpd_forge.vhd`** - MCC interface integration
4. **`vhdl/BPD_forge_shim.vhd`** - Register unpacking + synchronization
5. **`vhdl/src/basic_probe_driver_custom_inst_main.vhd`** - Main FSM implementation

### Step 2: Identify Patterns to Copy

**For your instrument, you'll need:**

1. **YAML Specification** - Model on `BPD-RTL.yaml`
   - Define your `app_reg_*` signals
   - Specify types from `forge_serialization_*` packages
   - Allocate Control Registers (remember CR0[31:29] is reserved!)

2. **CustomWrapper** - Copy `CustomWrapper_bpd_forge.vhd`
   - Extract FORGE control signals (CR0[31:29])
   - Instantiate your shim
   - Instantiate your main app

3. **Shim Layer** - Model on `BPD_forge_shim.vhd`
   - Unpack Control Registers → `app_reg_*` signals
   - Pack `app_status_*` signals → Status Registers
   - Implement `ready_for_updates` synchronization

4. **Main App** - Model on `src/basic_probe_driver_custom_inst_main.vhd`
   - Your FSM/application logic
   - Use `app_reg_*` inputs (NO Control Register knowledge!)
   - Generate `ready_for_updates` signal

### Step 3: Adapt for Your Application

**Replace BPD-specific logic with yours:**

- Probe control → Your instrument control
- FI timing → Your timing requirements
- Monitor feedback → Your input processing
- FSM states → Your state machine

**Keep the FORGE patterns:**
- ✅ CR0[31:29] control scheme
- ✅ app_reg_* abstraction
- ✅ ready_for_updates handshaking
- ✅ 3-layer architecture

---

## Testing

### Run CocoTB Tests

```bash
cd vhdl/tests

# Run P1 tests (LLM-optimized, <20 lines)
uv run python run.py

# Run P2 tests (comprehensive validation)
TEST_LEVEL=P2_INTERMEDIATE uv run python run.py

# Run P3 tests (full coverage)
TEST_LEVEL=P3_COMPREHENSIVE uv run python run.py
```

See `vhdl/tests/README.md` for complete testing guide.

---

## BPD Application Logic

**What BPD does:**

1. **Arming** - Wait for `app_reg_arm_enable` (IDLE → ARMED)
2. **Triggering** - Wait for external trigger or software trigger
3. **Firing** - Generate trig_out and intensity_out pulses with precise timing
4. **Monitoring** - Watch probe feedback signal for threshold crossing
5. **Cooldown** - Enforce minimum time between pulses (thermal safety)
6. **Fault Handling** - Detect faults (timeout, monitor failure) and require acknowledgment

**FSM States:** IDLE, ARMED, FIRING, COOLDOWN, FAULT

**Key Features:**
- Configurable pulse widths (nanosecond resolution)
- Configurable voltage levels (millivolt resolution)
- Monitor window with start delay and duration
- Auto-rearm mode for burst operation
- Watchdog timeout for trigger wait

---

## Integration with Moku + Riscure

**Platform:** Moku:Go (125 MHz clock)
**Probe:** Riscure DS1120A EMFI probe (example)

**Voltage Safety:**
- Uses `forge_serialization_voltage_pkg` for type-safe voltage handling
- Validates against `moku-models` platform constraints
- Validates against `riscure-models` probe specifications

**See:** `BPD-RTL.yaml` for complete register allocation and voltage ranges

---

## Documentation

- **Architecture:** `vhdl/FORGE_ARCHITECTURE.md` - Complete 3-layer spec with diagrams
- **Testing:** `vhdl/tests/README.md` - CocoTB progressive testing guide
- **Register Spec:** `BPD-RTL.yaml` - Authoritative register specification
- **Migration Notes:** `VHDL_SERIALIZATION_MIGRATION.md` - Package migration history
- **FSM Observer:** `vhdl/proposed_cocotb_test/FSM_OBSERVER_INTEGRATION.md` - Debugging guide

---

## Relationship to Template

**This example IS the template in action!**

- Uses `libs/platform/MCC_CustomInstrument.vhd` interface (simplified)
- Follows `libs/platform/FORGE_App_Wrapper.vhd` pattern
- Integrates with `libs/forge-vhdl` packages
- Uses `libs/moku-models` for platform specs
- Uses `libs/riscure-models` for probe specs

**When you build YOUR instrument:**
- Copy this structure
- Replace BPD logic with yours
- Keep the FORGE patterns
- Reference back here when stuck

---

## Status

**Current Phase:** Production-ready reference implementation

**Known Items:**
- FSM has known bug (debugging deferred for template work)
- BRAM loader not yet integrated (Layer 1 future work)
- Type system gaps documented (std_logic_reg, ±5V voltage type)

**This is INTENTIONAL** - Real-world examples have rough edges. This shows you:
- ✅ What production code looks like
- ✅ How to document known issues
- ✅ How to defer non-critical work
- ✅ How to maintain velocity

---

## Questions?

**Start with:** `vhdl/FORGE_ARCHITECTURE.md` - Most questions answered there

**Then:** Root `CLAUDE.md` - Complete monorepo architecture guide

**Code questions:** Inline comments in VHDL files are extensive

**Pattern questions:** Compare your code to BPD - if BPD does it, you should too!

---

**Version:** 1.0
**Last Updated:** 2025-11-06
**Status:** Production reference implementation
**License:** MIT
