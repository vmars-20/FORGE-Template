# Moku Instrument Forge

> **Build custom FPGA instruments for Moku platforms with safety, clarity, and AI assistance**

Transform your hardware probes into production-ready Moku instruments using the **FORGE architecture** - a proven pattern for safe, maintainable custom FPGA firmware.

---

## ✨ What is FORGE?

**FORGE** (Formal Organization for Register-Gated Execution) is an architectural pattern for building custom instruments on Moku platforms. It solves the fundamental challenge of safely coordinating network-settable registers with high-speed FPGA state machines.

### The Problem FORGE Solves

When building custom FPGA instruments, you face a critical challenge:
- **Network layer** sets control registers asynchronously (user changes settings)
- **FPGA layer** runs state machines at 125-200 MHz
- **Chaos ensues** when registers change mid-cycle

**FORGE provides the solution:**
- ✅ **Safe initialization** - 3-bit handshaking prevents premature starts
- ✅ **Clean abstraction** - Your FSM uses typed signals, not raw registers
- ✅ **Synchronization** - Shim layer protects against async updates
- ✅ **Proven pattern** - Production-tested in Basic Probe Driver (BPD)

---

## 🚀 Quick Start

### Create Your First Instrument

```bash
# 1. Use this template to create your repository on GitHub
# 2. Clone with submodules
git clone --recurse-submodules https://github.com/YOUR-USERNAME/your-instrument.git
cd your-instrument

# 3. Setup environment
uv sync

# 4. Verify setup
python -c "from moku_models import MOKU_GO_PLATFORM; print('✅ Ready to FORGE!')"

# 5. Study the reference implementation
cd examples/basic-probe-driver/
cat vhdl/FORGE_ARCHITECTURE.md
```

**Next:** Read `examples/basic-probe-driver/README.md` to see FORGE in action.

---

## 🏗️ The FORGE Architecture

### Three Layers, One Goal: Safety

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: BRAM Loader (future)                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Pre-loads register values from BRAM before execution   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Shim (register mapping + synchronization)         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Unpacks Control Registers → app_reg_* signals       │ │
│  │ • Respects ready_for_updates from main app            │ │
│  │ • Type conversions (voltage, time, boolean)           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Main (your application logic)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • FSM/application logic                               │ │
│  │ • Uses app_reg_enable, app_reg_voltage, etc.         │ │
│  │ • NO knowledge of Control Registers!                  │ │
│  │ • Signals ready_for_updates when safe                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Innovation: CR0[31:29] Control Scheme

```vhdl
-- Extract FORGE control signals from CR0
forge_ready <= Control0(31);  -- Network: "registers loaded"
user_enable <= Control0(30);  -- User: "enable instrument"
clk_enable  <= Control0(29);  -- Clock: "clocking enabled"

-- 4-condition safe start (all must be high)
global_enable <= forge_ready AND user_enable AND clk_enable AND loader_done;
```

**Why this matters:** Your instrument NEVER starts until all 4 conditions are met. No glitches, no race conditions, no surprises.

---

## 📦 What's in the Box?

### Core Foundation

| Component | What It Does | Why You Need It |
|-----------|--------------|-----------------|
| **`libs/platform/`** | FORGE entities (MCC interface + wrapper template) | **Required** - Your instruments start here |
| **`libs/moku-models/`** | Moku platform specs (Go/Lab/Pro/Delta) | **Required** - Hardware definitions |
| **`examples/basic-probe-driver/`** | Complete FORGE reference implementation | **Study this** - Production example |

### VHDL Development Tools

| Component | What It Does | When You Need It |
|-----------|--------------|------------------|
| **`tools/forge-codegen/`** | YAML → VHDL code generator | Generating register maps |
| **`libs/forge-vhdl/`** | Reusable VHDL components | Clock dividers, voltage utils, FSM observer |
| **`libs/riscure-models/`** | Example probe specifications | Building probe integration |

### AI Development Assistance

| Component | What It Does |
|-----------|--------------|
| **`.claude/agents/cocotb-integration-test/`** | Automated CocoTB test generation (tested) |
| **`.claude/commands/customize-monorepo`** | Interactive template customization |

**Note:** Only `cocotb-integration-test` agent has been tested. Other agents may need work.

---

## 🎯 Your First Custom Instrument

### Step 1: Define Your Application Registers (YAML)

