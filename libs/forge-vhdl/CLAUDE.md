# forge-vhdl Design and Testing Guide

**Version:** 1.0
**Purpose:** VHDL utilities with token-efficient AI-assisted testing
**Audience:** Human developers and AI agents

---

## Project Overview

**forge-vhdl** provides reusable VHDL components for Moku custom instrument development,
with CocoTB progressive testing infrastructure optimized for LLM-friendly iteration.

**Key Innovation:** 98% test output reduction (287 lines → 8 lines) through GHDL
output filtering + progressive test levels (P1/P2/P3/P4).

---

## Architecture

### Three-Tier Documentation Pattern

**Tier 1: llms.txt** (~800 tokens)
- Quick component catalog
- Basic usage examples
- Pointers to Tier 2

**Tier 2: CLAUDE.md** (this file, ~3-5k tokens)
- Testing standards (AUTHORITATIVE)
- Design patterns
- Component integration

**Tier 3: Source Code** (load as needed, 5-10k tokens per component)
- VHDL implementations
- CocoTB tests
- Inline documentation

---

## CocoTB Progressive Testing Standard

### The Golden Rule

> **"If your P1 test output exceeds 20 lines, you're doing it wrong."**

Default to silence. Escalate consciously. Preserve context religiously.

### Progressive Test Levels

**P1 - BASIC** (Default, LLM-optimized)
- 2-4 essential tests only
- Small test values (cycles=20)
- <20 line output, <100 tokens
- <5 second runtime
- **Environment:** `TEST_LEVEL=P1_BASIC` (default)

**P2 - INTERMEDIATE** (Standard validation)
- 5-10 tests with edge cases
- Realistic test values
- <50 line output
- <30 second runtime
- **Environment:** `TEST_LEVEL=P2_INTERMEDIATE`

**P3 - COMPREHENSIVE** (Full coverage)
- 15-25 tests with stress testing
- Boundary values, corner cases
- <100 line output
- <2 minute runtime
- **Environment:** `TEST_LEVEL=P3_COMPREHENSIVE`

**P4 - EXHAUSTIVE** (Debug mode)
- Unlimited tests, random testing
- Maximum verbosity
- **Environment:** `TEST_LEVEL=P4_EXHAUSTIVE`

### GHDL Output Filter Levels

**AGGRESSIVE** (Default for P1)
- 90-98% output reduction
- Filters: metavalue, null, init, internal, duplicates
- Preserves: errors, failures, PASS/FAIL, assertions

**NORMAL** (Balanced)
- 80-90% output reduction
- Filters: metavalue, null, init, duplicates
- Preserves: errors, failures, first warning occurrences

**MINIMAL** (Light touch)
- 50-70% output reduction
- Filters: duplicate metavalue warnings only

**NONE** (Pass-through)
- 0% filtering
- Use for debugging filter itself

**Environment:** `GHDL_FILTER_LEVEL=aggressive|normal|minimal|none`

---

## CocoTB Progressive Testing Standard

### The Golden Rule

> **"If your P1 test output exceeds 20 lines, you're doing it wrong."**

Default to silence. Escalate consciously. Preserve context religiously.

### Test Structure (Mandatory)

**Directory Organization:**
```
tests/
├── test_base.py                          # Base class (DO NOT MODIFY)
├── <module_name>_tests/                  # Per-module directory (REQUIRED)
│   ├── <module_name>_constants.py        # Shared constants (REQUIRED)
│   ├── P1_<module_name>_basic.py         # Minimal tests (REQUIRED)
│   ├── P2_<module_name>_intermediate.py  # Standard tests (OPTIONAL)
│   ├── P3_<module_name>_comprehensive.py # Full tests (OPTIONAL)
│   └── P4_<module_name>_exhaustive.py    # Debug tests (OPTIONAL)
└── run.py                                 # Test runner (AUTO-OPTIMIZED)
```

### P1 - Basic Tests (Required Template)

```python
import cocotb
from conftest import setup_clock, reset_active_low
from test_base import TestBase
from <module>_tests.<module>_constants import *

class ModuleTests(TestBase):
    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def run_p1_basic(self):
        # 3-5 ESSENTIAL tests only
        await self.test("Reset", self.test_reset)
        await self.test("Basic operation", self.test_basic_op)
        await self.test("Enable control", self.test_enable)

@cocotb.test()
async def test_module_p1(dut):
    tester = ModuleTests(dut)
    await tester.run_all_tests()
```

### Constants File (Required)

