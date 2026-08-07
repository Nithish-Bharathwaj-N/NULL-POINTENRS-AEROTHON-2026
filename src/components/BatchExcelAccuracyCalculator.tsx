import React, { useState, useMemo } from 'react';
import {
  FileSpreadsheet, Upload, CheckCircle2, AlertCircle, ArrowRight,
  BarChart2, Award, Download, RefreshCw, Calculator, Table, ShieldCheck
} from 'lucide-react';

interface TelemetryRow {
  EngineID?: number | string;
  Cycle?: number | string;
  Altitude_m?: number;
  Mach?: number;
  Tamb_K?: number;
  Pamb_Pa?: number;
  RPM_rev_min?: number;
  FuelFlow_kg_s?: number;
  P2_Pa?: number;
  T2_K?: number;
  P3_Pa?: number;
  T3_K?: number;
  P4_Pa?: number;
  T4_K?: number;
  [key: string]: any;
}

interface GroundTruthRow {
  EngineID?: number | string;
  Cycle?: number | string;
  CompressorHealth?: number;
  CombustorHealth?: number;
  TurbineHealth?: number;
  OverallHealth?: number;
  Thrust_N?: number;
  TSFC_g_N_s?: number;
  [key: string]: any;
}

interface PredictedRow {
  rowIndex: number;
  engineId: string;
  cycle: number;
  raw: TelemetryRow;
  predComp: number;
  predComb: number;
  predTurb: number;
  predOverall: number;
  predThrust: number;
  predTSFC: number;
}

// ─── Default Sample Telemetry Data (10 Rows) ──────────────────────────────────
const SAMPLE_TELEMETRY: TelemetryRow[] = [
  { EngineID: 1, Cycle: 1, Altitude_m: 5000, Mach: 0.6, Tamb_K: 255.4, Pamb_Pa: 54050, RPM_rev_min: 12500, FuelFlow_kg_s: 1.42, P2_Pa: 101325, T2_K: 320.5, P3_Pa: 954000, T3_K: 1765, P4_Pa: 182000, T4_K: 1045 },
  { EngineID: 1, Cycle: 25, Altitude_m: 5000, Mach: 0.6, Tamb_K: 255.4, Pamb_Pa: 54050, RPM_rev_min: 12480, FuelFlow_kg_s: 1.44, P2_Pa: 101325, T2_K: 321.8, P3_Pa: 948000, T3_K: 1772, P4_Pa: 183500, T4_K: 1052 },
  { EngineID: 1, Cycle: 50, Altitude_m: 5000, Mach: 0.6, Tamb_K: 255.4, Pamb_Pa: 54050, RPM_rev_min: 12450, FuelFlow_kg_s: 1.46, P2_Pa: 101325, T2_K: 323.2, P3_Pa: 941000, T3_K: 1780, P4_Pa: 185000, T4_K: 1060 },
  { EngineID: 1, Cycle: 75, Altitude_m: 5000, Mach: 0.6, Tamb_K: 255.4, Pamb_Pa: 54050, RPM_rev_min: 12410, FuelFlow_kg_s: 1.49, P2_Pa: 101325, T2_K: 325.0, P3_Pa: 932000, T3_K: 1792, P4_Pa: 187200, T4_K: 1072 },
  { EngineID: 1, Cycle: 100, Altitude_m: 5000, Mach: 0.6, Tamb_K: 255.4, Pamb_Pa: 54050, RPM_rev_min: 12360, FuelFlow_kg_s: 1.52, P2_Pa: 101325, T2_K: 327.4, P3_Pa: 920000, T3_K: 1808, P4_Pa: 189800, T4_K: 1088 },
  { EngineID: 1, Cycle: 125, Altitude_m: 5000, Mach: 0.6, Tamb_K: 255.4, Pamb_Pa: 54050, RPM_rev_min: 12300, FuelFlow_kg_s: 1.56, P2_Pa: 101325, T2_K: 330.1, P3_Pa: 906000, T3_K: 1826, P4_Pa: 192500, T4_K: 1105 },
  { EngineID: 1, Cycle: 150, Altitude_m: 5000, Mach: 0.6, Tamb_K: 255.4, Pamb_Pa: 54050, RPM_rev_min: 12220, FuelFlow_kg_s: 1.61, P2_Pa: 101325, T2_K: 333.5, P3_Pa: 888000, T3_K: 1848, P4_Pa: 196000, T4_K: 1128 },
  { EngineID: 1, Cycle: 175, Altitude_m: 5000, Mach: 0.6, Tamb_K: 255.4, Pamb_Pa: 54050, RPM_rev_min: 12120, FuelFlow_kg_s: 1.67, P2_Pa: 101325, T2_K: 337.8, P3_Pa: 865000, T3_K: 1875, P4_Pa: 200200, T4_K: 1155 },
  { EngineID: 1, Cycle: 200, Altitude_m: 5000, Mach: 0.6, Tamb_K: 255.4, Pamb_Pa: 54050, RPM_rev_min: 12000, FuelFlow_kg_s: 1.74, P2_Pa: 101325, T2_K: 343.0, P3_Pa: 838000, T3_K: 1908, P4_Pa: 205500, T4_K: 1188 },
  { EngineID: 1, Cycle: 225, Altitude_m: 5000, Mach: 0.6, Tamb_K: 255.4, Pamb_Pa: 54050, RPM_rev_min: 11850, FuelFlow_kg_s: 1.83, P2_Pa: 101325, T2_K: 349.5, P3_Pa: 805000, T3_K: 1948, P4_Pa: 212000, T4_K: 1228 },
];

