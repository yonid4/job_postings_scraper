"use client"

import { useState, useEffect } from "react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { CheckCircle, AlertTriangle, Info, X, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

export interface FlashMessageData {
  id: string
  type: "success" | "error" | "warning" | "info"
  message: string
  duration?: number
}

// Global flash message store
let flashMessages: FlashMessageData[] = []
let listeners: (() => void)[] = []

export const flashMessage = {
  show: (message: string, type: FlashMessageData["type"] = "info", duration = 5000) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newMessage: FlashMessageData = { id, type, message, duration }
    flashMessages = [...flashMessages, newMessage]
    listeners.forEach((listener) => listener())

    if (duration > 0) {
      setTimeout(() => {
        flashMessage.dismiss(id)
      }, duration)
    }
  },
  dismiss: (id: string) => {
    flashMessages = flashMessages.filter((msg) => msg.id !== id)
    listeners.forEach((listener) => listener())
  },
  clear: () => {
    flashMessages = []
    listeners.forEach((listener) => listener())
  },
}

export function FlashMessage() {
  const [messages, setMessages] = useState<FlashMessageData[]>([])

  useEffect(() => {
    const updateMessages = () => setMessages([...flashMessages])
    listeners.push(updateMessages)
    updateMessages()

    return () => {
      listeners = listeners.filter((listener) => listener !== updateMessages)
    }
  }, [])

  if (messages.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-md">
      {messages.map((message) => (
        <FlashMessageItem key={message.id} message={message} onDismiss={flashMessage.dismiss} />
      ))}
    </div>
  )
}

function FlashMessageItem({
  message,
  onDismiss,
}: {
  message: FlashMessageData
  onDismiss: (id: string) => void
}) {
  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  }

  const Icon = icons[message.type]

  return (
    <Alert
      className={cn(
        "animate-in slide-in-from-right-full duration-300",
        message.type === "success" && "border-green-200 bg-green-50 text-green-800",
        message.type === "error" && "border-red-200 bg-red-50 text-red-800",
        message.type === "warning" && "border-amber-200 bg-amber-50 text-amber-800",
        message.type === "info" && "border-blue-200 bg-blue-50 text-blue-800",
      )}
    >
      <Icon className="h-4 w-4" />
      <AlertDescription className="flex items-center justify-between">
        <span>{message.message}</span>
        <Button variant="ghost" size="sm" className="h-auto p-1 ml-2" onClick={() => onDismiss(message.id)}>
          <X className="h-3 w-3" />
        </Button>
      </AlertDescription>
    </Alert>
  )
}