```python
# <module>_tests/<module>_constants.py
from pathlib import Path

MODULE_NAME = "<module>"
HDL_SOURCES = [Path("../vhdl/<category>/<module>.vhd")]
HDL_TOPLEVEL = "<entity_name>"  # lowercase!

class TestValues:
    P1_MAX_VALUES = [10, 15, 20]      # SMALL for speed
    P2_MAX_VALUES = [100, 255, 1000]  # Realistic
```

### Execution Commands

```bash
# Default (LLM-optimized, P1 only)
uv run python tests/run.py <module>

# P2 (comprehensive validation)
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py <module>

# With more verbosity
COCOTB_VERBOSITY=NORMAL uv run python tests/run.py <module>

# List all tests
uv run python tests/run.py --list
```

### Critical Rules

**DO:**
- Start with P1 (get basics working first)
- Use small test values in P1 (10, not 10000)
- Keep P1 under 10 tests
- Inherit from TestBase for verbosity control
- Use conftest utilities (setup_clock, reset_active_low)

**DON'T:**
- Create monolithic tests (use progressive levels)
- Use large values in P1 (keep it fast)
- Print debug info by default (use self.log())
- Modify test_base.py (it's the framework)

---

## Component Naming Convention

### Pattern

- Entities: `forge_<category>_<function>`
- Packages: `forge_<domain>_pkg` or `volo_<domain>_pkg` (legacy)
- Test files: `test_<component>_progressive.py`

### Categories

- `forge_util_*` - Generic utilities (clk_divider, edge_detector, synchronizer)
- `forge_debug_*` - Debug infrastructure (fsm_observer, signal_tap)
- `forge_loader_*` - Memory initialization (bram_loader, config_loader)

### Examples

```
forge_util_clk_divider.vhd           # Programmable clock divider
forge_debug_fsm_observer.vhd         # FSM state observer (future)
forge_loader_bram.vhd                # BRAM initialization (future)
forge_lut_pkg.vhd                    # LUT package
forge_common_pkg.vhd                 # Common types and constants
```

---

## VHDL Coding Standards

### Mandatory Rules

All new forge-vhdl components MUST follow these rules:

**FSM States:** Use `std_logic_vector`, not enums (Verilog compatibility)
**Port Order:** clk, rst_n, clk_en, enable, data, status
**Signal Naming:** Universal prefixes (`ctrl_`, `cfg_`, `stat_`, `dbg_`)
**Reset Hierarchy:** rst_n > clk_en > enable

### Why These Rules?

1. **Verilog Compatibility**: VHDL enums don't translate to Verilog
2. **Synthesis Predictability**: Explicit encoding prevents synthesis surprises
3. **Code Consistency**: Uniform naming enables instant comprehension
4. **Safety**: Reset hierarchy prevents unsafe states

### Documentation

- **Complete Guide:** `docs/VHDL_CODING_STANDARDS.md` (~600 lines)
- **Quick Reference:** `docs/VHDL_QUICK_REF.md` (templates & checklists)

### Example: FSM State Declaration

```vhdl
-- ✅ CORRECT (Verilog-compatible)
constant STATE_IDLE   : std_logic_vector(1 downto 0) := "00";
constant STATE_ARMED  : std_logic_vector(1 downto 0) := "01";
signal state : std_logic_vector(1 downto 0);

-- ❌ FORBIDDEN (No Verilog translation)
type state_t is (IDLE, ARMED);  -- DO NOT USE!
signal state : state_t;
```

### Example: Port Order

```vhdl
entity forge_util_example is
    port (
        -- 1. Clock & Reset
        clk    : in std_logic;
        rst_n  : in std_logic;  -- Active-low

        -- 2. Control
        clk_en : in std_logic;
        enable : in std_logic;

        -- 3. Data inputs
        data_in : in std_logic_vector(15 downto 0);

        -- 4. Data outputs
        data_out : out std_logic_vector(15 downto 0);

        -- 5. Status
        busy : out std_logic
    );
end entity;
```

---

## Critical CocoTB Interface Rules

### Rule 1: CocoTB Type Constraints ⚠️

**CocoTB CANNOT access these types through entity ports:**
- ❌ `real`, `boolean`, `time`, `file`, custom records

**CocoTB CAN access:**
- ✅ `signed`, `unsigned`, `std_logic_vector`, `std_logic`

**Error message if violated:**
```
AttributeError: 'HierarchyObject' object has no attribute 'value'
"contains no child object"
```

### Rule 2: Test Wrapper Pattern

When testing packages with `real` or `boolean` types:

**❌ WRONG:**
```vhdl
entity wrapper is
    port (
        test_voltage : in real;        -- CocoTB can't access!
        is_valid : out boolean         -- CocoTB can't access!
    );
end entity;
```

**✅ CORRECT:**
```vhdl
entity wrapper is
    port (
        clk : in std_logic;
        test_voltage_digital : in signed(15 downto 0);  -- Scaled
        sel_test : in std_logic;                        -- Function select
        digital_result : out signed(15 downto 0);       -- Scaled output
        is_valid : out std_logic                        -- 0/1, not boolean
    );
end entity;

architecture rtl of wrapper is
    signal voltage_real : real;  -- Internal conversion
begin
    voltage_real <= (real(to_integer(test_voltage_digital)) / 32767.0) * V_MAX;

    process(clk)
    begin
        if rising_edge(clk) then
            if sel_test = '1' then
                digital_result <= to_digital(voltage_real);
                is_valid <= '1' when is_valid_fn(voltage_real) else '0';
            end if;
        end if;
    end process;
end architecture;
```

### Rule 3: Python Signal Access

```python
# std_logic_vector / unsigned
data = int(dut.data.value)

# signed (IMPORTANT: Use .signed_integer)
voltage = int(dut.voltage.value.signed_integer)

# std_logic
enable = int(dut.enable.value)  # Returns 0 or 1
```

**Complete guide:** See `docs/COCOTB_TROUBLESHOOTING.md` Section 0

---

## Component Catalog

### Utilities (forge_util_*)

**forge_util_clk_divider**
- Function: Programmable clock divider
- Generics: MAX_DIV (bit width)
- Ports: clk_in, reset, enable, divisor, clk_out
- Tests: 3 P1, 4 P2
- Use case: Clock generation, FSM timing
- File: `vhdl/utilities/forge_util_clk_divider.vhd`

### Packages

**forge_lut_pkg**
- Function: Look-up table utilities
- Exports: Voltage/index conversion functions, LUT constants
- Tests: 4 P1, 4 P2, 1 P3
- Use case: Voltage discretization, LUT-based calculations
- File: `vhdl/packages/forge_lut_pkg.vhd`

**forge_voltage_3v3_pkg**
- Function: 0-3.3V unipolar voltage domain utilities
- Domain: TTL/digital logic, GPIO, 3.3V probe interfaces
- Tests: 4 P1, 2 P2
- Use case: Digital voltage levels, TTL trigger thresholds
- File: `vhdl/packages/forge_voltage_3v3_pkg.vhd`

**forge_voltage_5v0_pkg**
- Function: 0-5.0V unipolar voltage domain utilities
- Domain: Sensor supply, unipolar analog signals
- Tests: 4 P1, 2 P2
- Use case: 0-5V DAC outputs, sensor power control
- File: `vhdl/packages/forge_voltage_5v0_pkg.vhd`

**forge_voltage_5v_bipolar_pkg**
- Function: ±5.0V bipolar voltage domain utilities
- Domain: Moku DAC/ADC, AC signals (default choice for analog work)
- Tests: 4 P1, 2 P2
- Use case: Moku platform interfaces, AC signal generation/measurement
- File: `vhdl/packages/forge_voltage_5v_bipolar_pkg.vhd`

**Design philosophy:** Explicit package selection enforces voltage domain boundaries. Function-based type safety (Verilog-compatible).
**Complete design doc:** `.migration/VOLTAGE_TYPE_SYSTEM_DESIGN.md`
**Python mirror:** `.migration/voltage_types_reference.py`

**forge_common_pkg**
- Function: Common constants and types
- Exports: VOLO_READY control scheme, BRAM loader protocol
- Tests: None yet
- File: `vhdl/packages/forge_common_pkg.vhd`

### Debugging (forge_debug_*)

**fsm_observer** (no tests yet)
- Function: Export FSM state to Moku registers for oscilloscope debugging
- Generics: NUM_STATES, V_MIN, V_MAX, FAULT_STATE_THRESHOLD
- Use case: Hardware FSM debugging without simulation
- File: `vhdl/debugging/fsm_observer.vhd`

### Loaders (forge_loader_*)

**forge_bram_loader** (no tests yet)
- Function: BRAM initialization from external sources
- Use case: LUT loading, configuration data
- File: `vhdl/loader/forge_bram_loader.vhd`

---

## Testing Workflow

### Running Tests

```bash
# Navigate to forge-vhdl
cd libs/forge-vhdl

# Run P1 tests (default, LLM-optimized)
uv run python tests/run.py forge_util_clk_divider

# Run P2 tests with more verbosity
TEST_LEVEL=P2_INTERMEDIATE COCOTB_VERBOSITY=NORMAL \
  uv run python tests/run.py forge_util_clk_divider

# List all available tests
uv run python tests/run.py --list

# Run all tests
uv run python tests/run.py --all
```

### Adding Tests for New Components

See `docs/PROGRESSIVE_TESTING_GUIDE.md` for step-by-step instructions.

Quick summary:
1. Copy template from `test_forge_util_clk_divider_progressive.py`
2. Create `<component>_tests/` directory with constants + P1/P2 modules
3. Update `tests/test_configs.py` with component entry
4. Run tests, ensure <20 line P1 output

---

## Integration with forge/

### forge/ Code Generation
- Uses `basic-app-datatypes` for type system (12 voltage types)
- Generates VHDL shim + main template
- Auto-generates type packages (`basic_app_types_pkg.vhd`)

### forge-vhdl Utilities
- Provides practical utilities for manual VHDL in `*_main.vhd`
- Focus on 3 common voltage ranges (3.3V, 5V, ±5V)
- Standalone, works outside forge/ ecosystem

**Separation:**
- forge/ = Comprehensive, auto-generated, YAML-driven
- forge-vhdl = Pragmatic, hand-written, day-to-day

---

## Voltage Type System (Phase 4)

### Design Philosophy

**Problem:** Prevent voltage domain mismatches (e.g., 3.3V TTL signal going to ±5V DAC).

**Solution:** Function-based type safety via explicit package selection.

### Three Voltage Domains

**1. forge_voltage_3v3_pkg** - 0-3.3V unipolar
- Use for: TTL, GPIO, digital glitch, 3.3V probe interfaces
- Scale: 0V → 0x0000, 3.3V → 0x7FFF

**2. forge_voltage_5v0_pkg** - 0-5.0V unipolar
- Use for: Sensor supply, 0-5V DAC outputs
- Scale: 0V → 0x0000, 5.0V → 0x7FFF

**3. forge_voltage_5v_bipolar_pkg** - ±5.0V bipolar
- Use for: Moku DAC/ADC, AC signals, most analog work
- Scale: -5V → 0x8000, 0V → 0x0000, +5V → 0x7FFF

### Usage Pattern (VHDL)

```vhdl
-- Declare domain by package selection
use work.forge_voltage_3v3_pkg.all;

signal trigger_volts : real := 2.5;  -- In 3.3V domain context
signal trigger_digital : signed(15 downto 0);

-- Explicit conversion (auditable)
trigger_digital <= to_digital(trigger_volts);

-- Runtime validation
assert is_valid(trigger_volts)
    report "Trigger voltage out of range" severity error;
```

### Python Mirror

```python
from voltage_types import Voltage_3V3

# Type-safe assignment (range validated)
trigger = Voltage_3V3(2.5)

# Type checker catches domain mismatches
# trigger = Voltage_5V_Bipolar(-3.0)  # mypy error!

# Explicit conversion to digital
trigger_digital = trigger.to_digital()  # int for register write
```

### Design Rationale

- **Verilog compatible:** Uses standard types only (no records/physical types)
- **Explicit domain:** Package name declares voltage range
- **Function-based:** Follows existing `volo_voltage_pkg` pattern
- **80% type safety:** Explicit packages + runtime validation (vs 100% with records)
- **Production-proven:** Based on EZ-EMFI patterns

**Trade-off:** No compile-time type safety (VHDL limitation for Verilog compatibility), but explicit package selection + runtime checks prevent most errors.

### Documentation

- **Design doc:** `docs/migration/VOLTAGE_TYPE_SYSTEM_DESIGN.md` (comprehensive rationale)
- **Python reference:** `docs/migration/voltage_types_reference.py` (implementation)
- **Relationship:** Independent from forge/basic-app-datatypes (different domains)

### Status

- Design finalized (2025-11-04)
- Implementation: Phase 4 (TBD)
- Will replace legacy `volo_voltage_pkg.vhd`

---

## Token Efficiency Metrics

### Before CocoTB + GHDL Filter

```
Test output: 287 lines
Token consumption: ~4000 tokens
LLM context impact: SEVERE
Cost per test: $0.12 (GPT-4)
```

### After CocoTB + GHDL Filter

```
Test output: 8 lines (P1), 20 lines (P2)
Token consumption: ~50 tokens (P1), ~150 tokens (P2)
LLM context impact: MINIMAL
Cost per test: $0.001 (GPT-4)
```

**Savings:** 98% reduction, 120x cost reduction

---

## Development Workflow

### Adding New Component

1. Write VHDL component in appropriate `vhdl/` subdirectory
2. Create CocoTB test using template
3. Run P1 tests, ensure <20 line output
4. Commit in submodule with descriptive message
5. Update `llms.txt` catalog
6. Add component section to this `CLAUDE.md`

### Modifying Existing Component

1. Make VHDL changes
2. Run existing tests (should still pass)
3. Add new tests if behavior changed
4. Commit in submodule

### Git Submodule Protocol

**CRITICAL:** All commits must be made inside `libs/forge-vhdl` submodule!

```bash
cd libs/forge-vhdl
git checkout 20251104-vhdl-forge-dev  # Ensure on feature branch
# make changes
git add .
git commit -m "descriptive message"
git push origin 20251104-vhdl-forge-dev
cd ../..
git add libs/forge-vhdl  # Update parent reference
git commit -m "chore: Update forge-vhdl submodule"
git push origin 20251104-vhdl-forge-dev
```

---

## Common Testing Patterns

### Pattern 1: Simple Entity Test

See `test_forge_util_clk_divider_progressive.py` for complete example.

```python
class ForgeUtilClkDividerTests(TestBase):
    async def run_p1_basic(self):
        await self.test("Reset", self.test_reset)
        await self.test("Divide by 2", self.test_divide_by_2)

    async def test_reset(self):
        await reset_active_low(self.dut)
        assert int(self.dut.clk_out.value) == 0
```

### Pattern 2: Package Test (Needs Wrapper)

See `test_forge_lut_pkg_progressive.py` + `forge_lut_pkg_tb_wrapper.vhd`.

```vhdl
-- Wrapper entity (packages can't be top-level)
entity forge_lut_pkg_tb_wrapper is
end entity;

architecture tb of forge_lut_pkg_tb_wrapper is
    -- Expose package functions/constants as signals
    signal test_constant : std_logic_vector(15 downto 0) := PACKAGE_CONSTANT;
end architecture;
```

---

## Appendix: VHDL Quick Reference

### Port Order Template

```vhdl
entity forge_module_example is
    port (
        -- 1. Clock & Reset
        clk    : in std_logic;
        rst_n  : in std_logic;  -- Active-low

        -- 2. Control
        clk_en : in std_logic;
        enable : in std_logic;

        -- 3. Data inputs
        data_in : in std_logic_vector(15 downto 0);

        -- 4. Data outputs
        data_out : out std_logic_vector(15 downto 0);

        -- 5. Status
        busy  : out std_logic
    );
end entity;
```

### FSM State Declaration

```vhdl
-- ✅ ALWAYS use std_logic_vector (NOT enums!)
constant STATE_IDLE   : std_logic_vector(1 downto 0) := "00";
constant STATE_ARMED  : std_logic_vector(1 downto 0) := "01";
constant STATE_FIRING : std_logic_vector(1 downto 0) := "10";

signal state, next_state : std_logic_vector(1 downto 0);
```

### Signal Naming Prefixes

| Prefix | Purpose | Example |
|--------|---------|---------|
| `ctrl_` | Control signals | `ctrl_enable`, `ctrl_arm` |
| `cfg_` | Configuration | `cfg_threshold`, `cfg_mode` |
| `stat_` | Status outputs | `stat_busy`, `stat_fault` |
| `dbg_` | Debug outputs | `dbg_state_voltage` |
| `_n` | Active-low | `rst_n`, `enable_n` |
| `_next` | Next-state | `state_next` |

### Clocked Process Template

```vhdl
process(clk, rst_n)
begin
    if rst_n = '0' then
        output <= (others => '0');
        state  <= STATE_IDLE;

    elsif rising_edge(clk) then
        if clk_en = '1' then
            if enable = '1' then
                output <= input;
                state  <= next_state;
            end if;
        end if;
    end if;
end process;
```

**Hierarchy:** rst_n > clk_en > enable

---

## Related Documentation

**Documentation Hierarchy:**
- **Tier 1 (Quick Ref):** `llms.txt` - Component catalog, basic usage
- **Tier 2 (Authoritative):** `CLAUDE.md` (this file) - Complete design & testing guide
- **Tier 3 (Specialized):** Load only when needed

### Tier 3: Specialized References

**In `docs/`:**
- `VHDL_CODING_STANDARDS.md` - Complete style guide (600 lines, reference material)
- `COCOTB_TROUBLESHOOTING.md` - Problem→Solution debugging guide

**In `scripts/`:**
- `GHDL_FILTER.md` - Filter implementation details (for debugging filter)

**In parent monorepo:**
- `../../.claude/shared/ARCHITECTURE_OVERVIEW.md` - Hierarchical architecture

---

**Last Updated:** 2025-11-04
**Maintainer:** Moku Instrument Forge Team
**Version:** 2.0.0