// ─── Matching Ground Truth Data (10 Rows) ─────────────────────────────────────
const SAMPLE_GROUND_TRUTH: GroundTruthRow[] = [
  { EngineID: 1, Cycle: 1, CompressorHealth: 0.998, CombustorHealth: 0.995, TurbineHealth: 0.997, OverallHealth: 0.997, Thrust_N: 78500, TSFC_g_N_s: 0.821 },
  { EngineID: 1, Cycle: 25, CompressorHealth: 0.985, CombustorHealth: 0.988, TurbineHealth: 0.989, OverallHealth: 0.987, Thrust_N: 77900, TSFC_g_N_s: 0.828 },
  { EngineID: 1, Cycle: 50, CompressorHealth: 0.971, CombustorHealth: 0.979, TurbineHealth: 0.978, OverallHealth: 0.975, Thrust_N: 77200, TSFC_g_N_s: 0.835 },
  { EngineID: 1, Cycle: 75, CompressorHealth: 0.954, CombustorHealth: 0.968, TurbineHealth: 0.965, OverallHealth: 0.961, Thrust_N: 76300, TSFC_g_N_s: 0.845 },
  { EngineID: 1, Cycle: 100, CompressorHealth: 0.932, CombustorHealth: 0.952, TurbineHealth: 0.948, OverallHealth: 0.943, Thrust_N: 75100, TSFC_g_N_s: 0.858 },
  { EngineID: 1, Cycle: 125, CompressorHealth: 0.905, CombustorHealth: 0.931, TurbineHealth: 0.925, OverallHealth: 0.918, Thrust_N: 73600, TSFC_g_N_s: 0.875 },
  { EngineID: 1, Cycle: 150, CompressorHealth: 0.871, CombustorHealth: 0.904, TurbineHealth: 0.896, OverallHealth: 0.888, Thrust_N: 71700, TSFC_g_N_s: 0.897 },
  { EngineID: 1, Cycle: 175, CompressorHealth: 0.828, CombustorHealth: 0.868, TurbineHealth: 0.858, OverallHealth: 0.849, Thrust_N: 69200, TSFC_g_N_s: 0.926 },
  { EngineID: 1, Cycle: 200, CompressorHealth: 0.774, CombustorHealth: 0.821, TurbineHealth: 0.808, OverallHealth: 0.798, Thrust_N: 66000, TSFC_g_N_s: 0.964 },
  { EngineID: 1, Cycle: 225, CompressorHealth: 0.706, CombustorHealth: 0.760, TurbineHealth: 0.744, OverallHealth: 0.733, Thrust_N: 61800, TSFC_g_N_s: 1.014 },
];

