"use client";

import React from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const MOCK_DATA = [
  { date: '2023-10-01', price: 2900, benchmark: 19500 },
  { date: '2023-10-05', price: 2950, benchmark: 19600 },
  { date: '2023-10-10', price: 2880, benchmark: 19450 },
  { date: '2023-10-15', price: 3020, benchmark: 19800 },
  { date: '2023-10-20', price: 3100, benchmark: 19900 },
  { date: '2023-10-25', price: 3050, benchmark: 19750 },
];

export const PerformanceChart = ({ symbol }: { symbol: string }) => {
  return (
    <div className="bg-card p-6 rounded-3xl border border-white/5 shadow-2xl h-[400px]">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-lg font-bold">{symbol} vs NIFTY 50</h3>
          <p className="text-xs text-white/40">Historical price correlation relative to benchmark</p>
        </div>
      </div>
      
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={MOCK_DATA}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="date" stroke="rgba(255,255,255,0.2)" fontSize={10} />
            <YAxis yAxisId="left" stroke="#3b82f6" fontSize={10} />
            <YAxis yAxisId="right" orientation="right" stroke="#f59e0b" fontSize={10} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#171717', border: '1px solid #262626', borderRadius: '12px' }}
              itemStyle={{ fontSize: '12px' }}
            />
            <Legend verticalAlign="top" height={36}/>
            <Line yAxisId="left" type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={3} dot={false} name={symbol} />
            <Line yAxisId="right" type="monotone" dataKey="benchmark" stroke="#f59e0b" strokeWidth={2} dot={false} name="NIFTY 50" strokeDasharray="5 5" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
