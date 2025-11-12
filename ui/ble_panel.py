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
            self.status.emit(f"Conectando a {self.device.name}...")
            await ble.connect(self.device)
            self.status.emit(f"Conectado a {self.device.name}")
            def cb(text):
                self.data_received.emit(text)
            await ble.start_notify(cb)
            # loop hasta que thread sea detenido
            while not self._stopped:
                await asyncio.sleep(0.1)
            await ble.stop()
            self.status.emit("Desconectado")
        except Exception as e:
            self.status.emit("Error: " + str(e))

    def stop(self):
        self._stopped = True
        self.quit()


class BLEPanel(QFrame):
    data_callback = None  # callback externo (raw CSV string)

    def __init__(self, storage):
        super().__init__()
        self.setObjectName("card")
        self.storage = storage
        self.layout = QVBoxLayout()

        self.scan_btn = QPushButton("🔍 Escanear BLE")
        self.scan_btn.clicked.connect(self.scan)

        self.device_list = QListWidget()

        self.connect_btn = QPushButton("🔗 Conectar")
        self.connect_btn.clicked.connect(self.connect_selected)

        self.status_label = QLabel("Estado: Desconectado")

        self.layout.addWidget(self.scan_btn)
        self.layout.addWidget(self.device_list)
        self.layout.addWidget(self.connect_btn)
        self.layout.addWidget(self.status_label)
        self.setLayout(self.layout)

        self.scan_worker = None
        self.ble_worker = None
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
            name = d.name or "Desconocido"
            self.device_list.addItem(f"{name} | {d.address}")

    def on_error(self, msg):
        self.scan_btn.setEnabled(True)
        QMessageBox.warning(self, "Error de escaneo", msg)

    def connect_selected(self):
        idx = self.device_list.currentRow()
        if idx < 0 or idx >= len(self.devices):
            QMessageBox.information(self, "Seleccionar dispositivo", "Por favor seleccione un dispositivo primero")
            return
        device = self.devices[idx]
        self.ble_worker = BLEWorker(device)
        self.ble_worker.data_received.connect(self.on_data)
        self.ble_worker.status.connect(self.on_status)
        self.ble_worker.start()

    def on_data(self, raw):
        # enviar a handler externo si existe
        try:
            if self.data_callback:
                self.data_callback(raw)
        except Exception as e:
            print("BLEPanel on_data error:", e)

    def on_status(self, text):
        self.status_label.setText(f"Estado: {text}")

    def disconnect(self):
        if self.ble_worker:
            self.ble_worker.stop()
            self.ble_worker = None
