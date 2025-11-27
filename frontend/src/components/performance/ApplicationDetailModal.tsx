import type {
  PerformanceAnalysis,
  PerformanceApplicationDetails,
} from "../../types/performance";
import { StatusBadge } from "./StatusBadge";
import { PerformanceChart } from "./PerformanceChart";
import { MessageSquare, X } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { ScrollArea } from "../ui/scroll-area";

interface ApplicationDetailModalProps {
  application: PerformanceApplicationDetails | null;
  isOpen: boolean;
  onClose: () => void;
  onBrainstorm: () => void;
  analysis?: PerformanceAnalysis | null;
  analysisLoading?: boolean;
}

export const ApplicationDetailModal = ({
  application,
  isOpen,
  onClose,
  onBrainstorm,
  analysis,
  analysisLoading,
}: ApplicationDetailModalProps) => {
  if (!application) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="flex h-[90vh] max-w-6xl flex-col p-0">
        <DialogHeader className="border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="mb-2 text-2xl font-bold">
                {application.name}
              </DialogTitle>
              <StatusBadge status={application.status} />
            </div>
            <Button variant="outline" onClick={onClose} size="icon">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        <ScrollArea className="flex-1 px-6">
          <div className="space-y-6 py-6">
            <Card className="border-primary/20 bg-primary/5 p-6">
              <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold">
                <span className="text-primary">Executive Summary</span>
              </h3>
              <p className="text-sm leading-relaxed">
                {application.executiveSummary}
              </p>
            </Card>

            <div className="space-y-4">
              <h3 className="text-xl font-semibold">Performance Metrics</h3>
              <div className="grid gap-4">
                <PerformanceChart
                  title="Response Time"
                  data={application.metrics.responseTime}
                  unit="ms"
                  color="hsl(var(--chart-1))"
                />
                <PerformanceChart
                  title="Error Rate"
                  data={application.metrics.errorRate}
                  unit="%"
                  color="hsl(var(--chart-5))"
                />
                <PerformanceChart
                  title="Throughput"
                  data={application.metrics.throughput}
                  unit=" req/s"
                  color="hsl(var(--chart-3))"
                />
              </div>
            </div>

            <Card className="p-6 space-y-3">
              <h3 className="text-lg font-semibold">
                Analysis &amp; Reasoning
              </h3>
              <div className="prose prose-sm max-w-none">
                <div className="whitespace-pre-line text-sm leading-relaxed">
                  {application.reasoning}
                </div>
              </div>

              <div className="border-t pt-3">
                <h4 className="mb-2 text-sm font-semibold text-muted-foreground">
                  AI Analysis (live)
                </h4>
                {analysisLoading ? (
                  <p className="text-sm text-muted-foreground">
                    Running performance analysis with the AI agent…
                  </p>
                ) : analysis ?
                  <div className="whitespace-pre-line text-sm leading-relaxed">
                    {analysis.response}
                  </div>
                : (
                  <p className="text-sm text-muted-foreground">
                    Trigger an AI analysis from the dashboard to see a live summary here.
                  </p>
                )}
              </div>
            </Card>

            <div className="flex justify-center pb-4">
              <Button
                onClick={onBrainstorm}
                size="lg"
                className="gap-2 shadow-lg"
              >
                <MessageSquare className="h-5 w-5" />
                Brainstorm with AI for Deeper Analysis
              </Button>
            </div>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};


