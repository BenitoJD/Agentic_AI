import { AlertTriangle, Cpu, Database, HardDrive, Network, Zap, AlertCircle } from "lucide-react";
import type { BottleneckReport } from "@shared/types";

type BottleneckDisplayProps = {
  bottlenecks: BottleneckReport[];
};

const getBottleneckIcon = (type: BottleneckReport["bottleneck_type"]) => {
  switch (type) {
    case "cpu":
      return <Cpu className="h-4 w-4" />;
    case "memory":
      return <Zap className="h-4 w-4" />;
    case "network":
      return <Network className="h-4 w-4" />;
    case "database":
      return <Database className="h-4 w-4" />;
    case "disk_io":
      return <HardDrive className="h-4 w-4" />;
    default:
      return <AlertCircle className="h-4 w-4" />;
  }
};

const getSeverityColor = (severity: BottleneckReport["severity"]) => {
  switch (severity) {
    case "critical":
      return "bg-red-500/20 text-red-400 border-red-500/30";
    case "high":
      return "bg-orange-500/20 text-orange-400 border-orange-500/30";
    case "medium":
      return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    case "low":
      return "bg-blue-500/20 text-blue-400 border-blue-500/30";
    default:
      return "bg-gray-500/20 text-gray-400 border-gray-500/30";
  }
};

const getBottleneckTypeLabel = (type: BottleneckReport["bottleneck_type"]) => {
  const labels: Record<BottleneckReport["bottleneck_type"], string> = {
    cpu: "CPU",
    memory: "Memory",
    network: "Network",
    database: "Database",
    disk_io: "Disk I/O",
    application: "Application",
    other: "Other",
  };
  return labels[type] || type;
};

export const BottleneckDisplay = ({ bottlenecks }: BottleneckDisplayProps) => {
  if (!bottlenecks || bottlenecks.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-textPrimary">
        <AlertTriangle className="h-4 w-4 text-yellow-400" />
        Performance Bottlenecks Identified
      </div>
      {bottlenecks.map((bottleneck, index) => (
        <div
          key={index}
          className={`rounded-lg border p-4 ${getSeverityColor(bottleneck.severity)}`}
        >
          <div className="mb-2 flex items-center gap-2">
            {getBottleneckIcon(bottleneck.bottleneck_type)}
            <span className="font-medium">
              {getBottleneckTypeLabel(bottleneck.bottleneck_type)} Bottleneck
            </span>
            <span className="ml-auto rounded-full px-2 py-0.5 text-xs font-medium capitalize">
              {bottleneck.severity}
            </span>
          </div>
          <p className="mb-3 text-sm">{bottleneck.description}</p>
          
          {bottleneck.evidence && bottleneck.evidence.length > 0 && (
            <div className="mb-3">
              <p className="mb-1 text-xs font-medium opacity-80">Evidence:</p>
              <ul className="list-disc space-y-0.5 pl-4 text-xs opacity-70">
                {bottleneck.evidence.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          
          {bottleneck.recommendations && bottleneck.recommendations.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium opacity-80">Recommendations:</p>
              <ul className="list-disc space-y-0.5 pl-4 text-xs opacity-70">
                {bottleneck.recommendations.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

