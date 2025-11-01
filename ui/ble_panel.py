# ui/ble_panel.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QLabel, QMessageBox, QFrame
from PySide6.QtCore import Qt, QThread, Signal
import asyncio
from services.ble_service import BLEService

class BLEScanWorker(QThread):
    devices_found = Signal(list)
    error = Signal(str)

    def __init__(self, timeout=8):
        super().__init__()
        self.timeout = timeout
        self._stopped = False

    def run(self):
        asyncio.run(self._scan())

    async def _scan(self):
        try:
            ble = BLEService()
            devices = await ble.scan(timeout=self.timeout)
            self.devices_found.emit(devices)
        except Exception as e:
            self.error.emit(str(e))


class BLEWorker(QThread):
    data_received = Signal(str)
    status = Signal(str)

    def __init__(self, device):
        super().__init__()
        self.device = device
        self._stopped = False
        self.ble_service = None

    def run(self):
        # corremos conexión en asyncio dentro del thread
        asyncio.run(self._run())

    async def _run(self):
        try:
            ble = BLEService()
            self.ble_service = ble  # Store reference for calibration access
            self.status.emit(f"Connecting to {self.device.name}...")
            await ble.connect(self.device)
            self.status.emit(f"Connected to {self.device.name}")
            def cb(text):
                self.data_received.emit(text)
            await ble.start_notify(cb)
            # loop hasta que thread sea detenido
            while not self._stopped:
                await asyncio.sleep(0.1)
            await ble.stop()
            self.status.emit("Disconnected")
        except Exception as e:
            self.status.emit("Error: " + str(e))

    def stop(self):
        self._stopped = True
        self.quit()


class BLECalibrationWorker(QThread):
    success = Signal(str)
    error = Signal(str)

    def __init__(self, ble_service, method_name):
        super().__init__()
        self.ble_service = ble_service
        self.method_name = method_name

    def run(self):
        asyncio.run(self._calibrate())

    async def _calibrate(self):
        try:
            if self.method_name == "rest":
                await self.ble_service.calibrate_rest()
                self.success.emit("Rest calibration sent successfully")
            elif self.method_name == "bite":
                await self.ble_service.calibrate_bite()
                self.success.emit("Bite calibration sent successfully")
        except Exception as e:
            self.error.emit(f"Calibration error: {str(e)}")


class BLEPanel(QFrame):
    data_callback = None  # callback externo (raw CSV string)

    def __init__(self, storage):
        super().__init__()
        self.setObjectName("card")
        self.storage = storage
        self.layout = QVBoxLayout()

        self.scan_btn = QPushButton("🔍 Scan BLE")
        self.scan_btn.clicked.connect(self.scan)

        self.device_list = QListWidget()

        self.connect_btn = QPushButton("🔗 Connect")
        self.connect_btn.clicked.connect(self.connect_selected)

        # Calibration buttons
        self.calibrate_rest_btn = QPushButton("🔧 Calibrate Rest")
        self.calibrate_rest_btn.setObjectName("calibrateRestBtn")
        self.calibrate_rest_btn.setEnabled(False)
        self.calibrate_rest_btn.clicked.connect(self.calibrate_rest_clicked)

        self.calibrate_bite_btn = QPushButton("🔧 Calibrate Bite")
        self.calibrate_bite_btn.setObjectName("calibrateBiteBtn")
        self.calibrate_bite_btn.setEnabled(False)
        self.calibrate_bite_btn.clicked.connect(self.calibrate_bite_clicked)

        self.status_label = QLabel("Status: Disconnected")

        self.layout.addWidget(self.scan_btn)
        self.layout.addWidget(self.device_list)
        self.layout.addWidget(self.connect_btn)
        self.layout.addWidget(self.calibrate_rest_btn)
        self.layout.addWidget(self.calibrate_bite_btn)
        self.layout.addWidget(self.status_label)
        self.setLayout(self.layout)

        self.scan_worker = None
        self.ble_worker = None
        self.calibration_worker = None
        self.devices = []

    def scan(self):
        self.device_list.clear()
        self.scan_btn.setEnabled(False)
        self.scan_worker = BLEScanWorker()
        self.scan_worker.devices_found.connect(self.on_devices)
        self.scan_worker.error.connect(self.on_error)
        self.scan_worker.start()

    def on_devices(self, devices):
        self.scan_btn.setEnabled(True)
        self.devices = devices
        for d in devices:
            name = d.name or "Unknown"
            self.device_list.addItem(f"{name} | {d.address}")

    def on_error(self, msg):
        self.scan_btn.setEnabled(True)
        QMessageBox.warning(self, "Scan error", msg)

    def connect_selected(self):
        idx = self.device_list.currentRow()
        if idx < 0 or idx >= len(self.devices):
            QMessageBox.information(self, "Select device", "Please select a device first")
            return
        device = self.devices[idx]
        self.ble_worker = BLEWorker(device)
        self.ble_worker.data_received.connect(self.on_data)
        self.ble_worker.status.connect(self.on_status)
        self.ble_worker.start()

    def calibrate_rest_clicked(self):
        if self.ble_worker and self.ble_worker.ble_service:
            self.status_label.setText("Status: Sending rest calibration command...")
            self.calibration_worker = BLECalibrationWorker(self.ble_worker.ble_service, "rest")
            self.calibration_worker.success.connect(self.on_calibration_success)
            self.calibration_worker.error.connect(self.on_calibration_error)
            self.calibration_worker.start()

    def calibrate_bite_clicked(self):
        if self.ble_worker and self.ble_worker.ble_service:
            self.status_label.setText("Status: Sending bite calibration command...")
            self.calibration_worker = BLECalibrationWorker(self.ble_worker.ble_service, "bite")
            self.calibration_worker.success.connect(self.on_calibration_success)
            self.calibration_worker.error.connect(self.on_calibration_error)
            self.calibration_worker.start()

    def on_calibration_success(self, msg):
        self.status_label.setText(f"Status: {msg}")

    def on_calibration_error(self, msg):
        self.status_label.setText(f"Status: {msg}")

    def on_data(self, raw):
        # enviar a handler externo si existe
        try:
            if self.data_callback:
                self.data_callback(raw)
        except Exception as e:
            print("BLEPanel on_data error:", e)

    def on_status(self, text):
        self.status_label.setText(f"Status: {text}")
        # Enable/disable calibration buttons based on connection status
        if "Connected" in text and "Connecting" not in text:
            self.calibrate_rest_btn.setEnabled(True)
            self.calibrate_bite_btn.setEnabled(True)
        elif "Disconnected" in text or "Error" in text:
            self.calibrate_rest_btn.setEnabled(False)
            self.calibrate_bite_btn.setEnabled(False)

    def disconnect(self):
        if self.ble_worker:
            self.ble_worker.stop()
            self.ble_worker = None
