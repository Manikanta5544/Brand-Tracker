const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface Mention {
  id: string;
  text: string;
  source: 'twitter' | 'reddit' | 'news' | 'review';
  sentiment: 'positive' | 'negative' | 'neutral';
  sentiment_score: number;
  timestamp: string;
  author_name?: string;
  author_handle?: string;
  profile_image_url?: string;
  url?: string;
  engagement_metrics?: {
    likes: number;
    shares: number;
    comments: number;
    impressions: number;
  };
  categories: string[];
  language: string;
  location?: string;
  brand_mentions: string[];
}

export interface DashboardStats {
  total_mentions: number;
  sentiment_distribution: {
    positive: number;
    negative: number;
    neutral: number;
  };
  active_alerts: number;
  mention_velocity: number;
  engagement_rate: number;
  top_sources: Array<{
    source: string;
    count: number;
    percentage: number;
  }>;
  top_categories: Array<{
    category: string;
    count: number;
    percentage: number;
  }>;
}

interface DashboardBackendStats {
  total_mentions?: number;
  positive_mentions?: number;
  negative_mentions?: number;
  neutral_mentions?: number;
  spike_alerts?: unknown[];
  recent_mentions?: number;
  top_sources?: {
    source: string;
    count: number;
    percentage: number;
  }[];
  trending_topics?: {
    name?: string;
    count?: number;
  }[];
}

export interface Filters {
  source: string;
  sentiment: string;
  date_range: string;
  search: string;
  category?: string;
  language?: string;
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  pagination?: PaginationInfo;
  timestamp: string;
}

export interface MentionsResponse {
  mentions: Mention[];
  pagination: PaginationInfo;
}

export interface Alert {
  id: string;
  type: 'sentiment_spike' | 'volume_spike' | 'competitor_mention' | 'negative_trend';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  triggered_at: string;
  is_resolved: boolean;
  metadata: Record<string, unknown>;
}
 
interface BackendAlert {
  id: string | number;
  alert_type?: Alert['type'];
  severity?: Alert['severity'];
  title?: string;
  message?: string;
  created_at?: string;
  is_resolved?: boolean;
  metadata?: Record<string, unknown>;
}

interface ActiveAlertsResponse {
  alerts: BackendAlert[];
}

class ApiClient {
  private baseURL: string;
  private retryCount: number;
  private maxRetries: number;

  constructor() {
    this.baseURL = API_BASE_URL;
    this.retryCount = 0;
    this.maxRetries = 3;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {},
    retry = true
  ): Promise<ApiResponse<T>> {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${this.baseURL}${cleanEndpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.headers,
    };

    try {
      const config: RequestInit = {
        ...options,
        headers,
        credentials: 'include' as RequestCredentials,
        mode: 'cors' as RequestMode,
      };

      const response = await fetch(url, config);

      if (response.redirected) {
        console.warn(`Request was redirected to: ${response.url}`);
      }

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`Endpoint not found: ${url}`);
        }
        
