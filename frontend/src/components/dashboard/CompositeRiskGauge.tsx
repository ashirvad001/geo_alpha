"use client";

import React from 'react';
import { motion } from 'framer-motion';

export const CompositeRiskGauge = ({ score }: { score: number }) => {
  const radius = 80;
  const strokeWidth = 12;
  const normalizedRadius = radius - strokeWidth * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (score / 100) * (circumference / 2);

  const color = score < 40 ? '#22c55e' : score < 70 ? '#f59e0b' : '#ef4444';

  return (
    <div className="bg-card p-6 rounded-3xl border border-white/5 flex flex-col items-center justify-center relative overflow-hidden group shadow-2xl">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-risk-low via-risk-mid to-risk-high opacity-50"></div>
      
      <h3 className="text-sm font-medium text-white/40 mb-4 uppercase tracking-widest text-center">Composite Risk Index</h3>
      
      <div className="relative flex items-center justify-center h-40">
        <svg height={radius * 2} width={radius * 2} className="transform -rotate-90">
          <circle
            stroke="rgba(255,255,255,0.05)"
            fill="transparent"
            strokeWidth={strokeWidth}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
            strokeDasharray={`${circumference / 2} ${circumference}`}
            strokeLinecap="round"
          />
          <motion.circle
            stroke={color}
            fill="transparent"
            strokeWidth={strokeWidth}
            strokeDasharray={`${circumference / 2} ${circumference}`}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
            strokeLinecap="round"
          />
        </svg>
        
        <div className="absolute text-center">
          <motion.div 
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-4xl font-black text-white"
          >
            {score}
          </motion.div>
          <div className="text-[10px] text-white/30 font-bold uppercase tracking-tighter">Index Points</div>
        </div>
      </div>
      
      <div className="text-center mt-2 group-hover:scale-105 transition-transform">
        <div className={`text-xs font-bold uppercase ${score < 40 ? 'text-risk-low' : score < 70 ? 'text-risk-mid' : 'text-risk-high'}`}>
          {score < 40 ? 'Stable Outlook' : score < 70 ? 'Moderate Volatility' : 'Extreme Risk'}
        </div>
        <p className="text-[10px] text-white/20 mt-1 max-w-[120px]">Based on GPR monitoring and macro indicators</p>
      </div>
    </div>
  );
};
