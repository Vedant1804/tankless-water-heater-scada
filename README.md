# Tankless Gas Water Heater / Heat Cell Process SCADA System
## Real-Time Process Monitoring & Academic Digital Model Dashboard

---

### 1. Executive Summary & Project Overview

This project is a professional, industrial-grade **Supervisory Control and Data Acquisition (SCADA) / Human-Machine Interface (HMI)** process monitoring dashboard for an academic digital twin of a **tankless gas water heater and heat cell process**.

The system is designed specifically for presentations to **engineering faculty, project evaluators, and industrial automation professionals**, providing an authentic process plant interface adhering to ISA-18.2 alarm management and modern industrial visual hierarchy standards.

#### Key Process Constraints & Scope:
- **Exclusively 4 Process Variables**: The system monitors the physical process states without artificial or unmodeled controller data:
  1. **Outlet Temperature** ($T_{out}$, `TT-101`) [°C]
  2. **Water Flow Rate** ($\dot{m}$, `FT-101`) [L/min]
  3. **Burner Thermal Power** ($P_{burner}$, `PT-101`) [kW]
  4. **Heat Cell Temperature** ($T_{cell}$, `TT-102`) [°C]
- **No Controller Artificial Data**: No PID, no MPC, no artificial setpoint tracking or simulated control loops are present, keeping the focus strictly on the actual Simulink digital model outputs.

---

### 2. End-to-End System Architecture

```
┌─────────────────────────────────┐
│     Simulink Process Model      │
│ (Tap Flow, Switch, Heat Cell)   │
└────────────────┬────────────────┘
                 │ USB Serial (115200 baud)
                 ▼
┌─────────────────────────────────┐
│      ESP32 Microcontroller      │
│ (WiFi UDP Bridge: Port 5005)    │
└────────────────┬────────────────┘
                 │ Wi-Fi UDP Datagrams (Local Network / Hotspot)
                 ▼
┌─────────────────────────────────┐
│   Python Industrial SCADA HMI   │
│   (Streamlit + Plotly Engine)   │
└─────────────────────────────────┘
```

#### Dual Operational Modes:
1. **DEMO MODE**:
   - Executes a dynamic first-principles physical simulation of coupled fluid flow, burner firing, heat exchanger thermal inertia, and transport delay.
   - Allows full UI demonstration and testing independently of hardware.
   - Clearly stamped as simulated data.
2. **LIVE MODE**:
   - Spawns a background non-blocking UDP receiver thread listening on port 5005.
   - Parses incoming CSV datagrams from the ESP32.
   - Features real-time packet rate monitoring (Hz), stale data warnings, and communication loss alarms.

---

### 3. Payload Protocol Specification

Both the ESP32 firmware and Python parser utilize a standardized, lightweight comma-separated value (CSV) string terminated with a newline:

```text
outlet_temperature,flow_rate,burner_power,heat_cell_temperature\n
```

**Concrete Example:**
```text
48.08,5.00,13.20,48.10
```

| Field Index | Variable Name | Unit | Nominal Range | Description |
|:---:|:---|:---:|:---:|:---|
| 0 | `outlet_temperature` | °C | 10.0 – 80.0 | Heated fluid discharge temperature |
| 1 | `flow_rate` | L/min | 0.0 – 15.0 | Water demand through heat cell |
| 2 | `burner_power` | kW | 0.0 – 30.0 | Thermal power modulated by gas burner |
| 3 | `heat_cell_temperature` | °C | 10.0 – 95.0 | Core temperature of heat cell exchanger |

---

### 4. Step-by-Step Windows Installation & Execution Guide

Follow these exact steps in your Windows Command Prompt or PowerShell:

#### Step 1: Open PowerShell / Command Prompt
Press `Win + R`, type `powershell` or `cmd`, and press **Enter**.

#### Step 2: Navigate to the Project Workspace
```powershell
cd "e:\MPC project\7th sem project\Burner Project"
```

#### Step 3: Verify Python Installation
Check which Python executable is available on your machine:
```powershell
py -0
# or
& "C:\Users\ramj2\AppData\Local\Programs\Python\Python312\python.exe" --version
```
*(Python 3.12 is pre-installed on this machine at the path above).*

#### Step 4: Create a Dedicated Virtual Environment
```powershell
& "C:\Users\ramj2\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv
```

#### Step 5: Activate the Virtual Environment
```powershell
.venv\Scripts\Activate.ps1
# If you are in standard Command Prompt (cmd.exe), run instead:
# .venv\Scripts\activate.bat
```

> **Note on PowerShell Script Execution**: If PowerShell displays an `Execution_Policies` restriction warning, enable running local scripts for this session:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .venv\Scripts\Activate.ps1
> ```

#### Step 6: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

#### Step 7: Launch the SCADA Dashboard
```powershell
streamlit run app.py
```
Streamlit will launch and automatically open your default browser to:
`http://localhost:8501`

