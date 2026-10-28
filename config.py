"""
SCADA & Industrial Process Configuration for Tankless Water Heater Monitoring.
All engineering units, nominal thresholds, visual palettes, and communication settings.
"""

# ==============================================================================
# APPLICATION METADATA
# ==============================================================================
APP_NAME = "Tankless Water Heater Process Monitoring"
APP_SUBTITLE = "Real-Time Process Monitoring & Digital Model"
PLANT_TAG = "PROCESS TRAIN 01 • HEAT CELL MONITORING"
SYSTEM_ID = "SCADA-WH-01"
VERSION = "2.4.0-IND"

# ==============================================================================
# COMMUNICATION DEFAULTS
# ==============================================================================
DEFAULT_UDP_HOST = "0.0.0.0"       # Listen on all interfaces
DEFAULT_UDP_PORT = 5005          # Default UDP port matching ESP32 firmware
COMM_TIMEOUT_SEC = 3.0           # Seconds before declaring communication loss
COMM_STALE_SEC = 1.5             # Seconds before declaring data stale
DEFAULT_REFRESH_RATE = 1.0       # Dashboard update period in seconds

# ==============================================================================
# PROCESS VARIABLES SPECIFICATION (STRICTLY 4 VARIABLES)
# ==============================================================================
# 1. Outlet Temperature
TAG_OUTLET_TEMP = "TT-101"
NAME_OUTLET_TEMP = "Outlet Temperature"
UNIT_OUTLET_TEMP = "°C"
RANGE_OUTLET_TEMP = (10.0, 80.0)
DEFAULT_OUTLET_HIGH_WARN = 58.0   # Amber warning
DEFAULT_OUTLET_HIGH_ALARM = 65.0  # Red scald alarm

# 2. Flow Rate
TAG_FLOW_RATE = "FT-101"
NAME_FLOW_RATE = "Water Flow Rate"
UNIT_FLOW_RATE = "L/min"
RANGE_FLOW_RATE = (0.0, 15.0)
DEFAULT_FLOW_LOW_WARN = 2.0      # Amber low flow warning
FLOW_SWITCH_TRIP = 1.8           # Minimum flow to close flow switch & permit burner

# 3. Burner Power
TAG_BURNER_POWER = "PT-101"
NAME_BURNER_POWER = "Burner Power"
UNIT_BURNER_POWER = "kW"
RANGE_BURNER_POWER = (0.0, 30.0)
DEFAULT_BURNER_HIGH_WARN = 26.0  # Amber high thermal firing warning

# 4. Heat Cell Temperature
TAG_HEAT_CELL_TEMP = "TT-102"
NAME_HEAT_CELL_TEMP = "Heat Cell Temperature"
UNIT_HEAT_CELL_TEMP = "°C"
RANGE_HEAT_CELL_TEMP = (10.0, 95.0)
DEFAULT_HEAT_CELL_HIGH_WARN = 75.0 # Amber warning for heat cell core

# ==============================================================================
# INDUSTRIAL SCADA DESIGN & COLOR PALETTE
# ==============================================================================
# SCADA Dark Navy / Charcoal Theme
COLOR_BG_PRIMARY = "#0a0e17"     # Deepest slate background
COLOR_BG_CARD = "#121a29"        # Elevated panel charcoal
COLOR_BG_CARD_HOVER = "#182337"  # Hover state
COLOR_BORDER = "#1e293b"         # Subtle slate border
COLOR_BORDER_ACCENT = "#334155"  # Active border

# Process & Status Colors
COLOR_NORMAL = "#10b981"         # Industrial Green (Normal / Operational)
COLOR_WARNING = "#f59e0b"        # Industrial Amber (Warning)
COLOR_ALARM = "#ef4444"          # Industrial Red (Alarm / Trip)
COLOR_OFFLINE = "#64748b"        # Muted Slate (Offline / Stale / Disconnected)

# Variable Theme Colors
COLOR_OUTLET_TEMP = "#00e5ff"     # Bright Cyan
COLOR_FLOW_RATE = "#06b6d4"       # Deep Water Cyan
COLOR_BURNER_POWER = "#f97316"    # Combustion Flame Orange
COLOR_HEAT_CELL_TEMP = "#a855f7"  # Thermal Core Purple / Hot Copper

# Typography & Grid
FONT_MONO = "'JetBrains Mono', 'Consolas', 'Fira Code', monospace"
FONT_SANS = "'Inter', '-apple-system', 'Segoe UI', Roboto, sans-serif"

# ==============================================================================
# DATA BUFFER & TIME WINDOWS
# ==============================================================================
MAX_HISTORY_POINTS = 1800         # Max records retained in rolling buffer (~30 min at 1s)
TIME_WINDOW_OPTIONS = {
    "30 Seconds": 30,
    "1 Minute": 60,
    "2 Minutes": 120,
    "5 Minutes": 300,
    "10 Minutes": 600,
}
DEFAULT_TIME_WINDOW = 60         # 1 Minute default rolling view
