"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { InfoIcon, CheckCircle, AlertCircle } from "lucide-react"

export function SystemStatus() {
  const [status, setStatus] = useState<"loading" | "online" | "offline">("loading")
  const [lastChecked, setLastChecked] = useState<string>("")

  useEffect(() => {
    const checkStatus = async () => {
      try {
        // In a real app, this would be a fetch to your API
        // await fetch('/api/health')

        // Simulating API call
        await new Promise((resolve) => setTimeout(resolve, 1000))

        setStatus("online")
        setLastChecked(new Date().toLocaleTimeString())
      } catch (error) {
        setStatus("offline")
        setLastChecked(new Date().toLocaleTimeString())
      }
    }

    checkStatus()
  }, [])

  const features = [
    { name: "LinkedIn job extraction", available: true },
    { name: "AI qualification analysis", available: true },
    { name: "Google Sheets integration", available: true },
    { name: "Custom rule-based analysis", available: true },
  ]

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg font-medium">
          <InfoIcon className="h-5 w-5 text-blue-500" />
          System Status
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          {status === "loading" && (
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <span>Checking system status...</span>
            </div>
          )}

          {status === "online" && (
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span>System is running</span>
            </div>
          )}

          {status === "offline" && (
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-amber-500" />
              <span>System status unknown</span>
            </div>
          )}

          {lastChecked && <p className="mt-1 text-xs text-muted-foreground">Last checked: {lastChecked}</p>}
        </div>

        <div>
          <h3 className="mb-2 text-sm font-medium">Features Available:</h3>
          <ul className="space-y-2">
            {features.map((feature, index) => (
              <li key={index} className="flex items-center gap-2 text-sm">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span>{feature.name}</span>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}
