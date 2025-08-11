"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { MapPin, Calendar, DollarSign, Heart, ExternalLink } from "lucide-react"
import type { Job } from "@/app/jobs/[id]/page"

interface JobHeaderProps {
  job: Job
  isFavorited: boolean
  onToggleFavorite: () => void
}

export function JobHeader({ job, isFavorited, onToggleFavorite }: JobHeaderProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex justify-between items-start mb-6">
          <div className="flex-1">
            <h1 className="text-3xl font-bold mb-2">{job.job_title}</h1>
            <h2 className="text-xl text-muted-foreground mb-4">{job.company_name}</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <MapPin className="w-4 h-4" />
                  <span>{job.location || "Location not specified"}</span>
                </div>

                {job.date_posted && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Calendar className="w-4 h-4" />
                    <span>Posted {formatDate(job.date_posted)}</span>
                  </div>
                )}

                {job.salary_range && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <DollarSign className="w-4 h-4" />
                    <span>{job.salary_range}</span>
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                {job.job_type && <Badge variant="default">{job.job_type}</Badge>}
                {job.experience_level && <Badge variant="secondary">{job.experience_level}</Badge>}
                {job.work_arrangement && <Badge variant="outline">{job.work_arrangement}</Badge>}
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-2 ml-6">
            <Button
              variant="outline"
              size="sm"
              onClick={onToggleFavorite}
              className="flex items-center gap-2 bg-transparent"
            >
              <Heart className={`w-4 h-4 ${isFavorited ? "fill-red-500 text-red-500" : "text-muted-foreground"}`} />
              {isFavorited ? "Favorited" : "Favorite"}
            </Button>

            <Button asChild>
              <a href={job.job_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="w-4 h-4 mr-2" />
                View Original
              </a>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
