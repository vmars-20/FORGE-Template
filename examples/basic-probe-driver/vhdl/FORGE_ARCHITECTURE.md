# BPD Forge Architecture Guide

**Version:** 1.0
**Date:** 2025-11-05
**Status:** Production

## Overview

The Basic Probe Driver (BPD) has been migrated to the **Forge 3-Layer Architecture**, providing MCC platform compliance, safe initialization, and code reusability.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: MCC_TOP_forge_loader.vhd                          │
│          (Future: Static loader, shared across all apps)    │
│          - Manages BRAM loading                             │
│          - Sets forge_ready flag                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: BPD_forge_shim.vhd                                │
│          (Generated register mapping)                        │
│          - Receives FORGE control signals                    │
│          - Maps CR20-CR30 → friendly names                   │
│          - Computes global_enable                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: BPD_forge_main.vhd                                │
│          (Hand-written application logic)                    │
│          - Completely MCC-agnostic                           │
│          - Only knows friendly signal names                  │
│          - Contains FSM and application logic                │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**Layer 1: MCC_TOP_forge_loader.vhd** (Future)
- Manages BRAM initialization from external sources
- Sets `forge_ready` flag when deployment complete
- Provides unified infrastructure for all Forge apps

**Layer 2: BPD_forge_shim.vhd** (Present)
- Register mapping: CR20-CR30 → application signals
- FORGE control scheme enforcement (CR0[31:29])
- Computes `global_enable` from 4 conditions
- **Generated from YAML** (future automation)

**Layer 3: BPD_forge_main.vhd** (Present)
- Pure application logic (FSM, timers, outputs)
- Zero knowledge of Control Registers
- Zero knowledge of FORGE control scheme
- **Portable** - can be reused in other platforms

---

## FORGE Control Scheme (CR0[31:29])

### The 3-Bit Handshake

The FORGE control scheme uses **3 bits** in Control Register 0 to ensure safe module initialization:

```
CR0[31] = forge_ready   ← Set by loader after deployment
CR0[30] = user_enable   ← User control (GUI toggle)
CR0[29] = clk_enable    ← Clock gating control
```

Plus a fourth signal (not a register bit):
```
loader_done             ← BRAM loader FSM completion
```

### Combined Enable Logic

```vhdl
global_enable = forge_ready AND user_enable AND clk_enable AND loader_done
```

**All four conditions must be met** for the module to operate.

### Safe Default Behavior

```
Power-on state: Control0 = 0x00000000
  ↓
All control bits = '0'
  ↓
global_enable = '0'
  ↓
Module DISABLED (safe state)
```

### Initialization Sequence

```
1. Power-on
   Control0 = 0x00000000
   → Module disabled ✓

2. MCC loader completes deployment
   Control0[31] ← 1  (forge_ready = 1)
   → Module still disabled (waiting for user)

3. BRAM loader completes (if used)
   loader_done ← 1
   → Module still disabled (waiting for user)

4. User enables module via GUI
   Control0[30] ← 1  (user_enable = 1)
   → Module still disabled (clock not enabled)

5. User enables clock
   Control0[29] ← 1  (clk_enable = 1)
   → Module ENABLED ✓

   global_enable = 1 AND 1 AND 1 AND 1 = 1
```

### Example: Typical Operation

```python
# Python pseudocode for MCC GUI

# Initial state (power-on)
moku.set_control(0, 0x00000000)  # All disabled

# Deployment complete (set by loader)
moku.set_control(0, 0x80000000)  # forge_ready = 1 (bit 31)

# User enables module
moku.set_control(0, 0xC0000000)  # forge_ready=1, user_enable=1 (bits 31,30)

# User enables clock
moku.set_control(0, 0xE0000000)  # All three bits set (bits 31,30,29)

# Module now operating!
# global_enable = forge_ready AND user_enable AND clk_enable AND loader_done
#               = 1           AND 1            AND 1          AND 1
#               = 1 ✓
```

---

## Register Mapping

### Control0: FORGE Control Scheme

| Bit | Signal | Description | Set By |
|-----|--------|-------------|--------|
| 31 | forge_ready | Deployment complete | MCC loader |
| 30 | user_enable | User enable/disable | User (GUI) |
| 29 | clk_enable | Clock gating | User (GUI) |
| 28-0 | (unused) | Reserved | - |

