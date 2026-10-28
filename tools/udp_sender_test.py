"""
UDP Telemetry Emulator & Testing Utility for Live Mode.
Emulates an ESP32 or Simulink model sending real-time UDP packets
to the Tankless Water Heater SCADA Dashboard.

Usage:
    python tools/udp_sender_test.py
    python tools/udp_sender_test.py --mode high_temp
    python tools/udp_sender_test.py --mode low_flow
    python tools/udp_sender_test.py --rate 5
"""

import socket
import time
import math
import argparse
import sys


def run_sender(target_ip: str, target_port: int, rate_hz: float, scenario: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    interval = 1.0 / max(0.1, rate_hz)

    print("=" * 65)
    print("   SCADA UDP TELEMETRY EMULATOR (ESP32 / SIMULINK MOCK)")
    print("=" * 65)
    print(f"Target Endpoint:  {target_ip}:{target_port}")
    print(f"Update Rate:      {rate_hz} Hz ({interval * 1000:.0f} ms period)")
    print(f"Scenario Mode:    {scenario.upper()}")
    print("Payload Format:   outlet_temp,flow_rate,burner_power,heat_cell_temp")
    print("Press Ctrl+C to stop transmission.\n")

    t_start = time.time()
    packet_count = 0

    try:
        while True:
            t = time.time() - t_start

            if scenario == "normal":
                flow = 5.00 + 0.15 * math.sin(t * 0.4)
                power = 13.20 + 0.30 * math.sin(t * 0.3)
                cell = 48.10 + 0.12 * math.sin(t * 0.2)
                outlet = 48.08 + 0.08 * math.sin(t * 0.15)
            elif scenario == "high_temp":
                flow = 3.50 + 0.10 * math.sin(t * 0.4)
                power = 22.00 + 1.00 * math.sin(t * 0.3)
                cell = 68.50 + 2.00 * math.sin(t * 0.2)
                outlet = 64.20 + 2.50 * math.sin(t * 0.2)  # Triggers High Warning and High-High Alarm
            elif scenario == "low_flow":
                flow = 1.20 + 0.10 * math.sin(t * 0.5)     # Below switch trip (1.8 L/min)
                power = 0.00                               # Burner cut off
                cell = 32.00 - min(10.0, t * 0.5)          # Cooling
                outlet = 30.00 - min(8.0, t * 0.4)
            else:
                flow = 5.00
                power = 13.20
                cell = 48.10
                outlet = 48.08

            payload = f"{outlet:.2f},{flow:.2f},{power:.2f},{cell:.2f}\n"
            sock.sendto(payload.encode("utf-8"), (target_ip, target_port))
            packet_count += 1

            sys.stdout.write(f"\r[TX #{packet_count:05d}] {payload.strip():<40} -> {target_ip}:{target_port}")
            sys.stdout.flush()

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nTransmission stopped by operator.")
    finally:
        sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP Telemetry Sender Test")
    parser.add_argument("--ip", default="127.0.0.1", help="Target IP (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5005, help="Target UDP port (default: 5005)")
    parser.add_argument("--rate", type=float, default=2.0, help="Packet rate in Hz (default: 2.0)")
    parser.add_argument(
        "--mode",
        choices=["normal", "high_temp", "low_flow"],
        default="normal",
        help="Test scenario: normal, high_temp, or low_flow"
    )

    args = parser.parse_args()
    run_sender(args.ip, args.port, args.rate, args.mode)
