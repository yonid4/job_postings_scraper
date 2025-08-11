"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { BaseLayout } from "@/components/base-layout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Slider } from "@/components/ui/slider"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Save,
  LogOut,
  Brain,
  FileText,
  Upload,
  Target,
  Info,
  HelpCircle,
  CheckCircle,
  AlertTriangle,
  Loader2,
  ExternalLink,
  Edit3,
  Check,
  X,
  FileCheck,
  Trash2,
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { flashMessage } from "@/components/flash-message"

interface ResumeStatus {
  has_resume: boolean
  filename?: string
  file_type?: string
  file_size?: number
  uploaded_at?: string
  is_processed?: boolean
}

interface UserSettings {
  score_threshold: number
}

export default function SettingsPage() {
  const [scoreThreshold, setScoreThreshold] = useState(70)
  const [isEditingThreshold, setIsEditingThreshold] = useState(false)
  const [tempThreshold, setTempThreshold] = useState("")
  const [isSaving, setIsSaving] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [resumeStatus, setResumeStatus] = useState<ResumeStatus | null>(null)
  const [isLoadingResume, setIsLoadingResume] = useState(true)
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  useEffect(() => {
    loadCurrentSettings()
    loadResumeStatus()
  }, [])

  const loadCurrentSettings = async () => {
    try {
      const response = await fetch("/api/user-settings")
      
      if (!response.ok) {
        throw new Error(`Failed to load settings: ${response.status}`)
      }
      
      const data = await response.json()
      if (data.score_threshold !== undefined) {
        setScoreThreshold(data.score_threshold)
      }
    } catch (error) {
      console.error("Error loading settings:", error)
      // Keep default threshold value
    }
  }

  const loadResumeStatus = async () => {
    setIsLoadingResume(true)
    try {
      const response = await fetch("/resume/status")
      
      if (!response.ok) {
        throw new Error(`Failed to load resume status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.success) {
        setResumeStatus(data.status)
      } else {
        throw new Error(data.error || "Failed to load resume status")
      }
    } catch (error) {
      console.error("Error loading resume status:", error)
      flashMessage.show("Failed to load resume status", "error")
    } finally {
      setIsLoadingResume(false)
    }
  }

  const handleSaveSettings = async () => {
    setIsSaving(true)
    try {
      const response = await fetch("/api/user-settings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          score_threshold: scoreThreshold,
        }),
      })

      const data = await response.json()
      if (data.success) {
        flashMessage.show("Settings saved successfully!", "success")
      } else {
        throw new Error(data.error || "Failed to save settings")
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to save settings"
      flashMessage.show(message, "error")
    } finally {
      setIsSaving(false)
    }
  }

  const handleThresholdChange = (value: number[]) => {
    setScoreThreshold(value[0])
  }

  const handleEditThreshold = () => {
    setIsEditingThreshold(true)
    setTempThreshold(scoreThreshold.toString())
  }

  const handleSaveThresholdEdit = () => {
    const newValue = Number.parseInt(tempThreshold)
    if (!isNaN(newValue) && newValue >= 1 && newValue <= 100) {
      setScoreThreshold(newValue)
    }
    setIsEditingThreshold(false)
    setTempThreshold("")
  }

  const handleCancelThresholdEdit = () => {
    setIsEditingThreshold(false)
    setTempThreshold("")
  }

  const getThresholdColor = (value: number) => {
    if (value >= 90) return "bg-green-500"
    if (value >= 70) return "bg-blue-500"
    if (value >= 50) return "bg-yellow-500"
    return "bg-gray-500"
  }

  const getThresholdVariant = (value: number): "default" | "secondary" | "destructive" | "outline" => {
    if (value >= 90) return "default"
    if (value >= 70) return "default"
    if (value >= 50) return "secondary"
    return "secondary"
  }

  const handleFileSelect = (file: File) => {
    // Validate file type
    const allowedTypes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if (!allowedTypes.includes(file.type)) {
      flashMessage.show("Please select a PDF or DOCX file", "error")
      return
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      flashMessage.show("File size must be less than 10MB", "error")
      return
    }

    setSelectedFile(file)
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  const handleUploadResume = async () => {
    if (!selectedFile) {
      flashMessage.show("Please select a file first", "error")
      return
    }

    setIsUploading(true)
    setUploadProgress(0)

    const formData = new FormData()
    formData.append("resume", selectedFile)

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return prev
          }
          return prev + 10
        })
      }, 200)

      const response = await fetch("/resume/upload", {
        method: "POST",
        body: formData,
      })

      clearInterval(progressInterval)
      setUploadProgress(100)

      const data = await response.json()
      if (data.success) {
        flashMessage.show(data.message || "Resume uploaded successfully!", "success")
        setSelectedFile(null)
        if (fileInputRef.current) {
          fileInputRef.current.value = ""
        }
        await loadResumeStatus()
      } else {
        throw new Error(data.error || "Upload failed")
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed"
      flashMessage.show(message, "error")
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const handleDeleteResume = async () => {
    try {
      const response = await fetch("/resume/delete", {
        method: "DELETE",
      })

      const data = await response.json()
      if (data.success) {
        flashMessage.show("Resume deleted successfully", "success")
        await loadResumeStatus()
      } else {
        throw new Error(data.error || "Failed to delete resume")
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to delete resume"
      flashMessage.show(message, "error")
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <BaseLayout>
      <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8">
          <div className="space-y-6">
            {/* Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
            >
              <div>
                <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
                <p className="text-muted-foreground">Configure your preferences and manage your profile</p>
              </div>
              <div className="flex items-center gap-3">
                <Button onClick={handleSaveSettings} disabled={isSaving} className="min-w-[140px]">
                  {isSaving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Save Settings
                    </>
                  )}
                </Button>
                <Button variant="outline" asChild>
                  <a href="/logout">
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                  </a>
                </Button>
              </div>
            </motion.div>

            <div className="grid gap-6 lg:grid-cols-3">
              {/* Main Settings */}
              <div className="lg:col-span-2 space-y-6">
                {/* AI Score Threshold */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Brain className="h-5 w-5 text-blue-500" />
                        AI Score Threshold
                      </CardTitle>
                    </CardHeader>
                <CardContent className="space-y-6">
                  <p className="text-sm text-muted-foreground">
                    Set the minimum AI score threshold for jobs to appear in your job tracker. Only jobs with scores
                    equal to or above this threshold will be displayed.
                  </p>

                  <div className="grid gap-6 md:grid-cols-3">
                    <div className="md:col-span-2 space-y-4">
                      <div className="space-y-2">
                        <Label className="text-sm font-medium">Minimum Score: {scoreThreshold}%</Label>
                        <Slider
                          value={[scoreThreshold]}
                          onValueChange={handleThresholdChange}
                          max={100}
                          min={1}
                          step={1}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>1% (Show All)</span>
                          <span>50% (Average)</span>
                          <span>100% (Perfect Match)</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col items-center justify-center space-y-3">
                      <div className="relative">
                        {isEditingThreshold ? (
                          <motion.div
                            initial={{ scale: 0.9 }}
                            animate={{ scale: 1 }}
                            className="flex items-center gap-2"
                          >
                            <Input
                              type="number"
                              value={tempThreshold}
                              onChange={(e) => setTempThreshold(e.target.value)}
                              min={1}
                              max={100}
                              className="w-16 h-8 text-center text-sm"
                              onKeyDown={(e) => {
                                if (e.key === "Enter") handleSaveThresholdEdit()
                                if (e.key === "Escape") handleCancelThresholdEdit()
                              }}
                              autoFocus
                            />
                            <div className="flex gap-1">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={handleSaveThresholdEdit}
                                className="h-6 w-6 p-0"
                              >
                                <Check className="h-3 w-3" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={handleCancelThresholdEdit}
                                className="h-6 w-6 p-0"
                              >
                                <X className="h-3 w-3" />
                              </Button>
                            </div>
                          </motion.div>
                        ) : (
                          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                            <Badge
                              variant={getThresholdVariant(scoreThreshold)}
                              className={`${getThresholdColor(scoreThreshold)} text-white cursor-pointer px-4 py-2 text-lg font-semibold hover:opacity-90 transition-opacity`}
                              onClick={handleEditThreshold}
                            >
                              <Target className="mr-2 h-4 w-4" />
                              {scoreThreshold}%
                            </Badge>
                          </motion.div>
                        )}
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-muted-foreground">Current threshold</p>
                        {!isEditingThreshold && (
                          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                            <Edit3 className="h-3 w-3" />
                            Click to edit
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription className="text-sm">
                      <strong>Tip:</strong> Lower values show more jobs but may include less relevant matches. Higher
                      values show fewer but more qualified jobs.
                    </AlertDescription>
                  </Alert>
                </CardContent>
              </Card>
            </motion.div>

            {/* Resume Upload */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-green-500" />
                    Resume Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <p className="text-sm text-muted-foreground">
                    Upload your resume for better job matching. It will be processed automatically when you search for
                    jobs.
                  </p>

                  {/* File Upload Area */}
                  <div
                    className={`relative border-2 border-dashed rounded-lg p-6 transition-colors ${
                      isDragOver
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-950/20"
                        : "border-gray-300 dark:border-gray-600"
                    }`}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.docx"
                      onChange={handleFileInputChange}
                      className="hidden"
                    />

                    <div className="text-center space-y-4">
                      <div className="mx-auto w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                        <Upload className="h-6 w-6 text-gray-500" />
                      </div>

                      {selectedFile ? (
                        <div className="space-y-2">
                          <p className="text-sm font-medium">{selectedFile.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatFileSize(selectedFile.size)} • {selectedFile.type.includes("pdf") ? "PDF" : "DOCX"}
                          </p>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <p className="text-sm font-medium">
                            Drag and drop your resume here, or{" "}
                            <button
                              type="button"
                              onClick={() => fileInputRef.current?.click()}
                              className="text-blue-500 hover:text-blue-600 underline"
                            >
                              browse files
                            </button>
                          </p>
                          <p className="text-xs text-muted-foreground">Supports PDF and DOCX files up to 10MB</p>
                        </div>
                      )}

                      {selectedFile && (
                        <div className="flex justify-center gap-2">
                          <Button onClick={handleUploadResume} disabled={isUploading} size="sm">
                            {isUploading ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Uploading...
                              </>
                            ) : (
                              <>
                                <Upload className="mr-2 h-4 w-4" />
                                Upload Resume
                              </>
                            )}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelectedFile(null)
                              if (fileInputRef.current) {
                                fileInputRef.current.value = ""
                              }
                            }}
                          >
                            Cancel
                          </Button>
                        </div>
                      )}
                    </div>

                    {isUploading && (
                      <div className="mt-4">
                        <Progress value={uploadProgress} className="w-full" />
                        <p className="text-xs text-center text-muted-foreground mt-2">{uploadProgress}% uploaded</p>
                      </div>
                    )}
                  </div>

                  {/* Current Resume Status */}
                  {!isLoadingResume && resumeStatus && (
                    <AnimatePresence>
                      {resumeStatus.has_resume ? (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                        >
                          <Alert>
                            <FileCheck className="h-4 w-4" />
                            <AlertDescription>
                              <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                  <h6 className="font-medium">Current Resume</h6>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={handleDeleteResume}
                                    className="text-red-500 hover:text-red-600 h-6 px-2"
                                  >
                                    <Trash2 className="h-3 w-3" />
                                  </Button>
                                </div>
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                  <div>
                                    <p className="text-muted-foreground">File:</p>
                                    <p className="font-medium">{resumeStatus.filename}</p>
                                  </div>
                                  <div>
                                    <p className="text-muted-foreground">Type:</p>
                                    <p className="font-medium">{resumeStatus.file_type?.toUpperCase()}</p>
                                  </div>
                                  <div>
                                    <p className="text-muted-foreground">Size:</p>
                                    <p className="font-medium">
                                      {resumeStatus.file_size ? formatFileSize(resumeStatus.file_size) : "N/A"}
                                    </p>
                                  </div>
                                  <div>
                                    <p className="text-muted-foreground">Uploaded:</p>
                                    <p className="font-medium">
                                      {resumeStatus.uploaded_at
                                        ? new Date(resumeStatus.uploaded_at).toLocaleDateString()
                                        : "N/A"}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            </AlertDescription>
                          </Alert>
                        </motion.div>
                      ) : (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                        >
                          <Alert>
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>
                              <h6 className="font-medium mb-1">No Resume Uploaded</h6>
                              <p className="text-sm">Upload a resume to get better job matching results.</p>
                            </AlertDescription>
                          </Alert>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  )}

                  <div className="text-xs text-muted-foreground space-y-1">
                    <p>
                      <strong>Supported formats:</strong> PDF, DOCX
                    </p>
                    <p>
                      <strong>Max file size:</strong> 10MB
                    </p>
                    <p>
                      <strong>Processing:</strong> Your resume will be processed when you search for jobs
                    </p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Current Status */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Info className="h-4 w-4 text-blue-500" />
                    Current Status
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h6 className="text-sm font-medium mb-2">Resume Status</h6>
                    {isLoadingResume ? (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Loading...
                      </div>
                    ) : resumeStatus?.has_resume ? (
                      <div className="flex items-center gap-2 text-sm text-green-600">
                        <CheckCircle className="h-4 w-4" />
                        Resume uploaded
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-sm text-yellow-600">
                        <AlertTriangle className="h-4 w-4" />
                        No resume uploaded
                      </div>
                    )}
                  </div>

                  <Separator />

                  <div>
                    <h6 className="text-sm font-medium mb-2">System Status</h6>
                    <div className="flex items-center gap-2 text-sm text-green-600">
                      <CheckCircle className="h-4 w-4" />
                      System ready
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Help & Support */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <HelpCircle className="h-4 w-4 text-purple-500" />
                    Help & Support
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h6 className="text-sm font-medium mb-2">Getting Started</h6>
                    <div className="space-y-1">
                      <a
                        href="https://console.cloud.google.com/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm text-blue-500 hover:text-blue-600 transition-colors"
                      >
                        Google Cloud Console
                        <ExternalLink className="h-3 w-3" />
                      </a>
                      <a
                        href="https://developers.google.com/sheets/api"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm text-blue-500 hover:text-blue-600 transition-colors"
                      >
                        Google Sheets API Docs
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </div>

                  <Separator />

                  <div>
                    <h6 className="text-sm font-medium mb-2">Features</h6>
                    <div className="space-y-1">
                      {[
                        "LinkedIn job extraction",
                        "Google Sheets integration",
                        "Job qualification analysis",
                        "Advanced filtering options",
                      ].map((feature, index) => (
                        <div key={index} className="flex items-center gap-2 text-sm">
                          <CheckCircle className="h-3 w-3 text-green-500" />
                          {feature}
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
            </div>
          </div>
      </div>
    </BaseLayout>
  )
}