### CR20-CR30: Application Registers

| Register | Bits | Signal | Units | Description |
|----------|------|--------|-------|-------------|
| CR20 | [0] | arm_enable | - | Arm FSM (IDLE→ARMED) |
| CR20 | [1] | ext_trigger_in | - | External trigger input |
| CR20 | [2] | auto_rearm_enable | - | Re-arm after cooldown |
| CR20 | [3] | fault_clear | - | Clear fault state |
| CR21 | [15:0] | trig_out_voltage | mV | Trigger voltage |
| CR22 | [15:0] | trig_out_duration | ns | Trigger pulse width |
| CR23 | [15:0] | intensity_voltage | mV | Intensity voltage |
| CR24 | [15:0] | intensity_duration | ns | Intensity pulse width |
| CR25 | [15:0] | trigger_wait_timeout | s | Armed state timeout |
| CR26 | [23:0] | cooldown_interval | μs | Cooldown period |
| CR27 | [0] | monitor_enable | - | Enable monitor |
| CR27 | [1] | monitor_expect_negative | - | Polarity select |
| CR28 | [15:0] | monitor_threshold_voltage | mV | Threshold voltage |
| CR29 | [31:0] | monitor_window_start | ns | Window delay |
| CR30 | [31:0] | monitor_window_duration | ns | Window length |

---

## File Structure

```
bpd-tiny-vhdl/
├── forge_common_pkg.vhd              # FORGE control scheme (NEW)
├── BPD_forge_shim.vhd                # Layer 2: Register mapping (NEW)
├── BPD_forge_main.vhd                # Layer 3: FSM logic (REFACTORED)
├── CustomWrapper_bpd_forge.vhd       # Wrapper using Forge arch (NEW)
│
├── CustomWrapper_bpd.vhd             # Legacy wrapper (DEPRECATED)
├── CustomWrapper_test_stub.vhd       # Entity definition
│
├── src/
│   ├── basic_app_types_pkg.vhd       # Application types
│   ├── basic_app_voltage_pkg.vhd     # Voltage utilities
│   └── basic_app_time_pkg.vhd        # Time conversions
│
└── external_Example/                  # Reference implementation
    ├── DS1140_polo_main.vhd           # VOLO pattern (inspiration)
    ├── DS1140_polo_shim.vhd           # VOLO pattern (inspiration)
    └── volo_common_pkg.vhd            # VOLO common (inspiration)
```

---

## Migration from Legacy (2-Layer) to Forge (3-Layer)

### Before (2-Layer)

```vhdl
-- CustomWrapper_bpd.vhd
architecture bpd_wrapper of CustomWrapper is
    constant GLOBAL_ENABLE : std_logic := '1';  -- ❌ Always on!
begin
    BPD_FSM: entity WORK.basic_probe_driver_custom_inst_main
        generic map (CLK_FREQ_HZ => 125000000)
        port map (
            Clk => Clk,
            Reset => Reset,
            global_enable => GLOBAL_ENABLE,  -- ❌ No handshaking!

            arm_enable => Control0(0),       -- ❌ Direct register access
            ext_trigger_in => Control0(1),
            ...
        );
end architecture;
```

**Problems:**
- ❌ No safe initialization (module always on)
- ❌ No deployment handshaking
- ❌ Main entity knows about Control registers (not MCC-agnostic)
- ❌ Direct register mapping (not generated)

### After (3-Layer)

```vhdl
-- CustomWrapper_bpd_forge.vhd
architecture bpd_forge of CustomWrapper is
    signal forge_ready  : std_logic;
    signal user_enable  : std_logic;
    signal clk_enable   : std_logic;
    signal loader_done  : std_logic;
begin
    -- Extract FORGE control bits
    forge_ready <= Control0(31);  -- ✓ Loader handshaking
    user_enable <= Control0(30);  -- ✓ User control
    clk_enable  <= Control0(29);  -- ✓ Clock gating
    loader_done <= '1';           -- ✓ BRAM ready (future: actual loader)

    -- Instantiate shim (Layer 2)
    BPD_SHIM: entity WORK.BPD_forge_shim
        port map (
            forge_ready  => forge_ready,   -- ✓ Safe handshaking
            user_enable  => user_enable,
            clk_enable   => clk_enable,
            loader_done  => loader_done,

            app_reg_20 => Control20,       -- ✓ Application registers
            app_reg_21 => Control21,
            ...
        );
end architecture;
```

