export interface Stock {
  symbol: string;
  name: string;
  sector: string;
  price: number;
  change: number;
  changePercent: number;
  gprScore: number;
  sentimentScore: number;
  signal: 'BUY' | 'SELL' | 'HOLD';
  lastUpdated: string;
}

export interface GPRData {
  symbol: string;
  indexValue: number;
  change: number;
  history: { date: string; value: number }[];
}

export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  timestamp: string;
  sentiment: number; // -1 to 1
  relatedStocks: string[];
}

export interface MacroIndicator {
  label: string;
  value: string | number;
  change: number;
  unit: string;
  category: 'RBI' | 'Global' | 'Market';
}

export interface PortfolioStock extends Stock {
  shares: number;
  avgPrice: number;
  targetWeight: number;
  actualWeight: number;
}
