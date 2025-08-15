"use client"

import { useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuth } from "@/hooks/use-auth"

interface RouteGuardProps {
  children: React.ReactNode
}

export function RouteGuard({ children }: RouteGuardProps) {
  const { isAuthenticated, loading, user } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  // Define which routes are public (accessible without authentication)
  const publicRoutes = ["/", "/auth/login", "/auth/register", "/auth/callback", "/forgot_password"]
  
  // Define which routes authenticated users should be redirected from
  const authRedirectRoutes = ["/auth/login", "/auth/register"]

  useEffect(() => {
    if (loading) return // Wait for auth to load

    const isPublicRoute = publicRoutes.includes(pathname)
    const shouldRedirectAuth = authRedirectRoutes.includes(pathname)

    if (!isAuthenticated && !isPublicRoute) {
      // Redirect unauthenticated users to login
      router.push("/auth/login")
    } else if (isAuthenticated && shouldRedirectAuth) {
      // Only redirect authenticated users away from auth pages if their email is verified
      // This prevents interrupting the registration flow for unverified users
      const isEmailVerified = user?.email_verified ?? false
      if (isEmailVerified) {
        router.push("/")
      }
    }
  }, [isAuthenticated, loading, pathname, router, user])

  // Show loading state while auth is being determined
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  // For authenticated users trying to access auth pages, show loading while redirecting
  // Only redirect if email is verified
  const shouldRedirectAuth = authRedirectRoutes.includes(pathname)
  const isEmailVerified = user?.email_verified ?? false
  if (isAuthenticated && shouldRedirectAuth && isEmailVerified) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  // For unauthenticated users trying to access protected pages, show loading while redirecting
  const isPublicRoute = publicRoutes.includes(pathname)
  if (!isAuthenticated && !isPublicRoute) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return <>{children}</>
}