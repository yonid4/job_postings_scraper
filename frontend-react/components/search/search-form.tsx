"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Slider } from "@/components/ui/slider"
import { Button } from "@/components/ui/button"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Badge } from "@/components/ui/badge"
import { Search, Filter, ChevronDown, X } from "lucide-react"
import type { SearchFilters } from "@/app/search/page"

interface SearchFormProps {
  filters: SearchFilters
  onFiltersChange: (filters: SearchFilters) => void
  isSearching: boolean
}

export function SearchForm({ filters, onFiltersChange, isSearching }: SearchFormProps) {
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)

  const updateFilter = (key: keyof SearchFilters, value: any) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  const handleCheckboxChange = (key: keyof SearchFilters, value: string, checked: boolean) => {
    const currentValues = filters[key] as string[]
    if (checked) {
      updateFilter(key, [...currentValues, value])
    } else {
      updateFilter(
        key,
        currentValues.filter((v) => v !== value),
      )
    }
  }

  const clearFilters = () => {
    onFiltersChange({
      ...filters,
      location: "",
      distance: "25",
      workArrangement: [],
      experienceLevel: [],
      jobType: [],
      datePosted: "any",
      qualificationThreshold: 70,
      jobLimit: 25,
      additionalKeywords: "",
    })
  }

  const getActiveFiltersCount = () => {
    let count = 0
    if (filters.location) count++
    if (filters.workArrangement.length > 0) count++
    if (filters.experienceLevel.length > 0) count++
    if (filters.jobType.length > 0) count++
    if (filters.datePosted !== "any") count++
    if (filters.qualificationThreshold !== 70) count++
    if (filters.jobLimit !== 25) count++
    if (filters.additionalKeywords) count++
    return count
  }

  return (
    <div className="space-y-6">
      {/* Main Search Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Job Search
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="website">Job Website</Label>
            <Select value={filters.website} onValueChange={(value) => updateFilter("website", value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="linkedin">LinkedIn</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">Currently supporting LinkedIn. More job sites coming soon!</p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="keywords">Job Title/Keywords *</Label>
              <Input
                id="keywords"
                placeholder="e.g., Software Engineer, Data Scientist"
                value={filters.keywords}
                onChange={(e) => updateFilter("keywords", e.target.value)}
                disabled={isSearching}
              />
              <p className="text-sm text-muted-foreground">Enter job titles, skills, or keywords you're looking for</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="location">Location *</Label>
              <Input
                id="location"
                placeholder="e.g., San Francisco, CA, Remote"
                value={filters.location}
                onChange={(e) => updateFilter("location", e.target.value)}
                disabled={isSearching}
              />
              <p className="text-sm text-muted-foreground">Enter city, state, or "Remote"</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Advanced Filters */}
      <Card>
        <Collapsible open={showAdvancedFilters} onOpenChange={setShowAdvancedFilters}>
          <CollapsibleTrigger asChild>
            <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Filter className="h-5 w-5" />
                  Advanced Filters
                  {getActiveFiltersCount() > 0 && (
                    <Badge variant="secondary" className="ml-2">
                      {getActiveFiltersCount()}
                    </Badge>
                  )}
                </div>
                <ChevronDown className={`h-4 w-4 transition-transform ${showAdvancedFilters ? "rotate-180" : ""}`} />
              </CardTitle>
            </CardHeader>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Distance from Location</Label>
                  <Select value={filters.distance} onValueChange={(value) => updateFilter("distance", value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="exact">Exact location only</SelectItem>
                      <SelectItem value="5">Within 5 miles</SelectItem>
                      <SelectItem value="10">Within 10 miles</SelectItem>
                      <SelectItem value="25">Within 25 miles</SelectItem>
                      <SelectItem value="50">Within 50 miles</SelectItem>
                      <SelectItem value="100">Within 100 miles</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Date Posted</Label>
                  <Select value={filters.datePosted} onValueChange={(value) => updateFilter("datePosted", value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="any">Any time</SelectItem>
                      <SelectItem value="1">Past 24 hours</SelectItem>
                      <SelectItem value="7">Past week</SelectItem>
                      <SelectItem value="30">Past month</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <Label className="text-base font-medium">Work Arrangement</Label>
                  <div className="grid grid-cols-3 gap-4 mt-2">
                    {[
                      { value: "on-site", label: "On-Site" },
                      { value: "remote", label: "Remote" },
                      { value: "hybrid", label: "Hybrid" },
                    ].map((option) => (
                      <div key={option.value} className="flex items-center space-x-2">
                        <Checkbox
                          id={`work-${option.value}`}
                          checked={filters.workArrangement.includes(option.value)}
                          onCheckedChange={(checked) =>
                            handleCheckboxChange("workArrangement", option.value, checked as boolean)
                          }
                        />
                        <Label htmlFor={`work-${option.value}`} className="text-sm font-normal">
                          {option.label}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <Label className="text-base font-medium">Experience Level</Label>
                  <div className="grid grid-cols-3 gap-4 mt-2">
                    {[
                      { value: "entry", label: "Entry Level" },
                      { value: "associate", label: "Associate" },
                      { value: "mid", label: "Mid Level" },
                      { value: "senior", label: "Senior" },
                      { value: "director", label: "Director" },
                      { value: "executive", label: "Executive" },
                    ].map((option) => (
                      <div key={option.value} className="flex items-center space-x-2">
                        <Checkbox
                          id={`exp-${option.value}`}
                          checked={filters.experienceLevel.includes(option.value)}
                          onCheckedChange={(checked) =>
                            handleCheckboxChange("experienceLevel", option.value, checked as boolean)
                          }
                        />
                        <Label htmlFor={`exp-${option.value}`} className="text-sm font-normal">
                          {option.label}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <Label className="text-base font-medium">Job Type</Label>
                  <div className="grid grid-cols-3 gap-4 mt-2">
                    {[
                      { value: "full-time", label: "Full-time" },
                      { value: "part-time", label: "Part-time" },
                      { value: "contract", label: "Contract" },
                      { value: "temporary", label: "Temporary" },
                      { value: "internship", label: "Internship" },
                    ].map((option) => (
                      <div key={option.value} className="flex items-center space-x-2">
                        <Checkbox
                          id={`job-${option.value}`}
                          checked={filters.jobType.includes(option.value)}
                          onCheckedChange={(checked) =>
                            handleCheckboxChange("jobType", option.value, checked as boolean)
                          }
                        />
                        <Label htmlFor={`job-${option.value}`} className="text-sm font-normal">
                          {option.label}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-3">
                  <Label>Qualification Threshold: {filters.qualificationThreshold}%</Label>
                  <Slider
                    value={[filters.qualificationThreshold]}
                    onValueChange={(value) => updateFilter("qualificationThreshold", value[0])}
                    max={100}
                    min={0}
                    step={5}
                    className="w-full"
                  />
                  <p className="text-sm text-muted-foreground">
                    Only show jobs with qualification score above this threshold
                  </p>
                </div>

                <div className="space-y-3">
                  <Label>Job Limit: {filters.jobLimit} jobs</Label>
                  <Slider
                    value={[filters.jobLimit]}
                    onValueChange={(value) => updateFilter("jobLimit", value[0])}
                    max={100}
                    min={1}
                    step={1}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>1 job</span>
                    <span>50 jobs</span>
                    <span>100 jobs</span>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="additionalKeywords">Additional Keywords</Label>
                <Input
                  id="additionalKeywords"
                  placeholder="e.g., python, react, aws, docker"
                  value={filters.additionalKeywords}
                  onChange={(e) => updateFilter("additionalKeywords", e.target.value)}
                />
                <p className="text-sm text-muted-foreground">Add keywords to narrow down your search</p>
              </div>

              <div className="flex justify-end">
                <Button variant="outline" size="sm" onClick={clearFilters}>
                  <X className="w-4 h-4 mr-2" />
                  Clear Filters
                </Button>
              </div>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>
    </div>
  )
}
