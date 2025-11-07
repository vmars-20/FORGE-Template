# Architectural Design Decisions

**Rationale behind key architectural choices in moku-instrument-forge**

**Purpose:** Understand why specific design decisions were made, alternatives considered, and trade-offs

---

## Table of Contents

1. [Decision: YAML over JSON/TOML/Python DSL](#decision-yaml-over-jsontomlpython-dsl)
2. [Decision: Pydantic for Validation](#decision-pydantic-for-validation)
3. [Decision: Automatic Register Packing](#decision-automatic-register-packing)
4. [Decision: Git Submodules over Monorepo](#decision-git-submodules-over-monorepo)
5. [Decision: 5 Specialized Agents](#decision-5-specialized-agents)
6. [Decision: manifest.json as Source of Truth](#decision-manifestjson-as-source-of-truth)
7. [Decision: Type System (BasicAppDataTypes)](#decision-type-system-basicappdatatypes)

---

## Decision: YAML over JSON/TOML/Python DSL

**Choice:** YAML as the specification format for custom instrument definitions

### Rationale

**1. Human readability:**
- Comments supported natively
- Minimal syntax overhead
- Natural indentation-based structure

**2. Version control friendly:**
- Clean diffs (no trailing commas, brackets)
- Easy to review in pull requests
- Merge conflicts easier to resolve

**3. Declarative nature:**
- Describes *what* the instrument should be
- No imperative logic (unlike Python DSL)
- Matches mental model of specification

**Example comparison:**

**YAML (chosen):**
```yaml
app_name: DS1140_PD
description: EMFI probe driver
platform: moku_go

datatypes:
  - name: intensity
    datatype: voltage_output_05v_s16
    description: Output intensity
    default_value: 2400
    units: V
```

**JSON (alternative):**
```json
{
  "app_name": "DS1140_PD",
  "description": "EMFI probe driver",
  "platform": "moku_go",
  "datatypes": [
    {
      "name": "intensity",
      "datatype": "voltage_output_05v_s16",
      "description": "Output intensity",
      "default_value": 2400,
      "units": "V"
    }
  ]
}
```

### Alternatives Considered

**Alternative A: JSON**
- ❌ Verbose (trailing commas, quotes on keys)
- ❌ No comments support
- ✅ Native Python support
- ✅ Strict parsing
- **Why not chosen:** Too verbose for human authoring

**Alternative B: TOML**
- ✅ Human-readable
- ❌ Limited nesting (awkward for lists of datatypes)
- ❌ Less familiar to users
- **Why not chosen:** Nesting limitations for complex specs

**Alternative C: Python DSL**
```python
spec = InstrumentSpec(
    app_name="DS1140_PD",
    datatypes=[
        Datatype("intensity", VOLTAGE_OUTPUT_05V_S16, default=2400)
    ]
)
```
- ✅ Type checking in IDE
- ✅ Powerful (can use variables, functions)
- ❌ Too flexible (users might add logic)
- ❌ Not declarative
- ❌ Harder to parse by non-Python tools
- **Why not chosen:** Too imperative, violates declarative principle

### Trade-offs

**✅ Pros:**
- Easy to read and write
- Version control friendly
- Natural for configuration
- Wide tooling support

**❌ Cons:**
- YAML syntax quirks (indentation-sensitive)
- Type coercion surprises (`yes` → `True`, `0x10` → string)
- Multiple ways to write same thing (can cause inconsistency)

### Outcome

YAML chosen for user-facing specs. Mitigation for cons:
- Use `yaml.safe_load()` to avoid code execution
- Pydantic validation catches type coercion issues
- Document canonical style in examples

---

## Decision: Pydantic for Validation

**Choice:** Pydantic v2 for YAML specification validation

### Rationale

**1. Type safety:**
- Automatic type checking and coercion
- Rich type annotations (enums, constraints, custom validators)
- IDE autocomplete support

**2. Automatic validation:**
- Schema violations caught immediately
- Clear error messages with field paths
- Default value handling

**3. JSON export:**
- `.model_dump()` generates clean JSON (for manifest.json)
- Schema export for documentation

**4. Developer experience:**
- Pythonic API
- Extensive documentation
- Wide adoption (mature ecosystem)

### Example

**Pydantic model:**
```python
from pydantic import BaseModel, Field, field_validator
from basic_app_datatypes import BasicAppDataTypes

class DataTypeSpec(BaseModel):
    name: str = Field(pattern=r'^[a-z][a-z0-9_]*$')
    datatype: BasicAppDataTypes
    description: str = ""
    default_value: int
    min_value: int
    max_value: int

    @field_validator('default_value')
    def check_range(cls, v, info):
        if not (info.data['min_value'] <= v <= info.data['max_value']):
            raise ValueError(f"default_value {v} out of range")
        return v
```

**Automatic validation:**
```python
spec = DataTypeSpec(
    name="intensity",
    datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
    default_value=40000  # Out of range!
)
# ❌ ValidationError: default_value 40000 out of range for voltage_output_05v_s16 (max: 32767)
```

### Alternatives Considered

**Alternative A: Manual dict validation**
```python
def validate_spec(spec_dict):
    if 'app_name' not in spec_dict:
        raise ValueError("Missing app_name")
    if not isinstance(spec_dict['app_name'], str):
        raise ValueError("app_name must be string")
    # ... 100 more lines
```
- ✅ No dependencies
- ❌ Error-prone (easy to miss cases)
- ❌ Verbose boilerplate
- ❌ No type hints
- **Why not chosen:** Too much manual work, hard to maintain

**Alternative B: dataclasses (stdlib)**
```python
from dataclasses import dataclass

@dataclass
class DataTypeSpec:
    name: str
    datatype: BasicAppDataTypes
    default_value: int
```
- ✅ Stdlib (no dependency)
- ❌ No automatic validation
- ❌ No field constraints (min/max, patterns)
- ❌ No JSON schema export
- **Why not chosen:** Insufficient validation features

**Alternative C: marshmallow**
- ✅ Validation features
- ❌ Separate schema and model classes
- ❌ Less Pythonic API
- ❌ Declining adoption
- **Why not chosen:** Pydantic more modern and popular

### Trade-offs

**✅ Pros:**
- Catch errors early (before code generation)
- Rich validation (ranges, patterns, custom logic)
- Type safety throughout codebase
- JSON export for manifest.json

**❌ Cons:**
- External dependency (Pydantic v2)
- Learning curve for contributors
- Version compatibility (v1 → v2 breaking changes)

### Outcome

Pydantic v2 chosen. Dependency justified by safety and DX improvements. Pin version to avoid breaking changes.

---

## Decision: Automatic Register Packing

**Choice:** Automatic bit packing with 3 strategies (first_fit, best_fit, type_clustering)

### Rationale

**1. Space efficiency:**
- 50-75% register savings vs one-signal-per-register
- Maximizes use of limited CR space (10 registers × 32 bits)

**2. Eliminates manual errors:**
- No manual bit-slicing calculations
- No register collision bugs
- Automated VHDL bit extraction

**3. Consistency:**
- Same algorithm applied to all specs
- Reproducible packing
- Documented strategy choice

### Real Examples

**Example 1: DS1140_PD (8 signals)**

Without packing (naive):
```
CR6 = intensity (16-bit)         # Wastes 16 bits
CR7 = arm_timeout (16-bit)       # Wastes 16 bits
CR8 = trigger_threshold (16-bit) # Wastes 16 bits
CR9 = cooling_duration (8-bit)   # Wastes 24 bits
CR10 = firing_duration (8-bit)   # Wastes 24 bits
CR11 = arm_probe (1-bit)         # Wastes 31 bits
CR12 = force_fire (1-bit)        # Wastes 31 bits
CR13 = reset_fsm (1-bit)         # Wastes 31 bits

Total: 8 registers, 67 bits used, 189 bits wasted (22% efficiency)
```

With packing (type_clustering):
```
CR6 [31:16] arm_timeout (16-bit)
CR6 [15:0]  intensity (16-bit)

CR7 [31:16] trigger_threshold (16-bit)
CR7 [15:8]  cooling_duration (8-bit)
CR7 [7:0]   firing_duration (8-bit)

CR8 [31]    arm_probe (1-bit)
CR8 [30]    force_fire (1-bit)
CR8 [29]    reset_fsm (1-bit)

Total: 3 registers, 67 bits used, 29 bits wasted (69.8% efficiency)
```

**Savings:** 5 registers freed (50% reduction)

---

**Example 2: minimal_probe (3 signals)**

Without packing:
```
CR6 = enable (1-bit)    # Wastes 31 bits
CR7 = threshold (16-bit) # Wastes 16 bits
CR8 = duration (8-bit)   # Wastes 24 bits

Total: 3 registers, 25 bits used, 71 bits wasted (26% efficiency)
```

With packing (best_fit):
```
CR6 [31]    enable (1-bit)
CR6 [30:15] threshold (16-bit)
CR6 [14:7]  duration (8-bit)

Total: 1 register, 25 bits used, 7 bits wasted (78% efficiency)
```

**Savings:** 2 registers freed (67% reduction)

---

**Example 3: multi_channel (6 signals, all 16-bit voltages)**

With packing (type_clustering):
```
CR6 [31:16] ch1_voltage
CR6 [15:0]  ch2_voltage

CR7 [31:16] ch3_voltage
CR7 [15:0]  ch4_voltage

CR8 [31:16] ch5_voltage
CR8 [15:0]  ch6_voltage

Total: 3 registers, 96 bits used, 0 bits wasted (100% efficiency)
```

**Perfect packing for uniform signal sizes!**

### Alternatives Considered

**Alternative A: Manual bit assignment**
```yaml
datatypes:
  - name: intensity
    cr_number: 6
    bit_high: 15
    bit_low: 0
```
- ✅ Full control
- ❌ Error-prone (bit collision, off-by-one)
- ❌ Tedious for large specs
- ❌ No optimization
- **Why not chosen:** Too much manual work, defeats purpose of code generation

**Alternative B: One signal per register**
```
CR6 = signal1
CR7 = signal2
CR8 = signal3
...
```
- ✅ Simple
- ❌ Wastes space (only 10 CRs available)
- ❌ Runs out of registers quickly
- **Why not chosen:** Not scalable, inefficient

**Alternative C: Automatic packing with single strategy (first_fit only)**
- ✅ Automatic
- ❌ Suboptimal packing
- ❌ No choice for different use cases
- **Why not chosen:** Wanted flexibility (3 strategies for different scenarios)

### Trade-offs

**✅ Pros:**
- 50-75% register space savings
- Zero manual bit-slicing errors
- Consistent packing across specs
- Multiple strategies for different use cases

**❌ Cons:**
- Less control (can't specify exact bit positions)
- Slight complexity (3 strategies to understand)
- Register layout may change if spec reordered (mitigated by version control)

### Outcome

Automatic packing chosen with 3 strategies:
- **first_fit:** Fast, simple (small specs)
- **best_fit:** Reduces fragmentation (medium specs)
- **type_clustering:** Best organization (production, default)

**Recommendation:** Use `type_clustering` for production specs.

---

## Decision: Git Submodules over Monorepo

**Choice:** Git submodules for reusable libraries (basic-app-datatypes, moku-models)

### Rationale

**1. Reusability:**
- `basic-app-datatypes` used by multiple projects
- `moku-models` shared across Moku toolchain
- Independent versioning per library

**2. Single source of truth:**
- Platform specs maintained in one place (moku-models)
- Type system maintained in one place (basic-app-datatypes)
- No duplication across projects

**3. Clear ownership:**
- Each submodule has dedicated maintainers
- Independent release cycles
- Isolated testing

**4. Selective updates:**
- Update submodule only when needed
- Pin to specific commit for stability
- Bisect bugs to specific library

### Example Structure

```
moku-instrument-forge/
├── .gitmodules
│   [submodule "libs/basic-app-datatypes"]
│       path = libs/basic-app-datatypes
│       url = https://github.com/liquidinstruments/basic-app-datatypes
│   [submodule "libs/moku-models"]
│       path = libs/moku-models
│       url = https://github.com/liquidinstruments/moku-models
├── forge/ (forge-specific code)
└── libs/
    ├── basic-app-datatypes/ (submodule)
    └── moku-models/ (submodule)
```

### Alternatives Considered

**Alternative A: Vendoring (copy code)**
```
moku-instrument-forge/
└── forge/
    └── vendor/
        ├── basic_app_datatypes/ (copied)
        └── moku_models/ (copied)
```
- ✅ Simple (no submodule complexity)
- ❌ Duplication across projects
- ❌ No single source of truth
- ❌ Drift (copied code diverges over time)
- ❌ Bug fixes need updating everywhere
- **Why not chosen:** Violates DRY, maintenance nightmare

**Alternative B: Monorepo (all in one repo)**
```
moku-monorepo/
├── basic-app-datatypes/
├── moku-models/
├── moku-instrument-forge/
└── other-projects/
```
- ✅ Single clone
- ✅ Atomic cross-project changes
- ❌ Tight coupling (can't use library without entire monorepo)
- ❌ Heavyweight for library consumers
- ❌ Requires monorepo tooling
- **Why not chosen:** Too heavyweight, limits reusability

**Alternative C: PyPI packages (pip install)**
```python
# pyproject.toml
dependencies = [
    "basic-app-datatypes>=2.0.0",
    "moku-models>=1.5.0"
]
```
- ✅ Standard Python packaging
- ✅ Version pinning
- ❌ Requires publishing to PyPI
- ❌ Overhead for rapid development (publish on every change)
- ❌ Can't easily develop across libraries (need `pip install -e`)
- **Why not chosen:** Too much overhead for active development

### Trade-offs

**✅ Pros:**
- Single source of truth for platform specs
- Reusable across multiple projects
- Independent versioning
- Clear ownership boundaries

**❌ Cons:**
- Submodule complexity (`git submodule update --init --recursive`)
- Users might forget to update submodules
- Slightly harder to contribute across boundaries

### Outcome

Git submodules chosen. Documented in:
- [submodule_integration.md](submodule_integration.md)
- `README.md` (setup instructions)

**Mitigation for cons:**
- Document submodule workflow clearly
- Provide setup script: `git submodule update --init --recursive`
- Pin to specific commits for stability

---

## Decision: 5 Specialized Agents

**Choice:** 5 specialized agents (workflow-coordinator, forge-context, deployment-context, docgen-context, hardware-debug-context)

### Rationale

**1. Separation of concerns:**
- Each agent is a domain expert
- No overlapping responsibilities
- Clear boundaries

**2. Parallel workflows:**
- deployment-context and docgen-context can run simultaneously
- Both consume manifest.json independently
- No shared state

**3. Focused expertise:**
- forge-context: VHDL generation expert
- deployment-context: Moku hardware expert
- docgen-context: Documentation generation expert
- hardware-debug-context: FSM debugging expert

**4. Independent development:**
- Each agent can be updated independently
- Testing isolated to domain
- Smaller, more maintainable codebases

### Agent Boundaries

| Agent | Domain | Inputs | Outputs | Knows About |
|-------|--------|--------|---------|-------------|
| workflow-coordinator | Orchestration | User intent | Workflow results | All other agents |
| forge-context | Code generation | YAML | VHDL + manifest | basic-app-datatypes, Jinja2 |
| deployment-context | Hardware | manifest.json | Deployed device | moku-models, Moku API |
| docgen-context | Documentation | manifest.json | Docs/UIs/APIs | Markdown, Textual, Jinja2 |
| hardware-debug-context | FSM debugging | Deployed hardware | Debug reports | Oscilloscope, voltage decoding |

**Key: No cross-domain knowledge!**

### Alternatives Considered

**Alternative A: Monolithic tool (single agent)**
```
moku-forge-agent:
  - Validate YAML
  - Generate VHDL
  - Deploy to hardware
  - Generate docs
  - Debug FSM
```
- ✅ Simple (one entry point)
- ❌ Mixed concerns (VHDL + deployment + debugging)
- ❌ Hard to test (need full stack)
- ❌ No parallel workflows
- ❌ Becomes complex over time
- **Why not chosen:** Violates separation of concerns

**Alternative B: Manual commands (no agents)**
```bash
$ python forge/generate.py spec.yaml
$ python deploy/deploy.py DS1140_PD
$ python docs/generate.py DS1140_PD
```
- ✅ Simple scripts
- ❌ No orchestration
- ❌ User must remember order
- ❌ No error recovery
- ❌ No state tracking
- **Why not chosen:** Poor user experience, error-prone

**Alternative C: 3 agents (merge some contexts)**
```
- forge-and-deploy-context (generation + deployment)
- docgen-context
- debug-context
```
- ✅ Fewer agents
- ❌ Tight coupling (generation + deployment)
- ❌ Can't generate without deploying
- ❌ Can't run docgen in parallel with deployment
- **Why not chosen:** Loses parallel execution benefits

### Trade-offs

**✅ Pros:**
- Clear separation of concerns
- Parallel workflows (deployment + docgen)
- Focused domain expertise
- Independent testing and development
- Easier to maintain (smaller codebases)

**❌ Cons:**
- Coordination overhead (workflow-coordinator complexity)
- More files to navigate
- Need to understand agent boundaries

### Outcome

5 specialized agents chosen. Benefits outweigh coordination overhead.

**Workflow-coordinator handles:**
- Multi-stage pipelines
- State tracking
- Error recovery
- Cross-context queries

**Specialized agents stay focused:**
- forge-context: Just code generation
- deployment-context: Just hardware deployment
- docgen-context: Just documentation
- hardware-debug-context: Just FSM debugging

---

## Decision: manifest.json as Source of Truth

**Choice:** Generated manifest.json as canonical contract for all downstream consumers

### Rationale

**1. Decoupling:**
- Downstream contexts don't parse YAML
- Clear API boundary
- Can change YAML format without breaking consumers

**2. Versioned schema:**
- JSON Schema validation
- Backward compatibility tracking
- Clear contracts

**3. Parallel workflows:**
- deployment-context reads manifest
- docgen-context reads manifest
- No coordination needed (both read same file)

**4. Source of truth:**
- manifest.json generated from validated YAML
- Contains all metadata downstream needs
- No re-parsing, no re-validation

### Data Flow

```
YAML spec
   │
   ▼
forge-context (validates + generates)
   │
   ▼
manifest.json ◄──────── SOURCE OF TRUTH
   │
   ├──► deployment-context (reads platform, CRs)
   ├──► docgen-context (reads datatypes, mappings)
   └──► hardware-debug-context (reads FSM states)
```

**Key: Each consumer reads manifest independently, no shared state**

### Alternatives Considered

**Alternative A: Re-parse YAML in each context**
```
deployment-context:
  - Load YAML
  - Parse datatypes
  - Extract platform

docgen-context:
  - Load YAML (again!)
  - Parse datatypes (again!)
  - Extract mappings
```
- ✅ No intermediate file
- ❌ Duplication (each context parses YAML)
- ❌ Inconsistency (different parsers might interpret differently)
- ❌ Tight coupling (all contexts need YAML knowledge)
- **Why not chosen:** Violates DRY, tight coupling

**Alternative B: Embed metadata in VHDL comments**
```vhdl
-- MANIFEST_START
-- app_name: DS1140_PD
-- platform: moku_go
-- MANIFEST_END
```
- ✅ Self-contained VHDL
- ❌ Parsing VHDL comments is fragile
- ❌ Not machine-readable (no schema)
- ❌ VHDL not always needed (docgen doesn't use it)
- **Why not chosen:** Fragile, non-standard

**Alternative C: Database or API server**
```
forge-context → POST /api/packages → Database
deployment-context → GET /api/packages/DS1140_PD
```
- ✅ Centralized
- ✅ Could track history
- ❌ Requires server infrastructure
- ❌ Overkill for local development
- ❌ Offline development harder
- **Why not chosen:** Too heavyweight for code generation tool

### Trade-offs

**✅ Pros:**
- Downstream contexts decoupled from YAML
- Single source of truth (manifest.json)
- Parallel workflows (multiple readers, no locks)
- Versioned schema (backward compatibility)
- Machine-readable (JSON Schema validation)

**❌ Cons:**
- Redundancy (manifest.json duplicates info from YAML)
- Extra file to maintain
- Needs to stay in sync with YAML (forge-context responsibility)

### Outcome

manifest.json chosen as canonical contract. YAML is user-facing, manifest.json is machine-facing.

**Contract enforced via:**
- JSON Schema validation
- See [.claude/shared/package_contract.md](../../.claude/shared/package_contract.md)

---

## Decision: Type System (BasicAppDataTypes)

**Choice:** Platform-agnostic type system with physical units (voltage, time, boolean)

### Rationale

**1. Platform abstraction:**
- User writes `voltage_output_05v_s16` (logical)
- System handles platform-specific conversion (raw bits)
- Same spec works across Moku:Go/Lab/Pro/Delta

**2. Unit conversion:**
- User thinks in volts, milliseconds, cycles
- Type system handles raw integer conversion
- Eliminates conversion bugs

**3. Safety:**
- Type metadata enforces ranges (min/max)
- Catch out-of-range values at validation time
- VHDL type packages ensure type safety in hardware

**4. User-friendly:**
- Intuitive type names (voltage_output_05v_s16)
- Physical units in YAML (V, ms, cycles)
- No raw bits in user specs

### Example

**User YAML (with types):**
```yaml
datatypes:
  - name: intensity
    datatype: voltage_output_05v_s16
    default_value: 2400
    units: V
```

**What user sees:** "Set intensity to 2400 (representing ~0.37V)"

**What system does:**
```python
TYPE_REGISTRY[VOLTAGE_OUTPUT_05V_S16] = {
    'bit_width': 16,
    'signedness': 'signed',
    'min_value': -32768,
    'max_value': 32767,
    'unit': 'mV',
    'vhdl_type': 'voltage_output_05v_s16'
}

# Validate
assert -32768 <= 2400 <= 32767  # ✅ In range

# Generate VHDL
signal intensity : voltage_output_05v_s16;
intensity <= voltage_output_05v_s16(signed(Control6(15 downto 0)));
```

### Alternatives Considered

**Alternative A: Raw integers**
```yaml
datatypes:
  - name: intensity
    bit_width: 16
    signedness: signed
    default_value: 2400  # Raw bits
```
- ✅ Simple
- ❌ No unit information (is 2400 volts? millivolts? raw bits?)
- ❌ Platform-specific (user needs to know DAC encoding)
- ❌ Error-prone (easy to confuse units)
- **Why not chosen:** Not user-friendly, error-prone

**Alternative B: Platform-specific types**
```yaml
datatypes:
  - name: intensity
    datatype: moku_go_dac_s16  # Platform-specific!
```
- ❌ Not portable (different types for each platform)
- ❌ User needs to know platform details
- ❌ Can't switch platforms without rewriting spec
- **Why not chosen:** Tight coupling to platform

**Alternative C: Untyped with units in comments**
```yaml
datatypes:
  - name: intensity  # Voltage, ±5V range
    default_value: 2400
```
- ❌ No validation (comments not parsed)
- ❌ No type safety
- ❌ Human-only (machine can't check)
- **Why not chosen:** No safety guarantees

### Trade-offs

**✅ Pros:**
- Platform-agnostic (same spec across devices)
- Unit conversion handled automatically
- Type safety (ranges enforced)
- User-friendly (physical units, not raw bits)
- VHDL type packages ensure hardware type safety

**❌ Cons:**
- Abstraction overhead (learning 25 types)
- Limited type set (might not cover all use cases)
- Type system is another dependency (basic-app-datatypes)

### Outcome

BasicAppDataTypes chosen for safety and portability.

**25 types across 3 categories:**
- 12 voltage types (signed/unsigned, various ranges)
- 12 time types (ns, μs, ms, s, cycles)
- 1 boolean type

**User benefits:**
- Write intuitive specs (volts, milliseconds)
- System handles platform details
- Catch errors early (validation)

**See:** `libs/basic-app-datatypes/llms.txt` for complete type catalog

---

## Summary Table

| Decision | Choice | Key Benefit | Main Trade-off |
|----------|--------|-------------|----------------|
| Specification format | YAML | Human-readable, version control friendly | Syntax quirks |
| Validation | Pydantic v2 | Type safety, rich validation | External dependency |
| Register packing | Automatic (3 strategies) | 50-75% space savings | Less control |
| Code organization | Git submodules | Single source of truth | Submodule complexity |
| Agent architecture | 5 specialized agents | Separation of concerns | Coordination overhead |
| Package contract | manifest.json | Decoupling, parallel workflows | Redundancy |
| Type system | BasicAppDataTypes | Platform abstraction, safety | Learning curve (25 types) |

---

## Lessons Learned

**1. Optimize for humans, not machines:**
- YAML more verbose than binary format, but humans write/read specs
- Type names longer than raw integers, but intuitive

**2. Fail fast with clear messages:**
- Pydantic validation catches errors before code generation
- Better to fail at YAML validation than deploy broken VHDL

**3. Separation of concerns pays off:**
- 5 agents more complex initially, but easier to maintain long-term
- Parallel workflows wouldn't be possible with monolithic design

**4. Abstractions have cost, but provide value:**
- Type system adds complexity, but eliminates conversion bugs
- manifest.json adds redundancy, but decouples consumers

**5. Version control matters:**
- YAML diffs clean (git-friendly)
- JSON Schema enables backward compatibility tracking

---

**See also:**
- [overview.md](overview.md) - High-level architecture
- [code_generation.md](code_generation.md) - Pipeline internals
- [agent_system.md](agent_system.md) - Agent boundaries
- [submodule_integration.md](submodule_integration.md) - Submodule strategy

---

**Last Updated:** 2025-11-03 (Phase 6D)
**Maintained By:** moku-instrument-forge team
