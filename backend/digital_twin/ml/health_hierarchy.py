"""
health_hierarchy.py
===================
Hierarchical Health Tree Builder for the Aerothon 2026 Digital Twin.

Constructs an 11-node, 5-branch health tree from real-time telemetry and ML
predictions.  Each node exposes a normalised health value (0-100 %), a trend
label, a confidence estimate, the contributing sensor list, and an engineering
note so the cockpit dashboard can surface actionable diagnostics.

Tree topology
-------------
  Overall Health  (weighted aggregate)
  ├── Mechanical Health    (weight 0.40)
  │   ├── Compressor_Health              <- ML prediction
  │   └── Turbine_Health                 <- ML prediction
  ├── Thermal Health       (weight 0.25)
  │   ├── EGT_Margin_Health              <- T4_K vs. 1273 K material limit
  │   └── Combustor_Thermal_State        <- T3/T2 temperature ratio
  ├── Pressure Health      (weight 0.20)
  │   ├── Compressor_PR_Health           <- isentropic efficiency mapping
  │   └── Turbine_PR_Health              <- expansion ratio health
  ├── Combustion Health    (weight 0.10)
  │   └── Combustor_Health               <- ML prediction
  └── Efficiency Health    (weight 0.05)
      ├── Compressor_Isentropic_Efficiency_Health  <- eta_c -> 0-100 %
      └── Turbine_Work_Coefficient_Health          <- W    -> 0-100 %

Leaf-node engineering mappings
-------------------------------
  * ML predictions  : already in [0, 1]; multiply by 100 -> percentage.
  * EGT margin      : 100 % at margin >= 200 K; 0 % at margin <= 0 K; linear.
  * Combustor TR    : 100 % at TR = 6.5 (nominal); degrades as |TR-6.5|/6.5.
  * Isentropic eff  : 100 % at eta = 0.85; 0 % at eta < 0.50; linear between.
  * Work coefficient: 100 % at W = 0.45; 0 % at W < 0.20; linear between.

Trend classification (requires temporal_context)
-------------------------------------------------
  slope > +0.5 %/cycle  -> IMPROVING
  |slope| <= 0.5 %/cycle -> STABLE
  -2.0 < slope <= -0.5   -> DEGRADING
  slope <= -2.0 %/cycle  -> DEGRADING_FAST

Usage
-----
    builder = HealthHierarchyBuilder()
    tree    = builder.build(telemetry, predictions, temporal_context)
    path    = builder.get_critical_path(tree)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

# ==============================================================================
# Physical constants & engineering limits
# ==============================================================================

#: Single-crystal Ni-superalloy turbine inlet temperature limit (CMSX-4)
T4_LIMIT_K: float = 1273.0

#: Minimum safe EGT margin below which health -> 0 %
EGT_MARGIN_SAFE_K: float = 200.0

#: Nominal combustor temperature ratio (T3/T2) for a healthy engine
TR_NOMINAL: float = 6.5

#: Design-point compressor isentropic efficiency (eta_c = 0.85 -> 100 %)
ETA_C_NOMINAL: float = 0.85

#: Minimum isentropic efficiency below which health -> 0 %
ETA_C_MIN: float = 0.50

#: Nominal turbine work coefficient (W = (T3-T4)/T3 = 0.45 -> 100 %)
W_NOMINAL: float = 0.45

#: Minimum work coefficient below which health -> 0 %
W_MIN: float = 0.20

# Branch weights (must sum to 1.0)
BRANCH_WEIGHTS: Dict[str, float] = {
    "mechanical": 0.40,
    "thermal":    0.25,
    "pressure":   0.20,
    "combustion": 0.10,
    "efficiency": 0.05,
}

# Trend thresholds in %/cycle (positive = improvement)
_TREND_IMPROVING_THRESH: float = 0.5
_TREND_DEGRADING_THRESH: float = -0.5
_TREND_FAST_THRESH:      float = -2.0

# Type alias
HealthNode = Dict[str, Any]


# ==============================================================================
# Helper utilities
# ==============================================================================

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp *value* to the closed interval [lo, hi]."""
    return max(lo, min(hi, value))


