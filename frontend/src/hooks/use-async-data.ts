'use client';

import { useState, useEffect, useCallback } from 'react';
import { DEMO_MODE } from '@/src/lib/api';

export interface AsyncDataResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  isDemo: boolean;
  refetch: () => void;
}

export function useAsyncData<T>(
  fetcher: () => Promise<T>,
  demoData?: T,
  deps: unknown[] = []
): AsyncDataResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [refetchKey, setRefetchKey] = useState(0);

  const refetch = useCallback(() => {
    setRefetchKey((key) => key + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError(null);

    fetcher()
      .then((result) => {
        if (cancelled) return;

        setData(result);
        setLoading(false);
        setIsDemo(false);
      })
      .catch((err: unknown) => {
        if (cancelled) return;

        const message =
          err instanceof Error
            ? err.message
            : 'Unable to load data';

        /*
         * Backend unavailable:
         * use demo data if DEMO_MODE is enabled.
         */
        if (DEMO_MODE && demoData !== undefined) {
          setData(demoData);
          setIsDemo(true);
          setError(null);
        } else {
          setData(null);
          setIsDemo(false);
          setError(message);
        }

        setLoading(false);
      });

    return () => {
      cancelled = true;
    };

    /*
     * IMPORTANT:
     * Do NOT add fetcher here.
     *
     * Inline functions such as:
     * () => api.listAnalyses()
     *
     * are recreated on every render.
     */
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refetchKey, ...deps]);

  return {
    data,
    loading,
    error,
    isDemo,
    refetch,
  };
}