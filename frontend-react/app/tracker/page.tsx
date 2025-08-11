"use client"

import { useState, useEffect, useMemo } from "react"
import { BaseLayout } from "@/components/base-layout"
import { AnalyticsCards } from "@/components/tracker/analytics-cards"
import { SearchAndFilters } from "@/components/tracker/search-and-filters"
import { JobGrid } from "@/components/tracker/job-grid"
import { JobDetailModal } from "@/components/tracker/job-detail-modal"
import { ExportModal } from "@/components/tracker/export-modal"
import { Button } from "@/components/ui/button"
import { RefreshCw, Download } from "lucide-react"
import { flashMessage } from "@/components/flash-message"

export interface JobItem {
  id: string
  job: {
    title?: string
    job_title?: string
    company?: string
    company_name?: string
    location?: string
    salary?: string
    salary_range?: string
    description?: string
    job_description?: string
    linkedin_url?: string
    date_found?: string
    gemini_score?: number
    qualification_score?: number
    score?: number
    ai_score?: number
    match_score?: number
    suitability_score?: number
    gemini_evaluation?: string
  }
  has_applied: boolean
  is_favorited: boolean
  notes?: string
  priority?: string
  source?: string
  date_applied?: string
  application_status?: "applied" | "interview" | "offer" | "rejected"
}

export interface AnalyticsData {
  total_jobs_tracked: number
  applications_submitted: number
  response_rate: number
  responses_received: number
  interviews_scheduled: number
  offers_received: number
  avg_qualification_score: number
  jobs_this_week: number
}