def _trend_from_slope(slope: Optional[float]) -> str:
    """
    Classify a per-cycle health slope (in percentage points / cycle) into one
    of four trend labels.

    Parameters
    ----------
    slope : float or None
        Gradient of the health time-series in %/cycle.
        ``None`` or ``math.nan`` -> ``'STABLE'``.

    Returns
    -------
    str
        One of ``'IMPROVING'``, ``'STABLE'``, ``'DEGRADING'``,
        ``'DEGRADING_FAST'``.
    """
    if slope is None or math.isnan(slope):
        return "STABLE"
    if slope > _TREND_IMPROVING_THRESH:
        return "IMPROVING"
    if slope <= _TREND_FAST_THRESH:
        return "DEGRADING_FAST"
    if slope <= _TREND_DEGRADING_THRESH:
        return "DEGRADING"
    return "STABLE"


def _make_node(
    name: str,
    value: float,
    slope: Optional[float],
    confidence: float,
    sensors: List[str],
    engineering_note: str,
    children: Optional[List[HealthNode]] = None,
) -> HealthNode:
    """
    Construct a single health-tree node dictionary.

    Parameters
    ----------
    name : str
        Human-readable identifier for the node.
    value : float
        Health percentage in [0, 100].
    slope : float or None
        Health trend slope in %/cycle (from temporal context).
    confidence : float
        Model confidence in [0, 1].
    sensors : list[str]
        Sensor tags that contributed to this node's computation.
    engineering_note : str
        Plain-English interpretation for the cockpit display.
    children : list[HealthNode] or None
        Child nodes; omit for leaf nodes.

    Returns
    -------
    HealthNode
        Dictionary with standardised keys.
    """
    node: HealthNode = {
        "name":                  name,
        "value":                 round(_clamp(value), 2),
        "trend":                 _trend_from_slope(slope),
        "confidence":            round(_clamp(confidence, 0.0, 1.0), 4),
        "contributing_sensors":  sensors,
        "engineering_note":      engineering_note,
    }
    if children is not None:
        node["children"] = children
    return node


def _safe_get(d: dict, *keys: str, default: float = 0.0) -> float:
    """Return the first key found in *d* cast to float, else *default*."""
    for k in keys:
        if k in d and d[k] is not None:
            try:
                return float(d[k])
            except (TypeError, ValueError):
                continue
    return default


# ==============================================================================
# Leaf-node health mapping functions
# ==============================================================================

def _ml_to_health(raw: float) -> float:
    """
    Convert an ML model output (fraction in [0, 1]) to a health percentage.

    Values in [0, 5] are treated as fractions and multiplied by 100.
    Values already in percent (> 5) are used directly.
    """
    if raw <= 5.0:
        return _clamp(raw * 100.0)
    return _clamp(raw)


def _egt_margin_health(t4_k: float) -> float:
    """
    Map current T4 to an EGT-margin health percentage.

    Health = clamp(margin / 200 * 100, 0, 100)
    where margin = T4_LIMIT_K - T4_K.

    * 100 % when margin >= 200 K (at least 200 K below limit)
    * 0 %   when margin <= 0 K  (at or above the material limit)

    Parameters
    ----------
    t4_k : float
        Measured turbine exit temperature in Kelvin.
    """
    margin = T4_LIMIT_K - t4_k
    return _clamp((margin / EGT_MARGIN_SAFE_K) * 100.0)


def _combustor_tr_health(t3_k: float, t2_k: float) -> float:
    """
    Map the combustor temperature ratio (T3/T2) to a health percentage.

    Health = clamp((1 - |TR - 6.5| / 6.5) * 100, 0, 100)

    * 100 % at TR = 6.5 (nominal design point)
    * 0 %   when deviation reaches 100 % of nominal (TR = 0 or TR = 13)

    Parameters
    ----------
    t3_k : float
        Combustor exit temperature in Kelvin.
    t2_k : float
        Compressor exit temperature in Kelvin.
    """
    if t2_k <= 0.0:
        return 50.0  # undefined -> neutral fallback
    tr = t3_k / t2_k
    deviation_fraction = abs(tr - TR_NOMINAL) / TR_NOMINAL
    return _clamp((1.0 - deviation_fraction) * 100.0)


def _isentropic_eff_health(eta_c: float) -> float:
    """
    Map compressor isentropic efficiency to a health percentage.

    Linear scale:
    * 100 % at eta_c = 0.85 (nominal design point)
    * 0 %   at eta_c <= 0.50 (severe degradation threshold)

    Parameters
    ----------
    eta_c : float
        Isentropic efficiency (dimensionless, typically 0.5 - 0.95).
    """
    return _clamp((eta_c - ETA_C_MIN) / (ETA_C_NOMINAL - ETA_C_MIN) * 100.0)


