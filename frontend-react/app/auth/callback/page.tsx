"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { supabase } from "@/lib/supabase"
import { CheckCircle, AlertCircle, Loader2 } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export default function AuthCallbackPage() {
  const router = useRouter()
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading")
  const [message, setMessage] = useState("")

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Get the current URL parameters
        const hashParams = new URLSearchParams(window.location.hash.substring(1))
        const searchParams = new URLSearchParams(window.location.search)
        
        // Check for error in URL
        const error = hashParams.get("error") || searchParams.get("error")
        const errorDescription = hashParams.get("error_description") || searchParams.get("error_description")
        
        if (error) {
          setStatus("error")
          setMessage(errorDescription || "Email verification failed. Please try again.")
          return
        }

        // Handle the auth callback
        const { data, error: authError } = await supabase.auth.getSession()
        
        if (authError) {
          setStatus("error")
          setMessage("Failed to verify email. Please try again.")
          return
        }

        if (data.session) {
          setStatus("success")
          setMessage("Email verified successfully! You are now logged in.")
          
          // Redirect to dashboard after 2 seconds
          setTimeout(() => {
            window.location.href = "https://job-os.vercel.app/"
          }, 2000)
        } else {
          // Try to exchange the tokens from URL
          const accessToken = hashParams.get("access_token")
          const refreshToken = hashParams.get("refresh_token")
          
          if (accessToken) {
            const { data: session, error: sessionError } = await supabase.auth.setSession({
              access_token: accessToken,
              refresh_token: refreshToken || "",
            })
            
            if (sessionError) {
              setStatus("error")
              setMessage("Failed to establish session. Please try logging in manually.")
              return
            }
            
            if (session) {
              setStatus("success")
              setMessage("Email verified successfully! You are now logged in.")
              
              // Redirect to dashboard after 2 seconds
              setTimeout(() => {
                window.location.href = "https://job-os.vercel.app/"
              }, 2000)
            } else {
              setStatus("error")
              setMessage("Session could not be established. Please try logging in manually.")
            }
          } else {
            setStatus("error")
            setMessage("No authentication tokens found. Please try the verification link again.")
          }
        }
      } catch (error) {
        console.error("Auth callback error:", error)
        setStatus("error")
        setMessage("An unexpected error occurred. Please try again.")
      }
    }

    handleAuthCallback()
  }, [router])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-xl border-0 bg-white/80 backdrop-blur-sm">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4">
            {status === "loading" && (
              <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
            )}
            {status === "success" && (
              <CheckCircle className="h-12 w-12 text-green-600" />
            )}
            {status === "error" && (
              <AlertCircle className="h-12 w-12 text-red-600" />
            )}
          </div>
          <CardTitle className="text-xl">
            {status === "loading" && "Verifying Email..."}
            {status === "success" && "Email Verified!"}
            {status === "error" && "Verification Failed"}
          </CardTitle>
          <CardDescription>
            {status === "loading" && "Please wait while we verify your email address."}
            {status === "success" && "Redirecting you to the dashboard..."}
            {status === "error" && "There was an issue verifying your email."}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          <p className="text-sm text-muted-foreground mb-6">
            {message}
          </p>
          
          {status === "error" && (
            <div className="space-y-3">
              <Button asChild className="w-full">
                <Link href="/auth/login">
                  Try Logging In
                </Link>
              </Button>
              <Button asChild variant="outline" className="w-full">
                <Link href="/auth/register">
                  Register Again
                </Link>
              </Button>
            </div>
          )}
          
          {status === "success" && (
            <Button asChild className="w-full">
              <a href="https://job-os.vercel.app/">
                Go to Dashboard
              </a>
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  )
}