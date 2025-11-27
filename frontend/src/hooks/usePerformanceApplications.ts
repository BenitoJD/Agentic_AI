import { useEffect, useMemo, useState } from "react";

import {
  mockPerformanceApplications,
  getPerformanceApplicationDetails,
} from "../data/performanceMockData";
import type {
  PerformanceApplication,
  PerformanceApplicationDetails,
} from "../types/performance";

const API_BASE = "/api";

export const usePerformanceApplications = () => {
  const [applications, setApplications] = useState<PerformanceApplication[]>(
    [],
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${API_BASE}/metrics/applications`);
        if (!res.ok) {
          throw new Error(await res.text());
        }
        const data = (await res.json()) as PerformanceApplication[];
        setApplications(data);
        setError(null);
      } catch (e) {
        console.warn("[metrics] falling back to mock data", e);
        setApplications(mockPerformanceApplications);
        setError("Using sample data (backend unavailable)");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const sortedApplications = useMemo<PerformanceApplication[]>(() => {
    const criticalityOrder: Record<PerformanceApplication["status"], number> = {
      critical: 0,
      warning: 1,
      healthy: 2,
    };
    return [...applications].sort(
      (a, b) => criticalityOrder[a.status] - criticalityOrder[b.status],
    );
  }, [applications]);

  const criticalCount = sortedApplications.filter(
    (app) => app.status === "critical",
  ).length;
  const warningCount = sortedApplications.filter(
    (app) => app.status === "warning",
  ).length;

  const getDetails = async (
    id: string,
  ): Promise<PerformanceApplicationDetails> => {
    try {
      const res = await fetch(`${API_BASE}/metrics/applications/${id}`);
      if (res.ok) {
        return (await res.json()) as PerformanceApplicationDetails;
      }
    } catch (e) {
      console.warn("[metrics] detail fetch failed, falling back to mock", e);
    }

    return getPerformanceApplicationDetails(id);
  };

  return {
    applications: sortedApplications,
    criticalCount,
    warningCount,
    getDetails,
    loading,
    error,
  };
};

