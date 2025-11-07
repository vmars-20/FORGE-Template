# MCC Routing Patterns

**Purpose:** Common signal routing patterns for Moku Multi-instrument Configuration Controller (MCC)

**API Reference:** See `moku_models.routing` for `MokuConnection` and `MokuConnectionList` classes

---

## Overview

MCC routing connects:
- **Physical I/O** (BNC connectors) ↔ **Slot virtual I/O** (CustomWrapper ports)
- **Slot outputs** ↔ **Slot inputs** (cross-slot signal processing)

**Key Principle:** Your VHDL module always sees the same `CustomWrapper` interface (InputA/B/C/D, OutputA/B/C/D) regardless of routing. MCC handles the external signal flow.

---

## Port Naming Convention

### Physical Ports
- **Inputs:** `IN1`, `IN2`, `IN3`, `IN4` (BNC input connectors)
- **Outputs:** `OUT1`, `OUT2`, `OUT3`, `OUT4` (BNC output connectors)

### Slot Virtual Ports
- **Inputs:** `Slot1InA`, `Slot1InB`, `Slot1InC`, `Slot1InD`
- **Outputs:** `Slot1OutA`, `Slot1OutB`, `Slot1OutC`, `Slot1OutD`

Replace `1` with slot number (1-4 depending on platform).

**Example Mapping:**
```
Physical IN1 → (MCC routing) → Slot2InA → CustomWrapper InputA (Slot 2)
CustomWrapper OutputA (Slot 2) → Slot2OutA → (MCC routing) → Physical OUT1
```

---

## Routing Rules

### ✅ Allowed Connections

1. **Physical Input → Slot Input(s)**
   - Example: `IN1` → `Slot1InA`
   - Fan-out allowed (one input to multiple slots)

2. **Slot Output → Physical Output(s)**
   - Example: `Slot1OutA` → `OUT1`
   - Fan-out allowed (one slot output to multiple physical outputs)

3. **Slot Output → Other Slot Input(s)**
   - Example: `Slot1OutA` → `Slot2InB`
   - Cross-slot signal processing
   - Fan-out allowed

### ❌ Forbidden Connections

1. **Slot Input → Anything**
   - Inputs are **destinations only**, not sources
   - CustomWrapper inputs are driven by MCC, not outputs

2. **Physical Output → Anything**
   - Physical outputs are **destinations only**

3. **Slot Output → Same Slot Input**
   - No internal loopback within a slot
   - Use VHDL internal signals for loopback

4. **Cyclic routing**
   - Example: `Slot1OutA` → `Slot2InA` → `Slot2OutA` → `Slot1InA` (cycle!)
   - Can cause undefined behavior

---

## Common Patterns

### Pattern 1: Simple Physical I/O

**Use case:** Basic signal processing with external input/output

```python
from moku_models import MokuConnection

connections = [
    MokuConnection(source='IN1', destination='Slot1InA'),
    MokuConnection(source='Slot1OutA', destination='OUT1'),
]
```

**Signal flow:** Physical IN1 → Your module → Physical OUT1

---

### Pattern 2: Monitor + Output

**Use case:** Custom instrument with oscilloscope monitoring

```python
connections = [
    MokuConnection(source='IN1', destination='Slot2InA'),      # External input
    MokuConnection(source='Slot2OutA', destination='OUT1'),    # Physical output
    MokuConnection(source='Slot2OutB', destination='Slot1InA'), # Monitor on Osc
]
```

**Setup:**
- Slot 1: Oscilloscope (for monitoring)
- Slot 2: Custom instrument (your VHDL)

**Signal flow:**
- Physical IN1 → Custom instrument InputA
- Custom instrument OutputA → Physical OUT1
- Custom instrument OutputB → Oscilloscope Ch1 (for debugging)

**Common usage:** Development and hardware validation

---

### Pattern 3: Cross-Slot Pipeline

**Use case:** Multi-stage signal processing

```python
connections = [
    MokuConnection(source='IN1', destination='Slot1InA'),
    MokuConnection(source='Slot1OutA', destination='Slot2InA'),  # Chain slots
    MokuConnection(source='Slot2OutA', destination='OUT1'),
]
```

**Setup:**
- Slot 1: First processing stage (e.g., filter)
- Slot 2: Second processing stage (e.g., amplifier)

**Signal flow:** Physical IN1 → Slot 1 → Slot 2 → Physical OUT1

---

### Pattern 4: Fan-Out (One Input → Multiple Slots)

**Use case:** Parallel processing of same input signal

```python
connections = [
    MokuConnection(source='IN1', destination='Slot1InA'),      # Slot 1 gets input
    MokuConnection(source='IN1', destination='Slot2InA'),      # Slot 2 gets same input
    MokuConnection(source='Slot1OutA', destination='OUT1'),    # Slot 1 output
    MokuConnection(source='Slot2OutA', destination='OUT2'),    # Slot 2 output
]
```

**Use case:** Process same signal in multiple ways simultaneously

---

### Pattern 5: Debug Mode (All Outputs Monitored)

**Use case:** Comprehensive hardware validation

