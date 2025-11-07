# VHDL Serialization Package Migration

**Date:** 2025-11-06
**Status:** ✅ Complete
**Impact:** Breaking change for VHDL imports

---

## Summary

Migrated VHDL serialization packages from `tools/forge-codegen/forge_codegen/vhdl/` to `libs/forge-vhdl/vhdl/packages/` with new naming convention using `forge_serialization_` prefix for clarity.

---

## What Changed

### Files Moved and Renamed

| Old Location | New Location | Purpose |
|-------------|--------------|---------|
| `tools/forge-codegen/forge_codegen/vhdl/basic_app_types_pkg.vhd` | `libs/forge-vhdl/vhdl/packages/forge_serialization_types_pkg.vhd` | Core serialization types |
| `tools/forge-codegen/forge_codegen/vhdl/basic_app_voltage_pkg.vhd` | `libs/forge-vhdl/vhdl/packages/forge_serialization_voltage_pkg.vhd` | Voltage serialization |
| `tools/forge-codegen/forge_codegen/vhdl/basic_app_time_pkg.vhd` | `libs/forge-vhdl/vhdl/packages/forge_serialization_time_pkg.vhd` | Time serialization |

### New Additions

| File | Source | Purpose |
|------|--------|---------|
| `libs/forge-vhdl/vhdl/packages/forge_common_pkg.vhd` | Copied from `bpd-tiny-vhdl/` | FORGE_READY control scheme (production-proven) |

### Removed

- ❌ `tools/forge-codegen/forge_codegen/vhdl/` directory (entire directory deleted)

---

## Naming Convention Change

### Old Names (Ambiguous)
```vhdl
use WORK.basic_app_types_pkg.ALL;
use WORK.basic_app_voltage_pkg.ALL;
use WORK.basic_app_time_pkg.ALL;
```

**Problems:**
- "basic" prefix unclear
- "app" is vague
- No indication these are for serialization

### New Names (Clear)
```vhdl
use WORK.forge_serialization_types_pkg.ALL;
use WORK.forge_serialization_voltage_pkg.ALL;
use WORK.forge_serialization_time_pkg.ALL;
```

**Benefits:**
- ✅ `forge_` prefix aligns with ecosystem
- ✅ `serialization_` clearly indicates purpose (register ↔ VHDL conversion)
- ✅ Distinguished from direct voltage utilities (`forge_voltage_3v3_pkg`, etc.)

---

## New forge-vhdl Package Structure

```
libs/forge-vhdl/vhdl/packages/
├── forge_common_pkg.vhd                     # FORGE_READY control (from BPD)
├── forge_lut_pkg.vhd                        # Look-up tables
├── forge_serialization_types_pkg.vhd        # Serialization core types (NEW)
├── forge_serialization_voltage_pkg.vhd      # Voltage serialization (NEW)
├── forge_serialization_time_pkg.vhd         # Time serialization (NEW)
├── forge_voltage_3v3_pkg.vhd                # Direct 0-3.3V utilities
├── forge_voltage_5v0_pkg.vhd                # Direct 0-5.0V utilities
└── forge_voltage_5v_bipolar_pkg.vhd         # Direct ±5.0V utilities
```

**Clear separation:**
- **Serialization packages** (`forge_serialization_*`) - For control register communication
- **Direct voltage packages** (`forge_voltage_*`) - For VHDL voltage domain conversions
- **Common packages** (`forge_common_pkg`) - Platform control schemes
- **Utility packages** (`forge_lut_pkg`) - Reusable utilities

---

## Migration Impact

### For BPD (bpd-tiny-vhdl)

**Before:**
```vhdl
-- Used stub files in bpd-tiny-vhdl/src/
use WORK.basic_app_types_pkg.ALL;
use WORK.basic_app_voltage_pkg.ALL;
```

**After (TODO):**
```vhdl
-- Reference libs/forge-vhdl/vhdl/packages/
use WORK.forge_serialization_types_pkg.ALL;
use WORK.forge_serialization_voltage_pkg.ALL;
use WORK.forge_common_pkg.ALL;  -- Now available!
```

