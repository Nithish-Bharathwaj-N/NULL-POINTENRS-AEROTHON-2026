import React from 'react';
import { AiMissionSummaryPanel } from '../overview';

export const AiDiagnosticsView: React.FC = React.memo(() => (
  <div className="p-3 h-full overflow-y-auto space-y-3 bg-[#0B132B]">
    <div className="grid grid-cols-12 gap-3 h-[600px]">
      <div className="col-span-12 h-full">
        <AiMissionSummaryPanel />
      </div>
    </div>
  </div>
));
AiDiagnosticsView.displayName = 'AiDiagnosticsView';
