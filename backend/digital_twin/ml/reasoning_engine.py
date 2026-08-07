"""
reasoning_engine.py
===================
Engineering Reasoning Layer for Aerothon 2026 Digital Twin.

Generates natural-language narratives that sound like a Level-4 aerospace engineer.
Uses structured inputs (health tree, RUL, SHAP chain, fleet context) to produce
a coherent, quantitative, actionable engineering assessment.

No ML models here — pure physics-guided rule-based narrative assembly.
Every sentence is traceable to a specific sensor reading or physics equation.
"""

import math
from typing import Dict, List, Optional, Any


# ─── Engineering Thresholds ────────────────────────────────────────────────────
HEALTH_CRITICAL  = 72.0    # %
HEALTH_HIGH      = 83.0    # %
HEALTH_MEDIUM    = 92.0    # %
HEALTH_NOMINAL   = 97.0    # %

RUL_CRITICAL     = 30      # cycles
RUL_HIGH         = 80      # cycles
RUL_MEDIUM       = 150     # cycles

EPS = 1e-9


class EngineeringReasoningEngine:
    """
    Converts structured prediction data into a coherent engineering narrative.

    The narrative answers (in order):
      1. Engine identification and operating state
      2. Current health status and dominant subsystem
      3. Observed sensor anomalies and their physical interpretation
      4. Degradation trend (velocity and acceleration)
      5. Fleet comparison (peer percentile)
      6. Root cause assessment
      7. RUL estimate with confidence
      8. Recommended maintenance actions
      9. Priority level and urgency
    """

    @staticmethod
    def generate_narrative(
        engine_id: str,
        health_tree: Dict,
        rul_estimate: Dict,
        causal_chain: List[Dict],
        fleet_context: Dict,
        predictions: Dict,
        temporal_context: Dict,
        root_cause: Optional[Dict] = None,
    ) -> str:
        """
        Generates a full aerospace-grade engineering narrative.
        Returns a multi-paragraph plain-text report.
        """
        paragraphs = []

        # ── Paragraph 1: State Summary ─────────────────────────────────────────
        overall_h  = float(predictions.get("Overall Health", predictions.get("OverallHealth", 95.0)))
        comp_h     = float(predictions.get("Compressor Health", predictions.get("CompressorHealth", 97.0)))
        comb_h     = float(predictions.get("Combustor Health", predictions.get("CombustorHealth", 97.0)))
        turb_h     = float(predictions.get("Turbine Health", predictions.get("TurbineHealth", 97.0)))
        thrust     = float(predictions.get("Thrust", predictions.get("Thrust_N", 54.0)))
        tsfc       = float(predictions.get("TSFC", predictions.get("TSFC_g_N_s", 0.025)))

        subsystems = {"Compressor": comp_h, "Combustor": comb_h, "Turbine": turb_h}
        worst_sub  = min(subsystems, key=subsystems.get)
        worst_h    = subsystems[worst_sub]
        best_sub   = max(subsystems, key=subsystems.get)

        state_adj  = _health_adjective(overall_h)
        para1 = (
            f"Engine {engine_id} is currently operating in a {state_adj} state "
            f"with an overall health index of {overall_h:.1f}%. "
            f"The {worst_sub} is the limiting subsystem at {worst_h:.1f}%, "
            f"while the {best_sub} remains in good condition. "
            f"Current thrust output is {thrust:.1f} kN at a specific fuel consumption "
            f"of {tsfc:.4f} g/N·s."
        )
        paragraphs.append(para1)

        # ── Paragraph 2: Sensor Anomalies ─────────────────────────────────────
        anomaly_sentences = []
        for entry in causal_chain[:3]:
            sensor     = entry.get("sensor", "")
            observation = entry.get("observation", "")
            phys_link  = entry.get("physics_link", "")
            health_eff = entry.get("health_effect", "")
            if observation:
                anomaly_sentences.append(f"{observation}. {phys_link}. {health_eff}.")

        if anomaly_sentences:
            para2 = "Sensor analysis reveals the following anomalies: " + " ".join(anomaly_sentences)
        else:
            para2 = "All primary sensor readings are within nominal operating bounds. No significant anomalies detected."
        paragraphs.append(para2)

        # ── Paragraph 3: Degradation Trend ────────────────────────────────────
        slope     = float(temporal_context.get("OverallHealth_slope_per_cycle", 0.0))
        deg_rate  = abs(slope) * 100  # convert fraction to percentage points per cycle
        h_change  = float(temporal_context.get("OverallHealth_20cycle_change", 0.0)) * 100

        if slope < -0.001:
            trend_desc = f"degrading at {deg_rate:.3f} percentage points per cycle"
            if h_change < -3.0:
                trend_desc += f", with a cumulative loss of {abs(h_change):.1f} percentage points over the observed window"
        elif slope > 0.001:
            trend_desc = "recovering (health index improving)"
        else:
            trend_desc = "stable with no significant trend"

        accel = float(temporal_context.get("degradation_acceleration", 0.0)) * 100
        accel_str = ""
        if abs(accel) > 0.0001:
            accel_str = (
                f" Degradation is {'accelerating' if accel < 0 else 'decelerating'} "
                f"at {abs(accel):.4f} percentage points per cycle²."
            )

        para3 = f"Health trend analysis shows the engine is {trend_desc}.{accel_str}"
        paragraphs.append(para3)

        # ── Paragraph 4: Fleet Context ─────────────────────────────────────────
        peer_pct_faster = float(fleet_context.get("fleet_percentile_faster", 50.0))
        cluster_archetype = fleet_context.get("archetype", "Normal Degrader")
        n_similar = fleet_context.get("n_similar_engines", 0)
        confidence_from_density = fleet_context.get("dataset_density_pct", None)

        if peer_pct_faster > 60:
            peer_desc = f"degrading faster than {peer_pct_faster:.0f}% of fleet peers"
        elif peer_pct_faster < 40:
            peer_desc = f"degrading more slowly than {100-peer_pct_faster:.0f}% of fleet peers"
        else:
            peer_desc = "degrading at a rate consistent with fleet average"

        density_note = ""
        if confidence_from_density is not None:
            density_note = (
                f" This prediction is supported by {n_similar} similar engine signatures "
                f"in the training dataset (operating point density: {confidence_from_density:.0f}%)."
            )

        para4 = (
            f"Fleet comparison indicates this engine belongs to the '{cluster_archetype}' archetype "
            f"and is currently {peer_desc}.{density_note}"
        )
        paragraphs.append(para4)

        # ── Paragraph 5: Root Cause ────────────────────────────────────────────
        if root_cause:
            mechanism  = root_cause.get("primary_failure_mechanism", "Unknown")
            subsystem  = root_cause.get("primary_failure_subsystem", "Unknown")
            confidence = root_cause.get("confidence", 0.0)
            evidence   = root_cause.get("evidence", [])
            law        = root_cause.get("governing_law", "")
            pathway    = root_cause.get("failure_pathway", mechanism)

            evidence_str = " ".join(f"({ev})" for ev in evidence[:2])
            para5 = (
                f"Root cause analysis (confidence: {confidence*100:.0f}%) indicates "
                f"the primary failure mechanism is '{mechanism}' affecting the {subsystem} subsystem, "
                f"governed by {law}. "
                f"Failure pathway: {pathway}. {evidence_str}"
            )
            paragraphs.append(para5)

        # ── Paragraph 6: RUL Estimate ──────────────────────────────────────────
        rul_mean = int(rul_estimate.get("rul_mean", 200))
        rul_p10  = int(rul_estimate.get("rul_p10", 150))
        rul_p90  = int(rul_estimate.get("rul_p90", 250))
        rul_conf = float(rul_estimate.get("confidence", 90.0))
        rul_warn = rul_estimate.get("warning", "NORMAL")
        rul_regime = rul_estimate.get("regime", "mid")

        rul_hours = round(rul_mean * 1.5, 0)  # ~1.5 flight hours per cycle
        rul_p10_h = round(rul_p10 * 1.5, 0)
        rul_p90_h = round(rul_p90 * 1.5, 0)

        urgency_map = {
            "CRITICAL": "IMMEDIATE action is required.",
            "WARNING":  "Maintenance should be scheduled within the next 10 operating cycles.",
            "MONITOR":  "Continued monitoring is advised. Plan maintenance within 50 cycles.",
            "NORMAL":   "No immediate maintenance required. Continue on-condition monitoring.",
        }
        urgency = urgency_map.get(rul_warn, urgency_map["NORMAL"])

        para6 = (
            f"Remaining useful life estimate: {rul_mean} cycles ({rul_hours:.0f} flight hours) "
            f"with a 90% prediction interval of [{rul_p10}–{rul_p90}] cycles "
            f"([{rul_p10_h:.0f}–{rul_p90_h:.0f} flight hours]). "
            f"Model confidence: {rul_conf:.0f}%. "
            f"Engine is in the '{rul_regime}' life phase. {urgency}"
        )
        paragraphs.append(para6)

        # ── Paragraph 7: Maintenance Recommendations ───────────────────────────
        recs = _generate_recommendations(comp_h, comb_h, turb_h, overall_h, rul_warn, root_cause)
        if recs:
            para7 = "Recommended actions: " + "; ".join(recs) + "."
        else:
            para7 = "No specific maintenance actions required at this time. Routine on-condition monitoring (OAP) continues."
        paragraphs.append(para7)

        return "\n\n".join(paragraphs)

    @staticmethod
    def generate_brief(engine_id: str, predictions: Dict, rul_mean: int,
                        rul_warning: str, overall_trend: str) -> str:
        """
        Generates a short one-paragraph executive summary for dashboard display.
        """
        overall_h = float(predictions.get("Overall Health", predictions.get("OverallHealth", 95.0)))
        thrust    = float(predictions.get("Thrust", predictions.get("Thrust_N", 54.0)))
        state_adj = _health_adjective(overall_h)

        urgency_map = {
            "CRITICAL": f"⛔ IMMEDIATE GROUNDING — {rul_mean} cycles to failure.",
            "WARNING":  f"⚠️ Schedule maintenance within 10 cycles. RUL: {rul_mean} cycles.",
            "MONITOR":  f"🔶 Monitor closely. RUL: {rul_mean} cycles.",
            "NORMAL":   f"✅ Normal operation. RUL: {rul_mean} cycles.",
        }
        urgency_brief = urgency_map.get(rul_warning, urgency_map["NORMAL"])

        return (
            f"Engine {engine_id} — {state_adj.upper()} state ({overall_h:.1f}% health). "
            f"Thrust: {thrust:.1f} kN. Trend: {overall_trend}. {urgency_brief}"
        )


