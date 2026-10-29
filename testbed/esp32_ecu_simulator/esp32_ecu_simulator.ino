/*
 * AutoPSY — ESP32 Vehicle ECU Simulator
 *
 * Simulates a real vehicle's CAN bus traffic using ESP32's built-in
 * TWAI (Two-Wire Automotive Interface) controller.
 *
 * Sends realistic CAN frames for:
 *   - Engine RPM (0x0C0) — ramps up/down like real driving
 *   - Vehicle Speed (0x0D0) — correlated with RPM
 *   - Brake Status (0x1A0) — periodic brake events
 *   - Steering Angle (0x0E0) — smooth sinusoidal steering
 *   - Coolant Temp (0x108) — slow temperature rise
 *   - Throttle Position (0x140) — correlated with RPM
 *   - Door Status (0x300) — periodic open/close
 *   - Airbag Status (0x050) — safety system heartbeat
 *   - ABS Status (0x1B0) — anti-lock brake system
 *   - Transmission (0x1C0) — gear shifts
 *
 * Hardware: ESP32 + CAN transceiver (TJA1050 or SN65HVD230)
 *   TX_PIN = GPIO 5
 *   RX_PIN = GPIO 4
 *
 * Upload with Arduino IDE:
 *   Board: ESP32 Dev Module
 *   Speed: 115200
 */

#include "driver/twai.h"

#define TX_PIN GPIO_NUM_5
#define RX_PIN GPIO_NUM_4

// CAN IDs (standard 11-bit, matching common vehicle protocols)
#define CAN_ID_ENGINE_RPM     0x0C0
#define CAN_ID_VEHICLE_SPEED  0x0D0
#define CAN_ID_STEERING       0x0E0
#define CAN_ID_AIRBAG         0x050
#define CAN_ID_COOLANT_TEMP   0x108
#define CAN_ID_THROTTLE       0x140
#define CAN_ID_BRAKE          0x1A0
#define CAN_ID_ABS            0x1B0
#define CAN_ID_TRANSMISSION   0x1C0
#define CAN_ID_DOOR_STATUS    0x300

// State variables — simulate realistic driving
float engine_rpm = 800.0;       // idle RPM
float vehicle_speed = 0.0;      // km/h
float steering_angle = 0.0;     // degrees, -540 to +540
float coolant_temp = 60.0;      // celsius, rises slowly
float throttle_pos = 0.0;       // 0-100%
uint8_t gear = 1;               // current gear
bool braking = false;
bool door_open = false;
uint32_t frame_counter = 0;
uint32_t drive_phase = 0;       // 0=idle, 1=accelerate, 2=cruise, 3=brake, 4=turn

unsigned long last_10ms = 0;    // fast signals (RPM, speed)
unsigned long last_50ms = 0;    // medium signals (steering, brake)
unsigned long last_100ms = 0;   // slow signals (temp, doors)
unsigned long last_phase = 0;   // drive phase changes

void setup() {
    Serial.begin(115200);
    Serial.println("\n=== AutoPSY ECU Simulator ===");
    Serial.println("Starting TWAI (CAN) interface...");

    // Configure TWAI
    twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT(TX_PIN, RX_PIN, TWAI_MODE_NORMAL);
    twai_timing_config_t t_config = TWAI_TIMING_CONFIG_500KBITS();  // 500kbps = standard automotive
    twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

    if (twai_driver_install(&g_config, &t_config, &f_config) == ESP_OK) {
        Serial.println("TWAI driver installed");
    } else {
        Serial.println("TWAI driver install FAILED");
        while (1);
    }

    if (twai_start() == ESP_OK) {
        Serial.println("TWAI started — CAN bus active at 500kbps");
    } else {
        Serial.println("TWAI start FAILED");
        while (1);
    }

    Serial.println("Sending vehicle CAN frames...\n");
}

void send_can(uint32_t id, uint8_t* data, uint8_t len) {
    twai_message_t msg;
    msg.identifier = id;
    msg.extd = 0;           // standard 11-bit ID
    msg.rtr = 0;
    msg.data_length_code = len;
    memcpy(msg.data, data, len);

    if (twai_transmit(&msg, pdMS_TO_TICKS(10)) == ESP_OK) {
        frame_counter++;
    }
}

