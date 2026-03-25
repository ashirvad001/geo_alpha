"use client";

import React from 'react';
import { usePortfolio } from '@/context/PortfolioContext';
import { Download, Trash2, Plus, Edit2, TrendingUp, TrendingDown, PieChart } from 'lucide-react';
import { downloadCSV, formatCurrency, getColorForGPR } from '@/lib/utils';
import { PerformanceChart } from '@/components/stocks/PerformanceChart';

export default function PortfolioPage() {
  const { portfolio, removeStock, updateWeight, totalValue } = usePortfolio();

  const handleExport = () => {
    downloadCSV(portfolio, 'my_portfolio_geoalpha.csv');
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-12">
      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-black text-white">Portfolio Intelligence</h1>
          <p className="text-white/40 text-sm mt-1">Manage and track your GPR-exposed assets</p>
        </div>
        
        <div className="flex gap-4">
          <button 
            onClick={handleExport}
            className="flex items-center gap-2 px-5 py-2.5 bg-white/5 border border-white/10 rounded-2xl text-xs font-bold hover:bg-white/10 transition-all"
          >
            <Download size={14} /> Export CSV
          </button>
          <button className="flex items-center gap-2 px-5 py-2.5 bg-accent rounded-2xl text-xs font-bold text-white hover:bg-accent/80 transition-all shadow-lg shadow-accent/20">
            <Plus size={14} /> Add Asset
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="bg-card p-6 rounded-3xl border border-white/5 space-y-2 col-span-1">
          <div className="text-[10px] text-white/30 font-bold tracking-widest uppercase">Total Portfolio Value</div>
          <div className="text-3xl font-black">{formatCurrency(totalValue || 0)}</div>
        </div>
        <div className="bg-card p-6 rounded-3xl border border-white/5 space-y-2 col-span-1">
          <div className="text-[10px] text-white/30 font-bold tracking-widest uppercase">Avg GPR Exposure</div>
          <div className="text-3xl font-black text-risk-mid">52.1</div>
        </div>
        <div className="bg-card p-6 rounded-3xl border border-white/5 col-span-2 flex items-center justify-between px-8">
           <div className="flex gap-4 items-center">
              <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center text-accent"><PieChart size={24} /></div>
              <div>
                <div className="text-xs font-bold">Allocation Strategy</div>
                <div className="text-[10px] text-white/30">Target Weights vs Actual</div>
              </div>
           </div>
           <div className="flex -space-x-3">
             <div className="w-10 h-10 border-4 border-[#171717] rounded-full bg-risk-low flex items-center justify-center text-[8px] font-bold">IT</div>
             <div className="w-10 h-10 border-4 border-[#171717] rounded-full bg-risk-mid flex items-center justify-center text-[8px] font-bold">FIN</div>
             <div className="w-10 h-10 border-4 border-[#171717] rounded-full bg-risk-high flex items-center justify-center text-[8px] font-bold">NRG</div>
           </div>
        </div>
      </div>

      <div className="bg-card rounded-3xl border border-white/5 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="text-[10px] uppercase tracking-widest text-white/30 font-bold border-b border-white/5">
                <th className="px-6 py-5">Asset</th>
                <th className="px-6 py-5">Holding</th>
                <th className="px-6 py-5">Value (₹)</th>
                <th className="px-6 py-5">GPR Score</th>
                <th className="px-6 py-5 text-center">Target Weight</th>
                <th className="px-6 py-5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {portfolio.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-white/20 italic text-sm">
                    No assets tracked. Add stocks from the dashboard or individual asset pages.
                  </td>
                </tr>
              ) : portfolio.map((stock) => (
                <tr key={stock.symbol} className="hover:bg-white/5 transition-all group">
                  <td className="px-6 py-6">
                    <div className="font-bold">{stock.symbol}</div>
                    <div className="text-[10px] text-white/20">{stock.name}</div>
                  </td>
                  <td className="px-6 py-6">
                    <div className="text-sm font-medium">{stock.shares} Units</div>
                    <div className="text-[10px] text-white/20">Avg: ₹{stock.avgPrice}</div>
                  </td>
                  <td className="px-6 py-6 font-bold">{formatCurrency(stock.price * stock.shares)}</td>
                  <td className={`px-6 py-6 font-bold ${getColorForGPR(stock.gprScore)}`}>{stock.gprScore}</td>
                  <td className="px-6 py-6">
                    <div className="flex items-center justify-center gap-4">
                       <span className="text-sm font-mono text-accent">{stock.targetWeight}%</span>
                       <input 
                         type="range" 
                         min="0" max="100" 
                         value={stock.targetWeight}
                         onChange={(e) => updateWeight(stock.symbol, parseInt(e.target.value))}
                         className="w-24 accent-accent h-1"
                       />
                    </div>
                  </td>
                  <td className="px-6 py-6 text-right">
                    <button 
                      onClick={() => removeStock(stock.symbol)}
                      className="p-2 text-white/10 hover:text-red-400 transition-all bg-white/5 hover:bg-red-400/10 rounded-xl"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      {portfolio.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-12">
           <PerformanceChart symbol="PORTFOLIO" />
           <div className="bg-card p-8 rounded-3xl border border-white/5 space-y-6">
              <h3 className="text-lg font-bold flex items-center gap-3"><Edit2 size={18} className="text-accent"/> Analysis Summary</h3>
              <p className="text-white/40 text-sm leading-relaxed">
                Your portfolio current exposure is heavily concentrated in <span className="text-white font-bold">Financials</span> (42%). 
                Based on rising GPR in EMEA regions, we recommend re-allocating <span className="text-risk-low font-bold">5%</span> into domestic consumer goods to neutralize regional risk spikes.
              </p>
              <div className="pt-4 space-y-3">
                 <div className="flex justify-between text-xs px-2"><span className="text-white/40">Expected Volatility</span> <span>12.4%</span></div>
                 <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden truncate"><div className="w-[60%] h-full bg-accent"></div></div>
                 <div className="flex justify-between text-xs px-2"><span className="text-white/40">GPR Diversification Score</span> <span className="text-green-400">EXCELLENT</span></div>
                 <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden truncate"><div className="w-[85%] h-full bg-green-500"></div></div>
              </div>
           </div>
        </div>
      )}
    </div>
  );
}
