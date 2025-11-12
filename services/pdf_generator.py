"""
PDF Report Generator for Bruxism Analysis - Dual Sensor Version
Combines dashboard visualizations with clinical analysis into a professional PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, HRFlowable
from reportlab.lib import colors
import os
import tempfile
from pathlib import Path
import pandas as pd

from services.dashboard_generator import generate_dashboard
from services.report_generator import BruxismReportGenerator


def generate_bruxism_pdf_report(session_data, output_pdf_path):
    """
    Generate a 2-page PDF report with dual sensor analysis

    Page 1: Sensor 1 (Left) - Dashboard + Clinical Analysis
    Page 2: Sensor 2 (Right) - Dashboard + Clinical Analysis

    Args:
        session_data: List of records (dicts) from storage.get_session_data()
        output_pdf_path: Path where PDF will be saved

    Returns:
        str: Path to generated PDF
    """

    # Create temporary directory for dashboard images and CSV
    temp_dir = tempfile.mkdtemp()
    temp_csv = Path(temp_dir) / "session_data.csv"

    try:
        # Convert session data to DataFrame and save as CSV
        df = pd.DataFrame(session_data)

        # Ensure required columns exist
        for col in ['sensorId', 'force', 'timestamp', 'date', 'event']:
            if col not in df.columns:
                if col == 'sensorId':
                    df['sensorId'] = 1
                elif col == 'force':
                    df['force'] = 0
                elif col == 'event':
                    df['event'] = 0.0
                elif col == 'timestamp':
                    df['timestamp'] = ''
                elif col == 'date':
                    df['date'] = ''

        # Save to CSV
        df.to_csv(temp_csv, index=False)

        # Generate dashboards for both sensors
        dashboard_sensor1 = Path(temp_dir) / "dashboard_sensor1.png"
        dashboard_sensor2 = Path(temp_dir) / "dashboard_sensor2.png"

        generate_dashboard(str(temp_csv), str(dashboard_sensor1), sensor_id=1)
        generate_dashboard(str(temp_csv), str(dashboard_sensor2), sensor_id=2)

        # Generate clinical reports for both sensors
        report_gen_1 = BruxismReportGenerator(df, sensor_id=1)
        report_gen_2 = BruxismReportGenerator(df, sensor_id=2)

        report_text_1 = report_gen_1.generate_summary_report()
        report_text_2 = report_gen_2.generate_summary_report()

        # Create the PDF
        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=A4,
            rightMargin=0.6*inch,
            leftMargin=0.6*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        # Build PDF elements
        elements = []

        # === PAGE 1: SENSOR 1 (LEFT) ===
        elements.extend(_create_sensor_page(
            dashboard_path=str(dashboard_sensor1),
            report_text=report_text_1,
            sensor_name="IZQUIERDO"
        ))

        # Page break
        elements.append(PageBreak())

        # === PAGE 2: SENSOR 2 (RIGHT) ===
        elements.extend(_create_sensor_page(
            dashboard_path=str(dashboard_sensor2),
            report_text=report_text_2,
            sensor_name="DERECHO"
        ))

        # Build the PDF
        doc.build(elements)

        print(f"\n✓ PDF generado exitosamente: {output_pdf_path}")
        print(f"  - Tamaño: {os.path.getsize(output_pdf_path) / 1024:.1f} KB")

        return output_pdf_path

    finally:
        # Cleanup temporary files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def _create_sensor_page(dashboard_path, report_text, sensor_name):
    """Create elements for a single sensor page"""

    elements = []

    # Color palette
    color_primary = colors.HexColor('#1a365d')
    color_secondary = colors.HexColor('#2c5282')
    color_accent = colors.HexColor('#2b6cb0')
    color_text = colors.HexColor('#2d3748')
    color_text_light = colors.HexColor('#4a5568')
    color_divider = colors.HexColor('#cbd5e0')

    # Styles
    main_title_style = ParagraphStyle(
        'MainTitle',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=color_primary,
        alignment=TA_CENTER,
        spaceAfter=12,
        spaceBefore=8,
        leading=20,
        letterSpacing=0.5
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=10.5,
        textColor=color_secondary,
        spaceAfter=6,
        spaceBefore=10,
        alignment=TA_LEFT,
        leading=13,
        letterSpacing=0.3
    )

    body_justified_style = ParagraphStyle(
        'BodyJustified',
        fontName='Times-Roman',
        fontSize=9.5,
        textColor=color_text,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leading=13,
        firstLineIndent=0
    )

    body_bold_justified_style = ParagraphStyle(
        'BodyBoldJustified',
        fontName='Times-Bold',
        fontSize=9.5,
        textColor=color_text,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leading=13
    )

    metadata_style = ParagraphStyle(
        'Metadata',
        fontName='Helvetica',
        fontSize=7.5,
        textColor=color_text_light,
        alignment=TA_CENTER,
        spaceAfter=2,
        leading=10
    )

    subsection_style = ParagraphStyle(
        'Subsection',
        fontName='Times-Bold',
        fontSize=9.5,
        textColor=color_secondary,
        alignment=TA_LEFT,
        spaceAfter=4,
        leading=12
    )

    # === DASHBOARD IMAGE ===
    if os.path.exists(dashboard_path):
        img = Image(dashboard_path, width=7*inch, height=4.2*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.2*inch))

    # === DIVIDER ===
    divider_table = Table([['']], colWidths=[6.8*inch])
    divider_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 2, color_accent),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, color_divider),
    ]))
    elements.append(divider_table)
    elements.append(Spacer(1, 0.12*inch))

    # === TITLE ===
    title = Paragraph(f"INFORME CLÍNICO - SENSOR {sensor_name}", main_title_style)
    elements.append(title)

    # Title underline
    title_underline = Table([['']], colWidths=[3*inch])
    title_underline.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 1.5, color_accent),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(title_underline)
    elements.append(Spacer(1, 0.15*inch))

    # === CLINICAL REPORT TEXT ===
    lines = report_text.split('\n')

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Skip title (already have it)
        if 'ANÁLISIS CLÍNICO DE BRUXISMO' in line:
            continue

        # Separators
        if line.startswith('---'):
            elements.append(Spacer(1, 0.08*inch))
            hr = HRFlowable(width="80%", thickness=0.5, color=color_divider,
                           spaceAfter=8, spaceBefore=8, hAlign='CENTER')
            elements.append(hr)
            continue

        # Section headers (all caps with colon)
        if line.isupper() and ':' in line and len(line) < 80:
            elements.append(Spacer(1, 0.08*inch))
            elements.append(Paragraph(line, section_header_style))
            continue

        # Metadata (with |)
        if '|' in line and ('Sensor:' in line or 'Fecha:' in line or 'Severidad:' in line):
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(line, metadata_style))
            continue

        # Disclaimer
        if 'Reporte automatizado' in line or 'juicio clínico' in line:
            elements.append(Paragraph(line, metadata_style))
            continue

        # Other lines with | (data)
        if '|' in line:
            elements.append(Paragraph(f"<b>{line}</b>", body_bold_justified_style))
            continue

        # Subsection headers (ends with colon)
        if line.endswith(':') and len(line) < 60:
            elements.append(Spacer(1, 0.05*inch))
            elements.append(Paragraph(line, subsection_style))
            continue

        # Normal text
        elements.append(Paragraph(line, body_justified_style))

    # Footer
    elements.append(Spacer(1, 0.08*inch))
    footer_line = Table([['']], colWidths=[6.8*inch])
    footer_line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 0.5, color_divider),
    ]))
    elements.append(footer_line)

    return elements
