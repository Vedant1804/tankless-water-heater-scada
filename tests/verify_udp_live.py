import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import socket
import config
from communication.udp_receiver import UDPDataReceiver
from communication.data_parser import parse_process_payload

# 1. Test Parser directly with exact user CSV payload
test_payload = b"48.08,5.00,13.20,48.10\n"
parsed, err = parse_process_payload(test_payload)
assert err is None, f"Parse error: {err}"
assert parsed["outlet_temp"] == 48.08
assert parsed["flow_rate"] == 5.00
assert parsed["burner_power"] == 13.20
assert parsed["heat_cell_temp"] == 48.10
print("[TEST 1/3 PASSED] CSV Payload parsed accurately: 48.08, 5.00, 13.20, 48.10")

# 2. Test Receiver Initial Waiting State
rx = UDPDataReceiver(host="127.0.0.1", port=5012)
rx.start()
data, stats = rx.get_latest()
assert data is None, "Data must be None before any packets arrive"
assert stats["status"] == "WAITING_FOR_ESP32", f"Expected WAITING_FOR_ESP32, got {stats['status']}"
assert stats["status_label"] == config.STATUS_WAITING_ESP32
print("[TEST 2/3 PASSED] Receiver starts in 'Waiting for ESP32' state without fake data.")

# 3. Test Live Packet Transmission and Connected State
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(test_payload, ("127.0.0.1", 5012))
time.sleep(0.15)

live_data, live_stats = rx.get_latest()
sock.close()
rx.stop()

assert live_data is not None, "Failed to capture live UDP packet"
assert live_data["outlet_temp"] == 48.08
assert live_data["flow_rate"] == 5.00
assert live_data["burner_power"] == 13.20
assert live_data["heat_cell_temp"] == 48.10
assert live_stats["status"] == "CONNECTED"
assert live_stats["status_label"] == config.STATUS_CONNECTED
print(f"[TEST 3/3 PASSED] Real packet received & state changed to 'Connected / Receiving Data': {live_data}")

print("\n===> ALL 3 LOCAL UDP TELEMETRY TESTS PASSED 100%! <===")
