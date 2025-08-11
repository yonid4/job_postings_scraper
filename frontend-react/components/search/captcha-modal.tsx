"use client"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Shield, Play, X, Info } from "lucide-react"

interface CaptchaModalProps {
  isOpen: boolean
  onClose: () => void
  onContinue: () => void
  data: any
}

export function CaptchaModal({ isOpen, onClose, onContinue, data }: CaptchaModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-amber-600" />
            Security Verification Required
          </DialogTitle>
          <DialogDescription>
            LinkedIn has detected automated access and requires manual verification.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <p>A browser window should have opened with a security challenge. Please complete the following steps:</p>

          <ol className="list-decimal list-inside space-y-2 text-sm">
            <li>Look for the browser window that opened automatically</li>
            <li>Complete the security challenge (CAPTCHA, puzzle, or verification)</li>
            <li>Wait for the page to load successfully</li>
            <li>Click the "Continue Analysis" button below</li>
          </ol>

          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              <strong>Note:</strong> This is a temporary security check. Once completed, your search will continue
              automatically.
            </AlertDescription>
          </Alert>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            <X className="w-4 h-4 mr-2" />
            Cancel
          </Button>
          <Button onClick={onContinue}>
            <Play className="w-4 h-4 mr-2" />
            Continue Analysis
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
