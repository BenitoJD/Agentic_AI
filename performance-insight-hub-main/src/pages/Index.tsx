import { useState, useMemo } from 'react';
import { mockApplications, getApplicationDetails } from '@/data/mockData';
import { ApplicationCard } from '@/components/ApplicationCard';
import { ApplicationDetailModal } from '@/components/ApplicationDetailModal';
import { BrainstormModal } from '@/components/BrainstormModal';
import { ApplicationDetails } from '@/types/application';
import { Activity } from 'lucide-react';

const Index = () => {
  const [selectedApp, setSelectedApp] = useState<ApplicationDetails | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isBrainstormOpen, setIsBrainstormOpen] = useState(false);

  // Sort applications by criticality
  const sortedApplications = useMemo(() => {
    const criticalityOrder = { critical: 0, warning: 1, healthy: 2 };
    return [...mockApplications].sort(
      (a, b) => criticalityOrder[a.status] - criticalityOrder[b.status]
    );
  }, []);

  const handleApplicationClick = (id: string) => {
    const details = getApplicationDetails(id);
    setSelectedApp(details);
    setIsDetailOpen(true);
  };

  const handleBrainstormClick = () => {
    setIsDetailOpen(false);
    setIsBrainstormOpen(true);
  };

  const criticalCount = sortedApplications.filter(app => app.status === 'critical').length;
  const warningCount = sortedApplications.filter(app => app.status === 'warning').length;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Activity className="h-6 w-6 text-primary" />
            </div>
            <h1 className="text-3xl font-bold">Performance Bottleneck Analysis</h1>
          </div>
          <p className="text-muted-foreground">
            Real-time monitoring and analysis of connected applications
          </p>
        </div>
      </header>

      {/* Stats Overview */}
      <div className="container mx-auto px-6 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-card border rounded-lg p-4">
            <p className="text-sm text-muted-foreground mb-1">Total Applications</p>
            <p className="text-2xl font-bold">{sortedApplications.length}</p>
          </div>
          <div className="bg-card border border-status-critical/20 rounded-lg p-4">
            <p className="text-sm text-muted-foreground mb-1">Critical Issues</p>
            <p className="text-2xl font-bold text-status-critical">{criticalCount}</p>
          </div>
          <div className="bg-card border border-status-warning/20 rounded-lg p-4">
            <p className="text-sm text-muted-foreground mb-1">Warnings</p>
            <p className="text-2xl font-bold text-status-warning">{warningCount}</p>
          </div>
          <div className="bg-card border border-status-healthy/20 rounded-lg p-4">
            <p className="text-sm text-muted-foreground mb-1">Healthy</p>
            <p className="text-2xl font-bold text-status-healthy">
              {sortedApplications.length - criticalCount - warningCount}
            </p>
          </div>
        </div>

        {/* Applications List */}
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Connected Applications</h2>
            <p className="text-sm text-muted-foreground">
              Sorted by criticality (highest first)
            </p>
          </div>
          
          {sortedApplications.map((app) => (
            <ApplicationCard
              key={app.id}
              application={app}
              onClick={() => handleApplicationClick(app.id)}
            />
          ))}
        </div>
      </div>

      {/* Detail Modal */}
      <ApplicationDetailModal
        application={selectedApp}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        onBrainstorm={handleBrainstormClick}
      />

      {/* Brainstorm Modal */}
      <BrainstormModal
        isOpen={isBrainstormOpen}
        onClose={() => {
          setIsBrainstormOpen(false);
          setIsDetailOpen(true);
        }}
        applicationName={selectedApp?.name || ''}
      />
    </div>
  );
};

export default Index;
