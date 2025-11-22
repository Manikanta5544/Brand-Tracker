import { useState, useEffect, useCallback } from 'react';
import { MentionFeed } from '../components/MentionFeed';
import { SentimentChart } from '../components/SentimentChart';
import { TrendGraph } from '../components/TrendGraph';
import { TopicClusters } from '../components/TopicClusters';
import { AlertCards } from '../components/AlertCards';
import { SourceBreakdown } from '../components/SourceBreakdown';
import { Filters } from '../components/Filters';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Activity, TrendingUp, AlertTriangle, MessageSquare, RefreshCw, Download, Server, Wifi, WifiOff } from 'lucide-react';
import { 
  api, 
  type Mention, 
  type DashboardStats, 
  type Filters as FiltersType,
  type PaginationInfo,
  type Alert 
} from '../services/api';

interface DashboardState {
  stats: DashboardStats | null;
  mentions: Mention[];
  alerts: Alert[];
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  lastUpdated: Date | null;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
}

export default function Dashboard() {
  const [filters, setFilters] = useState<FiltersType>({
    source: '',
    sentiment: '',
    date_range: '24h',
    search: ''
  });

  const [state, setState] = useState<DashboardState>({
    stats: null,
    mentions: [],
    alerts: [],
    loading: true,
    refreshing: false,
    error: null,
    lastUpdated: null,
    connectionStatus: 'connecting'
  });

  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    limit: 20,
    total: 0,
    total_pages: 0,
  });

  const checkConnection = useCallback(async () => {
    try {
      const isHealthy = await api.healthCheck();
      setState(prev => ({ 
        ...prev, 
        connectionStatus: isHealthy ? 'connected' : 'disconnected' 
      }));
      return isHealthy;
    } catch {
      setState(prev => ({ ...prev, connectionStatus: 'disconnected' }));
      return false;
    }
  }, []);

  const loadDashboardData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, error: null, loading: true }));
      
      let isConnected = false;
      try {
        isConnected = await checkConnection();
      } catch (connectionError) {
        console.error('Connection check failed:', connectionError);
        isConnected = false;
      }
      
      if (!isConnected) {
        // Use fallback data but show connection warning
        const fallbackStats = {
          total_mentions: 1247,
          sentiment_distribution: {
            positive: 560,
            negative: 312,
            neutral: 375
          },
          active_alerts: 3,
          mention_velocity: 12.5,
          engagement_rate: 4.2,
          top_sources: [
            { source: 'twitter', count: 543, percentage: 43.5 },
            { source: 'reddit', count: 321, percentage: 25.7 },
            { source: 'news', count: 215, percentage: 17.2 },
            { source: 'review', count: 168, percentage: 13.5 }
          ],
          top_categories: [
            { category: 'customer_service', count: 287, percentage: 23 },
            { category: 'product_quality', count: 234, percentage: 18.7 },
            { category: 'pricing', count: 198, percentage: 15.9 },
            { category: 'brand_awareness', count: 176, percentage: 14.1 }
          ]
        };
        
        setState(prev => ({
          ...prev,
          stats: fallbackStats,
          mentions: [],
          alerts: [],
          lastUpdated: new Date(),
          connectionStatus: 'disconnected',
          error: 'Running in offline mode with sample data. Backend server is not available.'
        }));
        return;
      }
      
      // If connected, load real data
      const [statsData, mentionsResponse, alertsData] = await Promise.all([
        api.getDashboardStats(filters.date_range),
        api.getMentions(filters, pagination.page, pagination.limit),
        api.getActiveAlerts(),
      ]);
      
      setState(prev => ({
        ...prev,
        stats: statsData,
        mentions: mentionsResponse.mentions,
        alerts: alertsData,
        lastUpdated: new Date(),
        connectionStatus: 'connected'
      }));

      setPagination(mentionsResponse.pagination);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load dashboard data';
      setState(prev => ({ 
        ...prev, 
        error: errorMessage,
        connectionStatus: 'disconnected'
      }));
      console.error('Dashboard data loading error:', err);
    } finally {
      setState(prev => ({ ...prev, loading: false, refreshing: false }));
    }
  }, [filters, pagination.page, pagination.limit, checkConnection]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleRefresh = () => {
    setState(prev => ({ ...prev, refreshing: true }));
    loadDashboardData();
  };

  const handleFiltersChange = (newFilters: FiltersType) => {
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handlePageChange = (newPage: number) => {
    setPagination(prev => ({ ...prev, page: newPage }));
  };

  const handleExport = async () => {
    try {
      const blob = await api.exportMentions(filters, 'csv');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `brand-mentions-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Export failed';
      setState(prev => ({ ...prev, error: errorMessage }));
    }
  };

  const positivePercentage = state.stats 
    ? Math.round((state.stats.sentiment_distribution.positive / state.stats.total_mentions) * 100) || 0
    : 0;

  const ConnectionStatus = () => (
    <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs ${
      state.connectionStatus === 'connected' 
        ? 'bg-green-100 text-green-800 border border-green-200' 
        : state.connectionStatus === 'disconnected'
        ? 'bg-red-100 text-red-800 border border-red-200'
        : 'bg-yellow-100 text-yellow-800 border border-yellow-200'
    }`}>
      {state.connectionStatus === 'connected' ? (
        <Wifi className="h-3 w-3" />
      ) : state.connectionStatus === 'disconnected' ? (
        <WifiOff className="h-3 w-3" />
      ) : (
        <Server className="h-3 w-3 animate-pulse" />
      )}
      <span className="capitalize">
        {state.connectionStatus === 'connecting' ? 'Checking...' : state.connectionStatus}
      </span>
    </div>
  );

  if (state.error && !state.loading && state.connectionStatus === 'disconnected' && !state.stats) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <Server className="h-16 w-16 text-red-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">Backend Connection Error</h2>
              <p className="text-muted-foreground mb-4">{state.error}</p>
              <div className="space-y-3">
                <button
                  onClick={handleRefresh}
                  className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
                >
                  Retry Connection
                </button>
                <div className="text-xs text-muted-foreground">
                  <p>Make sure your backend server is running:</p>
                  <code className="bg-gray-100 px-2 py-1 rounded mt-1 block">
                    python main.py
                  </code>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <header className="border-b bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-linear-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Brand Reputation Intelligence
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                Real-time monitoring & AI-powered insights
                {state.lastUpdated && (
                  <span className="ml-2">
                    • Last updated: {state.lastUpdated.toLocaleTimeString()}
                  </span>
                )}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <ConnectionStatus />
              <button
                onClick={handleExport}
                disabled={state.loading || state.connectionStatus === 'disconnected'}
                className="flex items-center gap-2 px-3 py-2 text-sm bg-background border border-border rounded-lg hover:bg-accent transition-colors disabled:opacity-50"
              >
                <Download className="h-4 w-4" />
                Export
              </button>
              <button
                onClick={handleRefresh}
                disabled={state.refreshing}
                className="flex items-center gap-2 px-3 py-2 text-sm bg-background border border-border rounded-lg hover:bg-accent transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${state.refreshing ? 'animate-spin' : ''}`} />
                {state.refreshing ? 'Refreshing...' : 'Refresh'}
              </button>
              <div className="flex gap-2">
                <Card className="px-4 py-2">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4 text-blue-500" />
                    <div>
                      <p className="text-xs text-muted-foreground">Total Mentions</p>
                      <p className="text-lg font-bold">
                        {state.loading ? '...' : (state.stats?.total_mentions || 0).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </Card>
                <Card className="px-4 py-2">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-green-500" />
                    <div>
                      <p className="text-xs text-muted-foreground">Positive</p>
                      <p className="text-lg font-bold">
                        {state.loading ? '...' : `${positivePercentage}%`}
                      </p>
                    </div>
                  </div>
                </Card>
                <Card className="px-4 py-2">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                    <div>
                      <p className="text-xs text-muted-foreground">Alerts</p>
                      <p className="text-lg font-bold">
                        {state.loading ? '...' : state.stats?.active_alerts || 0}
                      </p>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {state.error && (
          <div className={`mb-6 p-4 rounded-lg border ${
            state.connectionStatus === 'disconnected' 
              ? 'bg-yellow-50 border-yellow-200 text-yellow-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}>
            <div className="flex items-center gap-2">
              <AlertTriangle className={`h-4 w-4 ${
                state.connectionStatus === 'disconnected' ? 'text-yellow-600' : 'text-red-600'
              }`} />
              <span className="text-sm flex-1">{state.error}</span>
              <button
                onClick={() => setState(prev => ({ ...prev, error: null }))}
                className={`ml-2 ${
                  state.connectionStatus === 'disconnected' ? 'text-yellow-600' : 'text-red-600'
                } hover:opacity-70`}
              >
                ×
              </button>
            </div>
            {state.connectionStatus === 'disconnected' && (
              <div className="mt-2 text-xs">
                <p>To fix this:</p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>Ensure the backend server is running on http://localhost:8000</li>
                  <li>Check that CORS is properly configured</li>
                  <li>Verify the API endpoints are accessible</li>
                </ul>
              </div>
            )}
          </div>
        )}

        <div className="mb-6">
          <Filters filters={filters} setFilters={handleFiltersChange} />
        </div>

        <div className="mb-6">
          <AlertCards 
            alerts={state.alerts} 
            loading={state.loading}
            connectedStatus={state.connectionStatus}
          />
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-auto">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="mentions">
              Mentions {!state.loading && `(${(pagination.total || 0).toLocaleString()})`}
            </TabsTrigger>
            <TabsTrigger value="topics">Topics</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Sentiment Distribution</CardTitle>
                  <CardDescription>
                    {state.connectionStatus === 'disconnected' ? 'Sample data - Backend offline' : 'Real-time sentiment analysis'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <SentimentChart 
                    stats={state.stats} 
                    loading={state.loading}
                    offline={state.connectionStatus === 'disconnected'}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Mention Trends</CardTitle>
                  <CardDescription>
                    {state.connectionStatus === 'disconnected' ? 'Sample data - Backend offline' : 'Velocity and engagement'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <TrendGraph 
                    stats={state.stats} 
                    loading={state.loading}
                    offline={state.connectionStatus === 'disconnected'}
                  />
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Source Distribution</CardTitle>
                  <CardDescription>
                    {state.connectionStatus === 'disconnected' ? 'Sample data - Backend offline' : 'Where mentions are coming from'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <SourceBreakdown 
                    stats={state.stats} 
                    loading={state.loading}
                    offline={state.connectionStatus === 'disconnected'}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recent Mentions</CardTitle>
                  <CardDescription>
                    {state.connectionStatus === 'disconnected' ? 'No data - Backend offline' : 'Live feed'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="max-h-[400px] overflow-y-auto">
                  <MentionFeed 
                    mentions={state.mentions.slice(0, 5)} 
                    loading={state.loading}
                    showPagination={false}
                    offline={state.connectionStatus === 'disconnected'}
                  />
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="mentions">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  All Mentions
                  {state.connectionStatus === 'disconnected' && (
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
                      Offline Mode
                    </span>
                  )}
                </CardTitle>
                <CardDescription>
                  {state.connectionStatus === 'disconnected' 
                    ? 'No real data available - Backend server is offline'
                    : `Real-time feed of brand mentions • Page ${pagination.page} of ${pagination.total_pages || 1}`
                  }
                </CardDescription>
              </CardHeader>
              <CardContent>
                <MentionFeed 
                  mentions={state.mentions} 
                  loading={state.loading}
                  pagination={pagination}
                  onPageChange={handlePageChange}
                  showPagination={true}
                  offline={state.connectionStatus === 'disconnected'}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="topics">
            <Card>
              <CardHeader>
                <CardTitle>Topic Clusters</CardTitle>
                <CardDescription>
                  {state.connectionStatus === 'disconnected' ? 'No data - Backend offline' : 'AI-detected themes and conversations'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <TopicClusters 
                  mentions={state.mentions} 
                  loading={state.loading}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Sentiment Over Time</CardTitle>
                  <CardDescription>
                    {state.connectionStatus === 'disconnected' ? 'Sample data - Backend offline' : '7-day trend analysis'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <TrendGraph 
                    stats={state.stats} 
                    loading={state.loading} 
                    timeRange="7d"
                    offline={state.connectionStatus === 'disconnected'}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Engagement Analysis</CardTitle>
                  <CardDescription>
                    {state.connectionStatus === 'disconnected' ? 'Sample data - Backend offline' : 'Performance metrics by source'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <SourceBreakdown 
                    stats={state.stats} 
                    loading={state.loading} 
                    showEngagement={true}
                    offline={state.connectionStatus === 'disconnected'}
                  />
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer with connection status */}
      <footer className="border-t bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm mt-12">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-4">
              <span>Brand Reputation Intelligence v1.0.0</span>
              <span>•</span>
              <span>
                {state.connectionStatus === 'connected' 
                  ? 'Connected to backend API' 
                  : state.connectionStatus === 'disconnected'
                  ? 'Backend API unavailable - using sample data'
                  : 'Checking connection...'
                }
              </span>
            </div>
            <div>
              {state.lastUpdated && (
                <span>Last refresh: {state.lastUpdated.toLocaleTimeString()}</span>
              )}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}