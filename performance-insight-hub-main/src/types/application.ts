export type CriticalityLevel = 'critical' | 'warning' | 'healthy';

export interface Application {
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

export interface ApplicationDetails extends Application {
  executiveSummary: string;
  reasoning: string;
  metrics: {
    responseTime: PerformanceMetric[];
    errorRate: PerformanceMetric[];
    throughput: PerformanceMetric[];
  };
}