void update_driving_simulation() {
    // Change driving phase every 5-10 seconds
    if (millis() - last_phase > (5000 + random(5000))) {
        last_phase = millis();
        drive_phase = (drive_phase + 1) % 5;

        switch (drive_phase) {
            case 0: Serial.println("[SIM] Phase: IDLE"); break;
            case 1: Serial.println("[SIM] Phase: ACCELERATE"); break;
            case 2: Serial.println("[SIM] Phase: CRUISE"); break;
            case 3: Serial.println("[SIM] Phase: BRAKE"); break;
            case 4: Serial.println("[SIM] Phase: TURN"); break;
        }
    }

    // Update vehicle state based on phase
    switch (drive_phase) {
        case 0: // Idle
            engine_rpm += (800 - engine_rpm) * 0.1;
            throttle_pos += (0 - throttle_pos) * 0.2;
            braking = false;
            break;

        case 1: // Accelerate
            throttle_pos += (70 + random(30) - throttle_pos) * 0.05;
            engine_rpm += (3000 + random(2000) - engine_rpm) * 0.02;
            braking = false;
            // Shift gears based on RPM
            if (engine_rpm > 4000 && gear < 6) {
                gear++;
                engine_rpm *= 0.6;
                Serial.printf("[SIM] Shift up to gear %d\n", gear);
            }
            break;

        case 2: // Cruise
            throttle_pos += (30 + random(10) - throttle_pos) * 0.1;
            engine_rpm += (2000 + random(500) - engine_rpm) * 0.05;
            braking = false;
            break;

        case 3: // Brake
            throttle_pos += (0 - throttle_pos) * 0.3;
            braking = true;
            engine_rpm += (1200 - engine_rpm) * 0.05;
            if (gear > 1 && engine_rpm < 1500) {
                gear--;
                engine_rpm *= 1.3;
                Serial.printf("[SIM] Shift down to gear %d\n", gear);
            }
            break;

        case 4: // Turn
            throttle_pos += (20 - throttle_pos) * 0.1;
            steering_angle = 180.0 * sin(millis() / 2000.0);
            braking = false;
            break;
    }

    // Speed follows RPM and gear
    float target_speed = (engine_rpm / 6000.0) * gear * 30.0;
    vehicle_speed += (target_speed - vehicle_speed) * 0.05;
    if (braking) vehicle_speed *= 0.95;
    if (vehicle_speed < 0) vehicle_speed = 0;

    // Coolant rises slowly
    if (coolant_temp < 90) coolant_temp += 0.01;

    // Reset steering when not turning
    if (drive_phase != 4) {
        steering_angle *= 0.95;
    }
}

void send_engine_rpm() {
    uint16_t rpm = (uint16_t)engine_rpm;
    uint8_t data[8] = {
        (uint8_t)(rpm >> 8), (uint8_t)(rpm & 0xFF),  // RPM big-endian
        (uint8_t)throttle_pos,                         // throttle %
        0x00,                                          // engine load
        (uint8_t)coolant_temp,                         // coolant temp
        0x00, 0x00,
        (uint8_t)(frame_counter & 0xFF)                // rolling counter
    };
    send_can(CAN_ID_ENGINE_RPM, data, 8);
}

void send_vehicle_speed() {
    uint16_t speed = (uint16_t)(vehicle_speed * 100);  // speed in 0.01 km/h
    uint8_t data[8] = {
        (uint8_t)(speed >> 8), (uint8_t)(speed & 0xFF),
        0x00, 0x00, 0x00, 0x00, 0x00,
        (uint8_t)(frame_counter & 0xFF)
    };
    send_can(CAN_ID_VEHICLE_SPEED, data, 8);
}

void send_steering() {
    int16_t angle = (int16_t)(steering_angle * 10);  // 0.1 degree resolution
    uint8_t data[8] = {
        (uint8_t)(angle >> 8), (uint8_t)(angle & 0xFF),
        0x00, 0x00, 0x00, 0x00, 0x00,
        (uint8_t)(frame_counter & 0xFF)
    };
    send_can(CAN_ID_STEERING, data, 8);
}

