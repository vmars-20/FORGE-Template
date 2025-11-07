# Customize Monorepo

Guide users through customizing this **Moku Instrument Forge** template for their specific probe hardware.

---

## 🎯 What This Command Does

Helps you add **YOUR probe models** to the FORGE ecosystem. The template is already configured for Moku platform development - you're customizing which probes you integrate with.

---

## ⚠️ Pre-Flight Check

**Run this FIRST** to ensure setup is correct:

```bash
# Verify submodules initialized
git submodule status --recursive

# Initialize if needed (lines starting with '-')
git submodule update --init --recursive

# Install dependencies
uv sync

# Test imports
python -c "from moku_models import MOKU_GO_PLATFORM; print('✅ moku-models works')"
python -c "from riscure_models import DS1120A_PLATFORM; print('✅ riscure-models works')"
```

**If imports fail:** Run `uv pip install -e libs/moku-models/ -e libs/riscure-models/`

**Only proceed after these checks pass!**

---

## 📋 Foundation (Already Configured)

This template provides everything you need for Moku FPGA development:

### ✅ Core Platform (Required)
- **`libs/moku-models/`** - Moku platform specifications (Go/Lab/Pro/Delta)
- **`libs/platform/`** - FORGE foundational entities (MCC interface + wrapper)
- **`examples/basic-probe-driver/`** - Complete production reference

### ✅ VHDL Development Tools
- **`tools/forge-codegen/`** - YAML → VHDL code generator
- **`libs/forge-vhdl/`** - Reusable VHDL components
- **`libs/riscure-models/`** - Reference probe implementation

### ✅ AI Development
- **`.claude/agents/cocotb-integration-test/`** - CocoTB test generation (tested)
- **`.claude/commands/`** - Development commands

**DO NOT modify these** - they're production-ready and tested.

---

## 🔧 Customization: Add Your Probes

### Typical Workflow

**Most common scenario:** You're adding YOUR probe models to work with Moku.

```
Template (as provided)          Your Customization
━━━━━━━━━━━━━━━━━━━          ━━━━━━━━━━━━━━━━━━━━━━
libs/moku-models/      ───►   libs/moku-models/         ✅ Keep (Core!)
libs/riscure-models/   ───►   libs/riscure-models/      ✅ Keep (Reference)
                       ───►   libs/YOUR-probe-models/   ➕ Add (Your probes!)
tools/forge-codegen/   ───►   tools/forge-codegen/      ✅ Keep (VHDL gen)
libs/forge-vhdl/       ───►   libs/forge-vhdl/          ✅ Keep (VHDL utils)
examples/              ───►   examples/                 ✅ Keep (BPD reference)
libs/platform/         ───►   libs/platform/            ✅ Keep (FORGE entities)
```

**Result:** Template + your probe models = complete development environment

---

## Step-by-Step: Adding Your Probe Models

### Step 1: Create Your Probe Models Repository

Use `libs/riscure-models/` as template structure:

```bash
# Create new repo for your probe specs
# Example structure:
your-probe-models/
├── your_probe_models/          # Python package
│   ├── __init__.py
│   ├── probes.py              # Pydantic models
│   └── validation.py          # Voltage safety
├── tests/                      # Pytest tests
├── llms.txt                    # Quick reference (copy from riscure-models)
├── CLAUDE.md                   # Complete guide (copy from riscure-models)
├── pyproject.toml             # Package config
└── README.md                   # Usage guide
```

**Key components to include:**
- **Pydantic models** - Probe electrical specifications
- **Voltage safety validation** - Range checking (see riscure-models example)
- **Port definitions** - Inputs, outputs, control signals
- **3-tier documentation** - llms.txt → CLAUDE.md → source

### Step 2: Add as Submodule

```bash
# Add your probe models as git submodule
git submodule add https://github.com/YOUR-USERNAME/your-probe-models.git libs/your-probe-models/

# Update workspace configuration
# Edit pyproject.toml and add to [tool.uv.workspace] members:
#   "libs/your-probe-models",

# Sync dependencies
uv sync

# Test import
python -c "from your_probe_models import YOUR_PROBE; print('✅ Works!')"
```

### Step 3: Update Documentation

**Update `llms.txt`** - Add your probe models to component catalog:

```markdown
### Core Platform (git submodules)

| Component | Purpose | Quick Ref |
|-----------|---------|-----------|
| [moku-models](libs/moku-models/) | **REQUIRED** - Moku platform specifications | [llms.txt](libs/moku-models/llms.txt) |
| [riscure-models](libs/riscure-models/) | Example probe specs (reference) | [llms.txt](libs/riscure-models/llms.txt) |
| [your-probe-models](libs/your-probe-models/) | YOUR probe specifications | [llms.txt](libs/your-probe-models/llms.txt) |
```

