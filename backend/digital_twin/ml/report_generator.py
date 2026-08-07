"""
report_generator.py
====================
Automatic Engineering Report Generator for Aerothon 2026 Digital Twin.

Generates structured per-prediction engineering reports in:
  - JSON (always)
  - CSV (tabular summary)
  - Text (human-readable narrative)

PDF generation requires 'reportlab' package (optional).
"""

import json
import io
import csv
import datetime
from typing import Dict, Any, Optional, List


class EngineeringReportGenerator:
    """
    Generates exportable engineering reports from a complete prediction result.

    Input: The full response dict from process_active_frame() enriched with
           health_tree, rul_estimate, engineering_narrative, fleet_context, etc.

    Output formats: JSON dict, CSV bytes, TXT str, PDF bytes (if reportlab available)
    """

    @staticmethod
    def generate_report(
        engine_id: str,
        cycle: int,
        predictions: Dict,
        health_tree: Dict,
        rul_estimate: Dict,
        causal_chain: List[Dict],
        fleet_context: Dict,
        maintenance_prognosis: Dict,
        engineering_narrative: str,
        physics_validation: Dict,
        uncertainty_breakdown: Dict,
        inference_time_ms: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Builds and returns the master report dictionary.
        This is the canonical report format used for all export types.
        """
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        # Health summary
        overall_h = float(predictions.get("Overall Health", predictions.get("OverallHealth", 95.0)))
        comp_h    = float(predictions.get("Compressor Health", predictions.get("CompressorHealth", 97.0)))
        comb_h    = float(predictions.get("Combustor Health", predictions.get("CombustorHealth", 97.0)))
        turb_h    = float(predictions.get("Turbine Health", predictions.get("TurbineHealth", 97.0)))
        thrust    = float(predictions.get("Thrust", 54.0))
        tsfc      = float(predictions.get("TSFC", 0.025))
        confidence= float(predictions.get("Prediction Confidence", 95.0))

        rul_mean = int(rul_estimate.get("rul_mean", 200))
        rul_p10  = int(rul_estimate.get("rul_p10", 150))
        rul_p90  = int(rul_estimate.get("rul_p90", 250))
        rul_warn = rul_estimate.get("warning", "NORMAL")

        report = {
            # ── Metadata ──────────────────────────────────────────────────────
            "report_metadata": {
                "engine_id":       engine_id,
                "cycle":           cycle,
                "timestamp_utc":   timestamp,
                "report_version":  "2.0-Aerothon2026",
                "inference_time_ms": round(inference_time_ms, 2),
            },

            # ── Health Overview ────────────────────────────────────────────────
            "health_overview": {
                "overall_health_pct":     round(overall_h, 2),
                "compressor_health_pct":  round(comp_h, 2),
                "combustor_health_pct":   round(comb_h, 2),
                "turbine_health_pct":     round(turb_h, 2),
                "thrust_kN":              round(thrust, 2),
                "tsfc_g_N_s":             round(tsfc, 5),
                "prediction_confidence":  round(confidence, 2),
            },

            # ── Hierarchical Health Tree ───────────────────────────────────────
            "health_tree": health_tree,

            # ── RUL Estimate ──────────────────────────────────────────────────
            "rul_estimate": {
                "rul_mean_cycles":   rul_mean,
                "rul_p10_cycles":    rul_p10,
                "rul_p90_cycles":    rul_p90,
                "rul_mean_hours":    round(rul_mean * 1.5, 1),
                "rul_p10_hours":     round(rul_p10 * 1.5, 1),
                "rul_p90_hours":     round(rul_p90 * 1.5, 1),
                "warning_level":     rul_warn,
                "confidence_pct":    float(rul_estimate.get("confidence", 90.0)),
                "regime":            rul_estimate.get("regime", "mid"),
            },

            # ── Causal Chain (SHAP + Physics) ─────────────────────────────────
            "causal_chain": causal_chain[:5],  # top 5 causes

            # ── Fleet Context ─────────────────────────────────────────────────
            "fleet_context": fleet_context,

            # ── Maintenance Priority ──────────────────────────────────────────
            "maintenance_assessment": {
                "priority_level":     maintenance_prognosis.get("severity", "LOW"),
                "risk_assessment":    maintenance_prognosis.get("risk_assessment", "Nominal"),
                "action_tier":        maintenance_prognosis.get("action_tier", "On-Condition Monitoring"),
                "recommended_inspections": maintenance_prognosis.get("failure_modes_detected", []),
                "estimated_downtime_hrs": maintenance_prognosis.get("estimated_downtime_hrs", 0),
            },

            # ── Physics Validation ────────────────────────────────────────────
            "physics_validation": {
                "is_envelope_compliant": physics_validation.get("is_envelope_compliant", True),
                "compliance_score_pct":  physics_validation.get("compliance_score_pct", 100.0),
                "violation_count":       physics_validation.get("violation_count", 0),
                "violations":            physics_validation.get("violations", []),
                "physics_constrained":   physics_validation.get("physics_constrained", False),
            },

            # ── Uncertainty Decomposition ─────────────────────────────────────
            "uncertainty_breakdown": uncertainty_breakdown,

            # ── Engineering Narrative ─────────────────────────────────────────
            "engineering_narrative": engineering_narrative,
        }

        return report

    @staticmethod
    def to_json(report: Dict, indent: int = 2) -> str:
        """Serializes report to a JSON string."""
        return json.dumps(report, indent=indent, default=str)

    @staticmethod
    def to_csv(report: Dict) -> str:
        """
        Generates a flat CSV summary of the key report fields.
        Suitable for tabular analysis and spreadsheet import.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        meta = report.get("report_metadata", {})
        health = report.get("health_overview", {})
        rul    = report.get("rul_estimate", {})
        maint  = report.get("maintenance_assessment", {})
        phys   = report.get("physics_validation", {})

        headers = [
            "Engine ID", "Cycle", "Timestamp (UTC)",
            "Overall Health (%)", "Compressor Health (%)", "Combustor Health (%)", "Turbine Health (%)",
            "Thrust (kN)", "TSFC (g/N·s)", "Prediction Confidence (%)",
            "RUL Mean (cycles)", "RUL P10 (cycles)", "RUL P90 (cycles)",
            "RUL Mean (hours)", "Warning Level", "Regime",
            "Maintenance Priority", "Action Tier",
            "Physics Compliant", "Compliance Score (%)", "Violation Count",
        ]

        values = [
            meta.get("engine_id", ""),
            meta.get("cycle", ""),
            meta.get("timestamp_utc", ""),
            health.get("overall_health_pct", ""),
            health.get("compressor_health_pct", ""),
            health.get("combustor_health_pct", ""),
            health.get("turbine_health_pct", ""),
            health.get("thrust_kN", ""),
            health.get("tsfc_g_N_s", ""),
            health.get("prediction_confidence", ""),
            rul.get("rul_mean_cycles", ""),
            rul.get("rul_p10_cycles", ""),
            rul.get("rul_p90_cycles", ""),
            rul.get("rul_mean_hours", ""),
            rul.get("warning_level", ""),
            rul.get("regime", ""),
            maint.get("priority_level", ""),
            maint.get("action_tier", ""),
            phys.get("is_envelope_compliant", ""),
            phys.get("compliance_score_pct", ""),
            phys.get("violation_count", ""),
        ]

        writer.writerow(headers)
        writer.writerow(values)

        # Append causal chain as additional rows
        causal = report.get("causal_chain", [])
        if causal:
            writer.writerow([])
            writer.writerow(["CAUSAL CHAIN — Sensor", "Observation", "Physics Link",
                              "Subsystem Effect", "Health Effect", "Recommended Action"])
            for entry in causal:
                writer.writerow([
                    entry.get("sensor", ""),
                    entry.get("observation", ""),
                    entry.get("physics_link", ""),
                    entry.get("subsystem_effect", ""),
                    entry.get("health_effect", ""),
                    entry.get("action", ""),
                ])

        return output.getvalue()

    @staticmethod
    def to_text(report: Dict) -> str:
        """Generates a human-readable plain text report."""
        meta   = report.get("report_metadata", {})
        health = report.get("health_overview", {})
        rul    = report.get("rul_estimate", {})
        maint  = report.get("maintenance_assessment", {})
        phys   = report.get("physics_validation", {})
        narrative = report.get("engineering_narrative", "")

        lines = [
            "=" * 70,
            f"  AEROTWIN Ω — DIGITAL TWIN ENGINEERING REPORT",
            f"  Engine: {meta.get('engine_id','?')}  |  Cycle: {meta.get('cycle','?')}",
            f"  Generated: {meta.get('timestamp_utc','')}",
            "=" * 70,
            "",
            "── HEALTH OVERVIEW ─────────────────────────────────────────────────",
            f"  Overall Health:    {health.get('overall_health_pct','?')}%",
            f"  Compressor Health: {health.get('compressor_health_pct','?')}%",
            f"  Combustor Health:  {health.get('combustor_health_pct','?')}%",
            f"  Turbine Health:    {health.get('turbine_health_pct','?')}%",
            f"  Thrust:            {health.get('thrust_kN','?')} kN",
            f"  TSFC:              {health.get('tsfc_g_N_s','?')} g/N·s",
            f"  Confidence:        {health.get('prediction_confidence','?')}%",
            "",
            "── REMAINING USEFUL LIFE ───────────────────────────────────────────",
            f"  RUL Estimate:      {rul.get('rul_mean_cycles','?')} cycles  ({rul.get('rul_mean_hours','?')} flight hours)",
            f"  90% Interval:      [{rul.get('rul_p10_cycles','?')} – {rul.get('rul_p90_cycles','?')}] cycles",
            f"  Warning Level:     {rul.get('warning_level','?')}",
            f"  Life Regime:       {rul.get('regime','?')}",
            "",
            "── MAINTENANCE ASSESSMENT ──────────────────────────────────────────",
            f"  Priority:          {maint.get('priority_level','?')}",
            f"  Action Required:   {maint.get('action_tier','?')}",
            f"  Est. Downtime:     {maint.get('estimated_downtime_hrs','?')} hours",
            "",
            "── PHYSICS VALIDATION ──────────────────────────────────────────────",
            f"  Envelope Compliant:{phys.get('is_envelope_compliant','?')}",
            f"  Compliance Score:  {phys.get('compliance_score_pct','?')}%",
            f"  Violations:        {phys.get('violation_count','?')}",
            "",
            "── ENGINEERING NARRATIVE ───────────────────────────────────────────",
            "",
        ]

        if narrative:
            for para in narrative.split("\n\n"):
                lines.append(para)
                lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)

    @staticmethod
    def to_pdf_bytes(report: Dict) -> Optional[bytes]:
        """
        Generates a PDF report using ReportLab (if installed).
        Returns None if ReportLab is not available.
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.enums import TA_LEFT, TA_CENTER
        except ImportError:
            return None

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                 rightMargin=2*cm, leftMargin=2*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        meta   = report.get("report_metadata", {})
        health = report.get("health_overview", {})
        rul    = report.get("rul_estimate", {})
        maint  = report.get("maintenance_assessment", {})
        narrative = report.get("engineering_narrative", "")

        # Title
        title_style = ParagraphStyle("title", parent=styles["Heading1"],
                                      alignment=TA_CENTER, spaceAfter=12)
        story.append(Paragraph("AeroTwin Ω — Engineering Report", title_style))
        story.append(Paragraph(
            f"Engine {meta.get('engine_id','')} | Cycle {meta.get('cycle','')} | {meta.get('timestamp_utc','')}",
            styles["Normal"]
        ))
        story.append(Spacer(1, 0.5*cm))

        # Health table
        health_data = [
            ["Subsystem", "Health (%)"],
            ["Overall",    f"{health.get('overall_health_pct','?')}%"],
            ["Compressor", f"{health.get('compressor_health_pct','?')}%"],
            ["Combustor",  f"{health.get('combustor_health_pct','?')}%"],
            ["Turbine",    f"{health.get('turbine_health_pct','?')}%"],
        ]
        t = Table(health_data, colWidths=[7*cm, 7*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.grey),
            ("FONTSIZE",   (0,0), (-1,-1), 10),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))

        # RUL
        story.append(Paragraph(f"<b>RUL:</b> {rul.get('rul_mean_cycles','?')} cycles "
                                 f"({rul.get('rul_mean_hours','?')} hours) — {rul.get('warning_level','?')}",
                                 styles["Normal"]))
        story.append(Spacer(1, 0.3*cm))

        # Narrative
        story.append(Paragraph("<b>Engineering Assessment:</b>", styles["Heading3"]))
        for para in narrative.split("\n\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), styles["Normal"]))
                story.append(Spacer(1, 0.2*cm))

        doc.build(story)
        return buffer.getvalue()
