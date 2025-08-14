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
import { useProfile, ProfileData } from "@/hooks/useProfile"

export default function ProfilePage() {
  const { profile, loading: isLoading, error, saveProfile } = useProfile()
  const [profileData, setProfileData] = useState<ProfileData>({
    experienceLevel: "",
    educationLevel: "",
    skillsTechnologies: [],
    workArrangementPreference: "",
    preferredLocations: [],
  })
  const [isSaving, setIsSaving] = useState(false)
  const [completionPercentage, setCompletionPercentage] = useState(0)
  const { toast } = useToast()

  useEffect(() => {
    if (profile) {
      setProfileData(profile)
    }
  }, [profile])

  useEffect(() => {
    calculateCompletion()
  }, [profileData])

  useEffect(() => {
    if (error) {
      flashMessage.show(`Profile error: ${error}`, "error")
    }
  }, [error])

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

      // Save profile via hook
      const result = await saveProfile(data)
      flashMessage.show(result.message, "success")
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
