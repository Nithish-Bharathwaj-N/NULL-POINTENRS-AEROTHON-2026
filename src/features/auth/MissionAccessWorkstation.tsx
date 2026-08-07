import React, { useState, useEffect } from 'react';
import {
  Lock, UserCheck, Eye, EyeOff, Terminal, KeyRound,
  ArrowRight, ShieldCheck, Rocket, Layout, Layers, MonitorPlay, Ruler, PenTool, Wrench,
  FileText, History, Fingerprint, Server, Database, ChevronRight, AlertCircle, Wifi
} from 'lucide-react';
import { useAuthStore } from '@/stores';
import { LcaTejasWireframe } from './components/LcaTejasWireframe';
import { LiveWebcamScanner } from './components/LiveWebcamScanner';
import { OperatorRegistrationModal } from './components/OperatorRegistrationModal';

export type AuthStep = 'CREDENTIALS' | 'BIOMETRIC' | 'CLEARANCE' | 'BOOTSTRAP';

interface OperatorProfile {
  id: string;
  name: string;
  role: 'COMMANDER' | 'ENGINEER' | 'ANALYST' | 'ADMIN';
  callsign: string;
  squadron: string;
  clearanceLevel: string;
}

const PRESET_OPERATORS: OperatorProfile[] = [];

const TELEMETRY_MESSAGES = [
  'T4 COMBUSTOR TEMP 1723K • STATUS NOMINAL',
  'N2 SPOOL 18,230 RPM • PARITY OK',
  'VIBRATION 1.42G • HARMONIC CLEAR',
  'ARINC-429 LINK-17 ENCRYPTION VALID',
  'FUEL FLOW 4,210 KG/H • STABLE',
  'WING STATION 2 ASTRA MK1 BUS CLEARED',
];

const DEFAULT_NEW_OPERATOR: OperatorProfile = {
  id: 'NEW-OPERATOR',
  name: 'No Account Enrolled',
  role: 'ENGINEER',
  callsign: 'UNREGISTERED',
  squadron: 'IAF Propulsion Command',
  clearanceLevel: 'LEVEL 1 // ENROLLMENT REQUIRED',
};

