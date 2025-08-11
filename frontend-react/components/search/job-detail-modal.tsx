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
import { Separator } from "@/components/ui/separator"
import { ExternalLink, Save, CheckCircle, AlertTriangle } from "lucide-react"
import { getScoreColor } from "@/lib/utils"
import type { JobResult } from "@/app/search/page"

interface JobDetailModalProps {
  job: JobResult | null
  onClose: () => void
  onSave: (jobId: string) => Promise<void>
}

export function JobDetailModal({ job, onClose, onSave }: JobDetailModalProps) {
  if (!job) return null

  return (
    <Dialog open={!!job} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl">{job.job_title}</DialogTitle>
          <DialogDescription className="text-base">
            {job.company} • {job.location}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Score and Basic Info */}
          <div className="flex items-center justify-between">
            <div>
              <Badge className={`${getScoreColor(job.score)} border text-base px-4 py-2`}>{job.score}/100</Badge>
              <p className="text-sm text-muted-foreground mt-1">
                {job.score >= 80 ? "Excellent Match" : job.score >= 60 ? "Good Match" : "Fair Match"}
              </p>
            </div>
            {job.salary_range && (
              <div className="text-right">
                <p className="font-medium">{job.salary_range}</p>
                <p className="text-sm text-muted-foreground">Salary Range</p>
              </div>
            )}
          </div>

          <Separator />

          {/* Job Information */}
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-3">Job Information</h3>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Company:</span>
                  <span className="ml-2">{job.company}</span>
                </div>
                <div>
                  <span className="font-medium">Location:</span>
                  <span className="ml-2">{job.location}</span>
                </div>
                {job.required_experience && (
                  <div>
                    <span className="font-medium">Required Experience:</span>
                    <span className="ml-2">{job.required_experience}</span>
                  </div>
                )}
                {job.education_requirements && (
                  <div>
                    <span className="font-medium">Education:</span>
                    <span className="ml-2">{job.education_requirements}</span>
                  </div>
                )}
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-3">AI Analysis</h3>
              <div>
                <span className="font-medium">Reasoning:</span>
                <p className="text-muted-foreground mt-1">{job.reasoning}</p>
              </div>
            </div>
          </div>

          <Separator />

          {/* Skills and Analysis */}
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-3">Key Skills</h3>
              {job.key_skills && job.key_skills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {job.key_skills.map((skill, index) => (
                    <Badge key={index} variant="outline">
                      {skill}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No skills listed</p>
              )}
            </div>

            <div>
              <h3 className="font-semibold mb-3">Strengths</h3>
              {job.strengths && job.strengths.length > 0 ? (
                <ul className="space-y-1">
                  {job.strengths.map((strength, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span>{strength}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted-foreground">No specific strengths identified</p>
              )}
            </div>
          </div>

          {job.concerns && job.concerns.length > 0 && (
            <>
              <Separator />
              <div>
                <h3 className="font-semibold mb-3">Potential Concerns</h3>
                <ul className="space-y-1">
                  {job.concerns.map((concern, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                      <span>{concern}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          <Button variant="outline" onClick={() => onSave(job.id)}>
            <Save className="w-4 h-4 mr-2" />
            Save Job
          </Button>
          <Button asChild>
            <a href={job.job_url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="w-4 h-4 mr-2" />
              View on LinkedIn
            </a>
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