```vhdl
-- BPD_forge_shim.vhd (Layer 2)
architecture rtl of BPD_forge_shim is
    signal arm_enable : std_logic;
    signal ext_trigger_in : std_logic;
    ...
    signal global_enable : std_logic;
begin
    -- Compute global enable
    global_enable <= combine_forge_ready(forge_ready, user_enable,
                                         clk_enable, loader_done);

    -- Map registers to friendly names
    arm_enable     <= app_reg_20(0);    -- ✓ Friendly names
    ext_trigger_in <= app_reg_20(1);
    ...

    -- Instantiate main (Layer 3)
    BPD_MAIN: entity WORK.BPD_forge_main
        port map (
            Enable => global_enable,     -- ✓ Generic enable
            arm_enable => arm_enable,    -- ✓ Friendly names only
            ext_trigger_in => ext_trigger_in,
            ...
        );
end architecture;
```

```vhdl
-- BPD_forge_main.vhd (Layer 3)
entity BPD_forge_main is
    port (
        Clk    : in std_logic;
        Reset  : in std_logic;
        Enable : in std_logic;            -- ✓ Generic enable (no FORGE knowledge)
        ClkEn  : in std_logic;            -- ✓ Clock enable

        arm_enable     : in std_logic;    -- ✓ Only friendly names
        ext_trigger_in : in std_logic;
        ...

        OutputA : out signed(15 downto 0); -- ✓ MCC I/O (not status ports)
        OutputB : out signed(15 downto 0);
        OutputC : out signed(15 downto 0);
        OutputD : out signed(15 downto 0)
    );
end entity;
```

**Benefits:**
- ✓ Safe initialization (4-condition enable)
- ✓ Deployment handshaking (forge_ready)
- ✓ Main entity truly MCC-agnostic
- ✓ Shim layer generated from YAML (future)
- ✓ Follows VOLO/MCC platform standards

---

## forge_common_pkg API

### Constants

```vhdl
use WORK.forge_common_pkg.all;

-- FORGE_READY Control Scheme (CR0[31:29])
constant FORGE_READY_BIT  : natural := 31;
constant USER_ENABLE_BIT  : natural := 30;
constant CLK_ENABLE_BIT   : natural := 29;

-- BRAM Loader Protocol (CR10-CR14)
constant BRAM_ADDR_WIDTH : natural := 12;  -- 4KB addressing
constant BRAM_DATA_WIDTH : natural := 32;

-- Application Register Range (CR20-CR30)
constant APP_REG_MIN : natural := 20;
constant APP_REG_MAX : natural := 30;
```

### Functions

```vhdl
-- Combine FORGE_READY signals into global enable
function combine_forge_ready(
    forge_ready  : std_logic;
    user_enable  : std_logic;
    clk_enable   : std_logic;
    loader_done  : std_logic
) return std_logic;

-- Usage:
global_enable <= combine_forge_ready(forge_ready, user_enable,
                                     clk_enable, loader_done);
```

---

## Design Patterns

### Pattern 1: Shim Layer (Layer 2)

**Purpose:** Map Control Registers to friendly signal names

```vhdl
library WORK;
use WORK.forge_common_pkg.all;

entity AppName_forge_shim is
    port (
        -- FORGE control
        forge_ready, user_enable, clk_enable : in std_logic;
        loader_done : in std_logic;

        -- Application registers
        app_reg_20, app_reg_21, ... : in std_logic_vector(31 downto 0);

        -- MCC I/O
        InputA, InputB : in signed(15 downto 0);
        OutputA, OutputB, OutputC, OutputD : out signed(15 downto 0)
    );
end entity;

architecture rtl of AppName_forge_shim is
    signal friendly_name_1 : std_logic;
    signal friendly_name_2 : signed(15 downto 0);
    signal global_enable : std_logic;
begin
    -- Compute global enable
    global_enable <= combine_forge_ready(forge_ready, user_enable,
                                         clk_enable, loader_done);

    -- Map registers
    friendly_name_1 <= app_reg_20(0);
    friendly_name_2 <= signed(app_reg_21(15 downto 0));

    -- Instantiate main
    MAIN_INST: entity WORK.AppName_forge_main
        port map (
            Enable => global_enable,
            friendly_name_1 => friendly_name_1,
            friendly_name_2 => friendly_name_2,
            ...
        );
end architecture;
```

