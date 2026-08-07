import React, { useState } from 'react';
import { Panel, StatusBadge } from '@/components';
import { Clock, Play, Pause, FastForward } from 'lucide-react';
import { useMissionStore } from '@/stores/useMissionStore';
import { formatTime } from '@/utils';

interface MissionTimelinePanelProps {
  onSelectStage: (stageRef: string) => void;
}

export const MissionTimelinePanel: React.FC<MissionTimelinePanelProps> = React.memo(({ onSelectStage }) => {
  const [isPlaying, setIsPlaying] = useState(true);
  const { missionTimeSec, timelineEvents, simulationSettings, setSimulationSettings } = useMissionStore();

  const handlePlayToggle = () => {
    const nextPlay = !isPlaying;
    setIsPlaying(nextPlay);
    setSimulationSettings({ simulationSpeed: nextPlay ? 1 : 0 });
  };

  const handleSpeedCycle = () => {
    const current = simulationSettings.simulationSpeed;
    const nextSpeed = current === 1 ? 4 : current === 4 ? 10 : 1;
    setSimulationSettings({ simulationSpeed: nextSpeed });
  };

  const speedLabel = simulationSettings.simulationSpeed === 1 ? '1X' : simulationSettings.simulationSpeed === 4 ? '4X' : simulationSettings.simulationSpeed === 10 ? '10X' : 'PAUSED';

  return (
    <Panel
      title="Synchronized Flight Data Recorder & Event Timeline"
      icon={Clock}
      className="h-full"
      right={
        <div className="flex items-center gap-2 font-mono text-xs">
          <button
            onClick={handlePlayToggle}
            className="flex items-center gap-1 px-2 py-0.5 bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-700 rounded-xs font-bold transition-colors cursor-pointer"
          >
            {isPlaying ? <Pause className="w-3 h-3 text-sky-400" /> : <Play className="w-3 h-3 text-sky-400" />}
            <span>{isPlaying ? 'PAUSE' : 'PLAY'}</span>
          </button>
          <button
            onClick={handleSpeedCycle}
            className="flex items-center gap-1 px-2 py-0.5 bg-sky-950 text-sky-300 border border-sky-800 hover:bg-sky-900 rounded-xs font-bold transition-colors cursor-pointer"
          >
            <FastForward className="w-3 h-3 text-sky-400" />
            <span>{speedLabel}</span>
          </button>
          <span className="text-amber-400 font-bold ml-2">MISSION TIME: {formatTime(Math.round(missionTimeSec))}</span>
        </div>
      }
    >
      <div className="space-y-3 font-mono text-xs select-none">
        {/* Continuous Interactive Time Scrub Slider */}
        <div className="flex items-center gap-3 bg-slate-950/80 p-2 rounded-sm border border-slate-800">
          <span className="text-[10px] font-bold text-slate-400">T-00:00</span>
          <input
            type="range"
            min={0}
            max={7200}
            value={Math.round(missionTimeSec)}
            onChange={(e) => {
              useMissionStore.setState({ missionTimeSec: Number(e.target.value) });
            }}
            className="flex-1 accent-sky-400 cursor-pointer h-2 bg-slate-800 rounded-lg"
          />
          <span className="text-[10px] font-bold text-slate-400">T+02:00 (LIVE)</span>
        </div>

        {/* Synchronized Avionics and Sensor Tracks */}
        <div className="grid grid-cols-5 gap-2">
          {timelineEvents.slice(0, 5).map((ev) => (
            <div
              key={ev.id}
              onClick={() => onSelectStage(ev.subsystemRef)}
              className="p-2 bg-slate-950/80 border border-slate-800 hover:border-sky-500 hover:bg-slate-900 rounded-xs transition-all cursor-pointer shadow-sm group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[9px] font-bold text-slate-400 group-hover:text-sky-300">{ev.timestamp}</span>
                  <StatusBadge status={ev.severity} size="sm" />
                </div>
                <div className="font-bold text-white group-hover:text-sky-400 text-xs leading-tight truncate">
                  {ev.title}
                </div>
                <div className="text-[10px] text-slate-300 font-normal mt-0.5 line-clamp-2">
                  {ev.description}
                </div>
              </div>
              <div className="mt-2 text-[9px] font-bold text-sky-400 uppercase tracking-wider flex items-center justify-between border-t border-slate-800 pt-1">
                <span>{ev.category}</span>
                <span>[{ev.subsystemRef.toUpperCase()}]</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Panel>
  );
});
MissionTimelinePanel.displayName = 'MissionTimelinePanel';
