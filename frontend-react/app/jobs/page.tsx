"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function JobsRedirectPage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect /jobs to /tracker since tracker provides better functionality
    router.replace("/tracker")
  }, [router])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h2 className="text-lg font-semibold mb-2">Redirecting...</h2>
        <p className="text-muted-foreground">Taking you to the Job Tracker page</p>
      </div>
    </div>
  )
}
