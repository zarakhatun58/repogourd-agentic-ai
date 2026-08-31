'use client';

import { useEffect, useState, useCallback } from 'react';
import { api, DEMO_MODE } from '@/lib/api';
import type { HealthStatus } from '@/src/types';

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
    const status = await api.getHealth();
    setHealth(status);
    setLoading(false);
  }, []);

  useEffect(() => {
    check();
  }, [check]);

  return { health, loading, check };
}
