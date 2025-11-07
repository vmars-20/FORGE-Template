# BPD Tiny VHDL Test Suite

**Status:** Cleaned and focused on FSM Observer testing
**Date:** 2025-11-06

---

## Directory Structure

```
tests/
├── bpd_fsm_observer_tests/          # FSM Observer test suite
│   ├── bpd_fsm_observer_constants.py # Shared constants
│   ├── P1_bpd_fsm_observer_basic.py  # Minimal tests (<20 lines output)
│   ├── P2_bpd_fsm_observer_intermediate.py # Standard validation
│   └── P3_bpd_fsm_observer_comprehensive.py # Full test suite
├── BPD-002v2.yaml                   # Configuration (to be revisited)
├── run.py                           # CocoTB test runner
├── test_bpd_fsm_observer_progressive.py # Test entry point
└── test_configs.py                  # Test configuration
```

---

## Running Tests

### Basic Usage (P1 - LLM-optimized)

```bash
cd bpd-tiny-vhdl/tests
python run.py bpd_fsm_observer
```

**Expected output:** <20 lines, <5 seconds

### Standard Validation (P2)

```bash
TEST_LEVEL=P2_INTERMEDIATE python run.py bpd_fsm_observer
```

### Comprehensive Testing (P3)

```bash
TEST_LEVEL=P3_COMPREHENSIVE python run.py bpd_fsm_observer
```

### List Available Tests

```bash
python run.py --list
```

---

## Test Dependencies

### Required VHDL Packages

From **bpd-tiny-vhdl/src/**:
- `basic_app_types_pkg.vhd`
- `basic_app_voltage_pkg.vhd`
- `basic_app_time_pkg.vhd`
- `basic_probe_driver_custom_inst_main.vhd`

From **libs/forge-vhdl/**:
- `vhdl/packages/forge_voltage_5v_bipolar_pkg.vhd`
- `vhdl/debugging/fsm_observer.vhd`

### Required Wrappers

- `CustomWrapper_test_stub.vhd`
- `CustomWrapper_bpd_with_observer.vhd`

---

## Test Infrastructure

### Progressive Testing Levels

| Level | Tests | Output | Runtime | Purpose |
|-------|-------|--------|---------|---------|
| P1 | 3 | <20 lines | <5s | LLM-friendly, fast iteration |
| P2 | 5-10 | <50 lines | <30s | Standard validation |
| P3 | 15-25 | <100 lines | <2min | Comprehensive coverage |

### GHDL Output Filtering

Uses `libs/forge-vhdl/scripts/ghdl_output_filter.py` for 98% noise reduction:
- Filters metavalue warnings, null transactions, init messages
- Preserves errors, failures, PASS/FAIL status
- Configurable via `GHDL_FILTER_LEVEL` environment variable

---

## Test Coverage

### FSM Observer Tests

**Purpose:** Verify fsm_observer.vhd correctly tracks BPD FSM state via voltage output

**P1 Tests (Basic):**
1. Reset behavior (IDLE = 0.0V)
2. IDLE → ARMED transition (voltage increase)
3. State progression stairstep (monotonic voltage increase)

**P2 Tests (Intermediate):**
4. FAULT state detection (negative voltage sign-flip)
5. Voltage magnitude consistency
6. Rapid state transitions

**P3 Tests (Comprehensive):**
7. All state transitions
8. Edge cases and corner cases
9. Stress testing with rapid cycles

---

## Cleanup Summary (2025-11-06)

**Removed:**
- ❌ `bpd_forge_tests/` - Different test suite (not needed)
- ❌ `test_bpd_forge_progressive.py` - Forge architecture tests
- ❌ `mcc/` - Deployment artifacts
- ❌ `sim_build/` - Build artifacts (regenerated per test)
- ❌ `README_FORGE_VHDL_INTEGRATION.md` - Outdated documentation
- ❌ `__pycache__/` - Python cache (regenerated)

**Kept:**
- ✅ `bpd_fsm_observer_tests/` - FSM observer test suite
- ✅ `BPD-002v2.yaml` - Configuration file (to be revisited)
- ✅ `run.py` - Test runner
- ✅ `test_bpd_fsm_observer_progressive.py` - Test entry point
- ✅ `test_configs.py` - Cleaned to only include bpd_fsm_observer

---

## Integration with forge-vhdl

This test suite uses the forge-vhdl progressive testing infrastructure:

**Shared components:**
- `libs/forge-vhdl/tests/conftest.py` - Clock and reset utilities
- `libs/forge-vhdl/tests/test_base.py` - TestBase class with verbosity control
- `libs/forge-vhdl/scripts/ghdl_output_filter.py` - GHDL output filtering

**Import pattern:**
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "forge-vhdl" / "tests"))
from conftest import setup_clock, reset_active_high
from test_base import TestBase, VerbosityLevel
```

---

## Next Steps

1. **Update package references** (after VHDL migration complete)
   - Change `basic_app_*_pkg.vhd` → `forge_serialization_*_pkg.vhd`
   - Point to `libs/forge-vhdl/vhdl/packages/` instead of local `src/`

2. **Run tests to verify**
   ```bash
   python run.py bpd_fsm_observer
   ```

3. **Revisit BPD-002v2.yaml**
   - Determine if still needed
   - Update or remove

---

**Last Updated:** 2025-11-06
**Maintained By:** BPD Development Team
