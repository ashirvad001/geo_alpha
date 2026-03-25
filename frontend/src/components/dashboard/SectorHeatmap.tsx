"use client";

import React from 'react';
import { ResponsiveContainer, Treemap, Tooltip } from 'recharts';

const data = [
  { name: 'Financials', children: [
    { name: 'HDFCBANK', size: 1200, gpr: 72 },
    { name: 'ICICIBANK', size: 900, gpr: 55 },
    { name: 'AXISBANK', size: 600, gpr: 32 },
    { name: 'SBIN', size: 700, gpr: 45 },
  ]},
  { name: 'IT Services', children: [
    { name: 'TCS', size: 1000, gpr: 45 },
    { name: 'INFY', size: 800, gpr: 28 },
    { name: 'HCLTECH', size: 400, gpr: 50 },
  ]},
  { name: 'Energy', children: [
    { name: 'RELIANCE', size: 1500, gpr: 32 },
    { name: 'ONGC', size: 300, gpr: 60 },
  ]},
  { name: 'Consumer', children: [
    { name: 'HINDUNILVR', size: 700, gpr: 25 },
    { name: 'ITC', size: 500, gpr: 40 },
  ]}
];

const CustomizedContent = (props: any) => {
  const { x, y, width, height, index, name, gpr } = props;

  const color = gpr < 40 ? '#22c55e' : gpr < 70 ? '#f59e0b' : '#ef4444';

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill: color,
          stroke: '#000',
          strokeWidth: 2,
          fillOpacity: 0.8,
        }}
        className="hover:fill-opacity-100 transition-all cursor-pointer"
      />
      {width > 50 && height > 30 && (
        <text
          x={x + width / 2}
          y={y + height / 2}
          textAnchor="middle"
          fill="#fff"
          fontSize={12}
          fontWeight="bold"
        >
          {name}
        </text>
      )}
    </g>
  );
};

export const SectorHeatmap = () => {
  return (
    <div className="w-full h-[400px] bg-card p-6 rounded-3xl border border-white/5 shadow-2xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-lg font-bold">Market Risk Treemap</h3>
          <p className="text-xs text-white/40">Visualizing GPR exposure across Nifty 50 sectors</p>
        </div>
        <div className="flex gap-4 text-[10px] items-center">
          <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-risk-low"></div> Low</div>
          <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-risk-mid"></div> Elevated</div>
          <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-risk-high"></div> High</div>
        </div>
      </div>
      
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <Treemap
            data={data}
            dataKey="size"
            aspectRatio={4 / 3}
            stroke="#fff"
            content={<CustomizedContent />}
          >
            <Tooltip 
              contentStyle={{ backgroundColor: '#171717', border: '1px solid #262626', borderRadius: '12px' }}
              itemStyle={{ color: '#fff' }}
            />
          </Treemap>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