```yaml
# my-instrument.yaml
app_registers:
  - name: enable
    datatype: boolean
    description: "Master enable for instrument"

  - name: output_voltage
    datatype: voltage_output_5v0_s16  # Type-safe voltage (0-5V)
    min_value: 0
    max_value: 5000  # millivolts
    description: "Output voltage level"

  - name: pulse_width
    datatype: time_ns_u32  # Nanosecond timing
    min_value: 8
    max_value: 1000000
    description: "Pulse width in nanoseconds"
```

### Step 2: Copy and Adapt BPD Structure

```bash
# Use BPD as template
cp -r examples/basic-probe-driver/vhdl my-instrument/

# Study these files in order:
# 1. CustomWrapper_bpd_forge.vhd - MCC interface integration
# 2. BPD_forge_shim.vhd - Register unpacking pattern
# 3. src/basic_probe_driver_custom_inst_main.vhd - FSM implementation
```

### Step 3: Replace BPD Logic with Yours

**Keep the FORGE patterns:**
- ✅ CR0[31:29] control scheme
- ✅ app_reg_* abstraction (NO raw Control Registers in main!)
- ✅ ready_for_updates handshaking
- ✅ 3-layer architecture

**Replace BPD specifics:**
- Probe control → Your instrument control
- FI timing → Your timing requirements
- Monitor feedback → Your input processing
- FSM states → Your state machine

---

## 🧪 Testing Your Instrument

### Progressive Testing (P1 → P2 → P3)

```bash
cd your-instrument/vhdl/tests/

# P1: LLM-optimized tests (<20 lines each, fast feedback)
uv run python run.py

# P2: Comprehensive validation (detailed scenarios)
TEST_LEVEL=P2_INTERMEDIATE uv run python run.py

# P3: Full coverage (every edge case)
TEST_LEVEL=P3_COMPREHENSIVE uv run python run.py
```

**See:** `examples/basic-probe-driver/vhdl/tests/README.md` for testing guide.

---

## 🎓 Learning Path

### New to FORGE?

