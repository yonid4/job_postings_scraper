"use client"

import React from "react"

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Skeleton } from "@/components/ui/skeleton"
import { User, Code, Briefcase } from "lucide-react"
import type { ProfileData } from "@/app/profile/page"

const profileSchema = z.object({
  yearsOfExperience: z.number().min(0).max(50).optional(),
  experienceLevel: z.string().min(1, "Experience level is required"),
  educationLevel: z.string().min(1, "Education level is required"),
  fieldOfStudy: z.string().optional(),
  skillsTechnologies: z.array(z.string()).min(1, "At least one skill is required"),
  workArrangementPreference: z.string().min(1, "Work arrangement preference is required"),
  preferredLocations: z.array(z.string()).optional(),
  salaryMin: z.number().min(0).optional(),
  salaryMax: z.number().min(0).optional(),
})

interface ProfileFormProps {
  data: ProfileData
  onSave: (data: ProfileData) => Promise<void>
  isLoading: boolean
  isSaving: boolean
}

export function ProfileForm({ data, onSave, isLoading, isSaving }: ProfileFormProps) {
  const [locationsInput, setLocationsInput] = React.useState("")
  const [skillsInput, setSkillsInput] = React.useState("")
  
  const form = useForm<ProfileData>({
    resolver: zodResolver(profileSchema),
    defaultValues: data,
  })

  // Update form and input fields when data changes
  React.useEffect(() => {
    form.reset(data)
    setLocationsInput(data.preferredLocations?.join(", ") || "")
    setSkillsInput(data.skillsTechnologies?.join(", ") || "")
  }, [data, form])

  const onSubmit = async (formData: ProfileData) => {
    // Ensure locations are processed before saving
    const locations = locationsInput
      .split(",")
      .map((location) => location.trim())
      .filter((location) => location.length > 0)
    
    const finalData = {
      ...formData,
      preferredLocations: locations,
    }
    
    await onSave(finalData)
  }

  const handleSkillsChange = (value: string) => {
    setSkillsInput(value)
    const skills = value
      .split(",")
      .map((skill) => skill.trim())
      .filter((skill) => skill.length > 0)
    form.setValue("skillsTechnologies", skills)
  }

  const handleLocationsChange = (value: string) => {
    setLocationsInput(value)
  }

  const handleLocationsBlur = () => {
    // Process locations when user finishes editing
    const locations = locationsInput
      .split(",")
      .map((location) => location.trim())
      .filter((location) => location.length > 0)
    form.setValue("preferredLocations", locations)
    // Clean up the display
    setLocationsInput(locations.join(", "))
  }

  if (isLoading) {
    return <ProfileFormSkeleton />
  }

  return (
    <Form {...form}>
      <form id="profile-form" onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Basic Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="yearsOfExperience"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Years of Experience</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        placeholder="e.g., 3"
                        min="0"
                        max="50"
                        {...field}
                        onChange={(e) => field.onChange(e.target.value ? Number.parseInt(e.target.value) : undefined)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="experienceLevel"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Experience Level *</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select experience level" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="entry">Entry Level</SelectItem>
                        <SelectItem value="junior">Junior</SelectItem>
                        <SelectItem value="mid">Mid Level</SelectItem>
                        <SelectItem value="senior">Senior Level</SelectItem>
                        <SelectItem value="lead">Lead</SelectItem>
                        <SelectItem value="executive">Executive</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="educationLevel"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Education Level *</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select education level" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="high_school">High School Diploma</SelectItem>
                        <SelectItem value="associates">Associate's Degree</SelectItem>
                        <SelectItem value="bachelors">Bachelor's Degree</SelectItem>
                        <SelectItem value="masters">Master's Degree</SelectItem>
                        <SelectItem value="phd">Doctoral Degree</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="fieldOfStudy"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Field of Study</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., Computer Science, Business Administration" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
        </Card>

        {/* Skills and Technologies */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code className="h-5 w-5" />
              Skills & Technologies *
            </CardTitle>
          </CardHeader>
          <CardContent>
            <FormField
              control={form.control}
              name="skillsTechnologies"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Skills and Technologies</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Enter your skills and technologies, separated by commas (e.g., Python, JavaScript, React, AWS)"
                      className="min-h-[100px]"
                      value={skillsInput}
                      onChange={(e) => handleSkillsChange(e.target.value)}
                    />
                  </FormControl>
                  <FormDescription>
                    List your technical skills, programming languages, frameworks, and tools.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        {/* Work Preferences */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Briefcase className="h-5 w-5" />
              Work Preferences
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="workArrangementPreference"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Work Arrangement *</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select work arrangement" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="any">Any</SelectItem>
                        <SelectItem value="remote">Remote</SelectItem>
                        <SelectItem value="hybrid">Hybrid</SelectItem>
                        <SelectItem value="on_site">On-site</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="preferredLocations"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Preferred Locations</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="e.g., San Francisco, CA, Remote"
                        value={locationsInput}
                        onChange={(e) => handleLocationsChange(e.target.value)}
                        onBlur={handleLocationsBlur}
                      />
                    </FormControl>
                    <FormDescription>Enter preferred locations, separated by commas.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="salaryMin"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Minimum Salary (USD)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        placeholder="e.g., 80000"
                        min="0"
                        step="1000"
                        {...field}
                        onChange={(e) => field.onChange(e.target.value ? Number.parseInt(e.target.value) : undefined)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="salaryMax"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Maximum Salary (USD)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        placeholder="e.g., 150000"
                        min="0"
                        step="1000"
                        {...field}
                        onChange={(e) => field.onChange(e.target.value ? Number.parseInt(e.target.value) : undefined)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
        </Card>
      </form>
    </Form>
  )
}

function ProfileFormSkeleton() {
  return (
    <div className="space-y-6">
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-10 w-full" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-10 w-full" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