---

### 5. Operating Instructions

#### Testing in DEMO MODE
1. Launch `streamlit run app.py`.
2. The dashboard defaults to **DEMO MODE (Simulated)**.
3. Observe:
   - **4 Top KPI Cards**: Outlet Temp (`48.08 °C`), Flow Rate (`5.00 L/min`), Burner Power (`13.20 kW`), Heat Cell Temp (`48.10 °C`) with live range meters and limit badges.
   - **Interactive Process Flow Diagram (PFD)**: Animated flow chevron pulses, flow switch contact indicator, combustion flame graphic, and live thermal gradients.
   - **3 Real-time Plotly Line Charts**:
     - *Chart 1*: Outlet Temperature Trend with high warning & alarm limit lines.
     - *Chart 2*: Flow Rate Trend with switch trip limit line.
     - *Chart 3*: Burner Power Trend with max firing threshold.
   - **Annunciation Panel**: ISA-18.2 style alarm matrix.
4. Click **⏸ PAUSE** to freeze updates, or **▶ START** to resume.
5. In the sidebar, select different **Rolling Time Windows** (30s, 1m, 2m, 5m, 10m).
6. Click **📥 Download CSV Log** to export all captured data points.

---

### 6. Testing LIVE MODE

You can verify LIVE MODE using either:
- **Method A**: The included Python UDP Emulator (tests everything on your laptop before touching hardware).
- **Method B**: The ESP32 Autonomous Test Generator Mode.
- **Method C**: Full Simulink Serial to ESP32 to Wi-Fi connection.

#### Method A: Testing with the Built-In UDP Emulator (No Hardware Required)
1. In the dashboard sidebar, switch **Operating Mode** to **LIVE MODE (ESP32 UDP)**.
2. Notice the status bar changes to `UDP: LISTENING...` awaiting packets.
3. Open a **second terminal window** and activate the environment:
   ```powershell
   cd "e:\MPC project\7th sem project\Burner Project"
   .venv\Scripts\Activate.ps1
   python tools/udp_sender_test.py --mode normal --rate 2
   ```
4. Look at the dashboard:
   - Link status immediately turns to **LIVE UDP: 5005 (2.0 Hz)** in green.
   - Real-time data streams into KPI cards and graphs without any lag.
5. Test Alarm Annunciation:
   Stop the emulator and run:
   ```powershell
   python tools/udp_sender_test.py --mode high_temp
   ```
   Observe the dashboard trigger an amber **High Warning** at 58°C and a red **High-High Alarm** at 65°C on TT-101!
6. Test Communication Loss:
   Stop the emulator script (`Ctrl+C`). After 3.0 seconds, the dashboard annunciates **COMMUNICATION LOSS (COMM-01)** in red.

---

### 7. ESP32 Microcontroller Setup & Deployment

