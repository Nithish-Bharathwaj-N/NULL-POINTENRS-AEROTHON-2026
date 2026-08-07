import React, { useMemo } from 'react';
import { Panel, StatusBadge, MiniSparkline } from '@/components';
import { Activity, Wifi, Radio, Zap, AlertCircle, ShieldCheck } from 'lucide-react';
import { useTelemetryStore, useMissionStore } from '@/stores';

export const TelemetryView: React.FC = React.memo(() => {
  const { isConnected, toggleLiveStreaming, historyBuffer } = useTelemetryStore();
  const telemetry = useMissionStore((s) => s.telemetry);
  const alerts = useMissionStore((s) => s.alerts);

  // Dynamically map live telemetry to 8 ARINC-429 transducer channels
  const channels = useMemo(() => {
    const last30 = historyBuffer.slice(-30);
    const getHist = (fn: (t: typeof telemetry) => number) => last30.map((p) => fn(p.sensors));

    const t4C = Math.round(telemetry.t4Kelvin - 273.15);
    const egtC = Math.round(telemetry.egtKelvin - 273.15);

    return [
      {
        id: 'TJ04-SER-88219-N1',
        name: 'Low Press Fan Speed (N1)',
        sensorRef: 'TJ04-LP',
        arinc429Word: '0246',
        channel: 'CH-01',
        current: Math.round(telemetry.n1Rpm),
        expected: 9850,
        delta: Number((telemetry.n1Rpm - 9850).toFixed(1)),
        unit: 'RPM',
        status: telemetry.n1Rpm > 11500 ? 'CRITICAL' : telemetry.n1Rpm > 10800 ? 'WARNING' : 'NOMINAL',
        history: getHist((s) => s.n1Rpm),
        crit: 11500,
        warn: 10800,
      },
      {
        id: 'TJ04-SER-88219-N2',
        name: 'High Press Core Spool (N2)',
        sensorRef: 'TJ04-HP',
        arinc429Word: '0247',
        channel: 'CH-02',
        current: Math.round(telemetry.n2Rpm),
        expected: 17200,
        delta: Number((telemetry.n2Rpm - 17200).toFixed(1)),
        unit: 'RPM',
        status: telemetry.n2Rpm > 19500 ? 'CRITICAL' : telemetry.n2Rpm > 18500 ? 'WARNING' : 'NOMINAL',
        history: getHist((s) => s.n2Rpm),
        crit: 19500,
        warn: 18500,
      },
      {
        id: 'TJ04-SER-88219-T4',
        name: 'Turbine Inlet Temp (T4)',
        sensorRef: 'TJ04-CB',
        arinc429Word: '0312',
        channel: 'CH-03',
        current: t4C,
        expected: 1350,
        delta: Number((t4C - 1350).toFixed(1)),
        unit: '°C',
        status: t4C > 1500 ? 'CRITICAL' : t4C > 1400 ? 'WARNING' : 'NOMINAL',
        history: getHist((s) => Math.round(s.t4Kelvin - 273.15)),
        crit: 1500,
        warn: 1400,
      },
      {
        id: 'TJ04-SER-88219-EGT',
        name: 'Exhaust Gas Temp (EGT / T5)',
        sensorRef: 'TJ04-EX',
        arinc429Word: '0313',
        channel: 'CH-04',
        current: egtC,
        expected: 780,
        delta: Number((egtC - 780).toFixed(1)),
        unit: '°C',
        status: egtC > 950 ? 'CRITICAL' : egtC > 850 ? 'WARNING' : 'NOMINAL',
        history: getHist((s) => Math.round(s.egtKelvin - 273.15)),
        crit: 950,
        warn: 850,
      },
      {
        id: 'TJ04-SER-88219-VIB',
        name: 'Core Vibration Transducer',
        sensorRef: 'TJ04-HP',
        arinc429Word: '0350',
        channel: 'CH-05',
        current: Number(telemetry.vibrationG.toFixed(2)),
        expected: 0.45,
        delta: Number((telemetry.vibrationG - 0.45).toFixed(2)),
        unit: 'G',
        status: telemetry.vibrationG > 2.0 ? 'CRITICAL' : telemetry.vibrationG > 1.6 ? 'WARNING' : 'NOMINAL',
        history: getHist((s) => Number(s.vibrationG.toFixed(2))),
        crit: 2.0,
        warn: 1.6,
      },
      {
        id: 'TJ04-SER-88219-P3',
        name: 'Combustor Static Press (P3)',
        sensorRef: 'TJ04-CB',
        arinc429Word: '0210',
        channel: 'CH-06',
        current: Number(telemetry.p3Bar.toFixed(1)),
        expected: 24.5,
        delta: Number((telemetry.p3Bar - 24.5).toFixed(1)),
        unit: 'Bar',
        status: telemetry.p3Bar > 30 ? 'CRITICAL' : telemetry.p3Bar > 27 ? 'WARNING' : 'NOMINAL',
        history: getHist((s) => Number(s.p3Bar.toFixed(1))),
        crit: 30,
        warn: 27,
      },
      {
        id: 'TJ04-SER-88219-WF',
        name: 'Fuel Flow Rate (Wf)',
        sensorRef: 'TJ04-AB',
        arinc429Word: '0220',
        channel: 'CH-07',
        current: Math.round(telemetry.fuelFlowKgH),
        expected: 3200,
        delta: Number((telemetry.fuelFlowKgH - 3200).toFixed(0)),
        unit: 'kg/h',
        status: telemetry.fuelFlowKgH > 7500 ? 'WARNING' : 'NOMINAL',
        history: getHist((s) => Math.round(s.fuelFlowKgH)),
        crit: 8500,
        warn: 7500,
      },
      {
        id: 'TJ04-SER-88219-OP',
        name: 'Oil Pressure Transducer',
        sensorRef: 'TJ04-LP',
        arinc429Word: '0340',
        channel: 'CH-08',
        current: Math.round(telemetry.oilPressurePsi),
        expected: 65,
        delta: Number((telemetry.oilPressurePsi - 65).toFixed(1)),
        unit: 'PSI',
        status: telemetry.oilPressurePsi < 35 ? 'CRITICAL' : telemetry.oilPressurePsi < 45 ? 'WARNING' : 'NOMINAL',
        history: getHist((s) => Math.round(s.oilPressurePsi)),
        crit: 35,
        warn: 45,
      },
    ];
  }, [telemetry, historyBuffer]);

  const critCount = useMemo(() => channels.filter((c) => c.status === 'CRITICAL').length, [channels]);
  const warnCount = useMemo(() => channels.filter((c) => c.status === 'WARNING').length, [channels]);

  return (
    <div className="p-3 h-full overflow-y-auto space-y-3 bg-[#0B132B]">
      {/* Top Engineering Summary Strip */}
      <div className="grid grid-cols-4 gap-3 font-mono text-xs">
        <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-sm shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase">ARINC-429 DATABUS CHANNELS</div>
            <div className="text-lg font-bold text-sky-300 mt-0.5">8 / 8 ONLINE</div>
            <div className="text-[9px] text-emerald-400 font-bold mt-0.5">● SYNCED (1,000 Hz ARINC WORD)</div>
          </div>
          <Radio className="w-8 h-8 text-sky-400/40" />
        </div>

        <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-sm shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase">ANOMALY TRANSDUCER TRIAGE</div>
            <div className={`text-lg font-bold mt-0.5 ${critCount > 0 ? 'text-red-400 animate-pulse' : warnCount > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
              {critCount} CRIT • {warnCount} WARN
            </div>
            <div className="text-[9px] text-slate-400 mt-0.5">{alerts.length} Active Diagnostic Work Orders</div>
          </div>
          {critCount > 0 ? <AlertCircle className="w-8 h-8 text-red-500/40 animate-pulse" /> : <ShieldCheck className="w-8 h-8 text-emerald-500/40" />}
        </div>

        <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-sm shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase">SENSOR NOISE & DRIFT FLOOR</div>
            <div className="text-lg font-bold text-white mt-0.5">±0.03 G • ±2.5 °C</div>
            <div className="text-[9px] text-slate-400 mt-0.5">Analog-to-Digital Quantization 16-bit</div>
          </div>
          <Zap className="w-8 h-8 text-amber-400/40" />
        </div>

        <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-sm shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase">BUS SIGNAL INTEGRITY</div>
            <div className="text-lg font-bold text-emerald-400 mt-0.5">99.98% SNR</div>
            <div className="text-[9px] text-slate-400 mt-0.5">Zero Parity or CRC Bit Errors</div>
          </div>
          <Activity className="w-8 h-8 text-emerald-400/40" />
        </div>
      </div>

      <Panel
        title="1Hz Real-Time ARINC-429 Transducer Stream & Signal Matrix"
        icon={Activity}
        right={
          <button
            onClick={toggleLiveStreaming}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-xs font-rajdhani font-bold text-xs uppercase tracking-wider transition-all cursor-pointer ${
              isConnected ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs' : 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
            }`}
          >
            <Wifi className="w-3.5 h-3.5" />
            <span>{isConnected ? 'STREAMING ACTIVE (1Hz)' : 'STREAM PAUSED'}</span>
          </button>
        }
      >
        <div className="overflow-x-auto font-mono text-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-800 text-sky-400 font-bold uppercase tracking-wider text-[10px] border-b border-slate-700">
                <th className="p-3">Transducer ID & Name</th>
                <th className="p-3">Subsystem Stage</th>
                <th className="p-3">ARINC-429 Word / Bus</th>
                <th className="p-3 text-right">Current Value</th>
                <th className="p-3 text-center">30s Telemetry Waveform</th>
                <th className="p-3 text-right">Expected Isentropic</th>
                <th className="p-3 text-right">Residual (Δ)</th>
                <th className="p-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {channels.map((ch) => {
                const isCrit = ch.status === 'CRITICAL';
                const isWarn = ch.status === 'WARNING';
                return (
                  <tr key={ch.id} className={`transition-colors ${isCrit ? 'bg-red-950/70 hover:bg-red-900/90' : isWarn ? 'bg-amber-950/70 hover:bg-amber-900/90' : 'hover:bg-slate-800/80'}`}>
                    <td className="p-3 font-bold text-white">
                      <div>{ch.name}</div>
                      <div className="text-[10px] font-normal text-slate-400">{ch.id}</div>
                    </td>
                    <td className="p-3 font-bold uppercase">
                      <span className="px-2 py-0.5 bg-slate-800 border border-slate-700 rounded-xs text-[10px] text-sky-300">
                        {ch.sensorRef}
                      </span>
                    </td>
                    <td className="p-3 text-slate-400 font-medium">
                      <span className="text-slate-200 font-bold">{ch.arinc429Word}</span> • {ch.channel}
                    </td>
                    <td className="p-3 text-right font-bold text-white text-sm">
                      {ch.current.toLocaleString()} <span className="text-[10px] font-normal text-sky-400">{ch.unit}</span>
                    </td>
                    <td className="p-3 text-center">
                      <MiniSparkline
                        data={ch.history}
                        width={100}
                        height={24}
                        showTrend={true}
                        thresholdWarn={ch.warn}
                        thresholdCrit={ch.crit}
                      />
                    </td>
                    <td className="p-3 text-right text-slate-300 font-medium">
                      {ch.expected.toLocaleString()} <span className="text-[10px] text-slate-400">{ch.unit}</span>
                    </td>
                    <td className={`p-3 text-right font-bold font-mono ${isCrit ? 'text-red-400 font-black' : isWarn ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {ch.delta > 0 ? `+${ch.delta.toLocaleString()}` : ch.delta.toLocaleString()} {ch.unit}
                    </td>
                    <td className="p-3 text-center">
                      <StatusBadge status={ch.status} size="md" />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
});
TelemetryView.displayName = 'TelemetryView';
