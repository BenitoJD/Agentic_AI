import type { CriticalityLevel } from "../../types/performance";
import { Badge } from "../ui/badge";
import { AlertCircle, AlertTriangle, CheckCircle } from "lucide-react";

interface StatusBadgeProps {
  status: CriticalityLevel;
  size?: "sm" | "md";
}

export const StatusBadge = ({ status, size = "md" }: StatusBadgeProps) => {
  const iconSize = size === "sm" ? 12 : 16;

  const config: Record<
    CriticalityLevel,
    { icon: typeof AlertCircle; label: string; className: string }
  > = {
    critical: {
      icon: AlertCircle,
      label: "Critical",
      className:
        "bg-status-critical/10 text-status-critical border-status-critical/20",
    },
    warning: {
      icon: AlertTriangle,
      label: "Warning",
      className:
        "bg-status-warning/10 text-status-warning border-status-warning/20",
    },
    healthy: {
      icon: CheckCircle,
      label: "Healthy",
      className:
        "bg-status-healthy/10 text-status-healthy border-status-healthy/20",
    },
  };

  const { icon: Icon, label, className } = config[status];

  return (
    <Badge variant="outline" className={className}>
      <Icon size={iconSize} className="mr-1.5" />
      {label}
    </Badge>
  );
};


