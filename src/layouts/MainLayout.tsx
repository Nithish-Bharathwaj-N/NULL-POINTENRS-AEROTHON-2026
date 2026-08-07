import React from 'react';
import { WorkstationHeader, WorkstationSidebar, OperationalStatusStrip } from '@/components';

export interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = React.memo(({ children }) => {
  return (
    <div className="fixed inset-0 flex flex-col h-full w-full overflow-hidden bg-[#0B132B] m-0 p-0">
      {/* Top 48px Engineering Command Bar */}
      <WorkstationHeader />

      {/* Main Workstation Dock: Sidebar (Left 224px) + Active Viewport Area */}
      <div className="flex flex-1 overflow-hidden relative min-h-0 min-w-0">
        <WorkstationSidebar />
        <main className="flex-1 overflow-hidden relative bg-[#0B132B] flex flex-col min-h-0 min-w-0">
          <div className="flex-1 overflow-hidden relative min-h-0 min-w-0">
            {children}
          </div>
          {/* Global Operational Status Strip — CAN Bus, AI Ref, Recorder & Load */}
          <OperationalStatusStrip />
        </main>
      </div>
    </div>
  );
});
MainLayout.displayName = 'MainLayout';
