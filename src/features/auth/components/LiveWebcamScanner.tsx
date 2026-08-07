import React, { useState, useEffect, useRef } from 'react';
import {
  CheckCircle2, AlertTriangle, Activity
} from 'lucide-react';
import { audio } from '../../../utils/audioEngine';

export type LiveBiometricScanState = 'IDLE' | 'CAPTURING' | 'VERIFYING' | 'VERIFIED' | 'FAILED';

interface LiveWebcamScannerProps {
  challengeId: string;
  livenessAction: string;
  operatorName: string;
  clearanceLevel?: string;
  authMode: 'REAL' | 'DEMO';
  onScanSuccess: (authData: any) => void;
  onFallbackToPassword?: () => void;
  onLockout?: () => void;
}

export const LiveWebcamScanner: React.FC<LiveWebcamScannerProps> = React.memo(({
  challengeId,
  livenessAction,
  operatorName,
  authMode,
  onScanSuccess,
  onLockout,
}) => {
  const [scanState, setScanState] = useState<LiveBiometricScanState>('IDLE');
  const [similarityScore, setSimilarityScore] = useState<number>(0);
  const [statusText, setStatusText] = useState<string>('Awaiting scan initiation');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [failedAttempts, setFailedAttempts] = useState<number>(0);
  const [qualityMetrics, setQualityMetrics] = useState({
    face_detected: true, face_centered: true,
    eyes_visible: true, lighting_acceptable: true,
  });

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Start webcam in REAL mode
  useEffect(() => {
    let mounted = true;
    if (authMode === 'REAL') {
      setStatusText('Requesting optical sensor access…');
      navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: 'user' } })
        .then((stream) => {
          if (!mounted) { stream.getTracks().forEach(t => t.stop()); return; }
          streamRef.current = stream;
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            setStatusText(`Optical feed active — perform [${livenessAction}]`);
          }
        })
        .catch(() => {
          setErrorMessage('Camera access denied. Check browser permissions or switch to DEMO mode.');
          setStatusText('Camera unavailable');
        });
    } else {
      setStatusText(`DEMO mode — perform [${livenessAction}] (simulated)`);
    }
    return () => {
      mounted = false;
      streamRef.current?.getTracks().forEach(t => t.stop());
    };
  }, [authMode, livenessAction]);

  const handleVerify = async () => {
    if (failedAttempts >= 3) return;
    
    // Start audio context and play scan blip
    audio.playScanBlip();
    
    setScanState('VERIFYING');
    setErrorMessage(null);
    setStatusText('Extracting biometric vector & verifying liveness…');

    let base64Frame = '';
    if (authMode === 'REAL' && videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        base64Frame = canvas.toDataURL('image/jpeg', 0.85);
      }
    }

    try {
      let res: Response;
      const verifyUrl = (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1')
        ? '/api/v1/auth/login/verify-face'
        : 'http://127.0.0.1:8000/api/v1/auth/login/verify-face';
      try {
        res = await fetch(verifyUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ challenge_id: challengeId, base64_frame: base64Frame || 'DEMO_FRAME', auth_mode: authMode }),
        });
      } catch {
        res = await fetch('/api/v1/auth/login/verify-face', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ challenge_id: challengeId, base64_frame: base64Frame || 'DEMO_FRAME', auth_mode: authMode }),
        });
      }
      const data = await res.json();

      if (!res.ok || !data.success) {
        audio.playErrorBuzzer();
        setScanState('FAILED');
        setSimilarityScore(data.similarity_score ? data.similarity_score * 100 : 38.4);

        const newAttempts = failedAttempts + 1;
        setFailedAttempts(newAttempts);

        if (newAttempts >= 3) {
          setErrorMessage('SYSTEM LOCKOUT: 3 FAILED BIOMETRIC ATTEMPTS DETECTED. PLEASE CONTACT ADMINISTRATOR.');
          if (onLockout) onLockout();
        } else {
          setErrorMessage(data.detail || data.message || 'BIOMETRIC MISMATCH: Access denied for unauthorized face.');
        }

        setStatusText('Verification denied — unauthorized identity');
        if (data.quality_metrics) setQualityMetrics(data.quality_metrics);
        return;
      }

      audio.playUnlockChime();
      setScanState('VERIFIED');
      setSimilarityScore(data.similarity_score ? data.similarity_score * 100 : 98.4);
      setStatusText('Identity confirmed — issuing JWT session token');
      if (data.quality_metrics) setQualityMetrics(data.quality_metrics);
      setTimeout(() => onScanSuccess(data), 1000);

    } catch {
      audio.playErrorBuzzer();
      setScanState('FAILED');
      setErrorMessage('Backend verification error. Ensure FastAPI server is running on port 8000.');
      setStatusText('Verification error');
    }
  };

  const handleRetry = () => {
    setScanState('IDLE');
    setErrorMessage(null);
    setSimilarityScore(0);
    setStatusText(`Ready — perform [${livenessAction}]`);
  };

  return (
    <div className="border border-[#CBD5E1] bg-[#F8FAFC] flex flex-col font-mono">
      
      {/* Header Status Bar */}
      <div className={`flex items-center justify-between px-3 py-2 border-b border-[#CBD5E1] ${scanState === 'VERIFIED' ? 'bg-[#DCFCE7] text-[#166534]' : scanState === 'FAILED' ? 'bg-[#FEF2F2] text-[#991B1B]' : 'bg-[#E2E8F0] text-[#0F172A]'}`}>
        <div className="flex items-center gap-2">
          {scanState === 'VERIFIED' ? <CheckCircle2 className="w-4 h-4" /> : scanState === 'FAILED' ? <AlertTriangle className="w-4 h-4" /> : <Activity className="w-4 h-4 animate-pulse" />}
          <span className="font-black text-[10px] tracking-widest uppercase">
            {scanState === 'VERIFIED' ? 'IDENTITY VERIFIED' : scanState === 'FAILED' ? 'VERIFICATION FAILED' : `CHALLENGE: ${livenessAction}`}
          </span>
        </div>
        <span className="text-[9px] font-black uppercase px-2 py-0.5 bg-[#FFFFFF] border border-[#CBD5E1]">
          {authMode === 'DEMO' ? 'SIMULATION' : 'OPTICAL'}
        </span>
      </div>

      {/* Viewfinder */}
      <div className="relative w-full bg-[#0F172A] flex items-center justify-center overflow-hidden" style={{ height: 180 }}>
        
        {/* Flat Targeting Bracket */}
        <div className={`absolute w-[120px] h-[120px] border-2 transition-colors duration-300 z-10 ${scanState === 'VERIFIED' ? 'border-[#22C55E]' : scanState === 'FAILED' ? 'border-[#DC2626]' : 'border-[#64748B]'}`}>
          <div className="absolute top-1/2 left-0 w-full h-px bg-white/20" />
          <div className="absolute top-0 left-1/2 w-px h-full bg-white/20" />
        </div>

        {authMode === 'REAL' ? (
          <video
            ref={videoRef}
            autoPlay playsInline muted
            className="absolute inset-0 w-full h-full object-cover opacity-80"
            style={{ transform: 'scaleX(-1)' }}
          />
        ) : (
          <div className="absolute inset-0 cad-grid-bg opacity-30" />
        )}

        <canvas ref={canvasRef} className="hidden" />

        {scanState === 'VERIFYING' && (
          <div className="absolute inset-0 bg-[#0F172A]/50 flex items-center justify-center z-20">
            <span className="text-[10px] text-[#60A5FA] font-black tracking-widest uppercase eng-led-pulse">ANALYZING VECTOR...</span>
          </div>
        )}

        {/* Quality Metrics */}
        <div className="absolute bottom-0 left-0 w-full bg-black/60 p-2 flex items-center justify-between text-[8px] font-black tracking-widest z-20">
          <div className="flex gap-2">
             <span className={(qualityMetrics as any)['face_centered'] ? 'text-[#22C55E]' : 'text-[#64748B]'}>CNTR</span>
             <span className={(qualityMetrics as any)['lighting_acceptable'] ? 'text-[#22C55E]' : 'text-[#64748B]'}>LUM</span>
             <span className={(qualityMetrics as any)['eyes_visible'] ? 'text-[#22C55E]' : 'text-[#64748B]'}>EYE</span>
          </div>
          <span className="text-[#64748B]">SIM_SCORE: {(similarityScore * 100).toFixed(1)}%</span>
        </div>
      </div>

      {/* Footer Controls */}
      <div className="p-3 bg-[#FFFFFF] flex flex-col gap-2">
        <div className="text-[9px] font-bold text-[#64748B] flex items-center justify-between">
           <span>{statusText}</span>
           {errorMessage && <span className="text-[#DC2626] truncate max-w-[200px]">{errorMessage}</span>}
        </div>
        
        <div className="flex gap-2 mt-1">
          {scanState === 'IDLE' && (
             <button onClick={handleVerify} disabled={authMode === 'REAL' && !qualityMetrics.face_centered} className="flex-1 bg-[#0F172A] hover:bg-[#1E293B] text-white py-2 text-[9px] font-black tracking-widest uppercase disabled:opacity-50">
               CAPTURE VECTOR
             </button>
          )}
          {(scanState === 'FAILED' || scanState === 'VERIFIED') && (
             <button onClick={handleRetry} className="flex-1 border border-[#CBD5E1] bg-[#F1F5F9] hover:bg-[#E2E8F0] text-[#0F172A] py-2 text-[9px] font-black tracking-widest uppercase">
               RESET SENSOR
             </button>
          )}
          {scanState === 'VERIFIED' && (
             <button onClick={onScanSuccess} className="flex-1 bg-[#16A34A] hover:bg-[#15803D] text-white py-2 text-[9px] font-black tracking-widest uppercase">
               CONFIRM IDENTITY
             </button>
          )}
        </div>
      </div>

    </div>
  );
});

LiveWebcamScanner.displayName = 'LiveWebcamScanner';
