"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Save, Loader2 } from "lucide-react"
import type { Application } from "@/app/jobs/[id]/page"

interface EditApplicationModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: Partial<Application>) => Promise<void>
  application: Application | null
  jobTitle: string
  companyName: string
}

export function EditApplicationModal({
  isOpen,
  onClose,
  onSubmit,
  application,
  jobTitle,
  companyName,
}: EditApplicationModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    applied_date: "",
    application_method: "",
    application_status: "",
    follow_up_date: "",
    interview_date: "",
    salary_offered: "",
    notes: "",
  })

  useEffect(() => {
    if (application && isOpen) {
      setFormData({
        applied_date: application.applied_date || "",
        application_method: application.application_method || "",
        application_status: application.application_status || "",
        follow_up_date: application.follow_up_date || "",
        interview_date: application.interview_date || "",
        salary_offered: application.salary_offered?.toString() || "",
        notes: application.notes || "",
      })
    }
  }, [application, isOpen])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    setIsSubmitting(true)
    try {
      const submitData: Partial<Application> = {
        ...formData,
        salary_offered: formData.salary_offered ? Number(formData.salary_offered) : undefined,
      }

      await onSubmit(submitData)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      onClose()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Edit Application</DialogTitle>
          <p className="text-sm text-muted-foreground">
            {jobTitle} at {companyName}
          </p>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="applied_date">Application Date</Label>
              <Input
                id="applied_date"
                type="date"
                value={formData.applied_date}
                onChange={(e) => setFormData({ ...formData, applied_date: e.target.value })}
                required
              />
            </div>

            <div>
              <Label htmlFor="application_method">Application Method</Label>
              <Select
                value={formData.application_method}
                onValueChange={(value) => setFormData({ ...formData, application_method: value })}
                required
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select method" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="manual">Manual Application</SelectItem>
                  <SelectItem value="linkedin_easy_apply">LinkedIn Easy Apply</SelectItem>
                  <SelectItem value="indeed_quick_apply">Indeed Quick Apply</SelectItem>
                  <SelectItem value="email">Email</SelectItem>
                  <SelectItem value="company_website">Company Website</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="application_status">Status</Label>
              <Select
                value={formData.application_status}
                onValueChange={(value) => setFormData({ ...formData, application_status: value })}
                required
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="applied">Applied</SelectItem>
                  <SelectItem value="interviewing">Interviewing</SelectItem>
                  <SelectItem value="offered">Offered</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="withdrawn">Withdrawn</SelectItem>
                  <SelectItem value="accepted">Accepted</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="follow_up_date">Follow-up Date</Label>
              <Input
                id="follow_up_date"
                type="date"
                value={formData.follow_up_date}
                onChange={(e) => setFormData({ ...formData, follow_up_date: e.target.value })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="interview_date">Interview Date</Label>
              <Input
                id="interview_date"
                type="date"
                value={formData.interview_date}
                onChange={(e) => setFormData({ ...formData, interview_date: e.target.value })}
              />
            </div>

            <div>
              <Label htmlFor="salary_offered">Salary Offered</Label>
              <Input
                id="salary_offered"
                type="number"
                placeholder="Enter amount"
                value={formData.salary_offered}
                onChange={(e) => setFormData({ ...formData, salary_offered: e.target.value })}
              />
            </div>
          </div>

          <div>
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              placeholder="Any notes about this application..."
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              rows={4}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Changes
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
