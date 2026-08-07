"""
fleet_analytics.py
==================
Fleet-Level Intelligence for Aerothon 2026.

Analyzes cross-engine degradation patterns across all 100 engines to discover:
  - Engine clusters (degradation archetypes)
  - Root cause failure mechanisms (automatic per engine)
  - Engine similarity search (nearest neighbor in feature space)
  - Sensor degradation ordering (which sensor degrades first)
  - Critical operating envelope (conditions → fastest degradation)
  - Failure precursors (patterns N cycles before threshold crossing)
  - Fleet health distribution by life phase

All analyses are physics-grounded and interpretable.
"""

import os
import json
import numpy as np
import pandas as pd
import warnings
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

warnings.filterwarnings("ignore")

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.linear_model import LinearRegression
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False

EPS = 1e-9
HEALTH_CRITICAL_THRESHOLD = 0.70
HEALTH_WARNING_THRESHOLD  = 0.85

# Failure mechanism signatures (physics-based rules)
FAILURE_SIGNATURES = {
    "Compressor Fouling": {
        "primary_sensor": "PR_compressor",
        "direction": "decreasing",
        "description": "Compressor pressure ratio decline — blade fouling/erosion reducing stage efficiency",
        "governing_law": "Sand/salt particle impact wear (Finnie, 1960)",
    },
    "Combustor Efficiency Loss": {
        "primary_sensor": "TR_combustor",
        "direction": "decreasing",
        "description": "Combustor temperature ratio decline — fuel nozzle coking or TBC spallation",
        "governing_law": "Thermal fatigue cycling (Coffin-Manson law)",
    },
    "Turbine Thermal Damage": {
        "primary_sensor": "Work_Coefficient",
        "direction": "decreasing",
        "description": "Turbine work coefficient decline — HPT blade creep or TBC oxidation",
        "governing_law": "Larson-Miller creep parameter",
    },
    "EGT Exceedance": {
        "primary_sensor": "EGT_Margin_K",
        "direction": "decreasing",
        "description": "Exhaust gas temperature approaching material limit — accelerated thermal aging",
        "governing_law": "Arrhenius thermal degradation kinetics",
    },
    "Multi-subsystem": {
        "primary_sensor": "Health_Divergence",
        "direction": "increasing",
        "description": "Multiple subsystems degrading simultaneously — systemic wear or contamination event",
        "governing_law": "Concurrent failure mode interaction",
    },
}

CLUSTER_ARCHETYPES = {
    0: "Slow Degrader",
    1: "Normal Degrader",
    2: "Fast Degrader",
    3: "Anomalous Pattern",
}


