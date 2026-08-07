import React from 'react';
import { AuthStep } from '../MissionAccessWorkstation';

interface LcaTejasWireframeProps {
  authStep?: AuthStep;
  isLockedOut?: boolean;
}

export const LcaTejasWireframe: React.FC<LcaTejasWireframeProps> = React.memo(() => {
  return (
    <div className="relative w-full h-full bg-[#F8FAFC] border border-[#CBD5E1] flex flex-col overflow-hidden select-none font-sans shadow-sm">
      
      {/* TOP RULER */}
      <div className="h-6 border-b border-[#CBD5E1] bg-[#F1F5F9] flex items-end pl-8">
        <div className="flex-1 flex justify-between px-10 text-[9px] font-mono text-[#64748B] font-bold">
          <span>-40</span>
          <span>-30</span>
          <span>-20</span>
          <span>-10</span>
          <span>0</span>
          <span>10</span>
          <span>20</span>
          <span>30</span>
          <span>40</span>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden relative">
        {/* LEFT RULER */}
        <div className="w-8 border-r border-[#CBD5E1] bg-[#F1F5F9] flex flex-col items-center justify-between py-10 text-[9px] font-mono text-[#64748B] font-bold shrink-0">
          <span>A</span>
          <span>B</span>
          <span>C</span>
          <span>D</span>
          <span>E</span>
          <span>F</span>
        </div>

        {/* CENTER CANVAS */}
        <div className="flex-1 relative bg-[#F8FAFC] overflow-hidden cad-grid-bg">
          
          {/* Engineering Crosshairs */}
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-1/2 left-0 w-full h-px bg-[#CBD5E1] opacity-50" />
            <div className="absolute top-0 left-1/2 w-px h-full bg-[#CBD5E1] opacity-50" />
            
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 border border-[#94A3B8] rounded-full" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1 h-1 bg-[#94A3B8] rounded-full" />
          </div>

          {/* Top Left Document Label */}
          <div className="absolute top-6 left-6 space-y-1 z-20">
            <h1 className="text-[12px] font-black uppercase tracking-widest text-[#0F172A]">CLASSIFIED ENGINEERING ASSET</h1>
            <p className="text-[10px] uppercase tracking-widest font-bold text-[#64748B]">DIGITAL TWIN WORKSPACE</p>
            
            <div className="mt-4 p-4 border border-[#CBD5E1] bg-[#FFFFFF]/80 backdrop-blur-sm inline-block relative">
              <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-[#0F172A]" />
              <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-[#0F172A]" />
              <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-[#0F172A]" />
              <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-[#0F172A]" />
              
              <p className="text-[8px] font-bold uppercase tracking-widest text-[#64748B] mb-1">DOCUMENT VISIBILITY</p>
              <p className="text-[14px] font-black uppercase tracking-widest text-[#DC2626]">RESTRICTED</p>
              <p className="text-[8px] font-bold uppercase tracking-widest text-[#0F172A] mt-1">AUTHORIZATION REQUIRED</p>
            </div>
          </div>

          {/* Top Right Access Control */}
          <div className="absolute top-6 right-6 border border-[#CBD5E1] bg-[#FFFFFF]/80 backdrop-blur-sm p-4 flex items-center gap-4 z-20">
            <div className="w-10 h-10 border border-[#CBD5E1] flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0F172A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
            </div>
            <div>
              <p className="text-[8px] font-bold uppercase tracking-widest text-[#64748B]">ACCESS CONTROL</p>
              <p className="text-[10px] font-black uppercase tracking-widest text-[#DC2626] mt-0.5">ALL SYSTEMS LOCKED</p>
              <p className="text-[9px] text-[#64748B] mt-0.5">Authenticate to proceed</p>
            </div>
          </div>

          {/* Bottom Left 3D Origin */}
          <div className="absolute bottom-8 left-8 w-16 h-16 pointer-events-none z-20">
            <div className="absolute bottom-0 left-0 w-px h-12 bg-[#DC2626]">
              <div className="absolute -top-1 -left-1 w-0 h-0 border-l-[3px] border-r-[3px] border-b-[4px] border-l-transparent border-r-transparent border-b-[#DC2626]" />
            </div>
            <span className="absolute bottom-12 -left-3 text-[8px] font-bold text-[#DC2626]">N</span>
            
            <div className="absolute bottom-0 left-0 w-px h-8 bg-[#16A34A] origin-bottom -rotate-45">
              <div className="absolute -top-1 -left-1 w-0 h-0 border-l-[3px] border-r-[3px] border-b-[4px] border-l-transparent border-r-transparent border-b-[#16A34A]" />
            </div>
            <span className="absolute bottom-6 left-6 text-[8px] font-bold text-[#16A34A]">Z</span>
            
            <div className="absolute bottom-0 left-0 h-px w-12 bg-[#2563EB]">
              <div className="absolute -right-1 -top-1 w-0 h-0 border-t-[3px] border-b-[3px] border-l-[4px] border-t-transparent border-b-transparent border-l-[#2563EB]" />
            </div>
            <span className="absolute -bottom-3 left-12 text-[8px] font-bold text-[#2563EB]">X</span>
          </div>

          {/* Bottom Right Grid Reference */}
          <div className="absolute bottom-6 right-6 border border-[#CBD5E1] bg-[#FFFFFF]/80 backdrop-blur-sm p-4 z-20 w-64">
             <p className="text-[8px] font-bold uppercase tracking-widest text-[#64748B] mb-2">GRID REFERENCE</p>
             <div className="flex justify-between items-center text-[10px] font-mono font-bold text-[#0F172A] border-b border-[#E2E8F0] pb-2">
               <span>X: ---.--</span>
               <span>Y: ---.--</span>
               <span>Z: ---.--</span>
             </div>
             <div className="flex justify-between items-center text-[9px] font-bold uppercase tracking-widest text-[#64748B] pt-2">
               <span>UNITS: MILLIMETERS</span>
               <span>SCALE: 1:50</span>
             </div>
          </div>

          {/* REDACTED SILHOUETTE HERO */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <svg viewBox="0 0 800 600" className="w-[90%] h-[90%] blur-[24px] opacity-70">
                 <path d="M400 50 L460 250 L780 350 L780 420 L460 420 L460 550 L400 580 L340 550 L340 420 L20 420 L20 350 L340 250 Z" fill="#94A3B8" />
              </svg>
            </div>

            <div className="absolute flex flex-col items-center pointer-events-auto">
              <div className="w-20 h-24 mb-6 relative flex items-center justify-center">
                <svg viewBox="0 0 100 115" className="absolute inset-0 w-full h-full">
                  <polygon points="50,0 100,28 100,86 50,115 0,86 0,28" fill="none" stroke="#CBD5E1" strokeWidth="2" />
                  <polygon points="50,6 93,31 93,83 50,109 7,83 7,31" fill="#FFFFFF" opacity="0.9" />
                </svg>
                <div className="relative z-10 w-10 h-10 bg-[#0F172A] rounded flex items-center justify-center shadow-inner">
                   <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                </div>
              </div>

              <h2 className="text-[20px] font-black tracking-[0.2em] uppercase text-[#0F172A]">CLASSIFIED ENGINEERING ASSET</h2>
              <p className="text-[11px] font-bold tracking-[0.3em] uppercase text-[#64748B] mt-2 mb-8">UNAUTHORIZED DISCLOSURE PROHIBITED</p>

              <div className="text-center text-[10px] text-[#0F172A] tracking-wider leading-relaxed mb-6">
                <p>This workspace contains sensitive engineering data.</p>
                <p>Authentication and authorization required to access</p>
                <p>Digital Twin, Telemetry, and Mission Systems.</p>
              </div>

              <div className="flex items-center gap-4 text-[10px] font-black uppercase tracking-widest text-[#0F172A] border border-[#CBD5E1] bg-[#FFFFFF] px-6 py-2 shadow-sm">
                <span>ZERO TRUST</span>
                <span className="w-px h-3 bg-[#CBD5E1]" />
                <span>NEED TO KNOW</span>
                <span className="w-px h-3 bg-[#CBD5E1]" />
                <span>LEAST PRIVILEGE</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
});

LcaTejasWireframe.displayName = 'LcaTejasWireframe';
