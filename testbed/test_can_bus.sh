#!/bin/bash
# AutoPSY — CAN Bus Quick Test
# Run on Pi 5 after setup + ESP32 is sending frames
#
# Usage: bash test_can_bus.sh

echo "=========================================="
echo "  AutoPSY — CAN Bus Test"
echo "=========================================="

# Check can0 exists
echo ""
echo "[1] Checking can0 interface..."
if ip link show can0 > /dev/null 2>&1; then
    echo "  [OK] can0 exists"
    ip -details link show can0 | grep -E "can|state"
else
    echo "  [FAIL] can0 not found!"
    echo "  Run: sudo bash setup_pi_can.sh && reboot"
    exit 1
fi

# Check if can0 is up
STATE=$(ip link show can0 | grep -o "state [A-Z]*" | awk '{print $2}')
if [ "$STATE" != "UP" ]; then
    echo "  [*] Bringing up can0 at 500kbps..."
    sudo ip link set can0 type can bitrate 500000
    sudo ip link set up can0
fi

# Dump traffic for 5 seconds
echo ""
echo "[2] Listening for CAN frames (5 seconds)..."
echo "    If ESP32 is connected, you should see frames:"
echo ""
timeout 5 candump can0 2>&1 | head -30

echo ""
FRAME_COUNT=$(timeout 3 candump can0 2>&1 | wc -l)
echo "[3] Received $FRAME_COUNT frames in 3 seconds"

if [ "$FRAME_COUNT" -gt "0" ]; then
    echo "  [OK] CAN bus is working!"
    echo ""
    echo "[4] CAN traffic statistics:"
    timeout 3 canbusload can0 500000 2>&1 | tail -5
    echo ""
    echo "  Ready for AutoPSY attacks!"
    echo "  Run: python -m autopsy attack can-inject --interface can0"
else
    echo "  [WARN] No frames received."
    echo "  Check:"
    echo "    - ESP32 is powered and running ecu_simulator.ino"
    echo "    - CAN_H and CAN_L are connected correctly"
    echo "    - Common GND between Pi and ESP32"
    echo "    - 120 ohm termination resistors in place"
    echo ""
    echo "  Try sending a test frame:"
    echo "    cansend can0 123#DEADBEEF"
fi
