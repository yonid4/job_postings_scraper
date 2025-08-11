"use client"

import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Download, FileText, Table } from "lucide-react"
import { flashMessage } from "@/components/flash-message"
import type { JobItem } from "@/app/tracker/page"

interface ExportModalProps {
  isOpen: boolean
  onClose: () => void
  jobs: JobItem[]
}

export function ExportModal({ isOpen, onClose, jobs }: ExportModalProps) {
  const [exportFormat, setExportFormat] = useState("csv")
  const [selectedFields, setSelectedFields] = useState({
    title: true,
    company: true,
    location: true,
    salary: true,
    score: true,
    status: true,
    dateFound: true,
    notes: false,
    description: false,
  })
  const [isExporting, setIsExporting] = useState(false)

  const fields = [
    { key: "title", label: "Job Title", required: true },
    { key: "company", label: "Company", required: true },
    { key: "location", label: "Location", required: false },
    { key: "salary", label: "Salary", required: false },
    { key: "score", label: "AI Score", required: false },
    { key: "status", label: "Application Status", required: false },
    { key: "dateFound", label: "Date Found", required: false },
    { key: "notes", label: "Notes", required: false },
    { key: "description", label: "Job Description", required: false },
  ]

  const handleFieldChange = (field: string, checked: boolean) => {
    setSelectedFields((prev) => ({ ...prev, [field]: checked }))
  }

  const handleExport = async () => {
    setIsExporting(true)
    try {
      // Simulate export process
      await new Promise((resolve) => setTimeout(resolve, 2000))

      // In a real implementation, you would generate and download the file here
      const exportData = jobs.map((jobItem) => {
        const job = jobItem.job
        const data: any = {}

        if (selectedFields.title) data.title = job.title || job.job_title || ""
        if (selectedFields.company) data.company = job.company || job.company_name || ""
        if (selectedFields.location) data.location = job.location || ""
        if (selectedFields.salary) data.salary = job.salary || job.salary_range || ""
        if (selectedFields.score) {
          const score = getJobScore(job)
          data.score = score ? `${score}%` : ""
        }
        if (selectedFields.status) {
          data.status = jobItem.application_status || (jobItem.has_applied ? "Applied" : "Not Applied")
        }
        if (selectedFields.dateFound) data.dateFound = job.date_found || ""
        if (selectedFields.notes) data.notes = jobItem.notes || ""
        if (selectedFields.description) data.description = job.description || job.job_description || ""

        return data
      })

      // Create and download file
      if (exportFormat === "csv") {
        downloadCSV(exportData)
      } else {
        downloadJSON(exportData)
      }

      flashMessage.show(`Successfully exported ${jobs.length} jobs as ${exportFormat.toUpperCase()}`, "success")
      onClose()
    } catch (error) {
      flashMessage.show("Failed to export jobs", "error")
    } finally {
      setIsExporting(false)
    }
  }

  const downloadCSV = (data: any[]) => {
    if (data.length === 0) return

    const headers = Object.keys(data[0])
    const csvContent = [
      headers.join(","),
      ...data.map((row) => headers.map((header) => `"${String(row[header] || "").replace(/"/g, '""')}"`).join(",")),
    ].join("\n")

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
    const link = document.createElement("a")
    link.href = URL.createObjectURL(blob)
    link.download = `job-tracker-export-${new Date().toISOString().split("T")[0]}.csv`
    link.click()
  }

  const downloadJSON = (data: any[]) => {
    const jsonContent = JSON.stringify(data, null, 2)
    const blob = new Blob([jsonContent], { type: "application/json;charset=utf-8;" })
    const link = document.createElement("a")
    link.href = URL.createObjectURL(blob)
    link.download = `job-tracker-export-${new Date().toISOString().split("T")[0]}.json`
    link.click()
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="w-5 h-5" />
            Export Jobs
          </DialogTitle>
          <DialogDescription>Export {jobs.length} jobs to a file for external use.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Export Format */}
          <div className="space-y-2">
            <Label>Export Format</Label>
            <Select value={exportFormat} onValueChange={setExportFormat}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">
                  <div className="flex items-center gap-2">
                    <Table className="w-4 h-4" />
                    CSV (Spreadsheet)
                  </div>
                </SelectItem>
                <SelectItem value="json">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    JSON (Data)
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Field Selection */}
          <div className="space-y-2">
            <Label>Fields to Export</Label>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {fields.map((field) => (
                <div key={field.key} className="flex items-center space-x-2">
                  <Checkbox
                    id={field.key}
                    checked={selectedFields[field.key as keyof typeof selectedFields]}
                    onCheckedChange={(checked) => handleFieldChange(field.key, checked as boolean)}
                    disabled={field.required}
                  />
                  <Label htmlFor={field.key} className="text-sm font-normal">
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </Label>
                </div>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose} disabled={isExporting}>
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={isExporting}>
            {isExporting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                Export
              </>
            )}
          </Button>
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
