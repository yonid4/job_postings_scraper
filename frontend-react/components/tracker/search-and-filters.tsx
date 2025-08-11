"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import { Search, X, Filter } from "lucide-react"

interface SearchAndFiltersProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  activeFilter: string
  onFilterChange: (filter: string) => void
  scoreThreshold: number
  onScoreThresholdChange: (threshold: number) => void
  totalJobs: number
  filteredCount: number
}

export function SearchAndFilters({
  searchQuery,
  onSearchChange,
  activeFilter,
  onFilterChange,
  scoreThreshold,
  onScoreThresholdChange,
  totalJobs,
  filteredCount,
}: SearchAndFiltersProps) {
  const filters = [
    { id: "all", label: "All Jobs", count: totalJobs },
    { id: "applied", label: "Applied" },
    { id: "favorites", label: "Favorites" },
    { id: "this_week", label: "This Week" },
    { id: "high_score", label: "High Score (80+)" },
  ]

  const clearSearch = () => {
    onSearchChange("")
  }

  const clearAllFilters = () => {
    onSearchChange("")
    onFilterChange("all")
    onScoreThresholdChange(70)
  }

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Search Bar */}
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search jobs, companies, locations..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                className="pl-10 pr-10"
              />
              {searchQuery && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearSearch}
                  className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>

          {/* Quick Filters */}
          <div className="flex flex-wrap gap-2">
            {filters.map((filter) => (
              <Button
                key={filter.id}
                variant={activeFilter === filter.id ? "default" : "outline"}
                size="sm"
                onClick={() => onFilterChange(filter.id)}
                className="text-sm"
              >
                {filter.label}
                {filter.count !== undefined && ` (${filter.count})`}
              </Button>
            ))}
          </div>

          {/* Score Threshold */}
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Label className="text-sm font-medium">AI Score Threshold: {scoreThreshold}%</Label>
              <Slider
                value={[scoreThreshold]}
                onValueChange={(value) => onScoreThresholdChange(value[0])}
                max={100}
                min={0}
                step={5}
                className="mt-2"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={clearAllFilters}>
              <Filter className="w-4 h-4 mr-2" />
              Clear All
            </Button>
          </div>

          {/* Results Count */}
          <div className="flex justify-between items-center text-sm text-muted-foreground">
            <span>{filteredCount === totalJobs ? `${totalJobs} jobs` : `${filteredCount} of ${totalJobs} jobs`}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
