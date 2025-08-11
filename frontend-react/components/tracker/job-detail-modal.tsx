"use client"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  ExternalLink,
  Heart,
  CheckCircle,
  MapPin,
  DollarSign,
  Calendar,
  Building,
  FileText,
  Bot,
  TrendingUp,
} from "lucide-react"
import { getScoreColor } from "@/lib/utils"
import type { JobItem } from "@/app/tracker/page"

interface JobDetailModalProps {
  job: JobItem | null
  onClose: () => void
  onToggleFavorite: (jobId: string) => void
  onMarkAsApplied: (jobId: string) => void
  onUpdateStatus: (jobId: string, status: JobItem["application_status"]) => void
}

export function JobDetailModal({
  job,
  onClose,
  onToggleFavorite,
  onMarkAsApplied,
  onUpdateStatus,
}: JobDetailModalProps) {
  if (!job) return null

  const jobData = job.job
  const jobTitle = jobData.title || jobData.job_title || "Unknown Title"
  const companyName = jobData.company || jobData.company_name || "Unknown Company"
  const jobScore = getJobScore(jobData)
  const dateFound = jobData.date_found ? new Date(jobData.date_found).toLocaleDateString() : "Unknown"

  const getScoreLabel = (score: number) => {
    if (score >= 90) return "Excellent Match"
    if (score >= 80) return "Great Match"
    if (score >= 70) return "Good Match"
    if (score >= 60) return "Fair Match"
    if (score >= 50) return "Possible Match"
    return "Low Match"
  }

  const formatJobDescription = (description: string) => {
    if (!description) return "No description available"

    // Split into paragraphs and format
    const paragraphs = description.split("\n\n").filter((p) => p.trim())
    return paragraphs
      .map((paragraph) => {
        // Check if it's a header (ends with colon or is short)
        if (paragraph.endsWith(":") || paragraph.length < 50) {
          return `<h4 class="font-semibold text-sm mt-4 mb-2">${paragraph}</h4>`
        }
        // Check if it's a bullet point
        if (paragraph.startsWith("•") || paragraph.startsWith("-")) {
          return `<li class="ml-4">${paragraph.substring(1).trim()}</li>`
        }
        return `<p class="mb-2">${paragraph}</p>`
      })
      .join("")
  }

  return (
    <Dialog open={!!job} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <DialogTitle className="text-xl mb-2">{jobTitle}</DialogTitle>
              <DialogDescription className="flex items-center gap-2 text-base">
                <Building className="w-4 h-4" />
                {companyName}
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2">
              {jobScore && (
                <Badge className={`${getScoreColor(jobScore)} border text-base px-3 py-1`}>{jobScore}%</Badge>
              )}
              <Button variant="ghost" size="sm" onClick={() => onToggleFavorite(job.id)} className="p-2">
                <Heart
                  className={`w-5 h-5 ${job.is_favorited ? "fill-red-500 text-red-500" : "text-muted-foreground"}`}
                />
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6">
          {/* Job Information */}
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-3">Job Information</h3>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-muted-foreground" />
                    <span>{jobData.location || "Remote"}</span>
                  </div>
                  {(jobData.salary || jobData.salary_range) && (
                    <div className="flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-muted-foreground" />
                      <span className="text-green-600">{jobData.salary || jobData.salary_range}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-muted-foreground" />
                    <span>Found: {dateFound}</span>
                  </div>
                </div>
              </div>

              {/* Application Status */}
              <div>
                <h3 className="font-semibold mb-3">Application Status</h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">Status:</span>
                    <Select
                      value={job.application_status || (job.has_applied ? "applied" : "not_applied")}
                      onValueChange={(value) => onUpdateStatus(job.id, value as JobItem["application_status"])}
                    >
                      <SelectTrigger className="w-40">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="not_applied">Not Applied</SelectItem>
                        <SelectItem value="applied">Applied</SelectItem>
                        <SelectItem value="interview">Interview</SelectItem>
                        <SelectItem value="offer">Offer</SelectItem>
                        <SelectItem value="rejected">Rejected</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {job.date_applied && (
                    <div className="text-sm text-muted-foreground">
                      Applied: {new Date(job.date_applied).toLocaleDateString()}
                    </div>
                  )}
                  {job.priority && (
                    <div className="flex items-center gap-2">
                      <span className="text-sm">Priority:</span>
                      <Badge variant="outline">{job.priority}</Badge>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              {/* AI Score */}
              {jobScore && (
                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    AI Match Score
                  </h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">{getScoreLabel(jobScore)}</span>
                      <span className="font-semibold">{jobScore}%</span>
                    </div>
                    <Progress value={jobScore} className="h-3" />
                  </div>
                </div>
              )}

              {/* AI Evaluation */}
              {jobData.gemini_evaluation && (
                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <Bot className="w-4 h-4" />
                    AI Evaluation
                  </h3>
                  <div className="bg-muted/50 p-3 rounded-md">
                    <p className="text-sm">{jobData.gemini_evaluation}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <Separator />

          {/* Notes */}
          {job.notes && (
            <>
              <div>
                <h3 className="font-semibold mb-3">Notes</h3>
                <div className="bg-muted/50 p-3 rounded-md">
                  <p className="text-sm">{job.notes}</p>
                </div>
              </div>
              <Separator />
            </>
          )}

          {/* Job Description */}
          <div>
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Job Description
            </h3>
            <div
              className="bg-muted/50 p-4 rounded-md max-h-96 overflow-y-auto prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{
                __html: formatJobDescription(jobData.description || jobData.job_description || ""),
              }}
            />
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          {!job.has_applied && (
            <Button onClick={() => onMarkAsApplied(job.id)}>
              <CheckCircle className="w-4 h-4 mr-2" />
              Mark as Applied
            </Button>
          )}
          {jobData.linkedin_url && (
            <Button asChild>
              <a href={jobData.linkedin_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="w-4 h-4 mr-2" />
                View on LinkedIn
              </a>
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
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
