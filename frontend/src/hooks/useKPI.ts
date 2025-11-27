import { useState, useCallback } from "react";
import type { KPIConfig, KPIExplanation } from "@shared/types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function useKPI() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getKPIs = useCallback(async (): Promise<KPIConfig | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/kpis`);
      if (!response.ok) {
        throw new Error("Failed to fetch KPIs");
      }
      const data = await response.json();
      return data as KPIConfig;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch KPIs");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateKPIs = useCallback(async (kpis: KPIConfig): Promise<KPIConfig | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/kpis`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(kpis),
      });
      if (!response.ok) {
        throw new Error("Failed to update KPIs");
      }
      const data = await response.json();
      return data as KPIConfig;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update KPIs");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const getExplanation = useCallback(async (): Promise<KPIExplanation | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/kpis/explain`);
      if (!response.ok) {
        throw new Error("Failed to fetch KPI explanation");
      }
      const data = await response.json();
      return data as KPIExplanation;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch KPI explanation");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    getKPIs,
    updateKPIs,
    getExplanation,
    loading,
    error,
  };
}

