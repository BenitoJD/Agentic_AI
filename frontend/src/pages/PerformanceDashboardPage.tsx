import { useState } from "react";
import { Activity } from "lucide-react";

import type { PerformanceApplicationDetails } from "../types/performance";
import { ApplicationCard } from "../components/performance/ApplicationCard";
import { ApplicationDetailModal } from "../components/performance/ApplicationDetailModal";
import { BrainstormModal } from "../components/performance/BrainstormModal";
import { usePerformanceApplications } from "../hooks/usePerformanceApplications";

type PerformanceDashboardPageProps = {
  onOpenChat: () => void;
  onOpenUploads: () => void;
};

export const PerformanceDashboardPage = ({
  onOpenChat,
  onOpenUploads,
}: PerformanceDashboardPageProps) => {
  const {
    applications,
    criticalCount,
    warningCount,
    getDetails,
  } = usePerformanceApplications();

  const [selectedApp, setSelectedApp] =
    useState<PerformanceApplicationDetails | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isBrainstormOpen, setIsBrainstormOpen] = useState(false);

  const handleApplicationClick = (id: string) => {
    const details = getDetails(id);
    setSelectedApp(details);
    setIsDetailOpen(true);
  };

  const handleBrainstormClick = () => {
    setIsDetailOpen(false);
    setIsBrainstormOpen(true);
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="container mx-auto flex items-center justify-between px-6 py-6">
          <div>
            <div className="mb-2 flex items-center gap-3">
              <div className="rounded-lg bg-primary/10 p-2">
                <Activity className="h-6 w-6 text-primary" />
              </div>
              <h1 className="text-3xl font-bold">
                Performance Bottleneck Analysis
              </h1>
            </div>
            <p className="text-sm text-muted-foreground">
              Real-time monitoring and analysis of connected applications
            </p>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onOpenChat}
              className="rounded-md border px-3 py-1.5 text-sm font-medium text-foreground hover:bg-muted"
            >
              Chat
            </button>
            <button
              type="button"
              onClick={onOpenUploads}
              className="rounded-md border px-3 py-1.5 text-sm font-medium text-foreground hover:bg-muted"
            >
              Uploads
            </button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-6">
        <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-4">
          <div className="rounded-lg border bg-card p-4">
            <p className="mb-1 text-sm text-muted-foreground">
              Total Applications
            </p>
            <p className="text-2xl font-bold">{applications.length}</p>
          </div>
          <div className="rounded-lg border border-status-critical/20 bg-card p-4">
            <p className="mb-1 text-sm text-muted-foreground">Critical Issues</p>
            <p className="text-2xl font-bold text-status-critical">
              {criticalCount}
            </p>
          </div>
          <div className="rounded-lg border border-status-warning/20 bg-card p-4">
            <p className="mb-1 text-sm text-muted-foreground">Warnings</p>
            <p className="text-2xl font-bold text-status-warning">
              {warningCount}
            </p>
          </div>
          <div className="rounded-lg border border-status-healthy/20 bg-card p-4">
            <p className="mb-1 text-sm text-muted-foreground">Healthy</p>
            <p className="text-2xl font-bold text-status-healthy">
              {applications.length - criticalCount - warningCount}
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold">Connected Applications</h2>
            <p className="text-sm text-muted-foreground">
              Sorted by criticality (highest first)
            </p>
          </div>

          {applications.map((app) => (
            <ApplicationCard
              key={app.id}
              application={app}
              onClick={() => handleApplicationClick(app.id)}
            />
          ))}
        </div>
      </div>

      <ApplicationDetailModal
        application={selectedApp}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        onBrainstorm={handleBrainstormClick}
      />

      <BrainstormModal
        isOpen={isBrainstormOpen}
        onClose={() => {
          setIsBrainstormOpen(false);
          setIsDetailOpen(true);
        }}
        applicationName={selectedApp?.name ?? ""}
      />
    </div>
  );
};


