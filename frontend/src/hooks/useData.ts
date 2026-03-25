"use client";

import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export const useStockData = (symbol?: string) => {
  const { data, error, mutate } = useSWR(
    symbol ? `/api/stocks/${symbol}` : '/api/stocks',
    fetcher,
    {
      refreshInterval: 60000, // 60 seconds
      revalidateOnFocus: true,
      optimisticData: (current: any) => current, // Simple optimistic UI placeholder
    }
  );

  return {
    stocks: data,
    isLoading: !error && !data,
    isError: error,
    mutate
  };
};

export const useMacroData = () => {
  const { data, error } = useSWR('/api/macro', fetcher, {
    refreshInterval: 300000, // 5 minutes for macro
  });

  return {
    macro: data,
    isLoading: !error && !data,
    isError: error
  };
};