void send_brake_status() {
    uint8_t data[8] = {
        braking ? 0x01 : 0x00,        // brake pedal
        braking ? 0x50 : 0x00,        // brake pressure
        0x00,                          // ABS active
        0x00,                          // ESP active
        0x00, 0x00, 0x00,
        (uint8_t)(frame_counter & 0xFF)
    };
    send_can(CAN_ID_BRAKE, data, 8);
}

void send_abs_status() {
    uint8_t data[4] = {
        0x00,                          // ABS fault code
        braking ? 0x01 : 0x00,        // ABS active
        0x00,                          // wheel slip
        (uint8_t)(frame_counter & 0xFF)
    };
    send_can(CAN_ID_ABS, data, 4);
}

void send_transmission() {
    uint8_t data[8] = {
        gear,                          // current gear
        0x00,                          // gear request
        (uint8_t)(engine_rpm / 50),    // torque converter
        0x00,                          // transmission temp
        0x00, 0x00, 0x00,
        (uint8_t)(frame_counter & 0xFF)
    };
    send_can(CAN_ID_TRANSMISSION, data, 8);
}

void send_throttle() {
    uint8_t data[4] = {
        (uint8_t)throttle_pos,         // throttle position %
        (uint8_t)(throttle_pos * 2.55),// throttle voltage (0-255)
        0x00,
        (uint8_t)(frame_counter & 0xFF)
    };
    send_can(CAN_ID_THROTTLE, data, 4);
}

void send_coolant_temp() {
    uint8_t data[4] = {
        (uint8_t)coolant_temp,         // coolant temp celsius
        0x00,                          // oil temp
        0x00,                          // intake air temp
        (uint8_t)(frame_counter & 0xFF)
    };
    send_can(CAN_ID_COOLANT_TEMP, data, 4);
}

void send_door_status() {
    // Randomly toggle door every ~30 seconds
    if (random(3000) < 1) {
        door_open = !door_open;
        Serial.printf("[SIM] Door %s\n", door_open ? "OPEN" : "CLOSED");
    }
    uint8_t data[4] = {
        door_open ? 0x01 : 0x00,      // driver door
        0x00,                          // passenger door
        0x00,                          // rear left
        0x00                           // rear right
    };
    send_can(CAN_ID_DOOR_STATUS, data, 4);
}

void send_airbag_heartbeat() {
    uint8_t data[4] = {
        0x00,                          // fault code (0 = OK)
        0x01,                          // system ready
        0x00,                          // crash sensor
        (uint8_t)(frame_counter & 0xFF)
    };
    send_can(CAN_ID_AIRBAG, data, 4);
}

void loop() {
    unsigned long now = millis();

    update_driving_simulation();

    // 10ms cycle — fast signals (RPM, speed) — 100 Hz
    if (now - last_10ms >= 10) {
        last_10ms = now;
        send_engine_rpm();
        send_vehicle_speed();
    }

    // 50ms cycle — medium signals (steering, brake, ABS) — 20 Hz
    if (now - last_50ms >= 50) {
        last_50ms = now;
        send_steering();
        send_brake_status();
        send_abs_status();
        send_transmission();
    }

    // 100ms cycle — slow signals (temp, doors, airbag) — 10 Hz
    if (now - last_100ms >= 100) {
        last_100ms = now;
        send_throttle();
        send_coolant_temp();
        send_door_status();
        send_airbag_heartbeat();
    }

    // Print stats every 5 seconds
    static unsigned long last_stats = 0;
    if (now - last_stats >= 5000) {
        last_stats = now;
        Serial.printf("[STATS] RPM:%.0f SPD:%.1fkm/h THR:%.0f%% GEAR:%d TEMP:%.0fC STEER:%.1f° FRAMES:%lu\n",
            engine_rpm, vehicle_speed, throttle_pos, gear, coolant_temp, steering_angle, frame_counter);
    }
}
