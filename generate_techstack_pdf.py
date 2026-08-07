import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and display total page count in header/footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Header (Top decorative line & Header text)
        self.setStrokeColor(colors.HexColor("#0284C7")) # HAL Cyan
        self.setLineWidth(1.5)
        self.line(54, 750, 558, 750)
        
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0F172A"))
        self.drawString(54, 756, "HAL AEROSPACE — LCA TEJAS Mk1A DIGITAL TWIN PLATFORM")
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawRightString(558, 756, "AEROTHON 2026 | TECHNICAL SPECIFICATION")

        # Footer (Bottom line & Page numbering)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(54, 45, 558, 45)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 32, "CONFIDENTIAL & PROPRIETARY — HINDUSTAN AERONAUTICS LIMITED")
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        
        self.restoreState()

def create_tech_stack_pdf(output_filename):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=54,  # 0.75 inch
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0F172A")    # Deep Navy
    SECONDARY = colors.HexColor("#0284C7")  # Aerospace Blue / Cyan
    ACCENT = colors.HexColor("#0369A1")     # Deep Cyan
    TEXT_DARK = colors.HexColor("#1E293B")  # Slate 800
    TEXT_MUTED = colors.HexColor("#475569") # Slate 600
    BG_LIGHT = colors.HexColor("#F8FAFC")   # Slate 50
    BG_HEADER = colors.HexColor("#0F172A")  # Dark Header fill
    BORDER_COLOR = colors.HexColor("#CBD5E1")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=ACCENT,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=TEXT_DARK,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    tbl_header_style = ParagraphStyle(
        'TblHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=0
    )

    tbl_cell_style = ParagraphStyle(
        'TblCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=TEXT_DARK
    )

    tbl_cell_bold = ParagraphStyle(
        'TblCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=PRIMARY
    )

    tbl_cell_code = ParagraphStyle(
        'TblCellCode',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8,
        leading=11,
        textColor=SECONDARY
    )

    story = []

    # Title Banner Block
    story.append(Spacer(1, 10))
    story.append(Paragraph("HAL Aerospace — LCA Tejas Mk1A Digital Twin", title_style))
    story.append(Paragraph("Framework & Technology Stack Architecture Specification | AEROTHON 2026", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=SECONDARY, spaceBefore=0, spaceAfter=12))

    # Executive Overview
    story.append(Paragraph("1. Executive Overview & System Architecture", h1_style))
    overview_text = (
        "The <b>HAL Aerospace Digital Twin Platform</b> is an enterprise-grade, full-stack mission control workstation "
        "engineered for real-time health monitoring, telemetry processing, and predictive maintenance of the "
        "<b>GE F404-IN20 turbofan engine</b> powering the <b>LCA Tejas Mk1A</b> fighter aircraft. Built for HAL Mission Control, "
        "the workstation unifies high-frequency thermodynamic simulation (Brayton cycle 0D/1D solver), 3-factor biometric access, "
        "interactive 3D graphics rendering, and explainable AI (XAI) diagnostics across fleet squadrons."
    )
    story.append(Paragraph(overview_text, body_style))
    story.append(Spacer(1, 6))

    # High Level Architecture Table
    arch_data = [
        [Paragraph("Layer", tbl_header_style), Paragraph("Component", tbl_header_style), Paragraph("Technology / Framework", tbl_header_style), Paragraph("Primary Responsibility", tbl_header_style)],
        [Paragraph("Frontend", tbl_cell_bold), Paragraph("User Interface", tbl_cell_style), Paragraph("React 19 + Vite 6 + TypeScript 5", tbl_cell_code), Paragraph("60 FPS Telemetry Dashboard, 3D Digital Twin Viewport, Fleet Operations", tbl_cell_style)],
        [Paragraph("Frontend", tbl_cell_bold), Paragraph("State & Async Data", tbl_cell_style), Paragraph("Zustand 5 + TanStack Query 5", tbl_cell_code), Paragraph("Global UI state, telemetry store, server-side REST caching & revalidation", tbl_cell_style)],
        [Paragraph("Frontend", tbl_cell_bold), Paragraph("Visualization & Graphics", tbl_cell_style), Paragraph("ECharts 5.6 + Recharts + Three.js", tbl_cell_code), Paragraph("Live gauge streaming, Weibull survival curves, SHAP waterfalls, SVG cutaways", tbl_cell_style)],
        [Paragraph("Backend", tbl_cell_bold), Paragraph("REST API Server", tbl_cell_style), Paragraph("FastAPI 0.140 + Uvicorn ASGI", tbl_cell_code), Paragraph("Async REST endpoints, biometric auth verification, physics model execution", tbl_cell_style)],
        [Paragraph("Backend", tbl_cell_bold), Paragraph("Persistence Layer", tbl_cell_style), Paragraph("SQLAlchemy 2.0 + SQLite DB", tbl_cell_code), Paragraph("Operator registry, mission logs, sortie replay history, audit trails", tbl_cell_style)],
        [Paragraph("Backend", tbl_cell_bold), Paragraph("Security & Biometrics", tbl_cell_style), Paragraph("PyJWT + Passlib + OpenCV + MediaPipe", tbl_cell_code), Paragraph("JWT token creation, PBKDF2 hashing, 3-factor facial landmark extraction", tbl_cell_style)],
    ]
    arch_table = Table(arch_data, colWidths=[1.0*inch, 1.3*inch, 2.1*inch, 2.6*inch])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_HEADER),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 12))

    # Detailed Frontend Tech Stack
    story.append(Paragraph("2. Frontend Framework & Technology Stack Details", h1_style))
    story.append(Paragraph("The presentation layer is built as a Single Page Application (SPA) using React 19 and Vite 6, providing instant render updates and modular UI components.", body_style))
    story.append(Spacer(1, 4))

    fe_data = [
        [Paragraph("Technology / Library", tbl_header_style), Paragraph("Version", tbl_header_style), Paragraph("Category", tbl_header_style), Paragraph("Technical Usage in Platform", tbl_header_style)],
        [Paragraph("React", tbl_cell_bold), Paragraph("19.0.0", tbl_cell_code), Paragraph("UI Core Framework", tbl_cell_style), Paragraph("Concurrent rendering, functional components, custom telemetry hooks.", tbl_cell_style)],
        [Paragraph("TypeScript", tbl_cell_bold), Paragraph("5.7.2", tbl_cell_code), Paragraph("Language", tbl_cell_style), Paragraph("Strict end-to-end type safety, engine sensor schemas, API interfaces.", tbl_cell_style)],
        [Paragraph("Vite", tbl_cell_bold), Paragraph("6.1.0", tbl_cell_code), Paragraph("Build Tool & Server", tbl_cell_style), Paragraph("Lightning-fast HMR dev server and optimized production ESM bundler.", tbl_cell_style)],
        [Paragraph("TailwindCSS", tbl_cell_bold), Paragraph("3.4.17", tbl_cell_code), Paragraph("Styling & Design System", tbl_cell_style), Paragraph("Utility-first styling, custom dark-mode aerospace cockpit color theme.", tbl_cell_style)],
        [Paragraph("Zustand", tbl_cell_bold), Paragraph("5.0.3", tbl_cell_code), Paragraph("Global State", tbl_cell_style), Paragraph("Centralized state management for telemetry streams & selected squadron.", tbl_cell_style)],
        [Paragraph("TanStack Query", tbl_cell_bold), Paragraph("5.66.0", tbl_cell_code), Paragraph("Server State / Cache", tbl_cell_style), Paragraph("Asynchronous API data fetching, query caching, and auto-refetching.", tbl_cell_style)],
        [Paragraph("ECharts & ECharts React", tbl_cell_bold), Paragraph("5.6.0 / 3.0.2", tbl_cell_code), Paragraph("Data Visualization", tbl_cell_style), Paragraph("High-frequency telemetry charts (N1/N2 RPM, T4 temp), gauge clusters.", tbl_cell_style)],
        [Paragraph("Recharts", tbl_cell_bold), Paragraph("2.15.1", tbl_cell_code), Paragraph("Data Visualization", tbl_cell_style), Paragraph("Weibull reliability curves, RUL predictions, SHAP waterfall charts.", tbl_cell_style)],
        [Paragraph("Three.js & Unity WebGL", tbl_cell_bold), Paragraph("0.185.1 / 9.6.0", tbl_cell_code), Paragraph("3D / CAD Viewport", tbl_cell_style), Paragraph("Interactive GE F404 turbofan rendering, SVG thermal cutaway overlay.", tbl_cell_style)],
        [Paragraph("Framer Motion", tbl_cell_bold), Paragraph("12.0.0", tbl_cell_code), Paragraph("Animations", tbl_cell_style), Paragraph("Micro-interactions, alert drawer transitions, diagnostic modal reveals.", tbl_cell_style)],
        [Paragraph("React Router", tbl_cell_bold), Paragraph("7.1.5", tbl_cell_code), Paragraph("Routing", tbl_cell_style), Paragraph("Client-side view routing (Mission Control, Fleet, Diagnostics, Replay).", tbl_cell_style)],
        [Paragraph("Lucide React", tbl_cell_bold), Paragraph("0.475.0", tbl_cell_code), Paragraph("Icon System", tbl_cell_style), Paragraph("Military-grade vector iconography for engine telemetry and status badges.", tbl_cell_style)],
        [Paragraph("Zod", tbl_cell_bold), Paragraph("3.24.2", tbl_cell_code), Paragraph("Schema Validation", tbl_cell_style), Paragraph("Runtime data validation for telemetry payloads and operator auth credentials.", tbl_cell_style)],
        [Paragraph("Playwright", tbl_cell_bold), Paragraph("1.62.0", tbl_cell_code), Paragraph("Testing Framework", tbl_cell_style), Paragraph("Automated End-to-End testing of critical mission control workflows.", tbl_cell_style)]
    ]

    fe_table = Table(fe_data, colWidths=[1.5*inch, 0.8*inch, 1.4*inch, 3.3*inch])
    fe_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_HEADER),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(fe_table)
    story.append(Spacer(1, 12))

    # Detailed Backend Tech Stack
    story.append(Paragraph("3. Backend Framework & Technology Stack Details", h1_style))
    story.append(Paragraph("The server application is built in Python 3.10+ using FastAPI, delivering high-performance asynchronous REST endpoints, database ORM bindings, and mathematical physics algorithms.", body_style))
    story.append(Spacer(1, 4))

    be_data = [
        [Paragraph("Technology / Library", tbl_header_style), Paragraph("Version", tbl_header_style), Paragraph("Category", tbl_header_style), Paragraph("Technical Usage in Platform", tbl_header_style)],
        [Paragraph("FastAPI", tbl_cell_bold), Paragraph("0.140.0", tbl_cell_code), Paragraph("REST API Framework", tbl_cell_style), Paragraph("High-performance asynchronous Python API with automatic OpenAPI / Swagger specs.", tbl_cell_style)],
        [Paragraph("Uvicorn", tbl_cell_bold), Paragraph("0.51.0", tbl_cell_code), Paragraph("ASGI Web Server", tbl_cell_style), Paragraph("Asynchronous server gateway interface hosting FastAPI backend services.", tbl_cell_style)],
        [Paragraph("SQLAlchemy", tbl_cell_bold), Paragraph("2.0.38", tbl_cell_code), Paragraph("Database ORM", tbl_cell_style), Paragraph("Object-relational mapping for operator data, login audits, and mission logs.", tbl_cell_style)],
        [Paragraph("SQLite", tbl_cell_bold), Paragraph("Embedded", tbl_cell_code), Paragraph("Database Engine", tbl_cell_style), Paragraph("Low-latency relational storage (`hal_mission_control.db`) for mission registries.", tbl_cell_style)],
        [Paragraph("PyJWT", tbl_cell_bold), Paragraph("2.13.0", tbl_cell_code), Paragraph("Security & Auth", tbl_cell_style), Paragraph("Generation and verification of cryptographically signed JWT access tokens.", tbl_cell_style)],
        [Paragraph("Passlib", tbl_cell_bold), Paragraph("1.7.4", tbl_cell_code), Paragraph("Security & Auth", tbl_cell_style), Paragraph("Secure password hashing using `pbkdf2_sha256` with automated salt creation.", tbl_cell_style)],
        [Paragraph("Pydantic", tbl_cell_bold), Paragraph("2.13.0", tbl_cell_code), Paragraph("Data Validation", tbl_cell_style), Paragraph("Data parsing, request model validation, and structured JSON responses.", tbl_cell_style)],
        [Paragraph("NumPy", tbl_cell_bold), Paragraph("2.5.0", tbl_cell_code), Paragraph("Numerical Computing", tbl_cell_style), Paragraph("Vectorized math for thermodynamic Brayton cycle & biometric vector matching.", tbl_cell_style)],
        [Paragraph("OpenCV (optional)", tbl_cell_bold), Paragraph("4.11.0", tbl_cell_code), Paragraph("Computer Vision", tbl_cell_style), Paragraph("Real-time webcam frame acquisition for military facial authentication.", tbl_cell_style)],
        [Paragraph("MediaPipe (optional)", tbl_cell_bold), Paragraph("0.10.21", tbl_cell_code), Paragraph("AI & Computer Vision", tbl_cell_style), Paragraph("3D facial landmark mesh extraction for live 3-factor biometric verification.", tbl_cell_style)]
    ]

    be_table = Table(be_data, colWidths=[1.5*inch, 0.8*inch, 1.4*inch, 3.3*inch])
    be_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_HEADER),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(be_table)
    story.append(Spacer(1, 12))

    # Core Engineering Modules & Technical Specs
    story.append(Paragraph("4. Core Engineering Modules & Technical Specifications", h1_style))
    story.append(Paragraph("The platform integrates specialized defense aerospace engineering capabilities across key operational modules:", body_style))

    modules = [
        ("🔐 Military-Grade Biometric Auth", "3-Factor authentication pipeline combining Operator ID, PBKDF2 hashed password, and live facial landmark verification (DEMO & REAL webcam modes supported)."),
        ("✈️ Interactive Digital Twin Viewport", "High-precision SVG engine cutaway with interactive toggleable visual modes: Normal, X-Ray (structural stress), and Thermal (temperature gradient heatmaps)."),
        ("📡 Real-Time Telemetry Streaming Engine", "60 FPS streaming processor tracking critical GE F404 metrics: N1 Low-Pressure Spool RPM, N2 High-Pressure Spool RPM, T4 Turbine Inlet Temperature (°C), Vibration (mm/s), Fuel Flow (kg/h), and Compressor Pressure Ratio."),
        ("🧠 AI Predictive Maintenance & RUL", "Weibull distribution hazard modeling, Anomaly Scoring engines, and Remaining Useful Life (RUL) forecasting based on cumulative flight hours."),
        ("🔬 Explainable AI (XAI) Diagnostics", "SHAP (SHapley Additive exPlanations) waterfall chart generation pinpointing top contributing factors behind flagged operational anomalies."),
        ("⚙️ Physics-Informed Thermodynamics Solver", "0D/1D Brayton cycle solver calculating real-time turbine inlet thermal loads, compressor operating maps, and aerodynamic surge margins."),
        ("🌳 Causal Fault Tree Analysis", "Interactive fault propagation tree tracking root-cause sequences (e.g., Fuel Injector Clogging → Hot Spot → Thermal Creep → Turbine Blade Micro-fracture)."),
        ("🔁 Mission Replay & Historical Analytics", "Flight telemetry replay engine featuring 500 historical sorties with interactive surge event injection for operator training.")
    ]

    for title, desc in modules:
        story.append(Paragraph(f"• <b>{title}</b>: {desc}", bullet_style))

    story.append(Spacer(1, 10))

    # Project Directory Structure Overview
    story.append(Paragraph("5. System Repository Directory Structure", h1_style))
    dir_code = (
        "<b>AEROTHON2026/</b><br/>"
        "├── <b>backend/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Python FastAPI Service<br/>"
        "│ &nbsp;&nbsp;├── main.py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# REST API routes & app entry point<br/>"
        "│ &nbsp;&nbsp;├── auth/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# JWT security & biometric engine<br/>"
        "│ &nbsp;&nbsp;└── digital_twin/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Brayton thermodynamic solver & AI models<br/>"
        "├── <b>src/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# React 19 Frontend Source Code<br/>"
        "│ &nbsp;&nbsp;├── components/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Digital Twin, Charts, Telemetry gauges<br/>"
        "│ &nbsp;&nbsp;├── store/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Zustand state stores<br/>"
        "│ &nbsp;&nbsp;└── types/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# TypeScript interface definitions<br/>"
        "├── hal_mission_control.db &nbsp;&nbsp;# SQLite Relational Database<br/>"
        "├── package.json &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Frontend Dependencies & Build Scripts<br/>"
        "└── vite.config.ts &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Vite ESM Config & Proxy Rules"
    )
    story.append(Paragraph(dir_code, body_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {output_filename}")

if __name__ == "__main__":
    output_pdf = r"c:\Users\praja\Downloads\AEROTHON2026-main (2)\AEROTHON2026-main\HAL_Tejas_Digital_Twin_Tech_Stack.pdf"
    create_tech_stack_pdf(output_pdf)
