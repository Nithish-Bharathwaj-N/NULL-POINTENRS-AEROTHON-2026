import React from 'react';
import { Panel } from '@/components';
import { TrendingUp } from 'lucide-react';
import { FleetMember } from '@/types';
import ReactECharts from 'echarts-for-react';

interface FleetHealthChartProps {
  ac: FleetMember;
}

export const FleetHealthChart: React.FC<FleetHealthChartProps> = React.memo(({ ac }) => {
  const option = {
    grid: { top: 25, right: 15, bottom: 25, left: 40 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: ['T-50h', 'T-40h', 'T-30h', 'T-20h', 'T-10h', 'Current'],
      axisLine: { lineStyle: { color: '#CBD5E1' } },
      axisLabel: { color: '#64748B', fontFamily: 'JetBrains Mono', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      min: 50,
      max: 100,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#F1F5F9', type: 'dashed' } },
      axisLabel: { color: '#64748B', fontFamily: 'JetBrains Mono', fontSize: 10, formatter: '{value}%' },
    },
    series: [
      {
        name: 'Propulsion Health Index',
        type: 'line',
        smooth: true,
        data: [98, 97, 95, 93, 91, ac.engineHealth],
        itemStyle: { color: '#003366' },
        lineStyle: { width: 3 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0, 51, 102, 0.25)' },
              { offset: 1, color: 'rgba(0, 51, 102, 0.0)' },
            ],
          },
        },
      },
    ],
  };

  return (
    <Panel title="AeroNet-v4 RUL Degradation Trajectory" icon={TrendingUp} className="h-full">
      <div className="h-[180px] w-full">
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} notMerge={true} />
      </div>
    </Panel>
  );
});
FleetHealthChart.displayName = 'FleetHealthChart';
