import { useMemo, useState } from "react";
import { Activity } from "lucide-react";

import type {
  PerformanceAnalysis,
  PerformanceApplicationDetails,
} from "../types/performance";
import { ApplicationCard } from "../components/performance/ApplicationCard";
import { ApplicationDetailModal } from "../components/performance/ApplicationDetailModal";
import { BrainstormModal } from "../components/performance/BrainstormModal";
import { usePerformanceApplications } from "../hooks/usePerformanceApplications";

type PerformanceDashboardPageProps = {
  onOpenChat: () => void;
  onOpenUploads: () => void;
};

type StatusFilter = "all" | "critical" | "warning" | "healthy";

export const PerformanceDashboardPage = ({
  onOpenChat,
  onOpenUploads,
}: PerformanceDashboardPageProps) => {
  const {
    applications,
    criticalCount,
    warningCount,
    getDetails,
    loading,
    error,
  } = usePerformanceApplications();

  const [selectedApp, setSelectedApp] =
    useState<PerformanceApplicationDetails | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isBrainstormOpen, setIsBrainstormOpen] = useState(false);
  const [analysis, setAnalysis] = useState<PerformanceAnalysis | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [filter, setFilter] = useState<StatusFilter>("all");

  const filteredApplications = useMemo(
    () =>
      applications.filter((app) =>
        filter === "all" ? true : app.status === filter,
      ),
    [applications, filter],
  );

  const handleApplicationClick = async (id: string) => {
    const details = await getDetails(id);
    setSelectedApp(details);
    setIsDetailOpen(true);

    setAnalysis(null);
    setAnalysisError(null);
    setAnalysisLoading(true);

    try {
      const res = await fetch(`/api/analysis/applications/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        throw new Error(await res.text());
      }
      const data = (await res.json()) as PerformanceAnalysis;
      setAnalysis(data);
    } catch (e) {
      console.error("[analysis] failed", e);
      setAnalysisError("AI analysis failed. Showing static reasoning only.");
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleBrainstormClick = () => {
    setIsDetailOpen(false);
    setIsBrainstormOpen(true);
  };

  return (
    <div className="min-h-screen bg-surface">
      <header className="border-b bg-gradient-to-r from-primary to-accentToken text-white shadow-lg">
        <div className="container mx-auto flex items-center justify-between px-6 py-6">
          <div>
            <div className="mb-2 flex items-center gap-3">
              <div className="rounded-xl bg-white/10 p-2 shadow">
                <Activity className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-3xl font-bold tracking-tight">
                Performance Bottleneck Analysis
              </h1>
            </div>
            <p className="text-sm text-white/80">
              Real-time monitoring and analysis of connected applications
            </p>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onOpenChat}
              className="rounded-md border border-white/30 bg-white/10 px-3 py-1.5 text-sm font-medium text-white backdrop-blur hover:bg-white/20"
            >
              Chat
            </button>
            <button
              type="button"
              onClick={onOpenUploads}
              className="rounded-md border border-white/30 bg-white/10 px-3 py-1.5 text-sm font-medium text-white backdrop-blur hover:bg-white/20"
            >
              Uploads
            </button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        {error && (
          <p className="mb-4 text-sm text-yellow-600">
            {error}
          </p>
        )}

        <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-4">
          <button
            type="button"
            onClick={() => setFilter("all")}
            className={`rounded-xl border bg-card p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-xl ${
              filter === "all" ? "ring-2 ring-primary/60" : ""
            }`}
          >
            <p className="mb-1 text-sm font-medium text-black">
              Total Applications
            </p>
            <p className="text-2xl font-bold text-black">
              {applications.length}
            </p>
          </button>
          <button
            type="button"
            onClick={() => setFilter("critical")}
            className={`rounded-xl border border-status-critical/30 bg-card p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-xl ${
              filter === "critical" ? "ring-2 ring-status-critical/60" : ""
            }`}
          >
            <p className="mb-1 text-sm font-medium text-black">Critical Issues</p>
            <p className="text-2xl font-bold text-black">{criticalCount}</p>
          </button>
          <button
            type="button"
            onClick={() => setFilter("warning")}
            className={`rounded-xl border border-status-warning/30 bg-card p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-xl ${
              filter === "warning" ? "ring-2 ring-status-warning/60" : ""
            }`}
          >
            <p className="mb-1 text-sm font-medium text-black">Warnings</p>
            <p className="text-2xl font-bold text-black">{warningCount}</p>
          </button>
          <button
            type="button"
            onClick={() => setFilter("healthy")}
            className={`rounded-xl border border-status-healthy/30 bg-card p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-xl ${
              filter === "healthy" ? "ring-2 ring-status-healthy/60" : ""
            }`}
          >
            <p className="mb-1 text-sm font-medium text-black">Healthy</p>
            <p className="text-2xl font-bold text-black">
              {applications.length - criticalCount - warningCount}
            </p>
          </button>
        </div>

        <div className="space-y-4">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold">Connected Applications</h2>
            <p className="text-sm text-muted-foreground">
              {filter === "all"
                ? "Sorted by criticality (highest first)"
                : `Showing only ${filter} applications`}
            </p>
          </div>

          {loading ? (
            <p className="text-sm text-muted-foreground">Loading applications…</p>
          ) : filteredApplications.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No applications match this filter.
            </p>
          ) : (
            filteredApplications.map((app) => (
              <ApplicationCard
                key={app.id}
                application={app}
                onClick={() => {
                  void handleApplicationClick(app.id);
                }}
              />
            ))
          )}
        </div>
      </div>

      <ApplicationDetailModal
        application={selectedApp}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        onBrainstorm={handleBrainstormClick}
        analysis={analysis}
        analysisLoading={analysisLoading}
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