The ESP32 sketch is located at:
[`esp32/esp32_udp_bridge.ino`](file:///e:/MPC%20project/7th%20sem%20project/Burner%20Project/esp32/esp32_udp_bridge.ino)

#### Step 1: Find Your Laptop's Wi-Fi IP Address
1. Open PowerShell or Command Prompt.
2. Run:
   ```powershell
   ipconfig
   ```
3. Locate your **Wireless LAN adapter Wi-Fi** section and note the **IPv4 Address** (e.g. `192.168.1.100` or `192.168.43.50`).

#### Step 2: Configure the ESP32 Code
Open `esp32/esp32_udp_bridge.ino` in the Arduino IDE:
1. Update the Wi-Fi credentials:
   ```cpp
   const char* WIFI_SSID     = "Your_WiFi_Network_Or_Hotspot";
   const char* WIFI_PASSWORD = "Your_Password";
   ```
2. Update the laptop's IP address:
   ```cpp
   const char* LAPTOP_IP     = "192.168.1.100"; // Replace with your IP
   const int   UDP_PORT      = 5005;
   ```

#### Step 3: Flash the ESP32
1. Connect your ESP32 to your laptop via USB cable.
2. Select your board (`ESP32 Dev Module`) and COM Port in Arduino IDE.
3. Click **Upload**.
4. Open the Arduino Serial Monitor at `115200` baud to confirm the ESP32 connects to Wi-Fi and prints its assigned IP.

---

### 8. Simulink Model Serial Interfacing

To feed live outputs from your Simulink model to the ESP32:

1. In Simulink, open the **Instrument Control Toolbox** (or Serial library).
2. Add a **Serial Send** or **To Instrument** block to the output of your 4 process variables.
3. Use a **String Format** or **S-Function / MATLAB Function block** to format the values into CSV:
   ```matlab
   % MATLAB Function Block inside Simulink:
   function payload = format_telemetry(outlet_temp, flow_rate, burner_power, heat_cell_temp)
       payload = sprintf('%.2f,%.2f,%.2f,%.2f\n', outlet_temp, flow_rate, burner_power, heat_cell_temp);
   end
   ```
4. Connect the output to the **Serial Send** block:
   - **Port**: Set to your ESP32's COM port (e.g., `COM3`, `COM4`).
   - **Baud rate**: `115200`.
   - **Terminator**: `LF (\n)`.
5. Run your Simulink simulation! The ESP32 will read each line over USB Serial and broadcast it as a UDP packet to your dashboard.

---

### 9. Alarm & Trip Limit Thresholds

Default industrial parameters configured in [`config.py`](file:///e:/MPC%20project/7th%20sem%20project/Burner%20Project/config.py):

| Parameter | Tag | Warning Limit (Amber) | Alarm Limit (Red) | Logic / Engineering Reason |
|:---|:---:|:---:|:---:|:---|
| **Outlet Temp** | `TT-101` | $\ge 58.0$ °C | $\ge 65.0$ °C | Scald hazard prevention |
| **Flow Rate** | `FT-101` | $< 2.0$ L/min | $\le 1.8$ L/min | Below switch engagement threshold |
| **Burner Power** | `PT-101` | $\ge 26.0$ kW | -- | Near maximum thermal modulation |
| **Heat Cell Temp** | `TT-102` | $\ge 75.0$ °C | -- | Heat exchanger core thermal stress |
| **Communication** | `COMM-01` | $> 1.5$ s delay | $> 3.0$ s delay | Telemetry drop detection |

All thresholds can be dynamically tuned live in the sidebar under **⚙️ Alarm Limits Configuration**.

---

### 10. Troubleshooting Common Windows Issues

| Issue / Symptom | Root Cause | Solution |
|:---|:---|:---|
| **Windows Security Alert pop-up on first launch** | Windows Defender Firewall blocking inbound UDP port 5005. | Click **Allow access** on both **Private** and **Public** networks. |
| **Status shows `UDP: WAITING FOR DATA` indefinitely in Live mode** | Laptop and ESP32 are not on the same subnet, or wrong IP was entered in ESP32. | 1. Ensure both laptop and ESP32 are connected to the same Wi-Fi router or phone mobile hotspot.<br>2. Run `ipconfig` on the laptop and verify the IP matches `LAPTOP_IP` in `esp32_udp_bridge.ino`. |
| **PowerShell script execution error: `cannot be loaded because running scripts is disabled`** | Windows execution policy blocks `.ps1` virtual environment activation. | Run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then re-run `.venv\Scripts\Activate.ps1`. |
| **Port 5005 already in use error** | Another application or previous background process is bound to port 5005. | Change the port to `5006` in both the dashboard sidebar and ESP32 firmware, or kill the lingering process using `netstat -ano \| findstr :5005`. |
| **Graph points reset when changing controls** | Outdated Streamlit execution model. | The system utilizes `@st.fragment` partial rendering; controls and trend history remain cached in `st.session_state`. |

---

### 11. Project Directory Structure

```
Burner Project/
│
├── .streamlit/
│   └── config.toml           # Industrial SCADA dark theme palette definition
│
├── app.py                    # Main Streamlit SCADA application entrypoint
├── config.py                 # System tags, thresholds, units, and palettes
├── requirements.txt          # Python dependencies
├── README.md                 # Technical engineering documentation & instructions
│
├── components/
│   ├── __init__.py
│   ├── header.py             # SCADA header banner, system clock, & status LEDs
│   ├── kpi_cards.py          # 4 Primary process variable metric cards
│   ├── live_charts.py        # 3 Dedicated Plotly trend line charts
│   ├── process_overview.py   # SVG/HTML industrial Process Flow Diagram (PFD)
│   ├── alarm_panel.py        # ISA-18.2 alarm matrix and annunciator table
│   └── controls.py           # Operator sidebar console & threshold inputs
│
├── communication/
│   ├── __init__.py
│   ├── data_parser.py        # Robust CSV/JSON payload parser & validator
│   └── udp_receiver.py       # Threaded non-blocking UDP background socket listener
│
├── data/
│   ├── __init__.py
│   └── sample_data.py        # First-principles dynamic thermal demo simulator
│
├── utils/
│   ├── __init__.py
│   ├── data_logger.py        # Thread-safe persistent CSV logging engine
│   └── helpers.py            # Custom CSS styling injection & alarm evaluator
│
├── esp32/
│   └── esp32_udp_bridge.ino  # Ready-to-flash ESP32 Arduino C++ firmware
│
└── tools/
    └── udp_sender_test.py    # Windows command-line UDP test emulator
```
