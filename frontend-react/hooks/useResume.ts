import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

export interface ResumeStatus {
  has_resume: boolean
  filename?: string
  file_type?: string
  file_size?: number
  uploaded_at?: string
  is_processed?: boolean
}

export function useResume() {
  const [resumeStatus, setResumeStatus] = useState<ResumeStatus>({
    has_resume: false,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchResumeStatus = async () => {
    try {
      setLoading(true)
      console.log('🔍 Checking Supabase connection for resume...')
      
      if (!supabase) {
        console.warn('⚠️ Supabase not configured - no resume status')
        setError('Supabase not configured. Cannot fetch resume status.')
        setResumeStatus({ has_resume: false })
        return
      }
      
      console.log('📡 Fetching resume status from Supabase...')
      const { data, error: fetchError } = await supabase
        .from('user_resume')
        .select('*')
        .eq('is_active', true)
        .single()
      
      console.log('📊 Supabase resume response:', { data, fetchError })
      
      if (fetchError) {
        if (fetchError.code === 'PGRST116') {
          // No resume found
          console.log('📝 No resume found')
          setResumeStatus({ has_resume: false })
          setError(null)
        } else {
          console.error('❌ Supabase resume error:', fetchError)
          setError(`Resume fetch error: ${fetchError.message}`)
          setResumeStatus({ has_resume: false })
        }
      } else {
        console.log('✅ Resume status fetched successfully')
        setResumeStatus({
          has_resume: true,
          filename: data.filename,
          file_type: data.file_type,
          file_size: data.file_size,
          uploaded_at: data.uploaded_at,
          is_processed: data.is_processed,
        })
        setError(null)
      }
    } catch (err) {
      console.error('💥 Resume fetch error:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
      setResumeStatus({ has_resume: false })
    } finally {
      setLoading(false)
    }
  }

  const uploadResume = async (file: File) => {
    try {
      if (!supabase) {
        throw new Error('Supabase not configured')
      }
      
      const user = await supabase.auth.getUser()
      if (!user.data.user) {
        throw new Error('User not authenticated')
      }
      
      console.log('📤 Uploading resume to Supabase Storage...')
      
      // Upload file to Supabase Storage
      const fileName = `${user.data.user.id}/${Date.now()}_${file.name}`
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('resumes')
        .upload(fileName, file)
      
      if (uploadError) {
        console.error('❌ Storage upload error:', uploadError)
        throw new Error(`Upload failed: ${uploadError.message}`)
      }
      
      console.log('✅ File uploaded to storage:', uploadData.path)
      
      // Save resume record to database
      const resumePayload = {
        user_id: user.data.user.id,
        filename: file.name,
        file_path: uploadData.path,
        storage_path: uploadData.path,
        file_hash: `${Date.now()}_${file.name}`, // Simple hash for now
        file_size: file.size,
        file_type: file.type.includes('pdf') ? 'pdf' : 'docx',
        is_active: true,
      }
      
      // First, deactivate any existing resumes
      await supabase
        .from('user_resume')
        .update({ is_active: false })
        .eq('user_id', user.data.user.id)
      
      // Insert new resume record
      const { data, error } = await supabase
        .from('user_resume')
        .insert(resumePayload)
        .select()
        .single()
      
      if (error) {
        console.error('❌ Resume record save error:', error)
        throw new Error(`Failed to save resume record: ${error.message}`)
      }
      
      console.log('✅ Resume uploaded successfully')
      await fetchResumeStatus() // Refresh status
      return { success: true, message: 'Resume uploaded successfully' }
    } catch (err) {
      console.error('💥 Resume upload error:', err)
      throw err
    }
  }

  const deleteResume = async () => {
    try {
      if (!supabase) {
        throw new Error('Supabase not configured')
      }
      
      const user = await supabase.auth.getUser()
      if (!user.data.user) {
        throw new Error('User not authenticated')
      }
      
      console.log('🗑️ Deleting resume...')
      
      // Get current resume info
      const { data: resumeData } = await supabase
        .from('user_resume')
        .select('storage_path')
        .eq('user_id', user.data.user.id)
        .eq('is_active', true)
        .single()
      
      if (resumeData) {
        // Delete from storage
        await supabase.storage
          .from('resumes')
          .remove([resumeData.storage_path])
        
        // Delete from database
        await supabase
          .from('user_resume')
          .delete()
          .eq('user_id', user.data.user.id)
          .eq('is_active', true)
      }
      
      console.log('✅ Resume deleted successfully')
      await fetchResumeStatus() // Refresh status
      return { success: true, message: 'Resume deleted successfully' }
    } catch (err) {
      console.error('💥 Resume delete error:', err)
      throw err
    }
  }

  useEffect(() => {
    fetchResumeStatus()
  }, [])

  return { 
    resumeStatus, 
    loading, 
    error, 
    uploadResume, 
    deleteResume, 
    refetch: fetchResumeStatus 
  }
}