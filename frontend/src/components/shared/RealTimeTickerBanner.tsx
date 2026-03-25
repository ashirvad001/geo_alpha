"use client";

import React from 'react';
import { TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import { Stock } from '@/types';

const MOCK_DATA: Partial<Stock>[] = [
  { symbol: 'RELIANCE', price: 2985.40, changePercent: 1.2, gprScore: 32 },
  { symbol: 'TCS', price: 4120.15, changePercent: -0.5, gprScore: 45 },
  { symbol: 'HDFCBANK', price: 1450.20, changePercent: 0.8, gprScore: 72 },
  { symbol: 'INFY', price: 1620.50, changePercent: 2.1, gprScore: 28 },
  { symbol: 'ICICIBANK', price: 1080.30, changePercent: -1.2, gprScore: 55 },
];

export const RealTimeTickerBanner = () => {
  return (
    <div className="w-full bg-black/50 border-b border-white/10 py-2 overflow-hidden whitespace-nowrap sticky top-0 z-50 backdrop-blur-md">
      <div className="inline-block animate-ticker hover:pause-animation">
        {MOCK_DATA.map((stock, i) => (
          <span key={stock.symbol} className="mx-8 items-center inline-flex gap-2 text-sm font-medium">
            <span className="text-white/60">{stock.symbol}</span>
            <span className="text-white">₹{stock.price?.toLocaleString()}</span>
            <span className={stock.changePercent! > 0 ? 'text-green-400 flex items-center gap-1' : 'text-red-400 flex items-center gap-1'}>
              {stock.changePercent! > 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {Math.abs(stock.changePercent!)}%
            </span>
            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
              stock.gprScore! < 40 ? 'bg-green-500/20 text-green-400' : 
              stock.gprScore! < 70 ? 'bg-amber-500/20 text-amber-400' : 
              'bg-red-500/20 text-red-400'
            }`}>
              GPR {stock.gprScore}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
};
