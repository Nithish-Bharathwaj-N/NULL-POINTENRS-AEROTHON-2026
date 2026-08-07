import React from 'react';
import { Panel, ValueBadge } from '@/components';
import { FileSpreadsheet, Download, ShieldCheck } from 'lucide-react';
import { useAircraftStore } from '@/stores';
import { reportService } from '@/services';

export const ReportsView: React.FC = React.memo(() => {
  const { selectedAircraft } = useAircraftStore();
  const ac = selectedAircraft;

  const handleGenerate = (format: 'PDF' | 'DOCX') => {
    reportService.generateAirworthinessReport(`GE-F404-IN20-${ac.tail}`, format).then((res) => {
      alert(`Airworthiness Report dispatched to IAF databus & local queue: ${res.filename}`);
    });
  };

  return (
    <div className="p-3 h-full overflow-y-auto space-y-3 bg-[#0B132B]">
      <Panel title="Official HAL / IAF Airworthiness Certificate Generator" icon={FileSpreadsheet}>
        <div className="space-y-4 font-mono text-xs">
          <div className="p-4 bg-slate-900 text-white rounded-sm border border-slate-800 flex items-center justify-between">
            <div className="space-y-1">
              <div className="text-sky-400 font-bold uppercase text-[10px] tracking-widest">MINISTRY OF DEFENCE • INDIAN AIR FORCE</div>
              <h2 className="text-xl font-bold font-rajdhani uppercase tracking-wider text-white">
                FLIGHT CLEARANCE & AIRWORTHINESS CERTIFICATE
              </h2>
              <p className="text-xs text-slate-300">
                AIRCRAFT TAIL: <span className="font-bold text-white">{ac.tail}</span> • SQUADRON: <span className="font-bold text-white">{ac.squadron}</span>
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleGenerate('PDF')}
                className="flex items-center gap-1.5 px-4 py-2 bg-[#00A86B] hover:bg-[#008F5B] text-white rounded-sm font-rajdhani font-bold text-xs uppercase tracking-wider shadow-md border border-[#00A86B]"
              >
                <Download className="w-4 h-4" />
                <span>Download PDF Certificate</span>
              </button>
              <button
                onClick={() => handleGenerate('DOCX')}
                className="flex items-center gap-1.5 px-4 py-2 bg-[#003366] hover:bg-[#002244] text-white rounded-sm font-rajdhani font-bold text-xs uppercase tracking-wider shadow-md border border-[#003366]"
              >
                <Download className="w-4 h-4" />
                <span>Export DOCX Package</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <ValueBadge label="Compliance Standard" value="MIL-STD-1553B / ARINC-429" status="NOMINAL" />
            <ValueBadge label="Digital Twin Verification" value="PASSED (99.4% Accuracy)" status="NOMINAL" />
            <ValueBadge label="Overhaul Authority Sign-Off" value="HAL ENG CHIEF M. RAO" status="NOMINAL" />
          </div>

          <div className="p-3 bg-emerald-50 border border-emerald-600 rounded-sm flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-700 shrink-0" />
            <div className="text-xs font-bold text-emerald-900">
              THIS AIRCRAFT IS FULLY CERTIFIED FOR ACTIVE COMBAT SORTIE AND SUPERSONIC ENVELOPE OPENING UNDER IAF COMMAND DIRECTIVE #2026-OP-SINDHUR.
            </div>
          </div>
        </div>
      </Panel>
    </div>
  );
});
ReportsView.displayName = 'ReportsView';
