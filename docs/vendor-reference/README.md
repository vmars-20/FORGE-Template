# Vendor Reference Files

This directory contains original vendor-provided interface definitions for reference purposes.

---

## MCC_CustomWrapper_original.vhd

**Source:** Moku Control Computer (MCC) upstream specification
**Date Received:** 2025-11-06
**Status:** Reference only - DO NOT USE directly

### What This Is

Original MCC `CustomWrapper` entity definition with:
- 16 Control Registers (CR0-CR15) - Network settable
- 16 Status Registers (SR0-SR15) - Network readable (future)
- Interlacing support (`CustomWrapperInterlaced` entity)
- Platform-specific signals (`Sync`, `ExtTrig`)

### Why We Don't Use It Directly

**Problems with upstream definition:**
1. **Interlacing complexity** - `CustomWrapperInterlaced` adds unnecessary complexity for most use cases
2. **Platform-specific signals** - `Sync` and `ExtTrig` not supported on all Moku platforms
3. **No FORGE integration** - Missing CR0[31:29] control scheme documentation
4. **Unstable** - Vendor is still evolving the interface (interlacing may change)

### Our Simplified Version

**Location:** `libs/platform/MCC_CustomInstrument.vhd`

**Simplifications:**
- ✅ Removed `CustomWrapperInterlaced` entity (complexity)
- ✅ Removed `Sync` signal (not universally supported)
- ✅ Removed `ExtTrig` signal (not universally supported)
- ✅ Added CR0[31:29] FORGE control scheme documentation
- ✅ Platform-agnostic (works on Go/Lab/Pro)
- ✅ Stable interface isolated from vendor changes

**Result:** Clean, documented, FORGE-compatible entity definition

---

## Vendor Changes We Track

### 2025-11-06 Update

**Major changes:**
- Reduced from 32 control registers → 16 control registers
- Added 16 status registers (future network readable)
- Introduced interlacing support (experimental)

**Impact on FORGE:**
- ✅ Adapted register allocation (CR0[31:29] + CR1-CR15 for app)
- ✅ BRAM loader needs 16-register redesign (was 32)
- ⚠️ Status registers not yet network readable (future MCC release)

---

## How to Use This Reference

### When vendor provides updates:

1. **Save new version here** - `MCC_CustomWrapper_YYYYMMDD.vhd`
2. **Document changes** - Update this README with change notes
3. **Evaluate impact** - Does it affect `libs/platform/MCC_CustomInstrument.vhd`?
4. **Adapt if needed** - Update our simplified version if critical changes
5. **Test compatibility** - Ensure BPD example still works

### Don't blindly adopt vendor changes!

**Our principle:** Vendor interface is a **reference**, not gospel.

- We maintain a **simplified, stable** version in `libs/platform/`
- We **adapt** vendor changes that improve functionality
- We **reject** vendor changes that add unnecessary complexity
- We **document** differences and rationale

---

## Version History

| Date | Vendor Version | Our Version | Major Changes |
|------|----------------|-------------|---------------|
| 2025-11-06 | CustomWrapper (16 CR) | MCC_CustomInstrument v1.0 | Initial simplified version |

---

## Questions?

**Why maintain our own version?**
- Vendor interface is evolving and unstable
- We need FORGE-specific documentation
- Platform-agnostic subset is more reliable
- Isolation from vendor changes protects users

**When to update our version?**
- Only when vendor makes breaking changes
- Only when new features are universally available
- Only when changes improve functionality
- Never just to "stay current"

**How often to check vendor updates?**
- Review quarterly or when notified by vendor
- Document but don't immediately adopt
- Let vendor interface stabilize first

---

**Last Updated:** 2025-11-06
**Maintained By:** Moku Instrument Forge Team
**Purpose:** Track vendor changes, maintain stable simplified version
