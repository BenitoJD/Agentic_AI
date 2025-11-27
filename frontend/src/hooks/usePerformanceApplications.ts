import { useMemo } from "react";

import {
  mockPerformanceApplications,
  getPerformanceApplicationDetails,
} from "../data/performanceMockData";
import type {
  PerformanceApplication,
  PerformanceApplicationDetails,
} from "../types/performance";

export const usePerformanceApplications = () => {
  const applications = useMemo<PerformanceApplication[]>(
    () => [...mockPerformanceApplications],
    [],
  );

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

  const getDetails = (id: string): PerformanceApplicationDetails =>
    getPerformanceApplicationDetails(id);

  return {
    applications: sortedApplications,
    criticalCount,
    warningCount,
    getDetails,
  };
};


