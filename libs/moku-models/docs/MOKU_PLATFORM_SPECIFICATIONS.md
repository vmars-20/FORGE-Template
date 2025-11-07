# Moku Platform Hardware Specifications

**Source**: Official Liquid Instruments datasheets (2024)
**Purpose**: Reference for `moku-models` platform model development

---

## Platform Comparison Table

| Feature | Moku:Go | Moku:Lab | Moku:Pro | Moku:Delta |
|---------|---------|----------|----------|------------|
| **Multi-Instrument Slots** | 2 | 2 | 4 | 3 (standard) or 8 (advanced) |
| **Analog Inputs** | 2 | 2 | 4 | 8 |
| **Analog Outputs** | 2 | 2 | 4 | 8 |
| **ADC Resolution** | 12-bit | 12-bit | 10-bit + 18-bit blended | 14-bit + 20-bit blended |
| **DAC Resolution** | 12-bit | 16-bit | 16-bit | 14-bit |
| **ADC Sample Rate** | 125 MSa/s | 500 MSa/s | 5 GSa/s (1ch) / 1.25 GSa/s (4ch) | 5 GSa/s (all 8 channels) |
| **DAC Sample Rate** | 125 MSa/s | 1 GSa/s | 1.25 GSa/s | 10 GSa/s (with interpolation) |
| **Input Bandwidth** | 30 MHz | 200 MHz | 300/600 MHz (selectable) | 2 GHz |
| **Output Bandwidth** | 20 MHz | 300 MHz | 500 MHz | 2 GHz |
| **Input Impedance** | 1 MΩ (AC/DC coupling) | 50 Ω or 1 MΩ (switchable) | 50 Ω or 1 MΩ (switchable) | 50 Ω or 1 MΩ (switchable) |
| **Output Impedance** | Low impedance | 50 Ω | 50 Ω | 50 Ω |
| **Input Voltage Range** | ±25 V (fixed) | 1 Vpp or 10 Vpp (switchable) | 400 mVpp, 4 Vpp, or 40 Vpp (switchable) | 100 mVpp, 1 Vpp, 10 Vpp, or 40 Vpp (switchable) |
| **Output Voltage Range** | ±5 V | 2 Vpp (into 50 Ω) | ±1 V up to 500 MHz, ±5 V up to 100 MHz | ±500 mV up to 2 GHz, ±5 V up to 100 MHz |
| **Digital I/O** | 16 pins @ 125 MSa/s | N/A (no DIO header) | N/A (no DIO header) | 32 pins (2×16) @ 5 GSa/s |
| **DIO Logic Level** | 3.3 V (5 V tolerant) | N/A | N/A | 3.3 V (5 V tolerant) |
| **FPGA** | Not specified | Xilinx Zynq 7020 | Xilinx Ultrascale+ | Xilinx RFSoC (3rd gen) |
| **Clock Stability** | Not specified | 500 ppb | 0.3 ppm | 1 ppb OCXO |
| **Data Storage** | N/A | SD card | 240 GB SSD | 1 TB SSD |
| **Form Factor** | Portable (1.7 lb) | Benchtop | Benchtop (rack mount) | Benchtop (2U rack) |
| **Connectivity** | USB-C, Wi-Fi, Ethernet (M2) | Wi-Fi, Ethernet, USB | Wi-Fi, Ethernet, USB-C | Ethernet, SFP, QSFP, USB-C |

---

## Detailed Specifications

### Moku:Go
**Target**: Education, portable prototyping
**Datasheet**: `Datasheet-MokuGo.pdf` (v24-0815)

#### Analog I/O
- **Inputs**: 2 channels, 12-bit, 125 MSa/s
  - Bandwidth: 30 MHz (-3 dB)
  - Coupling: AC or DC
  - Impedance: 1 MΩ (fixed)
  - Range: ±25 V (50 Vpp, fixed)

- **Outputs**: 2 channels, 12-bit, 125 MSa/s
  - Bandwidth: 20 MHz (-3 dB, low impedance)
  - Range: ±5 V (10 Vpp max)

#### Digital I/O
- 16 channels @ 125 MSa/s
- 3.3 V logic (5 V tolerant)

#### Multi-Instrument Mode
- **2 simultaneous instruments**

#### Available Instruments (14 total)
Arbitrary Waveform Generator, Data Logger, Digital Filter Box, Frequency Response Analyzer, FIR Filter Builder, Laser Lock Box, Lock-in Amplifier, Logic Analyzer, Oscilloscope/Voltmeter, Phasemeter, PID Controller, Time & Frequency Analyzer, Spectrum Analyzer, Waveform Generator

#### Notes
- Portable design with Wi-Fi hotspot
- Optional 4-channel programmable power supplies (M2 model)
- Available in 6 colors

---

