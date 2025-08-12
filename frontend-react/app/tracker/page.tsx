"use client"

import { useState, useEffect, useMemo } from "react"
import { motion } from "framer-motion"
import { BaseLayout } from "@/components/base-layout"
import { SearchAndFilters } from "@/components/tracker/search-and-filters"
import { JobGrid } from "@/components/tracker/job-grid"
import { JobDetailModal } from "@/components/tracker/job-detail-modal"
import { ExportModal } from "@/components/tracker/export-modal"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { RefreshCw, Download, TrendingUp } from "lucide-react"
import { flashMessage } from "@/components/flash-message"
import { useJobs } from '@/hooks/useJobs'

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
  // API data state (fallback)
  const [apiJobs, setApiJobs] = useState<JobItem[]>([])
  const [apiAnalytics, setApiAnalytics] = useState<AnalyticsData | null>(null)
  const [apiLoading, setApiLoading] = useState(true)
  
  // Hook data state (primary)
  const [hookTransformedJobs, setHookTransformedJobs] = useState<JobItem[]>([])
  const [hookAnalytics, setHookAnalytics] = useState<AnalyticsData | null>(null)
  
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [selectedJob, setSelectedJob] = useState<JobItem | null>(null)
  const [showExportModal, setShowExportModal] = useState(false)

  // Use Supabase hook data directly
  const { jobs: hookJobs, loading: hookLoading, error: hookError } = useJobs()
  const [searchQuery, setSearchQuery] = useState("")
  const [activeFilter, setActiveFilter] = useState("all")
  const [scoreThreshold, setScoreThreshold] = useState(70)

  // FALLBACK MECHANISM: Use hook data as primary, API data as fallback
  const displayJobs = hookTransformedJobs && hookTransformedJobs.length > 0 ? hookTransformedJobs : apiJobs
  const displayAnalytics = hookAnalytics || apiAnalytics
  // Only show loading if we have no data from either source AND at least one source is still loading
  const displayLoading = (displayJobs.length === 0) && (hookLoading || apiLoading)

  // Optional: Log data source for debugging (can be removed in production)
  // console.log('🔍 Data loaded:', {
  //   'source': displayJobs.length > 0 ? (hookTransformedJobs.length > 0 ? 'Supabase' : 'API') : 'none',
  //   'jobs': displayJobs.length,
  //   'loading': displayLoading
  // })

  // Transform Supabase data to component format
  useEffect(() => {
    if (!hookLoading) {
      if (hookJobs && hookJobs.length > 0) {
        // Transform Supabase jobs to expected JobItem format
        const transformedJobs: JobItem[] = hookJobs.map((job: any) => ({
          id: job.id?.toString() || Math.random().toString(),
          job: {
            title: job.title || job.job_title || 'Untitled Position',
            job_title: job.title || job.job_title || 'Untitled Position',
            company: job.company || job.company_name || 'Unknown Company',
            company_name: job.company || job.company_name || 'Unknown Company',
            location: job.location || 'Location not specified',
            salary: job.salary_range || job.salary || null,
            salary_range: job.salary_range || job.salary || null,
            description: job.description || job.job_description || 'No description available',
            job_description: job.description || job.job_description || 'No description available',
            linkedin_url: job.url || job.job_url || '#',
            date_found: job.created_at ? new Date(job.created_at).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
            qualification_score: job.qualification_score || job.score || Math.floor(Math.random() * 40) + 60,
            score: job.qualification_score || job.score || Math.floor(Math.random() * 40) + 60,
            gemini_score: job.gemini_score || job.qualification_score || job.score || Math.floor(Math.random() * 40) + 60,
            gemini_evaluation: job.evaluation || job.gemini_evaluation || 'No evaluation available'
          },
          has_applied: job.has_applied || job.applied || false,
          is_favorited: job.is_favorited || job.favorited || false,
          notes: job.notes || '',
          priority: job.priority || 'Medium',
          source: job.url || job.job_url || job.source || 'Supabase',
          date_applied: job.application_date || job.date_applied || null,
          application_status: job.application_status || 'not_applied'
        }))

        // Generate analytics from job data
        const transformedAnalytics: AnalyticsData = {
          total_jobs_tracked: transformedJobs.length,
          applications_submitted: transformedJobs.filter(job => job.has_applied).length,
          response_rate: 0, // Would need response data
          responses_received: 0,
          interviews_scheduled: 0,
          offers_received: 0,
                  avg_qualification_score: transformedJobs.length > 0 
          ? Math.round(transformedJobs.reduce((sum, job) => sum + (job.job?.qualification_score || job.job?.score || 0), 0) / transformedJobs.length)
          : 0,
        jobs_this_week: transformedJobs.filter(job => {
          const jobDate = new Date(job.job?.date_found || new Date())
          const weekAgo = new Date()
          weekAgo.setDate(weekAgo.getDate() - 7)
          return jobDate >= weekAgo
        }).length,
        }

        // Jobs successfully transformed and ready for display
        
        setHookTransformedJobs(transformedJobs)
        setHookAnalytics(transformedAnalytics)
      } else if (hookError) {
        console.error("Supabase hook error:", hookError)
        flashMessage.show(`Failed to load jobs: ${hookError}`, "error")
      } else {
        setHookTransformedJobs([])
        setHookAnalytics({
          total_jobs_tracked: 0,
          applications_submitted: 0,
          response_rate: 0,
          responses_received: 0,
          interviews_scheduled: 0,
          offers_received: 0,
          avg_qualification_score: 0,
          jobs_this_week: 0,
        })
      }
    }
  }, [hookJobs, hookLoading, hookError])

  // Load API data as fallback
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setApiLoading(true)
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
      
      setApiJobs(transformedJobs)
      setApiAnalytics(transformedAnalytics)
    } catch (error) {
      console.error("Error loading job data:", error)
      
      // Fallback to empty data if API fails
      setApiJobs([])
      setApiAnalytics({
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
      setApiLoading(false)
    }
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      // Simple page refresh to reload data from Supabase
      window.location.reload()
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
        // Update the appropriate state based on which data source is active
        if (hookTransformedJobs && hookTransformedJobs.length > 0) {
          setHookTransformedJobs((prevJobs) =>
            prevJobs.map((job) => (job.id === jobId ? { ...job, is_favorited: !job.is_favorited } : job)),
          )
        } else {
          setApiJobs((prevJobs) =>
            prevJobs.map((job) => (job.id === jobId ? { ...job, is_favorited: !job.is_favorited } : job)),
          )
        }
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
        // Update the appropriate state based on which data source is active
        if (hookTransformedJobs && hookTransformedJobs.length > 0) {
          setHookTransformedJobs((prevJobs) =>
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
        } else {
          setApiJobs((prevJobs) =>
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
        }
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
        // Update the appropriate state based on which data source is active
        if (hookTransformedJobs && hookTransformedJobs.length > 0) {
          setHookTransformedJobs((prevJobs) => 
            prevJobs.map((job) => (job.id === jobId ? { ...job, application_status: status } : job))
          )
        } else {
          setApiJobs((prevJobs) => 
            prevJobs.map((job) => (job.id === jobId ? { ...job, application_status: status } : job))
          )
        }
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
    return displayJobs.filter((jobItem) => {
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
  }, [displayJobs, searchQuery, activeFilter, scoreThreshold])

  return (
    <BaseLayout title="Job Tracker" showSidebar={true}>
      <div className="w-[calc(100vw-18rem)] ml-4 md:ml-6 px-6 md:px-10">
        <div className="space-y-6">
          {/* Header Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <TrendingUp className="h-6 w-6 text-blue-600" />
              <p className="text-gray-600">Track and manage your job applications with AI-powered insights</p>
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
          </motion.div>

          {/* Analytics Cards with Gradient Styling */}
          {displayLoading ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
            >
              {[...Array(4)].map((_, i) => (
                <Card key={i}>
                  <CardHeader className="pb-2">
                    <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
                  </CardHeader>
                  <CardContent>
                    <div className="h-8 w-16 bg-gray-200 rounded animate-pulse mb-2" />
                    <div className="h-3 w-32 bg-gray-200 rounded animate-pulse" />
                  </CardContent>
                </Card>
              ))}
            </motion.div>
          ) : displayAnalytics ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
            >
              <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium opacity-90">Total Jobs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{displayAnalytics?.total_jobs_tracked || 0}</div>
                  <p className="text-xs opacity-75">Jobs tracked</p>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-r from-green-500 to-green-600 text-white">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium opacity-90">Applications</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{displayAnalytics?.applications_submitted || 0}</div>
                  <p className="text-xs opacity-75">Submitted</p>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-r from-purple-500 to-purple-600 text-white">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium opacity-90">Response Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{(displayAnalytics?.response_rate || 0).toFixed(1)}%</div>
                  <p className="text-xs opacity-75">Response rate</p>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-r from-orange-500 to-orange-600 text-white">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium opacity-90">Avg Score</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{Math.round(displayAnalytics?.avg_qualification_score || 0)}%</div>
                  <p className="text-xs opacity-75">AI qualification</p>
                </CardContent>
              </Card>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
            >
              <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium opacity-90">Total Jobs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">0</div>
                  <p className="text-xs opacity-75">Jobs tracked</p>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-r from-green-500 to-green-600 text-white">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium opacity-90">Applications</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">0</div>
                  <p className="text-xs opacity-75">Submitted</p>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-r from-purple-500 to-purple-600 text-white">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium opacity-90">Response Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">0.0%</div>
                  <p className="text-xs opacity-75">Response rate</p>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-r from-orange-500 to-orange-600 text-white">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium opacity-90">Avg Score</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">0%</div>
                  <p className="text-xs opacity-75">AI qualification</p>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Search and Filters */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <SearchAndFilters
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              activeFilter={activeFilter}
              onFilterChange={setActiveFilter}
              scoreThreshold={scoreThreshold}
              onScoreThresholdChange={setScoreThreshold}
              totalJobs={displayJobs.length}
              filteredCount={filteredJobs.length}
            />
          </motion.div>

          {/* Job Grid */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <JobGrid
              jobs={filteredJobs}
              isLoading={displayLoading}
              onJobSelect={setSelectedJob}
              onToggleFavorite={handleToggleFavorite}
              onMarkAsApplied={handleMarkAsApplied}
            />
          </motion.div>

          {/* Modals */}
          <JobDetailModal
            job={selectedJob}
            onClose={() => setSelectedJob(null)}
            onToggleFavorite={handleToggleFavorite}
            onMarkAsApplied={handleMarkAsApplied}
            onUpdateStatus={handleUpdateApplicationStatus}
          />

          <ExportModal isOpen={showExportModal} onClose={() => setShowExportModal(false)} jobs={filteredJobs} />
        </div>
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
