"use client";

import React from 'react';
import { SectorHeatmap } from '@/components/dashboard/SectorHeatmap';
import { Layers, Info } from 'lucide-react';

export default function RiskMapPage() {
  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-12 h-[calc(100vh-140px)] flex flex-col">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-black text-white flex items-center gap-3">
            <Layers className="text-accent" />
            Market Risk Heatmap
          </h1>
          <p className="text-white/40 text-sm mt-1 uppercase tracking-widest text-[10px]">Real-time sectoral GPR exposure visualization</p>
        </div>
        
        <div className="flex items-center gap-2 text-white/20 hover:text-white/60 transition-colors cursor-help group">
           <Info size={16} />
           <span className="text-[10px] uppercase font-bold tracking-widest opacity-0 group-hover:opacity-100 transition-opacity">How weightage is calculated?</span>
        </div>
      </header>

      <div className="flex-1 min-h-[600px] w-full bg-card rounded-[40px] border border-white/5 overflow-hidden shadow-2xl p-2">
         <div className="w-full h-full">
           <SectorHeatmap />
         </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
         <div className="bg-white/5 p-4 rounded-2xl flex items-center justify-between">
            <div className="text-[10px] text-white/30 font-bold uppercase">Heaviest Exposure</div>
            <div className="text-sm font-black text-risk-high uppercase tracking-tighter">Energy (74.2)</div>
         </div>
         <div className="bg-white/5 p-4 rounded-2xl flex items-center justify-between">
            <div className="text-[10px] text-white/30 font-bold uppercase">Safest Shelter</div>
            <div className="text-sm font-black text-risk-low uppercase tracking-tighter">IT Services (22.5)</div>
         </div>
         <div className="bg-white/5 p-4 rounded-2xl flex items-center justify-between">
            <div className="text-[10px] text-white/30 font-bold uppercase">Largest Movement</div>
            <div className="text-sm font-black text-risk-mid uppercase tracking-tighter">Financials (+12%)</div>
         </div>
      </div>
    </div>
  );
}
