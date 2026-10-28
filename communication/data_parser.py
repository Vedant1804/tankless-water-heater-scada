"""
Data Parser and Validator for Incoming Process Packets.
Parses CSV strings (primary) and JSON strings (secondary) received over UDP.
Validates variable counts, datatypes, and physical sanity bounds.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Sanity physical bounds for sanity filtering (reject crazy sensor spikes)
BOUNDS = {
    "outlet_temp": (0.0, 150.0),       # °C
    "flow_rate": (0.0, 50.0),          # L/min
    "burner_power": (0.0, 100.0),      # kW
    "heat_cell_temp": (0.0, 200.0)     # °C
}


def parse_process_payload(raw_data: bytes) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse a raw UDP byte payload into a validated process dictionary.

    Format expected (CSV):
        outlet_temperature,flow_rate,burner_power,heat_cell_temperature
        e.g. "48.08,5.00,13.20,48.10"

    Returns:
        (data_dict, None) on success
        (None, error_message) on failure
    """
    if not raw_data:
        return None, "Empty payload received"

    try:
        text = raw_data.decode("utf-8", errors="replace").strip()
    except Exception as exc:
        return None, f"UTF-8 decode error: {exc}"

    if not text:
        return None, "Decoded payload is empty"

    # Attempt 1: Standard Comma-Separated Values (CSV)
    if "," in text and not text.startswith("{"):
        tokens = [token.strip() for token in text.split(",")]
        if len(tokens) < 4:
            return None, f"Insufficient tokens in payload: expected 4, got {len(tokens)} ('{text}')"

        try:
            outlet_temp = float(tokens[0])
            flow_rate = float(tokens[1])
            burner_power = float(tokens[2])
            heat_cell_temp = float(tokens[3])
        except ValueError as exc:
            return None, f"Non-numeric value in CSV payload: '{text}' ({exc})"

    # Attempt 2: JSON payload (alternative fallback)
    elif text.startswith("{") and text.endswith("}"):
        try:
            obj = json.loads(text)
            # Accept common key variations
            outlet_temp = float(obj.get("outlet_temp", obj.get("outlet_temperature", 0.0)))
            flow_rate = float(obj.get("flow_rate", obj.get("flow", 0.0)))
            burner_power = float(obj.get("burner_power", obj.get("power", 0.0)))
            heat_cell_temp = float(obj.get("heat_cell_temp", obj.get("heat_cell_temperature", 0.0)))
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            return None, f"JSON parsing failed: '{text}' ({exc})"
    else:
        # Fallback whitespace separated
        tokens = text.split()
        if len(tokens) >= 4:
            try:
                outlet_temp = float(tokens[0])
                flow_rate = float(tokens[1])
                burner_power = float(tokens[2])
                heat_cell_temp = float(tokens[3])
            except ValueError:
                return None, f"Unrecognized payload format: '{text}'"
        else:
            return None, f"Unrecognized payload format: '{text}'"

    # Physical Bounds Validation
    parsed = {
        "outlet_temp": round(outlet_temp, 2),
        "flow_rate": round(flow_rate, 2),
        "burner_power": round(burner_power, 2),
        "heat_cell_temp": round(heat_cell_temp, 2),
        "timestamp": datetime.now()
    }

    for key, (lower, upper) in BOUNDS.items():
        val = parsed[key]
        if not (lower <= val <= upper):
            return None, f"Value out of bounds for {key}: {val} (allowed {lower} to {upper})"

    return parsed, None
