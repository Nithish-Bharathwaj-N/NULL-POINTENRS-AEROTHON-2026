import React, { useState, useEffect } from 'react';
import { CheckCircle2, Loader2, Server, Activity, Cpu, Brain, Boxes, Database, ShieldCheck, Terminal, Radio } from 'lucide-react';

interface BootstrapStep {
  id: string;
  label: string;
  statusText: string;
  icon: React.ReactNode;
  delayMs: number;
}

const BOOTSTRAP_STEPS: BootstrapStep[] = [
  { id: 'identity', label: 'Operator Identity Verified', statusText: 'PKI PASSED', icon: <ShieldCheck className="w-4 h-4 text-[#2E7D32]" />, delayMs: 350 },
  { id: 'profile', label: 'Mission Profile Loaded', statusText: 'NO. 45 SQN', icon: <Server className="w-4 h-4 text-[#1565C0]" />, delayMs: 400 },
  { id: 'telemetry', label: 'Telemetry Bus Connected', statusText: 'ARINC-429 LINK', icon: <Activity className="w-4 h-4 text-[#0097A7]" />, delayMs: 400 },
  { id: 'twin', label: 'Digital Twin Ready', statusText: 'WASM CAD ENGINE', icon: <Boxes className="w-4 h-4 text-[#1565C0]" />, delayMs: 450 },
  { id: 'physics', label: 'Physics Solver Online', statusText: '1.00 Hz REAL-TIME', icon: <Terminal className="w-4 h-4 text-[#2E7D32]" />, delayMs: 400 },
  { id: 'ai', label: 'AI Diagnostics Ready', statusText: 'AERONET-V4 RUL', icon: <Brain className="w-4 h-4 text-[#1565C0]" />, delayMs: 450 },
  { id: 'db', label: 'Historical Database Connected', statusText: 'SQLITE ONLINE', icon: <Database className="w-4 h-4 text-[#ED6C02]" />, delayMs: 400 },
  { id: 'databus', label: 'Secure Databus Established', statusText: 'LINK-17 ENCRYPTED', icon: <Radio className="w-4 h-4 text-[#0097A7]" />, delayMs: 400 },
  { id: 'ready', label: 'Mission Control Ready', statusText: 'WORKSTATION ONLINE', icon: <Cpu className="w-4 h-4 text-[#2E7D32]" />, delayMs: 450 },
];

interface ServiceLoaderProps {
  onComplete: () => void;
  operatorName: string;
  role: string;
}

export const ServiceLoader: React.FC<ServiceLoaderProps> = React.memo(({ onComplete, operatorName, role }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [completedStepIds, setCompletedStepIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (currentStepIndex >= BOOTSTRAP_STEPS.length) {
      const finishTimer = setTimeout(() => {
        onComplete();
      }, 400);
      return () => clearTimeout(finishTimer);
    }

    const currentStep = BOOTSTRAP_STEPS[currentStepIndex];
    const timer = setTimeout(() => {
      setCompletedStepIds((prev) => new Set(prev).add(currentStep.id));
      setCurrentStepIndex((prev) => prev + 1);
    }, currentStep.delayMs);

    return () => clearTimeout(timer);
  }, [currentStepIndex, onComplete]);

  const progressPercent = Math.min(100, Math.round(((completedStepIds.size) / BOOTSTRAP_STEPS.length) * 100));

  return (
    <div className="w-full bg-[#FFFFFF] border border-[#D9E1EA] rounded-sm p-5 space-y-4 font-mono text-xs select-none shadow-sm">
      {/* Bootstrap Terminal Header */}
      <div className="flex items-center justify-between border-b border-[#D9E1EA] pb-2.5">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-xs bg-[#1565C0] animate-pulse" />
          <span className="font-bold text-xs tracking-wider uppercase text-[#10233A]">
            HAL AEROSPACE • ENTERPRISE WORKSTATION INITIALIZATION SEQUENCE
          </span>
        </div>
        <span className="text-[10px] text-[#1565C0] font-bold bg-[#F7F8FA] px-2 py-0.5 rounded-xs border border-[#D9E1EA]">
          BOOT PROGRESS: {progressPercent}%
        </span>
      </div>

      {/* Progress Bar (Engineering Blue #1565C0) */}
      <div className="w-full bg-[#F7F8FA] h-2 rounded-xs overflow-hidden border border-[#D9E1EA]">
        <div 
          className="bg-gradient-to-r from-[#1565C0] via-[#0097A7] to-[#2E7D32] h-full transition-all duration-300 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Operator Target Profile Info */}
      <div className="p-2.5 bg-[#F7F8FA] border border-[#D9E1EA] rounded-xs flex items-center justify-between">
        <div>
          <div className="text-[9px] text-[#5E738D]">AUTHORIZING OPERATOR:</div>
          <div className="font-bold text-[#10233A] text-xs">{operatorName}</div>
        </div>
        <div className="text-right">
          <div className="text-[9px] text-[#5E738D]">ASSIGNED CLEARANCE:</div>
          <div className="font-bold text-[#1565C0] text-xs">{role} // CLEARED</div>
        </div>
      </div>

      {/* Sequential 9-Step Checklist Matrix */}
      <div className="space-y-1.5 max-h-[220px] overflow-y-auto pr-1">
        {BOOTSTRAP_STEPS.map((step, idx) => {
          const isDone = completedStepIds.has(step.id);
          const isCurrent = idx === currentStepIndex;

          return (
            <div
              key={step.id}
              className={`p-2 rounded-xs border transition-all flex items-center justify-between ${
                isDone
                  ? 'bg-[#F7F8FA] border-[#2E7D32]/40 text-[#10233A]'
                  : isCurrent
                  ? 'bg-[#FFFFFF] border-[#1565C0] text-[#10233A] shadow-2xs scale-[1.01]'
                  : 'bg-[#FFFFFF] border-[#EEF2F7] text-[#5E738D] opacity-60'
              }`}
            >
              <div className="flex items-center gap-2.5">
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-[#2E7D32] shrink-0 animate-bounce" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 text-[#1565C0] animate-spin shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border border-[#D9E1EA] flex items-center justify-center text-[9px] font-bold text-[#5E738D]">
                    {idx + 1}
                  </div>
                )}
                <span className={`font-semibold tracking-wide text-xs ${isDone ? 'text-[#10233A]' : isCurrent ? 'text-[#1565C0] font-bold' : ''}`}>
                  {step.label}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-xs uppercase border ${
                  isDone
                    ? 'bg-[#FFFFFF] border-[#2E7D32]/40 text-[#2E7D32]'
                    : isCurrent
                    ? 'bg-[#F7F8FA] border-[#1565C0] text-[#1565C0] animate-pulse'
                    : 'bg-[#F7F8FA] border-[#D9E1EA] text-[#5E738D]'
                }`}>
                  {isDone ? step.statusText : isCurrent ? 'INITIALIZING...' : 'STANDBY'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Terminal System Footer */}
      <div className="pt-1.5 border-t border-[#D9E1EA] flex items-center justify-between text-[9px] text-[#5E738D]">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#2E7D32] animate-ping" />
          <span>MIL-STD-498 • SECURITY GATEWAY ENCRYPTED</span>
        </div>
        <span>ESTIMATED TIMEFRAME: &lt; 2.50s</span>
      </div>
    </div>
  );
});

ServiceLoader.displayName = 'ServiceLoader';
