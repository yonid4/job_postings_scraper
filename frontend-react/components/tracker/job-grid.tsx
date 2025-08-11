"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Heart, MapPin, DollarSign, Calendar, ExternalLink, Eye, CheckCircle } from "lucide-react"
import { getScoreColor } from "@/lib/utils"
import type { JobItem } from "@/app/tracker/page"

interface JobGridProps {
  jobs: JobItem[]
  isLoading: boolean
  onJobSelect: (job: JobItem) => void
  onToggleFavorite: (jobId: string) => void
  onMarkAsApplied: (jobId: string) => void
}

export function JobGrid({ jobs, isLoading, onJobSelect, onToggleFavorite, onMarkAsApplied }: JobGridProps) {
  const [favoriteLoading, setFavoriteLoading] = useState<Set<string>>(new Set())
  const [applyLoading, setApplyLoading] = useState<Set<string>>(new Set())

  if (isLoading) {
    return <JobGridSkeleton />
  }

  if (jobs.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <div className="text-center">
            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
              <Eye className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No jobs found</h3>
            <p className="text-muted-foreground mb-4">Try adjusting your filters or search for new opportunities.</p>
            <Button asChild>
              <a href="/search">Search for Jobs</a>
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  const handleToggleFavorite = async (jobId: string) => {
    setFavoriteLoading((prev) => new Set(prev).add(jobId))
    try {
      await onToggleFavorite(jobId)
    } finally {
      setFavoriteLoading((prev) => {
        const newSet = new Set(prev)
        newSet.delete(jobId)
        return newSet
      })
    }
  }

  const handleMarkAsApplied = async (jobId: string) => {
    setApplyLoading((prev) => new Set(prev).add(jobId))
    try {
      await onMarkAsApplied(jobId)
    } finally {
      setApplyLoading((prev) => {
        const newSet = new Set(prev)
        newSet.delete(jobId)
        return newSet
      })
    }
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {jobs.map((jobItem) => (
        <JobCard
          key={jobItem.id}
          job={jobItem}
          onSelect={() => onJobSelect(jobItem)}
          onToggleFavorite={() => handleToggleFavorite(jobItem.id)}
          onMarkAsApplied={() => handleMarkAsApplied(jobItem.id)}
          isFavoriteLoading={favoriteLoading.has(jobItem.id)}
          isApplyLoading={applyLoading.has(jobItem.id)}
        />
      ))}
    </div>
  )
}

function JobCard({
  job,
  onSelect,
  onToggleFavorite,
  onMarkAsApplied,
  isFavoriteLoading,
  isApplyLoading,
}: {
  job: JobItem
  onSelect: () => void
  onToggleFavorite: () => void
  onMarkAsApplied: () => void
  isFavoriteLoading: boolean
  isApplyLoading: boolean
}) {
  const jobData = job.job
  const jobTitle = jobData.title || jobData.job_title || "Unknown Title"
  const companyName = jobData.company || jobData.company_name || "Unknown Company"
  const jobScore = getJobScore(jobData)
  const dateFound = jobData.date_found ? new Date(jobData.date_found).toLocaleDateString() : "Unknown"

  const getStatusBadge = () => {
    if (job.application_status === "interview") {
      return <Badge className="bg-blue-100 text-blue-800">Interview</Badge>
    }
    if (job.application_status === "offer") {
      return <Badge className="bg-green-100 text-green-800">Offer</Badge>
    }
    if (job.application_status === "rejected") {
      return <Badge className="bg-red-100 text-red-800">Rejected</Badge>
    }
    if (job.has_applied) {
      return <Badge className="bg-green-100 text-green-800">Applied</Badge>
    }
    return <Badge variant="secondary">Not Applied</Badge>
  }

  return (
    <Card className="hover:shadow-md transition-all duration-200 cursor-pointer group" onClick={onSelect}>
      <CardContent className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h3 className="font-semibold text-lg mb-1 group-hover:text-primary transition-colors">{jobTitle}</h3>
            <p className="text-muted-foreground mb-2">{companyName}</p>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                <span>{jobData.location || "Remote"}</span>
              </div>
              {(jobData.salary || jobData.salary_range) && (
                <div className="flex items-center gap-1">
                  <DollarSign className="w-4 h-4" />
                  <span>{jobData.salary || jobData.salary_range}</span>
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {jobScore && <Badge className={`${getScoreColor(jobScore)} border`}>{jobScore}%</Badge>}
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                onToggleFavorite()
              }}
              disabled={isFavoriteLoading}
              className="p-1 h-8 w-8"
            >
              <Heart
                className={`w-4 h-4 ${
                  job.is_favorited ? "fill-red-500 text-red-500" : "text-muted-foreground"
                } ${isFavoriteLoading ? "animate-pulse" : ""}`}
              />
            </Button>
          </div>
        </div>

        {jobData.description && (
          <p className="text-sm text-muted-foreground mb-4 line-clamp-3">
            {jobData.description.substring(0, 150)}
            {jobData.description.length > 150 ? "..." : ""}
          </p>
        )}

        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            {getStatusBadge()}
            {job.priority && <Badge variant="outline">{job.priority}</Badge>}
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Calendar className="w-3 h-3" />
            <span>{dateFound}</span>
          </div>
        </div>

        {job.notes && (
          <div className="mb-4 p-3 bg-muted/50 rounded-md">
            <p className="text-sm text-muted-foreground">{job.notes}</p>
          </div>
        )}

        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onSelect}>
            <Eye className="w-4 h-4 mr-2" />
            Details
          </Button>
          {jobData.linkedin_url && (
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                window.open(jobData.linkedin_url, "_blank")
              }}
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              View Job
            </Button>
          )}
          {!job.has_applied && (
            <Button
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                onMarkAsApplied()
              }}
              disabled={isApplyLoading}
            >
              {isApplyLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  Applying...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Mark Applied
                </>
              )}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function JobGridSkeleton() {
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <Card key={index}>
          <CardContent className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="flex-1">
                <Skeleton className="h-6 w-48 mb-2" />
                <Skeleton className="h-4 w-32 mb-2" />
                <div className="flex gap-4">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-20" />
                </div>
              </div>
              <div className="flex gap-2">
                <Skeleton className="h-6 w-12" />
                <Skeleton className="h-8 w-8 rounded-full" />
              </div>
            </div>
            <Skeleton className="h-16 w-full mb-4" />
            <div className="flex justify-between items-center mb-4">
              <div className="flex gap-2">
                <Skeleton className="h-6 w-16" />
                <Skeleton className="h-6 w-12" />
              </div>
              <Skeleton className="h-4 w-20" />
            </div>
            <div className="flex gap-2">
              <Skeleton className="h-8 w-20" />
              <Skeleton className="h-8 w-24" />
              <Skeleton className="h-8 w-28" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// Helper function to get job score
function getJobScore(job: JobItem["job"]): number | null {
  let score =
    job.gemini_score || job.qualification_score || job.score || job.ai_score || job.match_score || job.suitability_score

  if (typeof score === "string") {
    const parsed = Number.parseFloat(score)
    score = isNaN(parsed) ? null : parsed
  }

  if (score && score <= 10) {
    score = score * 10 // Convert 7.5/10 to 75%
  }

  return score ? Math.round(score) : null
}
