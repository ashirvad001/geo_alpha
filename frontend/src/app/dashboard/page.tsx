"use client";

import React, { Suspense } from 'react';
import { MacroDashboard } from '@/components/dashboard/MacroDashboard';
import { SectorHeatmap } from '@/components/dashboard/SectorHeatmap';
import { CompositeRiskGauge } from '@/components/dashboard/CompositeRiskGauge';
import { StocksTable } from '@/components/dashboard/StocksTable';
import { NewsFeed } from '@/components/dashboard/NewsFeed';
import { DashboardSkeleton } from '@/components/shared/Skeleton';
import { motion } from 'framer-motion';

export default function DashboardPage() {
  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-12">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-4">
          Market Intelligence Terminal
          <span className="text-xs bg-accent/20 text-accent px-2 py-1 rounded border border-accent/20 font-mono">v1.2.0</span>
        </h1>
        <p className="text-white/40 text-sm max-w-2xl">
          Aggregating real-time geopolitical risk indicators and sentiment flows for the Nifty 50 universe.
        </p>
      </header>
      
      <Suspense fallback={<DashboardSkeleton />}>
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          {/* Macro Row */}
          <MacroDashboard />
          
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Column - Main Charts & Tables */}
            <div className="lg:col-span-8 space-y-8">
              <SectorHeatmap />
              <StocksTable />
            </div>
            
            {/* Right Column - Gauges & Feeds */}
            <div className="lg:col-span-4 space-y-8 h-full">
              <CompositeRiskGauge score={68} />
              <div className="flex-1">
                <NewsFeed />
              </div>
            </div>
          </div>
        </motion.div>
      </Suspense>
    </div>
  );
}
