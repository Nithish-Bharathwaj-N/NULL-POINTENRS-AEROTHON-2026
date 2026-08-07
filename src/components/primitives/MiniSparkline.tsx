// HAL Mission Control - Mini Sparkline Component
// Converts numbers into high-density visual engineering intelligence.
// GPU accelerated SVG rendering with trend arrows and limit indicators.

import React, { useMemo } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface MiniSparklineProps {
  data: number[];
  min?: number;
  max?: number;
  color?: string;
  height?: number;
  width?: number;
  showTrend?: boolean;
  thresholdWarn?: number;
  thresholdCrit?: number;
  className?: string;
}

export const MiniSparkline: React.FC<MiniSparklineProps> = React.memo(({
  data,
  min,
  max,
  color = '#2563EB',
  height = 24,
  width = 80,
  showTrend = true,
  thresholdWarn,
  thresholdCrit,
  className = '',
}) => {
  const cleanData = useMemo(() => (data.length > 0 ? data : [0, 0]), [data]);
  const minVal = useMemo(() => (min !== undefined ? min : Math.min(...cleanData)), [min, cleanData]);
  const maxVal = useMemo(() => (max !== undefined ? max : Math.max(...cleanData, minVal + 0.001)), [max, cleanData, minVal]);

  const current = cleanData[cleanData.length - 1];
  const prev = cleanData.length > 1 ? cleanData[cleanData.length - 2] : current;
  const diff = current - prev;

  const isCrit = thresholdCrit !== undefined && current >= thresholdCrit;
  const isWarn = !isCrit && thresholdWarn !== undefined && current >= thresholdWarn;

  const activeColor = isCrit ? '#EF4444' : isWarn ? '#F59E0B' : color;

  const points = useMemo(() => {
    const len = cleanData.length;
    if (len === 1) return `0,${height / 2} ${width},${height / 2}`;
    return cleanData
      .map((val, idx) => {
        const x = (idx / (len - 1)) * width;
        const norm = Math.max(0, Math.min(1, (val - minVal) / (maxVal - minVal)));
        const y = height - norm * (height - 4) - 2;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  }, [cleanData, minVal, maxVal, width, height]);

  return (
    <div className={`inline-flex items-center gap-1.5 font-mono select-none ${className}`}>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="overflow-visible shrink-0"
      >
        <polyline
          fill="none"
          stroke={activeColor}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
        />
        {/* Current value dot */}
        <circle
          cx={width}
          cy={height - Math.max(0, Math.min(1, (current - minVal) / (maxVal - minVal))) * (height - 4) - 2}
          r="2.5"
          fill={activeColor}
          className={isCrit ? 'animate-ping' : ''}
        />
      </svg>

      {showTrend && (
        <span className="shrink-0 flex items-center">
          {diff > 0.01 ? (
            <TrendingUp className="w-3 h-3 text-red-500" />
          ) : diff < -0.01 ? (
            <TrendingDown className="w-3 h-3 text-emerald-500" />
          ) : (
            <Minus className="w-3 h-3 text-slate-400" />
          )}
        </span>
      )}
    </div>
  );
});
MiniSparkline.displayName = 'MiniSparkline';
