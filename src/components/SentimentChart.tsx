import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import type { SentimentChartProps } from './types';

export function SentimentChart({ stats, loading = false }: SentimentChartProps) {
  if (loading || !stats) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center bg-muted/20 rounded-lg">
        <div className="text-center">
          <div className="w-32 h-32 bg-muted rounded-full mx-auto animate-pulse"></div>
          <p className="mt-4 text-muted-foreground">Loading sentiment data...</p>
        </div>
      </div>
    );
  }

  const data = [
    { name: 'Positive', value: stats.sentiment_distribution.positive, color: '#10b981' },
    { name: 'Neutral', value: stats.sentiment_distribution.neutral, color: '#64748b' },
    { name: 'Negative', value: stats.sentiment_distribution.negative, color: '#ef4444' }
  ];
  
  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}