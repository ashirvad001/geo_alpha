"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, BarChart2, Briefcase, Map, Search, Bell, User } from 'lucide-react';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
  { label: 'Risk Map', icon: Map, href: '/risk-map' },
  { label: 'Portfolio', icon: Briefcase, href: '/portfolio' },
];

export const Sidebar = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-white/5 h-screen sticky top-0 bg-black/20 backdrop-blur-xl flex flex-col pt-6 max-md:hidden">
      <div className="px-6 mb-8 flex items-center gap-3">
        <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center font-bold text-white italic">GA</div>
        <span className="font-bold text-lg tracking-tight">GEO ALPHA</span>
      </div>
      
      <nav className="flex-1 px-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link 
              key={item.href} 
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group",
                isActive ? "bg-accent/10 text-accent font-medium" : "text-white/40 hover:text-white/80 hover:bg-white/5"
              )}
            >
              <Icon size={20} className={isActive ? "text-accent" : "text-white/40 group-hover:text-white/80"} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-white/5 mx-3 mb-4 rounded-2xl bg-white/5">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center"><User size={20} /></div>
          <div>
            <div className="text-sm font-medium">Ashirvad Singh</div>
            <div className="text-[10px] text-white/30 truncate">ashirvad@geoalpha.ai</div>
          </div>
        </div>
      </div>
    </aside>
  );
};

export const Navbar = () => {
  return (
    <header className="h-16 border-b border-white/5 flex items-center justify-between px-8 bg-black/20 backdrop-blur-xl sticky top-0 z-40">
      <div className="relative w-96 max-md:hidden">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" size={18} />
        <input 
          type="text" 
          placeholder="Search Nifty 50 tokens..." 
          className="w-full bg-white/5 border border-white/10 rounded-full py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 transition-all border-none"
        />
      </div>
      
      <div className="flex items-center gap-4">
        <button className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-white/5 text-white/40 hover:text-white transition-all">
          <Bell size={20} />
        </button>
        <div className="w-px h-6 bg-white/5"></div>
        <div className="text-xs font-mono text-white/40">NSE: OPEN</div>
      </div>
    </header>
  );
};
