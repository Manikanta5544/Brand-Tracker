import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { TrendGraphProps } from './types';

interface DataPoint {
  time: string;
  positive: number;
  neutral: number;
  negative: number;
  total: number;
}

const LOADING_HEIGHTS = [45, 75, 30, 90, 60, 25, 80, 50, 35, 85, 40, 70];

const generateMockData = (hours: number, interval: number, timeRange: string): DataPoint[] => {
  const data: DataPoint[] = [];
  for (let i = 0; i < hours; i += interval) {
    const baseValue = i * 3;
    const positive = (baseValue % 30) + 40;
    const neutral = (baseValue % 20) + 10;
    const negative = (baseValue % 15) + 5;
    
    data.push({
      time: timeRange === '7d' ? `Day ${Math.floor(i/24) + 1}` : `${i}:00`,
      positive,
      neutral,
      negative,
      total: positive + neutral + negative
    });
  }
  
  return data;
};

export function TrendGraph({ stats, loading = false, timeRange = '24h' }: TrendGraphProps) {
  if (loading || !stats) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center bg-muted/20 rounded-lg">
        <div className="w-full max-w-md">
          <div className="flex items-end justify-between h-32 gap-1">
            {LOADING_HEIGHTS.map((height, i) => (
              <div
                key={i}
                className="flex-1 bg-muted rounded-t animate-pulse"
                style={{ height: `${height}%` }}
              />
            ))}
          </div>
          <p className="text-center mt-4 text-muted-foreground">Loading trend data...</p>
        </div>
      </div>
    );
  }
  
  const hours = timeRange === '7d' ? 168 : 24;
  const interval = timeRange === '7d' ? 6 : 1;
  
  const data = generateMockData(hours, interval, timeRange);

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-800" />
          <XAxis 
            dataKey="time" 
            className="text-xs"
            tick={{ fill: 'currentColor' }}
          />
          <YAxis 
            className="text-xs"
            tick={{ fill: 'currentColor' }}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'hsl(var(--background))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '6px'
            }}
          />
          <Legend />
          <Area 
            type="monotone" 
            dataKey="positive" 
            stackId="1"
            stroke="#10b981" 
            fill="#10b981"
            fillOpacity={0.6}
          />
          <Area 
            type="monotone" 
            dataKey="neutral" 
            stackId="1"
            stroke="#64748b" 
            fill="#64748b"
            fillOpacity={0.6}
          />
          <Area 
            type="monotone" 
            dataKey="negative" 
            stackId="1"
            stroke="#ef4444" 
            fill="#ef4444"
            fillOpacity={0.6}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}