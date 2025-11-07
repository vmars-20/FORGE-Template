# Troubleshooting Guide

**Quick reference for common issues and solutions**

---

## Table of Contents

1. [YAML Validation Errors](#yaml-validation-errors)
2. [Code Generation Issues](#code-generation-issues)
3. [VHDL Compilation Errors](#vhdl-compilation-errors)
4. [Python Control Issues](#python-control-issues)
5. [Hardware Testing Issues](#hardware-testing-issues)
6. [Performance Issues](#performance-issues)
7. [Debug Techniques](#debug-techniques)
8. [Getting Help](#getting-help)
9. [FAQ](#faq)

---

## YAML Validation Errors

### Error: "YAML syntax error"

**Symptom:**
```
❌ YAML syntax error at line 12: mapping values are not allowed here
```

**Causes:**
- Missing colon after key
- Incorrect indentation (use spaces, not tabs)
- Missing quotes around special characters

**Solution:**
```yaml
# ❌ Wrong (missing colon)
datatypes
  - name: voltage

# ✅ Correct
datatypes:
  - name: voltage
```

**Validate indentation:**
```yaml
# ❌ Wrong (inconsistent indentation)
datatypes:
  - name: voltage
   datatype: voltage_output_05v_s16  # 3 spaces (should be 4)

# ✅ Correct (2-space indentation)
datatypes:
  - name: voltage
    datatype: voltage_output_05v_s16
```

---

### Error: "Unknown datatype"

**Symptom:**
```
❌ Unknown datatype 'voltage_5v_s16' in signal 'output_voltage'
```

**Causes:**
- Typo in datatype name
- Type doesn't exist in BasicAppDataTypes
- Case mismatch (types are case-sensitive)

**Solution:**
```yaml
# ❌ Wrong (typo)
datatype: voltage_5v_s16

# ✅ Correct
datatype: voltage_output_05v_s16
```

**Check available types:**
```bash
uv run python -c "from forge.types.registry import TYPE_REGISTRY; print([t for t in TYPE_REGISTRY.get_all_types()])"
```

**See:** [Type System Reference](../reference/type_system.md) or [`libs/basic-app-datatypes/llms.txt`](../../libs/basic-app-datatypes/llms.txt)

---

### Error: "Default value out of range"

**Symptom:**
```
❌ Default value 100 out of range for type 'time_cycles_u8' (max: 255)
❌ Default value -10 invalid for unsigned type 'time_milliseconds_u16'
```

**Causes:**
- default_value exceeds type's maximum
- Negative value for unsigned type
- Wrong physical units (using raw counts for scaled types)

**Solution:**

```yaml
# ❌ Wrong (exceeds u8 max of 255)
- name: cycle_count
  datatype: time_cycles_u8
  default_value: 300  # > 255

# ✅ Correct
- name: cycle_count
  datatype: time_cycles_u8
  default_value: 100  # ≤ 255

# ✅ Or use larger type
- name: cycle_count
  datatype: time_cycles_u16  # max 65535
  default_value: 300
```

**Check type ranges:**
- `u8`: 0-255
- `u16`: 0-65535
- `u32`: 0-4294967295
- `s16`: -32768 to 32767
- `s32`: -2147483648 to 2147483647

---

### Error: "Required field missing"

**Symptom:**
```
❌ Field 'description' is required for signal 'output_voltage'
```

**Causes:**
- Forgot required field
- Typo in field name (e.g., `descr` instead of `description`)

**Solution:**

```yaml
# ❌ Wrong (missing description)
- name: output_voltage
  datatype: voltage_output_05v_s16
  default_value: 0

# ✅ Correct (all required fields)
- name: output_voltage
  datatype: voltage_output_05v_s16
  description: Output voltage setpoint  # Added
  default_value: 0
```

**Required fields:**
- Top-level: `app_name`, `version`, `description`, `platform`, `datatypes`
- Per signal: `name`, `datatype`, `description`, `default_value`

---

### Error: "Invalid platform"

**Symptom:**
```
❌ Platform 'moku' is not valid. Must be one of: moku_go, moku_lab, moku_pro, moku_delta
```

**Causes:**
- Typo in platform name
- Using old platform names

**Solution:**

```yaml
# ❌ Wrong
platform: moku  # Generic, not specific

# ✅ Correct (choose one)
platform: moku_go     # 125 MHz
platform: moku_lab    # 125 MHz
platform: moku_pro    # 1 GHz
platform: moku_delta  # 5 GHz
```

---

## Code Generation Issues

### Error: "Register overflow"

**Symptom:**
```
❌ Register mapping failed: Cannot pack 15 signals into 10 registers (320 bits max)
Total bits required: 400 bits (exceeds 320-bit limit)
```

**Causes:**
- Too many signals for available registers (CR6-CR15 = 10 registers × 32 bits)
- Inefficient packing strategy
- Unnecessarily wide types

**Solution:**

**1. Reduce signal count:**
```yaml
# Remove non-critical signals or combine related flags into bitfields
```

**2. Use narrower types:**
```yaml
# ❌ Wasteful (32 bits for 0-100 range)
- name: progress
  datatype: time_cycles_u32
  default_value: 0

# ✅ Efficient (8 bits for 0-100 range)
- name: progress
  datatype: time_cycles_u8
  default_value: 0
```

**3. Try different packing strategy:**
```yaml
mapping_strategy: best_fit  # Instead of default type_clustering
```

**Check efficiency:**
```bash
uv run python -m forge.generate_package specs/my_instrument.yaml
# Look for efficiency metrics in manifest.json
```

---

### Error: "Template rendering failed"

**Symptom:**
```
❌ Jinja2 template error: 'NoneType' object has no attribute 'bit_width'
```

**Causes:**
- Internal bug in template
- Type missing metadata in TYPE_REGISTRY
- Custom type not registered

**Solution:**

**Check type registration:**
```python
from forge.types.registry import TYPE_REGISTRY
type_obj = TYPE_REGISTRY.get_type('your_type_name')
print(type_obj.bit_width)  # Should print integer, not None
```

**If using custom types:** Ensure they're registered before generation:
```python
TYPE_REGISTRY.register_type(MyCustomType)
```

**Report bug:** If using standard types, file GitHub issue with YAML spec.

---

### Error: "Package validation failed"

**Symptom:**
```
❌ Pydantic validation error: field required (type=value_error.missing)
```

**Causes:**
- YAML passed syntax check but failed Pydantic model validation
- Type mismatch (string where number expected)
- Missing nested field

**Solution:**

**Check field types:**
```yaml
# ❌ Wrong (version should be string)
version: 1.0  # Interpreted as float

# ✅ Correct (quote numbers for string fields)
version: "1.0.0"
```

**Check nested structures:**
```yaml
# ❌ Wrong (datatypes should be array)
datatypes:
  name: voltage

# ✅ Correct
datatypes:
  - name: voltage  # Array item (note the dash)
```

---

## VHDL Compilation Errors

**Note:** VHDL compilation happens in CloudCompile (external to forge). These are common issues when uploading generated VHDL.

### Error: "Entity not found"

**Symptom:**
```
CloudCompile Error: Entity 'my_instrument_main' not found
```

**Causes:**
- Uploaded shim but not main (or vice versa)
- Filename doesn't match entity name

**Solution:**

**Upload both files:**
- `my_instrument_shim.vhd`
- `my_instrument_main.vhd`

**Verify entity names match:**
```vhdl
-- In my_instrument_shim.vhd
entity my_instrument_shim is  -- Must match filename
```

---

### Error: "Type mismatch in port map"

**Symptom:**
```
CloudCompile Error: Type mismatch: expected std_logic_vector, got signed
```

**Causes:**
- Modified generated shim (don't do this!)
- Type mismatch in main entity port

**Solution:**

**Regenerate shim (never edit manually):**
```bash
uv run python -m forge.generate_package specs/my_instrument.yaml
```

**Match types in main entity:**
```vhdl
-- In my_instrument_main.vhd, match types from shim:
entity my_instrument_main is
  port (
    output_voltage : in signed(15 downto 0);  -- Must match shim output type
    ...
  );
end entity;
```

---

### Error: "Clock domain crossing"

**Symptom:**
```
CloudCompile Warning: Asynchronous clock domain crossing detected
```

**Causes:**
- Using control register values directly in different clock domain
- No synchronization flip-flops

**Solution:**

**Add synchronizer in main entity:**
```vhdl
-- Synchronize control signals to your clock domain
signal voltage_sync : signed(15 downto 0);

process(your_clk)
begin
  if rising_edge(your_clk) then
    voltage_sync <= output_voltage;  -- Synchronize from control clock
  end if;
end process;
```

**See:** Moku platform docs for multi-clock designs.

---

## Python Control Issues

### Error: "Cannot connect to Moku"

**Symptom:**
```python
ConnectionError: Failed to connect to 192.168.1.100
```

**Causes:**
- Moku not on network
- Wrong IP address
- Firewall blocking connection

**Solution:**

**1. Verify IP address:**
```bash
# Use Moku desktop app or check device display
# Typical: 192.168.1.x
```

**2. Test ping:**
```bash
ping 192.168.1.100
```

**3. Check firewall:**
```bash
# Allow TCP connections to Moku (ports 22, 80, 27182)
```

---

### Error: "Instrument not deployed"

**Symptom:**
```python
RuntimeError: Custom instrument 'my_instrument' not found on device
```

**Causes:**
- Bitstream not deployed
- App name mismatch
- Deployment failed silently

**Solution:**

**Deploy bitstream first:**
```python
from moku.instruments import CustomInstrument
instr = CustomInstrument('192.168.1.100')
instr.deploy_bitstream('path/to/bitstream.bit', 'my_instrument')
```

**Verify app name matches manifest:**
```python
import json
with open('output/my_instrument/manifest.json') as f:
    manifest = json.load(f)
print(manifest['app_name'])  # Must match deployment name
```

---

### Error: "Register write has no effect"

**Symptom:**
```python
instr.set_control_register(6, 1000)
print(instr.get_control_register(6))  # Returns 0, not 1000
```

**Causes:**
- VHDL main entity not using signals from shim
- Bitstream not reloaded after VHDL changes
- Register packing error

**Solution:**

**1. Verify VHDL uses signals:**
```vhdl
-- In my_instrument_main.vhd
architecture rtl of my_instrument_main is
begin
  -- ❌ Wrong (signals not used)
  -- dac_output <= (others => '0');

  -- ✅ Correct (use signals from shim)
  dac_output <= output_voltage;
end architecture;
```

**2. Rebuild and redeploy:**
```bash
# Regenerate VHDL
uv run python -m forge.generate_package specs/my_instrument.yaml

# Upload to CloudCompile
# Download new bitstream
# Redeploy to Moku
```

**3. Check register mapping:**
```python
# Verify you're writing to correct register
import json
with open('output/my_instrument/control_registers.json') as f:
    regs = json.load(f)
print(regs)  # Check which signals are in which registers
```

---

## Hardware Testing Issues

### Issue: "FSM stuck in one state"

**Symptom:**
- FSM never transitions
- Signals don't respond to control register changes

**Debugging:**

**1. Use FSM observer pattern:**

See [FSM Observer Pattern](../debugging/fsm_observer_pattern.md) for voltage-encoded state debugging.

**2. Check trigger signals:**
```python
# Ensure trigger is being set
instr.set_parameter('fsm_trigger', 1)
time.sleep(0.1)
instr.set_parameter('fsm_trigger', 0)  # Pulse trigger
```

**3. Verify reset logic:**
```vhdl
-- In VHDL, ensure async reset works
process(clk, reset)
begin
  if reset = '1' then
    state <= IDLE;
  elsif rising_edge(clk) then
    -- State transitions
  end if;
end process;
```

---

### Issue: "Signals not visible on oscilloscope"

**Symptom:**
- Control registers write successfully
- VHDL simulation works
- Oscilloscope shows no output

**Debugging:**

**1. Check MCC routing:**

Verify MCC routes signals to physical outputs.

**See:** [MCC Routing Patterns](../../libs/moku-models/docs/routing_patterns.md)

**2. Check output enable:**
```python
# Ensure output drivers are enabled
instr.set_parameter('enable_output', 1)
```

**3. Check scaling:**
```python
# Voltage might be too small to see
instr.set_parameter('output_voltage', 5.0)  # Max output
```

**See:** [Hardware Validation Guide](../debugging/hardware_validation.md) for oscilloscope workflows.

---

### Issue: "Timing violations"

**Symptom:**
- CloudCompile reports timing errors
- Design doesn't meet timing at high clock rates

**Solutions:**

**1. Pipeline critical paths:**
```vhdl
-- Add register stages to break long combinational paths
signal voltage_stage1, voltage_stage2 : signed(15 downto 0);

process(clk)
begin
  if rising_edge(clk) then
    voltage_stage1 <= output_voltage;
    voltage_stage2 <= voltage_stage1 * gain;  -- Registered multiply
    dac_output <= voltage_stage2;
  end if;
end process;
```

**2. Use platform-appropriate types:**
- Moku Go/Lab (125 MHz): Relaxed timing
- Moku Pro (1 GHz): Pipeline critical paths
- Moku Delta (5 GHz): Aggressive pipelining required

**3. Simplify combinational logic:**
- Avoid deep multiplier chains
- Use lookup tables for complex functions

---

## Performance Issues

### Issue: "Low register efficiency"

**Symptom:**
```json
"efficiency": {
  "percentage": 0.25,  // Only 25% efficient
  "registers_saved": 0
}
```

**Causes:**
- Using one register per signal (default without mapping)
- Mixed signal widths prevent packing
- Inefficient packing strategy

**Solutions:**

**1. Use type_clustering:**
```yaml
mapping_strategy: type_clustering  # Default, but verify
```

**2. Group similar widths:**
```yaml
# Put all 16-bit signals together in YAML
- name: voltage_1
  datatype: voltage_output_05v_s16  # 16 bits
- name: voltage_2
  datatype: voltage_output_05v_s16  # 16 bits
- name: voltage_3
  datatype: voltage_output_05v_s16  # 16 bits

# Put all booleans together
- name: enable_1
  datatype: boolean_1  # 1 bit
- name: enable_2
  datatype: boolean_1  # 1 bit
```

**3. Avoid odd widths:**
```yaml
# ❌ Harder to pack (24 bits doesn't fit evenly)
datatype: custom_24bit

# ✅ Easier to pack (16 bits, power of 2)
datatype: voltage_output_05v_s16
```

**Target:** >50% efficiency for most designs.

---

### Issue: "Generation takes too long"

**Symptom:**
- `generate_package` takes >10 seconds
- Validation is slow

**Causes:**
- Very large YAML (hundreds of signals)
- Inefficient packing algorithm (best_fit with many signals)

**Solutions:**

**1. Use faster packing:**
```yaml
mapping_strategy: type_clustering  # Fastest (O(n log n))
# vs
mapping_strategy: best_fit         # Slower (O(n²))
```

**2. Simplify spec:**
- Combine related signals
- Remove unused signals

**3. Upgrade hardware:**
- Use faster CPU for template rendering

---

## Debug Techniques

### Enable Verbose Logging

```bash
# Show detailed validation output
uv run python -m forge.validate_yaml specs/my_instrument.yaml --verbose

# Show register mapping details
uv run python -m forge.generate_package specs/my_instrument.yaml --verbose
```

### Inspect Intermediate Outputs

```bash
# Check Pydantic model
uv run python -c "
from forge.models.package import BasicAppsRegPackage
pkg = BasicAppsRegPackage.from_yaml('specs/my_instrument.yaml')
print(pkg.model_dump_json(indent=2))
"

# Check register mapping
cat output/my_instrument/control_registers.json | python -m json.tool
```

### Use Python REPL

```python
# Interactive debugging
from forge.models.package import BasicAppsRegPackage
from forge.mapper import BADRegisterMapper

pkg = BasicAppsRegPackage.from_yaml('specs/my_instrument.yaml')
mapper = BADRegisterMapper()
result = mapper.map_to_registers(pkg.datatypes, strategy='type_clustering')

print(result.registers)
print(result.efficiency)
```

### FSM Debugging

**See:** [FSM Observer Pattern](../debugging/fsm_observer_pattern.md)

### Hardware Validation

**See:** [Hardware Validation Guide](../debugging/hardware_validation.md)

### Common Issues Cookbook

**See:** [Common Issues](../debugging/common_issues.md)

---

## Getting Help

### Before Filing an Issue

**Check:**
1. This troubleshooting guide
2. [Getting Started](getting_started.md) tutorial
3. [User Guide](user_guide.md) reference
4. [Examples](../examples/) - Does your issue occur with examples?

**Gather information:**
```bash
# Version info
uv run python -c "import forge; print(forge.__version__)"

# YAML spec (sanitize if sensitive)
cat specs/my_instrument.yaml

# Error output
uv run python -m forge.generate_package specs/my_instrument.yaml 2>&1 | tee error.log
```

### File a GitHub Issue

**Include:**
- Minimal YAML spec that reproduces issue
- Full error message
- forge version (`forge.__version__`)
- Python version (`python --version`)
- Platform (macOS, Linux, Windows)

**Template:**
```markdown
**Bug Description:**
Brief description of issue

**YAML Spec:**
```yaml
app_name: minimal_repro
...
```

**Error Output:**
```
❌ Error message here
```

**Environment:**
- forge version: X.Y.Z
- Python version: 3.10.5
- Platform: macOS 14.0
```

**GitHub Issues:** [moku-instrument-forge/issues](https://github.com/liquidinstruments/moku-instrument-forge/issues)

---

## FAQ

### Q: Can I edit generated VHDL files?

**A:** Only edit `*_main.vhd` (your instrument logic). **Never edit `*_shim.vhd`** - it's regenerated from YAML and your changes will be lost.

---

### Q: Why does my default_value cause validation error?

**A:** Ensure default_value matches the type's range and signedness:
- Unsigned types (u8, u16, u32): no negative values
- Signed types (s16, s32): check ±range
- Scaled types (voltage_output_05v_s16): use physical units (volts), not raw counts

---

### Q: How do I add a new type?

**A:** Types are defined in `libs/basic-app-datatypes/`. See [Type System Reference](../reference/type_system.md) for guidance on extending the type system.

---

### Q: Can I use more than 10 control registers?

**A:** No. Moku platforms reserve CR0-CR5 for system use, CR6-CR15 for custom instruments (10 registers, 320 bits total). Design your instrument to fit within this limit.

---

### Q: Why is my register efficiency low?

**A:** See [Performance Issues](#issue-low-register-efficiency) above. Use `type_clustering`, group similar widths, avoid odd bit widths.

---

### Q: Does forge support custom VHDL templates?

**A:** Advanced users can modify templates in `forge/templates/`. See [VHDL Generation](../reference/vhdl_generation.md) for details.

---

### Q: Can I deploy to multiple platforms with one YAML?

**A:** No. Each YAML targets one platform (`moku_go`, `moku_lab`, etc.). Create separate specs for different platforms if needed.

---

### Q: What if CloudCompile synthesis fails?

**A:** Check generated VHDL for errors. Verify `*_main.vhd` has correct entity definition matching `*_shim.vhd`. See [VHDL Compilation Errors](#vhdl-compilation-errors).

---

**Still stuck?** Ask on GitHub Discussions or file an issue with full context.
