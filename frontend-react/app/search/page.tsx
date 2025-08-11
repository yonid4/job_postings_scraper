"use client"

import { useState, useEffect } from "react"
import { BaseLayout } from "@/components/base-layout"
import { SearchForm } from "@/components/search/search-form"
import { SearchResults } from "@/components/search/search-results"
import { SearchSidebar } from "@/components/search/search-sidebar"
import { JobDetailModal } from "@/components/search/job-detail-modal"
import { CaptchaModal } from "@/components/search/captcha-modal"
import { SearchStrategy } from "@/components/search/search-strategy"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { BotIcon as Robot, Rocket, Shield, Zap } from "lucide-react"
import { flashMessage } from "@/components/flash-message"

export interface SearchFilters {
  website: string
  keywords: string
  location: string
  distance: string
  workArrangement: string[]
  experienceLevel: string[]
  jobType: string[]
  datePosted: string
  qualificationThreshold: number
  jobLimit: number
  additionalKeywords: string
}

export interface JobResult {
  id: string
  job_title: string
  company: string
  location: string
  job_url: string
  score: number
  reasoning: string
  key_skills: string[]
  strengths: string[]
  concerns: string[]
  required_experience?: string
  education_requirements?: string
  date_posted?: string
  salary_range?: string
}

export interface SearchResponse {
  success: boolean
  jobs_count?: number
  total_jobs?: number
  results: JobResult[]
  strategy_info?: {
    method: string
    estimated_time: string
    performance_impact: string
    reason: string
  }
  date_filter_applied?: boolean
  date_filter_days?: number
  error?: string
  requires_manual_intervention?: boolean
}

