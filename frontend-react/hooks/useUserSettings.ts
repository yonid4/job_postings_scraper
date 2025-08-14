import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

export interface UserSettings {
  score_threshold: number
  job_limit?: number
}

export function useUserSettings() {
  const [settings, setSettings] = useState<UserSettings>({
    score_threshold: 70,
    job_limit: 25,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSettings = async () => {
    try {
      setLoading(true)
      console.log('🔍 Checking Supabase connection for user settings...')
      
      if (!supabase) {
        console.warn('⚠️ Supabase not configured - using default settings')
        setError('Supabase not configured. Using default settings for development.')
        setSettings({ score_threshold: 70, job_limit: 25 })
        return
      }
      
      console.log('📡 Fetching user settings from Supabase...')
      const { data, error: fetchError } = await supabase
        .from('user_profiles')
        .select('score_threshold, job_limit')
        .single()
      
      console.log('📊 Supabase settings response:', { data, fetchError })
      
      if (fetchError) {
        if (fetchError.code === 'PGRST116') {
          // No profile found, return defaults
          console.log('📝 No user profile found, using defaults')
          setSettings({ score_threshold: 70, job_limit: 25 })
          setError(null)
        } else {
          console.error('❌ Supabase settings error:', fetchError)
          setError(`Settings fetch error: ${fetchError.message}`)
        }
      } else {
        console.log('✅ User settings fetched successfully')
        setSettings({
          score_threshold: data.score_threshold || 70,
          job_limit: data.job_limit || 25,
        })
        setError(null)
      }
    } catch (err) {
      console.error('💥 Settings fetch error:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const saveSettings = async (newSettings: UserSettings) => {
    try {
      if (!supabase) {
        throw new Error('Supabase not configured')
      }
      
      console.log('💾 Saving user settings to Supabase...', newSettings)
      
      const user = await supabase.auth.getUser()
      if (!user.data.user) {
        throw new Error('User not authenticated')
      }
      
      const settingsPayload = {
        user_id: user.data.user.id,
        score_threshold: newSettings.score_threshold,
        job_limit: newSettings.job_limit,
      }
      
      const { data, error } = await supabase
        .from('user_profiles')
        .upsert(settingsPayload)
        .select()
        .single()
      
      if (error) {
        console.error('❌ Settings save error:', error)
        throw new Error(`Failed to save settings: ${error.message}`)
      }
      
      console.log('✅ Settings saved successfully')
      setSettings(newSettings)
      return { success: true, message: 'Settings saved successfully' }
    } catch (err) {
      console.error('💥 Settings save error:', err)
      throw err
    }
  }

  useEffect(() => {
    fetchSettings()
  }, [])

  return { settings, loading, error, saveSettings, refetch: fetchSettings }
}