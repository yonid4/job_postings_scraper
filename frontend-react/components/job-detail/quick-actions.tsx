"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { CheckCircle, Heart, ExternalLink, Share } from "lucide-react"
import type { Job, Application } from "@/app/jobs/[id]/page"

interface QuickActionsProps {
  job: Job
  application: Application | null
  isFavorited: boolean
  onMarkAsApplied: () => void
  onToggleFavorite: () => void
  onShare: () => void
}

export function QuickActions({
  job,
  application,
  isFavorited,
  onMarkAsApplied,
  onToggleFavorite,
  onShare,
}: QuickActionsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {!application && (
            <Button onClick={onMarkAsApplied} className="w-full">
              <CheckCircle className="w-4 h-4 mr-2" />
              Mark as Applied
            </Button>
          )}

          <Button variant="outline" onClick={onToggleFavorite} className="w-full bg-transparent">
            <Heart className={`w-4 h-4 mr-2 ${isFavorited ? "fill-red-500 text-red-500" : ""}`} />
            {isFavorited ? "Remove from" : "Add to"} Favorites
          </Button>

          {job.application_url && (
            <Button variant="outline" asChild className="w-full bg-transparent">
              <a href={job.application_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="w-4 h-4 mr-2" />
                Apply Now
              </a>
            </Button>
          )}

          <Button variant="outline" onClick={onShare} className="w-full bg-transparent">
            <Share className="w-4 h-4 mr-2" />
            Share Job
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
