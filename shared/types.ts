export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: string[];
  confidence?: number;
  followUpQuestions?: string[];
  bottlenecks?: BottleneckReport[];
};

export type ChatResponse = {
  response: string;
  sources: string[];
  confidence?: number;
  confidenceLevel?: "low" | "medium" | "high";
  followUpQuestions?: string[];
  bottlenecks?: BottleneckReport[];
};

export type BottleneckType =
  | "cpu"
  | "memory"
  | "network"
  | "database"
  | "disk_io"
  | "application"
  | "other";

export type BottleneckSeverity = "critical" | "high" | "medium" | "low";

export type BottleneckReport = {
  bottleneck_type: BottleneckType;
  severity: BottleneckSeverity;
  description: string;
  evidence: string[];
  recommendations: string[];
};

export type StreamDelta =
  | { event: "status"; payload: { stage: string } }
  | { event: "trace"; payload: { type: "sources"; items: string[] } }
  | { event: "token"; payload: { text: string } }
  | { event: "final"; payload: { response: string; sources: string[] } };

export type KPIThreshold = {
  threshold: number;
  unit: string;
  detected: boolean;
};

export type KPIConfig = {
  cpu: KPIThreshold;
  memory: KPIThreshold;
  network: KPIThreshold;
  database: KPIThreshold;
  disk_io: KPIThreshold;
};

export type KPIExplanation = {
  kpis: KPIConfig;
  explanations: Record<string, string>;
};