def _health_adjective(h: float) -> str:
    if h >= HEALTH_NOMINAL:
        return "fully nominal"
    elif h >= HEALTH_MEDIUM:
        return "slightly degraded"
    elif h >= HEALTH_HIGH:
        return "moderately degraded"
    elif h >= HEALTH_CRITICAL:
        return "severely degraded"
    else:
        return "critically degraded"


def _generate_recommendations(comp_h: float, comb_h: float, turb_h: float,
                                overall_h: float, rul_warn: str,
                                root_cause: Optional[Dict]) -> List[str]:
    """Physics-grounded maintenance recommendation generator."""
    recs = []

    if comp_h < HEALTH_CRITICAL:
        recs.append("Immediate borescope inspection of HPC stages 1–3 for blade damage, crack initiation, and TBC delamination")
    elif comp_h < HEALTH_MEDIUM:
        recs.append("Schedule compressor detergent wash and borescope inspection of HPC stage 1–3 within 20 cycles")

    if comb_h < HEALTH_CRITICAL:
        recs.append("Immediate fuel nozzle flow-check and combustor liner TBC thickness measurement (LIDAR profilometry)")
    elif comb_h < HEALTH_MEDIUM:
        recs.append("Flow-check fuel injectors and verify combustion liner TBC coating thickness within 30 cycles")

    if turb_h < HEALTH_CRITICAL:
        recs.append("Immediate HPT/LPT blade trailing edge creep measurement and cooling hole blockage check")
    elif turb_h < HEALTH_MEDIUM:
        recs.append("Schedule HPT blade inspection and cooling passage flow test within 30 cycles")

    if rul_warn == "CRITICAL":
        recs.insert(0, "Aircraft on Ground (AOG) until component inspection completed and airworthiness restored")
    elif rul_warn == "WARNING":
        recs.insert(0, "Schedule immediate unscheduled maintenance event (UME) within next 10 operating cycles")

    if root_cause:
        mechanism = root_cause.get("primary_failure_mechanism", "")
        if "Fouling" in mechanism:
            recs.append("Compressor water-detergent wash at next available ground stop")
        elif "EGT" in mechanism:
            recs.append("Reduce throttle margin by 3% and monitor T4 trend for the next 10 cycles")

    return recs[:5]  # cap at 5 recommendations