### Moku:Lab
**Target**: Research applications, optical metrology
**Datasheet**: `Datasheet-MokuLab.pdf` (v24-0412)

#### Analog I/O
- **Inputs**: 2 channels, 12-bit, 500 MSa/s
  - Bandwidth: 200 MHz
  - Coupling: AC or DC (switchable)
  - Impedance: 50 Ω or 1 MΩ (switchable)
  - Range: 1 Vpp or 10 Vpp (switchable)

- **Outputs**: 2 channels, 16-bit, 1 GSa/s
  - Bandwidth: 300 MHz (anti-aliasing filters)
  - Range: 2 Vpp (into 50 Ω)

#### Digital I/O
- **None** (no DIO header on Moku:Lab)

#### Multi-Instrument Mode
- **2 simultaneous instruments**
- 12.5 Gb/s inter-slot signal path

#### Performance
- Noise: < 30 nV/√Hz above 100 kHz
- Clock stability: 500 ppb
- Latency: < 1 μs input to output

#### Available Instruments (14 total)
Same as Moku:Go (14 instruments)

#### Notes
- Powered by Xilinx Zynq 7020 FPGA
- SD card for data storage
- 10 MHz sync in/out

---

### Moku:Pro
**Target**: High-performance research, quantum computing
**Datasheet**: `Datasheet-MokuPro.pdf` (v24-1015)

#### Analog I/O
- **Inputs**: 4 channels, **blended ADC architecture**
  - Primary: 10-bit ADC @ 5 GSa/s (single channel) or 1.25 GSa/s (4 channels)
  - Secondary: 18-bit ADC @ 10 MSa/s
  - Bandwidth: 300/600 MHz (selectable)
  - Coupling: AC or DC (switchable)
  - Impedance: 50 Ω or 1 MΩ (switchable)
  - Range: 400 mVpp, 4 Vpp, or 40 Vpp (switchable)
  - Noise:
    - 30 nV/√Hz @ 100 Hz
    - 20 nV/√Hz @ 10 MHz @ 1.25 GSa/s
    - 13 nV/√Hz @ 10 MHz @ 5 GSa/s

- **Outputs**: 4 channels, 16-bit, 1.25 GSa/s
  - Range: ±1 V up to 500 MHz, ±5 V up to 100 MHz

#### Digital I/O
- **None** (no DIO header on Moku:Pro)

#### Multi-Instrument Mode
- **4 simultaneous instruments**
- 30 Gb/s inter-slot signal path

#### Performance
- Noise: 500 µV RMS at full bandwidth
- Clock stability: 0.3 ppm
- Latency: < 650 ns input to output
- Storage: 240 GB high-speed SSD

#### Available Instruments (15 total)
All 14 from Go/Lab, plus **Neural Network**

#### Notes
- Powered by Xilinx Ultrascale+ FPGA
- Blended ADC provides optimized SNR across all frequencies
- 10 MHz reference in/out
- Rack-mountable

---

### Moku:Delta
**Target**: Ultra-high-performance, precision measurements
**Datasheet**: `Datasheet-MokuDelta.pdf` (v25-0820)

#### Analog I/O
- **Inputs**: 8 channels, **blended ADC architecture**
  - Primary: 14-bit ADC @ 5 GSa/s (all 8 channels simultaneously)
  - Secondary: 20-bit ADC @ 40 MSa/s (frequency-dependent blending)
  - Bandwidth: 2 GHz
  - Coupling: AC or DC (switchable)
  - Impedance: 50 Ω or 1 MΩ (switchable)
  - Range: 100 mVpp, 1 Vpp, 10 Vpp, or 40 Vpp (switchable)
  - Noise: < 10 nV/√Hz @ 100 Hz

- **Outputs**: 8 channels, 14-bit, 10 GSa/s (with interpolation)
  - Bandwidth: 2 GHz
  - Range (into 50 Ω):
    - ±500 mV up to 2 GHz
    - ±5 V up to 100 MHz

#### Digital I/O
- **32 channels** (2 sets of 16 pins)
- High-speed digital I/O
- TTL logic compatible

#### Multi-Instrument Mode
- **8 simultaneous instruments** (advanced mode)
- **3 instruments** (standard mode with better sampling rates)
- 80 Gb/s inter-slot signal path

#### Performance
- Noise floor: < 10 nV/√Hz
- Clock stability: ±1 ppb OCXO
- Latency: 127 ns input to output
- Storage: 1 TB internal SSD

#### Available Instruments (15 total)
Same as Moku:Pro (15 instruments including Neural Network)

#### Connectivity
- 100 Gb/s QSFP
- Two 10 Gb/s SFP
- 1 Gb/s Ethernet
- USB-C
- GPS timing reference module
- Optional WiFi via external adapter

#### Notes
- Powered by Xilinx UltraScale+ RFSoC FPGA (3rd generation)
- Partial reconfiguration support
- 2U rack-mount form factor
- 10 MHz, 100 MHz, and GPS clock references
- **This is the flagship Moku platform**

