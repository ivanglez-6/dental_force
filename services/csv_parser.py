# services/csv_parser.py
import datetime

class CSVParser:
    def __init__(self, storage=None):
        self.storage = storage  # opcional, puede ser None

    @staticmethod
    def parse(csv_string):
        """
        Espera formato: sensorId,force_kg,timestamp,event_flag
        timestamp preferentemente en ms (como millis).
        Retorna dict o None.
        """
        try:
            s = csv_string.strip()
            if not s:
                return None
            parts = s.split(',')
            if len(parts) < 4:
                return None
            sensor_id = int(parts[0])
            force_kg = float(parts[1])
            timestamp = int(parts[2])
            event_flag = float(parts[3])
            dt = datetime.datetime.fromtimestamp(timestamp/1000.0)
            return {
                "sensorId": sensor_id,
                "force": force_kg,
                "timestamp": timestamp,
                "date": dt.isoformat(),
                "event": event_flag
            }
        except Exception as e:
            print("CSVParser error:", e)
            return None