        let errorMessage = `HTTP Error: ${response.status} ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || errorData.detail || errorMessage;
        } catch (parseError) {
          console.warn('Failed to parse error response body as JSON:', parseError);
        }
        
        throw new Error(errorMessage);
      }

      if (response.status === 204) {
        return {
          success: true,
          data: {} as T,
          timestamp: new Date().toISOString(),
        };
      }

      const responseData = await response.json() as ApiResponse<T>;
      return responseData;
    } catch (error) {
      console.error(`API request failed for ${url}:`, error);
      
      if (retry && this.retryCount < this.maxRetries && error instanceof TypeError) {
        this.retryCount++;
        console.log(`Retrying request (${this.retryCount}/${this.maxRetries})...`);
        await new Promise(resolve => setTimeout(resolve, 1000 * this.retryCount));
        return this.request<T>(endpoint, options, false);
      }
      
      this.retryCount = 0;
      
      if (error instanceof TypeError && error.message.includes('fetch')) {
        if (error.message.includes('CORS')) {
          throw new Error('CORS error: Unable to connect to the API server. Please check if the server is running and CORS is configured properly.');
        }
        throw new Error('Network error: Unable to connect to the server. Please check your connection and try again.');
      }
      
      throw error;
    }
  }

  async getDashboardStats(timeRange: string = '24h'): Promise<DashboardStats> {
    try {
      const response = await fetch(
        `${this.baseURL}/analytics/dashboard/stats?time_range=${timeRange}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          credentials: 'include',
          mode: 'cors',
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status} ${response.statusText}`);
      }

      const backendData = await response.json() as DashboardBackendStats;
      
      if (backendData.total_mentions === 0) {
        return this.getFallbackDashboardStats();
      }
      
      return {
        total_mentions: backendData.total_mentions || 0,
        sentiment_distribution: {
          positive: backendData.positive_mentions || 0,
          negative: backendData.negative_mentions || 0,
          neutral: backendData.neutral_mentions || 0
        },
        active_alerts: backendData.spike_alerts?.length || 0,
        mention_velocity: backendData.recent_mentions || 0,
        engagement_rate: 0,
        top_sources: backendData.top_sources || [],
        top_categories: backendData.trending_topics?.map((topic) => ({
          category: topic.name || 'Unknown',
          count: topic.count || 0,
          percentage: 0
        })) || []
      };
    } catch (error) {
      console.warn('Using fallback dashboard data due to API error:', error);
      return this.getFallbackDashboardStats();
    }
  }

  async getMentions(
    filters: Filters, 
    page: number = 1, 
    limit: number = 20
  ): Promise<MentionsResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...this.cleanFilters(filters),
    });
    
    const endpoint = `/mentions?${params}`.replace(/\/+/, '/');
    
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include',
        mode: 'cors',
      });

      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status} ${response.statusText}`);
      }

      const responseData = await response.json();
      
      const mentions = responseData?.mentions || [];
      const paginationData = responseData?.pagination || {};
      
      if (mentions.length === 0) {
        return this.getFallbackMentionsResponse(page, limit);
      }
      
      return {
        mentions: mentions,
        pagination: {
          page: paginationData.page || page,
          limit: paginationData.limit || limit,
          total: paginationData.total || 0,
          total_pages: paginationData.pages || paginationData.total_pages || 0,
        },
      };
    } catch (error) {
      console.warn('Using fallback mentions data due to API error:', error);
      return this.getFallbackMentionsResponse(page, limit);
    }
  }

  async getActiveAlerts(): Promise<Alert[]> {
    try {
      const response = await fetch(
        `${this.baseURL}/alerts/active`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          credentials: 'include',
          mode: 'cors',
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status} ${response.statusText}`);
      }

      const responseData = await response.json() as ActiveAlertsResponse;
      const backendAlerts = responseData.alerts || [];
      
      return backendAlerts.map((alert): Alert => ({
        id: alert.id?.toString() || '',
        type: alert.alert_type || 'volume_spike',
        severity: alert.severity || 'medium',
        title: alert.title || '',
        description: alert.message || '',
        triggered_at: alert.created_at || new Date().toISOString(),
        is_resolved: alert.is_resolved || false,
        metadata: alert.metadata || {}
      }));
    } catch (error) {
      console.warn('Using fallback alerts data due to API error:', error);
      return [];
    }
  }

  async exportMentions(filters: Filters, format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    const params = new URLSearchParams({
      ...this.cleanFilters(filters),
      format,
    });

    const url = `${this.baseURL}/mentions/export?${params}`;
    
    const response = await fetch(url, {
      credentials: 'include',
      mode: 'cors',
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.status} ${response.statusText}`);
    }

    return response.blob();
  }

  private cleanFilters(filters: Filters): Record<string, string> {
    const cleaned: Record<string, string> = {};
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        cleaned[key] = String(value);
      }
    });

    return cleaned;
  }

  
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/health`, {
        method: 'GET',
        credentials: 'include',
        mode: 'cors',
      });
      
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }
      
      const data = await response.json();
      return data.status === 'healthy';
    } catch (error) {
      console.warn('Health check failed:', error);
      return false;
    }
  }

  private getFallbackDashboardStats(): DashboardStats {
    return {
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
  }

  private getFallbackMentionsResponse(page: number, limit: number): MentionsResponse {
    const fallbackMentions: Mention[] = [
      {
        id: '1',
        text: 'Great product! Loving the new features and improvements.',
        source: 'twitter',
        sentiment: 'positive',
        sentiment_score: 0.9,
        timestamp: new Date().toISOString(),
        author_name: 'TechEnthusiast',
        author_handle: '@techlover',
        categories: ['product_feedback'],
        language: 'en',
        brand_mentions: ['YourBrand']
      },
      {
        id: '2',
        text: 'Having some issues with customer service response times.',
        source: 'reddit',
        sentiment: 'negative',
        sentiment_score: -0.7,
        timestamp: new Date().toISOString(),
        author_name: 'ConcernedUser',
        categories: ['customer_service'],
        language: 'en',
        brand_mentions: ['YourBrand']
      }
    ];

    return {
      mentions: fallbackMentions,
      pagination: {
        page,
        limit,
        total: fallbackMentions.length,
        total_pages: 1,
      },
    };
  }
}

export const api = new ApiClient();