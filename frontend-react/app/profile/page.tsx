"use client"

import { useState, useEffect } from "react"
import { BaseLayout } from "@/components/base-layout"
import { ProfileForm } from "@/components/profile/profile-form"
import { ProfileSidebar } from "@/components/profile/profile-sidebar"
import { ProfileProgress } from "@/components/profile/profile-progress"
import { Button } from "@/components/ui/button"
import { Save, Loader2 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { flashMessage } from "@/components/flash-message"

export interface ProfileData {
  yearsOfExperience?: number
  experienceLevel: string
  educationLevel: string
  fieldOfStudy?: string
  skillsTechnologies: string[]
  workArrangementPreference: string
  preferredLocations: string[]
  salaryMin?: number
  salaryMax?: number
}

export default function ProfilePage() {
  const [profileData, setProfileData] = useState<ProfileData>({
    experienceLevel: "",
    educationLevel: "",
    skillsTechnologies: [],
    workArrangementPreference: "",
    preferredLocations: [],
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [completionPercentage, setCompletionPercentage] = useState(0)
  const { toast } = useToast()

  useEffect(() => {
    loadProfileData()
  }, [])

  useEffect(() => {
    calculateCompletion()
  }, [profileData])

  const loadProfileData = async () => {
    setIsLoading(true)
    try {
      const response = await fetch("/api/profile")
      
      if (!response.ok) {
        throw new Error(`Failed to load profile: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.success && data.profile) {
        setProfileData(data.profile)
      } else {
        throw new Error(data.error || "Failed to load profile data")
      }
    } catch (error) {
      console.error("Error loading profile data:", error)
      flashMessage.show("Failed to load profile data", "error")
    } finally {
      setIsLoading(false)
    }
  }

  const calculateCompletion = () => {
    const requiredFields = ["experienceLevel", "educationLevel", "skillsTechnologies", "workArrangementPreference"]

    const optionalFields = ["yearsOfExperience", "fieldOfStudy", "preferredLocations", "salaryMin"]

    let completed = 0
    const total = requiredFields.length + optionalFields.length

    // Check required fields
    requiredFields.forEach((field) => {
      if (field === "skillsTechnologies") {
        if (profileData[field] && profileData[field].length > 0) completed++
      } else if (profileData[field as keyof ProfileData]) {
        completed++
      }
    })

    // Check optional fields
    optionalFields.forEach((field) => {
      if (field === "preferredLocations") {
        if (profileData[field] && profileData[field].length > 0) completed++
      } else if (profileData[field as keyof ProfileData]) {
        completed++
      }
    })

    setCompletionPercentage(Math.round((completed / total) * 100))
  }

  const handleSaveProfile = async (data: ProfileData) => {
    setIsSaving(true)
    try {
      // Validate required fields
      if (!data.experienceLevel) {
        throw new Error("Please select an experience level")
      }
      if (!data.educationLevel) {
        throw new Error("Please select an education level")
      }
      if (!data.workArrangementPreference) {
        throw new Error("Please select a work arrangement preference")
      }
      if (!data.skillsTechnologies || data.skillsTechnologies.length === 0) {
        throw new Error("Please enter your skills and technologies")
      }

      // Save profile via API
      const response = await fetch("/api/profile", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error(`Failed to save profile: ${response.status}`)
      }

      const result = await response.json()
      
      if (result.success) {
        setProfileData(data)
        flashMessage.show(result.message || "Profile updated successfully!", "success")
      } else {
        throw new Error(result.error || "Failed to save profile")
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to save profile"
      flashMessage.show(message, "error")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <BaseLayout>
      <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Your Profile</h1>
            <p className="text-muted-foreground">Manage your qualifications and preferences</p>
          </div>
          <div className="flex items-center gap-3">
            <ProfileProgress percentage={completionPercentage} />
            <Button
              onClick={() => {
                const form = document.getElementById("profile-form") as HTMLFormElement
                if (form) {
                  form.requestSubmit()
                }
              }}
              disabled={isSaving}
              className="min-w-[120px]"
            >
              {isSaving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Profile
                </>
              )}
            </Button>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <ProfileForm data={profileData} onSave={handleSaveProfile} isLoading={isLoading} isSaving={isSaving} />
          </div>
          <div className="space-y-6">
            <ProfileSidebar completionPercentage={completionPercentage} />
          </div>
        </div>
      </div>
    </BaseLayout>
  )
}
