# AutoPSY CAN Bus Testbed

Real vehicle security testbed using Raspberry Pi 5 + ESP32.

## Hardware Required
- Raspberry Pi 5 (any RAM)
- MCP2515 CAN Bus Module (with TJA1050 transceiver)
- ESP32 DevKit (any variant)
- CAN transceiver for ESP32 (SN65HVD230 or TJA1050) — OR a second MCP2515
- Breadboard + jumper wires
- 2x 120Ω resistors (CAN termination)

## Quick Start

### 1. Wire everything
See [WIRING_GUIDE.md](WIRING_GUIDE.md)

### 2. Setup Pi 5
```bash
sudo bash setup_pi_can.sh
# Reboot when prompted
```

### 3. Flash ESP32
Open `esp32_ecu_simulator/esp32_ecu_simulator.ino` in Arduino IDE:
- Board: **ESP32 Dev Module**
- Upload Speed: 115200
- Flash

### 4. Test the bus
```bash
bash test_can_bus.sh
```

### 5. Run AutoPSY attacks
```bash
# Install AutoPSY
cd /path/to/AutoPSY && pip install -e .

# Sniff CAN traffic
candump can0

# Inject malicious frames
python -m autopsy attack can-inject --interface can0 --arb-id 0x0C0 --data FF00000000000000

# Replay attack
python -m autopsy attack can-replay --interface can0 --count 100

# Bus-off attack
python -m autopsy attack can-busoff --interface can0

# Full forensic acquisition
python -m autopsy forensics --interface can0 --duration 30

# Anti-forensic detection
python -m autopsy anti-forensics --interface can0

# Full demo
python -m autopsy demo --interface can0
```

## What the ESP32 Simulates

10 ECU signals at realistic rates:

| CAN ID | Signal | Rate | Description |
|--------|--------|------|-------------|
| 0x0C0 | Engine RPM | 100 Hz | 800-6000 RPM with driving phases |
| 0x0D0 | Vehicle Speed | 100 Hz | 0-180 km/h correlated with RPM |
| 0x0E0 | Steering Angle | 20 Hz | -540° to +540° sinusoidal |
| 0x050 | Airbag | 10 Hz | Safety system heartbeat |
| 0x108 | Coolant Temp | 10 Hz | 60-90°C gradual rise |
| 0x140 | Throttle | 10 Hz | 0-100% position |
| 0x1A0 | Brake | 20 Hz | Pedal + pressure |
| 0x1B0 | ABS | 20 Hz | Anti-lock status |
| 0x1C0 | Transmission | 20 Hz | Gear 1-6 with shifts |
| 0x300 | Door Status | 10 Hz | Open/close events |

The simulator cycles through driving phases: Idle → Accelerate → Cruise → Brake → Turn, with realistic gear shifts and speed/RPM correlation.
