import React, { useState, useMemo } from 'react';
import { CADViewMode } from '@/types';
import { CADToolbar } from './CADToolbar';
import { statusColor } from '@/utils';
import { useMissionStore } from '@/stores/useMissionStore';

interface DigitalTwinViewportProps {
  selectedStageRef: string | null;
  onSelectStage: (stageRef: string | null) => void;
}

export const DigitalTwinViewport: React.FC<DigitalTwinViewportProps> = React.memo(({ selectedStageRef, onSelectStage }) => {
  const [viewMode, setViewMode] = useState<CADViewMode>('NORMAL ASSEMBLY');
  const [zoom, setZoom] = useState<number>(1.0);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const stages = useMissionStore((state) => state.subsystemStages);
  const telemetry = useMissionStore((state) => state.telemetry);
  const alerts = useMissionStore((state) => state.alerts);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  // Dynamic spool rotation speeds (CSS animation duration in seconds)
  const n1SpeedSec = useMemo(() => Math.max(0.15, 6000 / Math.max(500, telemetry.n1Rpm)).toFixed(2), [telemetry.n1Rpm]);
  const n2SpeedSec = useMemo(() => Math.max(0.1, 10000 / Math.max(500, telemetry.n2Rpm)).toFixed(2), [telemetry.n2Rpm]);

  // Is there an active thermal overtemp or surge cascade?
  const hasCascadeAlert = useMemo(() => alerts.some((a) => a.severity === 'CRITICAL' || a.title.includes('Surge')), [alerts]);

  return (
    <div className="bg-white border border-slate-300 rounded-sm shadow-sm flex flex-col h-full overflow-hidden select-none relative">
      <CADToolbar viewMode={viewMode} setViewMode={setViewMode} zoom={zoom} setZoom={setZoom} setPan={setPan} />

      <div
        className={`flex-1 flex items-center justify-center relative bg-[#0B132B] overflow-hidden ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Encapsulated GPU Accelerated Animations */}
        <style>{`
          @keyframes airflow-stream {
            0% { stroke-dashoffset: 40; }
            100% { stroke-dashoffset: 0; }
          }
          @keyframes spin-cw {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          @keyframes spin-ccw {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(-360deg); }
          }
          .animate-airflow {
            animation: airflow-stream 1.2s linear infinite;
          }
          .animate-airflow-fast {
            animation: airflow-stream 0.5s linear infinite;
          }
        `}</style>

        {/* CAD Grid Background Overlay */}
        <div
          className="absolute inset-0 opacity-20 pointer-events-none"
          style={{
            backgroundImage: 'linear-gradient(to right, #1E293B 1px, transparent 1px), linear-gradient(to bottom, #1E293B 1px, transparent 1px)',
            backgroundSize: '32px 32px',
          }}
        />

        {/* CAD Coordinate Triad Overlay */}
        <div className="absolute top-4 left-4 bg-slate-900/90 border border-slate-700 p-2.5 shadow-lg z-10 font-mono text-[10px] text-slate-200 pointer-events-none min-w-[240px]">
          <div className="font-bold text-sky-400 border-b border-slate-700 pb-1 mb-1.5 uppercase tracking-wider flex items-center justify-between gap-4">
            <span>LCA TEJAS MK1A • GE F404-IN20</span>
            <span className="text-[9px] bg-emerald-950 text-emerald-400 border border-emerald-800 px-1.5 py-0.5 font-bold">LIVE TWIN ACTIVE</span>
          </div>
          <div className="flex items-center gap-3 text-[10px]">
            <span className="text-red-400 font-bold">X: AXIAL (N1/N2)</span>
            <span className="text-emerald-400 font-bold">Y: RADIAL</span>
            <span className="text-blue-400 font-bold">Z: CIRCUMFERENTIAL</span>
          </div>
          <div className="mt-1.5 text-slate-400 text-[9px] flex justify-between border-t border-slate-800/80 pt-1">
            <span>VIEWPORT: <span className="font-bold text-white">{viewMode}</span></span>
            <span>SCALE: <span className="font-bold text-white">{Math.round(zoom * 100)}%</span></span>
          </div>
        </div>

        {/* Live Operational Telemetry Overlay HUD */}
        <div className="absolute top-4 right-4 bg-slate-900/90 border border-slate-700 rounded-xs p-2 shadow-lg z-10 font-mono text-[10px] text-slate-200 pointer-events-none min-w-[180px]">
          <div className="text-[9px] font-bold text-sky-400 uppercase border-b border-slate-700 pb-0.5 mb-1 flex justify-between">
            <span>TRANSDUCER KINEMATICS</span>
            <span className="animate-pulse text-emerald-400">● 60 FPS</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">N1 FAN RPM:</span>
            <span className="font-bold text-white">{Math.round(telemetry.n1Rpm).toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">N2 SPOOL RPM:</span>
            <span className="font-bold text-white">{Math.round(telemetry.n2Rpm).toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">T4 TURBINE INLET:</span>
            <span className={`font-bold ${telemetry.t4Kelvin > 1750 ? 'text-red-400 animate-pulse' : 'text-amber-400'}`}>
              {Math.round(telemetry.t4Kelvin - 273.15)} °C
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">CORE VIBRATION:</span>
            <span className={`font-bold ${telemetry.vibrationG > 1.8 ? 'text-red-400 font-black' : 'text-emerald-400'}`}>
              {telemetry.vibrationG.toFixed(2)} G
            </span>
          </div>
        </div>

        {/* 3D Digital Twin SVG Schematic Cutaway */}
        <div
          className="absolute inset-0 m-auto flex items-center justify-center transition-transform duration-100 ease-out pointer-events-none"
          style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}
        >
          <svg viewBox="0 0 1000 400" className="w-[92%] max-h-[72%] overflow-visible drop-shadow-2xl pointer-events-auto">
            <defs>
              <radialGradient id="thermalCore" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#EF4444" stopOpacity="0.8" />
                <stop offset="60%" stopColor="#F97316" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#1E293B" stopOpacity="0" />
              </radialGradient>
              <radialGradient id="surgeCascade" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#DC2626" stopOpacity="0.9" />
                <stop offset="50%" stopColor="#B91C1C" stopOpacity="0.5" />
                <stop offset="100%" stopColor="#000000" stopOpacity="0" />
              </radialGradient>
            </defs>

            {/* Engine Outer Nacelle & Casing */}
            <path
              d="M 50,120 L 250,110 L 450,110 L 650,115 L 850,130 L 950,150 L 950,250 L 850,270 L 650,285 L 450,290 L 250,290 L 50,280 Z"
              fill={viewMode === 'THERMAL FIELD' ? '#1E293B' : viewMode === 'X-RAY SPOOLS' ? '#0F172A' : '#334155'}
              stroke="#64748B"
              strokeWidth="3"
              className="transition-colors duration-300"
            />

            {/* Thermal / Surge Heat Overlay Glow (When in Thermal mode or active anomaly) */}
            {(viewMode === 'THERMAL FIELD' || hasCascadeAlert) && (
              <ellipse
                cx="550"
                cy="200"
                rx="280"
                ry="90"
                fill={hasCascadeAlert ? 'url(#surgeCascade)' : 'url(#thermalCore)'}
                className={hasCascadeAlert ? 'animate-pulse' : 'transition-opacity duration-700'}
              />
            )}

            {/* Dual Concentric Spool Centerline Shafts */}
            <line x1="50" y1="200" x2="950" y2="200" stroke="#94A3B8" strokeWidth="2" strokeDasharray="8 4" />
            {viewMode === 'X-RAY SPOOLS' && (
              <>
                <rect x="250" y="195" width="400" height="10" fill="#00A86B" opacity="0.6" rx="2" />
                <rect x="100" y="190" width="600" height="20" fill="#1E90FF" opacity="0.4" rx="4" />
              </>
            )}

            {/* Rotating N1 Low Pressure Fan Rotor Blades (Station 1 / 2) */}
            <g
              style={{
                transformOrigin: '140px 200px',
                animation: `spin-cw ${n1SpeedSec}s linear infinite`,
              }}
              className="opacity-90 pointer-events-none"
            >
              <line x1="140" y1="130" x2="140" y2="270" stroke="#38BDF8" strokeWidth="6" strokeLinecap="round" />
              <line x1="105" y1="165" x2="175" y2="235" stroke="#38BDF8" strokeWidth="5" strokeLinecap="round" />
              <line x1="105" y1="235" x2="175" y2="165" stroke="#38BDF8" strokeWidth="5" strokeLinecap="round" />
            </g>

            {/* Rotating N2 High Pressure Compressor Spool Blades (Station 3) */}
            <g
              style={{
                transformOrigin: '320px 200px',
                animation: `spin-ccw ${n2SpeedSec}s linear infinite`,
              }}
              className="opacity-90 pointer-events-none"
            >
              <line x1="320" y1="140" x2="320" y2="260" stroke="#FBBF24" strokeWidth="6" strokeLinecap="round" />
              <line x1="290" y1="170" x2="350" y2="230" stroke="#FBBF24" strokeWidth="5" strokeLinecap="round" />
              <line x1="290" y1="230" x2="350" y2="170" stroke="#FBBF24" strokeWidth="5" strokeLinecap="round" />
            </g>

            {/* Rotating High Pressure Turbine Blades (Station 4.5 / 5) */}
            <g
              style={{
                transformOrigin: '680px 200px',
                animation: `spin-cw ${n2SpeedSec}s linear infinite`,
              }}
              className="opacity-90 pointer-events-none"
            >
              <line x1="680" y1="145" x2="680" y2="255" stroke="#F97316" strokeWidth="6" strokeLinecap="round" />
              <line x1="655" y1="175" x2="705" y2="225" stroke="#F97316" strokeWidth="5" strokeLinecap="round" />
              <line x1="655" y1="225" x2="705" y2="175" stroke="#F97316" strokeWidth="5" strokeLinecap="round" />
            </g>

            {/* Animated Airflow Velocity Vectors (Intake → Exhaust Gas Path) */}
            <g className="pointer-events-none opacity-80">
              <path
                d="M 60,165 L 940,165"
                stroke="#38BDF8"
                strokeWidth="2"
                strokeDasharray="12 8"
                fill="none"
                className={hasCascadeAlert ? 'animate-airflow-fast stroke-amber-400' : 'animate-airflow'}
              />
              <path
                d="M 60,235 L 940,235"
                stroke="#38BDF8"
                strokeWidth="2"
                strokeDasharray="12 8"
                fill="none"
                className={hasCascadeAlert ? 'animate-airflow-fast stroke-amber-400' : 'animate-airflow'}
              />
              <path
                d="M 450,180 L 920,180"
                stroke="#F97316"
                strokeWidth="2.5"
                strokeDasharray="16 8"
                fill="none"
                className="animate-airflow-fast opacity-90"
              />
              <path
                d="M 450,220 L 920,220"
                stroke="#F97316"
                strokeWidth="2.5"
                strokeDasharray="16 8"
                fill="none"
                className="animate-airflow-fast opacity-90"
              />
            </g>

            {/* Interactive Subsystem Stages */}
            {stages.map((stg, idx) => {
              const isSelected = selectedStageRef === stg.ref;
              const xStart = 80 + idx * 105;
              const width = 95;
              const isThermal = viewMode === 'THERMAL FIELD';
              const isStress = viewMode === 'STRESS LOAD (FEA)';

              let fillCol = '#475569';
              if (isThermal) {
                fillCol = stg.temp > 1300 ? '#EF4444' : stg.temp > 800 ? '#F97316' : '#3B82F6';
              } else if (isStress) {
                fillCol = stg.pressure > 20 ? '#EF4444' : stg.pressure > 10 ? '#EAB308' : '#10B981';
              } else if (isSelected) {
                fillCol = '#003366';
              } else if (stg.status === 'CRITICAL') {
                fillCol = '#EF4444';
              } else if (stg.status === 'WARNING') {
                fillCol = '#F59E0B';
              }

              return (
                <g key={stg.ref} onClick={(e) => { e.stopPropagation(); onSelectStage(stg.ref); }} className="cursor-pointer group">
                  <rect
                    x={xStart}
                    y={130}
                    width={width}
                    height={140}
                    rx="4"
                    fill={fillCol}
                    fillOpacity="0.85"
                    stroke={isSelected ? '#00A86B' : '#94A3B8'}
                    strokeWidth={isSelected ? '4' : '2'}
                    className="transition-all duration-200 group-hover:opacity-100 group-hover:scale-[1.02]"
                  />
                  <text x={xStart + width / 2} y={195} textAnchor="middle" fill="#FFFFFF" fontSize="11" fontWeight="bold" fontFamily="JetBrains Mono">
                    {stg.ref.toUpperCase()}
                  </text>
                  <text x={xStart + width / 2} y={215} textAnchor="middle" fill="#E2E8F0" fontSize="9" fontFamily="JetBrains Mono">
                    {stg.health}% HLTH
                  </text>
                  {isSelected && (
                    <>
                      <circle cx={xStart + width / 2} cy={120} r="6" fill="#00A86B" className="animate-ping" />
                      <line x1={xStart + width / 2} y1={120} x2={xStart + width / 2} y2={130} stroke="#00A86B" strokeWidth="2" />
                    </>
                  )}
                </g>
              );
            })}

            {/* Fault Propagation Vectors (Pulsing Red Cascade Arrows during Anomaly) */}
            {hasCascadeAlert && (
              <g className="animate-pulse pointer-events-none">
                <path d="M 450,115 L 530,115" stroke="#EF4444" strokeWidth="4" markerEnd="url(#arrow)" />
                <path d="M 550,115 L 630,115" stroke="#EF4444" strokeWidth="4" markerEnd="url(#arrow)" />
                <text x="540" y="105" textAnchor="middle" fill="#EF4444" fontSize="11" fontWeight="bold" fontFamily="JetBrains Mono">
                  ⚠️ THERMAL RUNAWAY CASCADE PATH
                </text>
              </g>
            )}
          </svg>
        </div>

        {/* Bottom Interactive Subsystem Stage Ribbon */}
        <div className="absolute bottom-0 inset-x-0 bg-slate-900/95 border-t border-slate-800 p-2 flex items-center justify-between gap-1.5 overflow-x-auto z-10">
          <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider px-2 shrink-0 border-r border-slate-700">
            SUBSYSTEM SELECTOR:
          </div>
          <div className="flex items-center gap-1.5 overflow-x-auto flex-1">
            {stages.map((stg) => {
              const isSelected = selectedStageRef === stg.ref;
              const badgeCol = statusColor(stg.status);
              return (
                <button
                  key={stg.ref}
                  onClick={() => onSelectStage(stg.ref)}
                  className={`flex items-center gap-2 px-2.5 py-1 rounded-xs font-mono text-xs transition-all shrink-0 border ${
                    isSelected
                      ? 'bg-[#003366] text-white border-[#00A86B] shadow-md font-bold'
                      : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-700 hover:text-white'
                  }`}
                >
                  <span className="uppercase">{stg.ref}</span>
                  <span className="text-[10px] opacity-80">({stg.health}%)</span>
                  <span className={`w-2 h-2 rounded-full ${badgeCol}`} />
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
});
DigitalTwinViewport.displayName = 'DigitalTwinViewport';
