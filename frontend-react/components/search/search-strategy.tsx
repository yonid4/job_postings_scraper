import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Zap, Globe, Clock } from "lucide-react"

interface SearchStrategyProps {
  method: string
  estimatedTime: string
  reason: string
}

export function SearchStrategy({ method, estimatedTime, reason }: SearchStrategyProps) {
  const isApiMode = method.includes("API")

  return (
    <Card className="border-blue-200 bg-blue-50/50">
      <CardContent className="pt-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            {isApiMode ? <Zap className="h-6 w-6 text-green-600" /> : <Globe className="h-6 w-6 text-amber-600" />}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="font-medium">Search Strategy:</span>
              <Badge variant={isApiMode ? "default" : "secondary"} className="text-xs">
                {method}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground mb-2">{reason}</p>
            <div className="flex items-center gap-2 text-sm">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">Estimated time: {estimatedTime}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
