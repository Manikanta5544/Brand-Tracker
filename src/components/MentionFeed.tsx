import { useState } from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Avatar, AvatarFallback } from './ui/avatar';
import { ThumbsUp, ThumbsDown, Minus, ExternalLink } from 'lucide-react';
import { cn } from '../lib/utils';
import type { MentionFeedProps } from './types';

interface LocalMention {
  id: number;
  text: string;
  source: string;
  author: string;
  sentiment: string;
  timestamp: string;
  url?: string;
  category?: string;
}

export function MentionFeed({ mentions: propMentions, loading = false, showPagination = false, pagination, onPageChange }: MentionFeedProps) {
  const mockMentions: LocalMention[] = [
    {
      id: 1,
      text: "Just tried this brand and I'm impressed! The quality is outstanding and customer service was excellent.",
      source: 'reddit',
      author: 'user_123',
      sentiment: 'positive',
      timestamp: '2024-01-15T10:55:00.000Z', 
      category: 'Praise'
    },
    {
      id: 2,
      text: "Has anyone else had issues with their customer support? Been waiting for a response for days.",
      source: 'twitter',
      author: '@tech_user',
      sentiment: 'negative',
      timestamp: '2024-01-15T10:45:00.000Z',
      category: 'Complaint'
    },
    {
      id: 3,
      text: "The new product features are exactly what we needed. Great update!",
      source: 'twitter',
      author: '@happy_customer',
      sentiment: 'positive',
      timestamp: '2024-01-15T10:30:00.000Z', 
      category: 'Feedback'
    },
    {
      id: 4,
      text: "Not sure how I feel about the recent changes. Some things are better, others worse.",
      source: 'reddit',
      author: 'neutral_user',
      sentiment: 'neutral',
      timestamp: '2024-01-15T10:15:00.000Z', 
      category: 'Review'
    }
  ];

  const [mentions] = useState<LocalMention[]>(() => {
    if (propMentions && Array.isArray(propMentions) && propMentions.length > 0) {
      return propMentions as unknown as LocalMention[];
    }
    return mockMentions;
  });

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return <ThumbsUp className="h-4 w-4 text-green-500" />;
      case 'negative':
        return <ThumbsDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-slate-500" />;
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      case 'negative':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
      default:
        return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'reddit':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300';
      case 'twitter':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
      case 'news':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300';
      default:
        return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Card key={i} className="p-4 animate-pulse">
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-3/4 mb-2" />
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/2" />
          </Card>
        ))}
      </div>
    );
  }

  if (mentions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No mentions found matching your filters.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {mentions.map((mention) => (
        <Card key={mention.id} className="p-4 hover:shadow-md transition-shadow">
          <div className="flex gap-3">
            <Avatar className="h-10 w-10">
              <AvatarFallback className="bg-linear-to-br from-blue-500 to-purple-500 text-white">
                {mention.author?.charAt(0).toUpperCase() || 'U'}
              </AvatarFallback>
            </Avatar>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <span className="font-medium text-sm">{mention.author || 'Unknown'}</span>
                <Badge variant="outline" className={cn("text-xs", getSourceColor(mention.source))}>
                  {mention.source}
                </Badge>
                <Badge variant="outline" className={cn("text-xs", getSentimentColor(mention.sentiment))}>
                  <span className="flex items-center gap-1">
                    {getSentimentIcon(mention.sentiment)}
                    {mention.sentiment}
                  </span>
                </Badge>
                {mention.category && (
                  <Badge variant="outline" className="text-xs">
                    {mention.category}
                  </Badge>
                )}
                <span className="text-xs text-muted-foreground ml-auto">
                  {formatTimestamp(mention.timestamp)}
                </span>
              </div>
              
              <p className="text-sm text-foreground leading-relaxed mb-2">
                {mention.text}
              </p>
              
              {mention.url && (
                <a 
                  href={mention.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                >
                  View original <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          </div>
        </Card>
      ))}
      
      {showPagination && pagination && onPageChange && pagination.total_pages > 1 && (
        <div className="flex justify-center items-center gap-2 mt-4">
          <button
            onClick={() => onPageChange(pagination.page - 1)}
            disabled={pagination.page <= 1}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-muted-foreground">
            Page {pagination.page} of {pagination.total_pages}
          </span>
          <button
            onClick={() => onPageChange(pagination.page + 1)}
            disabled={pagination.page >= pagination.total_pages}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}