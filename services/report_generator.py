"""
Clinical Report Generator for Bruxism Analysis - Dual Sensor Version
Adapted from BLE_processing report_generation_system.py
"""

import pandas as pd
import numpy as np
from datetime import datetime


class BruxismReportGenerator:
    """
    Generates clinical reports based on bruxism data analysis for a single sensor.
    """

    def __init__(self, df, sensor_id=1):
        """
        Initialize with dataframe and sensor ID

        Args:
            df: DataFrame with columns: sensorId, force, timestamp, date, event
            sensor_id: 1 (left) or 2 (right)
        """
        self.sensor_id = sensor_id
        self.sensor_name = "IZQUIERDO" if sensor_id == 1 else "DERECHO"

        # Filter for this sensor
        self.df = df[df['sensorId'] == sensor_id].copy()

        # Convert timestamp if needed
        if not pd.api.types.is_datetime64_any_dtype(self.df['timestamp']):
            self.df['timestamp'] = pd.to_datetime(self.df['date'], errors='coerce', infer_datetime_format=True)

        # Get events
        self.events = self.df[self.df['event'] == 1.0].copy()

        # Calculate all clinical parameters
        self.calculate_parameters()

    def calculate_parameters(self):
        """Calculate all clinical parameters"""

        # Basic metrics
        self.total_events = len(self.events)

        if self.total_events == 0:
            # No events - set defaults
            self.mean_force = 0
            self.max_force = 0
            self.median_force = 0
            self.std_force = 0
            self.force_cv = 0
            self.low_force_pct = 0
            self.high_force_pct = 0
            self.rem_concentration = 0
            self.peak_hour = None
            self.peak_hour_events = 0
            self.temporal_concentration = 0
            self.severity_level = 'NORMAL'
            self.temporal_pattern = 'NO_EVENTS'
            self.force_pattern = 'NO_EVENTS'
            self.risk_level = 'LOW'
            return

        self.mean_force = self.events['force'].mean()
        self.max_force = self.events['force'].max()
        self.median_force = self.events['force'].median()
        self.std_force = self.events['force'].std()

        # Force variability
        self.force_cv = self.std_force / self.mean_force if self.mean_force > 0 else 0

        # Force distribution
        self.low_force_pct = len(self.events[self.events['force'] < 5]) / self.total_events * 100
        self.high_force_pct = len(self.events[self.events['force'] >= 7]) / self.total_events * 100

        # Temporal analysis
        self.events['hour'] = self.events['timestamp'].dt.hour
        hourly_counts = self.events.groupby('hour').size()

        # REM period (2-4 AM) concentration
        rem_events = len(self.events[self.events['hour'].isin([2, 3])])
        self.rem_concentration = (rem_events / self.total_events * 100)

        # Find peak hour
        if len(hourly_counts) > 0:
            self.peak_hour = hourly_counts.idxmax()
            self.peak_hour_events = hourly_counts.max()
        else:
            self.peak_hour = None
            self.peak_hour_events = 0

        # Temporal concentration
        max_2hr_concentration = 0
        for h in range(24):
            next_h = (h + 1) % 24
            window_events = len(self.events[self.events['hour'].isin([h, next_h])])
            concentration = (window_events / self.total_events * 100)
            max_2hr_concentration = max(max_2hr_concentration, concentration)
        self.temporal_concentration = max_2hr_concentration

        # Classify parameters
        self.classify_all_parameters()

    def classify_all_parameters(self):
        """Classify parameters into categories"""

        # Severity level
        if self.max_force > 12 or self.mean_force > 8 or self.total_events > 80:
            self.severity_level = 'CRITICAL'
        elif self.max_force > 10 or self.mean_force > 7 or self.total_events > 60:
            self.severity_level = 'SEVERE'
        elif self.max_force > 7 or self.mean_force > 5 or self.total_events > 40:
            self.severity_level = 'MODERATE'
        elif self.max_force > 5 or self.mean_force > 3 or self.total_events > 20:
            self.severity_level = 'MILD'
        else:
            self.severity_level = 'NORMAL'

        # Temporal pattern
        if self.rem_concentration > 60:
            self.temporal_pattern = 'REM_DOMINANT'
        elif self.temporal_concentration < 30:
            self.temporal_pattern = 'DISTRIBUTED'
        elif self.peak_hour and self.peak_hour <= 2:
            self.temporal_pattern = 'EARLY_NIGHT'
        else:
            self.temporal_pattern = 'LATE_NIGHT'

        # Force pattern
        if self.force_cv < 0.2:
            self.force_pattern = 'CONSISTENT'
        elif self.force_cv < 0.4:
            self.force_pattern = 'MODERATE_VARIABILITY'
        else:
            if self.low_force_pct > 25 and self.high_force_pct > 25:
                self.force_pattern = 'BIMODAL'
            else:
                self.force_pattern = 'HIGHLY_VARIABLE'

        # Risk level
        if self.max_force > 12:
            self.risk_level = 'URGENT'
        elif self.severity_level in ['SEVERE', 'CRITICAL'] and self.rem_concentration > 50:
            self.risk_level = 'HIGH'
        elif self.severity_level == 'MODERATE':
            self.risk_level = 'MODERATE'
        else:
            self.risk_level = 'LOW'

    def generate_summary_report(self):
        """Generate compact summary for PDF"""

        if self.total_events == 0:
            return f"""ANÁLISIS CLÍNICO DE BRUXISMO - SENSOR {self.sensor_name}

PATRÓN IDENTIFICADO:
No se detectaron eventos de bruxismo en este sensor durante el período de registro.

SIGNIFICADO CLÍNICO:
Actividad de bruxismo ausente o por debajo del umbral de detección en el sensor {self.sensor_name.lower()}.

RIESGO PRIORITARIO:
Sin riesgos identificados para este sensor.

INTERVENCIÓN RECOMENDADA:
Continuar monitoreo rutinario.

SEGUIMIENTO: Monitoreo estándar

---
Sensor: {self.sensor_name} | Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Reporte automatizado basado en sensores. El juicio clínico debe guiar decisiones finales.
"""

        # Pattern descriptions
        temporal_desc = {
            'REM_DOMINANT': f'{self.rem_concentration:.0f}% de eventos concentrados en período REM (2-4 AM)',
            'DISTRIBUTED': f'Eventos distribuidos durante la noche (<30% concentración)',
            'EARLY_NIGHT': f'Concentración en primera mitad de noche',
            'LATE_NIGHT': f'Mayor actividad en segunda mitad de noche'
        }.get(self.temporal_pattern, 'Patrón temporal mixto')

        force_desc = {
            'CONSISTENT': f'fuerzas consistentes (baja variabilidad)',
            'BIMODAL': f'patrón bimodal ({self.low_force_pct:.0f}% bajas, {self.high_force_pct:.0f}% altas)',
            'HIGHLY_VARIABLE': f'fuerzas erráticas (CV={self.force_cv:.2f})',
            'MODERATE_VARIABILITY': f'fuerzas moderadamente variables'
        }.get(self.force_pattern, 'fuerzas variables')

        # Clinical meaning
        if self.temporal_pattern == 'REM_DOMINANT':
            if self.force_pattern in ['HIGHLY_VARIABLE', 'BIMODAL']:
                clinical_meaning = "Sugiere bruxismo asociado a estrés con activación durante sueño REM."
            else:
                clinical_meaning = "Indica bruxismo de sueño primario vinculado a arquitectura del sueño."
        elif self.force_pattern in ['HIGHLY_VARIABLE', 'BIMODAL']:
            clinical_meaning = "Patrón indica bruxismo mediado por estrés con componente reactivo."
        else:
            clinical_meaning = "Patrón sugiere bruxismo relacionado con transiciones de sueño."

        # Peak insight
        peak_insight = f"Pico de actividad a las {self.peak_hour:02d}:00 hrs ({self.peak_hour_events} eventos)." if self.peak_hour is not None else ""

        # Severity context
        if self.severity_level in ['SEVERE', 'CRITICAL']:
            severity_context = f"Excede umbrales clínicos: {len(self.events[self.events['force'] > 7])} eventos severos (>7kg)."
        elif self.severity_level == 'MODERATE':
            severity_context = f"{len(self.events[self.events['force'] > 5])} eventos superan umbral moderado (>5kg)."
        else:
            severity_context = "Actividad dentro de rangos manejables."

        # Primary risk
        if self.max_force > 10:
            primary_risk = "Riesgo de fractura dental (ALTO): Fuerzas exceden umbral de seguridad."
        elif self.max_force > 7:
            primary_risk = "Riesgo de desgaste dental (MODERADO-ALTO): Fuerzas causan atrición acelerada."
        elif self.mean_force > 5:
            primary_risk = "Riesgo de desgaste crónico (MODERADO): Erosión del esmalte a largo plazo."
        else:
            primary_risk = "Sin riesgos inmediatos identificados."

        # Primary intervention
        if self.severity_level in ['CRITICAL', 'SEVERE']:
            primary_intervention = "Terapia Inmediata con Férula Oclusal - Fabricar férula de estabilización de acrílico duro"
        elif self.severity_level == 'MODERATE':
            primary_intervention = "Terapia con Férula Oclusal - Protector nocturno, reevaluar en 4 semanas"
        else:
            primary_intervention = "Manejo Conservador - Educación sobre higiene del sueño y reducción del estrés"

        # Follow-up
        followup_map = {'URGENT': '1 semana', 'HIGH': '2 semanas', 'MODERATE': '4 semanas', 'LOW': '8-12 semanas'}
        followup = followup_map.get(self.risk_level, '8-12 semanas')

        # Key metric
        if self.severity_level in ['SEVERE', 'CRITICAL']:
            key_metric = "reducción de fuerza máxima <7kg y frecuencia -40%"
        elif self.severity_level == 'MODERATE':
            key_metric = "reducción de fuerza promedio -30%"
        else:
            key_metric = "monitoreo de progresión"

        summary = f"""ANÁLISIS CLÍNICO DE BRUXISMO - SENSOR {self.sensor_name}

PATRÓN IDENTIFICADO:
{temporal_desc.capitalize()} con {force_desc}. {peak_insight} {severity_context}

SIGNIFICADO CLÍNICO:
{clinical_meaning}

RIESGO PRIORITARIO:
{primary_risk}

INTERVENCIÓN RECOMENDADA:
{primary_intervention}

SEGUIMIENTO: Reevaluación en {followup} - Objetivo: {key_metric}

---
Sensor: {self.sensor_name} | Severidad: {self.severity_level} | Eventos: {self.total_events} | Fuerza Máx: {self.max_force:.1f}kg
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Reporte automatizado basado en sensores. El juicio clínico debe guiar decisiones finales.
"""
        return summary
