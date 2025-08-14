"use client"

import { useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuth } from "@/hooks/use-auth"

interface RouteGuardProps {
  children: React.ReactNode
}

export function RouteGuard({ children }: RouteGuardProps) {
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  // Define which routes are public (accessible without authentication)
  const publicRoutes = ["/", "/auth/login", "/auth/register", "/forgot_password"]
  
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
      // Redirect authenticated users away from login/register
      router.push("/")
    }
  }, [isAuthenticated, loading, pathname, router])

  // Show loading state while auth is being determined
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  // For authenticated users trying to access auth pages, show loading while redirecting
  const shouldRedirectAuth = authRedirectRoutes.includes(pathname)
  if (isAuthenticated && shouldRedirectAuth) {
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