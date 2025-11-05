# Quick Reference Guide

**Dental Force Monitoring System - Developer Cheat Sheet**

---

## 🚀 Quick Start

```bash
# Start application
cd C:\Users\iauribe\Documents\repos\dental_force
python main.py

# Test simulation mode
# 1. Launch app
# 2. Click "Iniciar Simulación"
# 3. Watch graph for kg values and event indicators
```

---

## 📦 BLE Packet Structure

**Hardware sends (20 bytes):**
```cpp
float packet[5] = {sL, sR, F_L, F_R, eventOn};
```

**Software receives:**
```python
sL, sR, F_L, F_R, event_flag = struct.unpack("<fffff", data)
```

**CSV format (what we use):**
```
sensorId,force_kg,timestamp,event_flag
1,2.45,1698765432123,0.0
2,1.87,1698765432123,0.0
```

---

## 🔑 Key Files

| File | Purpose | Critical Functions |
|------|---------|-------------------|
| `services/ble_service.py` | BLE comm | `start_notify()`, `_notification_handler()` |
| `services/csv_parser.py` | Parse CSV | `parse()` |
| `services/data_storage.py` | DB + sessions | `add_record()`, `save_session()` |
| `ui/live_plot.py` | Visualization | `update_plot()`, `_simulate_one_sample()` |
| `ui/main_window.py` | Main app | `on_ble_data()`, `start_real_session()` |
| `utils/constants.py` | Config | BLE UUIDs, thresholds |

---

## 🎯 Critical Code References

### BLE Packet Unpacking
**File:** `services/ble_service.py:34`
```python
sL, sR, F_L, F_R, event_flag = struct.unpack("<fffff", data)
csv_left = f"1,{F_L},{timestamp_ms},{event_flag}"  # Use F_L (kg), not sL!
```

### CSV Parsing
**File:** `services/csv_parser.py:22-32`
```python
sensor_id = int(parts[0])
force_kg = float(parts[1])
timestamp = int(parts[2])
event_flag = float(parts[3])
return {"sensorId": sensor_id, "force": force_kg, "timestamp": timestamp,
        "date": dt.isoformat(), "event": event_flag}
```

### Data Display
**File:** `ui/live_plot.py:128-129`
```python
left_forces_kg = [r['force'] for r in left_data]   # NO conversion!
right_forces_kg = [r['force'] for r in right_data] # Already in kg!
```

### Event Detection
**File:** `ui/live_plot.py:202-243`
```python
latest_event_left = left_data[-1].get('event', 0.0) if left_data else 0.0
if latest_event_left == 1.0:
    display = "⚠ EVENTO DE BRUXISMO | Sensor Izquierdo"
```

---

## ⚙️ Configuration

### BLE UUIDs
```python
SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
CHARACTERISTIC_UUID_TX = "00005678-0000-1000-8000-00805f9b34fb"
DEVICE_NAME_FILTER = ["DentalGuard", "ESP32", "Arduino", "XIAO_FSR"]
```

### Force Thresholds (in kg)
```python
# Progress bar colors
LOW = 1.5 kg    # Green
MEDIUM = 3.5 kg # Yellow
HIGH = 5.0 kg   # Red (max scale)
```

### Hardware Calibration
```cpp
// Default values (can be calibrated with 'r' and 'm' commands)
VminL = 0.9V, VmaxL = 1.5V  // Left sensor
VminR = 0.9V, VmaxR = 2.1V  // Right sensor

// Force models (experimental calibration)
F_L = 13.54 × (V - 0.9)^1.0612 kg
F_R = 5.67 × (V - 0.9)^1.0358 kg
```

---

## 🗄️ Database Schema

### Sessions Table
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT,
    summary_json TEXT,  -- {totalReadings, avgForce, maxForce, minForce, start, end}
    data_json TEXT      -- [{sensorId, force, timestamp, date, event}, ...]
);
```

### Data Record Format
```python
{
    "sensorId": 1 or 2,
    "force": float,      # in kg
    "timestamp": int,    # milliseconds
    "date": str,         # ISO8601
    "event": float       # 0.0 or 1.0
}
```

---

## 🧪 Testing Checklist

### ✅ Simulation Mode
- [ ] Graph shows kg values (0-5 range)
- [ ] Y-axis says "Fuerza (kg)"
- [ ] Force label: "Izq: X.XX kg  Der: X.XX kg"
- [ ] Event status turns red every ~10 seconds
- [ ] Progress bar changes color
- [ ] Session saves successfully

### ✅ BLE Mode
- [ ] Device found in scan
- [ ] Connection successful
- [ ] Real-time graph updates
- [ ] Force values realistic (0-10 kg)
- [ ] Event triggers on high force
- [ ] Export to CSV works

---

## 🔧 Common Tasks

### Add New Sensor
1. Update `SENSOR_CONFIG` in `utils/constants.py`
2. Modify BLE packet structure in hardware
3. Update `ble_service.py` unpacking logic
4. Add filtering in `live_plot.py`

### Change Force Thresholds
1. Edit `live_plot.py:184-189`
2. Update comments to reflect new values
3. Update documentation

### Modify BLE Protocol
1. Change hardware packet in `ble_setup.ino:225`
2. Update unpacking in `ble_service.py:34`
3. Modify CSV generation format
4. Update `csv_parser.py` to match
5. **Update documentation!**

---

## 🐛 Debugging

### Enable Verbose Logging
```python
# In ble_service.py, add:
print(f"BLE RX: {data.hex()}")
print(f"Unpacked: sL={sL}, sR={sR}, F_L={F_L}, F_R={F_R}, event={event_flag}")

# In live_plot.py, add:
print(f"Data points: {len(left_data)} left, {len(right_data)} right")
print(f"Force range: {min(all_forces):.2f} - {max(all_forces):.2f} kg")
```

### Check Database
```bash
sqlite3 data/dental.db
> SELECT COUNT(*) FROM sessions;
> SELECT id, created_at FROM sessions ORDER BY id DESC LIMIT 5;
> .schema sessions
> .quit
```

### Verify BLE Connection
```python
# In BLEPanel, check console for:
"BLE: Device found: XIAO_FSR"
"BLE: Connected successfully"
"BLE: Notifications started"
```

---

## 📊 Data Flow Summary

```
Hardware → BLE (20 bytes) → ble_service.py → CSV string →
csv_parser.py → dict → data_storage.py → current_session_data[] →
live_plot.py (400ms timer) → matplotlib graph + event status
```

---

## 🚨 Red Flags

**❌ NEVER:**
- Convert kg values to N in Python (already in kg!)
- Use normalized values (sL, sR) for display (use F_L, F_R)
- Ignore event_flag from hardware
- Skip database event field
- Hardcode calibration values in Python

**✅ ALWAYS:**
- Use hardware-calculated kg values
- Include event_flag in data pipeline
- Validate BLE packet structure matches hardware
- Update documentation when changing protocol
- Test both simulation and real modes

---

## 📞 Help

**Something broken?**
1. Check [Troubleshooting](ARCHITECTURE_AND_IMPLEMENTATION.md#troubleshooting) section
2. Verify BLE packet format matches between hardware and software
3. Check console output for errors
4. Test in simulation mode to isolate hardware vs. software issues

**Want to understand architecture?**
→ Read [ARCHITECTURE_AND_IMPLEMENTATION.md](ARCHITECTURE_AND_IMPLEMENTATION.md)

**Want to modify system?**
→ Read Section 5 (Implementation History) to understand why things are the way they are

---

**Last Updated:** 2025-11-02