```python
connections = [
    MokuConnection(source='IN1', destination='Slot2InA'),       # Input to custom module
    MokuConnection(source='Slot2OutA', destination='Slot1InA'), # OutA → Osc Ch1
    MokuConnection(source='Slot2OutB', destination='Slot1InB'), # OutB → Osc Ch2
    MokuConnection(source='Slot2OutC', destination='OUT1'),     # OutC → Physical OUT1
]
```

**Setup:**
- Slot 1: Oscilloscope (2-channel monitoring)
- Slot 2: Custom instrument under test

**Use case:** Simultaneously monitor multiple debug outputs and physical output

---

### Pattern 6: Feedback Loop (Careful!)

**Use case:** External feedback through physical connectors

**⚠️ WARNING:** Not a true "routing loop" - uses physical cable!

```python
connections = [
    MokuConnection(source='IN1', destination='Slot1InA'),
    MokuConnection(source='Slot1OutA', destination='OUT1'),
]
```

**Physical setup:** Use BNC cable to connect OUT1 → IN2 externally

**Use case:** Testing feedback algorithms (ensure stability!)

---

## Platform-Specific Considerations

### Moku:Go (2 slots, 2 I/O)
- Limited to `Slot1` and `Slot2`
- Only `IN1`, `IN2`, `OUT1`, `OUT2` available
- Common: Slot 1 = Oscilloscope, Slot 2 = CloudCompile

### Moku:Lab (2 slots, 2 I/O)
- Same as Moku:Go (2 slots, 2 I/O)
- Higher sample rate (500 MHz vs 125 MHz)

### Moku:Pro (4 slots, 4 I/O)
- All 4 slots available
- `IN1`-`IN4`, `OUT1`-`OUT4` available
- More complex cross-slot pipelines possible

### Moku:Delta (3 slots, 8 I/O)
- 3 slots in standard mode (8-slot advanced mode not covered here)
- `IN1`-`IN8`, `OUT1`-`OUT8` available
- Highest bandwidth (5 GHz clock)

**See:** `MOKU_PLATFORM_SPECIFICATIONS.md` for detailed platform specs

---

## Validation

Use `MokuConfig.validate_routing()` to catch routing errors before deployment:

```python
from moku_models import MokuConfig, SlotConfig, MokuConnection, MOKU_GO_PLATFORM

config = MokuConfig(
    platform=MOKU_GO_PLATFORM,
    slots={
        1: SlotConfig(instrument='Oscilloscope'),
        2: SlotConfig(instrument='CloudCompile', bitstream='probe.tar')
    },
    routing=[
        MokuConnection(source='IN1', destination='Slot2InA'),
        MokuConnection(source='Slot2OutA', destination='OUT1'),
        MokuConnection(source='Slot2OutB', destination='Slot1InA'),
    ]
)

# Validate (checks for invalid ports, routing cycles, etc.)
errors = config.validate_routing()
if errors:
    for error in errors:
        print(f"❌ {error}")
else:
    print("✅ Routing valid")
```

---

## Troubleshooting

### Error: "Source port 'Slot1InA' is not a valid source"

**Cause:** Trying to use a slot input as a source

**Fix:** Slot inputs are **destinations only**. Use `SlotXOutY` as sources.

---

### Error: "Destination port 'OUT1' is not a valid destination for platform"

**Cause:** Platform doesn't have that many outputs (e.g., Moku:Go only has OUT1-OUT2)

**Fix:** Check platform specs, use valid output numbers

---

### Warning: "Routing cycle detected"

**Cause:** Signal path forms a loop (Slot A → Slot B → Slot A)

**Fix:** Remove cyclic connection or use external feedback cable if intentional

---

### Issue: "Signal not appearing at output"

**Possible causes:**
1. Routing not configured (call `set_connections()` after `set_instrument()`)
2. CustomWrapper OutputA/B/C/D not driven in VHDL
3. Instrument not enabled (check control registers)

**Debug:** Use oscilloscope on intermediate slot outputs to trace signal path

---

## Best Practices

1. **Always reconfigure routing after `set_instrument()`**
   - `set_instrument()` clears routing
   - Call `set_connections()` immediately after

2. **Use descriptive variable names**
   ```python
   # Good
   external_input = MokuConnection(source='IN1', destination='Slot2InA')

   # Avoid
   conn1 = MokuConnection(source='IN1', destination='Slot2InA')
   ```

3. **Validate before deployment**
   - Use `MokuConfig.validate_routing()` to catch errors early
   - Avoids wasted deployment time

4. **Document complex routing**
   - Add comments explaining signal flow
   - Draw block diagrams for multi-slot setups

5. **Test with oscilloscope first**
   - Monitor custom module outputs before connecting to physical outputs
   - Verify signal integrity and timing

---

## References

- **API:** `moku_models.routing.MokuConnection`
- **Platform Specs:** `docs/MOKU_PLATFORM_SPECIFICATIONS.md`
- **Python API:** `moku.instruments.MultiInstrument.set_connections()`

---

**Last Updated:** 2025-11-03
**See Also:** Original patterns documented in EZ-EMFI Serena memories
