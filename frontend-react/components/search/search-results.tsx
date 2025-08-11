"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { BarChart3, Eye, Save, SaveAll, ExternalLink } from "lucide-react"
import { getScoreColor } from "@/lib/utils"
import type { JobResult } from "@/app/search/page"

interface SearchResultsProps {
  results: JobResult[]
  stats: {
    total: number
    qualified: number
    excellent: number
    avgScore: number
  } | null
  isLoading: boolean
  onJobSelect: (job: JobResult) => void
  onSaveJob: (jobId: string) => Promise<void>
  onSaveAllJobs: () => Promise<void>
}

export function SearchResults({
  results,
  stats,
  isLoading,
  onJobSelect,
  onSaveJob,
  onSaveAllJobs,
}: SearchResultsProps) {
  const [savingJobs, setSavingJobs] = useState<Set<string>>(new Set())
  const [savingAll, setSavingAll] = useState(false)

  const handleSaveJob = async (jobId: string) => {
    setSavingJobs((prev) => new Set(prev).add(jobId))
    try {
      await onSaveJob(jobId)
    } finally {
      setSavingJobs((prev) => {
        const newSet = new Set(prev)
        newSet.delete(jobId)
        return newSet
      })
    }
  }

  const handleSaveAll = async () => {
    setSavingAll(true)
    try {
      await onSaveAllJobs()
    } finally {
      setSavingAll(false)
    }
  }

  if (isLoading) {
    return <SearchResultsSkeleton />
  }

  if (results.length === 0) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* Results Summary */}
      {stats && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Analysis Results
            </CardTitle>
            <Button onClick={handleSaveAll} disabled={savingAll} variant="outline">
              {savingAll ? (
                <>
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                  Saving...
                </>
              ) : (
                <>
                  <SaveAll className="w-4 h-4 mr-2" />
                  Save All ({stats.total})
                </>
              )}
            </Button>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-primary">{stats.total}</div>
                <div className="text-sm text-muted-foreground">Total Jobs</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-green-600">{stats.qualified}</div>
                <div className="text-sm text-muted-foreground">Qualified (60+)</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-green-600">{stats.excellent}</div>
                <div className="text-sm text-muted-foreground">Excellent (80+)</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-primary">{stats.avgScore}</div>
                <div className="text-sm text-muted-foreground">Avg Score</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Job Results */}
      <div className="space-y-4">
        {results.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            onSelect={() => onJobSelect(job)}
            onSave={() => handleSaveJob(job.id)}
            isSaving={savingJobs.has(job.id)}
          />
        ))}
      </div>
    </div>
  )
}

function JobCard({
  job,
  onSelect,
  onSave,
  isSaving,
}: {
  job: JobResult
  onSelect: () => void
  onSave: () => void
  isSaving: boolean
}) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="pt-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h3 className="font-semibold text-lg mb-1">
              <button onClick={onSelect} className="text-left hover:text-primary transition-colors">
                {job.job_title}
              </button>
            </h3>
            <p className="text-muted-foreground mb-1">{job.company}</p>
            <p className="text-sm text-muted-foreground">{job.location}</p>
          </div>
          <div className="text-right">
            <Badge className={`${getScoreColor(job.score)} border text-sm px-3 py-1`}>{job.score}/100</Badge>
            <div className="text-xs text-muted-foreground mt-1">
              {job.score >= 80 ? "Excellent Match" : job.score >= 60 ? "Good Match" : "Fair Match"}
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4 mb-4">
          {job.strengths && job.strengths.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-green-700 mb-1">Strengths</h4>
              <p className="text-sm text-muted-foreground">{job.strengths.slice(0, 2).join(", ")}</p>
            </div>
          )}
          {job.concerns && job.concerns.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-amber-700 mb-1">Concerns</h4>
              <p className="text-sm text-muted-foreground">{job.concerns.slice(0, 2).join(", ")}</p>
            </div>
          )}
        </div>

        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onSelect}>
            <Eye className="w-4 h-4 mr-2" />
            View Details
          </Button>
          <Button variant="outline" size="sm" onClick={onSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save Job
              </>
            )}
          </Button>
          <Button variant="outline" size="sm" asChild>
            <a href={job.job_url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="w-4 h-4 mr-2" />
              View on LinkedIn
            </a>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function SearchResultsSkeleton() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="text-center p-4 border rounded-lg">
                <Skeleton className="h-8 w-12 mx-auto mb-2" />
                <Skeleton className="h-4 w-16 mx-auto" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <Skeleton className="h-6 w-64 mb-2" />
                  <Skeleton className="h-4 w-32 mb-1" />
                  <Skeleton className="h-4 w-24" />
                </div>
                <Skeleton className="h-6 w-16" />
              </div>
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
              <div className="flex gap-2">
                <Skeleton className="h-8 w-24" />
                <Skeleton className="h-8 w-20" />
                <Skeleton className="h-8 w-32" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
