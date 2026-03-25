"use client";

import React from 'react';
import { cn } from '@/lib/utils';

export const Skeleton = ({ className }: { className?: string }) => {
  return (
    <div className={cn("animate-pulse bg-white/5 rounded-xl", className)} />
  );
};

export const DashboardSkeleton = () => {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-28 rounded-3xl" />)}
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <Skeleton className="h-[400px] rounded-3xl" />
          <Skeleton className="h-[500px] rounded-3xl" />
        </div>
        <div className="space-y-8">
          <Skeleton className="h-64 rounded-3xl" />
          <Skeleton className="h-[600px] rounded-3xl" />
        </div>
      </div>
    </div>
  );
};
