# Phase 6 Documentation Plan - Progress Tracker

**Created:** 2025-11-03
**Last Updated:** 2025-11-03 (Phase D complete)
**Purpose:** Master progress tracker and workflow guide for Phase 6 documentation

---

## Phase Status Tracker

| Phase | Deliverables | Status | Completion | Commit | Summary |
|-------|--------------|--------|------------|--------|---------|
| **A** | Structure + Essential Guides (6 files) | 🟢 Complete | 2025-11-03 | `afc4028` | [Phase A Complete](#phase-a-structure--essential-guides) |
| **B** | Technical Reference (6 files) | 🟢 Complete | 2025-11-03 | `8333a96` | [Phase B Complete](#phase-b-technical-reference) |
| **C** | Examples (5 files) | 🟢 Complete | 2025-11-03 | `57017dc` | [Phase C Complete](#phase-c-examples) |
| **D** | Architecture (4 files) | 🟢 Complete | 2025-11-03 | - | [Phase D Complete](#phase-d-architecture) |
| **E** | Integration (4 updates) | 🔴 Not Started | - | - | [Phase E Plan](#phase-e-integration) |
| **F** | Validation (checks) | 🔴 Not Started | - | - | [Phase F Plan](#phase-f-validation) |

**Legend:**
- **Status:** 🔴 Not Started | 🟡 In Progress | 🟢 Complete | ⚠️ Blocked
- **Completion:** Date when phase was completed

---

## Git Workflow Strategy

### Branch Strategy (Lightweight)

**For Phase 6 documentation work, we use a simple linear workflow:**

```
main
└── (all phases committed directly to main)
```

**Rationale:** Documentation changes are low-risk, don't break code, and benefit from immediate availability.

**Alternative (if you prefer feature branches):**

```
main
└── docs/phase6
    ├── (Phase A commit)
    ├── (Phase B commit)
    ├── (Phase C commit)
    └── (Merge to main when complete)
```

### Commit Message Format

```bash
docs: Complete Phase 6{X} - {Description}

Phase {X} deliverables ({N} files):
- file1 - description
- file2 - description
...

Key achievements:
✅ Achievement 1
✅ Achievement 2

Next: Phase {X+1} ({description})

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Example (Phase A):**
```bash
git commit -m "$(cat <<'EOF'
docs: Complete Phase 6A - Essential documentation structure

Phase A deliverables (6 files):
- docs/README.md - Navigation hub
- docs/guides/getting_started.md - 30-min tutorial
- docs/guides/user_guide.md - Comprehensive usage
- docs/guides/troubleshooting.md - Common issues
- docs/architecture/submodule_integration.md - Submodule delegation
- Directory structure created

Key achievements:
✅ Tutorial-first approach
✅ Clear architectural boundaries
✅ Link-based documentation

Next: Phase B (Technical Reference)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Working on a Phase

```bash
# 1. Ensure you're on main (or docs/phase6 branch)
git checkout main

# 2. Create phase files (use Write tool)
# ... work on phase ...

# 3. Stage files
git add docs/

# 4. Commit with phase message
git commit -m "docs: Complete Phase 6B - Technical reference"

# 5. Update this plan (PHASE6_PLAN.md)
# ... mark phase complete ...

# 6. Commit plan update
git add docs/PHASE6_PLAN.md
git commit -m "docs: Update Phase 6 plan - Phase B complete"
```

---

## Phase A: Structure + Essential Guides

**Status:** 🟢 Complete
**Commit:** `afc4028`
**Completed:** 2025-11-03

### Deliverables (6 files)

✅ **1. `docs/README.md`** (250 lines)
- Navigation hub with quick links
- What is moku-instrument-forge
- Documentation structure preview
- Submodule links

✅ **2. `docs/guides/getting_started.md`** (350 lines)
- 30-minute tutorial
- `minimal_probe.yaml` example (3 signals)
- Step-by-step: install → validate → generate → inspect
- Register mapping explanation (52% efficiency)

✅ **3. `docs/guides/user_guide.md`** (500 lines)
- Complete workflow reference
- YAML schema, type system, register mapping
- Python control, best practices, common patterns
- Link-heavy (references all other docs)

✅ **4. `docs/guides/troubleshooting.md`** (600 lines)
- YAML validation errors
- Code generation issues
- VHDL compilation, Python control, hardware testing
- Performance issues, debug techniques, FAQ

✅ **5. `docs/architecture/submodule_integration.md`** (450 lines)
- Submodule philosophy (link, don't duplicate)
- All 3 submodules: basic-app-datatypes, moku-models, riscure-models
- Documentation boundaries
- Git submodule workflow, dependency graph

✅ **6. Directory structure**
- `docs/guides/`, `docs/reference/`, `docs/architecture/`, `docs/examples/`

### Key Achievements

- ✅ Tutorial-first approach (working example before theory)
- ✅ Clear architectural boundaries (forge vs submodules)
- ✅ Link-based documentation (no duplication of submodule content)
- ✅ Comprehensive troubleshooting (all error categories)
- ✅ Complete navigation (users can find anything from README.md)

---

## Phase B: Technical Reference

**Status:** 🟢 Complete
**Commit:** `8333a96`
**Completed:** 2025-11-03
**Deliverables:** 6 technical reference documents

### Files to Create

#### 1. `docs/reference/type_system.md`
**Purpose:** Overview of BasicAppDataTypes with links to authoritative docs

**Structure:**
- Overview (what is BasicAppDataTypes, why it exists)
- Type categories (voltage: 12, time: 12, boolean: 1)
- Quick reference table (type, bits, range, use case)
- Common use cases (when to use each type)
- Platform compatibility (all types on all platforms)
- **LINK to `libs/basic-app-datatypes/llms.txt`** for full details
- Type metadata (how to query TYPE_REGISTRY)
- Examples (3-4 type usage examples)

**Key Principle:** Single source of truth in library, forge docs provide context.

**Estimated:** ~300 lines

---

#### 2. `docs/reference/yaml_schema.md`
**Purpose:** Complete specification of YAML v2.0 format

**Structure:**
- Schema overview
- Top-level fields (`app_name`, `version`, `description`, `platform`)
- `datatypes` array specification
  - Required fields (`name`, `datatype`, `description`, `default_value`)
  - Optional fields (`display_name`, `units`, `min_value`, `max_value`)
  - Field validation rules
- `mapping_strategy` (optional, default: type_clustering)
- Examples for each field type
- Complete example (6-signal spec with all field types)

**Reference:** BasicAppDataTypes for type details, focus on YAML structure.

**Estimated:** ~400 lines

---

#### 3. `docs/reference/register_mapping.md`
**Purpose:** Explain the 3 packing strategies

**Structure:**
- Overview (why automatic packing matters)
- Strategy 1: `first_fit` - Algorithm, pros/cons, use cases
- Strategy 2: `best_fit` - Algorithm, pros/cons, use cases
- Strategy 3: `type_clustering` - Algorithm (default), pros/cons, use cases
- Visual examples (ASCII art register diagrams showing bit allocation)
- Efficiency metrics (how savings are calculated)
- Choosing a strategy (guidance)
- Manual override (if supported)

**Visual Example:**
```
first_fit (naive):
CR6: [voltage_16bit................] 16/32 bits used
CR7: [time_16bit...................] 16/32 bits used
CR8: [boolean.......................] 1/32 bits used
Total: 3 registers, 33/96 bits (34% efficient)

type_clustering (optimized):
CR6: [voltage_16bit|time_16bit.....] 32/32 bits used
CR7: [boolean.......................] 1/32 bits used
Total: 2 registers, 33/64 bits (52% efficient)
```

**Estimated:** ~350 lines

---

#### 4. `docs/reference/manifest_schema.md`
**Purpose:** Document manifest.json structure

**IMPORTANT:** DO NOT DUPLICATE `.claude/shared/package_contract.md`!

**Structure:**
```markdown
# manifest.json Schema Reference

See [Package Contract Specification](../../.claude/shared/package_contract.md) for the canonical schema definition.

## Quick Reference

**Key Fields:**
- `app_name`, `version`, `platform` - Basic metadata
- `datatypes[]` - Signal definitions
- `register_mappings[]` - CR assignments
- `efficiency` - Packing metrics

**Example:** [See Package Contract](../../.claude/shared/package_contract.md#example-manifestjson)

## Usage by Context

**forge-context** - Generates manifest.json
**deployment-context** - Reads manifest.json for deployment
**docgen-context** - Reads manifest.json to generate docs
**hardware-debug-context** - Reads manifest.json for FSM states

See [Package Contract](../../.claude/shared/package_contract.md) for detailed schemas and validation rules.
```

**Estimated:** ~150 lines (mostly links)

---

#### 5. `docs/reference/vhdl_generation.md`
**Purpose:** Document the generation pipeline internals

**Structure:**
- Pipeline overview (YAML → Pydantic → Mapper → Templates → VHDL)
- YAML parsing (Pydantic validation)
- Register mapping (first_fit/best_fit/type_clustering)
- Template rendering (Jinja2 templates)
- VHDL file structure (shim vs main)
- Platform-specific constants (clock frequency injection)
- Generated artifacts (manifest.json, control_registers.json, VHDL files)
- Customizing templates (for advanced users)

**Estimated:** ~400 lines

---

#### 6. `docs/reference/python_api.md`
**Purpose:** Document key Python classes for advanced users

**Structure:**
- `BasicAppsRegPackage` - Pydantic model, methods, usage
- `DataTypeSpec` - Signal definition, validation
- `BADRegisterMapper` - Mapping engine API
- `TypeConverter` - Conversion utilities (link to basic-app-datatypes for details)
- File I/O - Loading YAML, exporting manifest.json
- Integration with moku-models (to_control_registers())

**Note:** This can be partially auto-generated by docgen-context!

**Estimated:** ~300 lines

---

### Phase B Success Criteria

- [x] All 6 reference docs created
- [x] No duplication of submodule content
- [x] All cross-references valid (relative links work)
- [x] Code examples accurate and tested
- [x] Links to `.claude/shared/package_contract.md` correct

---

## Phase C: Examples

**Status:** 🟢 Complete
**Commit:** `57017dc`
**Completed:** 2025-11-03
**Deliverables:** 5 example files (2 YAML + 3 markdown) + consistency fixes

### Files to Create

#### 1. `docs/examples/minimal_probe.yaml`
**Purpose:** Simplest possible spec (3 signals)

**Content:** Same as used in getting_started.md
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
    datatype: boolean_1
    description: Enable output driver
    default_value: 0

  - name: pulse_width
    datatype: time_milliseconds_u16
    description: Pulse width in milliseconds
    default_value: 100
    units: ms
```

---

#### 2. `docs/examples/minimal_walkthrough.md`
**Purpose:** Deep dive into the simplest possible spec

**Structure:**
- Complete minimal_probe.yaml (from above)
- Line-by-line explanation of every field
- Why each datatype was chosen
- How register mapping works (show the output)
- Generated VHDL snippets (key sections)
- Generated manifest.json (complete)
- How to deploy and test
- Variations (what if we changed types?)

**Estimated:** ~400 lines

---

#### 3. `docs/examples/multi_channel.yaml`
**Purpose:** Show type variety and register packing (6 signals)

**Spec:** 6-signal example with:
- 2× voltage types (output + input ranges)
- 2× time types (milliseconds + cycles)
- 2× boolean types (flags)

**Example:**
```yaml
app_name: multi_channel_probe
version: 1.0.0
description: Multi-channel probe controller with type variety
platform: moku_pro

datatypes:
  - name: dac_voltage_ch1
    datatype: voltage_output_05v_s16
    description: Channel 1 DAC output
    default_value: 0
    units: V

  - name: dac_voltage_ch2
    datatype: voltage_output_05v_s16
    description: Channel 2 DAC output
    default_value: 0
    units: V

  - name: pulse_width
    datatype: time_milliseconds_u16
    description: Pulse width
    default_value: 100
    units: ms

  - name: settling_time
    datatype: time_cycles_u8
    description: ADC settling time in clock cycles
    default_value: 10
    units: cycles

  - name: enable_ch1
    datatype: boolean_1
    description: Enable channel 1
    default_value: 0

  - name: enable_ch2
    datatype: boolean_1
    description: Enable channel 2
    default_value: 0
```

---

#### 4. `docs/examples/multi_channel_walkthrough.md`
**Purpose:** Show type variety and register packing in action

**Structure:**
- Requirements (what we're building)
- YAML specification (complete)
- Type selection rationale (why each type)
- Register mapping output (6 signals → 2 registers, show packing)
- VHDL generation (shim + main excerpts)
- Deployment workflow
- Python control example
- Lessons learned (packing efficiency, type choices)

**Note:** Use this instead of DS1140_PD initially (DS1140_PD uses old VoloApp format, needs migration).

**Estimated:** ~500 lines

---

#### 5. `docs/examples/common_patterns.md`
**Purpose:** Reusable patterns for common scenarios

**Structure:**
1. **FSM Control Signals** - Boolean grouping, naming conventions
2. **Voltage Parameters** - Output vs input types, range selection
3. **Timing Configuration** - Type selection (ms vs µs vs cycles)
4. **Multi-Channel Control** - Naming conventions, arrays
5. **Safety Constraints** - Min/max validation, default values
6. **Register Optimization** - Packing strategies, bit width selection

**Format:** Each pattern as a mini-example with YAML snippet + explanation.

**Estimated:** ~400 lines

---

### Phase C Success Criteria

- [x] All 5 example files created
- [x] Both YAML examples validate successfully
- [x] Both YAML examples generate successfully
- [x] Walkthroughs explain all concepts clearly (400-500 lines each)
- [x] Common patterns catalog comprehensive (6 patterns)
- [x] Consistency fixes applied to Phases A-B (type names corrected)

---

## Phase D: Architecture

**Status:** 🔴 Not Started
**Target:** Day 6
**Deliverables:** 4 architecture documents

### Files to Create

#### 1. `docs/architecture/overview.md`
**Purpose:** High-level design overview

**Structure:**
- Data flow: YAML → Package → Deployment
- Component architecture: forge, libs, platform
- Agent system: 5 agents, boundaries, workflows (link to agent_system.md)
- Package contract: manifest.json as source of truth (link to package_contract.md)
- Type system: 25 types, converters, registry (link to basic-app-datatypes)
- Submodule delegation: How forge uses libs/ (link to submodule_integration.md)
- ASCII diagrams for data flow

**Estimated:** ~350 lines

---

#### 2. `docs/architecture/code_generation.md`
**Purpose:** Document generator pipeline internals

**Structure:**
- Pipeline stages (YAML → Pydantic → Mapper → Templates → Files)
- Pydantic validation (type checking, range validation)
- Register mapping (3 strategies in detail)
- Jinja2 template rendering (variables, filters, macros)
- VHDL generation (shim entity, signal unpacking)
- Manifest generation (schema, efficiency metrics)
- File output (directory structure, naming conventions)

**Estimated:** ~400 lines

---

#### 3. `docs/architecture/agent_system.md`
**Purpose:** Document the 5-agent architecture

**Structure:**
- **forge-context** - Scope, commands, outputs, boundaries
- **deployment-context** - Scope, commands, outputs, boundaries
- **docgen-context** - Scope, commands, outputs, boundaries
- **hardware-debug-context** - Scope, commands, outputs, boundaries
- **workflow-coordinator** - Workflows, orchestration, pipelines
- Agent boundaries (who does what)
- Workflow examples (`/workflow new-probe`, `/workflow iterate`)
- Reference `.claude/agents/*/agent.md` for detailed specs

**Estimated:** ~400 lines

---

#### 4. `docs/architecture/design_decisions.md`
**Purpose:** Why we built it this way

**Structure:**
- Why YAML? (declarative, version control, readable)
- Why Pydantic? (validation, type safety, JSON serialization)
- Why automatic packing? (50-75% savings, reduces errors)
- Why submodules? (reusability, single source of truth)
- Why 5 agents? (separation of concerns, parallel workflows)
- Why manifest.json? (source of truth for deployment)
- Why type system? (platform-agnostic, user-friendly units)
- Trade-offs and alternatives considered

**Estimated:** ~350 lines

---

### Phase D Success Criteria

- [ ] All 4 architecture docs created
- [ ] Design rationale clearly explained
- [ ] Agent boundaries clearly defined
- [ ] All cross-references valid

---

## Phase E: Integration

**Status:** 🔴 Not Started
**Target:** Day 7
**Deliverables:** 4 file updates

### Files to Update

#### 1. Update `llms.txt` (Root)
**Add BasicAppDataTypes section** (overview only, link to submodule):

```markdown
## BasicAppDataTypes (Type System)

moku-instrument-forge uses a 25-type system for type-safe register communication.

**Type Categories:**
- **Voltage (12):** voltage_output_05v_s16, voltage_signed_s16, voltage_millivolts_s16, etc.
- **Time (12):** time_milliseconds_u16, time_cycles_u8, time_microseconds_u16, etc.
- **Boolean (1):** boolean_1

**Key Features:**
- Fixed bit widths (no dynamic sizing)
- Platform-agnostic (125 MHz to 5 GHz)
- User-friendly units (volts, milliseconds, not raw bits)
- Automatic register packing (50-75% savings)

**Quick Reference:**
| Type | Bits | Range | Use Case |
|------|------|-------|----------|
| voltage_output_05v_s16 | 16 | ±5V | DAC output |
| time_milliseconds_u16 | 16 | 0-65535 ms | Durations |
| boolean_1 | 1 | 0/1 | Flags |

**Full Documentation:** See [`libs/basic-app-datatypes/llms.txt`](libs/basic-app-datatypes/llms.txt)

**Source:** `libs/basic-app-datatypes/` (git submodule)
```

---

#### 2. Update `.claude/agents/forge-context/agent.md`
**Add doc references:**

```markdown
## Reference Files

**Documentation:**
- [Type System Reference](../../../docs/reference/type_system.md)
- [YAML Schema](../../../docs/reference/yaml_schema.md)
- [Troubleshooting](../../../docs/guides/troubleshooting.md)
- [Examples](../../../docs/examples/)
```

---

#### 3. Update `.claude/agents/docgen-context/agent.md`
**Add doc references:**

```markdown
## Reference Files

**Documentation:**
- [User Guide](../../../docs/guides/user_guide.md) - For doc generation patterns
- [Examples](../../../docs/examples/) - For example patterns
```

---

#### 4. Create `.claude/shared/type_system_quick_ref.md`
**Purpose:** Quick lookup table for agents (machine-readable format)

**Structure:** Complete table of all 25 types

```markdown
# Type System Quick Reference

For agents to quickly look up type properties.

| Type | Bits | Signed | Range | Units | Category |
|------|------|--------|-------|-------|----------|
| voltage_output_05v_s16 | 16 | Yes | ±5V | V | Voltage |
| voltage_signed_s16 | 16 | Yes | ±5V | V | Voltage |
| voltage_millivolts_s16 | 16 | Yes | ±32767 mV | mV | Voltage |
| time_milliseconds_u16 | 16 | No | 0-65535 ms | ms | Time |
| time_cycles_u8 | 8 | No | 0-255 | cycles | Time |
| boolean_1 | 1 | No | 0-1 | - | Boolean |
[... all 25 types ...]

**Full Documentation:** See [`libs/basic-app-datatypes/llms.txt`](../../libs/basic-app-datatypes/llms.txt)
```

---

### Phase E Success Criteria

- [ ] `llms.txt` updated with BAD section
- [ ] Agent files reference new docs
- [ ] Type quick reference created (all 25 types)
- [ ] All links verified (relative paths work)

---

## Phase F: Validation

**Status:** 🔴 Not Started
**Target:** Day 8
**Deliverables:** Validation checks (no new files)

### Validation Checklist

#### 1. Test All YAML Examples
```bash
# Validate examples
uv run python -m forge.validate_yaml docs/examples/minimal_probe.yaml
uv run python -m forge.validate_yaml docs/examples/multi_channel.yaml

# Generate packages
uv run python -m forge.generate_package docs/examples/minimal_probe.yaml --output-dir /tmp/test_minimal
uv run python -m forge.generate_package docs/examples/multi_channel.yaml --output-dir /tmp/test_multi

# Verify outputs exist
ls /tmp/test_minimal/manifest.json
ls /tmp/test_multi/manifest.json
```

**Criteria:**
- [ ] Both YAML examples validate without errors
- [ ] Both examples generate successfully
- [ ] Generated manifest.json files valid

---

#### 2. Verify All Python Snippets
```bash
# Extract Python snippets from docs
# Test syntax and imports
python -m py_compile <snippet.py>
```

**Criteria:**
- [ ] All Python code blocks have valid syntax
- [ ] All imports resolve (forge, moku, basic_app_datatypes)
- [ ] No placeholder code (e.g., `# TODO`, `...`)

---

#### 3. Check All Cross-References
```bash
# Manually verify all markdown links
# Or use markdown link checker
```

**Check:**
- [ ] All `[Text](link)` links work from their doc location
- [ ] All relative paths correct (`../`, `../../`)
- [ ] All links to submodule docs work (`../../libs/...`)
- [ ] All links to `.claude/` files work
- [ ] No broken anchors (`#section-name`)

---

#### 4. Run Through Getting Started
**Test the 30-minute tutorial as a new user:**

```bash
# Follow docs/guides/getting_started.md step-by-step
# Record any issues or unclear steps
```

**Criteria:**
- [ ] Can complete tutorial without external help
- [ ] All commands work as written
- [ ] Example generates successfully
- [ ] Tutorial matches actual behavior

---

#### 5. Final Review

**Completeness:**
- [ ] All 28 files created (check against PHASE6_DOCUMENTATION_PROMPT.md)
- [ ] All phases (A-E) completed
- [ ] All success criteria met

**Quality:**
- [ ] No duplication of submodule content
- [ ] All examples tested
- [ ] All cross-references verified
- [ ] Single source of truth maintained

**Accessibility:**
- [ ] New users can follow getting_started.md
- [ ] Technical reference complete
- [ ] Migration guide clear
- [ ] Examples cover common patterns

---

### Phase F Success Criteria

- [ ] All YAML examples validated
- [ ] All Python snippets tested
- [ ] All cross-references checked
- [ ] Getting started tutorial verified
- [ ] All success criteria from PHASE6_DOCUMENTATION_PROMPT.md met

---

## Decision Log

Track key decisions as phases progress:

| Date | Phase | Decision | Rationale |
|------|-------|----------|-----------|
| 2025-11-03 | Setup | Use PHASE6_PLAN.md for tracking | Inspired by BAD_MASTER_Orchestrator.md from EZ-EMFI |
| 2025-11-03 | Setup | Simple git workflow (main branch) | Documentation is low-risk, benefits from immediate availability |
| 2025-11-03 | A | Tutorial-first approach | Show working code before explaining theory |
| 2025-11-03 | A | Link, don't duplicate | Single source of truth in submodules |
| 2025-11-03 | A | 6 essential docs in Phase A | Structure + navigation + troubleshooting foundation |
| 2025-11-03 | B | ASCII art for register layouts | Visual examples make packing strategies clearer |
| 2025-11-03 | B | Heavy cross-referencing | Enable users to navigate documentation efficiently |
| 2025-11-03 | B | Link to package_contract.md | Avoid duplicating manifest schema specification |
| 2025-11-03 | C | Validate before documenting | Generated real mappings (51.6%, 90.6%) before writing walkthroughs |
| 2025-11-03 | C | Consistency check after each phase | Found 20+ type name errors, fixed before Phase D |
| 2025-11-03 | C | Actual type names: boolean, pulse_duration_* | Corrected from assumed boolean_1, time_* names |

---

## Workflow Guidelines

### Starting a Phase

When starting a phase in a new Claude session:

1. **Check status:** Review this plan (PHASE6_PLAN.md)
2. **Read phase spec:** Check detailed plan above for the phase
3. **Review previous phase:** Look at last completed phase's commit
4. **Begin work:** Create files using Write tool
5. **Track progress:** Update status as you go

### Completing a Phase

When finishing a phase:

1. **Save all work:** Commit all files
2. **Update this plan:** Mark phase complete, add commit SHA
3. **Document decisions:** Add to decision log if needed
4. **Note blockers:** Document any issues for next session
5. **Commit plan update:** `git commit -m "docs: Update Phase 6 plan - Phase {X} complete"`

### Handoff Protocol

For multi-session work:

1. **Commit work-in-progress:** Even if phase not complete
2. **Update status:** Mark phase as 🟡 In Progress
3. **Note current state:** What's done, what's remaining
4. **Document blockers:** Any issues or questions
5. **Next session picks up:** Read this plan, check git log, continue

---

## File Count Tracker

**Total Files to Create:** 28 files + 4 updates = 32 changes

### Created (17/28)
- ✅ `docs/README.md`
- ✅ `docs/guides/getting_started.md` (+ consistency fixes)
- ✅ `docs/guides/user_guide.md` (+ consistency fixes)
- ✅ `docs/guides/troubleshooting.md`
- ✅ `docs/architecture/submodule_integration.md`
- ✅ Directory structure (guides/, reference/, architecture/, examples/)
- ✅ `docs/reference/type_system.md`
- ✅ `docs/reference/yaml_schema.md`
- ✅ `docs/reference/register_mapping.md`
- ✅ `docs/reference/manifest_schema.md`
- ✅ `docs/reference/vhdl_generation.md`
- ✅ `docs/reference/python_api.md`
- ✅ `docs/examples/minimal_probe.yaml`
- ✅ `docs/examples/minimal_walkthrough.md`
- ✅ `docs/examples/multi_channel.yaml`
- ✅ `docs/examples/multi_channel_walkthrough.md`
- ✅ `docs/examples/common_patterns.md`

### Remaining (11/28)

**Phase C - Examples (5):**
- ✅ `docs/examples/minimal_probe.yaml`
- ✅ `docs/examples/minimal_walkthrough.md`
- ✅ `docs/examples/multi_channel.yaml`
- ✅ `docs/examples/multi_channel_walkthrough.md`
- ✅ `docs/examples/common_patterns.md`

**Phase D - Architecture (4):**
- ⬜ `docs/architecture/overview.md`
- ⬜ `docs/architecture/code_generation.md`
- ⬜ `docs/architecture/agent_system.md`
- ⬜ `docs/architecture/design_decisions.md`

**Phase E - Updates (4):**
- ⬜ `llms.txt` (root) - Add BAD section
- ⬜ `.claude/agents/forge-context/agent.md` - Add doc refs
- ⬜ `.claude/agents/docgen-context/agent.md` - Add doc refs
- ⬜ `.claude/shared/type_system_quick_ref.md` - NEW file

**Phase F - Debugging (3):**
- ⬜ `docs/debugging/hardware_validation.md`
- ⬜ `docs/debugging/common_issues.md`
- ✅ `docs/debugging/fsm_observer_pattern.md` (already exists)

---

## Timeline Estimate

**8-day estimate** (compressed possible):

- **Days 1-2:** Phase A (structure + essential guides) ✅ **COMPLETE**
- **Days 3-4:** Phase B (technical reference) 🔴 **NEXT**
- **Day 5:** Phase C (examples)
- **Day 6:** Phase D (architecture)
- **Day 7:** Phase E (integration)
- **Day 8:** Phase F (validation)

**Can be compressed:**
- Use docgen-context for API docs (Phase B)
- Parallelize independent documentation (Phases B-D)
- Leverage test examples for YAML validation (Phase F)

---

## Getting Help

If you get stuck:

1. **Check this plan** for phase details
2. **Review git log** for recent changes
3. **Consult PHASE6_DOCUMENTATION_PROMPT.md** for full specification
4. **Check PHASE6_QUICKSTART.md** for overview
5. **Reference submodule docs** for type/platform details

---

**Last Updated:** 2025-11-03
**Current Phase:** C (Complete) → D (Next)
**Progress:** 17/28 files (61% complete)
**Repository:** `/Users/johnycsh/moku-instrument-forge`