export default function SearchPage() {
  const [filters, setFilters] = useState<SearchFilters>({
    website: "linkedin",
    keywords: "",
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

  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<JobResult[]>([])
  const [searchStats, setSearchStats] = useState<{
    total: number
    qualified: number
    excellent: number
    avgScore: number
  } | null>(null)
  const [selectedJob, setSelectedJob] = useState<JobResult | null>(null)
  const [showCaptcha, setShowCaptcha] = useState(false)
  const [captchaData, setCaptchaData] = useState<any>(null)
  const [searchStrategy, setSearchStrategy] = useState<{
    method: string
    estimatedTime: string
    reason: string
  } | null>(null)

  // Calculate search strategy based on filters
  useEffect(() => {
    calculateSearchStrategy()
  }, [filters])

  const calculateSearchStrategy = () => {
    const hasBasicParams = filters.keywords && filters.location
    const hasAdvancedFilters =
      filters.datePosted !== "any" ||
      filters.workArrangement.length > 0 ||
      filters.experienceLevel.length > 0 ||
      filters.jobType.length > 0

    if (hasBasicParams) {
      if (hasAdvancedFilters) {
        setSearchStrategy({
          method: "WebDriver Mode",
          estimatedTime: "10-30 seconds",
          reason: "Advanced filters detected - using WebDriver for precise filtering",
        })
      } else {
        setSearchStrategy({
          method: "Fast API Mode",
          estimatedTime: "2-5 seconds",
          reason: "Basic search - using fast API-only approach",
        })
      }
    } else {
      setSearchStrategy(null)
    }
  }

  const handleSearch = async () => {
    if (!filters.keywords.trim()) {
      flashMessage.show("Please enter job keywords", "error")
      return
    }
    if (!filters.location.trim()) {
      flashMessage.show("Please enter a location", "error")
      return
    }

    setIsSearching(true)
    setSearchResults([])
    setSearchStats(null)

    try {
      // Simulate API call - replace with actual implementation
      await new Promise((resolve) => setTimeout(resolve, 2000))

      // Mock response - replace with actual API call
      const mockResults: JobResult[] = [
        {
          id: "1",
          job_title: "Senior Software Engineer",
          company: "TechCorp Inc.",
          location: "San Francisco, CA",
          job_url: "https://linkedin.com/jobs/123",
          score: 85,
          reasoning: "Strong match based on your React and Node.js experience",
          key_skills: ["React", "Node.js", "TypeScript", "AWS"],
          strengths: ["Matches your tech stack", "Senior level position", "Great company culture"],
          concerns: ["Requires 5+ years experience", "On-site position"],
          required_experience: "5+ years",
          education_requirements: "Bachelor's degree preferred",
          salary_range: "$120,000 - $160,000",
        },
        {
          id: "2",
          job_title: "Frontend Developer",
          company: "StartupXYZ",
          location: "Remote",
          job_url: "https://linkedin.com/jobs/456",
          score: 72,
          reasoning: "Good match for frontend skills, remote work available",
          key_skills: ["React", "JavaScript", "CSS", "Git"],
          strengths: ["Remote work option", "Growing startup", "Modern tech stack"],
          concerns: ["Lower salary range", "Early stage company"],
          required_experience: "3+ years",
          education_requirements: "Degree or equivalent experience",
          salary_range: "$80,000 - $110,000",
        },
      ]

      setSearchResults(mockResults)
      setSearchStats({
        total: mockResults.length,
        qualified: mockResults.filter((job) => job.score >= 60).length,
        excellent: mockResults.filter((job) => job.score >= 80).length,
        avgScore: Math.round(mockResults.reduce((sum, job) => sum + job.score, 0) / mockResults.length),
      })

      flashMessage.show(`Successfully found ${mockResults.length} jobs!`, "success")
    } catch (error) {
      flashMessage.show("Search failed. Please try again.", "error")
    } finally {
      setIsSearching(false)
    }
  }

  const handleSaveJob = async (jobId: string) => {
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000))
      flashMessage.show("Job saved successfully!", "success")
    } catch (error) {
      flashMessage.show("Failed to save job", "error")
    }
  }

  const handleSaveAllJobs = async () => {
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500))
      flashMessage.show(`Successfully saved ${searchResults.length} jobs!`, "success")
    } catch (error) {
      flashMessage.show("Failed to save jobs", "error")
    }
  }

  return (
    <BaseLayout>
      <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Job Search & Analysis</h1>
            <p className="text-muted-foreground">Analyze job opportunities with AI-powered qualification screening</p>
            <div className="flex gap-2 mt-3">
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                <Rocket className="w-3 h-3 mr-1" />
                Optimized Search
              </Badge>
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                <Shield className="w-3 h-3 mr-1" />
                CAPTCHA Handling
              </Badge>
              <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                <Zap className="w-3 h-3 mr-1" />
                Fast API Mode
              </Badge>
            </div>
          </div>
          <Button onClick={handleSearch} disabled={isSearching} size="lg" className="min-w-[140px]">
            {isSearching ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Analyzing...
              </>
            ) : (
              <>
                <Robot className="w-4 h-4 mr-2" />
                Analyze Jobs
              </>
            )}
          </Button>
        </div>

        <div className="grid gap-6 lg:grid-cols-4">
          <div className="lg:col-span-3 space-y-6">
            <SearchForm filters={filters} onFiltersChange={setFilters} isSearching={isSearching} />

            {searchStrategy && (
              <SearchStrategy
                method={searchStrategy.method}
                estimatedTime={searchStrategy.estimatedTime}
                reason={searchStrategy.reason}
              />
            )}

            <SearchResults
              results={searchResults}
              stats={searchStats}
              isLoading={isSearching}
              onJobSelect={setSelectedJob}
              onSaveJob={handleSaveJob}
              onSaveAllJobs={handleSaveAllJobs}
            />
          </div>

          <div>
            <SearchSidebar />
          </div>
        </div>

        <JobDetailModal job={selectedJob} onClose={() => setSelectedJob(null)} onSave={handleSaveJob} />

        <CaptchaModal
          isOpen={showCaptcha}
          onClose={() => setShowCaptcha(false)}
          onContinue={() => {
            setShowCaptcha(false)
            // Continue search after CAPTCHA
          }}
          data={captchaData}
        />
      </div>
    </BaseLayout>
  )
}
