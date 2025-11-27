import { Application } from '@/types/application';
import { Card } from '@/components/ui/card';
import { StatusBadge } from './StatusBadge';
import { Activity, Clock, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ApplicationCardProps {
  application: Application;
  onClick: () => void;
}

export const ApplicationCard = ({ application, onClick }: ApplicationCardProps) => {
  return (
    <Card 
      className={cn(
        "p-6 cursor-pointer transition-all hover:shadow-lg border-l-4",
        application.status === 'critical' && "border-l-status-critical",
        application.status === 'warning' && "border-l-status-warning",
        application.status === 'healthy' && "border-l-status-healthy"
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold mb-1">{application.name}</h3>
          <p className="text-sm text-muted-foreground">{application.description}</p>
        </div>
        <StatusBadge status={application.status} />
      </div>
      
      <div className="grid grid-cols-3 gap-4 mt-4">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">Response Time</p>
            <p className="text-sm font-semibold">{application.responseTime}ms</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">Error Rate</p>
            <p className="text-sm font-semibold">{application.errorRate}%</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">Throughput</p>
            <p className="text-sm font-semibold">{application.throughput}/s</p>
          </div>
        </div>
      </div>
    </Card>
  );
};
