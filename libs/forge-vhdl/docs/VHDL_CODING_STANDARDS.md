# VHDL Coding Standards & Design Rules

**Extracted from EZ-EMFI Project**
**For: Synthesis-ready, Verilog-compatible, maintainable VHDL**

---

## Table of Contents
1. [Core Principles](#core-principles)
2. [FSM Design Rules](#fsm-design-rules)
3. [Package Design](#package-design)
4. [Signal Naming Conventions](#signal-naming-conventions)
5. [Reset & Enable Hierarchy](#reset--enable-hierarchy)
6. [Synthesis Guidelines](#synthesis-guidelines)
7. [Verilog Compatibility](#verilog-compatibility)
8. [Safety & Constraints](#safety--constraints)
9. [Common Anti-Patterns](#common-anti-patterns)
10. [Code Examples](#code-examples)

---

## Core Principles

### 1. Synthesis-First Mindset
✅ Write for hardware, not simulation
✅ Avoid VHDL features that don't synthesize
✅ Keep synthesis tools in mind (Xilinx, Intel, others)

### 2. Readability Over Cleverness
✅ Explicit is better than implicit
✅ Clear signal names (not `x`, `y`, `temp`)
✅ Self-documenting code with helper functions

### 3. Testability
✅ Every module must have a testbench
✅ Minimize combinational depth
✅ Separate sequential and combinational logic

---

## FSM Design Rules

### ⚠️ CRITICAL: Use std_logic_vector for States (NOT Enums!)

**Why?** Verilog compatibility + synthesis predictability

```vhdl
-- ❌ DON'T: Enums don't translate well to Verilog
type state_t is (IDLE, ARMED, FIRING, DONE);
signal state : state_t;

-- ✅ DO: Explicit std_logic_vector encoding
constant STATE_IDLE   : std_logic_vector(2 downto 0) := "000";
constant STATE_ARMED  : std_logic_vector(2 downto 0) := "001";
constant STATE_FIRING : std_logic_vector(2 downto 0) := "010";
constant STATE_DONE   : std_logic_vector(2 downto 0) := "100";

signal state : std_logic_vector(2 downto 0);
```

### FSM Template (Recommended)

```vhdl
-- State definitions in package
package my_fsm_pkg is
    constant STATE_IDLE   : std_logic_vector(1 downto 0) := "00";
    constant STATE_ACTIVE : std_logic_vector(1 downto 0) := "01";
    constant STATE_DONE   : std_logic_vector(1 downto 0) := "10";
end package;

-- FSM implementation
architecture rtl of my_fsm is
    signal state, next_state : std_logic_vector(1 downto 0);
begin
    -- Synchronous state register
    FSM_REG: process(clk, rst_n)
    begin
        if rst_n = '0' then
            state <= STATE_IDLE;
        elsif rising_edge(clk) then
            if clk_en = '1' then
                state <= next_state;
            end if;
        end if;
    end process;

    -- Combinational next-state logic
    FSM_LOGIC: process(state, inputs)
    begin
        next_state <= state;  -- Default: hold state

        case state is
            when STATE_IDLE =>
                if trigger = '1' then
                    next_state <= STATE_ACTIVE;
                end if;

            when STATE_ACTIVE =>
                if done_condition then
                    next_state <= STATE_DONE;
                end if;

            when STATE_DONE =>
                next_state <= STATE_IDLE;

            when others =>
                next_state <= STATE_IDLE;  -- Safe default
        end case;
    end process;
end architecture;
```

### FSM Best Practices

✅ **Separate state register from next-state logic**
✅ **Always include `when others` case** (synthesis safety)
✅ **Reset to known safe state** (usually IDLE)
✅ **Use meaningful state names** (not S0, S1, S2)
✅ **Document state transitions** (comments or diagram)

---

## Package Design

### Standard Package Structure

```vhdl
--------------------------------------------------------------------------------
-- File: my_module_pkg.vhd
-- Description: Constants, types, and utilities for my_module
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

package my_module_pkg is

    ----------------------------------------------------------------------------
    -- Constants
    ----------------------------------------------------------------------------
    constant DATA_WIDTH : natural := 16;
    constant MAX_COUNT  : natural := 255;

    ----------------------------------------------------------------------------
    -- FSM States (std_logic_vector, not enum!)
    ----------------------------------------------------------------------------
    constant STATE_IDLE   : std_logic_vector(1 downto 0) := "00";
    constant STATE_ACTIVE : std_logic_vector(1 downto 0) := "01";

    ----------------------------------------------------------------------------
    -- Status Register Bits
    ----------------------------------------------------------------------------
    constant STATUS_READY_BIT : natural := 0;
    constant STATUS_BUSY_BIT  : natural := 1;
    constant STATUS_FAULT_BIT : natural := 7;  -- ALWAYS bit 7 for faults

    ----------------------------------------------------------------------------
    -- Helper Functions
    ----------------------------------------------------------------------------

    -- Clamp value to range
    function clamp(
        value : signed;
        max_val : signed
    ) return signed;

    -- Convert state to string (simulation only)
    function state_to_string(state : std_logic_vector(1 downto 0)) return string;

end package;

package body my_module_pkg is

    function clamp(value : signed; max_val : signed) return signed is
    begin
        if value > max_val then
            return max_val;
        elsif value < -max_val then
            return -max_val;
        else
            return value;
        end if;
    end function;

    function state_to_string(state : std_logic_vector(1 downto 0)) return string is
    begin
        case state is
            when STATE_IDLE   => return "IDLE";
            when STATE_ACTIVE => return "ACTIVE";
            when others       => return "UNKNOWN";
        end case;
    end function;

end package body;
```

### Package Best Practices

✅ **Group related constants together** (with comment headers)
✅ **Use `natural` for non-negative integers** (clearer than `integer range 0 to X`)
✅ **Put helper functions in package body** (not inline)
✅ **Document function parameters** (especially units)
✅ **Avoid package dependencies** (keep packages independent)

---

## Signal Naming Conventions

### Prefixes (Recommended)

| Prefix | Purpose | Example |
|--------|---------|---------|
| `ctrl_` | Control signals | `ctrl_enable`, `ctrl_reset` |
| `cfg_` | Configuration parameters | `cfg_threshold`, `cfg_duration` |
| `stat_` | Status/monitoring | `stat_busy`, `stat_fault` |
| `dbg_` | Debug outputs | `dbg_state_voltage` |

### Suffixes (Recommended)

| Suffix | Purpose | Example |
|--------|---------|---------|
| `_n` | Active-low signal | `rst_n`, `enable_n` |
| `_r` | Registered version | `data_r`, `count_r` |
| `_d` | Delayed version | `signal_d` |
| `_next` | Next-state value | `state_next` |

### Examples

```vhdl
-- ✅ GOOD: Clear, self-documenting
signal ctrl_enable        : std_logic;
signal ctrl_reset_n       : std_logic;  -- Active-low
signal cfg_threshold      : unsigned(15 downto 0);
signal stat_busy          : std_logic;
signal state_next         : std_logic_vector(2 downto 0);

-- ❌ BAD: Unclear, generic
signal en   : std_logic;
signal rst  : std_logic;  -- Active high or low?
signal thr  : unsigned(15 downto 0);
signal x    : std_logic;
signal ns   : std_logic_vector(2 downto 0);
```

---

## Reset & Enable Hierarchy

### Priority Order (Mandatory)

1. **Reset** - Forces safe state unconditionally
2. **ClkEn** - Freezes sequential logic (clock gating)
3. **Enable** - Disables functional operation

```vhdl
entity my_module is
    port (
        -- Standard control ports (IN THIS ORDER!)
        clk    : in std_logic;
        rst_n  : in std_logic;  -- Active-low reset
        clk_en : in std_logic;  -- Clock enable
        enable : in std_logic;  -- Functional enable

        -- Data ports
        data_in  : in  std_logic_vector(15 downto 0);
        data_out : out std_logic_vector(15 downto 0)
    );
end entity;

architecture rtl of my_module is
begin
    process(clk, rst_n)
    begin
        if rst_n = '0' then
            -- 1. RESET: Unconditional safe state
            data_out <= (others => '0');

        elsif rising_edge(clk) then
            if clk_en = '1' then
                -- 2. CLK_EN: Clock gating

                if enable = '1' then
                    -- 3. ENABLE: Functional operation
                    data_out <= data_in;
                else
                    -- Disabled: hold or safe state
                    data_out <= (others => '0');
                end if;
            end if;
            -- If clk_en = '0', state is frozen
        end if;
    end process;
end architecture;
```

### Reset Guidelines

✅ **Use active-low reset** (`rst_n`) - Industry standard
✅ **Asynchronous assert, synchronous deassert** (template above)
✅ **Reset to safe/known state** (not X or undefined)
✅ **Reset ALL registers** (don't leave any uninitialized)

---

## Synthesis Guidelines

### Inferred vs Instantiated

**Let synthesis infer when possible:**
- ✅ Registers (DFF)
- ✅ Simple arithmetic (+, -, *)
- ✅ Multiplexers
- ✅ Simple FSMs

**Explicitly instantiate when:**
- 🔧 Block RAM (BRAM)
- 🔧 DSP slices
- 🔧 Clock management (PLL, MMCM)
- 🔧 High-speed I/O (SERDES)

### Avoid Latches!

```vhdl
-- ❌ BAD: Incomplete sensitivity/case creates latch
process(sel, data_in)
begin
    if sel = '1' then
        data_out <= data_in;
    end if;
    -- What happens when sel = '0'? → LATCH!
end process;

-- ✅ GOOD: Complete case prevents latch
process(sel, data_in)
begin
    if sel = '1' then
        data_out <= data_in;
    else
        data_out <= (others => '0');  -- Explicit default
    end if;
end process;

-- ✅ BETTER: Registered output (no latches possible)
process(clk, rst_n)
begin
    if rst_n = '0' then
        data_out <= (others => '0');
    elsif rising_edge(clk) then
        if sel = '1' then
            data_out <= data_in;
        end if;
    end if;
end process;
```

### Combinational Logic Rules

✅ **Always include default assignments**
✅ **Cover all cases** (`when others`)
✅ **Keep combinational depth reasonable** (<10 levels)
✅ **Avoid long combinational chains**

---

## Verilog Compatibility

### Key Differences to Avoid

| VHDL Feature | Verilog Compatible? | Alternative |
|--------------|---------------------|-------------|
| Enums | ❌ NO | `std_logic_vector` constants |
| Records | ❌ NO | Separate signals or arrays |
| Subtypes | ⚠️ Limited | Use base type |
| Physical types | ❌ NO | Comments for units |
| File I/O | ❌ NO | Testbench only |

### Verilog-Friendly VHDL

```vhdl
-- ❌ VHDL-only features
type state_t is (IDLE, ARMED, FIRING);  -- Enum
type my_record_t is record              -- Record
    data : std_logic_vector(7 downto 0);
    valid : std_logic;
end record;

-- ✅ Verilog-compatible
constant STATE_IDLE   : std_logic_vector(1 downto 0) := "00";
constant STATE_ARMED  : std_logic_vector(1 downto 0) := "01";
constant STATE_FIRING : std_logic_vector(1 downto 0) := "10";

-- Separate signals instead of record
signal data  : std_logic_vector(7 downto 0);
signal valid : std_logic;
```

---

## Safety & Constraints

### Define Safety Limits in Package

```vhdl
package safety_pkg is
    -- Voltage limits (16-bit signed, ±5V scale)
    constant MAX_VOLTAGE_3V0 : signed(15 downto 0) := x"4CCD";  -- 3.0V
    constant MIN_VOLTAGE     : signed(15 downto 0) := x"8000";  -- -5.0V

    -- Timing limits
    constant MAX_PULSE_WIDTH : natural := 32;   -- cycles
    constant MIN_COOLDOWN    : natural := 8;    -- cycles

    -- Counter limits
    constant MAX_RETRY_COUNT : natural := 15;   -- 4-bit

    -- Helper function
    function clamp_voltage(
        voltage : signed(15 downto 0);
        max_val : signed(15 downto 0)
    ) return signed;
end package;
```

### Use Clamping Functions

```vhdl
use work.safety_pkg.all;

-- Clamp intensity to safe maximum
intensity_safe <= clamp_voltage(intensity_raw, MAX_VOLTAGE_3V0);

-- Limit counter range
if counter < MAX_RETRY_COUNT then
    counter <= counter + 1;
else
    counter <= MAX_RETRY_COUNT;  -- Saturate
end if;
```

---

## Common Anti-Patterns

### ❌ Don't: Multiple Drivers

```vhdl
-- BAD: Two processes drive same signal
process(clk)
begin
    if rising_edge(clk) then
        data_out <= data_a;
    end if;
end process;

process(clk)
begin
    if rising_edge(clk) then
        data_out <= data_b;  -- ❌ Multiple drivers!
    end if;
end process;
```

### ❌ Don't: Incomplete Sensitivity List

```vhdl
-- BAD: Missing signals in sensitivity list
process(sel)  -- ❌ Missing data_a, data_b!
begin
    if sel = '1' then
        output <= data_a;
    else
        output <= data_b;
    end if;
end process;

-- GOOD: Complete sensitivity or use clocked process
process(sel, data_a, data_b)  -- ✅ All inputs
begin
    if sel = '1' then
        output <= data_a;
    else
        output <= data_b;
    end if;
end process;
```

### ❌ Don't: Blocking in Sequential Logic

```vhdl
-- BAD: Combinational assignment in clocked process
process(clk)
begin
    if rising_edge(clk) then
        temp := data_in;      -- Variable (combinational)
        data_out <= temp + 1; -- Signal (registered)
    end if;
end process;

-- GOOD: Separate or use signals throughout
process(clk)
begin
    if rising_edge(clk) then
        data_out <= data_in + 1;  -- Direct registered assignment
    end if;
end process;
```

---

## Code Examples

See `examples/` directory for complete working examples:

### Packages
- `forge_common_pkg.vhd` - Control scheme, BRAM interface
- `ds1120_pd_pkg.vhd` - Safety constants, helper functions (example)
- `forge_voltage_pkg.vhd` - Voltage conversion utilities

### Modules
- `forge_util_clk_divider.vhd` - Clock divider with enable control
- `fsm_observer.vhd` - FSM debugging module

---

## Quick Reference Card

### Port Declaration Order
```vhdl
entity my_module is
    generic (
        PARAM : natural := 16  -- Generics first
    );
    port (
        -- 1. Clock & Reset
        clk    : in std_logic;
        rst_n  : in std_logic;

        -- 2. Control
        clk_en : in std_logic;
        enable : in std_logic;

        -- 3. Data inputs
        data_in : in std_logic_vector(15 downto 0);

        -- 4. Data outputs
        data_out : out std_logic_vector(15 downto 0);

        -- 5. Status
        busy  : out std_logic;
        fault : out std_logic
    );
end entity;
```

### Clocked Process Template
```vhdl
process(clk, rst_n)
begin
    if rst_n = '0' then
        -- Asynchronous reset
        output <= (others => '0');
    elsif rising_edge(clk) then
        if clk_en = '1' then
            if enable = '1' then
                -- Functional logic
                output <= input;
            end if;
        end if;
    end if;
end process;
```

---

## Checklist for New VHDL Modules

Before committing:

- [ ] FSM states use `std_logic_vector` (not enums)
- [ ] All case statements have `when others`
- [ ] All signals have default/reset values
- [ ] Port order: clk, rst_n, clk_en, enable, then data
- [ ] Active-low reset (`rst_n`)
- [ ] No latches inferred (check synthesis report)
- [ ] Signal names follow conventions
- [ ] Safety limits defined in package
- [ ] Helper functions in package body
- [ ] Code synthesizes without warnings
- [ ] Testbench exists and passes

---

**Exported from:** EZ-EMFI Project
**Date:** 2025-11-04
**Version:** 1.0

**See also:**
- HUMAN_NEW_MODULE_GUIDE.md - Step-by-step module creation
- CLAUDE_FULL_BACKUP.md - Complete EZ-EMFI VHDL reference
- vhdl.md - VHDL development context and quick reference
