import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ApplicationDetails } from '@/types/application';
import { StatusBadge } from './StatusBadge';
import { PerformanceChart } from './PerformanceChart';
import { MessageSquare, X } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

interface ApplicationDetailModalProps {
  application: ApplicationDetails | null;
  isOpen: boolean;
  onClose: () => void;
  onBrainstorm: () => void;
}

export const ApplicationDetailModal = ({ 
  application, 
  isOpen, 
  onClose,
  onBrainstorm 
}: ApplicationDetailModalProps) => {
  if (!application) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl h-[90vh] p-0">
        <DialogHeader className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="text-2xl font-bold mb-2">{application.name}</DialogTitle>
              <StatusBadge status={application.status} />
            </div>
            <Button variant="outline" onClick={onClose} size="icon">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        <ScrollArea className="flex-1 px-6">
          <div className="space-y-6 py-6">
            {/* Executive Summary */}
            <Card className="p-6 bg-primary/5 border-primary/20">
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="text-primary">Executive Summary</span>
              </h3>
              <p className="text-sm leading-relaxed">{application.executiveSummary}</p>
            </Card>

            {/* Performance Graphs */}
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

            {/* Reasoning */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Analysis & Reasoning</h3>
              <div className="prose prose-sm max-w-none">
                <div className="whitespace-pre-line text-sm leading-relaxed">
                  {application.reasoning}
                </div>
              </div>
            </Card>

            {/* Brainstorm Button */}
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
