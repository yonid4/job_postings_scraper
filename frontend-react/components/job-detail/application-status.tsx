"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Edit, Calendar } from "lucide-react"
import type { Application } from "@/app/jobs/[id]/page"

interface ApplicationStatusProps {
  application: Application | null
  onEdit: () => void
}

export function ApplicationStatus({ application, onEdit }: ApplicationStatusProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "applied":
        return "bg-blue-100 text-blue-800"
      case "interviewing":
        return "bg-yellow-100 text-yellow-800"
      case "offered":
        return "bg-green-100 text-green-800"
      case "rejected":
        return "bg-red-100 text-red-800"
      case "withdrawn":
        return "bg-gray-100 text-gray-800"
      case "accepted":
        return "bg-emerald-100 text-emerald-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  const formatMethod = (method: string) => {
    return method.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Application Status</CardTitle>
      </CardHeader>
      <CardContent>
        {application ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Badge className={getStatusColor(application.application_status)}>
                {application.application_status.charAt(0).toUpperCase() + application.application_status.slice(1)}
              </Badge>
              <Button variant="outline" size="sm" onClick={onEdit}>
                <Edit className="w-4 h-4 mr-2" />
                Edit
              </Button>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Calendar className="w-4 h-4" />
                <span>Applied: {formatDate(application.applied_date)}</span>
              </div>

              <p className="text-muted-foreground">Method: {formatMethod(application.application_method)}</p>

              {application.interview_date && (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="w-4 h-4" />
                  <span>Interview: {formatDate(application.interview_date)}</span>
                </div>
              )}

              {application.follow_up_date && (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="w-4 h-4" />
                  <span>Follow-up: {formatDate(application.follow_up_date)}</span>
                </div>
              )}
            </div>

            {application.notes && (
              <div className="bg-muted/50 rounded-lg p-3">
                <h6 className="font-medium mb-1">Notes:</h6>
                <p className="text-sm text-muted-foreground">{application.notes}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-4">
            <Badge variant="secondary" className="mb-4">
              Not Applied
            </Badge>
            <p className="text-sm text-muted-foreground">No application recorded for this job yet.</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
