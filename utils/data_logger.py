"""
Industrial Process Data Logger.
Maintains persistent CSV logs of incoming live telemetry or demo runs.
Thread-safe and exportable for engineering analysis.
"""

import os
import csv
import io
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional


class ProcessDataLogger:
    """
    Manages local file CSV logging and in-memory logging buffer.
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.lock = threading.Lock()
        self.current_filepath: Optional[str] = None
        self.records: List[Dict[str, Any]] = []
        self.is_logging_enabled = True

        os.makedirs(self.log_dir, exist_ok=True)
        self._init_new_file()

    def _init_new_file(self):
        """Create a new timestamped CSV file with standard SCADA header."""
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_filepath = os.path.join(self.log_dir, f"process_telemetry_{now_str}.csv")
        try:
            with open(self.current_filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp",
                    "Outlet_Temperature_C",
                    "Flow_Rate_Lmin",
                    "Burner_Power_kW",
                    "Heat_Cell_Temperature_C",
                    "Data_Source",
                    "Alarm_State"
                ])
        except Exception as exc:
            print(f"[Logger Error] Could not create CSV log file: {exc}")

    def log_record(
        self,
        data: Dict[str, Any],
        source: str,
        alarm_state: str = "NORMAL"
    ):
        """
        Append a process record to in-memory buffer and active CSV file.
        """
        if not self.is_logging_enabled or not data:
            return

        ts_str = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if isinstance(data.get("timestamp"), datetime) else str(data.get("timestamp", datetime.now()))

        record = {
            "Timestamp": ts_str,
            "Outlet_Temperature_C": data.get("outlet_temp", 0.0),
            "Flow_Rate_Lmin": data.get("flow_rate", 0.0),
            "Burner_Power_kW": data.get("burner_power", 0.0),
            "Heat_Cell_Temperature_C": data.get("heat_cell_temp", 0.0),
            "Data_Source": source,
            "Alarm_State": alarm_state
        }

        with self.lock:
            self.records.append(record)

            # Cap in-memory records to prevent memory exhaustion
            if len(self.records) > 5000:
                self.records.pop(0)

            if self.current_filepath:
                try:
                    with open(self.current_filepath, mode="a", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            record["Timestamp"],
                            record["Outlet_Temperature_C"],
                            record["Flow_Rate_Lmin"],
                            record["Burner_Power_kW"],
                            record["Heat_Cell_Temperature_C"],
                            record["Data_Source"],
                            record["Alarm_State"]
                        ])
                except Exception as exc:
                    print(f"[Logger Error] Could not append to CSV: {exc}")

    def get_csv_bytes(self) -> bytes:
        """Export all logged records in memory as downloadable CSV bytes."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Timestamp",
            "Outlet_Temperature_C",
            "Flow_Rate_Lmin",
            "Burner_Power_kW",
            "Heat_Cell_Temperature_C",
            "Data_Source",
            "Alarm_State"
        ])

        with self.lock:
            for rec in self.records:
                writer.writerow([
                    rec["Timestamp"],
                    rec["Outlet_Temperature_C"],
                    rec["Flow_Rate_Lmin"],
                    rec["Burner_Power_kW"],
                    rec["Heat_Cell_Temperature_C"],
                    rec["Data_Source"],
                    rec["Alarm_State"]
                ])

        return output.getvalue().encode("utf-8")

    def get_record_count(self) -> int:
        with self.lock:
            return len(self.records)

    def clear(self):
        with self.lock:
            self.records.clear()
            self._init_new_file()
