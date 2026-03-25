"use client";

import React from 'react';
import { Newspaper, MessageSquare, ExternalLink } from 'lucide-react';
import { NewsItem } from '@/types';
import { cn } from '@/lib/utils';

const MOCK_NEWS: NewsItem[] = [
  { id: '1', title: 'NSE indices face volatility amid escalating border tensions', summary: 'GPR index for Nifty 50 spikes as international reports suggest increased defense readiness...', source: 'Reuters', timestamp: '22 mins ago', sentiment: -0.45, relatedStocks: ['RELIANCE', 'TCS'] },
  { id: '2', title: 'RBI maintains status quo, highlights geopolitical resilience', summary: 'Governor dash notes that Indian markets are better cushioned against global commodity shocks...', source: 'ET Markets', timestamp: '1 hour ago', sentiment: 0.35, relatedStocks: ['HDFCBANK', 'ICICIBANK'] },
  { id: '3', title: 'Tech Mahindra targets expansion in EMEA regions', summary: 'Strategic move to decrease reliance on US markets as regional risk indices stabilize...', source: 'Bloomberg', timestamp: '4 hours ago', sentiment: 0.60, relatedStocks: ['TECHM', 'INFY'] },
];

export const NewsFeed = () => {
  return (
    <div className="bg-card p-6 rounded-3xl border border-white/5 shadow-2xl flex flex-col h-full">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-bold flex items-center gap-3">
          <Newspaper size={20} className="text-accent" />
          Intelligence Flow
        </h3>
        <span className="text-[10px] bg-accent/10 text-accent px-2 py-1 rounded-full font-bold">LIVE</span>
      </div>
      
      <div className="space-y-4 flex-1 overflow-y-auto pr-2 custom-scrollbar">
        {MOCK_NEWS.map((news) => (
          <div key={news.id} className="p-4 rounded-2xl bg-white/5 hover:bg-white/10 transition-all border border-transparent hover:border-white/5 group relative overflow-hidden">
            <div className={`absolute top-0 left-0 bottom-0 w-1 ${news.sentiment > 0 ? 'bg-green-500' : 'bg-red-500'}`}></div>
            
            <div className="flex justify-between items-start mb-2">
              <span className="text-[10px] text-white/30 uppercase font-bold tracking-widest">{news.source} • {news.timestamp}</span>
              <button className="text-white/20 group-hover:text-accent transition-all"><ExternalLink size={14} /></button>
            </div>
            
            <h4 className="text-sm font-bold mb-2 group-hover:text-white/90 leading-snug">{news.title}</h4>
            
            <div className="flex flex-wrap gap-2 mt-3">
              {news.relatedStocks.map(symbol => (
                <span key={symbol} className="text-[8px] bg-white/5 px-1.5 py-0.5 rounded border border-white/5 text-white/40">{symbol}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
      
      <button className="w-full mt-6 py-3 rounded-2xl bg-white/5 text-xs font-bold text-white/40 hover:bg-white/10 hover:text-white transition-all flex items-center justify-center gap-2">
        <MessageSquare size={14} />
        View All Analysis
      </button>
    </div>
  );
};