**Update `CLAUDE.md`** - Add section about your probe integration

**Update `README.md`** - Replace Riscure examples with your probes (or keep both!)

### Step 4: Commit Changes

```bash
git add .gitmodules libs/your-probe-models/ pyproject.toml llms.txt CLAUDE.md README.md
git commit -m "feat: Add YOUR-probe-models for custom probe support"
git push
```

---

## 🎯 Common Scenarios

### Scenario 1: "I'm using Moku + Riscure EMFI"

**Action:** NO customization needed! Use template as-is.

```bash
git clone --recurse-submodules <repo>
cd <repo>
uv sync
# Start developing!
```

### Scenario 2: "I'm using Moku + Custom Laser Probes" (MOST COMMON)

**Actions:**
1. ✅ Keep everything in template (Riscure as reference)
2. ➕ Create `libs/laser-models/` (use riscure-models as template)
3. ➕ Add as submodule (follow steps above)
4. 📝 Update documentation

### Scenario 3: "I'm using Moku + Multiple Probe Types"

**Actions:**
1. ✅ Keep everything
2. ➕ Add `libs/laser-models/`
3. ➕ Add `libs/rf-models/`
4. ➕ Add `libs/whatever-models/`
5. 📝 Update docs to reflect multi-probe setup

**All probes coexist** in `libs/` - no conflicts!

### Scenario 4: "I only need Python, no VHDL/FPGA" (RARE)

**Actions:**
1. ✅ Keep `libs/moku-models/` + probe models
2. ❌ Remove `tools/forge-codegen/`
3. ❌ Remove `libs/forge-vhdl/`

**Note:** This is unusual for Moku development. Most custom instrument work involves FPGA!

---

## ⚠️ What NOT to Remove

### Never Remove These:
- ⛔ **`libs/moku-models/`** - This is the CORE! Without it, you're not developing for Moku
- ⛔ **`libs/platform/`** - FORGE foundational entities (MCC interface required!)
- ⛔ **`examples/basic-probe-driver/`** - Production reference (you'll need this!)

### Be Careful Removing These:
- ⚠️ **`tools/forge-codegen/`** - Only remove if doing pure Python (no VHDL)
- ⚠️ **`libs/forge-vhdl/`** - Only remove if doing pure Python (no VHDL)

### Safe to Remove (But Recommended to Keep):
- ✅ **`libs/riscure-models/`** - Only if not using Riscure AND you're confident
  - **Recommendation:** Keep as reference even if using different probes!
  - Shows voltage safety patterns
  - Good template for your own probe models

---

## 📚 Reference Documentation

### Creating Probe Models
- **Template:** `libs/riscure-models/` - Copy this structure
- **Voltage safety:** See `riscure_models/validation.py`
- **3-tier docs:** llms.txt → CLAUDE.md → source (copy pattern from riscure-models)

### FORGE Architecture
- **Quick start:** `examples/basic-probe-driver/README.md`
- **Complete spec:** `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md`
- **Templates:** `libs/platform/FORGE_App_Wrapper.vhd`

### Integration Patterns
- **Root guide:** `CLAUDE.md` - Complete architecture
- **Quick ref:** `llms.txt` - Component catalog
- **Manifest:** `.claude/manifest.json` - Programmatic structure

---

## 🚀 Next Steps After Customization

1. **Test everything:**
   ```bash
   git submodule status --recursive  # All submodules initialized?
   uv sync                           # Dependencies installed?
   pytest                            # Tests passing?
   ```

2. **Update project name:**
   - GitHub repository name
   - README.md title
   - CLAUDE.md title

3. **Start building:**
   - Study BPD example
   - Copy patterns
   - Adapt for your probes
   - Test with CocoTB

4. **Share back:**
   - Document patterns
   - Consider contributing improvements
   - Share probe models (if not proprietary)

---

## 💡 Philosophy

**This is YOUR template now!**

- You own it - customize freely
- FORGE patterns are proven - don't break them
- Keep the 3-tier documentation - helps AI agents
- Islands of authority - each submodule is self-contained
- Test after each change

**The template gives you:**
- ✅ Proven FORGE architecture
- ✅ Production-ready tools
- ✅ Complete BPD reference
- ✅ Clean foundation

**You add:**
- ➕ Your probe specifications
- ➕ Your instrument logic
- ➕ Your test cases
- ➕ Your innovations

**Result:** Production-ready custom Moku instruments! 🚀

---

## Questions?

- **Documentation:** Start with `examples/basic-probe-driver/README.md`
- **Architecture:** See `CLAUDE.md` for complete details
- **FORGE patterns:** See `libs/platform/` and BPD example
- **Agent help:** Use `.claude/agents/cocotb-integration-test/` (tested)

**Welcome to the FORGE ecosystem!**
