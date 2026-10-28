"""
Dynamic Physical Process Simulator for Tankless Gas Water Heater / Heat Cell.
Used exclusively in DEMO MODE to generate realistic, physically coupled process responses
without requiring physical ESP32 or Simulink model to be active.
"""

import math
import random
import time
from datetime import datetime
from typing import Dict, Any


class WaterHeaterDemoSimulator:
    """
    First-principles coupled thermal and hydraulic simulator representing
    the tankless water heater process:
    - Tap demand / water flow (L/min)
    - Flow switch contact (trips at 1.8 L/min)
    - Burner thermal firing (kW)
    - Heat cell thermal dynamics (°C)
    - Pipe transport lag and heat loss
    - Outlet temperature sensor (°C)
    """

    def __init__(self):
        # Physical boundary conditions
        self.t_inlet = 20.0             # Inlet cold water temperature (°C)
        self.flow_switch_threshold = 1.8 # Min flow rate (L/min) to engage burner

        # State variables
        self.flow_rate = 5.00           # Current water flow (L/min)
        self.target_flow = 5.00         # Flow setpoint for demo transitions
        self.burner_power = 13.20       # Burner firing power (kW)
        self.heat_cell_temp = 48.10     # Heat cell metal & fluid temperature (°C)
        self.outlet_temp = 48.08        # Pipe outlet water temperature (°C)

        # Dynamic simulation clock
        self.last_sim_time = time.time()
        self.sim_tick = 0

    def set_flow_demand(self, target_lpm: float):
        """Allow manual adjustment of simulated flow demand."""
        self.target_flow = max(0.0, min(15.0, target_lpm))

    def step(self, dt: float = 1.0) -> Dict[str, Any]:
        """
        Advance process dynamics by dt seconds.
        Returns the exact 4 process variables.
        """
        self.sim_tick += 1

        # 1. Hydraulic Flow Dynamics (Tap demand with realistic turbulent fluctuations)
        # Smooth transition toward target_flow
        self.flow_rate += (self.target_flow - self.flow_rate) * min(1.0, dt / 2.0)
        
        # Subtle sensor noise and turbulence if flow is active
        if self.flow_rate > 0.1:
            flow_noise = 0.04 * math.sin(self.sim_tick * 0.3) + random.uniform(-0.02, 0.02)
            actual_flow = max(0.0, self.flow_rate + flow_noise)
        else:
            actual_flow = 0.0

        # 2. Flow Switch & Burner Ignition Logic
        # If flow is below safety switch threshold (1.8 L/min), burner cannot ignite (0 kW)
        if actual_flow >= self.flow_switch_threshold:
            # Steady heating power needed: P_th ~ m_dot * Cp * delta_T
            # For 5 L/min and delta_T ~ 28°C (20°C -> 48°C), theoretical thermal power ~ 9.76 kW
            # With combustion & heat cell efficiency (~74%), gas input power is ~ 13.2 kW
            target_power = actual_flow * 2.64
            # Add small flame modulation ripple
            flame_ripple = 0.15 * math.sin(self.sim_tick * 0.5) + random.uniform(-0.05, 0.05)
            # First order burner ramp
            self.burner_power += (target_power - self.burner_power) * min(1.0, dt / 1.5)
            actual_power = max(0.0, self.burner_power + flame_ripple)
        else:
            # Instant shutdown when flow switch opens
            self.burner_power = 0.0
            actual_power = 0.0

        # 3. Heat Cell Thermal Dynamics
        # Heat balance: C_cell * dT_cell/dt = eta * P_burner - m_dot * Cp * (T_cell - T_inlet) - heat_loss
        if actual_flow > 0.2:
            # Steady-state temperature target dictated by burner power and flow rate
            # delta_T = (P_burner * efficiency) / (flow_rate * Cp_factor)
            power_to_temp_gain = 2.12  # Empirical scaling factor matching Simulink heat cell
            target_cell_temp = self.t_inlet + (actual_power / max(1.0, actual_flow)) * power_to_temp_gain
        else:
            # No flow: cooling toward ambient
            target_cell_temp = self.t_inlet

        # Thermal inertia of the copper/stainless heat cell (time constant ~ 4 seconds)
        alpha_cell = min(1.0, dt / 4.0)
        self.heat_cell_temp += (target_cell_temp - self.heat_cell_temp) * alpha_cell
        cell_noise = random.uniform(-0.03, 0.03)
        actual_cell_temp = self.heat_cell_temp + cell_noise

        # 4. Pipe Transport & Outlet Temperature Sensor Dynamics
        # Water travels through pipe with transport delay and thermal conduction
        # Pipe thermal lag (time constant ~ 2.5 seconds)
        alpha_pipe = min(1.0, dt / 2.5)
        self.outlet_temp += (self.heat_cell_temp - self.outlet_temp) * alpha_pipe
        # Sensor micro-noise (typical RTD/thermocouple ADC noise)
        sensor_noise = random.uniform(-0.02, 0.02)
        actual_outlet_temp = max(self.t_inlet, self.outlet_temp + sensor_noise)

        return {
            "outlet_temp": round(actual_outlet_temp, 2),
            "flow_rate": round(actual_flow, 2),
            "burner_power": round(actual_power, 2),
            "heat_cell_temp": round(actual_cell_temp, 2),
            "timestamp": datetime.now()
        }