1. **Start:** Read this README (you're here!)
2. **Understand:** `examples/basic-probe-driver/README.md` - What BPD demonstrates
3. **Deep dive:** `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md` - Complete spec
4. **Implement:** Copy BPD structure, replace logic, test

### Need Architecture Details?

- **Complete spec:** [CLAUDE.md](CLAUDE.md) - Full architecture, MCC interface, integration
- **Quick ref:** [llms.txt](llms.txt) - Component catalog for AI navigation
- **Customization:** Run `/customize-monorepo` in Claude Code

### Ready to Build?

1. Study `libs/platform/FORGE_App_Wrapper.vhd` - Your starting template
2. Reference `libs/platform/MCC_CustomInstrument.vhd` - MCC interface entity
3. Follow BPD patterns exactly (proven in production!)

---

## 🏛️ Foundational Entities

**Located in `libs/platform/` - DO NOT MODIFY THESE:**

| Entity | Purpose | Status |
|--------|---------|--------|
| **MCC_CustomInstrument** | Simplified MCC interface (16 CR, 16 SR) | Authoritative |
| **FORGE_App_Wrapper** | 3-layer wrapper template | Customize for your app |

**Key Documentation:**
```vhdl
-- CR0[31:29] is RESERVED for FORGE control scheme
-- CR0[28:0] + CR1-CR15 available for your application
forge_ready <= Control0(31);  -- Network ready
user_enable <= Control0(30);  -- User enabled
clk_enable  <= Control0(29);  -- Clock enabled
```

---

## 🌍 Ecosystem

### Platform Support

- **Moku:Go** - 125 MHz, compact form factor
- **Moku:Lab** - 200 MHz, benchtop instrument
- **Moku:Pro** - 200 MHz, rackmount system
- **Moku:Delta** - (future support)

### Probe Integration

This template includes **Riscure EMFI probe models** as reference:
- Voltage safety validation
- Port specifications
- Documentation patterns

**Add your probes:** Use `libs/riscure-models/` as template, create `libs/YOUR-probe-models/`

### Type System

**23 serialization types** for YAML → VHDL:
- Voltage types: 0-3.3V, 0-5V, ±0.5V, ±20V, ±25V
- Time types: nanoseconds, microseconds, milliseconds
- Boolean, integers (signed/unsigned), enumerated types

**See:** `tools/forge-codegen/llms.txt` for complete type catalog

---

## 🧩 Directory Structure

```
your-moku-instrument/
├── libs/
│   ├── platform/              # FORGE foundational entities
│   │   ├── MCC_CustomInstrument.vhd    # MCC interface (DO NOT MODIFY)
│   │   └── FORGE_App_Wrapper.vhd       # 3-layer template (CUSTOMIZE)
│   ├── moku-models/           # Submodule: Platform specifications
│   ├── riscure-models/        # Submodule: Example probe specs
│   └── forge-vhdl/            # Submodule: VHDL utilities
│
├── tools/
│   └── forge-codegen/         # Submodule: YAML → VHDL generator
│
├── examples/
│   └── basic-probe-driver/    # Complete FORGE reference
│       ├── README.md          # Usage guide
│       ├── BPD-RTL.yaml       # Register specification
│       └── vhdl/              # VHDL implementation
│           ├── FORGE_ARCHITECTURE.md   # Architecture spec
│           ├── CustomWrapper_bpd_forge.vhd
│           ├── BPD_forge_shim.vhd
│           ├── BPD_forge_main.vhd
│           └── tests/         # CocoTB progressive tests
│
├── docs/
│   └── vendor-reference/      # MCC upstream tracking
│
├── .claude/
│   ├── agents/                # AI agents (cocotb-integration-test tested)
│   └── commands/              # Slash commands
│
├── CLAUDE.md                  # Complete architecture guide
├── llms.txt                   # AI navigation quick ref
└── README.md                  # This file
```

---

## 📚 Documentation Philosophy

### 3-Tier Progressive Disclosure

**Optimized for both humans AND AI agents:**

| Tier | What | When | Token Cost |
|------|------|------|------------|
| **Tier 1** | `llms.txt` files | Always load first | ~500-1000 |
| **Tier 2** | `CLAUDE.md` files | When designing/integrating | ~3000-5000 |
| **Tier 3** | Source code + tests | When implementing | Variable |

**Why this matters:**
- AI agents load minimal context first
- Expand to detailed docs only when needed
- Source code accessed selectively
- Fast, efficient context management

---

## 🤝 Contributing

This is a **template repository** - make it yours!

### Using This Template

1. Click **"Use this template"** on GitHub
2. Clone with submodules: `git clone --recurse-submodules ...`
3. Customize for your probes/instruments
4. Build amazing things!

### Sharing Back

If you create generally useful patterns:
- Document them for others
- Consider contributing enhancements
- Share custom probe models (if not proprietary)

### Submodule Development

1. Make changes in appropriate submodule repository
2. Write CocoTB tests for VHDL changes
3. Validate with `pytest`
4. Update submodule reference in parent repo

---

## ⚡ Why FORGE?

### Before FORGE
```vhdl
-- Main app directly reads Control Registers
if Control1(0) = '1' then  -- What does bit 0 mean? 🤔
    voltage_out <= Control2;  -- Raw bits, no type safety! 😱
    -- Hope nothing changes mid-cycle! 🤞
end if;
```

### After FORGE
```vhdl
-- Main app uses typed, meaningful signals
if app_reg_enable = '1' then  -- Clear intent ✅
    voltage_out <= app_reg_output_voltage;  -- Type-safe voltage ✅
    -- ready_for_updates handshaking prevents async issues ✅
end if;
```

**Result:**
- Safer code (protected from async changes)
- Clearer intent (typed signals with meaningful names)
- Easier maintenance (main app doesn't know about registers)
- Production-proven (BPD validates the pattern)

---

## 📖 Version History

**v2.0.0** (2025-11-06) - Template Release
- FORGE 3-layer architecture established
- MCC CustomInstrument interface (16 CR, 16 SR)
- Complete BPD reference implementation
- 3-tier documentation system
- Comprehensive .gitignore
- Template-ready structure

---

## 📞 Get Help

- **Documentation:** Start with `examples/basic-probe-driver/README.md`
- **Architecture:** See `CLAUDE.md` for complete details
- **AI Assistance:** Run `/customize-monorepo` in Claude Code
- **Issues:** Open issues in your repository (this is a template!)

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## 🎉 Ready to Build?

```bash
# Clone this template
git clone --recurse-submodules https://github.com/YOUR-USERNAME/your-instrument.git

# Setup environment
cd your-instrument
uv sync

# Study the reference
cd examples/basic-probe-driver/
cat README.md

# Start building!
```

**Welcome to the FORGE ecosystem. Let's build something amazing! 🚀**
