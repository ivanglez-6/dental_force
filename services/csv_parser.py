# services/csv_parser.py
import datetime

class CSVParser:
    def __init__(self, storage=None):
        self.storage = storage  # opcional, puede ser None

    @staticmethod
    def parse(csv_string):
        """
        Espera formato: sensorId,force,timestamp
        timestamp preferentemente en ms (como millis).
        Retorna dict o None.
        """
        try:
            s = csv_string.strip()
            if not s:
                return None
            parts = s.split(',')
            if len(parts) < 3:
                return None
            sensor_id = int(parts[0])
            force = float(parts[1])
            timestamp = int(parts[2])
            dt = datetime.datetime.fromtimestamp(timestamp/1000.0)
            return {
                "sensorId": sensor_id,
                "force": force,
                "timestamp": timestamp,
                "date": dt.isoformat()
            }
        except Exception as e:
            print("CSVParser error:", e)
            return None
