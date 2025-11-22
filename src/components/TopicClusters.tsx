import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { TrendingUp, MessageSquare } from 'lucide-react';
import type { TopicClustersProps } from './types';

interface Topic {
  id: number;
  label: string;
  count: number;
  sentiment: string;
  keywords: string[];
  color: string;
}

export function TopicClusters({ mentions, loading = false }: TopicClustersProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="p-4 animate-pulse">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-muted rounded-full"></div>
                <div className="h-4 bg-muted rounded w-24"></div>
              </div>
              <div className="h-4 bg-muted rounded w-12"></div>
            </div>
            <div className="flex items-center gap-4 mb-3">
              <div className="h-3 bg-muted rounded w-16"></div>
              <div className="h-3 bg-muted rounded w-12"></div>
            </div>
            <div className="flex flex-wrap gap-1">
              {[...Array(3)].map((_, idx) => (
                <div key={idx} className="h-4 bg-muted rounded w-8"></div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    );
  }
  
  const topics = mentions.reduce((acc, mention) => {
    mention.categories.forEach(category => {
      acc[category] = (acc[category] || 0) + 1;
    });
    return acc;
  }, {} as Record<string, number>);

  const topicEntries = Object.entries(topics)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 6)
    .map(([label, count], index) => ({
      id: index + 1,
      label,
      count,
      sentiment: count > 10 ? 'positive' : 'neutral',
      keywords: [label, 'related', 'topic'],
      color: `bg-${['blue', 'purple', 'orange', 'green', 'pink', 'indigo'][index]}-500`
    }));

  if (topicEntries.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No topics detected in current mentions.
      </div>
    );
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'text-green-600 dark:text-green-400';
      case 'negative':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-slate-600 dark:text-slate-400';
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {topicEntries.map((topic) => (
        <Card key={topic.id} className="p-4 hover:shadow-lg transition-shadow">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${topic.color}`} />
              <h3 className="font-semibold">{topic.label}</h3>
            </div>
            <Badge variant="outline" className={getSentimentColor(topic.sentiment)}>
              {topic.sentiment}
            </Badge>
          </div>

          <div className="flex items-center gap-4 mb-3">
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <MessageSquare className="h-4 w-4" />
              <span>{topic.count} mentions</span>
            </div>
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <TrendingUp className="h-4 w-4" />
              <span>Trending</span>
            </div>
          </div>

          <div className="flex flex-wrap gap-1">
            {topic.keywords.map((keyword, idx) => (
              <Badge key={idx} variant="secondary" className="text-xs">
                {keyword}
              </Badge>
            ))}
          </div>
        </Card>
      ))}
    </div>
  );
}