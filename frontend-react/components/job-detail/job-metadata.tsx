"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Calendar, Globe, AlertCircle, FileText } from "lucide-react"
import type { Job } from "@/app/jobs/[id]/page"

interface JobMetadataProps {
  job: Job
}

export function JobMetadata({ job }: JobMetadataProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Job Details</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Globe className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">Job Site</span>
              </div>
              <p className="text-sm text-muted-foreground">{job.job_site}</p>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-1">
                <Calendar className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">Scraped</span>
              </div>
              <p className="text-sm text-muted-foreground">{formatDate(job.scraped_date)}</p>
            </div>
          </div>

          {job.application_deadline && (
            <div>
              <div className="flex items-center gap-2 mb-1">
                <AlertCircle className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">Application Deadline</span>
              </div>
              <p className="text-sm text-muted-foreground">{formatDate(job.application_deadline)}</p>
            </div>
          )}

          {job.notes && (
            <div>
              <div className="flex items-center gap-2 mb-1">
                <FileText className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">Notes</span>
              </div>
              <p className="text-sm text-muted-foreground">{job.notes}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
