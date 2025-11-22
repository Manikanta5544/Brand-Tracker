import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Search, Filter, X } from 'lucide-react';
import { Card } from './ui/card';
import type { FiltersProps } from './types';

export function Filters({ filters, setFilters }: FiltersProps) {
  const clearFilters = () => {
    setFilters({
      source: '',
      sentiment: '',
      date_range: '24h',
      search: ''
    });
  };

  const hasActiveFilters = filters.source || filters.sentiment || filters.search;

  const handleSelectChange = (key: keyof typeof filters, value: string) => {
    const safeValue = value && value.trim() !== '' ? value : '';
    setFilters({ ...filters, [key]: safeValue });
  };

  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-3">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <h3 className="font-semibold text-sm">Filters</h3>
        {hasActiveFilters && (
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={clearFilters}
            className="ml-auto h-7 text-xs"
          >
            <X className="h-3 w-3 mr-1" />
            Clear
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search mentions..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="pl-9"
          />
        </div>

        <Select 
          value={filters.source || "all-sources"} 
          onValueChange={(value: string) => handleSelectChange('source', value === "all-sources" ? '' : value)}
        >
          <SelectTrigger>
            <SelectValue placeholder="All Sources" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-sources">All Sources</SelectItem>
            <SelectItem value="reddit">Reddit</SelectItem>
            <SelectItem value="twitter">Twitter</SelectItem>
            <SelectItem value="news">News</SelectItem>
            <SelectItem value="youtube">YouTube</SelectItem>
          </SelectContent>
        </Select>

        <Select 
          value={filters.sentiment || "all-sentiments"} 
          onValueChange={(value: string) => handleSelectChange('sentiment', value === "all-sentiments" ? '' : value)}
        >
          <SelectTrigger>
            <SelectValue placeholder="All Sentiments" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-sentiments">All Sentiments</SelectItem>
            <SelectItem value="positive">Positive</SelectItem>
            <SelectItem value="neutral">Neutral</SelectItem>
            <SelectItem value="negative">Negative</SelectItem>
          </SelectContent>
        </Select>

        <Select 
          value={filters.date_range} 
          onValueChange={(value: string) => handleSelectChange('date_range', value)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Time Range" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1h">Last Hour</SelectItem>
            <SelectItem value="24h">Last 24 Hours</SelectItem>
            <SelectItem value="7d">Last 7 Days</SelectItem>
            <SelectItem value="30d">Last 30 Days</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </Card>
  );
}