"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface JobDescriptionProps {
  description?: string
}

export function JobDescription({ description }: JobDescriptionProps) {
  if (!description) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Job Description</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No description available</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Job Description</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: description }} />
      </CardContent>
    </Card>
  )
}
