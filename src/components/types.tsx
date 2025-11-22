import type { Mention, DashboardStats, PaginationInfo, Alert } from '../services/api';

// MentionFeed component props
export interface MentionFeedProps {
  mentions: Mention[];
  loading: boolean;
  showPagination?: boolean;
  pagination?: PaginationInfo;
  onPageChange?: (page: number) => void;
  offline?: boolean;
}

// SentimentChart component props
export interface SentimentChartProps {
  stats: DashboardStats | null;
  loading?: boolean;
}

// TrendGraph component props  
export interface TrendGraphProps {
  stats: DashboardStats | null;
  loading?: boolean;
  timeRange?: string;
}

// SourceBreakdown component props
export interface SourceBreakdownProps {
  stats: DashboardStats | null;
  loading?: boolean;
  showEngagement?: boolean;
}

// TopicClusters component props
export interface TopicClustersProps {
  mentions: Mention[];
  loading?: boolean;
}

// AlertCards component props
export interface AlertCardsProps {
  alerts: Alert[];
  loading?: boolean;
  connectedStatus?: 'connected' | 'disconnected' | 'connecting';
}

interface ChartProps {
  stats: DashboardStats | null;
  loading: boolean;
  offline?: boolean;
  timeRange?: string;
  showEngagement?: boolean;
}

// Filters component props
export interface FiltersProps {
  filters: {
    source: string;
    sentiment: string;
    date_range: string;
    search: string;
    category?: string;
    language?: string;
  };
  setFilters: (filters: { source: string; sentiment: string; date_range: string; search: string; category?: string; language?: string }) => void;
}