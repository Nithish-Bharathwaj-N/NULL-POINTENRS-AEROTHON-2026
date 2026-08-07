// HAL Mission Control — Animated Value Hook
// Smooth 60fps number interpolation for gauges, values, and progress indicators.

import { useRef, useState, useEffect } from 'react';

export function useAnimatedValue(target: number, durationMs = 350): number {
  const [current, setCurrent] = useState(target);
  const startRef = useRef<number | null>(null);
  const fromRef = useRef(target);
  const targetRef = useRef(target);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (Math.abs(target - targetRef.current) < 0.001) return;
    fromRef.current = current;
    targetRef.current = target;
    startRef.current = null;

    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);

    const animate = (now: number) => {
      if (startRef.current === null) startRef.current = now;
      const elapsed = now - startRef.current;
      const progress = Math.min(elapsed / durationMs, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = fromRef.current + (targetRef.current - fromRef.current) * eased;
      setCurrent(Number(value.toFixed(4)));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };

    rafRef.current = requestAnimationFrame(animate);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [target, durationMs]);

  return current;
}

// Trend direction — requires tracking previous values
export function useTrendDirection(value: number, threshold = 0.5): '↑' | '↓' | '→' {
  const prevRef = useRef(value);
  const [trend, setTrend] = useState<'↑' | '↓' | '→'>('→');

  useEffect(() => {
    const diff = value - prevRef.current;
    if (diff > threshold) setTrend('↑');
    else if (diff < -threshold) setTrend('↓');
    else setTrend('→');
    prevRef.current = value;
  }, [value, threshold]);

  return trend;
}
