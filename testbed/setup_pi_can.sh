#!/bin/bash
# AutoPSY — Raspberry Pi 5 CAN Bus Setup Script
# Run this on the Pi 5 after connecting the MCP2515 module
#
# Usage: sudo bash setup_pi_can.sh

set -e

echo "=========================================="
echo "  AutoPSY — Pi 5 CAN Bus Setup"
echo "=========================================="

# Step 1: Enable SPI
echo "[1/6] Enabling SPI..."
if ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt 2>/dev/null; then
    echo "dtparam=spi=on" >> /boot/firmware/config.txt
    echo "  Added dtparam=spi=on"
else
    echo "  SPI already enabled"
fi

# Step 2: Add MCP2515 overlay
echo "[2/6] Adding MCP2515 device tree overlay..."
# For Pi 5: use the mcp2515-can0 overlay
# oscillator=16000000 for 16MHz crystal (most common on MCP2515 modules)
# interrupt=25 for GPIO25
OVERLAY_LINE="dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25"
if ! grep -q "mcp2515-can0" /boot/firmware/config.txt 2>/dev/null; then
    echo "$OVERLAY_LINE" >> /boot/firmware/config.txt
    echo "  Added MCP2515 overlay (16MHz crystal, INT on GPIO25)"
else
    echo "  MCP2515 overlay already configured"
fi

# Check if module has 8MHz crystal (some cheap modules do)
echo "  NOTE: If CAN doesn't work, your module might have an 8MHz crystal."
echo "  Change oscillator=16000000 to oscillator=8000000 in /boot/firmware/config.txt"

# Step 3: Install can-utils
echo "[3/6] Installing CAN utilities..."
apt-get update -qq
apt-get install -y -qq can-utils python3-pip

# Step 4: Install Python CAN library
echo "[4/6] Installing python-can..."
pip3 install python-can --break-system-packages 2>/dev/null || pip3 install python-can

# Step 5: Create CAN interface startup script
echo "[5/6] Creating CAN interface startup script..."
cat > /usr/local/bin/can-up.sh << 'CANEOF'
#!/bin/bash
# Bring up CAN interface at 500kbps (standard automotive speed)
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0
echo "can0 is UP at 500kbps"
ip -details link show can0
CANEOF
chmod +x /usr/local/bin/can-up.sh

# Step 6: Create systemd service for auto-start
echo "[6/6] Creating systemd service..."
cat > /etc/systemd/system/can0.service << 'SVCEOF'
[Unit]
Description=CAN Bus Interface can0
After=network.target

[Service]
Type=oneshot
ExecStart=/sbin/ip link set can0 type can bitrate 500000
ExecStart=/sbin/ip link set up can0
ExecStop=/sbin/ip link set down can0
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SVCEOF
systemctl daemon-reload
systemctl enable can0.service

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "  REBOOT REQUIRED for SPI + MCP2515 overlay"
echo ""
echo "  After reboot:"
echo "    1. Run: sudo can-up.sh"
echo "       (or it auto-starts via systemd)"
echo "    2. Test: candump can0"
echo "       (should show CAN frames from ESP32)"
echo "    3. Send test frame: cansend can0 123#DEADBEEF"
echo ""
echo "  Reboot now? (y/n)"
read -r answer
if [ "$answer" = "y" ]; then
    reboot
fi
