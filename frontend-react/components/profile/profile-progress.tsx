import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, AlertCircle } from "lucide-react"

interface ProfileProgressProps {
  percentage: number
  showLabel?: boolean
}

export function ProfileProgress({ percentage, showLabel = true }: ProfileProgressProps) {
  const getStatusColor = (percentage: number) => {
    if (percentage >= 80) return "bg-green-500"
    if (percentage >= 60) return "bg-blue-500"
    if (percentage >= 40) return "bg-amber-500"
    return "bg-red-500"
  }

  const getStatusText = (percentage: number) => {
    if (percentage >= 80) return "Complete"
    if (percentage >= 60) return "Good"
    if (percentage >= 40) return "Fair"
    return "Incomplete"
  }

  const getStatusIcon = (percentage: number) => {
    if (percentage >= 80) return <CheckCircle className="h-3 w-3" />
    return <AlertCircle className="h-3 w-3" />
  }

  return (
    <div className="flex items-center gap-3">
      {showLabel && (
        <Badge variant={percentage >= 80 ? "default" : "secondary"} className="flex items-center gap-1">
          {getStatusIcon(percentage)}
          {getStatusText(percentage)}
        </Badge>
      )}
      <div className="flex-1">
        <Progress value={percentage} className="h-2" />
      </div>
      {showLabel && <span className="text-sm text-muted-foreground min-w-[3ch]">{percentage}%</span>}
    </div>
  )
}
