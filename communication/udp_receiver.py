"""
Thread-safe UDP Receiver for Industrial SCADA Telemetry.
Listens for UDP datagrams transmitted by ESP32 or external emulators,
validates payload syntax, and updates real-time process state.
"""

import socket
import threading
import time
from datetime import datetime
import logging
from typing import Dict, Any, Optional, Tuple
from communication.data_parser import parse_process_payload
import config

logger = logging.getLogger(__name__)


class UDPDataReceiver:
    """
    Background daemon thread listening on a UDP port for real-time process data.
    Ensures zero UI blocking and thread-safe data access for Streamlit.
    """

    def __init__(self, host: str = config.DEFAULT_UDP_HOST, port: int = config.DEFAULT_UDP_PORT):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.thread: Optional[threading.Thread] = None
        self.is_running = False
        self.lock = threading.Lock()

        # Telemetry state
        self.latest_data: Optional[Dict[str, Any]] = None
        self.last_packet_time: Optional[float] = None
        self.last_sender: Optional[Tuple[str, int]] = None
        self.packet_count = 0
        self.error_count = 0
        self.last_error_msg: Optional[str] = None

        # Sample rate estimation
        self._recent_timestamps = []

    def start(self) -> Tuple[bool, str]:
        """Start listening on the configured UDP port in a non-blocking background thread."""
        with self.lock:
            if self.is_running and self.thread and self.thread.is_alive():
                return True, f"Receiver already active on port {self.port}"

            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.sock.bind((self.host, self.port))
                self.sock.settimeout(0.5)  # Periodic timeout to allow clean shutdown
                self.is_running = True
            except Exception as exc:
                self.is_running = False
                if self.sock:
                    try:
                        self.sock.close()
                    except Exception:
                        pass
                    self.sock = None
                return False, f"Failed to bind UDP socket on {self.host}:{self.port} - {exc}"

            self.thread = threading.Thread(target=self._listen_loop, daemon=True, name="SCADA-UDP-Receiver")
            self.thread.start()
            return True, f"Listening on UDP port {self.port}"

    def stop(self):
        """Stop receiver thread and release socket cleanly."""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        with self.lock:
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None

    def restart(self, port: int) -> Tuple[bool, str]:
        """Restart on a new port if reconfigured."""
        self.stop()
        self.port = port
        return self.start()

    def _listen_loop(self):
        """Internal daemon loop reading datagrams from ESP32."""
        while self.is_running:
            try:
                if not self.sock:
                    break
                raw_bytes, sender = self.sock.recvfrom(2048)
                current_time = time.time()

                parsed, error_msg = parse_process_payload(raw_bytes)

                with self.lock:
                    if parsed:
                        self.latest_data = parsed
                        self.last_packet_time = current_time
                        self.last_sender = sender
                        self.packet_count += 1

                        # Track sample rate over sliding window
                        self._recent_timestamps.append(current_time)
                        if len(self._recent_timestamps) > 20:
                            self._recent_timestamps.pop(0)
                    else:
                        self.error_count += 1
                        self.last_error_msg = error_msg
            except socket.timeout:
                # Normal timeout; loop back to check self.is_running
                continue
            except Exception as exc:
                if self.is_running:
                    with self.lock:
                        self.error_count += 1
                        self.last_error_msg = str(exc)
                break

    def get_latest(self) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        Thread-safe retrieval of latest telemetry and connection statistics.
        Non-blocking: safe to call from Streamlit's main execution thread.

        Returns:
            (latest_data_dict_or_None, stats_dict)
        """
        now = time.time()
        with self.lock:
            data_copy = dict(self.latest_data) if self.latest_data else None

            # Calculate sample rate in Hz over recent window
            hz = 0.0
            if len(self._recent_timestamps) >= 2:
                dt_span = self._recent_timestamps[-1] - self._recent_timestamps[0]
                if dt_span > 0:
                    hz = round((len(self._recent_timestamps) - 1) / dt_span, 1)

            # Determine connection status and user-facing labels
            if not self.is_running:
                status = "OFFLINE"
                status_label = "Offline"
            elif self.last_packet_time is None:
                status = "WAITING_FOR_ESP32"
                status_label = config.STATUS_WAITING_ESP32
            else:
                elapsed = now - self.last_packet_time
                if elapsed < config.COMM_STALE_SEC:
                    status = "CONNECTED"
                    status_label = config.STATUS_CONNECTED
                elif elapsed < config.COMM_TIMEOUT_SEC:
                    status = "STALE"
                    status_label = config.STATUS_STALE
                else:
                    status = "COMMUNICATION_LOSS"
                    status_label = config.STATUS_CONNECTION_LOST

            # Formatted last packet timestamp
            if self.last_packet_time:
                last_pkt_time_str = datetime.fromtimestamp(self.last_packet_time).strftime("%H:%M:%S")
                elapsed_sec = round(now - self.last_packet_time, 1)
            else:
                last_pkt_time_str = "Waiting for ESP32..."
                elapsed_sec = None

            stats = {
                "status": status,
                "status_label": status_label,
                "is_running": self.is_running,
                "port": self.port,
                "host": self.host,
                "packet_count": self.packet_count,
                "error_count": self.error_count,
                "last_error": self.last_error_msg,
                "last_packet_time": self.last_packet_time,
                "last_packet_time_str": last_pkt_time_str,
                "elapsed_since_packet": elapsed_sec,
                "sender": f"{self.last_sender[0]}:{self.last_sender[1]}" if self.last_sender else None,
                "sample_rate_hz": hz
            }

            return data_copy, stats
