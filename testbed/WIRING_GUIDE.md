# AutoPSY CAN Bus Testbed — Wiring Guide

## Components
- Raspberry Pi 5
- MCP2515 CAN Bus Module (with TJA1050 transceiver)
- ESP32 (any devkit — WROOM, S3, etc.)
- Breadboard
- Jumper wires
- 2x 120Ω resistors (CAN bus termination)

## Step 1: Wire MCP2515 to Raspberry Pi 5

The MCP2515 connects via SPI:

```
MCP2515 Module    →    Raspberry Pi 5
─────────────────────────────────────
VCC               →    3.3V (Pin 1)
GND               →    GND  (Pin 6)
CS                →    SPI0 CE0 / GPIO8 (Pin 24)
MOSI (SI)         →    SPI0 MOSI / GPIO10 (Pin 19)
MISO (SO)         →    SPI0 MISO / GPIO9 (Pin 21)
SCK               →    SPI0 SCLK / GPIO11 (Pin 23)
INT               →    GPIO25 (Pin 22)
```

**Pin layout on Pi 5 (looking at GPIO header, USB ports on right):**
```
3V3  [1]  [2]  5V
     [3]  [4]  5V
     [5]  [6]  GND     ← GND here
     ...
MOSI [19] [20] GND
MISO [21] [22] GPIO25  ← INT here
SCLK [23] [24] CE0     ← CS here
```

## Step 2: Wire ESP32 CAN (via MCP2515 or built-in TWAI)

### Option A: ESP32 with built-in TWAI (no extra module needed)
ESP32 has a built-in CAN controller (TWAI). You just need a **TJA1050 or SN65HVD230 CAN transceiver** module:

```
ESP32             →    CAN Transceiver (TJA1050/SN65HVD230)
──────────────────────────────────────────────────────────
GPIO 5            →    TX (CTX)
GPIO 4            →    RX (CRX)  
3.3V              →    VCC (use 3.3V transceiver like SN65HVD230)
GND               →    GND
```

### Option B: ESP32 with second MCP2515 module
If you have a second MCP2515:

```
ESP32             →    MCP2515 Module
──────────────────────────────────────
3.3V              →    VCC
GND               →    GND
GPIO 5 (VSPI CS)  →    CS
GPIO 23 (VSPI MOSI) → MOSI (SI)
GPIO 19 (VSPI MISO) → MISO (SO)
GPIO 18 (VSPI CLK)  → SCK
GPIO 4            →    INT
```

### Option C: ESP32 TWAI direct to MCP2515 transceiver (simplest)
If your MCP2515 module has the TJA1050 transceiver on it, you can tap directly into the CAN bus:

```
ESP32 TWAI TX (GPIO 5)  → through any CAN transceiver → CAN_H / CAN_L
```

## Step 3: Connect CAN Bus Between Pi and ESP32

```
Pi MCP2515 Module          ESP32 CAN Transceiver
─────────────────          ─────────────────────
CAN_H ──────────────┬──────── CAN_H
                     │
                [120Ω resistor]
                     │
CAN_L ──────────────┴──────── CAN_L

GND ─────────────────────────── GND (common ground!)
```

**CRITICAL: 120Ω termination resistors**
- Put one 120Ω resistor between CAN_H and CAN_L at the Pi end
- Put one 120Ω resistor between CAN_H and CAN_L at the ESP32 end
- Many MCP2515 modules have a built-in 120Ω (check for a jumper labeled "J1" or "R_TERM")
- If your module already has termination, don't add external resistors

**CRITICAL: Common ground**
- Connect GND between Pi and ESP32 — CAN won't work without common ground

## Final Wiring Diagram

```
  ┌─────────────┐          CAN Bus           ┌─────────────┐
  │   Pi 5      │                             │   ESP32     │
  │             │    ┌──[120Ω]──┐             │             │
  │   MCP2515   │    │          │             │  TWAI/MCP   │
  │   CAN_H ────┼────┤  CAN_H  ├─────────────┼── CAN_H    │
  │   CAN_L ────┼────┤  CAN_L  ├─────────────┼── CAN_L    │
  │             │    │          │             │             │
  │   GND  ─────┼────┴──[120Ω]─┴─────────────┼── GND      │
  └─────────────┘                             └─────────────┘
       │                                            │
   AutoPSY                                   ECU Simulator
   (attacker)                              (fake car signals)
```

## Step 4: After Wiring — Software Setup

1. On Pi 5: run `setup_pi_can.sh` (configures SPI + can0 interface)
2. On ESP32: flash `ecu_simulator.ino` (sends realistic CAN frames)
3. Test: `candump can0` on Pi should show frames from ESP32
4. Attack: `python -m autopsy attack can-inject --interface can0`
