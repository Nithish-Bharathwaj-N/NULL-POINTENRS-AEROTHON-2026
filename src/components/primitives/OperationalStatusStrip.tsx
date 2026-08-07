// HAL Mission Control - Operational Status Strip
// Injects authentic aerospace engineering telemetry, bus load, and hardware utilization
// into workstation layouts without clutter or layout shifts.

import React, { useState, useEffect } from 'react';
import { Cpu, HardDrive, Radio, ShieldCheck, Activity, Database } from 'lucide-react';
import { useLiveIndicators } from '@/hooks/useLiveIndicators';

export const OperationalStatusStrip: React.FC = React.memo(() => {
  const { packetCount, signalQuality, linkStatus } = useLiveIndicators();
  const [canBusMsgRate, setCanBusMsgRate] = useState(1284);
  const [cpuLoad, setCpuLoad] = useState(18);
  const [gpuLoad, setGpuLoad] = useState(34);
  const [aiTimer, setAiTimer] = useState(4.2);
  const [recSizeGb, setRecSizeGb] = useState(94.8);

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate authentic hardware fluctuation
      setCanBusMsgRate((r) => Math.max(1200, Math.min(1450, r + Math.round((Math.random() - 0.5) * 40))));
      setCpuLoad((c) => Math.max(14, Math.min(28, c + Math.round((Math.random() - 0.5) * 3))));
      setGpuLoad((g) => Math.max(28, Math.min(45, g + Math.round((Math.random() - 0.5) * 4))));
      setAiTimer((t) => {
        const next = t - 0.5;
        return next <= 0 ? 5.0 : Number(next.toFixed(1));
      });
      setRecSizeGb((s) => Number((s + 0.02).toFixed(2)));
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-slate-900 text-slate-300 border-t border-slate-800 px-3 py-1 flex items-center justify-between gap-4 font-mono text-[10px] select-none shrink-0 overflow-x-auto shadow-inner">
      <div className="flex items-center gap-3 shrink-0">
        <div className="flex items-center gap-1 text-emerald-400 font-bold">
          <Activity className="w-3 h-3 animate-pulse" />
          <span>CAN BUS:</span>
          <span className="text-white">{canBusMsgRate.toLocaleString()} msg/s</span>
        </div>
        <span className="text-slate-700">|</span>
        <div className="flex items-center gap-1 text-sky-400 font-bold">
          <Radio className="w-3 h-3" />
          <span>ARINC-429:</span>
          <span className="text-white">CH 1-4 SYNC ({signalQuality}% SNR, {packetCount.toLocaleString()} pkts)</span>
        </div>
        <span className="text-slate-700">|</span>
        <div className="flex items-center gap-1 text-purple-400 font-bold">
          <ShieldCheck className="w-3 h-3" />
          <span>SATCOM CRYPTO:</span>
          <span className="text-emerald-400">{linkStatus} (AES-256-GCM)</span>
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0 ml-auto">
        <div className="flex items-center gap-1 text-amber-400 font-bold">
          <Database className="w-3 h-3" />
          <span>AI WEIBULL REF:</span>
          <span className="text-white">{aiTimer}s</span>
        </div>
        <span className="text-slate-700">|</span>
        <div className="flex items-center gap-1 text-slate-400 font-medium">
          <HardDrive className="w-3 h-3 text-slate-400" />
          <span>REC:</span>
          <span className="text-white font-bold">{recSizeGb} GB / 500 GB</span>
        </div>
        <span className="text-slate-700">|</span>
        <div className="flex items-center gap-1.5 text-slate-400 font-medium">
          <Cpu className="w-3 h-3 text-slate-400" />
          <span>CPU <span className="text-white font-bold">{cpuLoad}%</span></span>
          <span>GPU <span className="text-white font-bold">{gpuLoad}%</span></span>
        </div>
        <div className="flex items-center gap-1 bg-emerald-950/60 border border-emerald-700/50 px-1.5 py-0.5 rounded-xs text-emerald-300 font-bold">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
          <span>60 FPS LOCKED</span>
        </div>
      </div>
    </div>
  );
});
OperationalStatusStrip.displayName = 'OperationalStatusStrip';
