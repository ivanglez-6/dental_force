# services/data_storage.py
import sqlite3
import json
import os
import csv
from datetime import datetime
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "dental.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

class DataStorage:
    def __init__(self, db_path=DB_PATH):
        self.db_path = os.path.abspath(db_path)
        # backward-compatible in-memory buffer used by widgets
        # (kept in sync with session_active/current_session when appropriate)
        self.current_session_data = []
        self.current_session_id = None
        self.session_active = False
        self._ensure_db()

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=30)

    def _ensure_db(self):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    full_name TEXT,
                    created_at TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT,
                    summary_json TEXT,
                    data_json TEXT
                )
            """)
            conn.commit()

    # -------------------
    # Session lifecycle (real-time)
    # -------------------
    def start_new_session(self):
        """Inicia una nueva sesión temporal para adquisición.
        Resetea current_session_data y marca session_active = True
        """
        self.current_session_data = []
        self.session_active = True
        self.current_session_id = int(datetime.utcnow().timestamp())
        print(f"[DataStorage] Nueva sesión iniciada (temp id {self.current_session_id})")

    def add_force_value(self, force, sensor_id=1):
        """Agregar una lectura simple (usado por LivePlot / simulación)."""
        if not self.session_active:
            self.start_new_session()
        record = {
            "sensorId": sensor_id,
            "force": float(force),
            "timestamp": datetime.utcnow().timestamp(),
            "date": datetime.utcnow().isoformat()
        }
        self.current_session_data.append(record)

    # alias para compatibilidad con versiones previas
    def add_record(self, record):
        """Si te pasan un registro ya parseado (dict) lo añade."""
        # normalize expected keys if necessary
        if not isinstance(record, dict):
            return
        if "force" not in record and "value" in record:
            record["force"] = record.pop("value")
        if "date" not in record and "timestamp" in record:
            try:
                record["date"] = datetime.utcfromtimestamp(record["timestamp"]).isoformat()
            except Exception:
                record["date"] = datetime.utcnow().isoformat()
        self.current_session_data.append(record)
        # ensure session flag
        if not self.session_active:
            self.session_active = True
            self.current_session_id = int(datetime.utcnow().timestamp())

    def get_recent_records(self, count=50):
        """Retorna los últimos `count` registros (compatibilidad con LivePlot)."""
        return self.current_session_data[-count:]

    def clear_current_session(self):
        """Borra buffer actual (no borra la DB)."""
        self.current_session_data = []

    def end_session(self, save=True):
        """Termina la sesión actual; si save=True la persiste en DB."""
        if not self.session_active:
            return None
        if save:
            result = self.save_session()
            print(f"[DataStorage] Sesión guardada (ID DB: {result['id']})")
            self.session_active = False
            return result
        else:
            self.clear_current_session()
            self.session_active = False
            print("[DataStorage] Sesión descartada (no guardada).")
            return None

    # -------------------
    # Persistence (DB) and exports (tu código original adaptado)
    # -------------------
    def save_session(self):
        """Guarda current_session_data en la tabla sessions y resetea el buffer."""
        if not self.current_session_data:
            raise ValueError("No data to save")
        forces = [r["force"] for r in self.current_session_data]
        summary = {
            "totalReadings": len(forces),
            "avgForce": round(sum(forces)/len(forces), 2),
            "maxForce": round(max(forces), 2),
            "minForce": round(min(forces), 2),
            "start": self.current_session_data[0].get("date"),
            "end": self.current_session_data[-1].get("date")
        }
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO sessions (created_at, summary_json, data_json) VALUES (?, ?, ?)",
                      (datetime.utcnow().isoformat(), json.dumps(summary), json.dumps(self.current_session_data)))
            conn.commit()
            session_id = c.lastrowid
        self.clear_current_session()
        return {"id": session_id, "summary": summary}

    def get_sessions(self):
        """Devuelve lista de sesiones (ID, created_at, summary) para listados."""
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("SELECT id, created_at, summary_json FROM sessions ORDER BY id DESC")
            rows = c.fetchall()
            result = []
            for r in rows:
                result.append({
                    "id": r[0],
                    "created_at": r[1],
                    "summary": json.loads(r[2]) if r[2] else {}
                })
            return result

    # Backwards-compatible helpers used by some widgets in older examples:
    def get_all_sessions(self):
        """(compat) Devuelve sesiones en un formato amigable para HistoryWidget/ReportsWidget."""
        rows = self.get_sessions()
        out = []
        for r in rows:
            out.append({
                "id": r["id"],
                "fecha": r["created_at"],
                "tipo": "Real/Guardada",
                "duracion": r["summary"].get("totalReadings", 0),
                "datos": self.get_session_data(r["id"])
            })
        return out

    def get_session_by_id(self, session_id):
        """(compat) devuelve sesión completa por id en formato para HistoryWidget de ejemplo."""
        data = self.get_session_data(session_id)
        if data is None:
            return None
        # recuperar summary
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("SELECT id, created_at, summary_json FROM sessions WHERE id=?", (session_id,))
            row = c.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "fecha": row[1],
                "tipo": "Real/Guardada",
                "duracion": json.loads(row[2]).get("totalReadings", 0),
                "datos": data
            }

    def get_session_data(self, session_id):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("SELECT data_json FROM sessions WHERE id=?", (session_id,))
            row = c.fetchone()
            return json.loads(row[0]) if row and row[0] else []

    def delete_session(self, session_id):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM sessions WHERE id=?", (session_id,))
            conn.commit()

    def export_session_csv(self, session_id, out_path):
        data = self.get_session_data(session_id)
        if not data:
            raise ValueError("No data")
        df = pd.DataFrame(data)
        df = df.rename(columns={"sensorId": "Sensor ID", "force": "Force (N)", "timestamp": "Timestamp", "date": "Date"})
        df.to_csv(out_path, index=False)
        return out_path

    def export_current_csv(self, out_path):
        if not self.current_session_data:
            raise ValueError("No data to export")
        df = pd.DataFrame(self.current_session_data)
        df = df.rename(columns={"sensorId": "Sensor ID", "force": "Force (N)", "timestamp": "Timestamp", "date": "Date"})
        df.to_csv(out_path, index=False)
        return out_path

    def export_all_sessions_csv(self, out_path):
        sessions = self.get_sessions()
        rows = []
        for s in sessions:
            data = self.get_session_data(s["id"])
            for d in data:
                rows.append({
                    "session_id": s["id"],
                    "created_at": s["created_at"],
                    "sensorId": d.get("sensorId"),
                    "force": d.get("force"),
                    "timestamp": d.get("timestamp"),
                    "date": d.get("date")
                })
        df = pd.DataFrame(rows)
        df.to_csv(out_path, index=False)
        return out_path
