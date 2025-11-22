import type { SourceBreakdownProps } from './types';

export function SourceBreakdown({ stats, loading = false, showEngagement = false }: SourceBreakdownProps) {
  if (loading || !stats) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center justify-between animate-pulse">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-muted rounded-full"></div>
              <div className="h-4 bg-muted rounded w-16"></div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-24 h-2 bg-muted rounded-full"></div>
              <div className="h-4 bg-muted rounded w-8"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {stats.top_sources.map((source) => (
        <div key={source.source} className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div 
              className={`w-3 h-3 rounded-full ${
                source.source === 'twitter' ? 'bg-blue-500' :
                source.source === 'reddit' ? 'bg-orange-500' :
                source.source === 'news' ? 'bg-green-500' :
                source.source === 'review' ? 'bg-purple-500' : 'bg-gray-500'
              }`} 
            />
            <span className="text-sm capitalize">{source.source}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
              <div 
                className={`h-full ${
                  source.source === 'twitter' ? 'bg-blue-500' :
                  source.source === 'reddit' ? 'bg-orange-500' :
                  source.source === 'news' ? 'bg-green-500' :
                  source.source === 'review' ? 'bg-purple-500' : 'bg-gray-500'
                }`}
                style={{ width: `${source.percentage}%` }}
              />
            </div>
            <span className="text-sm font-medium w-8 text-right">
              {showEngagement ? source.count : `${source.percentage}%`}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}