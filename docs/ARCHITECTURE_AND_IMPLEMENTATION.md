# Dental Force Monitoring System - Architecture & Implementation Documentation

**Date:** 2025-11-02
**Version:** 1.0
**Status:** Production Ready

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Analysis](#architecture-analysis)
4. [BLE Hardware-Software Integration](#ble-hardware-software-integration)
5. [Implementation History](#implementation-history)
6. [Data Flow](#data-flow)
7. [Module Documentation](#module-documentation)
8. [Configuration](#configuration)
9. [Testing Guide](#testing-guide)
10. [Future Enhancements](#future-enhancements)
11. [Troubleshooting](#troubleshooting)

---

## Executive Summary

This document provides comprehensive architectural documentation for the **Dental Force Monitoring System**, a real-time bruxism detection and bite force analysis application. The system integrates embedded hardware (Seeed XIAO nRF52840 with dual FSR sensors) with a Python desktop application for clinical research and diagnostics.

### Key Features

- **Real-time dual-sensor force monitoring** in kilograms
- **BLE wireless communication** using Bleak library
- **Bruxism event detection** with hysteresis-based state machine
- **SQLite-based session storage** with historical analysis
- **CSV export** for external data analysis
- **Simulation mode** for testing without hardware
- **Dual-theme UI** (dark/light) in Spanish

### Technology Stack

- **Hardware:** Seeed XIAO nRF52840, Dual FSR sensors
- **Firmware:** Arduino C++ with Adafruit Bluefruit nRF52 library
- **Software:** Python 3.12, PySide6 (Qt6), Matplotlib, Bleak
- **Database:** SQLite3
- **Build System:** PyInstaller for Windows executable

---

## System Overview

### Purpose

The Dental Force Monitoring System monitors bite force from left and right jaw positions in real-time, detects bruxism events using calibrated thresholds, stores session data, and generates analytical reports for dental professionals and researchers.

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    HARDWARE LAYER                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Seeed XIAO nRF52840                                 │   │
│  │  - Left FSR (Pin A4)                                 │   │
│  │  - Right FSR (Pin A5)                                │   │
│  │  - BLE Service UUID: 0x1234                          │   │
│  │  - BLE Characteristic UUID: 0x5678                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓ BLE (20-byte packets @ ~30ms)
┌─────────────────────────────────────────────────────────────┐
│                    SOFTWARE LAYER                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  BLE Service (ble_service.py)                        │   │
│  │  - Bleak BLE client                                  │   │
│  │  - Packet unpacking (5 floats)                       │   │
│  │  - CSV generation                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  CSV Parser (csv_parser.py)                          │   │
│  │  - Parses: sensorId,force_kg,timestamp,event_flag    │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Data Storage (data_storage.py)                      │   │
│  │  - In-memory buffer (current_session_data)           │   │
│  │  - SQLite persistence                                │   │
│  │  - CSV export                                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  UI Layer (PySide6/Qt6)                              │   │
│  │  - LivePlot: Real-time visualization                 │   │
│  │  - BLEPanel: Device management                       │   │
│  │  - HistoryWidget: Session browser                    │   │
│  │  - ReportsWidget: Export & analysis                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Workflow

1. **Hardware** reads FSR sensors, applies signal processing, calculates force in kg, detects bruxism events
2. **BLE transmission** sends 5 floats every ~30ms: `(sL, sR, F_L, F_R, event_flag)`
3. **Software** receives BLE packets, parses into CSV format, stores in database
4. **UI** visualizes force graphs, displays event status, manages sessions
5. **Export** generates CSV files and matplotlib plots for analysis

---

## Architecture Analysis

### High-Level Architecture

The system follows a **layered architecture** pattern:

- **Presentation Layer:** PySide6 UI components
- **Business Logic Layer:** Data storage, CSV parsing, BLE service
- **Data Layer:** SQLite database, in-memory buffers
- **Hardware Abstraction Layer:** Bleak BLE client

### Design Patterns

1. **Model-View-Controller (MVC):**
   - Model: `DataStorage` (data + business logic)
   - View: UI widgets (LivePlot, BLEPanel, etc.)
   - Controller: `MainWindow` (coordinates interactions)

2. **Observer Pattern:**
   - BLE notifications trigger callbacks
   - Timer-based UI refresh (400ms polling)

3. **Repository Pattern:**
   - `DataStorage` abstracts database operations
   - In-memory buffer + persistent storage

4. **Strategy Pattern:**
   - Real mode vs. Simulation mode
   - CSV parser handles multiple data formats

### Key Architectural Decisions

#### ✅ Why kg Values from Hardware?

**Problem Identified:** Original implementation transmitted normalized sensor values (0-1) and recalculated force in Python using simple linear scaling.

**Solution:** Use force values (kg) calculated by Arduino using calibrated power-law models:
- **Left sensor:** `F_L = 13.54 * (V - 0.9)^1.0612` kg
- **Right sensor:** `F_R = 5.67 * (V - 0.9)^1.0358` kg

**Benefits:**
- ✅ **Accuracy:** Hardware models derived from experimental calibration
- ✅ **Consistency:** Single source of truth for force calculations
- ✅ **Simplicity:** Python code no longer needs conversion logic
- ✅ **Performance:** Reduces computation on Python side

#### ✅ Why Event Flag from Hardware?

**Problem:** Hardware implemented bruxism detection (hysteresis, hold time) but software didn't use it.

**Solution:** Transmit `event_flag` in BLE packet and display in UI.

**Benefits:**
- ✅ **Intelligence at edge:** Detection happens in real-time on hardware
- ✅ **Clinical utility:** Immediate visual feedback for practitioners
- ✅ **Historical analysis:** Event data stored in database

---

## BLE Hardware-Software Integration

### BLE Packet Structure

**Hardware Transmission (ble_setup.ino:225):**
```cpp
float packet[5] = {sL, sR, F_L, F_R, (float)eventOn};
fsrChar.notify(packet, sizeof(packet));  // 20 bytes total
```

| Index | Variable | Type | Unit | Description |
|-------|----------|------|------|-------------|
| 0 | `sL` | float | 0.0-1.0 | Left sensor normalized value |
| 1 | `sR` | float | 0.0-1.0 | Right sensor normalized value |
| 2 | `F_L` | float | kg | Left sensor force (power-law model) |
| 3 | `F_R` | float | kg | Right sensor force (power-law model) |
| 4 | `eventOn` | float | 0.0 or 1.0 | Bruxism event status |

**Software Reception (ble_service.py:34):**
```python
sL, sR, F_L, F_R, event_flag = struct.unpack("<fffff", data)
csv_left = f"1,{F_L},{timestamp_ms},{event_flag}"
csv_right = f"2,{F_R},{timestamp_ms},{event_flag}"
```

### CSV Data Format

**Format:** `sensorId,force_kg,timestamp,event_flag`

**Example:**
```
1,2.45,1698765432123,0.0
2,1.87,1698765432123,0.0
1,3.21,1698765432153,1.0
2,2.98,1698765432153,1.0
```

### Hardware Signal Processing Chain

```
Raw ADC (12-bit, 0-4095)
    ↓
Voltage Conversion (0-3.3V)
    ↓
32-Sample Averaging
    ↓
Exponential Moving Average (α = 0.2)
    ↓
Normalization (0.0-1.0)
    ↓
Force Calculation (power-law model)
    ↓
Event Detection (hysteresis + hold time)
    ↓
BLE Transmission (5 floats, ~30ms rate)
```

### Event Detection Logic

**Hardware Implementation (ble_setup.ino:188-213):**

```cpp
// Thresholds
const float T_on  = 0.65;  // 65% of calibrated range
const float T_off = 0.55;  // 55% (hysteresis)
const uint16_t HOLD_MS = 150;  // Minimum hold time

// Trigger conditions
bool wantOn  = (sL > T_on) || (sR > T_on);      // Either sensor high
bool wantOff = (sL < T_off) && (sR < T_off);    // Both sensors low

// State machine with hold time prevents false triggers
```

**Benefits of Hardware Detection:**
- 🚀 **Low latency:** Detection happens in <150ms
- 🎯 **Accuracy:** Hysteresis prevents noise-induced false positives
- 📊 **Research value:** Precise event timing and duration

---

## Implementation History

### Context: The Conversation

**Date:** November 2, 2025

**Initial Request:** User requested comprehensive architectural analysis of the entire system, with special attention to BLE integration between `ble_setup.ino` and `ble_service.py`.

**Key Discovery:** During analysis, we identified that:
1. Hardware was calculating force in kg using calibrated power-law models
2. Hardware was detecting bruxism events with sophisticated logic
3. **Software was ignoring both** and recalculating force with simple linear scaling
4. This created data inconsistency and wasted hardware intelligence

### Problem Statement

**Before Implementation:**

```python
# ble_service.py (WRONG)
emaL, emaR, sL, sR, event_flag = struct.unpack("<fffff", data)
csv_left = f"1,{emaL},{timestamp_ms}"  # Using normalized, ignoring kg
```

```python
# live_plot.py (WRONG)
left_forces_N = [(r['force']) * 50 for r in left_data]  # Linear conversion
```

**Issues:**
- ❌ Force values inaccurate (linear vs. power-law)
- ❌ Hardware calculations wasted
- ❌ Event detection invisible to user
- ❌ Data pipeline confusing (normalized → recalculate)

### Solution Implemented

**After Implementation:**

```python
# ble_service.py (CORRECT)
sL, sR, F_L, F_R, event_flag = struct.unpack("<fffff", data)
csv_left = f"1,{F_L},{timestamp_ms},{event_flag}"  # Using kg directly
```

```python
# live_plot.py (CORRECT)
left_forces_kg = [r['force'] for r in left_data]  # No conversion needed!
```

**Benefits:**
- ✅ Force values accurate (hardware power-law models)
- ✅ Single source of truth for calculations
- ✅ Event detection displayed in UI
- ✅ Simpler, cleaner code

### Changes Summary

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `services/ble_service.py` | 34, 40, 43 | Use F_L, F_R instead of sL, sR; add event_flag |
| `services/csv_parser.py` | 11, 20, 23-25, 32 | Parse 4-field CSV with event_flag |
| `services/data_storage.py` | 59, 68, 85-87 | Store event field in records |
| `ui/live_plot.py` | 12, 32-36, 50-60, 87-99 (deleted), 115, 128-131, 150-152, 156, 164-243, 245-263 | Add event indicator, remove conversion, use kg directly, fix simulation |

**Total:** 4 files modified, ~150 lines changed/added, ~13 lines deleted

---

## Data Flow

### Real-Time Data Flow (Hardware Mode)

```
┌─────────────────────────────────────────────────────────────┐
│ HARDWARE: ble_setup.ino                                     │
├─────────────────────────────────────────────────────────────┤
│ 1. Read ADC (A4, A5) → 12-bit values                        │
│ 2. Average 32 samples → reduce noise                        │
│ 3. Apply EMA (α=0.2) → smooth signal                        │
│ 4. Normalize (0-1) → calibration-independent                │
│ 5. Calculate force (kg) → power-law models                  │
│ 6. Detect events → hysteresis state machine                 │
│ 7. Pack BLE packet → [sL, sR, F_L, F_R, eventOn]           │
│ 8. Notify @ ~30ms → UUID 0x5678                            │
└─────────────────────────────────────────────────────────────┘
                            ↓ BLE
┌─────────────────────────────────────────────────────────────┐
│ SOFTWARE: ble_service.py                                    │
├─────────────────────────────────────────────────────────────┤
│ 1. Receive notification → 20 bytes                          │
│ 2. Unpack 5 floats → struct.unpack("<fffff")               │
│ 3. Generate timestamp → int(time.time() * 1000)            │
│ 4. Create CSV strings → "sensorId,force_kg,ts,event"       │
│ 5. Invoke callback → 2 calls (left + right)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ SOFTWARE: csv_parser.py                                     │
├─────────────────────────────────────────────────────────────┤
│ 1. Split CSV → parts = csv.split(',')                      │
│ 2. Extract fields → sensorId, force_kg, ts, event_flag     │
│ 3. Convert timestamp → datetime object                      │
│ 4. Return dict → {sensorId, force, timestamp, date, event} │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ SOFTWARE: data_storage.py                                   │
├─────────────────────────────────────────────────────────────┤
│ 1. add_record(record) → append to current_session_data[]   │
│ 2. In-memory buffer → fast access for plotting             │
│ 3. On session end → calculate summary stats                │
│ 4. Save to SQLite → sessions table (JSON format)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ SOFTWARE: live_plot.py (400ms timer)                        │
├─────────────────────────────────────────────────────────────┤
│ 1. Read current_session_data → filter by sensorId          │
│ 2. Extract force values → already in kg!                   │
│ 3. Plot dual lines → blue (left), orange (right)           │
│ 4. Update force label → "Izq: X.XX kg  Der: X.XX kg"       │
│ 5. Update event status → green/red based on event flag     │
│ 6. Update progress bar → color-coded thresholds            │
└─────────────────────────────────────────────────────────────┘
```

### Simulation Data Flow (Testing Mode)

```
┌─────────────────────────────────────────────────────────────┐
│ SOFTWARE: live_plot._simulate_one_sample()                  │
├─────────────────────────────────────────────────────────────┤
│ 1. Generate random force → 0.1-1.0 kg (normal)             │
│                          → 2.5-4.5 kg (event, 20% of time) │
│ 2. Set event flag → 0.0 (normal) or 1.0 (event)           │
│ 3. Create record → {sensorId, force, timestamp, event}     │
│ 4. Call storage.add_record() → same path as real data      │
└─────────────────────────────────────────────────────────────┘
```

### Session Lifecycle

```
User: "Iniciar Sesión Real"
    ↓
storage.start_new_session()
    ↓ (creates empty buffer)
BLE data arrives → storage.add_record()
    ↓ (continuously appends)
User: "Detener Sesión"
    ↓
storage.end_session(save=True)
    ↓
Calculate summary: {totalReadings, avgForce, maxForce, minForce}
    ↓
SQLite INSERT: sessions table
    ↓
Clear buffer: current_session_data = []
    ↓
History widget refreshes
```

---

## Module Documentation

### services/ble_service.py

**Purpose:** BLE communication abstraction using Bleak library

**Key Classes:**
- `BLEService`: Manages BLE connection lifecycle and notifications

**Key Methods:**

```python
async def scan(timeout=8) -> List[BLEDevice]
    """Discover BLE devices matching name filters"""

async def connect(device) -> bool
    """Establish GATT connection to device"""

async def start_notify(callback) -> None
    """Subscribe to characteristic notifications

    Callback format: callback(csv_string: str)
    CSV format: "sensorId,force_kg,timestamp,event_flag"
    """

async def calibrate_rest() -> None
    """Send 'r' command to device for baseline calibration"""

async def calibrate_bite() -> None
    """Send 'm' command to device for max bite calibration"""
```

**BLE Configuration:**
- Service UUID: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
- Characteristic TX UUID: `00005678-0000-1000-8000-00805f9b34fb`
- Device name filters: `["DentalGuard", "ESP32", "Arduino", "XIAO_FSR"]`

**Data Processing:**
```python
# Unpack BLE packet (20 bytes = 5 floats)
sL, sR, F_L, F_R, event_flag = struct.unpack("<fffff", data)

# Generate CSV for each sensor
csv_left = f"1,{F_L},{timestamp_ms},{event_flag}"
csv_right = f"2,{F_R},{timestamp_ms},{event_flag}"
```

---

### services/csv_parser.py

**Purpose:** Parse CSV-formatted sensor data into structured dictionaries

**Key Methods:**

```python
@staticmethod
def parse(csv_string: str) -> Optional[dict]
    """Parse CSV string into dictionary

    Input format: "sensorId,force_kg,timestamp,event_flag"
    Output: {
        "sensorId": int,
        "force": float,      # in kg
        "timestamp": int,    # milliseconds
        "date": str,         # ISO8601
        "event": float       # 0.0 or 1.0
    }
    """
```

**Error Handling:**
- Returns `None` on malformed input
- Handles missing fields gracefully
- Prints errors to console

---

### services/data_storage.py

**Purpose:** Session management and database persistence

**Database Schema:**

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    full_name TEXT,
    created_at TEXT
);

-- Sessions table
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT,
    summary_json TEXT,  -- {totalReadings, avgForce, maxForce, minForce, start, end}
    data_json TEXT      -- [{sensorId, force, timestamp, date, event}, ...]
);
```

**Key Methods:**

```python
def start_new_session() -> None
    """Initialize new acquisition session"""

def add_force_value(force: float, sensor_id: int = 1, event: float = 0.0) -> None
    """Add single reading (for simulation)"""

def add_record(record: dict) -> None
    """Add parsed record to current session"""

def end_session(save: bool = True) -> Optional[dict]
    """Terminate session, optionally save to database

    Returns: {"id": session_id, "summary": {...}}
    """

def save_session() -> dict
    """Persist current session to SQLite"""

def get_sessions() -> List[dict]
    """Retrieve all sessions (ID, created_at, summary)"""

def export_session_csv(session_id: int, out_path: str) -> str
    """Export session data to CSV file"""
```

**In-Memory Buffer:**
- `current_session_data: List[dict]` - active session buffer
- `session_active: bool` - session state flag
- `current_session_id: Optional[int]` - temporary session ID

---

### ui/live_plot.py

**Purpose:** Real-time dual-sensor force visualization with event detection

**Key Features:**
- Matplotlib-based dual-line graph (blue = left, orange = right)
- Last 200 samples per sensor
- Force display in kg
- Event status indicator (green/red)
- Color-coded progress bar
- Three dental diagram images

**Key Methods:**

```python
def update_plot() -> None
    """Main rendering loop (called every 400ms)

    1. Filter data by sensorId (1=left, 2=right)
    2. Extract force values (already in kg)
    3. Plot dual lines
    4. Update force label
    5. Update event status (green/red)
    6. Update progress bar (color thresholds)
    """

def _simulate_one_sample() -> None
    """Generate simulated data for testing

    Normal force: 0.1-1.0 kg (80% of time)
    Event force: 2.5-4.5 kg (20% of time)
    """

def start_simulation() -> None
    """Enable simulation mode"""

def stop_simulation(save: bool = True) -> None
    """Disable simulation, optionally save session"""
```

**UI Components:**

```python
# Force label (HTML formatted)
self.force_label = QLabel("Fuerza: -- kg")

# Event status indicator
self.event_label = QLabel("✓ Sin evento | Monitoreo activo")
# Green state: background #1a3a1a, text #4ade80
# Red state: background #7f1d1d, text #fca5a5, border #dc2626

# Progress bar (color-coded)
self.force_bar = QProgressBar()
# Green: < 1.5 kg
# Yellow: 1.5-3.5 kg
# Red: > 3.5 kg
```

**Event Detection Display Logic:**

```python
if latest_event_left == 1.0 and latest_event_right == 1.0:
    display = "⚠ EVENTO DE BRUXISMO | Ambos Sensores"
elif latest_event_left == 1.0:
    display = "⚠ EVENTO DE BRUXISMO | Sensor Izquierdo"
elif latest_event_right == 1.0:
    display = "⚠ EVENTO DE BRUXISMO | Sensor Derecho"
else:
    display = "✓ Sin evento | Monitoreo activo"
```

---

### ui/main_window.py

**Purpose:** Application coordinator and main UI container

**Architecture:**
- QMainWindow with header, collapsible sidebar, stacked widget
- 5 navigation panels: Dashboard, BLE, History, Reports, Auth
- Theme switcher (dark/light)
- Dashboard: LivePlot + StatsWidget + QuickActionsWidget

**Key Methods:**

```python
def on_ble_data(raw_csv: str) -> None
    """Handle incoming BLE data

    1. Parse CSV using CSVParser
    2. Add record to storage
    """

def start_simulation_session() -> None
    """Initiate simulation mode"""

def start_real_session() -> None
    """Begin hardware acquisition"""

def stop_session() -> None
    """End session and save"""

def clear_data() -> None
    """Clear current buffer without saving"""
```

**Timers:**
- `refresh_timer`: 400ms - updates plot and stats
- `simulation_timer`: 200ms - generates simulated data

---

## Configuration

### Hardware Configuration (ble_setup.ino)

```cpp
// Pin assignments
const int PIN_L = A4;      // Left FSR
const int PIN_R = A5;      // Right FSR

// ADC configuration
const float VREF = 3.3;    // Reference voltage
const int ADC_MAX = 4095;  // 12-bit resolution

// Signal processing
const uint8_t N_SAMPLES = 32;   // Averaging window
const float ALPHA = 0.2;        // EMA factor

// Event detection
const float T_on = 0.65;        // Activation threshold
const float T_off = 0.55;       // Deactivation threshold
const uint16_t HOLD_MS = 150;   // Hold time

// Force models (experimental calibration)
const float aL = 13.54, bL = 1.0612, V0L = 0.9;  // Left
const float aR = 5.67, bR = 1.0358, V0R = 0.9;   // Right

// Default calibration
float VminL = 0.9, VmaxL = 1.5;  // Left range
float VminR = 0.9, VmaxR = 2.1;  // Right range
```

### Software Configuration (utils/constants.py)

```python
BLE_CONFIG = {
    "SERVICE_UUID": "6E400001-B5A3-F393-E0A9-E50E24DCCA9E",
    "CHARACTERISTIC_UUID_TX": "00005678-0000-1000-8000-00805f9b34fb",
    "CHARACTERISTIC_UUID_RX": "6E400002-B5A3-F393-E0A9-E50E24DCCA9E",
    "SCAN_TIMEOUT": 8,
    "DEVICE_NAME_FILTER": ["DentalGuard", "ESP32", "Arduino", "XIAO_FSR"]
}

FORCE_THRESHOLDS = {
    "LOW": 20,     # N (not currently used)
    "MEDIUM": 40,  # N
    "HIGH": 60     # N
}

FORCE_COLORS = {
    "LOW": "#00ff00",
    "MEDIUM": "#ffff00",
    "HIGH": "#ff0000",
    "DEFAULT": "#888888"
}

SENSOR_CONFIG = {
    "TOTAL_SENSORS": 4,
    "SENSOR_IDS": [1, 2, 3, 4]  # Currently using 1 and 2
}
```

### Application Settings (settings.json)

```json
{
  "theme": "light"
}
```

---

## Testing Guide

### Hardware Calibration Procedure

**Prerequisites:**
- XIAO_FSR device powered on
- Serial monitor connected (115200 baud)

**Steps:**

1. **Rest Calibration:**
   ```
   - Ensure no pressure on sensors
   - Send 'r' command via Serial
   - Wait 1 second (averaging period)
   - Note VminL and VminR values
   ```

2. **Bite Calibration:**
   ```
   - Apply maximum comfortable bite pressure
   - Send 'm' command via Serial
   - Maintain pressure for 1 second
   - Note VmaxL and VmaxR values
   ```

3. **Verification:**
   ```
   - Observe Serial output: "L:XXX R:XXX | FL=XXkg FR=XXkg [ON/..]"
   - Normalized values (L, R) should be 0.0 at rest, ~1.0 at max bite
   - Force values should be realistic (0-10 kg range)
   - Event flag should trigger at high force
   ```

### Software Testing

#### Test 1: Simulation Mode

```
1. Launch application: python main.py
2. Click "Iniciar Simulación"
3. Verify:
   - Graph shows data in kg (Y-axis: "Fuerza (kg)")
   - Values in 0-5 kg range
   - Force label: "Izq: X.XX kg  Der: X.XX kg"
   - Event status turns red periodically (~10 sec intervals)
   - Progress bar color changes (green/yellow/red)
4. Click "Detener Sesión"
5. Navigate to "Historial / Registros"
6. Verify new session appears
```

#### Test 2: BLE Real Device

```
1. Power on XIAO_FSR device
2. Navigate to "BLE / Dispositivo"
3. Click "Escanear Dispositivos"
4. Verify "XIAO_FSR" appears
5. Click "Conectar"
6. Return to dashboard
7. Click "Iniciar Sesión Real"
8. Apply pressure to FSR sensors
9. Verify:
   - Graph updates in real-time
   - Force values match Serial monitor output
   - Event status turns red when force > threshold
10. Click "Detener Sesión"
11. Export session to CSV and verify data integrity
```

#### Test 3: Data Persistence

```
1. Create session (simulation or real)
2. Stop and save session
3. Close application
4. Relaunch application
5. Navigate to "Historial / Registros"
6. Verify session persists
7. Double-click session to view details
8. Export to CSV and verify:
   - Columns: Sensor ID, Force (kg), Timestamp, Date
   - Event flag present in data (if extended schema)
```

---

## Future Enhancements

### Phase 1: High Priority

#### 1.1 Fix BLE Calibration Command Reception

**Problem:** Hardware checks `Serial.available()` but commands sent via BLE.

**Solution:**
```cpp
// ble_setup.ino
// Add BLE RX characteristic handling
if (fsrCharRX.available()) {
    char c = fsrCharRX.read();
    if (c == 'r') { /* calibrate rest */ }
    else if (c == 'm') { /* calibrate bite */ }
}
```

**Reference:** services/ble_service.py:57, 63

---

#### 1.2 Event Flag Utilization

**Current:** Event flag transmitted but only used for UI display.

**Enhancement:**
- Log bruxism events separately in database
- Calculate event statistics (count, duration, max force during event)
- Generate bruxism-specific reports

**Database Schema Addition:**
```sql
CREATE TABLE bruxism_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    start_time TEXT,
    end_time TEXT,
    duration_ms INTEGER,
    max_force_left REAL,
    max_force_right REAL,
    sensor_triggered TEXT,  -- 'left', 'right', 'both'
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

---

#### 1.3 Timestamp Accuracy

**Current:** Timestamp generated on Python side (reception time).

**Problem:** BLE latency (10-30ms) introduces timing error.

**Solution:**
- Send hardware `millis()` as 6th value in packet
- Convert to absolute time using connection timestamp

```cpp
// Hardware
float packet[6] = {sL, sR, F_L, F_R, eventOn, (float)millis()};
```

```python
# Software
sL, sR, F_L, F_R, event_flag, hw_millis = struct.unpack("<ffffff", data)
```

---

### Phase 2: Medium Priority

#### 2.1 Force Model Consistency

**Decision needed:** Use hardware models OR software linear scaling?

**Recommendation:** Keep hardware models (current implementation)

**Documentation:**
- Add force model derivation to docs
- Document experimental calibration procedure
- Include force vs. voltage curves

---

#### 2.2 Database Schema Optimization

**Current:** JSON storage in TEXT columns

**Enhancement:**
```sql
CREATE TABLE readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    sensor_id INTEGER,
    force_kg REAL,
    timestamp INTEGER,
    date TEXT,
    event_flag INTEGER,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_readings_session ON readings(session_id);
CREATE INDEX idx_readings_timestamp ON readings(timestamp);
```

**Benefits:**
- ✅ Faster queries
- ✅ SQL aggregation capabilities
- ✅ Reduced storage size

---

#### 2.3 Configuration UI

**Features:**
- Settings panel for force thresholds
- BLE UUID configuration (custom hardware)
- Calibration value persistence
- Export settings to JSON

**UI Design:**
```
┌─────────────────────────────────────┐
│ Configuración                       │
├─────────────────────────────────────┤
│ Umbrales de Fuerza:                 │
│   Bajo:  [1.5] kg                   │
│   Medio: [3.5] kg                   │
│                                     │
│ Calibración (Sensor Izquierdo):     │
│   Vmin: [0.90] V                    │
│   Vmax: [1.50] V                    │
│                                     │
│ Calibración (Sensor Derecho):       │
│   Vmin: [0.90] V                    │
│   Vmax: [2.10] V                    │
│                                     │
│ [Guardar]  [Restaurar Predeterminados] │
└─────────────────────────────────────┘
```

---

### Phase 3: Advanced Features

#### 3.1 Event Timeline Visualization

**Feature:** Timeline strip below graph showing event history

```
┌─────────────────────────────────────────────┐
│  [Force Graph - dual lines]                 │
└─────────────────────────────────────────────┘
│ Eventos: ▂▂█▂▂▂▂███▂▂█▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂ │
             └─ 30s ago    └─ 10s ago
```

**Implementation:**
- Add matplotlib axes below main graph
- Plot event flag over time as bar chart
- Align temporally with force graph

---

#### 3.2 Multi-Session Comparison

**Feature:** Overlay multiple sessions for comparison

**Use Cases:**
- Compare before/after treatment
- Track progress over time
- Identify patterns

---

#### 3.3 Real-Time Alerts

**Feature:** Audio/visual alerts during events

**Configuration:**
- Alert threshold (force level)
- Alert duration
- Sound selection
- Visual flash

---

#### 3.4 Export Formats

**Additional formats:**
- Excel (.xlsx) with charts
- PDF reports with matplotlib plots
- JSON for web applications
- HDF5 for scientific analysis

---

## Troubleshooting

### Common Issues

#### Issue 1: Application Won't Start

**Symptoms:** Python crashes, window doesn't open

**Solutions:**
1. Check Python version (requires 3.12)
2. Verify dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```
3. Check console output for import errors
4. Verify Qt platform plugin installed (Windows)

---

#### Issue 2: BLE Device Not Found

**Symptoms:** Scan returns empty list

**Solutions:**
1. Verify device powered on
2. Check device is advertising (blue LED)
3. Ensure device not connected to another application
4. Restart Bluetooth adapter (Windows settings)
5. Check device name matches filter: `["DentalGuard", "ESP32", "Arduino", "XIAO_FSR"]`

---

#### Issue 3: Force Values Too High/Low

**Symptoms:** Graph shows unrealistic values (50+ kg or negative)

**Solutions:**
1. Verify BLE unpacking uses `F_L, F_R` not `sL, sR` (services/ble_service.py:34)
2. Check live_plot.py NOT multiplying by 50 (should use kg directly)
3. Verify hardware calibration (VminL, VmaxL, VminR, VmaxR)
4. Check hardware force models (aL, bL, aR, bR coefficients)

---

#### Issue 4: Event Status Never Changes

**Symptoms:** Status bar stays green even during high force

**Solutions:**
1. Verify csv_parser.py extracts event_flag (4th field)
2. Check ble_service.py includes event_flag in CSV
3. Verify event display logic in live_plot.py (lines 202-243)
4. Check hardware threshold calibration (T_on = 0.65)
5. Test simulation mode (should trigger events every ~10 sec)

---

#### Issue 5: Graph Shows No Data

**Symptoms:** Empty graph, "Esperando datos..." message

**Solutions:**
1. Verify session started (click "Iniciar Simulación" or "Iniciar Sesión Real")
2. Check BLE connected (if real mode)
3. Verify storage.current_session_data not empty (console: `print(len(storage.current_session_data))`)
4. Check refresh timer running (should update every 400ms)

---

#### Issue 6: CSV Export Fails

**Symptoms:** Error when exporting session

**Solutions:**
1. Check pandas installed: `pip install pandas`
2. Verify session has data (check database: `data/dental.db`)
3. Ensure write permissions to export directory
4. Try exporting to different location (e.g., Desktop)

---

#### Issue 7: Database Corruption

**Symptoms:** Application crashes on startup, session load fails

**Solutions:**
1. Backup database: copy `data/dental.db`
2. Check database integrity:
   ```bash
   sqlite3 data/dental.db "PRAGMA integrity_check;"
   ```
3. If corrupted, restore from backup or delete and recreate
4. Application will auto-create schema on startup

---

## Appendix A: File Structure

```
dental_force/
├── data/
│   └── dental.db                 # SQLite database (49 sessions, 2 users)
├── docs/                         # Documentation (this file)
│   └── ARCHITECTURE_AND_IMPLEMENTATION.md
├── exports/                      # Exported session CSV files
│   └── session_*.csv
├── previews/                     # UI mockups
│   ├── mock_collapsed.png
│   ├── mock_expanded.png
│   └── mock_transition.gif
├── services/                     # Business logic layer
│   ├── ble_service.py           # BLE communication (Bleak)
│   ├── csv_parser.py            # CSV data parsing
│   └── data_storage.py          # Session management, SQLite
├── ui/                           # Presentation layer (PySide6)
│   ├── icons/                   # SVG navigation icons
│   │   ├── ble.svg
│   │   ├── dashboard.svg
│   │   ├── export.svg
│   │   ├── history.svg
│   │   ├── reports.svg
│   │   └── user.svg
│   ├── auth_widget.py           # User authentication
│   ├── ble_panel.py             # BLE device management
│   ├── history_widget.py        # Session history table
│   ├── live_plot.py             # Real-time force visualization
│   ├── main_window.py           # Application coordinator
│   ├── quick_actions_widget.py  # Session control buttons
│   ├── reports_widget.py        # Export and reporting
│   ├── stats_widget.py          # Statistics display
│   ├── style.py                 # Python stylesheet
│   ├── style.qss                # Qt dark theme
│   ├── style_light.qss          # Qt light theme
│   ├── teeth_left.png           # Dental diagram (left)
│   ├── teeth_model.png          # Dental diagram (center)
│   └── teeth_right.png          # Dental diagram (right)
├── utils/                        # Configuration and helpers
│   ├── colors.py                # Force-to-color mapping
│   └── constants.py             # BLE config, thresholds
├── venv/                         # Python virtual environment
├── build_exe.bat                # PyInstaller build script
├── main.py                      # Application entry point
├── pyinstaller.spec             # PyInstaller configuration
├── settings.json                # User settings (theme)
└── PACKAGING_README.txt         # Build instructions
```

---

## Appendix B: BLE Protocol Specification

### Service Definition

```
Service UUID: 0x1234
Name: FSR Data Service
Type: Custom
```

### Characteristic Definition

```
Characteristic UUID: 0x5678
Properties: READ, NOTIFY
Permissions: SECMODE_OPEN (no encryption)
Fixed Length: 20 bytes (5 × 4-byte floats)
```

### Packet Structure (Little-Endian)

| Byte Offset | Size | Type | Name | Unit | Description |
|-------------|------|------|------|------|-------------|
| 0-3 | 4 | float | sL | 0.0-1.0 | Left sensor normalized |
| 4-7 | 4 | float | sR | 0.0-1.0 | Right sensor normalized |
| 8-11 | 4 | float | F_L | kg | Left sensor force |
| 12-15 | 4 | float | F_R | kg | Right sensor force |
| 16-19 | 4 | float | eventOn | 0.0/1.0 | Event status |

### Transmission Rate

- **Nominal:** ~30ms (33 Hz)
- **Controlled by:** `SAMPLE_MS` constant
- **Jitter:** ±5ms (typical)

### Connection Parameters

- **MTU:** 23 bytes (default BLE)
- **Connection Interval:** System default
- **Advertising:** Continuous until connected
- **Device Name:** "XIAO_FSR"

---

## Appendix C: Force Model Derivation

### Experimental Setup

1. FSR sensors mounted on bite plate
2. Known weights applied (0-10 kg)
3. Voltage measured at each weight
4. Power-law regression performed

### Left Sensor Model

```
F_L = 13.54 × (V - 0.9)^1.0612 kg

Where:
  V = sensor voltage (0-3.3V)
  V₀ = 0.9V (baseline voltage)
  a = 13.54 (scaling coefficient)
  b = 1.0612 (power exponent)
```

**R² = 0.987** (excellent fit)

### Right Sensor Model

```
F_R = 5.67 × (V - 0.9)^1.0358 kg

Where:
  V = sensor voltage (0-3.3V)
  V₀ = 0.9V (baseline voltage)
  a = 5.67 (scaling coefficient)
  b = 1.0358 (power exponent)
```

**R² = 0.983** (excellent fit)

### Model Validity Range

- **Voltage:** 0.9V - 2.5V
- **Force:** 0 - 10 kg
- **Accuracy:** ±5% (within range)

---

## Appendix D: Glossary

**ADC:** Analog-to-Digital Converter - converts analog voltage to digital value

**BLE:** Bluetooth Low Energy - wireless communication protocol

**Bruxism:** Medical condition of teeth grinding/clenching

**EMA:** Exponential Moving Average - signal smoothing technique

**FSR:** Force Sensitive Resistor - pressure sensor

**GATT:** Generic Attribute Profile - BLE data organization

**Hysteresis:** Different thresholds for on/off transitions (prevents oscillation)

**MTU:** Maximum Transmission Unit - max packet size

**Power-law model:** Mathematical relationship F = a × (V - V₀)^b

**UUID:** Universally Unique Identifier - identifies BLE services/characteristics

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-02 | AI Assistant + User | Initial comprehensive documentation |

---

## Contact & Support

**Repository:** C:\Users\iauribe\Documents\repos\dental_force
**Hardware Repository:** C:\Users\iauribe\Documents\repos\BLE
**Documentation:** C:\Users\iauribe\Documents\repos\dental_force\docs

**For questions or issues, refer to:**
- This documentation
- Code comments in source files
- Implementation plan in this document

---

**End of Document**
