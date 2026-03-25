"use client";

import React from 'react';
import { IndianRupee, Globe, Activity, TrendingUp, TrendingDown } from 'lucide-react';
import { MacroIndicator } from '@/types';
import { cn } from '@/lib/utils';

const MOCK_MACRO: MacroIndicator[] = [
  { label: 'Repo Rate', value: '6.50', change: 0, unit: '%', category: 'RBI' },
  { label: 'CPI Inflation', value: '4.85', change: -0.2, unit: '%', category: 'RBI' },
  { label: 'USD/INR', value: '83.15', change: 0.05, unit: '', category: 'Market' },
  { label: 'GPR Global', value: '142.5', change: 12.3, unit: 'pts', category: 'Global' },
];

export const MacroDashboard = () => {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {MOCK_MACRO.map((item) => (
        <div key={item.label} className="bg-card p-5 rounded-3xl border border-white/5 shadow-xl hover:shadow-accent/5 transition-all group overflow-hidden relative">
           <div className="absolute -right-4 -top-4 text-white/5 transform rotate-12 group-hover:scale-125 transition-transform duration-500">
             {item.category === 'RBI' ? <IndianRupee size={80} /> : item.category === 'Global' ? <Globe size={80} /> : <Activity size={80} />}
           </div>
           
           <div className="relative z-10">
             <div className="text-[10px] text-white/30 uppercase font-black tracking-widest mb-1">{item.category}</div>
             <div className="text-white/60 text-xs font-medium mb-2">{item.label}</div>
             <div className="flex items-baseline gap-2">
               <span className="text-2xl font-black text-white">{item.value}{item.unit}</span>
               {item.change !== 0 && (
                 <span className={cn("text-[10px] font-bold flex items-center gap-0.5", item.change > 0 ? 'text-red-400' : 'text-green-400')}>
                   {item.change > 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                   {Math.abs(item.change)}
                 </span>
               )}
             </div>
           </div>
        </div>
      ))}
    </div>
  );
};
