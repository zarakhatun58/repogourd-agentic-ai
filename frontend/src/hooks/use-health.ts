'use client';

import { useEffect, useState, useCallback } from 'react';

import type { HealthStatus } from '@/src/types';
import { api, DEMO_MODE } from '@/src/lib/api';

export function useHealth() {
  const [health, setHealth] = useState<HealthStatus>({
    connected: false,
    checkedAt: new Date().toISOString(),
  });

  const [loading, setLoading] = useState(true);
      
  const check = useCallback(async () => {
    setLoading(true);

    if (DEMO_MODE) {
      setHealth({
        connected: false,
        environment: 'demo',
        checkedAt: new Date().toISOString(),
      });

      setLoading(false);
      return;
    }

    try {
      const status = await api.getHealth();
      setHealth(status);
    } catch {
      setHealth({
        connected: false,
        checkedAt: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    check();
  }, [check]);

  return {
    health,
    loading,
    check,
  };
}