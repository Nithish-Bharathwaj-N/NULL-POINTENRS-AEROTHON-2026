class AudioEngine {
  private ctx: AudioContext | null = null;
  private humOscillators: OscillatorNode[] = [];
  private humGain: GainNode | null = null;

  private init() {
    if (!this.ctx) {
      this.ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  // Play a short, mechanical keystroke tick
  public playKeystroke() {
    try {
      this.init();
      if (!this.ctx) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      
      osc.type = 'square';
      osc.frequency.setValueAtTime(800, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(100, this.ctx.currentTime + 0.05);
      
      gain.gain.setValueAtTime(0.05, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.05);
      
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      
      osc.start();
      osc.stop(this.ctx.currentTime + 0.05);
    } catch (e) { /* ignore audio errors */ }
  }

  // Play a radar-style scanning ping
  public playScanBlip() {
    try {
      this.init();
      if (!this.ctx) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      
      osc.type = 'sine';
      osc.frequency.setValueAtTime(1200, this.ctx.currentTime);
      
      gain.gain.setValueAtTime(0.1, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.1);
      
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      
      osc.start();
      osc.stop(this.ctx.currentTime + 0.1);
    } catch (e) {}
  }

  // Play a harsh error buzzer (dissonant sawtooth)
  public playErrorBuzzer() {
    try {
      this.init();
      if (!this.ctx) return;
      
      [150, 158].forEach(freq => {
        const osc = this.ctx!.createOscillator();
        const gain = this.ctx!.createGain();
        osc.type = 'sawtooth';
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.2, this.ctx!.currentTime);
        gain.gain.linearRampToValueAtTime(0, this.ctx!.currentTime + 0.4);
        osc.connect(gain);
        gain.connect(this.ctx!.destination);
        osc.start();
        osc.stop(this.ctx!.currentTime + 0.4);
      });
    } catch (e) {}
  }

  // Play a triumphant sci-fi unlock chord
  public playUnlockChime() {
    try {
      this.init();
      if (!this.ctx) return;
      
      // Major triad: C5 (523), E5 (659), G5 (783)
      [523.25, 659.25, 783.99].forEach((freq, index) => {
        const osc = this.ctx!.createOscillator();
        const gain = this.ctx!.createGain();
        osc.type = 'sine';
        osc.frequency.value = freq;
        
        // Stagger the start times slightly for a "rolling" effect
        const startTime = this.ctx!.currentTime + (index * 0.05);
        gain.gain.setValueAtTime(0, this.ctx!.currentTime);
        gain.gain.setValueAtTime(0.15, startTime);
        gain.gain.exponentialRampToValueAtTime(0.001, startTime + 1.5);
        
        osc.connect(gain);
        gain.connect(this.ctx!.destination);
        osc.start(startTime);
        osc.stop(startTime + 1.5);
      });
    } catch (e) {}
  }

  // Start continuous ambient hum
  public startAmbientHum() {
    try {
      this.init();
      if (!this.ctx || this.humGain) return;
      
      this.humGain = this.ctx.createGain();
      this.humGain.gain.value = 0.03; // Very quiet
      this.humGain.connect(this.ctx.destination);
      
      // Dual detuned low frequencies for mechanical drone
      [55, 57].forEach(freq => {
        const osc = this.ctx!.createOscillator();
        osc.type = 'sine';
        osc.frequency.value = freq;
        osc.connect(this.humGain!);
        osc.start();
        this.humOscillators.push(osc);
      });
    } catch (e) {}
  }

  // Stop continuous ambient hum
  public stopAmbientHum() {
    if (this.humOscillators.length > 0) {
      this.humOscillators.forEach(osc => {
        try { osc.stop(); } catch(e){}
      });
      this.humOscillators = [];
    }
    if (this.humGain) {
      this.humGain.disconnect();
      this.humGain = null;
    }
  }
}

export const audio = new AudioEngine();