class FleetAnalytics:
    """
    Cross-engine fleet intelligence system for 100-engine × 300-cycle dataset.

    Provides:
      1. Engine clustering by degradation archetype
      2. Automatic root cause failure mechanism classification
      3. Engine similarity search (cosine nearest-neighbor)
      4. Sensor degradation ordering across fleet
      5. Critical operating envelope analysis
      6. Failure precursor detection
      7. Fleet health distribution by life phase
    """

    def __init__(self):
        self.is_fitted_ = False
        self._engine_features: Optional[pd.DataFrame] = None  # per-engine summary features
        self._engine_trajectories: Optional[Dict] = None      # health over time per engine
        self._cluster_model: Optional[object] = None
        self._scaler: Optional[object] = None
        self._engine_clusters: Dict[str, int] = {}
        self._engine_root_causes: Dict[str, Dict] = {}
        self._sensor_degradation_order: List[Dict] = []
        self._failure_precursors: Optional[Dict] = None
        self._dataset_df: Optional[pd.DataFrame] = None

    def fit(self, df: pd.DataFrame) -> "FleetAnalytics":
        """
        Fit fleet analytics on the complete dataset.
        df must contain: EngineID, Cycle, sensor cols, health cols.
        """
        self._dataset_df = df.copy()
        self._extract_engine_features(df)
        self._cluster_engines()
        self._classify_root_causes(df)
        self._compute_sensor_degradation_order(df)
        self._detect_failure_precursors(df)
        self.is_fitted_ = True
        print(f"[FleetAnalytics] Fitted on {df['EngineID'].nunique()} engines, {len(df)} total observations.")
        return self

    # ── 1. Engine Feature Extraction ──────────────────────────────────────────
    def _extract_engine_features(self, df: pd.DataFrame):
        """
        Compute per-engine summary features for clustering and similarity search.
        Features are degradation-trajectory descriptors, not time-indexed.
        """
        records = []
        for eng_id, grp in df.groupby("EngineID"):
            grp = grp.sort_values("Cycle") if "Cycle" in grp.columns else grp
            rec = {"EngineID": str(eng_id)}

            # Final health values (end-of-life state)
            for hcol in ["CompressorHealth", "CombustorHealth", "TurbineHealth", "OverallHealth"]:
                if hcol in grp.columns:
                    rec[f"final_{hcol}"] = float(grp[hcol].iloc[-1])
                    rec[f"min_{hcol}"]   = float(grp[hcol].min())

            # Health degradation rate (total drop / number of cycles)
            if "OverallHealth" in grp.columns:
                h = grp["OverallHealth"].values
                rec["overall_deg_rate"]    = float((h[0] - h[-1]) / max(1, len(h)))
                rec["max_single_drop"]     = float(-np.diff(h).clip(max=0).min()) if len(h) > 1 else 0.0
                rec["deg_acceleration"]    = float(np.diff(np.diff(h)).mean()) if len(h) > 2 else 0.0
                rec["health_stability"]    = float(np.std(np.diff(h))) if len(h) > 1 else 0.0

            # Thermal loading profile
            for scol in ["T3_K", "T4_K"]:
                if scol in grp.columns:
                    rec[f"{scol}_mean"]   = float(grp[scol].mean())
                    rec[f"{scol}_max"]    = float(grp[scol].max())
                    rec[f"{scol}_trend"]  = float(np.polyfit(np.arange(len(grp)), grp[scol].values, 1)[0]) if len(grp) > 2 else 0.0

            # Pressure loading profile
            for pcol in ["P3_Pa", "P2_Pa"]:
                if pcol in grp.columns:
                    rec[f"{pcol}_mean"]   = float(grp[pcol].mean())

            # Pressure ratio trend
            if "P3_Pa" in grp.columns and "P2_Pa" in grp.columns:
                pr = (grp["P3_Pa"] / grp["P2_Pa"].replace(0, np.nan)).dropna()
                rec["PR_mean"]  = float(pr.mean())
                rec["PR_trend"] = float(np.polyfit(np.arange(len(pr)), pr.values, 1)[0]) if len(pr) > 2 else 0.0

            # Subsystem divergence (was one subsystem failing faster?)
            if all(c in grp.columns for c in ["CompressorHealth", "CombustorHealth", "TurbineHealth"]):
                final_comp = float(grp["CompressorHealth"].iloc[-1])
                final_comb = float(grp["CombustorHealth"].iloc[-1])
                final_turb = float(grp["TurbineHealth"].iloc[-1])
                rec["subsystem_divergence"] = float(np.std([final_comp, final_comb, final_turb]))
                rec["worst_subsystem_idx"]  = float(np.argmin([final_comp, final_comb, final_turb]))

            # Total cycles for this engine
            if "Cycle" in grp.columns:
                rec["n_cycles"] = int(grp["Cycle"].max())

            records.append(rec)

        self._engine_features = pd.DataFrame(records).set_index("EngineID").fillna(0.0)

    # ── 2. Clustering ─────────────────────────────────────────────────────────
    def _cluster_engines(self, n_clusters: int = 4):
        """K-Means clustering of engines by degradation archetype."""
        if not _SKLEARN_AVAILABLE or self._engine_features is None:
            return

        feat = self._engine_features.select_dtypes(include=[np.number])
        scaler = StandardScaler()
        X = scaler.fit_transform(feat.fillna(0.0))

        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = km.fit_predict(X)

        self._scaler = scaler
        self._cluster_model = km

        # Map cluster labels to archetypes (sort by overall_deg_rate)
        cluster_deg_rates = {}
        for eng_id, label in zip(feat.index, labels):
            rate = self._engine_features.loc[eng_id, "overall_deg_rate"] if "overall_deg_rate" in self._engine_features.columns else 0.0
            cluster_deg_rates.setdefault(label, []).append(rate)

        sorted_clusters = sorted(cluster_deg_rates.keys(), key=lambda c: np.mean(cluster_deg_rates[c]))
        archetype_map = {orig: i for i, orig in enumerate(sorted_clusters)}

        self._engine_clusters = {str(eng_id): archetype_map[label]
                                   for eng_id, label in zip(feat.index, labels)}

    # ── 3. Root Cause Classification ──────────────────────────────────────────
    def _classify_root_causes(self, df: pd.DataFrame):
        """Classify the primary failure mechanism for each engine."""
        self._engine_root_causes = {}

        for eng_id, grp in df.groupby("EngineID"):
            grp = grp.sort_values("Cycle") if "Cycle" in grp.columns else grp
            eng = str(eng_id)
            self._engine_root_causes[eng] = self._diagnose_engine(grp)

    def _diagnose_engine(self, grp: pd.DataFrame) -> Dict:
        """
        Rule-based root cause diagnosis using physics-grounded signatures.
        Examines sensor trends to identify the dominant failure mechanism.
        """
        evidence = []
        scores = {}

        n = len(grp)
        if n < 5:
            return {"primary_failure_mechanism": "Insufficient Data",
                    "confidence": 0.0, "evidence": []}

        # Score each failure mechanism
        for name, sig in FAILURE_SIGNATURES.items():
            sensor = sig["primary_sensor"]
            score = 0.0
            ev = []

            # Compute the trend of the key sensor
            if sensor == "PR_compressor" and "P3_Pa" in grp.columns and "P2_Pa" in grp.columns:
                series = (grp["P3_Pa"] / grp["P2_Pa"].replace(0, np.nan)).fillna(0.0).values
            elif sensor == "TR_combustor" and "T3_K" in grp.columns and "T2_K" in grp.columns:
                series = (grp["T3_K"] / grp["T2_K"].replace(0, np.nan)).fillna(0.0).values
            elif sensor == "Work_Coefficient" and "T3_K" in grp.columns and "T4_K" in grp.columns:
                series = ((grp["T3_K"] - grp["T4_K"]) / grp["T3_K"].replace(0, np.nan)).fillna(0.0).values
            elif sensor == "EGT_Margin_K" and "T4_K" in grp.columns:
                series = (1273.15 - grp["T4_K"]).values
            elif sensor == "Health_Divergence":
                cols = [c for c in ["CompressorHealth", "CombustorHealth", "TurbineHealth"] if c in grp.columns]
                if cols:
                    series = grp[cols].std(axis=1).values
                else:
                    series = np.zeros(n)
            else:
                series = np.zeros(n)

            if len(series) < 2:
                scores[name] = 0.0
                continue

            # Compute slope
            x = np.arange(len(series))
            slope = float(np.polyfit(x, series, 1)[0])
            total_change = float(series[-1] - series[0])

            if sig["direction"] == "decreasing":
                score = max(0.0, -slope * 100)
                if total_change < -0.5:
                    ev.append(f"{sensor} dropped {abs(total_change):.2f} over engine life")
                    score += abs(total_change) * 10
            else:  # increasing (Health_Divergence)
                score = max(0.0, slope * 100)
                if total_change > 0.01:
                    ev.append(f"{sensor} increased {total_change:.3f} (subsystems diverging)")
                    score += total_change * 100

            # Bonus: health of primary subsystem
            if "CompressorHealth" in grp.columns and name == "Compressor Fouling":
                comp_drop = float(grp["CompressorHealth"].iloc[0] - grp["CompressorHealth"].iloc[-1])
                if comp_drop > 0.10:
                    ev.append(f"CompressorHealth dropped {comp_drop:.3f}")
                    score += comp_drop * 50

            if "TurbineHealth" in grp.columns and name == "Turbine Thermal Damage":
                turb_drop = float(grp["TurbineHealth"].iloc[0] - grp["TurbineHealth"].iloc[-1])
                if turb_drop > 0.05:
                    ev.append(f"TurbineHealth dropped {turb_drop:.3f}")
                    score += turb_drop * 50

            scores[name] = score
            FAILURE_SIGNATURES[name]["_evidence"] = ev

        # Sort by score
        sorted_mechanisms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_mechanisms[0]
        secondary = sorted_mechanisms[1] if len(sorted_mechanisms) > 1 and sorted_mechanisms[1][1] > 0.5 else None

        total_score = sum(s for _, s in sorted_mechanisms)
        confidence = round(primary[1] / max(EPS, total_score), 3)

        primary_ev = FAILURE_SIGNATURES[primary[0]].get("_evidence", [])

        # Failure pathway description
        pathway_parts = [primary[0]]
        if secondary and secondary[1] > primary[1] * 0.5:
            pathway_parts.append(secondary[0])
        pathway = " → ".join(pathway_parts)

        return {
            "primary_failure_mechanism": primary[0],
            "primary_failure_subsystem": _mechanism_to_subsystem(primary[0]),
            "secondary_failure_mechanism": secondary[0] if secondary else None,
            "secondary_failure_subsystem": _mechanism_to_subsystem(secondary[0]) if secondary else None,
            "confidence": confidence,
            "evidence": primary_ev,
            "failure_pathway": pathway,
            "governing_law": FAILURE_SIGNATURES[primary[0]]["governing_law"],
        }

    # ── 4. Engine Similarity Search ────────────────────────────────────────────
    def find_similar_engines(self, engine_id: str, query_cycle: Optional[int] = None,
                              top_k: int = 5) -> Dict:
        """
        Cosine-similarity nearest-neighbor search in degradation feature space.
        Returns top-K most similar engines.
        """
        if not self.is_fitted_ or self._engine_features is None:
            return {"error": "Fleet analytics not fitted"}

        eng = str(engine_id)
        if eng not in self._engine_features.index:
            return {"error": f"Engine {eng} not found in fleet"}

        feat_df = self._engine_features.select_dtypes(include=[np.number]).fillna(0.0)
        X = feat_df.values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        idx = list(feat_df.index)
        query_idx = idx.index(eng)
        query_vec = X_scaled[query_idx].reshape(1, -1)

        sims = cosine_similarity(query_vec, X_scaled)[0]

        # Separate by health status
        results = []
        for i, (eid, sim) in enumerate(zip(idx, sims)):
            if eid == eng:
                continue
            row = self._engine_features.loc[eid]
            final_h = row.get("final_OverallHealth", 0.95)
            results.append({
                "engine_id": eid,
                "similarity_pct": round(float(sim) * 100, 1),
                "final_health": round(float(final_h), 4),
                "cluster": CLUSTER_ARCHETYPES.get(self._engine_clusters.get(eid, 1), "Normal"),
                "root_cause": self._engine_root_causes.get(eid, {}).get("primary_failure_mechanism", "Unknown"),
            })

        results.sort(key=lambda x: x["similarity_pct"], reverse=True)

        healthy   = [r for r in results if r["final_health"] > 0.90][:top_k]
        degraded  = [r for r in results if 0.70 < r["final_health"] <= 0.90][:top_k]
        failed    = [r for r in results if r["final_health"] <= 0.70][:top_k]
        overall   = results[:top_k]

        query_cluster = CLUSTER_ARCHETYPES.get(self._engine_clusters.get(eng, 1), "Normal")
        top = results[0] if results else {}

        return {
            "query_engine": eng,
            "nearest_overall":  overall,
            "nearest_healthy":  healthy,
            "nearest_degraded": degraded,
            "nearest_failure_pattern": failed,
            "explanation": (
                f"Engine {eng} ({query_cluster}) is most similar to Engine "
                f"{top.get('engine_id','?')} ({top.get('similarity_pct',0):.0f}% similarity) "
                f"based on degradation trajectory features."
            ) if top else "No similar engines found.",
        }

    # ── 5. Sensor Degradation Ordering ────────────────────────────────────────
    def _compute_sensor_degradation_order(self, df: pd.DataFrame):
        """Identify which sensors show earliest and most consistent degradation across fleet."""
        sensor_cols = [c for c in ["T3_K","T4_K","P3_Pa","P2_Pa","RPM_rev_min","FuelFlow_kg_s"]
                        if c in df.columns]
        ordering = []
        for scol in sensor_cols:
            slopes = []
            for _, grp in df.groupby("EngineID"):
                grp = grp.sort_values("Cycle") if "Cycle" in grp.columns else grp
                vals = grp[scol].dropna().values
                if len(vals) < 3:
                    continue
                slope = float(np.polyfit(np.arange(len(vals)), vals, 1)[0])
                slopes.append(slope)
            if slopes:
                ordering.append({
                    "sensor": scol,
                    "mean_slope": float(np.mean(slopes)),
                    "pct_engines_degrading": round(100.0 * sum(1 for s in slopes if s < 0) / len(slopes), 1),
                    "fleet_consistency": round(1.0 - (float(np.std(slopes)) / (abs(float(np.mean(slopes))) + EPS)), 3),
                })

        # Sort by consistency and magnitude of degradation
        ordering.sort(key=lambda x: x["pct_engines_degrading"], reverse=True)
        self._sensor_degradation_order = ordering

    # ── 6. Failure Precursors ─────────────────────────────────────────────────
    def _detect_failure_precursors(self, df: pd.DataFrame, n_before: int = 20):
        """
        Identify sensor patterns that consistently appear N cycles before
        OverallHealth crosses the warning threshold (0.85).
        """
        if "OverallHealth" not in df.columns:
            return

        precursor_signals = defaultdict(list)
        for _, grp in df.groupby("EngineID"):
            grp = grp.sort_values("Cycle") if "Cycle" in grp.columns else grp
            health = grp["OverallHealth"].values
            # Find first threshold crossing
            crossings = np.where(health < HEALTH_WARNING_THRESHOLD)[0]
            if len(crossings) == 0:
                continue
            crossing_idx = crossings[0]
            precursor_start = max(0, crossing_idx - n_before)

            for scol in ["T4_K","T3_K","P3_Pa","P2_Pa","FuelFlow_kg_s"]:
                if scol not in grp.columns:
                    continue
                window = grp[scol].values[precursor_start:crossing_idx]
                if len(window) < 3:
                    continue
                slope = float(np.polyfit(np.arange(len(window)), window, 1)[0])
                precursor_signals[scol].append(slope)

        self._failure_precursors = {
            sensor: {
                "mean_slope_before_failure": float(np.mean(slopes)),
                "direction": "increasing" if float(np.mean(slopes)) > 0 else "decreasing",
                "consistency_pct": round(100 * sum(1 for s in slopes if np.sign(s) == np.sign(np.mean(slopes))) / len(slopes), 1),
                "n_engines": len(slopes),
            }
            for sensor, slopes in precursor_signals.items() if len(slopes) >= 5
        }

    # ── Public Query Methods ───────────────────────────────────────────────────
    def get_engine_cluster(self, engine_id: str) -> Dict:
        cluster_idx = self._engine_clusters.get(str(engine_id), 1)
        archetype = CLUSTER_ARCHETYPES.get(cluster_idx, "Normal Degrader")
        return {"engine_id": engine_id, "cluster_index": cluster_idx, "archetype": archetype}

    def get_root_cause(self, engine_id: str) -> Dict:
        return self._engine_root_causes.get(str(engine_id), {"primary_failure_mechanism": "Not analyzed"})

    def get_sensor_degradation_ordering(self) -> List[Dict]:
        return self._sensor_degradation_order

    def get_failure_precursors(self) -> Optional[Dict]:
        return self._failure_precursors

    def get_peer_comparison(self, engine_id: str) -> Dict:
        """Returns fleet percentile for this engine's degradation rate."""
        eng = str(engine_id)
        if self._engine_features is None or eng not in self._engine_features.index:
            return {"error": "Engine not found"}

        if "overall_deg_rate" not in self._engine_features.columns:
            return {"error": "Degradation rate not computed"}

        rates = self._engine_features["overall_deg_rate"].dropna().values
        this_rate = float(self._engine_features.loc[eng, "overall_deg_rate"])
        pct_faster = round(100.0 * (this_rate > rates).mean(), 1)

        return {
            "engine_id": eng,
            "degradation_rate": round(this_rate, 6),
            "fleet_percentile_faster": pct_faster,  # X% of fleet degrade faster
            "fleet_percentile_slower": round(100.0 - pct_faster, 1),
            "summary": (
                f"Engine {eng} is degrading {'faster' if pct_faster < 50 else 'slower'} "
                f"than {max(pct_faster, 100-pct_faster):.0f}% of fleet peers."
            ),
        }

    def get_fleet_health_distribution(self, df: Optional[pd.DataFrame] = None) -> Dict:
        """Health statistics stratified by early/mid/late life."""
        data = df if df is not None else self._dataset_df
        if data is None:
            return {}

        if "OverallHealth" not in data.columns or "Cycle" not in data.columns:
            return {}

        max_cycles_per_engine = data.groupby("EngineID")["Cycle"].transform("max")
        life_frac = data["Cycle"] / max_cycles_per_engine.replace(0, 1)

        result = {}
        for phase, (lo, hi) in [("early", (0.0, 0.33)), ("mid", (0.33, 0.67)), ("late", (0.67, 1.0))]:
            mask = (life_frac >= lo) & (life_frac < hi)
            subset = data.loc[mask, "OverallHealth"]
            result[phase] = {
                "mean":   round(float(subset.mean()), 4),
                "std":    round(float(subset.std()),  4),
                "min":    round(float(subset.min()),  4),
                "max":    round(float(subset.max()),  4),
                "p25":    round(float(subset.quantile(0.25)), 4),
                "p75":    round(float(subset.quantile(0.75)), 4),
                "n_obs":  int(mask.sum()),
            }
        return result

    def get_critical_operating_envelope(self, df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Identifies which operating conditions (Mach, Altitude, T3) correlate
        with the fastest degradation rates.
        """
        data = df if df is not None else self._dataset_df
        if data is None or "OverallHealth" not in data.columns:
            return {}

        condition_cols = [c for c in ["Mach","Altitude_m","T3_K","FuelFlow_kg_s"] if c in data.columns]
        health_change = data.groupby("EngineID")["OverallHealth"].diff()
        correlations = {}
        for col in condition_cols:
            corr = data[col].corr(health_change)
            correlations[col] = round(float(corr), 4) if not np.isnan(corr) else 0.0

        # Identify critical (high Mach + high T3 + low altitude = high load)
        critical_conditions = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
        return {
            "sensor_health_correlations": dict(critical_conditions),
            "most_critical_condition": critical_conditions[0][0] if critical_conditions else "Unknown",
            "interpretation": "Negative correlation → higher value = faster degradation",
        }


def _mechanism_to_subsystem(mechanism: str) -> Optional[str]:
    """Maps failure mechanism name to subsystem label."""
    mapping = {
        "Compressor Fouling":       "Compressor",
        "Combustor Efficiency Loss":"Combustor",
        "Turbine Thermal Damage":   "Turbine",
        "EGT Exceedance":           "Turbine",
        "Multi-subsystem":          "Multiple",
    }
    return mapping.get(mechanism)


# Global singleton
_global_fleet: Optional[FleetAnalytics] = None

def get_global_fleet() -> FleetAnalytics:
    global _global_fleet
    if _global_fleet is None:
        _global_fleet = FleetAnalytics()
    return _global_fleet
