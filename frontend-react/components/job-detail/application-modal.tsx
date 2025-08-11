"use client"

import type React from "react"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { CheckCircle, Loader2 } from "lucide-react"
import type { Application } from "@/app/jobs/[id]/page"

interface ApplicationModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: Partial<Application>) => Promise<void>
  jobTitle: string
  companyName: string
}

export function ApplicationModal({ isOpen, onClose, onSubmit, jobTitle, companyName }: ApplicationModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    applied_date: new Date().toISOString().split("T")[0],
    application_method: "",
    notes: "",
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.application_method) return

    setIsSubmitting(true)
    try {
      await onSubmit(formData)
      setFormData({
        applied_date: new Date().toISOString().split("T")[0],
        application_method: "",
        notes: "",
      })
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
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Mark as Applied</DialogTitle>
          <p className="text-sm text-muted-foreground">
            {jobTitle} at {companyName}
          </p>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
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
                <SelectValue placeholder="Select application method" />
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

          <div>
            <Label htmlFor="notes">Notes (Optional)</Label>
            <Textarea
              id="notes"
              placeholder="Any notes about this application..."
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !formData.application_method}>
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Mark as Applied
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
