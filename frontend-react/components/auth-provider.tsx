"use client"

import type React from "react"
import { createContext, useContext, useState, useEffect } from "react"
import { createClient } from "@supabase/supabase-js"
import type { User as SupabaseUser } from "@supabase/supabase-js"

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ""
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ""
const hasSupabaseConfig = supabaseUrl && supabaseKey && supabaseUrl !== "https://your-project.supabase.co"

const supabase = hasSupabaseConfig ? createClient(supabaseUrl, supabaseKey) : null

interface User {
  id: string
  email: string
  display_name?: string
  avatar_url?: string
  email_verified: boolean
  profile_completed: boolean
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const convertSupabaseUser = (supabaseUser: SupabaseUser): User => {
    return {
      id: supabaseUser.id,
      email: supabaseUser.email || "",
      display_name: supabaseUser.user_metadata?.display_name || supabaseUser.user_metadata?.full_name,
      avatar_url: supabaseUser.user_metadata?.avatar_url,
      email_verified: supabaseUser.email_confirmed_at !== null,
      profile_completed: supabaseUser.user_metadata?.profile_completed || false,
    }
  }

  useEffect(() => {
    // If Supabase is not configured, use localStorage fallback
    if (!supabase) {
      const checkLocalAuth = async () => {
        try {
          const storedUser = localStorage.getItem("user")
          if (storedUser) {
            setUser(JSON.parse(storedUser))
          }
        } catch (error) {
          console.error("Auth check failed:", error)
        } finally {
          setLoading(false)
        }
      }
      checkLocalAuth()
      return
    }

    // Get initial session
    const getInitialSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession()
        if (session?.user) {
          setUser(convertSupabaseUser(session.user))
        }
      } catch (error) {
        console.error("Failed to get initial session:", error)
      } finally {
        setLoading(false)
      }
    }

    getInitialSession()

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (session?.user) {
        setUser(convertSupabaseUser(session.user))
      } else {
        setUser(null)
      }
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  const login = async (email: string, password: string) => {
    if (!supabase) {
      // Fallback to mock authentication for development
      const mockUser: User = {
        id: "1",
        email,
        display_name: "John Doe",
        avatar_url: "/placeholder.svg?height=32&width=32",
        email_verified: true,
        profile_completed: Math.random() > 0.5,
      }
      setUser(mockUser)
      localStorage.setItem("user", JSON.stringify(mockUser))
      return
    }

    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      throw error
    }

    if (data.user) {
      setUser(convertSupabaseUser(data.user))
    }
  }

  const logout = async () => {
    if (!supabase) {
      // Fallback for mock authentication
      setUser(null)
      localStorage.removeItem("user")
      return
    }

    await supabase.auth.signOut()
    setUser(null)
  }

  const value = {
    user,
    isAuthenticated: !!user,
    login,
    logout,
    loading,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
