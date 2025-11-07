# Agent System Architecture

**5-agent architecture for moku-instrument-forge**

**Purpose:** Understand agent boundaries, responsibilities, and orchestration workflows

---

## Table of Contents

1. [Agent System Overview](#agent-system-overview)
2. [Agent 1: workflow-coordinator](#agent-1-workflow-coordinator)
3. [Agent 2: forge-context](#agent-2-forge-context)
4. [Agent 3: deployment-context](#agent-3-deployment-context)
5. [Agent 4: docgen-context](#agent-4-docgen-context)
6. [Agent 5: hardware-debug-context](#agent-5-hardware-debug-context)
7. [Agent Interaction Patterns](#agent-interaction-patterns)
8. [Workflow Examples](#workflow-examples)
9. [Design Principles](#design-principles)

---

## Agent System Overview

### Architecture Pattern: Hub-and-Spoke

**Core principle:** Specialized agents with defined boundaries, coordinated by meta-agent

```
User
  │
  └─► workflow-coordinator (meta-agent)
        │
        ├─► forge-context ──────────► manifest.json
        │                             │
        ├─► deployment-context ◄──────┤
        │                             │
        ├─► docgen-context ◄──────────┤
        │                             │
        └─► hardware-debug-context ◄──┘
```

### Key Characteristics

**Separation of concerns:**
- Each agent is a domain expert in one area
- No overlapping responsibilities
- Clean handoffs via package contract (manifest.json)

**Context isolation:**
- forge-context doesn't know about hardware deployment
- deployment-context doesn't parse YAML
- docgen-context doesn't interact with hardware
- hardware-debug-context doesn't generate code

**Parallel execution:**
- deployment-context and docgen-context can run simultaneously
- Both consume manifest.json independently
- No shared state beyond package files

**Meta-coordination:**
- workflow-coordinator provides end-to-end workflows
- Specialized agents focus on their domain
- User can invoke either coordinator workflows or specific agents

---

## Agent 1: workflow-coordinator

**Domain:** Pipeline orchestration, multi-context workflows, state management

**Role:** Meta-agent that delegates to specialized contexts

### Responsibilities

**✅ Does:**
- Orchestrate multi-stage pipelines across contexts
- Manage pipeline state (track current package, deployment status)
- Delegate tasks to specialized agents
- Handle cross-context queries
- Provide recovery guidance on errors

**❌ Does NOT:**
- Generate VHDL directly (delegates to forge-context)
- Deploy hardware directly (delegates to deployment-context)
- Write documentation directly (delegates to docgen-context)
- Debug FSMs directly (delegates to hardware-debug-context)

### Available Workflows

**Command:** `/workflow <workflow_name> [args]`

**Workflows:**
1. `/workflow new-probe <yaml_file>` - Full pipeline (validate → generate → deploy → docs → monitor)
2. `/workflow iterate <yaml_file>` - Fast iteration (regenerate → redeploy)
3. `/workflow debug <app_name>` - Deploy + FSM monitoring
4. `/workflow document <app_name>` - Generate all docs/UIs/APIs
5. `/workflow optimize <yaml_file>` - Compare packing strategies

### Delegation Pattern

**Single-context tasks → Delegate immediately:**
```
User: "Validate my YAML"
workflow-coordinator: [Delegates to forge-context: /validate spec.yaml]
```

**Multi-context workflows → Coordinate:**
```
User: "Deploy my new probe"
workflow-coordinator:
  1. Delegate to forge-context: /validate spec.yaml
  2. Delegate to forge-context: /generate spec.yaml
  3. Delegate to deployment-context: /discover
  4. Delegate to deployment-context: /deploy app_name
  5. Delegate to hardware-debug-context: /monitor-state app_name
```

**See:** [.claude/agents/workflow-coordinator/agent.md](../../.claude/agents/workflow-coordinator/agent.md)

---

## Agent 2: forge-context

**Domain:** YAML specification → Well-formed package (VHDL + metadata)

**Role:** Code generation domain expert

### Responsibilities

**✅ Does:**
- Validate YAML specifications against Pydantic schemas
- Generate VHDL files (shim layer + main template)
- Perform register mapping with 3 strategies
- Create manifest.json and control_registers.json
- Optimize register packing efficiency
- Run forge test suite

**❌ Does NOT:**
- Deploy to hardware (no knowledge of Moku devices)
- Generate documentation (produces metadata only)
- Debug hardware (no oscilloscope access)
- Parse deployment configs

### Inputs & Outputs

**Inputs:**
- YAML specification (`apps/<app_name>/<app_name>.yaml`)

**Outputs (Well-Formed Package):**
```
apps/<app_name>/
├── <app_name>_custom_inst_shim.vhd     # Generated VHDL shim
├── <app_name>_custom_inst_main.vhd     # Generated VHDL main
├── manifest.json                        # Package metadata
├── control_registers.json               # Initial CR values
└── <app_name>.yaml                      # Original spec (copy)
```

### Available Commands

**1. `/generate <yaml_file>` - Full pipeline**
- Validate YAML → Map registers → Generate VHDL → Create manifest

**2. `/validate <yaml_file>` - Schema validation only**
- Check datatypes valid, defaults in range, signal names valid

**3. `/map-registers <yaml_file>` - Show register mapping analysis**
- Display CR assignments, bit allocations, efficiency

**4. `/optimize <yaml_file>` - Compare packing strategies**
- Run all 3 strategies (first_fit, best_fit, type_clustering)
- Show efficiency comparison

**5. `/test-forge` - Run Python test suite**
- Test mapper, package models, code generation, integration

### Scope Boundaries

**Read & Write:** `forge/`, `apps/*/`
**Read-Only:** `libs/basic-app-datatypes/`, `libs/moku-models/`
**No Access:** Deployment scripts, hardware

**See:** [.claude/agents/forge-context/agent.md](../../.claude/agents/forge-context/agent.md)

---

## Agent 3: deployment-context

**Domain:** Package → Deployed hardware configuration

**Role:** Hardware deployment domain expert

### Responsibilities

**✅ Does:**
- Deploy packages to Moku devices
- Discover devices on network
- Configure control registers (CR6-CR15)
- Set up MCC routing (connections between slots and I/O)
- Verify deployment with oscilloscope
- Cache device information

**❌ Does NOT:**
- Parse YAML specifications (reads manifest.json only)
- Generate VHDL or modify package files
- Create documentation
- Perform FSM debugging (reads control registers only)

### Inputs & Outputs

**Inputs:**
- `manifest.json` - Package metadata (platform, version)
- `control_registers.json` - Initial CR values
- Compiled bitstream (`<app_name>.tar.gz`)

**Outputs:**
- Deployed Moku device with configured instrument
- Device cache file (`.claude/state/device_cache.json`)
- Deployment logs

### Available Commands

**1. `/deploy <app_name> --device <ip>` - Deploy to hardware**
- Connect → Upload bitstream → Set CRs → Configure routing → Verify

**Flags:**
- `--device <ip>` - Target device IP
- `--slot <1-4>` - Custom instrument slot (default: 2)
- `--force` - Force reconnect, ignore warnings
- `--no-oscilloscope` - Skip oscilloscope deployment

**2. `/discover` - Find Moku devices on network**
- List available devices with IP, serial, platform
- Optional: `--platform <go|lab|pro|delta>` - Filter by platform
- Optional: `--save-cache` - Save to device cache

### moku-models Integration

**Primary interface:** Always use `moku-models` for type-safe configuration

```python
from moku_models import MokuConfig, SlotConfig, MokuConnection

# Type-safe configuration from manifest
config = MokuConfig(
    platform=MOKU_GO_PLATFORM,
    slots={
        1: SlotConfig(instrument='Oscilloscope'),
        2: SlotConfig(instrument='CloudCompile', bitstream='...', control_registers={...})
    },
    routing=[
        MokuConnection(source='Input1', destination='Slot2InA'),
        MokuConnection(source='Slot2OutA', destination='Output1')
    ]
)
```

### Routing Patterns

**Pattern 1: Monitor + Output**
```python
connections = [
    {'source': 'Input1', 'destination': 'Slot2InA'},      # External input
    {'source': 'Slot2OutA', 'destination': 'Output1'},    # Physical output
    {'source': 'Slot2OutB', 'destination': 'Slot1InA'},   # Monitor on osc
]
```

**Pattern 2: Cross-Slot Processing**
```python
connections = [
    {'source': 'Input1', 'destination': 'Slot1InA'},
    {'source': 'Slot1OutA', 'destination': 'Slot2InA'},   # Chain slots
    {'source': 'Slot2OutA', 'destination': 'Output1'},
]
```

**Pattern 3: Debug Mode**
```python
connections = [
    {'source': 'Input1', 'destination': 'Slot2InA'},
    {'source': 'Slot2OutA', 'destination': 'Slot1InA'},   # OutA → Osc Ch1
    {'source': 'Slot2OutB', 'destination': 'Slot1InB'},   # OutB → Osc Ch2
]
```

**See:** [.claude/agents/deployment-context/agent.md](../../.claude/agents/deployment-context/agent.md)

---

## Agent 4: docgen-context

**Domain:** Package → Documentation, UIs, Python APIs

**Role:** Documentation generation domain expert

### Responsibilities

**✅ Does:**
- Generate Markdown documentation from manifest.json
- Generate Textual TUI apps from datatypes
- Generate type-safe Python control classes
- Create usage examples and quickstart guides
- Document register maps with VHDL snippets

**❌ Does NOT:**
- Deploy to hardware
- Modify package core files (manifest.json, VHDL)
- Parse YAML directly (reads manifest.json only)
- Execute deployment commands

### Inputs & Outputs

**Inputs:**
- `manifest.json` - Complete package metadata

**Outputs:**
```
apps/<app_name>/docs/
├── README.md                 # Overview and quickstart
├── register_map.md           # Detailed register documentation
├── api_reference.md          # Python API docs
└── examples/
    └── basic_usage.py        # Example scripts

apps/<app_name>/ui/
├── <app_name>_tui.py         # Textual TUI app
└── requirements.txt          # UI dependencies

apps/<app_name>/python/
├── <app_name>_control.py     # Generated control class
└── __init__.py
```

### Available Commands

**1. `/gen-docs <app_name>` - Generate markdown documentation**
- README.md with quickstart
- register_map.md with bit allocations
- api_reference.md for Python API

**2. `/gen-ui <app_name>` - Generate Textual TUI app**
- Interactive control interface
- Auto-generates sliders/inputs based on datatypes
- Shows units, ranges, current values

**3. `/gen-python-api <app_name>` - Generate Python control class**
- Type-safe setters for each signal
- Automatic bit packing/unpacking
- Docstrings with units and ranges

### Generated Documentation Examples

**README.md structure:**
- Overview and description
- Quick start code snippet
- Signals table (name, type, description, default)
- Links to register map and Python API

**register_map.md structure:**
- Efficiency metrics
- Per-register breakdown with bit allocations
- VHDL extraction code snippets
- Control register hex values

**Python control class structure:**
```python
class DS1140_PD_Control:
    def __init__(self, moku_device, slot=2):
        self.device = moku_device
        self.slot = slot

    def set_intensity(self, value: int):
        """Set intensity (voltage_output_05v_s16).

        Range: -32768 to 32767
        Units: V
        Default: 2400
        """
        # Automatic CR6[15:0] bit packing
        self._update_cr(6, value, bit_low=0, bit_high=15)
```

**See:** [.claude/agents/docgen-context/agent.md](../../.claude/agents/docgen-context/agent.md)

---

## Agent 5: hardware-debug-context

**Domain:** FSM debugging, state machine analysis, signal tracing

**Role:** Hardware debugging domain expert

### Responsibilities

**✅ Does:**
- Debug FSM state machines via oscilloscope monitoring
- Decode voltage-encoded states using FSM Observer Pattern
- Monitor state transitions in real-time
- Analyze timing (state durations, timeouts)
- Diagnose faults (stuck states, unexpected transitions)
- Trace multi-channel signals

**❌ Does NOT:**
- Modify control registers (read-only for debugging)
- Deploy hardware or configure routing
- Generate code or documentation
- Parse YAML specifications

### Domain Expertise

**FSM Observer Pattern:**
- Voltage-encoded state debugging (DAC output → oscilloscope)
- State mapping with quantization tolerance (±0.15V typical)
- Common FSM patterns (Ready → Armed → Firing → Cooling)

**Oscilloscope techniques:**
- Latency handling (500ms stabilization delay)
- Polling vs continuous monitoring
- Stable sampling (midpoint of buffer)

### Inputs & Outputs

**Inputs:**
- Deployed hardware (device IP, slot configuration)
- Optional: FSM state definitions from `manifest.json`
- Oscilloscope routing configuration

**Outputs:**
- Debug reports with current state, recent transitions
- State timing analysis
- Fault diagnosis with recommendations
- Real-time monitoring logs

### Available Commands

**1. `/debug-fsm <app_name> --device <ip>` - FSM state analysis**
- Connect to oscilloscope
- Read FSM state voltage (typically OutC → Osc Ch1)
- Decode voltage to state name using manifest
- Display current state, recent transitions, duration
- Check for fault conditions (negative voltages, stuck states)

**2. `/monitor-state <app_name> --device <ip> --duration <seconds>`**
- Continuously monitor FSM state for specified duration
- Log all state transitions with timestamps
- Measure state durations and cycle times
- Detect faults and anomalies

**3. `/trace-signals <app_name> --device <ip> --channels <ch1,ch2>`**
- Multi-channel signal capture
- Synchronized timing analysis
- Correlation between signals

**4. `/analyze-timing <app_name> --device <ip>`**
- Measure actual timing vs expected (from manifest)
- Validate timeout behavior
- Clock cycle counting

### FSM Debugging Example

**Voltage-to-state decoding:**
```python
# FSM states from manifest.json
fsm_states = {
    0: {"name": "READY", "voltage": 0.0},
    1: {"name": "ARMED", "voltage": 0.5},
    2: {"name": "FIRING", "voltage": 1.0},
    3: {"name": "COOLING", "voltage": 1.5},
    4: {"name": "DONE", "voltage": 2.0},
    7: {"name": "HARDFAULT", "voltage": -2.5},
}

# Oscilloscope reading
voltage = 0.52  # ±0.15V tolerance

# Decoded state: ARMED (expected: 0.5V, actual: 0.52V)
```

**Typical debug session:**
```
[00:00] READY (0.00V)
[00:05] ARMED (0.52V) - transition detected
[00:07] FIRING (1.02V) - transition detected
[00:07] COOLING (1.49V) - transition detected (256ns after FIRING)
[00:07] DONE (1.79V) - transition detected (64ns after COOLING)
[00:12] READY (0.00V) - cycle complete (total: 7.2s)

✅ Normal operation
   State transitions: 5
   Timing: Within expected ranges
```

**See:** [.claude/agents/hardware-debug-context/agent.md](../../.claude/agents/hardware-debug-context/agent.md)

---

## Agent Interaction Patterns

### Pattern 1: Sequential Pipeline

**Workflow:** `/workflow new-probe spec.yaml`

```
1. forge-context: /validate spec.yaml
   └─► Output: Validation report

2. forge-context: /generate spec.yaml
   └─► Output: Well-formed package (manifest.json, VHDL)

3. deployment-context: /discover
   └─► Output: Available devices list

4. deployment-context: /deploy app_name --device 192.168.1.100
   └─► Output: Deployed hardware

5. docgen-context: /gen-docs app_name
   └─► Output: Documentation files

6. hardware-debug-context: /monitor-state app_name --device 192.168.1.100
   └─► Output: FSM state monitoring
```

**Dependencies:** Each step requires previous step's output

---

### Pattern 2: Parallel Execution

**Workflow:** `/workflow document app_name` (after generation complete)

```
forge-context: /generate spec.yaml
   └─► manifest.json created
       │
       ├─► deployment-context: /deploy app_name    (parallel)
       │   └─► Hardware deployed
       │
       └─► docgen-context: /gen-docs app_name      (parallel)
           └─► Docs generated
```

**No dependencies:** deployment and docgen both read manifest.json, no shared state

---

### Pattern 3: Iterative Development

**Workflow:** `/workflow iterate spec.yaml`

```
User: Modify spec.yaml
  │
  ├─► forge-context: /generate spec.yaml --force
  │   └─► Package regenerated
  │
  └─► deployment-context: /deploy app_name --force
      └─► Hardware redeployed
```

**Fast path:** Skip validation, use cached device info

---

### Pattern 4: Cross-Context Query

**User:** "Show me the complete deployment picture"

```
workflow-coordinator:
  1. Read apps/app_name/manifest.json
  2. Read apps/app_name/control_registers.json
  3. Query deployment-context for device state
  4. Synthesize report:
     - Package: app_name v1.0.0
     - Registers: 3 used (CR6-CR8), 69.8% efficiency
     - Deployed: Yes, on 192.168.1.100, Slot 2
     - Status: Monitoring active
```

**No agent delegation needed:** workflow-coordinator synthesizes from files and state

---

## Workflow Examples

### Example 1: New Probe Development

**Command:** `/workflow new-probe apps/minimal_probe/minimal_probe.yaml`

**Pipeline:**
```
Step 1: Validate specification
  forge-context: /validate minimal_probe.yaml
  ✅ Schema valid, 3 datatypes, platform: moku_go

Step 2: Generate package
  forge-context: /generate minimal_probe.yaml
  ✅ Generated package: apps/minimal_probe/
     - manifest.json
     - control_registers.json
     - minimal_probe_custom_inst_shim.vhd
     - minimal_probe_custom_inst_main.vhd
  ✅ Efficiency: 3 signals → 2 registers (52% used)

Step 3: Generate documentation
  docgen-context: /gen-docs minimal_probe
  ✅ Created docs/README.md, register_map.md

Step 4: Discover devices
  deployment-context: /discover
  ✅ Found 1 device: Moku:Go (192.168.1.100)

Step 5: Deploy to hardware
  deployment-context: /deploy minimal_probe --device 192.168.1.100
  ✅ Deployed to Slot 2, Oscilloscope to Slot 1
  ✅ Set control registers: CR6, CR7
  ✅ Configured routing: Input1 → Slot2, Slot2OutA → Output1

Step 6: Monitor initial state
  hardware-debug-context: /monitor-state minimal_probe --device 192.168.1.100
  ✅ Current state: READY (0.00V)
  ✅ No faults detected

✅ Deployment complete!
```

---

### Example 2: Fast Iteration

**Command:** `/workflow iterate apps/DS1140_PD/DS1140_PD.yaml --deploy`

**Pipeline:**
```
Step 1: Regenerate package (skip validation)
  forge-context: /generate DS1140_PD.yaml --force
  ✅ Regenerated in 0.4s

Step 2: Redeploy immediately (use cached device)
  deployment-context: /deploy DS1140_PD --force
  ✅ Redeployed to 192.168.1.100 (cached) in 2.1s

✅ Total time: 2.5s
```

**Use case:** Tweaking YAML defaults, testing register changes

---

### Example 3: Hardware Debugging

**Command:** `/workflow debug DS1140_PD`

**Pipeline:**
```
Step 1: Deploy package
  deployment-context: /deploy DS1140_PD --device 192.168.1.100
  ✅ Deployed

Step 2: Start FSM monitoring
  hardware-debug-context: /monitor-state DS1140_PD --device 192.168.1.100 --duration 60

  [00:00] READY (0.00V)
  [00:05] ARMED (0.52V) - transition detected
  ⚠️  State duration: 55 seconds (exceeds arm_timeout: 255ms)

  Recommendations:
  - Check trigger input connected
  - Verify trigger_threshold setting
  - Monitor for FIRING transition

Step 3: Analyze timing
  hardware-debug-context: /analyze-timing DS1140_PD --device 192.168.1.100

  Expected arm_timeout: 255ms
  Actual time in ARMED: 55s
  ❌ Timeout not functioning - possible causes:
     - arm_timeout register not read by VHDL
     - Timeout counter not implemented
     - Clock divider incorrect
```

**Use case:** FSM stuck in unexpected state, needs diagnosis

---

## Design Principles

### Principle 1: Single Responsibility

**Each agent has ONE domain:**
- forge-context: Code generation
- deployment-context: Hardware deployment
- docgen-context: Documentation generation
- hardware-debug-context: FSM debugging
- workflow-coordinator: Workflow orchestration

**Anti-pattern:** Agent trying to do multiple domains (e.g., forge-context deploying hardware)

---

### Principle 2: Contract-Based Interfaces

**All agents communicate via well-defined contracts:**
- forge-context → downstream: `manifest.json` (JSON Schema validated)
- deployment-context → hardware-debug: Device IP, slot config
- No hidden dependencies or shared state

**Benefits:**
- Clear API boundaries
- Versioned schemas
- Parallel execution possible

---

### Principle 3: Delegation Over Duplication

**workflow-coordinator delegates, never duplicates:**
```
❌ BAD:
workflow-coordinator generates VHDL directly
(duplicates forge-context logic)

✅ GOOD:
workflow-coordinator delegates to forge-context: /generate spec.yaml
(forge-context is the domain expert)
```

---

### Principle 4: Fail Fast with Recovery Guidance

**Error handling pattern:**
1. Agent detects error (e.g., YAML validation fails)
2. Agent returns specific error with context
3. workflow-coordinator provides recovery steps
4. User can retry specific step

**Example:**
```
forge-context: ❌ Validation failed: Unknown datatype 'voltage_10v_s16'

workflow-coordinator: Here are valid voltage types:
  - voltage_output_05v_s16
  - voltage_signed_s16
  - ...

  Update YAML and run: /validate spec.yaml
```

---

### Principle 5: Stateless Agents (Except Coordinator)

**Specialized agents are stateless:**
- forge-context: Reads YAML, writes package, done
- deployment-context: Reads package, deploys, done
- docgen-context: Reads package, writes docs, done

**workflow-coordinator tracks state:**
- Current package
- Last deployment
- Pipeline stage

**Benefits:**
- Agents can be invoked independently
- No synchronization issues
- Clear state ownership

---

## Summary

**5 agents, 5 domains:**

| Agent | Domain | Input | Output | Commands |
|-------|--------|-------|--------|----------|
| workflow-coordinator | Orchestration | User intent | Workflow results | `/workflow *` |
| forge-context | Code generation | YAML spec | Well-formed package | `/generate`, `/validate`, `/map-registers` |
| deployment-context | Hardware deployment | Package + device | Deployed hardware | `/deploy`, `/discover` |
| docgen-context | Documentation | Package metadata | Docs/UIs/APIs | `/gen-docs`, `/gen-ui`, `/gen-python-api` |
| hardware-debug-context | FSM debugging | Deployed hardware | Debug reports | `/debug-fsm`, `/monitor-state`, `/trace-signals` |

**Key success factors:**
- Clear boundaries → No responsibility overlap
- Contract-based → Clean handoffs via manifest.json
- Hub-and-spoke → forge at center, multiple consumers
- Delegation → workflow-coordinator orchestrates, doesn't duplicate
- Parallel execution → deployment + docgen can run simultaneously

---

**See also:**
- [overview.md](overview.md) - High-level architecture
- [code_generation.md](code_generation.md) - forge-context internals
- [design_decisions.md](design_decisions.md) - Why 5 agents?
- [.claude/shared/package_contract.md](../../.claude/shared/package_contract.md) - Agent communication contract

---

**Last Updated:** 2025-11-03 (Phase 6D)
**Maintained By:** moku-instrument-forge team