export const MissionAccessWorkstation: React.FC = React.memo(() => {
  const { login } = useAuthStore();
  const [currentStep, setCurrentStep] = useState<AuthStep>('CREDENTIALS');
  const [operatorsList, setOperatorsList] = useState<OperatorProfile[]>(() => {
    try {
      const saved = localStorage.getItem('hal_mission_control_operators');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {}
    return PRESET_OPERATORS;
  });
  const [selectedOpIndex, setSelectedOpIndex] = useState<number>(0);
  const [password, setPassword] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [utcClock, setUtcClock] = useState<string>('');
  const [telemetryMsg, setTelemetryMsg] = useState<string>(TELEMETRY_MESSAGES[0]);
  const [authMode, setAuthMode] = useState<'REAL' | 'DEMO'>('REAL');
  const [isRegModalOpen, setIsRegModalOpen] = useState<boolean>(false);
  const [challengeId, setChallengeId] = useState<string>('DEMO_CHALLENGE_001');
  const [livenessAction, setLivenessAction] = useState<string>('BLINK');
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isLockedOut, setIsLockedOut] = useState<boolean>(false);

  const activeOperator = (operatorsList && operatorsList.length > 0) ? (operatorsList[selectedOpIndex] || operatorsList[0]) : DEFAULT_NEW_OPERATOR;

  // Persist operatorsList to localStorage whenever updated
  useEffect(() => {
    try {
      if (operatorsList && operatorsList.length > 0) {
        localStorage.setItem('hal_mission_control_operators', JSON.stringify(operatorsList));
      }
    } catch {}
  }, [operatorsList]);

  // Dual-stack fetch operators from backend API
  useEffect(() => {
    const loadOperators = async () => {
      try {
        let res: Response;
        try {
          const authUrl = (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1')
            ? '/api/v1/auth/operators'
            : 'http://127.0.0.1:8000/api/v1/auth/operators';
          res = await fetch(authUrl);
        } catch {
          res = await fetch('/api/v1/auth/operators');
        }
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          const loaded = data.map((op: any) => ({
            id: op.id || op.operator_id,
            name: op.name || op.full_name,
            role: op.role as any || 'ENGINEER',
            callsign: op.callsign || 'HAL-OPS',
            squadron: op.squadron || 'IAF Propulsion Command',
            clearanceLevel: `LEVEL ${op.role === 'COMMANDER' ? 5 : op.role === 'ENGINEER' ? 4 : 3} // ${op.role} CLEARANCE`,
          }));
          setOperatorsList(prev => {
            const ids = new Set(loaded.map(l => l.id));
            const merged = [...loaded, ...prev.filter(p => !ids.has(p.id))];
            localStorage.setItem('hal_mission_control_operators', JSON.stringify(merged));
            return merged;
          });
        }
      } catch {}
    };
    loadOperators();
  }, []);

  // UTC Clock
  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setUtcClock(now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC');
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  // Telemetry ticker
  useEffect(() => {
    let i = 0;
    const id = setInterval(() => {
      i = (i + 1) % TELEMETRY_MESSAGES.length;
      setTelemetryMsg(TELEMETRY_MESSAGES[i]);
    }, 3000);
    return () => clearInterval(id);
  }, []);

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    login(activeOperator.name || 'NITHISH', activeOperator.role || 'COMMANDER');
  };

  const handleBiometricSuccess = () => setCurrentStep('CLEARANCE');
  const handleBootMissionControl = () => {
    setCurrentStep('BOOTSTRAP');
    setTimeout(() => {
      login(activeOperator.name, activeOperator.role);
    }, 3000);
  };

  return (
    <div className={`flex flex-col h-screen w-screen overflow-hidden bg-[#F8FAFC] text-[#0F172A] font-sans select-none ${isLockedOut ? 'border-4 border-[#DC2626]' : ''}`}>
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          TOP HEADER RIBBON
          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <header className="h-16 bg-[#FFFFFF] border-b border-[#CBD5E1] px-6 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#0F172A] rounded-full flex items-center justify-center text-white">
              <Rocket className="w-5 h-5 -rotate-45" />
            </div>
            <div className="flex flex-col justify-center">
              <div className="text-[16px] font-black tracking-widest uppercase text-[#0F172A] leading-tight">HAL AEROSPACE</div>
              <div className="text-[10px] text-[#64748B] tracking-widest uppercase font-bold">PROPULSION COMMAND</div>
            </div>
          </div>
          <div className="h-10 border-l border-[#CBD5E1] mx-2" />
          <div className="flex flex-col justify-center">
            <div className="text-[16px] font-black tracking-widest uppercase text-[#0F172A] leading-tight">MISSION ACCESS WORKSTATION</div>
            <div className="text-[10px] text-[#64748B] tracking-widest uppercase font-bold">SECURE ENGINEERING PLATFORM</div>
          </div>
        </div>

        <div className="flex items-center h-full text-[10px] font-bold uppercase tracking-widest">
          <div className="flex flex-col justify-center h-full border-l border-[#CBD5E1] px-6">
            <span className="text-[#64748B] mb-0.5">SYSTEM TIME (UTC)</span>
            <span className="text-[13px] font-black font-mono">{utcClock || '---'}</span>
          </div>
          <div className="flex flex-col justify-center h-full border-l border-[#CBD5E1] px-6 bg-[#F0FDF4]">
            <span className="text-[#64748B] mb-0.5">PLATFORM STATUS</span>
            <span className="text-[13px] font-black text-[#166534] flex items-center gap-1.5">
              <span className="w-2 h-2 bg-[#16A34A] rounded-full eng-led-pulse" /> SECURE MODE
            </span>
          </div>
          <div className="flex flex-col justify-center h-full border-l border-[#CBD5E1] px-6">
            <span className="text-[#64748B] mb-0.5">SOFTWARE BUILD</span>
            <span className="text-[13px] font-black text-[#0F172A]">v2026.2.2-PROD</span>
          </div>
          <div className="flex flex-col justify-center h-full border-l border-[#CBD5E1] px-6 bg-[#FEF2F2]">
            <span className="text-[#64748B] mb-0.5">AUTH STATUS</span>
            <span className="text-[13px] font-black text-[#991B1B] flex items-center gap-1.5">
              <span className="w-2 h-2 bg-[#DC2626] rounded-full" /> UNAUTHENTICATED
            </span>
          </div>
          <div className="flex flex-col justify-center h-full border-l border-[#CBD5E1] px-6">
            <span className="text-[#64748B] mb-0.5">SECURITY CLASSIFICATION</span>
            <span className="text-[13px] font-black text-[#DC2626] flex items-center gap-1.5">
              <span className="w-2 h-2 bg-[#DC2626] rounded-full" /> TOP SECRET
            </span>
          </div>
          <div className="flex items-center gap-2 h-full border-l border-[#CBD5E1] px-6">
            <button
              onClick={() => setAuthMode(authMode === 'REAL' ? 'DEMO' : 'REAL')}
              className={`px-3 py-2 text-[10px] font-mono font-black tracking-widest uppercase border transition-colors ${authMode === 'REAL' ? 'bg-[#0F172A] text-[#38BDF8] border-[#0F172A]' : 'bg-[#E2E8F0] text-[#0F172A] border-[#CBD5E1]'}`}
              title="Toggle between live optical webcam scan and demo mode simulation"
            >
              MODE: {authMode}
            </button>
            <button
              onClick={() => setIsRegModalOpen(true)}
              className="px-4 py-2 border border-[#0F172A] text-[10px] font-black tracking-widest text-[#0F172A] hover:bg-[#0F172A] hover:text-white transition-colors"
            >
              ENROLL OPERATOR
            </button>
          </div>
        </div>
      </header>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          MAIN 3-COLUMN WORKSPACE
          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <main className="flex-1 flex overflow-hidden bg-[#F1F5F9]">
        
        {/* LEFT: CAD TOOLBAR */}
        <aside className="w-24 bg-[#0F172A] border-r border-[#1E293B] flex flex-col items-center py-6 gap-6 shrink-0 z-10 shadow-[2px_0_15px_rgba(0,0,0,0.15)]">
          {[
            { icon: Layout, label: 'WORKSPACE', active: true },
            { icon: Layers, label: 'LAYERS' },
            { icon: MonitorPlay, label: 'VIEWS' },
            { icon: Ruler, label: 'MEASURE' },
            { icon: PenTool, label: 'ANNOTATE' },
            { icon: Wrench, label: 'TOOLS' },
            { icon: FileText, label: 'DOCUMENTS' },
            { icon: History, label: 'HISTORY' },
          ].map((tool, i) => (
            <div key={i} className={`flex flex-col items-center gap-2 cursor-pointer transition-colors group ${tool.active ? 'text-[#60A5FA]' : 'text-[#64748B] hover:text-[#FFFFFF]'}`}>
              {tool.active ? (
                <div className="w-12 h-12 border-2 border-[#60A5FA] bg-[#1E293B] flex items-center justify-center group-hover:bg-[#334155] transition-colors">
                  <tool.icon className="w-5 h-5" />
                </div>
              ) : (
                <div className="w-12 h-12 flex items-center justify-center group-hover:bg-[#1E293B] transition-colors border-2 border-transparent group-hover:border-[#334155]">
                  <tool.icon className="w-5 h-5" />
                </div>
              )}
              <span className="text-[9px] font-bold uppercase tracking-widest">{tool.label}</span>
            </div>
          ))}
        </aside>

        {/* CENTER: CAD VIEWPORT */}
        <section className="flex-1 flex flex-col relative p-6">
          <LcaTejasWireframe authStep={currentStep} isLockedOut={isLockedOut} />
        </section>

        {/* RIGHT: AUTHENTICATION CONSOLE */}
        <aside className="w-[450px] bg-[#FFFFFF] border-l border-[#CBD5E1] flex flex-col shrink-0 shadow-[-2px_0_15px_rgba(0,0,0,0.05)] z-10 overflow-y-auto">
          
          <div className="px-8 py-6 border-b border-[#E2E8F0] bg-[#F8FAFC]">
            <div className="flex items-center gap-3 mb-2">
              <Lock className="w-5 h-5 text-[#0F172A]" />
              <span className="text-[14px] font-black tracking-widest uppercase text-[#0F172A]">AUTHENTICATION CONSOLE</span>
            </div>
            <p className="text-[11px] text-[#64748B] tracking-wide">Secure access to mission engineering systems</p>
          </div>

          <div className="p-8 space-y-8">
            
            {/* 1. OPERATOR IDENTIFICATION */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 bg-[#0F172A] text-white flex items-center justify-center text-[10px] font-black">1</div>
                <h3 className="text-[11px] font-black text-[#0F172A] tracking-widest uppercase">OPERATOR IDENTIFICATION</h3>
              </div>
              {loginError && (
                <div className="p-2.5 border border-[#DC2626] bg-[#FEF2F2] flex items-center gap-2 text-[#991B1B] text-[10px] font-mono">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{loginError}</span>
                </div>
              )}
              <div className="space-y-3 pl-8">
                {operatorsList.length === 0 ? (
                  <div className="p-3 border border-sky-600/40 bg-sky-950/20 rounded-sm space-y-2 font-mono">
                    <div className="text-[11px] font-bold flex items-center gap-2 text-sky-700">
                      <UserCheck className="w-4 h-4 text-sky-600" />
                      <span>NO REGISTERED OPERATORS FOUND</span>
                    </div>
                    <p className="text-[10px] text-slate-600 leading-normal">
                      The database contains zero operator accounts. Click below to register your operator profile and password.
                    </p>
                    <button
                      type="button"
                      onClick={() => setIsRegModalOpen(true)}
                      className="w-full mt-1.5 py-2 px-3 bg-[#0F172A] hover:bg-slate-800 text-white font-bold text-[11px] uppercase tracking-wider transition-colors shadow-sm flex items-center justify-center gap-2 cursor-pointer"
                    >
                      <UserCheck className="w-3.5 h-3.5 text-sky-400" />
                      <span>REGISTER NEW OPERATOR ACCOUNT</span>
                    </button>
                  </div>
                ) : (
                  <div>
                    <label className="block text-[10px] font-bold text-[#64748B] uppercase tracking-widest mb-1.5">EMPLOYEE ID</label>
                    <div className="relative">
                      <select
                        value={selectedOpIndex}
                        onChange={e => setSelectedOpIndex(Number(e.target.value))}
                        className="w-full appearance-none bg-[#FFFFFF] border border-[#CBD5E1] focus:border-[#0F172A] px-3 py-2.5 text-[#0F172A] font-mono text-[11px] outline-none cursor-pointer"
                      >
                        {operatorsList.map((op, idx) => (
                          <option key={op.id} value={idx}>[{op.id}] {op.name}</option>
                        ))}
                      </select>
                      <UserCheck className="absolute right-3 top-2.5 w-4 h-4 text-[#94A3B8] pointer-events-none" />
                    </div>
                  </div>
                )}
                <div>
                  <label className="block text-[10px] font-bold text-[#64748B] uppercase tracking-widest mb-1.5">PASSWORD</label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      className="w-full bg-[#FFFFFF] border border-[#CBD5E1] focus:border-[#0F172A] px-3 py-2.5 text-[#0F172A] font-mono text-[11px] outline-none"
                      placeholder="Enter Password"
                    />
                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-2.5 text-[#94A3B8] hover:text-[#0F172A]">
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* 2. PKI AUTHENTICATION */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 bg-[#0F172A] text-white flex items-center justify-center text-[10px] font-black">2</div>
                <h3 className="text-[11px] font-black text-[#0F172A] tracking-widest uppercase">PKI AUTHENTICATION</h3>
              </div>
              <div className="space-y-3 pl-8">
                <div>
                  <label className="block text-[10px] font-bold text-[#64748B] uppercase tracking-widest mb-1.5">CERTIFICATE</label>
                  <div className="relative">
                    <select className="w-full appearance-none bg-[#FFFFFF] border border-[#CBD5E1] focus:border-[#0F172A] px-3 py-2.5 text-[#0F172A] font-mono text-[11px] outline-none cursor-pointer">
                      <option>Select PKI Certificate</option>
                      <option>HAL_RSA_4096_CERT_01</option>
                    </select>
                    <ChevronRight className="absolute right-3 top-3 w-4 h-4 text-[#94A3B8] rotate-90 pointer-events-none" />
                  </div>
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-[#64748B] uppercase tracking-widest mb-1.5">PKI STATUS</label>
                  <div className="p-2.5 border border-[#CBD5E1] bg-[#F8FAFC] flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-[#64748B]" />
                    <span className="text-[10px] font-mono font-bold text-[#64748B]">NOT VERIFIED</span>
                  </div>
                </div>
              </div>
            </div>

            {/* 3. BIOMETRIC VERIFICATION */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 bg-[#0F172A] text-white flex items-center justify-center text-[10px] font-black">3</div>
                <h3 className="text-[11px] font-black text-[#0F172A] tracking-widest uppercase">BIOMETRIC VERIFICATION</h3>
              </div>
              <div className="space-y-3 pl-8">
                <div>
                  <label className="block text-[10px] font-bold text-[#64748B] uppercase tracking-widest mb-1.5">BIOMETRIC SENSOR STATUS</label>
                  {currentStep === 'BIOMETRIC' ? (
                    <LiveWebcamScanner
                      challengeId={challengeId}
                      livenessAction={livenessAction}
                      operatorName={activeOperator.name}
                      clearanceLevel={activeOperator.clearanceLevel}
                      authMode={authMode}
                      onScanSuccess={handleBiometricSuccess}
                      onFallbackToPassword={() => setCurrentStep('CREDENTIALS')}
                      onLockout={() => setIsLockedOut(true)}
                    />
                  ) : (
                    <div className="p-3 border border-[#CBD5E1] bg-[#F8FAFC] flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Fingerprint className="w-6 h-6 text-[#94A3B8]" />
                        <div className="flex flex-col">
                          <span className="text-[11px] font-black tracking-widest text-[#0F172A]">{currentStep === 'CLEARANCE' || currentStep === 'BOOTSTRAP' ? 'VERIFIED' : 'STANDBY'}</span>
                          <span className="text-[9px] font-bold text-[#64748B]">{currentStep === 'CLEARANCE' || currentStep === 'BOOTSTRAP' ? 'Vector match confirmed' : 'Live face verification required'}</span>
                        </div>
                      </div>
                      <div className={`w-2 h-2 rounded-full ${currentStep === 'CLEARANCE' || currentStep === 'BOOTSTRAP' ? 'bg-[#16A34A]' : 'bg-[#0F172A]'}`} />
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 4. SECURITY CLEARANCE */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className={`w-5 h-5 flex items-center justify-center text-[10px] font-black ${(currentStep === 'CLEARANCE' || currentStep === 'BOOTSTRAP') ? 'bg-[#16A34A] text-white' : 'bg-[#0F172A] text-white'}`}>4</div>
                <h3 className="text-[11px] font-black text-[#0F172A] tracking-widest uppercase">SECURITY CLEARANCE</h3>
              </div>
              <div className="space-y-3 pl-8">
                <div>
                  <label className="block text-[10px] font-bold text-[#64748B] uppercase tracking-widest mb-1.5">CLEARANCE LEVEL</label>
                  <div className="relative">
                    <select className={`w-full appearance-none bg-[#FFFFFF] border border-[#CBD5E1] px-3 py-2.5 font-mono text-[11px] outline-none ${(currentStep === 'CLEARANCE' || currentStep === 'BOOTSTRAP') ? 'text-[#16A34A] font-black border-[#16A34A]' : 'text-[#94A3B8] cursor-not-allowed'}`} disabled>
                      <option>{(currentStep === 'CLEARANCE' || currentStep === 'BOOTSTRAP') ? activeOperator.clearanceLevel : 'Authorization Required'}</option>
                    </select>
                    <ChevronRight className={`absolute right-3 top-3 w-4 h-4 rotate-90 pointer-events-none ${(currentStep === 'CLEARANCE' || currentStep === 'BOOTSTRAP') ? 'text-[#16A34A]' : 'text-[#CBD5E1]'}`} />
                  </div>
                </div>
              </div>
            </div>

            {/* ACTION BUTTON */}
            <div className="pt-4 border-t border-[#E2E8F0] mt-6">
              {currentStep === 'BOOTSTRAP' ? (
                <div className="w-full bg-[#0F172A] text-[#16A34A] py-4 px-6 flex flex-col gap-2 font-mono border border-[#16A34A]">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Terminal className="w-4 h-4" />
                      <span className="text-[11px] font-black tracking-widest uppercase">BOOTING KERNEL...</span>
                    </div>
                    <span className="text-[10px] font-bold">PLEASE WAIT</span>
                  </div>
                  <div className="w-full h-1 bg-[#1E293B] overflow-hidden mt-1">
                    <div className="h-full bg-[#16A34A] animate-[pulse_1s_ease-in-out_infinite] w-[75%]" />
                  </div>
                </div>
              ) : currentStep === 'CLEARANCE' ? (
                 <button
                  type="button"
                  onClick={handleBootMissionControl}
                  className="w-full bg-[#16A34A] hover:bg-[#15803D] text-[#FFFFFF] py-4 px-6 flex items-center justify-between transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <Terminal className="w-4 h-4" />
                    <span className="text-[12px] font-black tracking-widest uppercase">BOOT MISSION CONTROL</span>
                  </div>
                  <ArrowRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleCredentialsSubmit}
                  disabled={currentStep === 'BIOMETRIC'}
                  className="w-full bg-[#0F172A] hover:bg-[#1E293B] disabled:bg-[#64748B] disabled:cursor-not-allowed text-[#FFFFFF] py-4 px-6 flex items-center justify-between transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <Lock className="w-4 h-4" />
                    <span className="text-[12px] font-black tracking-widest uppercase">INITIATE SECURE SESSION</span>
                  </div>
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
              <p className="text-[9px] font-bold text-[#64748B] mt-4 leading-relaxed">
                All authentication attempts are monitored and recorded. Unauthorized access is strictly prohibited.
              </p>
            </div>
            
            {/* IN-CONSOLE RESTRICTION WARNING */}
            <div className="mt-6 flex items-center gap-3 p-4 bg-[#F8FAFC] border border-[#CBD5E1]">
              <EyeOff className="w-6 h-6 text-[#64748B]" />
              <div className="flex flex-col">
                <span className="text-[9px] font-black uppercase tracking-widest text-[#64748B] mb-0.5">DATA VISIBILITY</span>
                <span className="text-[11px] font-black uppercase text-[#DC2626] mb-0.5">RESTRICTED</span>
                <span className="text-[9px] font-bold text-[#64748B]">Authentication required</span>
              </div>
            </div>

          </div>
        </aside>
      </main>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          BOTTOM SYSTEM SERVICES RIBBON
          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <footer className="h-16 bg-[#F8FAFC] border-t border-[#CBD5E1] flex items-center justify-between shrink-0 pl-6 pr-0">
        
        {/* Left Stats Area */}
        <div className="flex items-center gap-12 h-full py-2">
          
          <div className="flex flex-col justify-center gap-1">
            <span className="text-[8px] font-black text-[#64748B] uppercase tracking-widest">PLATFORM INTEGRITY</span>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#16A34A]" />
              <div className="flex flex-col">
                <span className="text-[11px] font-black text-[#16A34A]">SECURE</span>
                <span className="text-[8px] font-bold text-[#64748B]">System integrity verified</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col justify-center gap-1">
            <span className="text-[8px] font-black text-[#64748B] uppercase tracking-widest">TELEMETRY STREAM</span>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-black text-[#1565C0] font-mono">{telemetryMsg}</span>
            </div>
          </div>

          <div className="flex flex-col justify-center gap-1">
            <span className="text-[8px] font-black text-[#64748B] uppercase tracking-widest">SESSION STATUS</span>
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-[#0F172A]" />
              <div className="flex flex-col">
                <span className="text-[11px] font-black text-[#DC2626]">UNAUTHENTICATED</span>
                <span className="text-[8px] font-bold text-[#64748B]">No active session</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col justify-center gap-1">
            <span className="text-[8px] font-black text-[#64748B] uppercase tracking-widest">AUDIT LOG</span>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-[#0F172A]" />
              <div className="flex flex-col">
                <span className="text-[11px] font-black text-[#1565C0]">MONITORING ACTIVE</span>
                <span className="text-[8px] font-bold text-[#64748B]">All activities recorded</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Subsystems List */}
        <div className="flex items-center h-full border-l border-[#CBD5E1]">
          <div className="flex items-center h-full bg-[#FFFFFF] px-6 text-[11px] font-black tracking-widest text-[#0F172A]">
            SYSTEM SERVICES
          </div>
          
          <div className="flex items-center gap-6 px-6 text-[8px] font-bold uppercase tracking-widest text-[#64748B] h-full overflow-hidden">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4" />
              <div className="flex flex-col"><span className="text-[#0F172A]">AUTH SERVICE</span><span className="text-[#16A34A] flex items-center gap-1"><span className="w-1.5 h-1.5 bg-[#16A34A] rounded-full eng-led-pulse" /> ONLINE</span></div>
            </div>
            <div className="flex items-center gap-2">
              <KeyRound className="w-4 h-4" />
              <div className="flex flex-col"><span className="text-[#0F172A]">PKI SERVICE</span><span className="text-[#16A34A] flex items-center gap-1"><span className="w-1.5 h-1.5 bg-[#16A34A] rounded-full eng-led-pulse" /> ONLINE</span></div>
            </div>
            <div className="flex items-center gap-2">
              <UserCheck className="w-4 h-4" />
              <div className="flex flex-col"><span className="text-[#0F172A]">IDENTITY PROVIDER</span><span className="text-[#16A34A] flex items-center gap-1"><span className="w-1.5 h-1.5 bg-[#16A34A] rounded-full eng-led-pulse" /> ONLINE</span></div>
            </div>
            <div className="flex items-center gap-2">
              <Fingerprint className="w-4 h-4" />
              <div className="flex flex-col"><span className="text-[#0F172A]">BIOMETRIC SERVICE</span><span className="text-[#16A34A] flex items-center gap-1"><span className="w-1.5 h-1.5 bg-[#16A34A] rounded-full eng-led-pulse" /> ONLINE</span></div>
            </div>
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              <div className="flex flex-col"><span className="text-[#0F172A]">AUDIT LOGGER</span><span className="text-[#16A34A] flex items-center gap-1"><span className="w-1.5 h-1.5 bg-[#16A34A] rounded-full eng-led-pulse" /> ONLINE</span></div>
            </div>
            <div className="flex items-center gap-2">
              <Wifi className="w-4 h-4" />
              <div className="flex flex-col"><span className="text-[#0F172A]">SECURE TUNNEL</span><span className="text-[#16A34A] flex items-center gap-1"><span className="w-1.5 h-1.5 bg-[#16A34A] rounded-full eng-led-pulse" /> ONLINE</span></div>
            </div>
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4" />
              <div className="flex flex-col"><span className="text-[#0F172A]">DATABASE</span><span className="text-[#16A34A] flex items-center gap-1"><span className="w-1.5 h-1.5 bg-[#16A34A] rounded-full eng-led-pulse" /> ONLINE</span></div>
            </div>
          </div>
          
          <div className="flex items-center justify-center gap-3 h-full bg-[#0F172A] px-8 text-white min-w-[200px]">
            <ShieldCheck className="w-6 h-6 text-[#16A34A]" />
            <div className="flex flex-col">
              <span className="text-[9px] font-bold uppercase tracking-widest text-[#94A3B8]">NETWORK STATUS</span>
              <span className="text-[12px] font-black uppercase text-[#16A34A]">SECURE</span>
              <span className="text-[8px] font-bold text-[#CBD5E1]">Perimeter Protected</span>
            </div>
          </div>
        </div>
      </footer>

      {/* Operator Registration Modal */}
      <OperatorRegistrationModal
        isOpen={isRegModalOpen}
        onClose={() => setIsRegModalOpen(false)}
        onSuccess={(newOp) => {
          const formatted: OperatorProfile = {
            id: newOp.id || newOp.operator_id || `USR-${Math.floor(1000 + Math.random() * 9000)}`,
            name: newOp.name || newOp.full_name || 'Registered Operator',
            role: (newOp.role as any) || 'ENGINEER',
            callsign: newOp.callsign || 'HAL-OPS',
            squadron: newOp.squadron || 'IAF Propulsion Command',
            clearanceLevel: `LEVEL ${newOp.role === 'COMMANDER' ? 5 : 4} // ${newOp.role || 'ENGINEER'} CLEARANCE`,
          };
          setOperatorsList(prev => {
            const next = [formatted, ...prev.filter(p => p.id !== formatted.id)];
            try {
              localStorage.setItem('hal_mission_control_operators', JSON.stringify(next));
            } catch {}
            return next;
          });
          setSelectedOpIndex(0);
        }}
        authMode={authMode}
      />
    </div>
  );
});

MissionAccessWorkstation.displayName = 'MissionAccessWorkstation';
