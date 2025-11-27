export type CriticalityLevel = "critical" | "warning" | "healthy";

export interface PerformanceApplication {
  id: string;
  name: string;
  status: CriticalityLevel;
  responseTime: number;
  errorRate: number;
  throughput: number;
  lastChecked: string;
  description: string;
}

export interface PerformanceMetric {
  timestamp: string;
  value: number;
}

export interface PerformanceApplicationDetails extends PerformanceApplication {
  executiveSummary: string;
  reasoning: string;
  metrics: {
    responseTime: PerformanceMetric[];
    errorRate: PerformanceMetric[];
    throughput: PerformanceMetric[];
  };
}

export interface PerformanceAnalysis {
  response: string;
  sources: string[];
  confidence?: number;
}



