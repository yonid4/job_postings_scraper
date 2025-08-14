import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

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
  scoreThreshold?: number
  jobLimit?: number
}

export function useProfile() {
  const [profile, setProfile] = useState<ProfileData>({
    experienceLevel: "",
    educationLevel: "",
    skillsTechnologies: [],
    workArrangementPreference: "",
    preferredLocations: [],
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProfile = async () => {
    try {
      setLoading(true)
      console.log('🔍 Checking Supabase connection for profile...')
      
      if (!supabase) {
        console.warn('⚠️ Supabase not configured - using default profile')
        setError('Supabase not configured. Using default profile for development.')
        setProfile({
          experienceLevel: "",
          educationLevel: "",
          skillsTechnologies: [],
          workArrangementPreference: "",
          preferredLocations: [],
        })
        return
      }
      
      console.log('📡 Fetching profile from Supabase...')
      const { data, error: fetchError } = await supabase
        .from('user_profiles')
        .select('*')
        .single()
      
      console.log('📊 Supabase profile response:', { data, fetchError })
      
      if (fetchError) {
        if (fetchError.code === 'PGRST116') {
          // No profile found, return default
          console.log('📝 No profile found, using defaults')
          setProfile({
            experienceLevel: "",
            educationLevel: "",
            skillsTechnologies: [],
            workArrangementPreference: "",
            preferredLocations: [],
          })
          setError(null)
        } else {
          console.error('❌ Supabase profile error:', fetchError)
          setError(`Profile fetch error: ${fetchError.message}`)
        }
      } else {
        console.log('✅ Profile fetched successfully')
        setProfile({
          yearsOfExperience: data.years_of_experience,
          experienceLevel: data.experience_level || "",
          educationLevel: data.education_level || "",
          fieldOfStudy: data.field_of_study,
          skillsTechnologies: data.skills_technologies || [],
          workArrangementPreference: data.work_arrangement_preference || "",
          preferredLocations: data.preferred_locations || [],
          salaryMin: data.salary_min,
          salaryMax: data.salary_max,
          scoreThreshold: data.score_threshold,
          jobLimit: data.job_limit,
        })
        setError(null)
      }
    } catch (err) {
      console.error('💥 Profile fetch error:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const saveProfile = async (profileData: ProfileData) => {
    try {
      if (!supabase) {
        throw new Error('Supabase not configured')
      }
      
      console.log('💾 Saving profile to Supabase...', profileData)
      
      const profilePayload = {
        years_of_experience: profileData.yearsOfExperience,
        experience_level: profileData.experienceLevel,
        education_level: profileData.educationLevel,
        field_of_study: profileData.fieldOfStudy,
        skills_technologies: profileData.skillsTechnologies,
        work_arrangement_preference: profileData.workArrangementPreference,
        preferred_locations: profileData.preferredLocations,
        salary_min: profileData.salaryMin,
        salary_max: profileData.salaryMax,
        score_threshold: profileData.scoreThreshold,
        job_limit: profileData.jobLimit,
        user_id: (await supabase.auth.getUser()).data.user?.id,
      }
      
      const { data, error } = await supabase
        .from('user_profiles')
        .upsert(profilePayload, { 
          onConflict: 'user_id',
          ignoreDuplicates: false 
        })
        .select()
        .single()
      
      if (error) {
        console.error('❌ Profile save error:', error)
        throw new Error(`Failed to save profile: ${error.message}`)
      }
      
      console.log('✅ Profile saved successfully')
      setProfile(profileData)
      return { success: true, message: 'Profile saved successfully' }
    } catch (err) {
      console.error('💥 Profile save error:', err)
      throw err
    }
  }

  useEffect(() => {
    fetchProfile()
  }, [])

  return { profile, loading, error, saveProfile, refetch: fetchProfile }
}