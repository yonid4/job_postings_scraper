import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

export function useJobs() {
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setLoading(true)
        console.log('🔍 Checking Supabase connection...')
        
        // Check if Supabase is configured
        if (!supabase) {
          console.warn('⚠️ Supabase not configured - using placeholder credentials')
          console.log('💡 To connect to Supabase, set environment variables in frontend-react/.env.local:')
          console.log('   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url')
          console.log('   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key')
          setError('Supabase not configured. Using placeholder credentials for development.')
          setJobs([]) // Could add mock data here for development
          return
        }
        
        console.log('📡 Fetching jobs from Supabase...')
        const { data, error } = await supabase
          .from('jobs')
          .select('*')
          .order('created_at', { ascending: false })
        
        console.log('📊 Supabase response:', { data, error, count: data?.length })
        
        if (error) {
          console.error('❌ Supabase error:', error)
          setError(`Supabase error: ${error.message}`)
        } else {
          console.log('✅ Jobs fetched successfully:', data?.length || 0)
          setJobs(data || [])
          setError(null)
        }
      } catch (err) {
        console.error('💥 Fetch error:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchJobs()
  }, [])

  return { jobs, loading, error }
}
