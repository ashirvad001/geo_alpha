"use client";

import React from 'react';
import { PerformanceChart } from '@/components/stocks/PerformanceChart';
import { CompositeRiskGauge } from '@/components/dashboard/CompositeRiskGauge';
import { NewsFeed } from '@/components/dashboard/NewsFeed';
import { ArrowLeft, TrendingUp, TrendingDown, Target, Shield, Info } from 'lucide-react';
import Link from 'next/link';
import { usePortfolio } from '@/context/PortfolioContext';

export default function StockDetailPage({ params }: { params: { symbol: string } }) {
  const { symbol } = params;
  const { addStock } = usePortfolio();

  const handleTrack = () => {
    addStock({
      symbol,
      name: `${symbol} Industries`,
      sector: 'Diversified',
      price: 2985.40,
      change: 35.1,
      changePercent: 1.2,
      gprScore: 32,
      sentimentScore: 0.65,
      signal: 'BUY',
      lastUpdated: new Date().toISOString(),
      shares: 100,
      avgPrice: 2950,
      targetWeight: 5,
      actualWeight: 4.8
    });
    alert(`${symbol} added to portfolio tracking`);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-12">
      <Link href="/dashboard" className="flex items-center gap-2 text-white/40 hover:text-white transition-all text-sm font-medium">
        <ArrowLeft size={16} />
        Back to Intelligence Terminal
      </Link>

      <header className="flex justify-between items-end border-b border-white/5 pb-8">
        <div className="flex gap-6 items-center">
            <div className="w-16 h-16 rounded-2xl bg-accent flex items-center justify-center text-3xl font-black text-white italic shadow-lg shadow-accent/20">
              {symbol.substring(0,2)}
            </div>
            <div>
              <h1 className="text-4xl font-black text-white tracking-widest leading-none">{symbol}</h1>
              <p className="text-white/30 text-sm mt-2 font-medium tracking-tight uppercase tracking-widest">Nifty 50 Blue Chip • Sector: Energy</p>
            </div>
        </div>
        
        <div className="flex gap-4">
          <button 
            onClick={handleTrack}
            className="px-6 py-3 rounded-2xl bg-accent text-white font-bold text-sm hover:bg-accent/80 transition-all shadow-xl shadow-accent/10"
          >
            Track in Portfolio
          </button>
          <button className="px-6 py-3 rounded-2xl bg-white/5 text-white/40 border border-white/5 font-bold text-sm hover:text-white transition-all">
            Set Alert
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          <div className="lg:col-span-8 space-y-8">
             <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-card p-6 rounded-3xl border border-white/5 space-y-4">
                   <div className="flex items-center gap-2 text-white/40 text-[10px] font-bold uppercase tracking-widest">
                     <Target size={14} /> Current Valuation
                   </div>
                   <div className="text-3xl font-black">₹2,985.40</div>
                   <div className="text-green-400 text-xs font-bold flex items-center gap-1">
                      <TrendingUp size={14} /> +1.20% 今日
                   </div>
                </div>
                
                <div className="bg-card p-6 rounded-3xl border border-white/5 space-y-4">
                   <div className="flex items-center gap-2 text-white/40 text-[10px] font-bold uppercase tracking-widest">
                     <Shield size={14} /> Vulnerability Index
                   </div>
                   <div className="text-3xl font-black text-risk-low">32.4</div>
                   <div className="text-white/20 text-[10px]">LOW RISK PROXIMITY</div>
                </div>

                <div className="bg-card p-6 rounded-3xl border border-white/5 space-y-4">
                   <div className="flex items-center gap-2 text-white/40 text-[10px] font-bold uppercase tracking-widest">
                     <Info size={14} /> AI Sentiment
                   </div>
                   <div className="text-3xl font-black text-accent">0.82</div>
                   <div className="text-white/20 text-[10px]">STRONGLY POSITIVE</div>
                </div>
             </div>

             <PerformanceChart symbol={symbol} />
          </div>

          <div className="lg:col-span-4 space-y-8">
             <CompositeRiskGauge score={32} />
             <NewsFeed />
          </div>
      </div>
    </div>
  );
}