---

## Key Observations for Platform Models

### Voltage Range Handling
**Recommendation**: All platforms except Moku:Go support **switchable voltage ranges**.

- **Moku:Go**: Fixed ranges (±25 V input, ±5 V output)
- **Moku:Lab**: 2 input ranges (1 Vpp, 10 Vpp)
- **Moku:Pro**: 3 input ranges (400 mVpp, 4 Vpp, 40 Vpp)
- **Moku:Delta**: 4 input ranges (100 mVpp, 1 Vpp, 10 Vpp, 40 Vpp)

**Implementation Strategy**:
- For first pass, use **maximum range** as default
- Future enhancement: Add `voltage_ranges: list[float]` field to `AnalogPort`

### Impedance Handling
**Recommendation**: All platforms except Moku:Go support **switchable impedance**.

- **Moku:Go**: Fixed 1 MΩ input
- **Moku:Lab/Pro/Delta**: Switchable 50 Ω or 1 MΩ input

**Implementation Strategy**:
- For first pass, default to **1 MΩ for inputs, 50 Ω for outputs**
- Future enhancement: Add `impedance_options: list[str]` field

### Digital I/O Differences
- **Moku:Go**: Single 16-pin header @ 125 MSa/s
- **Moku:Lab/Pro**: **No DIO headers**
- **Moku:Delta**: **2 separate 16-pin headers** @ 5 GSa/s

**Implementation Strategy**:
- Use `Optional[DIOPort]` or `list[DIOPort]` to handle platforms without DIO
- Delta needs 2 DIO ports

### ADC/DAC Blending (Advanced Feature)
- **Moku:Pro**: Blends 10-bit + 18-bit ADCs
- **Moku:Delta**: Blends 14-bit + 20-bit ADCs

**Implementation Strategy**:
- For first pass, **ignore blending** and use primary ADC specs
- Note in docstrings that blended modes exist
- Future enhancement: Add optional blended ADC fields

### Multi-Instrument Slot Counts
- **Moku:Go**: 2 slots
- **Moku:Lab**: 2 slots
- **Moku:Pro**: 4 slots
- **Moku:Delta**: **3 slots (standard mode)** or 8 slots (advanced mode)

**Implementation Strategy**:
- For Delta, use **3 slots** as default (better sampling rates)
- Note in docstring that 8-slot mode exists

---

## Answers to Outstanding Questions

### 1. Voltage Ranges
**Answer**: Use **maximum range** for first pass:
- Go: 50 Vpp (±25 V) input, 10 Vpp (±5 V) output
- Lab: 10 Vpp input, 2 Vpp output
- Pro: 40 Vpp input, 10 Vpp output (±5 V up to 100 MHz)
- Delta: 40 Vpp input, 10 Vpp output (±5 V up to 100 MHz)

### 2. Impedance
**Answer**: Default values:
- **Inputs**: 1 MΩ (all platforms)
- **Outputs**: 50 Ω (all platforms except Go which is "low impedance")

Note: Lab/Pro/Delta support switchable 50 Ω/1 MΩ input, but we'll default to 1 MΩ.

### 3. Delta DIO
**Answer**: Use **2 separate `DIOPort` instances** in a list:
```python
dio_headers: list[DIOPort] = Field(
    default_factory=lambda: [
        DIOPort(num_pins=16, sample_rate_msa=5000),
        DIOPort(num_pins=16, sample_rate_msa=5000)
    ]
)
```

### 4. Delta DAC Rate
**Answer**: Use **5000 MSa/s** (native FPGA clock), ignore 10 GSa/s interpolation for now.

---

## Consistency Matrix

| Platform | Slots | IN | OUT | ADC Bits | DAC Bits | ADC MSa/s | DAC MSa/s | Clock MHz | DIO Pins |
|----------|-------|-----|-----|----------|----------|-----------|-----------|-----------|----------|
| Go       | 2     | 2   | 2   | 12       | 12       | 125       | 125       | 125       | 16       |
| Lab      | 2     | 2   | 2   | 12       | 16       | 500       | 1000      | 500       | 0        |
| Pro      | 4     | 4   | 4   | 10*      | 16       | 1250†     | 1250      | 1250      | 0        |
| Delta    | 3     | 8   | 8   | 14*      | 14       | 5000      | 5000‡     | 5000      | 32       |

\* Blended ADC (ignore secondary for first pass)
† 5000 MSa/s single channel mode available
‡ 10000 MSa/s with interpolation available (ignore for first pass)

---

**Last Updated**: 2025-01-28
**Datasheets**: Moku:Go v24-0815, Moku:Lab v24-0412, Moku:Pro v24-1015, Moku:Delta v25-0820
**Maintainer**: Sealab Team
