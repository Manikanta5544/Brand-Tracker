import { useState } from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { AlertTriangle, TrendingUp, AlertCircle, X } from 'lucide-react';
import { cn } from '../lib/utils';
import type { AlertCardsProps } from './types';

interface LocalAlert {
  id: number;
  type: string;
  message: string;
  severity: string;
  timestamp: string;
}

export function AlertCards({ alerts: propAlerts, loading = false }: AlertCardsProps) {
  const mockAlerts: LocalAlert[] = [
    {
      id: 1,
      type: 'spike',
      message: 'Mention volume increased by 150% in the last hour. Current count: 87 mentions.',
      severity: 'high',
      timestamp: '2024-01-15T10:00:00.000Z' 
    },
    {
      id: 2,
      type: 'negative_surge',
      message: 'Negative sentiment mentions increased by 45%. Investigate potential issues.',
      severity: 'medium',
      timestamp: '2024-01-15T09:30:00.000Z' 
    },
    {
      id: 3,
      type: 'toxicity_alert',
      message: '3 highly toxic mentions detected. Review and take action if necessary.',
      severity: 'critical',
      timestamp: '2024-01-15T09:15:00.000Z' 
    }
  ];

  
  const [alerts, setAlerts] = useState<LocalAlert[]>(() => {
    if (propAlerts && Array.isArray(propAlerts) && propAlerts.length > 0) {
      return propAlerts as unknown as LocalAlert[];
    }
    return mockAlerts;
  });

  const dismissAlert = (id: number) => {
    setAlerts(currentAlerts => currentAlerts.filter(alert => alert.id !== id));
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'border-red-500 bg-red-50 dark:bg-red-950';
      case 'high':
        return 'border-orange-500 bg-orange-50 dark:bg-orange-950';
      case 'medium':
        return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950';
      default:
        return 'border-blue-500 bg-blue-50 dark:bg-blue-950';
    }
  };

  const getSeverityIcon = (type: string) => {
    switch (type) {
      case 'spike':
        return <TrendingUp className="h-5 w-5" />;
      case 'toxicity_alert':
        return <AlertTriangle className="h-5 w-5" />;
      default:
        return <AlertCircle className="h-5 w-5" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 60) return `${minutes} minutes ago`;
    return `${Math.floor(minutes / 60)} hours ago`;
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <Card key={i} className="p-4 border-l-4 border-muted bg-muted/20 animate-pulse">
            <div className="flex items-start gap-3">
              <div className="h-5 w-5 bg-muted rounded mt-0.5"></div>
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <div className="h-4 bg-muted rounded w-16"></div>
                  <div className="h-3 bg-muted rounded w-20"></div>
                </div>
                <div className="h-4 bg-muted rounded w-full"></div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="text-center py-4 text-muted-foreground">
        No active alerts at this time.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <Card 
          key={alert.id} 
          className={cn(
            "p-4 border-l-4",
            getSeverityColor(alert.severity)
          )}
        >
          <div className="flex items-start gap-3">
            <div className={cn(
              "mt-0.5",
              alert.severity === 'critical' ? 'text-red-600' :
              alert.severity === 'high' ? 'text-orange-600' :
              alert.severity === 'medium' ? 'text-yellow-600' :
              'text-blue-600'
            )}>
              {getSeverityIcon(alert.type)}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="outline" className="text-xs font-semibold">
                  {alert.severity.toUpperCase()}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {formatTimestamp(alert.timestamp)}
                </span>
              </div>
              <p className="text-sm font-medium">
                {alert.message}
              </p>
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 shrink-0"
              onClick={() => dismissAlert(alert.id)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
}