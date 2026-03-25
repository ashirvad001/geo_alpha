"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { PortfolioStock } from '@/types';

interface PortfolioContextType {
  portfolio: PortfolioStock[];
  addStock: (stock: PortfolioStock) => void;
  removeStock: (symbol: string) => void;
  updateWeight: (symbol: string, weight: number) => void;
  totalValue: number;
}

const PortfolioContext = createContext<PortfolioContextType | undefined>(undefined);

export const PortfolioProvider = ({ children }: { children: ReactNode }) => {
  const [portfolio, setPortfolio] = useState<PortfolioStock[]>([]);

  const addStock = (stock: PortfolioStock) => {
    setPortfolio(prev => [...prev.filter(s => s.symbol !== stock.symbol), stock]);
  };

  const removeStock = (symbol: string) => {
    setPortfolio(prev => prev.filter(s => s.symbol !== symbol));
  };

  const updateWeight = (symbol: string, weight: number) => {
    setPortfolio(prev => prev.map(s => s.symbol === symbol ? { ...s, targetWeight: weight } : s));
  };

  const totalValue = portfolio.reduce((acc, stock) => acc + (stock.price * stock.shares), 0);

  return (
    <PortfolioContext.Provider value={{ portfolio, addStock, removeStock, updateWeight, totalValue }}>
      {children}
    </PortfolioContext.Provider>
  );
};

export const usePortfolio = () => {
  const context = useContext(PortfolioContext);
  if (!context) throw new Error('usePortfolio must be used within PortfolioProvider');
  return context;
};
