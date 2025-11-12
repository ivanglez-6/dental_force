"""
Bruxism Clinical Summary Dashboard
Publication-Quality Static Chart
Following "Storytelling with Data" Principles

Visualization 6: Comprehensive dashboard combining KPIs, summary statistics, and mini visualizations
The "executive summary" for rapid clinical decision-making
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np
from datetime import datetime
import matplotlib.dates as mdates
import textwrap
from matplotlib.cm import YlOrRd
from matplotlib.colors import Normalize



def generate_dashboard(csv_path, output_path, sensor_id=1):
    """
    Generate a comprehensive bruxism dashboard from session data.

    Args:
        csv_path (str): Path to input CSV file
        output_path (str): Path where the PNG will be saved

    Returns:
        str: Path to the generated PNG file
    """
    # Disable interactive plotting
    plt.ioff()

    # Load data
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['date'].str.replace('T', ' '))


    # Filter data for this sensor
    sensor_df = df[df['sensorId'] == sensor_id].copy()
    sensor_df = sensor_df.reset_index(drop=True)

    # ============================================
    # STEP 1: Calculate Time Span of Data
    # ============================================
    min_timestamp = sensor_df['timestamp'].min()
    max_timestamp = sensor_df['timestamp'].max()
    data_duration_hours = (max_timestamp - min_timestamp).total_seconds() / 3600
    is_overnight_data = data_duration_hours >= 5

    # ============================================
    # STEP 2: Process Events Based on Data Type
    # ============================================
    if is_overnight_data:
        # Overnight data: Keep raw events (no grouping)
        events = sensor_df[sensor_df['event'] == 1.0].copy()
    else:
        # Demo data: Group consecutive events into episodes
        event_rows = sensor_df[sensor_df['event'] == 1.0].copy()
        event_rows = event_rows.sort_values('timestamp')

        if len(event_rows) > 0:
            # Preserve original index to detect gaps in consecutive rows
            event_rows['original_index'] = event_rows.index
            event_rows = event_rows.reset_index(drop=True)

            # Create episode grouping identifier based on original index
            event_rows['original_index_diff'] = event_rows['original_index'].diff()
            event_rows['episode_group'] = (event_rows['original_index_diff'] != 1).cumsum()

            # Group by episode and get first timestamp and max force
            episodes_list = []
            for episode_id, group in event_rows.groupby('episode_group'):
                episodes_list.append({
                    'timestamp': group['timestamp'].iloc[0],
                    'force': group['force'].max(),
                    'event': 1.0
                })

            events = pd.DataFrame(episodes_list)
        else:
            events = event_rows

    # ============================================
    # CALCULATE KEY METRICS
    # ============================================

    total_events = len(events)
    mean_force = events['force'].mean() if len(events) > 0 else 0
    max_force = events['force'].max() if len(events) > 0 else 0

    # Calculate active time (approximate - consecutive events as continuous episodes)
    events_sorted = events.sort_values('timestamp')
    events_sorted['time_diff'] = events_sorted['timestamp'].diff().dt.total_seconds() / 60
    # Consider events within 2 minutes as same episode
    episodes = (events_sorted['time_diff'] > 2).cumsum()
    active_minutes = len(events)  # Rough approximation: 1 event ≈ 1 minute

    # Determine severity level
    def get_severity_level(total_events, mean_force, max_force):
        if max_force > 10 or mean_force > 7 or total_events > 60:
            return 'SEVERO', '#e74c3c'
        elif max_force > 7 or mean_force > 5 or total_events > 40:
            return 'MODERADO', '#f39c12'
        elif max_force > 5 or mean_force > 3 or total_events > 20:
            return 'LEVE', '#f39c12'
        else:
            return 'NORMAL', '#2ecc71'

    severity_level, severity_color = get_severity_level(total_events, mean_force, max_force)

    # ============================================
    # CREATE DASHBOARD LAYOUT
    # ============================================

    fig = plt.figure(figsize=(16, 10))

    # Complex GridSpec for dashboard layout
    gs = GridSpec(4, 4, height_ratios=[1.2, 2, 2, 0.8], width_ratios=[1, 1, 1, 1],
                  hspace=0.4, wspace=0.35,
                  left=0.08, right=0.95, top=0.92, bottom=0.08)

    # ============================================
    # TOP SECTION - KEY PERFORMANCE INDICATORS (KPIs)
    # ============================================

    # KPI panels
    kpi_positions = [
        (0, 0),  # Total Events
        (0, 1),  # Mean Force
        (0, 2),  # Max Force
        (0, 3),  # Active Time
    ]

    kpi_data = [
        {
            'label': 'Eventos Totales',
            'value': total_events,
            'unit': 'episodios',
            'color': severity_color if total_events > 40 else '#34495e',
            'threshold': 40,
            'status': 'ALTO' if total_events > 40 else 'NORMAL'
        },
        {
            'label': 'Fuerza Promedio',
            'value': mean_force,
            'unit': 'kg',
            'color': '#e74c3c' if mean_force > 7 else '#f39c12' if mean_force > 5 else '#2ecc71',
            'threshold': 5,
            'status': 'SEVERO' if mean_force > 7 else 'MODERADO' if mean_force > 5 else 'NORMAL'
        },
        {
            'label': 'Fuerza Máxima',
            'value': max_force,
            'unit': 'kg',
            'color': '#e74c3c' if max_force > 10 else '#f39c12' if max_force > 7 else '#2ecc71',
            'threshold': 7,
            'status': 'CRÍTICO' if max_force > 10 else 'ALTO' if max_force > 7 else 'NORMAL'
        },
        {
            'label': 'Tiempo Activo',
            'value': active_minutes,
            'unit': 'min',
            'color': '#34495e',
            'threshold': 30,
            'status': 'ALTO' if active_minutes > 30 else 'NORMAL'
        }
    ]

    for kpi, (row, col) in zip(kpi_data, kpi_positions):
        ax = fig.add_subplot(gs[row, col])

        # Remove axes
        ax.axis('off')

        # Background panel
        rect = mpatches.FancyBboxPatch((0, 0), 1, 1,
                                       boxstyle="round,pad=0.02",
                                       linewidth=2,
                                       edgecolor=kpi['color'],
                                       facecolor='white',
                                       alpha=0.9,
                                       transform=ax.transAxes,
                                       zorder=1)
        ax.add_patch(rect)

        # Label (top)
        ax.text(0.5, 0.75, kpi['label'],
               ha='center', va='center', fontsize=11,
               weight='bold', color='#34495e',
               transform=ax.transAxes)

        # Value (center - large)
        value_str = f"{kpi['value']:.1f}" if isinstance(kpi['value'], float) else str(kpi['value'])
        ax.text(0.5, 0.45, value_str,
               ha='center', va='center', fontsize=32,
               weight='bold', color=kpi['color'],
               transform=ax.transAxes)

        # Unit (below value)
        ax.text(0.5, 0.25, kpi['unit'],
               ha='center', va='center', fontsize=9,
               color='#7f8c8d',
               transform=ax.transAxes)

        # Status badge (bottom)
        if kpi['status'] != 'NORMAL':
            ax.text(0.5, 0.08, kpi['status'],
                   ha='center', va='center', fontsize=8,
                   weight='bold', color='white',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor=kpi['color'], alpha=0.8),
                   transform=ax.transAxes)

    # ============================================
    # MIDDLE LEFT - COMPRESSED TIMELINE CHART
    # ============================================

    ax_timeline = fig.add_subplot(gs[1:3, 0:2])

    if len(events) > 0:
        # Plot events as scatter with FIXED color and size scales
        # Fixed color scale: 0-14 kg (consistent across all sessions)
        norm = Normalize(vmin=0, vmax=14)
        colors = [YlOrRd(norm(force)) for force in events['force']]

        # Fixed size scale based on force with min/max limits
        # Size range: 20 (minimum) to 200 (maximum)
        def calculate_size(force):
            # Linear mapping: 0kg=20, 14kg=200
            size = 20 + (force / 14) * 180
            return max(20, min(200, size))  # Clamp between 20-200

        sizes = [calculate_size(force) for force in events['force']]

        ax_timeline.scatter(events['timestamp'], events['force'],
                           s=sizes, c=colors, alpha=0.85,
                           edgecolors='white', linewidth=0.8, zorder=3)

    # Clinical thresholds
    ax_timeline.axhline(y=5, color='#95a5a6', linestyle='--', linewidth=1, alpha=0.5, zorder=1)
    ax_timeline.axhline(y=7, color='#e74c3c', linestyle='--', linewidth=1, alpha=0.5, zorder=1)

    # REM shading (only for overnight data)
    if is_overnight_data:
        rem_start = pd.to_datetime('2025-11-07 02:00:00')
        rem_end = pd.to_datetime('2025-11-07 04:00:00')
        ax_timeline.axvspan(rem_start, rem_end, alpha=0.08, color='#3498db', zorder=0)

    # Formatting
    ax_timeline.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax_timeline.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax_timeline.set_xlabel('Hora de la Noche', fontsize=10, weight='bold')
    ax_timeline.set_ylabel('Fuerza (kg)', fontsize=10, weight='bold')
    ax_timeline.set_title('Línea de Tiempo de Eventos', fontsize=11, weight='bold', pad=10)
    ax_timeline.set_ylim(0, 14)
    ax_timeline.grid(axis='y', alpha=0.2, linestyle='-', linewidth=0.5, zorder=0)
    ax_timeline.set_axisbelow(True)
    ax_timeline.spines['top'].set_visible(False)
    ax_timeline.spines['right'].set_visible(False)

    # ============================================
    # MIDDLE RIGHT TOP - FORCE DISTRIBUTION HISTOGRAM
    # ============================================

    ax_force_hist = fig.add_subplot(gs[1, 2:4])

    if len(events) > 0:
        # Create histogram
        bins = np.arange(0, 15, 1)
        counts, bin_edges, patches = ax_force_hist.hist(events['force'], bins=bins,
                                                         edgecolor='white', linewidth=1,
                                                         alpha=0.8)

        # Color bars by severity
        for i, (patch, edge) in enumerate(zip(patches, bin_edges[:-1])):
            if edge < 5:
                patch.set_facecolor('#2ecc71')
            elif edge < 7:
                patch.set_facecolor('#f39c12')
            else:
                patch.set_facecolor('#e74c3c')

    # Formatting
    ax_force_hist.set_xlabel('Fuerza (kg)', fontsize=9, weight='bold')
    ax_force_hist.set_ylabel('Cantidad de Eventos', fontsize=9, weight='bold')
    ax_force_hist.set_title('Distribución de Fuerza', fontsize=11, weight='bold', pad=10)
    ax_force_hist.grid(axis='y', alpha=0.2, linestyle='-', linewidth=0.5, zorder=0)
    ax_force_hist.set_axisbelow(True)
    ax_force_hist.spines['top'].set_visible(False)
    ax_force_hist.spines['right'].set_visible(False)

    # Add threshold markers
    ax_force_hist.axvline(x=5, color='#95a5a6', linestyle='--', linewidth=1.5, alpha=0.6, zorder=10)
    ax_force_hist.axvline(x=7, color='#e74c3c', linestyle='--', linewidth=1.5, alpha=0.6, zorder=10)

    # ============================================
    # MIDDLE RIGHT BOTTOM - HOURLY DISTRIBUTION
    # ============================================

    ax_hourly = fig.add_subplot(gs[2, 2:4])

    if is_overnight_data:
        # ============================================
        # OVERNIGHT MODE: Hourly distribution
        # ============================================
        if len(events) > 0:
            # Calculate events per hour
            events['hour'] = events['timestamp'].dt.hour
            hourly_counts = events.groupby('hour').size()

            # Create bar chart
            hours = list(range(23)) + list(range(0, 7))
            hour_labels = []
            hour_values = []
            for h in hours:
                if h >= 11 or h <= 7:
                    hour_labels.append(f"{h:02d}")
                    hour_values.append(hourly_counts.get(h, 0))

            # Color bars - highlight REM period (2-4 AM)
            bar_colors = []
            for h in hours:
                if h >= 11 or h <= 7:
                    if 2 <= h <= 3:
                        bar_colors.append('#e74c3c')
                    else:
                        bar_colors.append('#34495e')

            bars = ax_hourly.bar(range(len(hour_values)), hour_values,
                                 color=bar_colors, alpha=0.7, edgecolor='white', linewidth=1)

        # Formatting
        ax_hourly.set_xlabel('Hora de la Noche', fontsize=9, weight='bold')
        ax_hourly.set_ylabel('Eventos', fontsize=9, weight='bold')
        ax_hourly.set_title('Distribución Horaria', fontsize=11, weight='bold', pad=10)
        if len(events) > 0:
            ax_hourly.set_xticks(range(len(hour_labels)))
            ax_hourly.set_xticklabels(hour_labels, fontsize=7)
    else:
        # ============================================
        # DEMO MODE: Minute-level distribution
        # ============================================
        if len(events) > 0:
            # Round timestamps to minute level
            events['minute'] = events['timestamp'].dt.floor('T')
            minute_counts = events.groupby('minute').size()

            # Determine display range
            min_minute = events['minute'].min()
            max_minute = events['minute'].max()
            display_start = min_minute - pd.Timedelta(minutes=1)
            display_end = max_minute + pd.Timedelta(minutes=1)

            # Generate all minutes in range
            all_minutes = pd.date_range(start=display_start, end=display_end, freq='T')
            minute_values = [minute_counts.get(m, 0) for m in all_minutes]
            minute_labels = [m.strftime('%H:%M') for m in all_minutes]

            # Create bar chart with neutral color
            bars = ax_hourly.bar(range(len(minute_values)), minute_values,
                                 color='#34495e', alpha=0.7, edgecolor='white', linewidth=1)

            # Formatting
            ax_hourly.set_xlabel('Minuto', fontsize=9, weight='bold')
            ax_hourly.set_ylabel('Eventos', fontsize=9, weight='bold')
            ax_hourly.set_title('Distribución por Minuto', fontsize=11, weight='bold', pad=10)
            ax_hourly.set_xticks(range(len(minute_labels)))
            ax_hourly.set_xticklabels(minute_labels, fontsize=7, rotation=45 if len(minute_labels) > 5 else 0)

    # Common formatting for both modes
    ax_hourly.grid(axis='y', alpha=0.2, linestyle='-', linewidth=0.5, zorder=0)
    ax_hourly.set_axisbelow(True)
    ax_hourly.spines['top'].set_visible(False)
    ax_hourly.spines['right'].set_visible(False)

    # ============================================
    # BOTTOM SECTION - CLINICAL INTERPRETATION
    # ============================================

    ax_interp = fig.add_subplot(gs[3, :])
    ax_interp.axis('off')

    # Generate clinical interpretation
    def generate_interpretation(severity, total_events, mean_force, max_force):
        if severity == 'SEVERO':
            if max_force > 10:
                return (f"Bruxismo SEVERO detectado con fuerzas críticamente altas (máx {max_force:.1f} kg). "
                       f"El paciente muestra {total_events} eventos con fuerza promedio de {mean_force:.1f} kg. "
                       f"SE RECOMIENDA INTERVENCIÓN INMEDIATA. Considere protector nocturno, medicación y manejo del estrés.")
            else:
                return (f"Bruxismo SEVERO con {total_events} eventos y fuerza promedio de {mean_force:.1f} kg. "
                       f"Preocupación clínica significativa. Se recomienda plan de tratamiento integral incluyendo protector nocturno y seguimiento.")
        elif severity == 'MODERADO':
            return (f"Actividad de bruxismo MODERADA detectada. {total_events} eventos con fuerza promedio de {mean_force:.1f} kg. "
                   f"Considere terapia con protector nocturno y monitoreo para progresión. Programe seguimiento en 2 semanas.")
        elif severity == 'LEVE':
            return (f"Actividad de bruxismo LEVE. {total_events} eventos con fuerza promedio de {mean_force:.1f} kg. "
                   f"Monitoree al paciente. Considere manejo conservador y técnicas de reducción de estrés.")
        else:
            return (f"Actividad de bruxismo dentro de límites normales. {total_events} eventos con fuerza promedio de {mean_force:.1f} kg. "
                   f"Continúe monitoreando. No se requiere intervención inmediata.")

    interpretation_text = generate_interpretation(severity_level, total_events, mean_force, max_force)

    # Interpretation box
    rect_interp = mpatches.FancyBboxPatch((0.05, 0.2), 0.75, 0.7,
                                         boxstyle="round,pad=0.02",
                                         linewidth=2,
                                         edgecolor='#34495e',
                                         facecolor='#ecf0f1',
                                         alpha=0.8,
                                         transform=ax_interp.transAxes,
                                         zorder=1)
    ax_interp.add_patch(rect_interp)

    # Wrap text to fit in the box (approximately 120 characters per line)
    wrapped_text = '\n'.join(textwrap.wrap(interpretation_text, width=120))

    ax_interp.text(0.425, 0.55, wrapped_text,
                  ha='center', va='center', fontsize=9,
                  color='#2c3e50',
                  transform=ax_interp.transAxes,
                  weight='normal')

    # Severity badge (large, prominent)
    badge_text = f"SEVERIDAD: {severity_level}"
    rect_badge = mpatches.FancyBboxPatch((0.82, 0.25), 0.15, 0.6,
                                        boxstyle="round,pad=0.02",
                                        linewidth=3,
                                        edgecolor=severity_color,
                                        facecolor=severity_color,
                                        alpha=0.9,
                                        transform=ax_interp.transAxes,
                                        zorder=2)
    ax_interp.add_patch(rect_badge)

    ax_interp.text(0.895, 0.55, badge_text,
                  ha='center', va='center', fontsize=12,
                  color='white', weight='bold',
                  transform=ax_interp.transAxes,
                  rotation=0)

    # ============================================
    # TITLE AND HEADER
    # ============================================

    fig.suptitle(f'Panel de Resumen Clínico - Análisis de Bruxismo (Sensor {sensor_id})',
                fontsize=18, weight='bold', y=0.97)

    # Patient and date info
    if is_overnight_data:
        time_period = 'Período de Sueño: 11:00 PM - 7:00 AM'
    else:
        if len(events) > 0:
            start_time = events['timestamp'].min().strftime('%I:%M %p')
            end_time = events['timestamp'].max().strftime('%I:%M %p')
            time_period = f'Período de Registro: {start_time} - {end_time}'
        else:
            time_period = 'Sin datos disponibles'

    if len(events) > 0:
        patient_info = f'ID Paciente: BRX-2025-001  |  Fecha: {events["timestamp"].dt.date.iloc[0]}  |  {time_period}'
    else:
        patient_info = f'ID Paciente: BRX-2025-001  |  {time_period}'

    fig.text(0.5, 0.93, patient_info,
            ha='center', fontsize=10, color='#34495e')

    # Timestamp
    fig.text(0.98, 0.01, f'Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            ha='right', fontsize=7, color='gray')

    # ============================================
    # SAVE OUTPUT
    # ============================================

    plt.savefig(output_path,
               dpi=300, bbox_inches='tight',
               facecolor='white', edgecolor='none')

    # Close the figure to free memory
    plt.close(fig)

    return output_path