def _turbine_pr_health(pr_turbine: float) -> float:
    """
    Map the turbine expansion ratio to a health percentage.

    Nominal expansion ratio for a modern turbofan turbine stage is ~5.0.
    Health degrades linearly as |PR - 5| / 5 increases.

    Parameters
    ----------
    pr_turbine : float
        Turbine pressure ratio P3/P4 (expansion ratio, dimensionless).
    """
    PR_NOMINAL = 5.0
    deviation = abs(pr_turbine - PR_NOMINAL) / PR_NOMINAL
    return _clamp((1.0 - deviation) * 100.0)


def _compressor_pr_health(pr_compressor: float) -> float:
    """
    Map the compressor pressure ratio to a health percentage.

    Nominal PR is ~12 for a high-bypass turbofan.
    Deviations beyond the nominal indicate blade erosion or fouling.

    Parameters
    ----------
    pr_compressor : float
        Compressor pressure ratio P3/P2 (dimensionless).
    """
    PR_NOMINAL = 12.0
    deviation = abs(pr_compressor - PR_NOMINAL) / PR_NOMINAL
    return _clamp((1.0 - deviation) * 100.0)


def _work_coefficient_health(w: float) -> float:
    """
    Map turbine work coefficient W = (T3 - T4) / T3 to a health percentage.

    Linear scale:
    * 100 % at W = 0.45 (nominal design point)
    * 0 %   at W <= 0.20 (minimum useful work threshold)

    Parameters
    ----------
    w : float
        Turbine work coefficient (dimensionless, typically 0.20 - 0.55).
    """
    return _clamp((w - W_MIN) / (W_NOMINAL - W_MIN) * 100.0)


# ==============================================================================
# Main builder class
# ==============================================================================

