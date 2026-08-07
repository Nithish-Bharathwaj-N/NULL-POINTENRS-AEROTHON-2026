import React from 'react';
import { useAuthStore, useAircraftStore, useUiStore } from '@/stores';
import { Shield, Clock, Wifi, Globe, Plane, Radio, Activity, Lock } from 'lucide-react';
import { useLiveIndicators } from '@/hooks/useLiveIndicators';

export const WorkstationHeader: React.FC = React.memo(() => {
  const { user, logout } = useAuthStore();
  const { selectedAircraft } = useAircraftStore();
  const { hudUnits, toggleHudUnits } = useUiStore();
  const { istTime, missionTime, packetCount, signalQuality, heartbeat, linkStatus } = useLiveIndicators();

  return (
    <header className="bg-slate-900 text-slate-300 border-b border-slate-800 px-3 py-1 flex items-center justify-between gap-3 font-mono text-[10px] select-none shrink-0 overflow-hidden w-full shadow-inner z-30">
      {/* Left Telemetry Group */}
      <div className="flex items-center gap-2.5 shrink-0 overflow-hidden">
        {/* Brand Logo & Mission Title */}
        <div className="flex items-center gap-2 pr-2 border-r border-slate-800 shrink-0">
          <div className="w-5 h-5 rounded-full flex items-center justify-center shrink-0" style={{ background: 'conic-gradient(#2563EB, #16A34A, #D97706, #2563EB)' }}>
            <div className="w-3.5 h-3.5 rounded-full bg-[#060B16] flex items-center justify-center border border-slate-700">
              <Plane size={9} className="text-sky-400" />
            </div>
          </div>
          <div className="shrink-0 whitespace-nowrap">
            <span className="font-rajdhani text-xs font-bold text-white uppercase tracking-wider">HAL <span className="font-normal text-slate-400">Mission Control</span></span>
          </div>
        </div>

        {/* Tail Number & Aircraft Model */}
        <div className="flex items-center gap-1 shrink-0 whitespace-nowrap">
          <span className="text-white font-bold">{selectedAircraft.tailNumber}</span>
          <span className="text-sky-400 text-[9px] font-bold">({selectedAircraft.type})</span>
        </div>

        <span className="text-slate-700">|</span>

        {/* Live Heartbeat Indicator */}
        <div className="flex items-center gap-1.5 text-emerald-400 font-bold shrink-0 whitespace-nowrap">
          <span
            className="w-2 h-2 rounded-full shrink-0 transition-colors duration-300"
            style={{ backgroundColor: heartbeat ? '#16A34A' : '#86efac' }}
          />
          <span>LIVE</span>
        </div>

        <span className="text-slate-700">|</span>

        {/* ARINC-429 Telemetry Stream */}
        <div className="flex items-center gap-1 text-emerald-400 font-bold shrink-0 whitespace-nowrap">
          <Activity className="w-3 h-3 animate-pulse text-emerald-400 shrink-0" />
          <span>PKT:</span>
          <span className="text-white">{packetCount.toLocaleString()}</span>
        </div>

        <span className="text-slate-700">|</span>

        {/* Signal Quality */}
        <div className="flex items-center gap-1 text-sky-400 font-bold shrink-0 whitespace-nowrap">
          <Wifi className="w-3 h-3 text-sky-400 shrink-0" />
          <span className="text-white">{signalQuality}%</span>
        </div>

        <span className="text-slate-700">|</span>

        {/* SATCOM Link Status */}
        <div className="flex items-center gap-1 text-purple-400 font-bold shrink-0 whitespace-nowrap">
          <Radio className="w-3 h-3 text-sky-400 shrink-0" />
          <span className="text-emerald-400">{linkStatus}</span>
        </div>
      </div>

      {/* Right Controls & Clock Group */}
      <div className="flex items-center gap-2.5 shrink-0 ml-auto whitespace-nowrap">
        {/* Mission Elapsed Time */}
        <div className="flex items-center gap-1 text-sky-300 font-bold shrink-0">
          <span className="text-slate-400 font-normal">MSRT</span>
          <span className="text-white">{missionTime}</span>
        </div>

        <span className="text-slate-700">|</span>

        {/* HUD Units Toggle */}
        <button
          onClick={toggleHudUnits}
          className="flex items-center gap-1 text-sky-400 hover:text-white font-bold cursor-pointer transition-colors shrink-0"
          title="Toggle Metric vs Imperial HUD Units"
        >
          <Globe className="w-3 h-3 text-sky-400 shrink-0" />
          <span>HUD: <span className="text-white">{hudUnits === 'metric' ? 'METRIC' : 'IMPERIAL'}</span></span>
        </button>

        <span className="text-slate-700">|</span>

        {/* IST Live Clock */}
        <div className="flex items-center gap-1 text-amber-400 font-medium shrink-0">
          <Clock className="w-3 h-3 text-amber-400 shrink-0" />
          <span className="text-white font-bold">{istTime}</span>
        </div>

        {/* Operator Security Clearance Badge */}
        {user && (
          <>
            <span className="text-slate-700">|</span>
            <div className="flex items-center gap-1 shrink-0">
              <Shield className="w-3 h-3 text-sky-400" />
              <span className="font-bold text-white">{user.name}</span>
              <span className="text-sky-400 font-bold uppercase text-[9px]">({user.role})</span>
            </div>
          </>
        )}
      </div>
    </header>
  );
});
WorkstationHeader.displayName = 'WorkstationHeader';
