import React, { useState, useEffect } from 'react';
import { Scan, ShieldCheck, Camera, RefreshCw, KeyRound, CheckCircle2 } from 'lucide-react';

export type BiometricScanState = 'IDLE' | 'DETECTING' | 'SCANNING' | 'MATCHING' | 'VERIFIED' | 'FAILED';

interface BiometricScannerProps {
  operatorName: string;
  clearanceLevel: string;
  onScanSuccess: () => void;
  onFallbackToPassword: () => void;
}

export const BiometricScanner: React.FC<BiometricScannerProps> = React.memo(({
  operatorName,
  clearanceLevel,
  onScanSuccess,
  onFallbackToPassword
}) => {
  const [scanState, setScanState] = useState<BiometricScanState>('IDLE');
  const [confidence, setConfidence] = useState<number>(0);
  const [statusText, setStatusText] = useState<string>('SYSTEM READY • AWAITING BIOMETRIC INITIATION');
  const [useSimulatedFeed, setUseSimulatedFeed] = useState<boolean>(true);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (scanState === 'DETECTING') {
      setStatusText('DETECTING FACIAL LANDMARKS (68-POINT MATRIX)...');
      setConfidence(15);
      timer = setTimeout(() => {
        setScanState('SCANNING');
      }, 800);
    } else if (scanState === 'SCANNING') {
      setStatusText('SCANNING IRIS & THERMAL MESH (MIL-STD-498)...');
      let currentConf = 15;
      const interval = setInterval(() => {
        currentConf += Math.floor(Math.random() * 18) + 8;
        if (currentConf >= 72) {
          clearInterval(interval);
          setConfidence(78);
          setScanState('MATCHING');
        } else {
          setConfidence(currentConf);
        }
      }, 250);
      return () => clearInterval(interval);
    } else if (scanState === 'MATCHING') {
      setStatusText(`MATCHING ENCRYPTION KEY AGAINST IAF PKI DATABASE...`);
      let currentConf = 78;
      const interval = setInterval(() => {
        currentConf += Math.floor(Math.random() * 8) + 3;
        if (currentConf >= 98) {
          clearInterval(interval);
          setConfidence(98.4);
          setScanState('VERIFIED');
        } else {
          setConfidence(Math.min(98.4, currentConf));
        }
      }, 200);
      return () => clearInterval(interval);
    } else if (scanState === 'VERIFIED') {
      setStatusText(`IDENTITY VERIFIED: ${operatorName} • CLEARANCE GRANTED`);
      setConfidence(98.4);
      timer = setTimeout(() => {
        onScanSuccess();
      }, 1000);
    }
    return () => clearTimeout(timer);
  }, [scanState, operatorName, onScanSuccess]);

  const handleStartScan = () => {
    setConfidence(0);
    setScanState('DETECTING');
  };

  const handleRetry = () => {
    setConfidence(0);
    setScanState('IDLE');
    setStatusText('SYSTEM READY • AWAITING BIOMETRIC INITIATION');
  };

  return (
    <div className="space-y-4 font-mono text-xs select-none">
      {/* Military Viewfinder & Scanner Container */}
      <div className="relative w-full h-[220px] bg-slate-950 border-2 border-slate-700 rounded-sm overflow-hidden flex flex-col items-center justify-center shadow-inner">
        
        {/* Corner Targeting Brackets */}
        <div className="absolute top-2 left-2 w-5 h-5 border-t-2 border-l-2 border-sky-400 pointer-events-none" />
        <div className="absolute top-2 right-2 w-5 h-5 border-t-2 border-r-2 border-sky-400 pointer-events-none" />
        <div className="absolute bottom-2 left-2 w-5 h-5 border-b-2 border-l-2 border-sky-400 pointer-events-none" />
        <div className="absolute bottom-2 right-2 w-5 h-5 border-b-2 border-r-2 border-sky-400 pointer-events-none" />

        {/* Radar / Blueprint Background Grid */}
        <div 
          className="absolute inset-0 opacity-20 pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(circle, #003366 1px, transparent 1px)`,
            backgroundSize: '16px 16px'
          }}
        />

        {/* Center Circular Biometric Reticule */}
        <div className={`relative w-36 h-36 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${
          scanState === 'VERIFIED'
            ? 'border-emerald-400 bg-emerald-500/10 shadow-[0_0_20px_rgba(16,185,129,0.3)]'
            : scanState === 'SCANNING' || scanState === 'MATCHING'
            ? 'border-sky-400 bg-sky-500/10 animate-pulse shadow-[0_0_20px_rgba(56,189,248,0.2)]'
            : 'border-slate-700 bg-slate-900/40'
        }`}>
          {/* Inner Reticule Rings */}
          <div className="absolute w-28 h-28 rounded-full border border-dashed border-sky-400/50 animate-[spin_10s_linear_infinite]" />
          <div className="absolute w-20 h-20 rounded-full border border-slate-600/70" />

          {/* Center Icon or Avatar Wireframe */}
          {scanState === 'VERIFIED' ? (
            <CheckCircle2 className="w-12 h-12 text-emerald-400 animate-bounce" />
          ) : (
            <Scan className={`w-10 h-10 transition-colors ${
              scanState !== 'IDLE' ? 'text-sky-400 animate-pulse' : 'text-slate-500'
            }`} />
          )}

          {/* Laser Scanning Bar */}
          {(scanState === 'DETECTING' || scanState === 'SCANNING' || scanState === 'MATCHING') && (
            <div className="absolute inset-x-0 h-0.5 bg-gradient-to-r from-transparent via-sky-400 to-transparent animate-[bounce_1.5s_infinite] opacity-80" />
          )}
        </div>

        {/* Live Camera Mode Badge */}
        <div className="absolute top-2.5 left-8 flex items-center gap-1.5 px-2 py-0.5 bg-slate-900/80 border border-slate-700 rounded-xs text-[9px] text-slate-300">
          <span className={`w-1.5 h-1.5 rounded-full ${scanState !== 'IDLE' ? 'bg-red-500 animate-ping' : 'bg-slate-500'}`} />
          <span>FEED: {useSimulatedFeed ? 'SIMULATED BIOMETRIC MATRIX' : 'LIVE OPTICAL SENSOR (OPT-01)'}</span>
        </div>

        {/* Biometric Confidence Overlay */}
        <div className="absolute bottom-2.5 right-8 font-mono text-[10px] text-right">
          <div className="text-slate-400 text-[8px]">MATCH CONFIDENCE</div>
          <div className={`font-bold ${confidence >= 90 ? 'text-emerald-400' : confidence >= 50 ? 'text-sky-400' : 'text-slate-300'}`}>
            {confidence.toFixed(1)}%
          </div>
        </div>

        {/* Operator Targeting Callout */}
        {scanState !== 'IDLE' && (
          <div className="absolute bottom-2.5 left-8 font-mono text-[9px] text-sky-400/90">
            <div>TARGET: <span className="text-white font-bold">{operatorName}</span></div>
            <div>CLEARANCE: <span className="text-amber-400 font-bold">{clearanceLevel}</span></div>
          </div>
        )}
      </div>

      {/* Dynamic Status Bar */}
      <div className={`p-2.5 rounded-sm border flex items-center justify-between ${
        scanState === 'VERIFIED'
          ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-300'
          : scanState !== 'IDLE'
          ? 'bg-sky-950/40 border-sky-500/50 text-sky-300'
          : 'bg-slate-900 border-slate-800 text-slate-400'
      }`}>
        <div className="flex items-center gap-2">
          {scanState === 'VERIFIED' ? (
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          ) : (
            <Scan className="w-4 h-4 text-sky-400 shrink-0" />
          )}
          <span className="font-bold tracking-wider text-[11px]">{statusText}</span>
        </div>
        <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded-xs bg-slate-800 border border-slate-700 text-white">
          {scanState}
        </span>
      </div>

      {/* Action Button Controls */}
      <div className="grid grid-cols-2 gap-2 pt-1">
        {scanState === 'IDLE' || scanState === 'FAILED' ? (
          <button
            onClick={handleStartScan}
            type="button"
            className="col-span-2 py-2.5 px-4 bg-[#003366] hover:bg-blue-700 text-white font-rajdhani font-bold text-sm tracking-wider uppercase rounded-sm shadow-sm transition-all flex items-center justify-center gap-2 border border-blue-500/30 cursor-pointer"
          >
            <Scan className="w-4 h-4" />
            <span>START ENTERPRISE BIOMETRIC SCAN</span>
          </button>
        ) : (
          <button
            onClick={handleRetry}
            type="button"
            disabled={scanState === 'VERIFIED'}
            className="col-span-2 py-2.5 px-4 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 font-rajdhani font-bold text-sm tracking-wider uppercase rounded-sm transition-all flex items-center justify-center gap-2 border border-slate-700 cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            <span>ABORT & RETRY BIOMETRIC SCAN</span>
          </button>
        )}

        <button
          onClick={() => setUseSimulatedFeed(!useSimulatedFeed)}
          type="button"
          className="py-1.5 px-3 bg-slate-900 hover:bg-slate-800 text-slate-300 text-[10px] uppercase tracking-wider font-semibold rounded-sm border border-slate-700 transition-all flex items-center justify-center gap-1.5 cursor-pointer"
        >
          <Camera className="w-3.5 h-3.5 text-sky-400" />
          <span>{useSimulatedFeed ? 'SWITCH TO CAMERA' : 'USE SIMULATED FEED'}</span>
        </button>

        <button
          onClick={onFallbackToPassword}
          type="button"
          className="py-1.5 px-3 bg-slate-900 hover:bg-slate-800 text-slate-300 text-[10px] uppercase tracking-wider font-semibold rounded-sm border border-slate-700 transition-all flex items-center justify-center gap-1.5 cursor-pointer"
        >
          <KeyRound className="w-3.5 h-3.5 text-amber-400" />
          <span>FALLBACK TO PASSWORD / PKI</span>
        </button>
      </div>
    </div>
  );
});
BiometricScanner.displayName = 'BiometricScanner';