**Action needed:**
1. Delete stub files in `bpd-tiny-vhdl/src/`
2. Update build to reference `libs/forge-vhdl/vhdl/packages/`
3. Update imports to new package names

### For forge-codegen

**Before:**
```python
# Generated VHDL referenced local vhdl/ directory
template_context = {
    'vhdl_package_path': 'forge_codegen/vhdl/'
}
```

**After (TODO):**
```python
# Generated VHDL should reference libs/forge-vhdl/
template_context = {
    'vhdl_package_path': '../../libs/forge-vhdl/vhdl/packages/'
}
# OR copy packages to output directory during generation
```

**Action needed:**
1. Update `tools/forge-codegen/forge_codegen/generator/codegen.py`
2. Update Jinja2 templates if they reference package paths
3. Update tests to use new package names

### For New Projects

**Recommended imports:**
```vhdl
library WORK;
use WORK.forge_common_pkg.ALL;                   -- FORGE_READY control scheme
use WORK.forge_serialization_types_pkg.ALL;      -- Core serialization types
use WORK.forge_serialization_voltage_pkg.ALL;    -- Voltage serialization
use WORK.forge_serialization_time_pkg.ALL;       -- Time serialization
```

---

## Rationale

### Why Move to forge-vhdl?

1. **forge-vhdl is the VHDL authority**
   - Already contains reusable VHDL packages
   - Has progressive CocoTB testing infrastructure
   - Self-contained, works standalone

2. **Serialization is a VHDL concern**
   - These packages are for FPGA synthesis
   - Used directly in VHDL code, not Python
   - Natural fit with other VHDL utilities

3. **BPD proved the need**
   - BPD copied these as stubs (needed real implementations)
   - BPD contributed `forge_common_pkg.vhd` (should be shared)
   - Production use validates the architecture

4. **Clean separation of concerns**
   - Python type system stays in forge-codegen (tightly coupled to generator)
   - VHDL packages in forge-vhdl (reusable across projects)

### Why Rename?

1. **Clarity**
   - "serialization" explicitly describes purpose
   - Developers immediately understand these are for register communication

2. **Ecosystem alignment**
   - `forge_` prefix matches other packages
   - Consistent with `forge_voltage_*`, `forge_util_*` naming

3. **Avoid confusion**
   - Clear distinction from direct voltage utilities
   - "basic_app" was ambiguous (basic what? which app?)

---

## Next Steps

### High Priority
1. [ ] Update BPD to use new packages from `libs/forge-vhdl/`
2. [ ] Delete BPD stub files (`bpd-tiny-vhdl/src/basic_app_*.vhd`)
3. [ ] Update BPD build configuration

### Medium Priority
4. [ ] Update forge-codegen generator to reference new locations
5. [ ] Update forge-codegen templates
6. [ ] Test generated VHDL with new package names

### Low Priority
7. [ ] Add CocoTB tests for serialization packages
8. [ ] Update CLAUDE.md in forge-vhdl with serialization package details
9. [ ] Create migration guide for external users

---

## Testing

**Pre-migration verification:**
- ✅ All files copied successfully
- ✅ Package names updated in VHDL files
- ✅ Internal `use WORK.*` references updated
- ✅ Old directory removed

**Post-migration verification (TODO):**
- [ ] BPD builds with new packages
- [ ] forge-codegen generates valid VHDL
- [ ] No broken imports

---

## Rollback Plan (If Needed)

If issues are discovered:

1. **Restore old files:**
   ```bash
   git checkout tools/forge-codegen/forge_codegen/vhdl/
   ```

2. **Remove new files:**
   ```bash
   rm libs/forge-vhdl/vhdl/packages/forge_serialization_*
   rm libs/forge-vhdl/vhdl/packages/forge_common_pkg.vhd
   ```

3. **Revert documentation:**
   ```bash
   git checkout libs/forge-vhdl/llms.txt
   ```

---

## References

- **forge-vhdl llms.txt:** Updated with new package descriptions
- **BPD source:** `bpd-tiny-vhdl/forge_common_pkg.vhd` (copied to forge-vhdl)
- **Migration discussion:** See conversation context

---

**Migration completed by:** Claude Code
**Approved by:** (pending user verification)
