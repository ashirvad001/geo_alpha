"use client";

import React, { useState } from 'react';
import { ChevronUp, ChevronDown, Filter, ExternalLink } from 'lucide-react';
import { Stock } from '@/types';
import { cn, formatCurrency, getColorForGPR } from '@/lib/utils';
import Link from 'next/link';

const MOCK_STOCKS: Stock[] = [
  { symbol: 'RELIANCE', name: 'Reliance Industries', sector: 'Energy', price: 2985.40, change: 35.1, changePercent: 1.2, gprScore: 32, sentimentScore: 0.65, signal: 'BUY', lastUpdated: '2023-10-25T10:00:00Z' },
  { symbol: 'TCS', name: 'Tata Consultancy Services', sector: 'IT Services', price: 4120.15, change: -20.5, changePercent: -0.5, gprScore: 45, sentimentScore: 0.45, signal: 'HOLD', lastUpdated: '2023-10-25T10:00:00Z' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank', sector: 'Financials', price: 1450.20, change: 11.5, changePercent: 0.8, gprScore: 72, sentimentScore: -0.15, signal: 'SELL', lastUpdated: '2023-10-25T10:00:00Z' },
  { symbol: 'INFY', name: 'Infosys', sector: 'IT Services', price: 1620.50, change: 33.2, changePercent: 2.1, gprScore: 28, sentimentScore: 0.80, signal: 'BUY', lastUpdated: '2023-10-25T10:00:00Z' },
  { symbol: 'ICICIBANK', name: 'ICICI Bank', sector: 'Financials', price: 1080.30, change: -13.1, changePercent: -1.2, gprScore: 55, sentimentScore: 0.20, signal: 'HOLD', lastUpdated: '2023-10-25T10:00:00Z' },
];

export const StocksTable = () => {
  const [sortConfig, setSortConfig] = useState<{ key: keyof Stock; direction: 'asc' | 'desc' } | null>(null);

  const sortedStocks = [...MOCK_STOCKS].sort((a, b) => {
    if (!sortConfig) return 0;
    const { key, direction } = sortConfig;
    if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
    if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
    return 0;
  });

  const requestSort = (key: keyof Stock) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  return (
    <div className="bg-card rounded-3xl border border-white/5 overflow-hidden shadow-2xl">
      <div className="p-6 border-b border-white/5 flex justify-between items-center">
        <div>
          <h3 className="text-lg font-bold">Nifty 50 Intelligence</h3>
          <p className="text-xs text-white/40">Real-time GPR and Sentiment analysis</p>
        </div>
        <button className="p-2 bg-white/5 rounded-xl text-white/40 hover:text-white transition-all"><Filter size={18} /></button>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="text-[10px] uppercase tracking-widest text-white/30 font-bold border-b border-white/5">
              <th className="px-6 py-4 cursor-pointer hover:text-white" onClick={() => requestSort('symbol')}>Assets</th>
              <th className="px-6 py-4 cursor-pointer hover:text-white" onClick={() => requestSort('price')}>Price (₹)</th>
              <th className="px-6 py-4 cursor-pointer hover:text-white text-right" onClick={() => requestSort('gprScore')}>Risk Profile</th>
              <th className="px-6 py-4 cursor-pointer hover:text-white text-right" onClick={() => requestSort('sentimentScore')}>Sentiment</th>
              <th className="px-6 py-4 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {sortedStocks.map((stock) => (
              <tr key={stock.symbol} className="group hover:bg-white/5 transition-all">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center font-bold text-[10px] text-white/40 group-hover:bg-accent group-hover:text-white transition-all">
                      {stock.symbol.substring(0, 2)}
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white group-hover:text-accent transition-colors">{stock.symbol}</div>
                      <div className="text-[10px] text-white/20">{stock.sector}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm font-medium">{formatCurrency(stock.price)}</div>
                  <div className={cn("text-[10px]", stock.changePercent > 0 ? 'text-green-400' : 'text-red-400')}>
                    {stock.changePercent > 0 ? '+' : ''}{stock.changePercent}%
                  </div>
                </td>
                <td className="px-6 py-4 text-right">
                  <div className={cn("text-lg font-black", getColorForGPR(stock.gprScore))}>
                    {stock.gprScore}
                  </div>
                  <progress 
                    className="w-16 h-1 rounded-full appearance-none [&::-webkit-progress-bar]:bg-white/5 [&::-webkit-progress-value]:bg-current" 
                    value={stock.gprScore} 
                    max="100"
                  />
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="text-sm font-medium flex items-center justify-end gap-2">
                    <div className={cn("w-2 h-2 rounded-full", stock.sentimentScore > 0 ? 'bg-green-500' : 'bg-red-500')}></div>
                    {stock.sentimentScore > 0 ? 'Positive' : 'Weak'}
                  </div>
                  <div className="text-[10px] text-white/20 italic">{stock.sentimentScore} score</div>
                </td>
                <td className="px-6 py-4 text-center">
                    <Link href={`/stocks/${stock.symbol}`} className="p-2 inline-block rounded-xl bg-white/5 text-white/40 hover:bg-accent/20 hover:text-accent transition-all">
                      <ExternalLink size={16} />
                    </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