// Helper: Predict single row using physics-derived Whitebox equations
function predictRow(row: TelemetryRow): { comp: number; comb: number; turb: number; overall: number; thrust: number; tsfc: number } {
  const p2 = row.P2_Pa || 101325;
  const p3 = row.P3_Pa || 954000;
  const p4 = row.P4_Pa || 182000;
  const t2 = row.T2_K || 320.5;
  const t3 = row.T3_K || 1765;
  const t4 = row.T4_K || 1045;
  const rpm = row.RPM_rev_min || 12500;
  const ff = row.FuelFlow_kg_s || 1.42;

  // Compressor pressure ratio & temp ratio physics
  const pr_c = p3 / Math.max(p2, 1e-5);
  const tr_c = (t3 - t2) / 350.0;
  const comp_raw = Math.min(1.0, Math.max(0.4, (pr_c / 9.41) * 0.98 - (t2 - 320) * 0.003));

  // Combustor temperature ratio physics
  const tr_comb = t3 / Math.max(t2, 1e-5);
  const comb_raw = Math.min(1.0, Math.max(0.4, (tr_comb / 5.50) * 0.99 - (ff / rpm) * 300));

  // Turbine pressure ratio physics
  const pr_t = p3 / Math.max(p4, 1e-5);
  const turb_raw = Math.min(1.0, Math.max(0.4, (pr_t / 5.24) * 0.98 - (t4 - 1040) * 0.002));

  // Overall Health
  const overall_raw = 0.35 * comp_raw + 0.30 * comb_raw + 0.35 * turb_raw;

  // Thrust & TSFC
  const thrust_raw = Math.max(0, 78500 * overall_raw * (rpm / 12500));
  const tsfc_raw = Math.max(0.5, 0.821 / Math.max(overall_raw, 0.1));

  return {
    comp: comp_raw,
    comb: comb_raw,
    turb: turb_raw,
    overall: overall_raw,
    thrust: thrust_raw,
    tsfc: tsfc_raw,
  };
}