export default function TrackerPage() {
  const [jobs, setJobs] = useState<JobItem[]>([])
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [selectedJob, setSelectedJob] = useState<JobItem | null>(null)
  const [showExportModal, setShowExportModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [activeFilter, setActiveFilter] = useState("all")
  const [scoreThreshold, setScoreThreshold] = useState(70)

  // Load data on component mount
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setIsLoading(true)
    try {
      // First test basic API connectivity
      console.log("Testing API ping...")
      const pingResponse = await fetch("/api/debug/ping")
      if (pingResponse.ok) {
        const pingData = await pingResponse.json()
        console.log("Ping successful:", pingData)
      } else {
        console.warn("Ping failed:", pingResponse.status)
      }

      // Test the auth debug endpoint to check authentication and database connectivity
      console.log("Testing debug endpoint...")
      const debugResponse = await fetch("/api/debug/test")
      if (debugResponse.ok) {
        const debugData = await debugResponse.json()
        console.log("Debug endpoint response:", debugData)
      } else {
        console.warn("Debug endpoint failed:", debugResponse.status)
        const errorText = await debugResponse.text()
        console.error("Debug endpoint error:", errorText)
      }

      // Load jobs data from the backend
      console.log("Loading job tracker and analytics data...")
      const [jobsResponse, analyticsResponse] = await Promise.all([
        fetch("/api/jobs/tracker"),
        fetch("/api/jobs/analytics")
      ])

      console.log("Jobs response status:", jobsResponse.status)
      console.log("Analytics response status:", analyticsResponse.status)

      if (!jobsResponse.ok) {
        const errorText = await jobsResponse.text()
        console.error("Jobs endpoint error:", errorText)
        throw new Error(`Failed to load jobs: ${jobsResponse.status} - ${errorText}`)
      }
      if (!analyticsResponse.ok) {
        const errorText = await analyticsResponse.text()
        console.error("Analytics endpoint error:", errorText)
        throw new Error(`Failed to load analytics: ${analyticsResponse.status} - ${errorText}`)
      }

      const jobsData = await jobsResponse.json()
      const analyticsData = await analyticsResponse.json()
      
      console.log("Jobs data received:", jobsData)
      console.log("Analytics data received:", analyticsData)

      // Transform backend data to match frontend interface
      const transformedJobs: JobItem[] = jobsData.jobs?.map((item: any) => ({
        id: item.id || item.job_id,
        job: {
          job_title: item.job?.job_title || item.title,
          company_name: item.job?.company_name || item.company,
          location: item.job?.location || item.location,
          salary_range: item.job?.salary_range || item.salary,
          description: item.job?.job_description || item.description,
          linkedin_url: item.job?.linkedin_url || item.source,
          date_found: item.job?.date_found || item.date_created,
          gemini_score: item.job?.gemini_score || item.job?.ai_score || item.score,
          gemini_evaluation: item.job?.gemini_evaluation || item.evaluation,
        },
        has_applied: item.has_applied || false,
        is_favorited: item.is_favorited || false,
        notes: item.notes || "",
        priority: item.priority || "Medium",
        source: item.source || item.job?.linkedin_url,
        date_applied: item.date_applied,
        application_status: item.application_status,
      })) || []

      // Transform analytics data
      const transformedAnalytics: AnalyticsData = {
        total_jobs_tracked: analyticsData.total_jobs_tracked || transformedJobs.length,
        applications_submitted: analyticsData.applications_submitted || transformedJobs.filter(job => job.has_applied).length,
        response_rate: analyticsData.response_rate || 0,
        responses_received: analyticsData.responses_received || 0,
        interviews_scheduled: analyticsData.interviews_scheduled || 0,
        offers_received: analyticsData.offers_received || 0,
        avg_qualification_score: analyticsData.avg_qualification_score || 0,
        jobs_this_week: analyticsData.jobs_this_week || 0,
      }

      console.log("Final transformed jobs:", transformedJobs)
      console.log("Final transformed analytics:", transformedAnalytics)
      
      setJobs(transformedJobs)
      setAnalytics(transformedAnalytics)
    } catch (error) {
      console.error("Error loading job data:", error)
      
      // Fallback to empty data if API fails
      setJobs([])
      setAnalytics({
        total_jobs_tracked: 0,
        applications_submitted: 0,
        response_rate: 0,
        responses_received: 0,
        interviews_scheduled: 0,
        offers_received: 0,
        avg_qualification_score: 0,
        jobs_this_week: 0,
      })
      
      flashMessage.show("Failed to load job data from database", "error")
    } finally {
      setIsLoading(false)
    }
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await loadData()
      flashMessage.show("Data refreshed successfully", "success")
    } finally {
      setIsRefreshing(false)
    }
  }

  const handleToggleFavorite = async (jobId: string) => {
    try {
      const response = await fetch("/api/jobs/favorite", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          job_id: jobId,
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to update favorite: ${response.status}`)
      }

      const result = await response.json()
      if (result.success) {
        // Update local state
        setJobs((prevJobs) =>
          prevJobs.map((job) => (job.id === jobId ? { ...job, is_favorited: !job.is_favorited } : job)),
        )
        flashMessage.show("Favorite updated successfully", "success")
      } else {
        throw new Error(result.error || "Failed to update favorite")
      }
    } catch (error) {
      console.error("Error updating favorite:", error)
      flashMessage.show("Failed to update favorite", "error")
    }
  }

  const handleMarkAsApplied = async (jobId: string) => {
    try {
      const response = await fetch("/api/jobs/apply", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          job_id: jobId,
          applied_date: new Date().toISOString().split('T')[0], // YYYY-MM-DD format
          application_method: "manual",
          notes: "Marked as applied from job tracker",
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to mark as applied: ${response.status}`)
      }

      const result = await response.json()
      if (result.success) {
        // Update local state
        setJobs((prevJobs) =>
          prevJobs.map((job) =>
            job.id === jobId
              ? {
                  ...job,
                  has_applied: true,
                  date_applied: new Date().toISOString(),
                  application_status: "applied" as const,
                }
              : job,
          ),
        )
        flashMessage.show("Marked as applied successfully", "success")
      } else {
        throw new Error(result.error || "Failed to mark as applied")
      }
    } catch (error) {
      console.error("Error marking as applied:", error)
      flashMessage.show("Failed to update application status", "error")
    }
  }

  const handleUpdateApplicationStatus = async (jobId: string, status: JobItem["application_status"]) => {
    try {
      const response = await fetch("/api/jobs/status-update", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          job_id: jobId,
          status: status,
          notes: `Status updated to ${status} from job tracker`,
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to update status: ${response.status}`)
      }

      const result = await response.json()
      if (result.success) {
        // Update local state
        setJobs((prevJobs) => 
          prevJobs.map((job) => (job.id === jobId ? { ...job, application_status: status } : job))
        )
        flashMessage.show("Application status updated successfully", "success")
      } else {
        throw new Error(result.error || "Failed to update status")
      }
    } catch (error) {
      console.error("Error updating status:", error)
      flashMessage.show("Failed to update status", "error")
    }
  }

  // Filter jobs based on search and filters
  const filteredJobs = useMemo(() => {
    return jobs.filter((jobItem) => {
      const job = jobItem.job
      const jobScore = getJobScore(job)

      // Score threshold filter
      if (jobScore !== null && jobScore < scoreThreshold) {
        return false
      }

      // Search filter
      if (searchQuery) {
        const searchableText = [
          job.title || job.job_title || "",
          job.company || job.company_name || "",
          job.location || "",
          jobItem.notes || "",
        ]
          .join(" ")
          .toLowerCase()

        if (!searchableText.includes(searchQuery.toLowerCase())) {
          return false
        }
      }

      // Quick filters
      switch (activeFilter) {
        case "applied":
          return jobItem.has_applied
        case "favorites":
          return jobItem.is_favorited
        case "this_week":
          const weekAgo = new Date()
          weekAgo.setDate(weekAgo.getDate() - 7)
          const jobDate = new Date(job.date_found || "")
          return jobDate >= weekAgo
        case "high_score":
          return jobScore !== null && jobScore >= 80
        case "all":
        default:
          return true
      }
    })
  }, [jobs, searchQuery, activeFilter, scoreThreshold])

  return (
    <BaseLayout>
      <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Job Tracker</h1>
              <p className="text-muted-foreground">Track and manage your job applications with AI-powered insights</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowExportModal(true)}>
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
              <Button onClick={handleRefresh} disabled={isRefreshing}>
                <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>
          </div>

          <div className="space-y-6">
            <AnalyticsCards analytics={analytics} isLoading={isLoading} />

            <SearchAndFilters
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              activeFilter={activeFilter}
              onFilterChange={setActiveFilter}
              scoreThreshold={scoreThreshold}
              onScoreThresholdChange={setScoreThreshold}
              totalJobs={jobs.length}
              filteredCount={filteredJobs.length}
            />

            <JobGrid
              jobs={filteredJobs}
              isLoading={isLoading}
              onJobSelect={setSelectedJob}
              onToggleFavorite={handleToggleFavorite}
              onMarkAsApplied={handleMarkAsApplied}
            />
          </div>

          <JobDetailModal
            job={selectedJob}
            onClose={() => setSelectedJob(null)}
            onToggleFavorite={handleToggleFavorite}
            onMarkAsApplied={handleMarkAsApplied}
            onUpdateStatus={handleUpdateApplicationStatus}
          />

          <ExportModal isOpen={showExportModal} onClose={() => setShowExportModal(false)} jobs={filteredJobs} />
        </div>
    </BaseLayout>
  )
}

// Helper function to get job score
function getJobScore(job: JobItem["job"]): number | null {
  let score: number | string | null | undefined =
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
