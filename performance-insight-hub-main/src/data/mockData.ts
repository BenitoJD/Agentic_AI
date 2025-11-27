import { Application, ApplicationDetails, PerformanceMetric } from '@/types/application';

const generateMetrics = (baseValue: number, variance: number, count: number = 24): PerformanceMetric[] => {
  const now = new Date();
  return Array.from({ length: count }, (_, i) => ({
    timestamp: new Date(now.getTime() - (count - i) * 3600000).toISOString(),
    value: Math.max(0, baseValue + (Math.random() - 0.5) * variance)
  }));
};

export const mockApplications: Application[] = [
  {
    id: '1',
    name: 'Payment Processing API',
    status: 'critical',
    responseTime: 2450,
    errorRate: 8.5,
    throughput: 1250,
    lastChecked: new Date().toISOString(),
    description: 'Core payment processing service handling all transaction requests'
  },
  {
    id: '2',
    name: 'User Authentication Service',
    status: 'warning',
    responseTime: 850,
    errorRate: 2.1,
    throughput: 5400,
    lastChecked: new Date().toISOString(),
    description: 'Authentication and authorization service for all applications'
  },
  {
    id: '3',
    name: 'Inventory Management',
    status: 'critical',
    responseTime: 3200,
    errorRate: 12.3,
    throughput: 800,
    lastChecked: new Date().toISOString(),
    description: 'Real-time inventory tracking and management system'
  },
  {
    id: '4',
    name: 'Analytics Dashboard',
    status: 'healthy',
    responseTime: 320,
    errorRate: 0.3,
    throughput: 2100,
    lastChecked: new Date().toISOString(),
    description: 'Business intelligence and reporting dashboard'
  },
  {
    id: '5',
    name: 'Email Notification Service',
    status: 'warning',
    responseTime: 1100,
    errorRate: 3.8,
    throughput: 3200,
    lastChecked: new Date().toISOString(),
    description: 'Handles all email notifications and communications'
  },
  {
    id: '6',
    name: 'Search Engine API',
    status: 'healthy',
    responseTime: 180,
    errorRate: 0.5,
    throughput: 8500,
    lastChecked: new Date().toISOString(),
    description: 'Full-text search service across all products'
  }
];

export const getApplicationDetails = (id: string): ApplicationDetails => {
  const app = mockApplications.find(a => a.id === id);
  if (!app) throw new Error('Application not found');

  const details: ApplicationDetails = {
    ...app,
    executiveSummary: generateExecutiveSummary(app),
    reasoning: generateReasoning(app),
    metrics: {
      responseTime: generateMetrics(app.responseTime, app.responseTime * 0.3),
      errorRate: generateMetrics(app.errorRate, app.errorRate * 0.4),
      throughput: generateMetrics(app.throughput, app.throughput * 0.2)
    }
  };

  return details;
};

const generateExecutiveSummary = (app: Application): string => {
  if (app.status === 'critical') {
    return `${app.name} is experiencing critical performance issues. Response times are averaging ${app.responseTime}ms (target: <500ms) with an error rate of ${app.errorRate}% (target: <1%). Immediate attention required to prevent service degradation and potential revenue impact.`;
  }
  if (app.status === 'warning') {
    return `${app.name} is showing warning signs with response times at ${app.responseTime}ms and error rates at ${app.errorRate}%. Performance is degraded but stable. Recommend investigation within 24-48 hours to prevent escalation to critical status.`;
  }
  return `${app.name} is operating within normal parameters. Response times averaging ${app.responseTime}ms with minimal errors (${app.errorRate}%). Current throughput of ${app.throughput} req/s is well within capacity limits.`;
};

const generateReasoning = (app: Application): string => {
  const issues = [];
  
  if (app.responseTime > 2000) {
    issues.push('• **Database Query Performance**: Slow queries detected, likely due to missing indexes or inefficient joins');
    issues.push('• **Memory Pressure**: High memory utilization causing garbage collection delays');
  } else if (app.responseTime > 800) {
    issues.push('• **Network Latency**: Increased latency in downstream service calls');
  }
  
  if (app.errorRate > 5) {
    issues.push('• **Connection Pool Exhaustion**: Database connections maxed out during peak load');
    issues.push('• **Timeout Issues**: Requests timing out before completion');
  } else if (app.errorRate > 2) {
    issues.push('• **Intermittent Failures**: Occasional timeouts under load');
  }
  
  if (app.throughput < 1000 && app.status !== 'healthy') {
    issues.push('• **Resource Constraints**: CPU or memory bottlenecks limiting throughput');
  }
  
  if (issues.length === 0) {
    return '**Performance Analysis:**\n\n• All metrics within acceptable ranges\n• No bottlenecks detected\n• System operating efficiently\n• Resource utilization optimal';
  }
  
  return '**Root Cause Analysis:**\n\n' + issues.join('\n');
};