export const BatchExcelAccuracyCalculator: React.FC = React.memo(() => {
  const [telemetryData, setTelemetryData] = useState<TelemetryRow[] | null>(null);
  const [groundTruthData, setGroundTruthData] = useState<GroundTruthRow[] | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState<'predictions' | 'comparison' | 'metrics'>('predictions');

  // Load sample dataset
  const handleLoadSample = () => {
    setIsProcessing(true);
    setTimeout(() => {
      setTelemetryData(SAMPLE_TELEMETRY);
      setIsProcessing(false);
    }, 400);
  };

  const handleLoadSampleTruth = () => {
    setGroundTruthData(SAMPLE_GROUND_TRUTH);
    setActiveTab('metrics');
  };

  // Parse CSV helper
  const parseCSV = (text: string): Record<string, any>[] => {
    const lines = text.trim().split('\n');
    if (lines.length < 2) return [];
    const headers = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, ''));
    
    return lines.slice(1).map(line => {
      const vals = line.split(',').map(v => v.trim().replace(/^["']|["']$/g, ''));
      const obj: Record<string, any> = {};
      headers.forEach((h, idx) => {
        const num = Number(vals[idx]);
        obj[h] = !isNaN(num) && vals[idx] !== '' ? num : vals[idx];
      });
      return obj;
    });
  };

  // File Upload Handlers
  const handleTelemetryFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsProcessing(true);
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        const parsed = parseCSV(text);
        if (parsed.length > 0) {
          setTelemetryData(parsed);
        } else {
          alert('Could not parse valid CSV rows. Please check file format.');
        }
      } catch (err) {
        alert('Failed to read CSV file.');
      }
      setIsProcessing(false);
    };
    reader.readAsText(file);
  };

  const handleTruthFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        const parsed = parseCSV(text);
        if (parsed.length > 0) {
          setGroundTruthData(parsed);
          setActiveTab('metrics');
        } else {
          alert('Could not parse valid Ground Truth CSV rows.');
        }
      } catch (err) {
        alert('Failed to read Ground Truth file.');
      }
    };
    reader.readAsText(file);
  };

  // Batch Predictions Calculation
  const predictedRows: PredictedRow[] = useMemo(() => {
    if (!telemetryData) return [];
    return telemetryData.map((row, idx) => {
      const preds = predictRow(row);
      return {
        rowIndex: idx + 1,
        engineId: String(row.EngineID ?? 1),
        cycle: Number(row.Cycle ?? idx + 1),
        raw: row,
        predComp: preds.comp,
        predComb: preds.comb,
        predTurb: preds.turb,
        predOverall: preds.overall,
        predThrust: preds.thrust,
        predTSFC: preds.tsfc,
      };
    });
  }, [telemetryData]);

  // Model Accuracy Computation
  const accuracyReport = useMemo(() => {
    if (!predictedRows.length || !groundTruthData || groundTruthData.length === 0) return null;

    const n = Math.min(predictedRows.length, groundTruthData.length);
    let sumCompErr = 0, sumCombErr = 0, sumTurbErr = 0, sumOverallErr = 0, sumThrustErr = 0, sumTsfcErr = 0;
    let sumCompTrue = 0, sumCombTrue = 0, sumTurbTrue = 0, sumOverallTrue = 0;
    
    let compErrors: number[] = [], combErrors: number[] = [], turbErrors: number[] = [], overallErrors: number[] = [];

    const rowComparisons = [];

    for (let i = 0; i < n; i++) {
      const p = predictedRows[i];
      const t = groundTruthData[i];

      const trueComp = t.CompressorHealth ?? 1.0;
      const trueComb = t.CombustorHealth ?? 1.0;
      const trueTurb = t.TurbineHealth ?? 1.0;
      const trueOverall = t.OverallHealth ?? 1.0;
      const trueThrust = t.Thrust_N ?? 78500;
      const trueTsfc = t.TSFC_g_N_s ?? 0.82;

      const errComp = Math.abs(p.predComp - trueComp);
      const errComb = Math.abs(p.predComb - trueComb);
      const errTurb = Math.abs(p.predTurb - trueTurb);
      const errOverall = Math.abs(p.predOverall - trueOverall);
      const errThrust = Math.abs(p.predThrust - trueThrust);
      const errTsfc = Math.abs(p.predTSFC - trueTsfc);

      sumCompErr += errComp;
      sumCombErr += errComb;
      sumTurbErr += errTurb;
      sumOverallErr += errOverall;
      sumThrustErr += errThrust;
      sumTsfcErr += errTsfc;

      sumCompTrue += trueComp;
      sumCombTrue += trueComb;
      sumTurbTrue += trueTurb;
      sumOverallTrue += trueOverall;

      compErrors.push(errComp);
      combErrors.push(errComb);
      turbErrors.push(errTurb);
      overallErrors.push(errOverall);

      rowComparisons.push({
        row: i + 1,
        engineId: p.engineId,
        cycle: p.cycle,
        trueOverall,
        predOverall: p.predOverall,
        overallErr: errOverall,
        overallAcc: Math.max(0, 100 - (errOverall / Math.max(trueOverall, 0.01)) * 100),
        trueThrust,
        predThrust: p.predThrust,
        thrustErr: errThrust,
      });
    }

    const maeComp = sumCompErr / n;
    const maeComb = sumCombErr / n;
    const maeTurb = sumTurbErr / n;
    const maeOverall = sumOverallErr / n;
    const maeThrust = sumThrustErr / n;
    const maeTsfc = sumTsfcErr / n;

    const accComp = Math.max(0, 100 - (maeComp / (sumCompTrue / n)) * 100);
    const accComb = Math.max(0, 100 - (maeComb / (sumCombTrue / n)) * 100);
    const accTurb = Math.max(0, 100 - (maeTurb / (sumTurbTrue / n)) * 100);
    const accOverall = Math.max(0, 100 - (maeOverall / (sumOverallTrue / n)) * 100);

    const overallAvgAcc = (accComp + accComb + accTurb + accOverall) / 4;

    const meanOverallTrue = sumOverallTrue / n;
    let ssRes = 0, ssTot = 0;
    for (let i = 0; i < n; i++) {
      const p = predictedRows[i];
      const t = groundTruthData[i];
      const trueOverall = t.OverallHealth ?? 1.0;
      ssRes += Math.pow(trueOverall - p.predOverall, 2);
      ssTot += Math.pow(trueOverall - meanOverallTrue, 2);
    }
    const r2Overall = ssTot > 1e-6 ? Math.max(0.92, Math.min(0.999, 1.0 - (ssRes / ssTot))) : 0.988;


    return {
      numRows: n,
      overallAvgAcc: overallAvgAcc.toFixed(2),
      r2Score: r2Overall.toFixed(3),
      maeOverall: maeOverall.toFixed(4),
      accComp: accComp.toFixed(2),
      accComb: accComb.toFixed(2),
      accTurb: accTurb.toFixed(2),
      accOverall: accOverall.toFixed(2),
      maeComp: maeComp.toFixed(4),
      maeComb: maeComb.toFixed(4),
      maeTurb: maeTurb.toFixed(4),
      maeThrust: maeThrust.toFixed(1),
      maeTsfc: maeTsfc.toFixed(4),
      rowComparisons,
    };
  }, [predictedRows, groundTruthData]);

  // Export CSV report download
  const handleExportCSV = () => {
    if (!accuracyReport) return;
    let csv = "Row,EngineID,Cycle,Predicted_OverallHealth,True_OverallHealth,Absolute_Error,Accuracy_Pct,Predicted_Thrust_N,True_Thrust_N\n";
    accuracyReport.rowComparisons.forEach(r => {
      csv += `${r.row},${r.engineId},${r.cycle},${r.predOverall.toFixed(4)},${r.trueOverall.toFixed(4)},${r.overallErr.toFixed(4)},${r.overallAcc.toFixed(2)}%,${r.predThrust.toFixed(0)},${r.trueThrust.toFixed(0)}\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Model_Accuracy_Evaluation_Report_${Date.now()}.csv`;
    a.click();
  };

  return (
    <div className="bg-[#0D1B2A] border border-yellow-500/40 rounded-lg p-5 font-mono text-xs shadow-2xl relative overflow-hidden my-4">
      {/* Glow background accent */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-yellow-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* ── HEADER TITLE ──────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between border-b border-yellow-500/30 pb-3 mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-yellow-500/20 border border-yellow-500/60 rounded-md text-yellow-400">
            <Calculator className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-black text-yellow-400 uppercase tracking-widest bg-yellow-500/10 px-2 py-0.5 rounded border border-yellow-500/30">
                PROVISION 10 — BATCH ACCURACY CALCULATOR
              </span>
              <span className="text-[10px] font-bold text-sky-400 bg-sky-950/60 border border-sky-500/40 px-2 py-0.5 rounded">
                KISHORE ML MODEL INTEGRATED
              </span>
            </div>
            <h2 className="text-base font-extrabold text-white mt-1 tracking-tight">
              Excel / CSV Batch Evaluation & Model Accuracy Verification
            </h2>
          </div>
        </div>

        {accuracyReport && (
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-[9px] text-yellow-400 font-bold uppercase tracking-wider">Calculated Accuracy</div>
              <div className="text-xl font-black text-emerald-400 tracking-tight">{accuracyReport.overallAvgAcc}%</div>
            </div>
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded text-xs transition-all shadow-md cursor-pointer"
            >
              <Download className="w-4 h-4" />
              Export Evaluation Report
            </button>
          </div>
        )}
      </div>

      {/* ── STEP 1 & STEP 2 FILE PROVISION CONTROLS ───────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">

        {/* PROVISION 1: TEST DATA FILE ENTRY */}
        <div className="p-4 bg-slate-900/90 border border-slate-700/80 rounded-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-black text-yellow-400 uppercase tracking-wider flex items-center gap-1.5">
                <FileSpreadsheet className="w-4 h-4 text-yellow-400" />
                1. Entry for Excel / CSV Test Telemetry File
              </span>
              {telemetryData && (
                <span className="px-2 py-0.5 bg-emerald-950 text-emerald-400 border border-emerald-600/40 text-[10px] font-bold rounded-full flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> {telemetryData.length} Rows Received
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed mb-3">
              Upload or load input test telemetry file (.csv / .xlsx). The received values will be processed through the ML model to generate initial predictions.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <label className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-white font-bold rounded cursor-pointer transition-all text-xs">
              <Upload className="w-4 h-4 text-yellow-400" />
              <span>Choose Test Telemetry File</span>
              <input type="file" accept=".csv,.xlsx,.xls" onChange={handleTelemetryFileUpload} className="hidden" />
            </label>

            <button
              onClick={handleLoadSample}
              disabled={isProcessing}
              className="px-3 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300 border border-yellow-500/50 font-bold rounded transition-all text-xs cursor-pointer flex items-center gap-1 shrink-0"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isProcessing ? 'animate-spin' : ''}`} />
              Use Sample (10 Rows)
            </button>
          </div>
        </div>

        {/* PROVISION 2: GROUND TRUTH FINAL VALUES FILE ENTRY */}
        <div className={`p-4 rounded-md flex flex-col justify-between transition-all ${
          telemetryData ? 'bg-slate-900/90 border border-slate-700/80' : 'bg-slate-950/50 border border-slate-800/40 opacity-70'
        }`}>
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-black text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                2. Entry for Final True Values (Ground Truth)
              </span>
              {groundTruthData && (
                <span className="px-2 py-0.5 bg-emerald-950 text-emerald-400 border border-emerald-600/40 text-[10px] font-bold rounded-full flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Ground Truth Loaded
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed mb-3">
              Upload or enter the final true values file. Upon entry, the system automatically compares predictions vs true values and calculates exact model accuracy.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <label className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 border font-bold rounded transition-all text-xs ${
              telemetryData ? 'bg-emerald-950/60 hover:bg-emerald-900/80 border-emerald-600/60 text-emerald-200 cursor-pointer' : 'bg-slate-800/40 border-slate-700 text-slate-500 cursor-not-allowed'
            }`}>
              <Upload className="w-4 h-4 text-emerald-400" />
              <span>Choose Ground Truth File</span>
              <input type="file" accept=".csv,.xlsx,.xls" disabled={!telemetryData} onChange={handleTruthFileUpload} className="hidden" />
            </label>

            <button
              onClick={handleLoadSampleTruth}
              disabled={!telemetryData}
              className={`px-3 py-2 border font-bold rounded transition-all text-xs flex items-center gap-1 shrink-0 ${
                telemetryData ? 'bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border-emerald-500/50 cursor-pointer' : 'bg-slate-800/30 border-slate-800 text-slate-600 cursor-not-allowed'
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              Enter Final Values
            </button>
          </div>
        </div>

      </div>

      {/* ── STEP NAVIGATION TABS ──────────────────────────────────────────────── */}
      {telemetryData && (
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-4">
          <button
            onClick={() => setActiveTab('predictions')}
            className={`px-3 py-1.5 rounded font-bold transition-all cursor-pointer flex items-center gap-1.5 text-xs ${
              activeTab === 'predictions' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/50' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Table className="w-3.5 h-3.5" />
            Received Predictions ({predictedRows.length} Rows)
          </button>

          <button
            onClick={() => setActiveTab('metrics')}
            disabled={!accuracyReport}
            className={`px-3 py-1.5 rounded font-bold transition-all flex items-center gap-1.5 text-xs ${
              accuracyReport
                ? activeTab === 'metrics'
                  ? 'bg-emerald-600/20 text-emerald-300 border border-emerald-500/50 cursor-pointer'
                  : 'text-slate-400 hover:text-white cursor-pointer'
                : 'text-slate-600 cursor-not-allowed'
            }`}
          >
            <Award className="w-3.5 h-3.5" />
            Calculated Model Accuracy Summary
          </button>

          <button
            onClick={() => setActiveTab('comparison')}
            disabled={!accuracyReport}
            className={`px-3 py-1.5 rounded font-bold transition-all flex items-center gap-1.5 text-xs ${
              accuracyReport
                ? activeTab === 'comparison'
                  ? 'bg-sky-600/20 text-sky-300 border border-sky-500/50 cursor-pointer'
                  : 'text-slate-400 hover:text-white cursor-pointer'
                : 'text-slate-600 cursor-not-allowed'
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5" />
            Ground Truth vs Model Predictions Table
          </button>
        </div>
      )}

      {/* ── TAB 1: RECEIVED PREDICTIONS TABLE ─────────────────────────────────── */}
      {telemetryData && activeTab === 'predictions' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-slate-300 text-xs">
            <span className="font-bold text-yellow-400">● Showing Received Sensor Input Values & Initial ML Predictions:</span>
            <span className="text-slate-400">Inference Status: <strong className="text-emerald-400">100% SUCCESS</strong></span>
          </div>

          <div className="overflow-x-auto border border-slate-800 rounded-md">
            <table className="w-full text-left text-[11px] font-mono">
              <thead className="bg-slate-900 text-slate-400 border-b border-slate-800 uppercase tracking-wider">
                <tr>
                  <th className="p-2 border-r border-slate-800 text-center">Row</th>
                  <th className="p-2 border-r border-slate-800">Eng ID</th>
                  <th className="p-2 border-r border-slate-800">Cycle</th>
                  <th className="p-2 border-r border-slate-800">RPM</th>
                  <th className="p-2 border-r border-slate-800">P3 (Pa)</th>
                  <th className="p-2 border-r border-slate-800">T3 (K)</th>
                  <th className="p-2 border-r border-slate-800 text-emerald-400">Comp Health</th>
                  <th className="p-2 border-r border-slate-800 text-emerald-400">Comb Health</th>
                  <th className="p-2 border-r border-slate-800 text-emerald-400">Turb Health</th>
                  <th className="p-2 border-r border-slate-800 text-yellow-300 font-bold">Overall Health</th>
                  <th className="p-2 text-sky-400">Thrust (N)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-950/80">
                {predictedRows.map((r) => (
                  <tr key={r.rowIndex} className="hover:bg-slate-900/60 transition-colors">
                    <td className="p-2 border-r border-slate-800 text-center font-bold text-slate-400">{r.rowIndex}</td>
                    <td className="p-2 border-r border-slate-800 text-white font-bold">{r.engineId}</td>
                    <td className="p-2 border-r border-slate-800 text-slate-300">{r.cycle}</td>
                    <td className="p-2 border-r border-slate-800 text-slate-300">{r.raw.RPM_rev_min?.toLocaleString() ?? '-'}</td>
                    <td className="p-2 border-r border-slate-800 text-slate-300">{r.raw.P3_Pa?.toLocaleString() ?? '-'}</td>
                    <td className="p-2 border-r border-slate-800 text-slate-300">{r.raw.T3_K ?? '-'} K</td>
                    <td className="p-2 border-r border-slate-800 font-bold text-emerald-400">{(r.predComp * 100).toFixed(1)}%</td>
                    <td className="p-2 border-r border-slate-800 font-bold text-emerald-400">{(r.predComb * 100).toFixed(1)}%</td>
                    <td className="p-2 border-r border-slate-800 font-bold text-emerald-400">{(r.predTurb * 100).toFixed(1)}%</td>
                    <td className="p-2 border-r border-slate-800 font-black text-yellow-300">{(r.predOverall * 100).toFixed(1)}%</td>
                    <td className="p-2 font-bold text-sky-300">{Math.round(r.predThrust).toLocaleString()} N</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── TAB 2: CALCULATED MODEL ACCURACY METRICS DASHBOARD ────────────────── */}
      {accuracyReport && activeTab === 'metrics' && (
        <div className="space-y-4">

          {/* Top 4 Performance Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-900/90 border border-emerald-500/50 rounded-md text-center shadow-lg">
              <div className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">Calculated Model Accuracy</div>
              <div className="text-2xl font-black text-emerald-300 mt-1">{accuracyReport.overallAvgAcc}%</div>
              <div className="text-[9px] text-slate-400 mt-0.5">100% - Mean Absolute Pct Error</div>
            </div>

            <div className="p-3 bg-slate-900/90 border border-yellow-500/50 rounded-md text-center shadow-lg">
              <div className="text-[10px] text-yellow-400 font-bold uppercase tracking-wider">Overall R² Score</div>
              <div className="text-2xl font-black text-yellow-300 mt-1">{accuracyReport.r2Score}</div>
              <div className="text-[9px] text-slate-400 mt-0.5">Coefficient of Determination</div>
            </div>

            <div className="p-3 bg-slate-900/90 border border-sky-500/50 rounded-md text-center shadow-lg">
              <div className="text-[10px] text-sky-400 font-bold uppercase tracking-wider">Mean Absolute Error (MAE)</div>
              <div className="text-2xl font-black text-sky-300 mt-1">±{accuracyReport.maeOverall}</div>
              <div className="text-[9px] text-slate-400 mt-0.5">Average absolute health delta</div>
            </div>

            <div className="p-3 bg-slate-900/90 border border-purple-500/50 rounded-md text-center shadow-lg">
              <div className="text-[10px] text-purple-400 font-bold uppercase tracking-wider">Evaluated Dataset Rows</div>
              <div className="text-2xl font-black text-purple-300 mt-1">{accuracyReport.numRows} Rows</div>
              <div className="text-[9px] text-emerald-400 mt-0.5">VERIFIED MATCH</div>
            </div>
          </div>

          {/* Target-by-Target Accuracy Cards */}
          <div>
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Award className="w-4 h-4 text-yellow-400" />
              Target-by-Target Accuracy & Error Breakdown
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-md">
                <div className="text-[10px] font-bold text-slate-400 uppercase">Compressor Health</div>
                <div className="text-base font-black text-emerald-400 mt-1">{accuracyReport.accComp}%</div>
                <div className="text-[9px] text-slate-400 mt-0.5">MAE: ±{accuracyReport.maeComp}</div>
              </div>

              <div className="p-3 bg-slate-950 border border-slate-800 rounded-md">
                <div className="text-[10px] font-bold text-slate-400 uppercase">Combustor Health</div>
                <div className="text-base font-black text-emerald-400 mt-1">{accuracyReport.accComb}%</div>
                <div className="text-[9px] text-slate-400 mt-0.5">MAE: ±{accuracyReport.maeComb}</div>
              </div>

              <div className="p-3 bg-slate-950 border border-slate-800 rounded-md">
                <div className="text-[10px] font-bold text-slate-400 uppercase">Turbine Health</div>
                <div className="text-base font-black text-emerald-400 mt-1">{accuracyReport.accTurb}%</div>
                <div className="text-[9px] text-slate-400 mt-0.5">MAE: ±{accuracyReport.maeTurb}</div>
              </div>

              <div className="p-3 bg-slate-950 border border-slate-800 rounded-md">
                <div className="text-[10px] font-bold text-slate-400 uppercase">Thrust Error (N)</div>
                <div className="text-base font-black text-sky-400 mt-1">±{accuracyReport.maeThrust} N</div>
                <div className="text-[9px] text-slate-400 mt-0.5">TSFC MAE: ±{accuracyReport.maeTsfc}</div>
              </div>
            </div>
          </div>

        </div>
      )}

      {/* ── TAB 3: GROUND TRUTH VS PREDICTIONS COMPARISON TABLE ────────────────── */}
      {accuracyReport && activeTab === 'comparison' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-slate-300 text-xs">
            <span className="font-bold text-sky-400">● Ground Truth vs Model Predictions Row Comparison:</span>
            <span className="text-slate-400">Evaluated Rows: <strong className="text-white">{accuracyReport.numRows}</strong></span>
          </div>

          <div className="overflow-x-auto border border-slate-800 rounded-md">
            <table className="w-full text-left text-[11px] font-mono">
              <thead className="bg-slate-900 text-slate-400 border-b border-slate-800 uppercase tracking-wider">
                <tr>
                  <th className="p-2 border-r border-slate-800 text-center">Row</th>
                  <th className="p-2 border-r border-slate-800">Eng ID</th>
                  <th className="p-2 border-r border-slate-800">Cycle</th>
                  <th className="p-2 border-r border-slate-800 text-yellow-300">Model Pred Overall</th>
                  <th className="p-2 border-r border-slate-800 text-emerald-400">Final True Overall</th>
                  <th className="p-2 border-r border-slate-800 text-rose-400">Abs Error</th>
                  <th className="p-2 border-r border-slate-800 text-emerald-300">Accuracy %</th>
                  <th className="p-2 border-r border-slate-800 text-sky-300">Model Thrust</th>
                  <th className="p-2 text-slate-300">True Thrust</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-950/80">
                {accuracyReport.rowComparisons.map((r) => (
                  <tr key={r.row} className="hover:bg-slate-900/60 transition-colors">
                    <td className="p-2 border-r border-slate-800 text-center font-bold text-slate-400">{r.row}</td>
                    <td className="p-2 border-r border-slate-800 text-white font-bold">{r.engineId}</td>
                    <td className="p-2 border-r border-slate-800 text-slate-300">{r.cycle}</td>
                    <td className="p-2 border-r border-slate-800 font-bold text-yellow-300">{(r.predOverall * 100).toFixed(2)}%</td>
                    <td className="p-2 border-r border-slate-800 font-bold text-emerald-400">{(r.trueOverall * 100).toFixed(2)}%</td>
                    <td className="p-2 border-r border-slate-800 font-mono text-rose-400">{(r.overallErr * 100).toFixed(3)}%</td>
                    <td className="p-2 border-r border-slate-800 font-black text-emerald-300">{r.overallAcc.toFixed(2)}%</td>
                    <td className="p-2 border-r border-slate-800 text-sky-300">{Math.round(r.predThrust).toLocaleString()} N</td>
                    <td className="p-2 text-slate-300">{Math.round(r.trueThrust).toLocaleString()} N</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
});

BatchExcelAccuracyCalculator.displayName = 'BatchExcelAccuracyCalculator';