### Pattern 2: Main Layer (Layer 3)

**Purpose:** Application logic (completely MCC-agnostic)

```vhdl
entity AppName_forge_main is
    port (
        -- Standard control (NO forge_ready, NO Control registers!)
        Clk, Reset : in std_logic;
        Enable, ClkEn : in std_logic;

        -- Friendly signal names ONLY
        friendly_name_1 : in std_logic;
        friendly_name_2 : in signed(15 downto 0);

        -- BRAM (always present, even if unused)
        bram_addr : in std_logic_vector(11 downto 0);
        bram_data : in std_logic_vector(31 downto 0);
        bram_we : in std_logic;

        -- MCC I/O (native MCC types)
        OutputA, OutputB, OutputC, OutputD : out signed(15 downto 0)
    );
end entity;

architecture rtl of AppName_forge_main is
begin
    process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                -- Reset logic
            elsif Enable = '1' and ClkEn = '1' then
                -- Application logic using friendly names
            end if;
        end if;
    end process;
end architecture;
```

---

## Testing Considerations

### Unit Tests (CocoTB)

**Layer 3 (Main):**
- Test with `Enable = '0'` → Verify disabled state
- Test with `Enable = '1', ClkEn = '0'` → Verify frozen state
- Test with `Enable = '1', ClkEn = '1'` → Verify full operation

**Layer 2 (Shim):**
- Test `combine_forge_ready()` with all 16 input combinations
- Verify only `1111` produces `global_enable = '1'`

**Layer 1 (Wrapper):**
- Test Control0[31:29] extraction
- Verify proper instantiation of shim

### Integration Tests

**FORGE Control Sequence:**
```python
# Test safe default
dut.Control0.value = 0x00000000
await Timer(10, units='ns')
assert dut.global_enable.value == 0  # Disabled

# Test forge_ready only
dut.Control0.value = 0x80000000  # forge_ready=1
await Timer(10, units='ns')
assert dut.global_enable.value == 0  # Still disabled

# Test forge_ready + user_enable
dut.Control0.value = 0xC0000000  # forge_ready=1, user_enable=1
await Timer(10, units='ns')
assert dut.global_enable.value == 0  # Still disabled

# Test all three bits
dut.Control0.value = 0xE0000000  # All three bits set
await Timer(10, units='ns')
assert dut.global_enable.value == 1  # ✓ Enabled!
```

---

## Future Enhancements

### 1. Automated Shim Generation

```bash
# Generate shim from YAML specification
forge-codegen generate-shim basic_probe_driver.yaml \
    --output BPD_forge_shim.vhd \
    --package forge_common_pkg
```

### 2. Layer 1 Implementation

Create `MCC_TOP_forge_loader.vhd` as shared infrastructure:
- BRAM loading FSM
- Deployment handshaking
- Sets `forge_ready` flag
- Provides unified loader for all Forge apps

### 3. forge-vhdl Component Integration

Integrate forge-vhdl utilities into BPD_forge_main:
- `fsm_observer` for OutputC (FSM state debugging)
- `forge_voltage_5v_bipolar_pkg` for voltage handling
- `forge_util_clk_divider` for clock division (if needed)

---

## References

- **forge_common_pkg.vhd** - FORGE control scheme implementation
- **external_Example/** - VOLO reference implementation
- **libs/forge-vhdl/CLAUDE.md** - Forge VHDL coding standards
- **libs/forge-vhdl/llms.txt** - Forge component catalog

---

**Version History:**
- 1.0 (2025-11-05): Initial documentation for Forge 3-layer architecture