class HealthHierarchyBuilder:
    """
    Build and analyse the hierarchical health tree for an Aerothon 2026 engine.

    The builder is stateless; each call to :meth:`build` returns an independent
    snapshot tree.

    Example
    -------
    >>> builder = HealthHierarchyBuilder()
    >>> tree = builder.build(telemetry, predictions, temporal_context)
    >>> critical = builder.get_critical_path(tree)
    >>> print(critical["branch"], critical["branch_health"])
    thermal 72.3
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        telemetry: dict,
        predictions: dict,
        temporal_context: Optional[dict] = None,
    ) -> HealthNode:
        """
        Construct the 11-node hierarchical health tree.

        Parameters
        ----------
        telemetry : dict
            Raw (or pre-normalised) sensor readings.  Expected keys:
            ``T2_K``, ``T3_K``, ``T4_K``, ``P2_Pa``, ``P3_Pa``, ``P4_Pa``,
            ``Tamb_K``, ``Pamb_Pa``, ``RPM_rev_min``, ``FuelFlow_kg_s``.
        predictions : dict
            Output from :class:`health_predictor.HealthPredictor`.  Expected
            keys: ``'Compressor Health'``, ``'Combustor Health'``,
            ``'Turbine Health'``, ``'Overall Health'``,
            ``'Prediction Confidence'``.
        temporal_context : dict or None
            Optional dictionary produced by the temporal-feature pipeline.
            When present, slopes under the ``'slopes'`` key drive trend labels.
            Expected structure (all values are %/cycle)::

                {
                    "slopes": {
                        "CompressorHealth": -0.8,
                        "TurbineHealth":    -0.3,
                        "CombustorHealth":  -0.1,
                        "EGT_Margin_K":     -1.5,
                        "TR_combustor":      0.0,
                        "PR_compressor":    -0.4,
                        "PR_turbine":       -0.2,
                        "Compressor_Isentropic_Eff": -0.6,
                        "Work_Coefficient": -0.9,
                        "OverallHealth":    -0.5,
                    }
                }

        Returns
        -------
        HealthNode
            Root node of the 11-node tree (1 overall + 5 branch + 9 leaf).
            Every node carries: ``name``, ``value`` (0-100), ``trend``,
            ``confidence``, ``contributing_sensors``, ``engineering_note``,
            and (for branch / root nodes) ``children``.

        Raises
        ------
        TypeError
            If *telemetry* or *predictions* is not a mapping.
        """
        if not isinstance(telemetry, dict):
            raise TypeError(
                f"telemetry must be a dict, got {type(telemetry).__name__}"
            )
        if not isinstance(predictions, dict):
            raise TypeError(
                f"predictions must be a dict, got {type(predictions).__name__}"
            )

        slopes = (temporal_context or {}).get("slopes", {})
        pred_confidence = _safe_get(predictions, "Prediction Confidence") / 100.0

        # ── Extract telemetry ──────────────────────────────────────────────
        t2   = _safe_get(telemetry, "T2_K",    default=300.0)
        t3   = _safe_get(telemetry, "T3_K",    default=1700.0)
        t4   = _safe_get(telemetry, "T4_K",    default=1000.0)
        p2   = _safe_get(telemetry, "P2_Pa",   default=500_000.0)
        p3   = _safe_get(telemetry, "P3_Pa",   default=2_400_000.0)
        p4   = _safe_get(telemetry, "P4_Pa",   default=120_000.0)
        tamb = _safe_get(telemetry, "Tamb_K",  default=228.0)

        # ── Derived physics quantities ─────────────────────────────────────
        pr_compressor = p3 / max(p2, 1e-9)
        pr_turbine    = p3 / max(p4, 1e-9)

        # Isentropic compressor efficiency
        gamma = 1.4
        isentropic_term = max(0.0, pr_compressor ** ((gamma - 1) / gamma) - 1.0)
        eta_c = (t2 - tamb) / max(isentropic_term * tamb, 1e-9)
        eta_c = max(0.0, min(1.5, eta_c))  # physical plausibility clamp

        # Turbine work coefficient  W = (T3 - T4) / T3
        w_coeff = (t3 - t4) / max(t3, 1e-9)

        # ── ML predictions ─────────────────────────────────────────────────
        comp_raw = _safe_get(predictions, "Compressor Health", default=0.98)
        turb_raw = _safe_get(predictions, "Turbine Health",    default=0.96)
        comb_raw = _safe_get(predictions, "Combustor Health",  default=0.97)

        # ── Leaf nodes ─────────────────────────────────────────────────────

        # --- Mechanical ---
        leaf_compressor = _make_node(
            name="Compressor_Health",
            value=_ml_to_health(comp_raw),
            slope=slopes.get("CompressorHealth"),
            confidence=min(pred_confidence + 0.02, 0.99),
            sensors=["P2_Pa", "P3_Pa", "T2_K", "RPM_rev_min"],
            engineering_note=(
                "ML ensemble prediction of compressor blade and seal health.  "
                "Values below 85 % indicate measurable aerodynamic degradation; "
                "below 70 % suggest imminent maintenance action."
            ),
        )

        leaf_turbine = _make_node(
            name="Turbine_Health",
            value=_ml_to_health(turb_raw),
            slope=slopes.get("TurbineHealth"),
            confidence=min(pred_confidence + 0.01, 0.99),
            sensors=["P3_Pa", "P4_Pa", "T3_K", "T4_K"],
            engineering_note=(
                "ML ensemble prediction of turbine blade, disk, and shroud health.  "
                "Creep and oxidation are primary degradation mechanisms at high T4."
            ),
        )

        # --- Thermal ---
        egt_health = _egt_margin_health(t4)
        leaf_egt_margin = _make_node(
            name="EGT_Margin_Health",
            value=egt_health,
            slope=slopes.get("EGT_Margin_K"),
            confidence=0.96,
            sensors=["T4_K"],
            engineering_note=(
                f"EGT margin = {(T4_LIMIT_K - t4):.1f} K "
                f"(limit {T4_LIMIT_K:.0f} K, safe margin {EGT_MARGIN_SAFE_K:.0f} K).  "
                "Margins below 50 K demand immediate power reduction or shutdown."
            ),
        )

        tr_health = _combustor_tr_health(t3, t2)
        leaf_comb_tr = _make_node(
            name="Combustor_Thermal_State",
            value=tr_health,
            slope=slopes.get("TR_combustor"),
            confidence=0.93,
            sensors=["T3_K", "T2_K"],
            engineering_note=(
                f"Combustor temperature ratio T3/T2 = {(t3 / max(t2, 1e-9)):.2f} "
                f"(nominal {TR_NOMINAL}).  "
                "Deviations indicate fuel scheduling errors or liner degradation."
            ),
        )

        # --- Pressure ---
        cpr_health = _compressor_pr_health(pr_compressor)
        leaf_comp_pr = _make_node(
            name="Compressor_PR_Health",
            value=cpr_health,
            slope=slopes.get("PR_compressor"),
            confidence=0.95,
            sensors=["P2_Pa", "P3_Pa"],
            engineering_note=(
                f"Compressor PR = {pr_compressor:.2f} (nominal 12.0).  "
                "Pressure ratio drop correlates with blade erosion or fouling."
            ),
        )

        tpr_health = _turbine_pr_health(pr_turbine)
        leaf_turb_pr = _make_node(
            name="Turbine_PR_Health",
            value=tpr_health,
            slope=slopes.get("PR_turbine"),
            confidence=0.94,
            sensors=["P3_Pa", "P4_Pa"],
            engineering_note=(
                f"Turbine expansion ratio P3/P4 = {pr_turbine:.2f} (nominal 5.0).  "
                "Low expansion ratio suggests nozzle blockage or tip-seal wear."
            ),
        )

        # --- Combustion ---
        leaf_combustor = _make_node(
            name="Combustor_Health",
            value=_ml_to_health(comb_raw),
            slope=slopes.get("CombustorHealth"),
            confidence=min(pred_confidence, 0.97),
            sensors=["T3_K", "P3_Pa", "FuelFlow_kg_s"],
            engineering_note=(
                "ML prediction of combustor liner, fuel nozzle, and igniter health.  "
                "Rich-quench-lean staging stability is the primary failure mode."
            ),
        )

        # --- Efficiency ---
        eta_health = _isentropic_eff_health(eta_c)
        leaf_eta_c = _make_node(
            name="Compressor_Isentropic_Efficiency_Health",
            value=eta_health,
            slope=slopes.get("Compressor_Isentropic_Eff"),
            confidence=0.91,
            sensors=["T2_K", "Tamb_K", "P2_Pa", "Pamb_Pa"],
            engineering_note=(
                f"Isentropic efficiency eta_c = {eta_c:.3f} "
                f"(100 % at eta={ETA_C_NOMINAL}, 0 % at eta<={ETA_C_MIN}).  "
                "Efficiency drop below 0.75 implies significant blade fouling."
            ),
        )

        w_health = _work_coefficient_health(w_coeff)
        leaf_work = _make_node(
            name="Turbine_Work_Coefficient_Health",
            value=w_health,
            slope=slopes.get("Work_Coefficient"),
            confidence=0.90,
            sensors=["T3_K", "T4_K"],
            engineering_note=(
                f"Turbine work coefficient W = {w_coeff:.3f} "
                f"(nominal {W_NOMINAL}, min {W_MIN}).  "
                "Low W indicates hot-section cooling flow leakage or turbine seal wear."
            ),
        )

        # ── Branch nodes ───────────────────────────────────────────────────

        branch_mechanical = self._branch(
            name="Mechanical_Health",
            children=[leaf_compressor, leaf_turbine],
            weights=[0.55, 0.45],
            slope=slopes.get("CompressorHealth"),
            confidence=min(pred_confidence + 0.01, 0.99),
            sensors=["P2_Pa", "P3_Pa", "P4_Pa", "T2_K", "T3_K", "T4_K", "RPM_rev_min"],
            note=(
                "Mechanical sub-system health dominated by compressor and turbine "
                "rotor integrity.  Mechanical degradation is the highest-cost failure mode."
            ),
        )

        branch_thermal = self._branch(
            name="Thermal_Health",
            children=[leaf_egt_margin, leaf_comb_tr],
            weights=[0.60, 0.40],
            slope=slopes.get("EGT_Margin_K"),
            confidence=0.95,
            sensors=["T2_K", "T3_K", "T4_K"],
            note=(
                "Thermal health is safety-critical: EGT over-temperature can cause "
                "irreversible turbine blade melting within seconds of exceedance."
            ),
        )

        branch_pressure = self._branch(
            name="Pressure_Health",
            children=[leaf_comp_pr, leaf_turb_pr],
            weights=[0.55, 0.45],
            slope=slopes.get("PR_compressor"),
            confidence=0.94,
            sensors=["P2_Pa", "P3_Pa", "P4_Pa", "Pamb_Pa"],
            note=(
                "Pressure health tracks the thermodynamic work potential of each stage.  "
                "A falling trend may precede compressor surge or turbine choke."
            ),
        )

        branch_combustion = self._branch(
            name="Combustion_Health",
            children=[leaf_combustor],
            weights=[1.0],
            slope=slopes.get("CombustorHealth"),
            confidence=min(pred_confidence, 0.97),
            sensors=["T3_K", "P3_Pa", "FuelFlow_kg_s"],
            note=(
                "Combustor health directly impacts NOx emissions, relight capability, "
                "and hot-section durability."
            ),
        )

        branch_efficiency = self._branch(
            name="Efficiency_Health",
            children=[leaf_eta_c, leaf_work],
            weights=[0.50, 0.50],
            slope=slopes.get("Compressor_Isentropic_Eff"),
            confidence=0.91,
            sensors=["T2_K", "T3_K", "T4_K", "Tamb_K", "P2_Pa", "Pamb_Pa"],
            note=(
                "Efficiency health captures thermodynamic cycle losses.  "
                "Degradation here increases TSFC and reduces specific thrust."
            ),
        )

        # ── Root node ──────────────────────────────────────────────────────

        branch_list = [
            (branch_mechanical, BRANCH_WEIGHTS["mechanical"]),
            (branch_thermal,    BRANCH_WEIGHTS["thermal"]),
            (branch_pressure,   BRANCH_WEIGHTS["pressure"]),
            (branch_combustion, BRANCH_WEIGHTS["combustion"]),
            (branch_efficiency, BRANCH_WEIGHTS["efficiency"]),
        ]

        overall_value = sum(b["value"] * w for b, w in branch_list)
        overall_conf  = sum(b["confidence"] * w for b, w in branch_list)

        # Deduplicated sensor list for the root
        all_sensors: List[str] = []
        seen: set = set()
        for b, _ in branch_list:
            for s in b["contributing_sensors"]:
                if s not in seen:
                    all_sensors.append(s)
                    seen.add(s)

        root = _make_node(
            name="Overall_Health",
            value=overall_value,
            slope=slopes.get("OverallHealth"),
            confidence=overall_conf,
            sensors=all_sensors,
            engineering_note=(
                "Weighted aggregate: "
                f"mechanical x{BRANCH_WEIGHTS['mechanical']:.2f} + "
                f"thermal x{BRANCH_WEIGHTS['thermal']:.2f} + "
                f"pressure x{BRANCH_WEIGHTS['pressure']:.2f} + "
                f"combustion x{BRANCH_WEIGHTS['combustion']:.2f} + "
                f"efficiency x{BRANCH_WEIGHTS['efficiency']:.2f}.  "
                "Values below 80 % require engineering review; "
                "below 65 % require ground maintenance before next dispatch."
            ),
            children=[
                branch_mechanical,
                branch_thermal,
                branch_pressure,
                branch_combustion,
                branch_efficiency,
            ],
        )

        return root

    # ------------------------------------------------------------------

    def get_critical_path(self, health_tree: HealthNode) -> Dict[str, Any]:
        """
        Identify the branch contributing most to overall health degradation.

        The critical branch is the one with the largest *weighted degradation
        contribution*:

            contribution_i = (100 - branch_health_i) * weight_i

        Parameters
        ----------
        health_tree : HealthNode
            Root node returned by :meth:`build`.

        Returns
        -------
        dict
            Keys:

            ``branch`` : str
                Internal branch key (``'mechanical'``, ``'thermal'``, ...).
            ``branch_node_name`` : str
                Human-readable node name.
            ``branch_health`` : float
                Branch health value in [0, 100] %.
            ``branch_weight`` : float
                Normalised weight in overall health.
            ``weighted_degradation`` : float
                (100 - branch_health) * branch_weight.
            ``limiting_leaf`` : HealthNode or None
                The child node with the lowest health value.
            ``recommendation`` : str
                Brief engineering recommendation.

        Raises
        ------
        KeyError
            If *health_tree* does not contain a ``'children'`` key.
        """
        if "children" not in health_tree:
            raise KeyError(
                "get_critical_path() requires the root HealthNode returned by build()."
            )

        branches = health_tree["children"]
        best: Optional[Dict[str, Any]] = None
        best_contrib = -1.0

        for branch_node in branches:
            bkey = _resolve_branch_key(branch_node["name"])
            weight = BRANCH_WEIGHTS.get(bkey, 0.0)
            contribution = (100.0 - branch_node["value"]) * weight

            if contribution > best_contrib:
                best_contrib = contribution
                limiting_leaf = _find_worst_child(branch_node)
                best = {
                    "branch":               bkey,
                    "branch_node_name":     branch_node["name"],
                    "branch_health":        branch_node["value"],
                    "branch_weight":        weight,
                    "weighted_degradation": round(contribution, 4),
                    "limiting_leaf":        limiting_leaf,
                    "recommendation":       _build_recommendation(
                                                bkey, branch_node, limiting_leaf
                                            ),
                }

        return best  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _branch(
        name: str,
        children: List[HealthNode],
        weights: List[float],
        slope: Optional[float],
        confidence: float,
        sensors: List[str],
        note: str,
    ) -> HealthNode:
        """
        Compute a branch node as a weighted average of its children.

        Parameters
        ----------
        name : str
            Branch node name.
        children : list[HealthNode]
            Leaf nodes under this branch.
        weights : list[float]
            Relative weights for each child (need not sum to 1.0; normalised
            internally).
        slope : float or None
            Trend slope for the branch in %/cycle.
        confidence : float
            Confidence in [0, 1].
        sensors : list[str]
            Sensor tags contributing to this branch.
        note : str
            Engineering note for the cockpit display.

        Returns
        -------
        HealthNode
        """
        assert len(children) == len(weights), (
            f"Branch '{name}': {len(children)} children but {len(weights)} weights"
        )
        total_w = sum(weights)
        norm_w  = [w / total_w for w in weights]
        value   = sum(c["value"] * nw for c, nw in zip(children, norm_w))
        return _make_node(
            name=name,
            value=value,
            slope=slope,
            confidence=confidence,
            sensors=sensors,
            engineering_note=note,
            children=children,
        )


# ==============================================================================
# Module-level utilities for get_critical_path
# ==============================================================================

def _resolve_branch_key(node_name: str) -> str:
    """
    Map a branch node name to its BRANCH_WEIGHTS key by prefix matching.

    'Mechanical_Health' -> 'mechanical', etc.
    """
    name_lower = node_name.lower()
    for key in BRANCH_WEIGHTS:
        if key in name_lower:
            return key
    return name_lower


def _find_worst_child(branch_node: HealthNode) -> Optional[HealthNode]:
    """Return the child node with the minimum ``value`` under *branch_node*."""
    children = branch_node.get("children")
    if not children:
        return None
    return min(children, key=lambda n: n["value"])


def _build_recommendation(
    branch_key: str,
    branch_node: HealthNode,
    limiting_leaf: Optional[HealthNode],
) -> str:
    """
    Generate a brief, context-aware maintenance recommendation.

    Parameters
    ----------
    branch_key : str
        BRANCH_WEIGHTS key identifying the degraded branch.
    branch_node : HealthNode
        Branch node (for health value context).
    limiting_leaf : HealthNode or None
        The worst child node under the branch.

    Returns
    -------
    str
        One-line engineering recommendation.
    """
    leaf_name = limiting_leaf["name"] if limiting_leaf else "N/A"
    leaf_val  = limiting_leaf["value"] if limiting_leaf else 0.0

    _recs: Dict[str, str] = {
        "mechanical": (
            f"Schedule borescope inspection of rotors.  "
            f"Limiting subsystem: {leaf_name} at {leaf_val:.1f} %.  "
            "Check for tip clearance degradation and FOD damage."
        ),
        "thermal": (
            f"Monitor EGT trends closely.  "
            f"Limiting subsystem: {leaf_name} at {leaf_val:.1f} %.  "
            "Verify cooling air supply and fuel scheduling trim."
        ),
        "pressure": (
            f"Investigate pressure ratio anomaly.  "
            f"Limiting subsystem: {leaf_name} at {leaf_val:.1f} %.  "
            "Check for compressor fouling or turbine nozzle blockage."
        ),
        "combustion": (
            f"Combustor health at {branch_node['value']:.1f} %.  "
            "Inspect fuel nozzle spray patterns and liner hot spots; "
            "verify igniter condition."
        ),
        "efficiency": (
            f"Thermodynamic efficiency declining.  "
            f"Limiting subsystem: {leaf_name} at {leaf_val:.1f} %.  "
            "Check compressor wash schedule and turbine seal condition."
        ),
    }

    return _recs.get(
        branch_key,
        (
            f"Branch '{branch_key}' health at {branch_node['value']:.1f} %.  "
            "Consult engine health-management (EHM) system for detailed diagnostics."
        ),
    )
