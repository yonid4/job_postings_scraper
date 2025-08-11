"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Brain } from "lucide-react"

interface AIEvaluationProps {
  score?: number
  evaluation?: string
}

export function AIEvaluation({ score, evaluation }: AIEvaluationProps) {
  const getScoreColor = (score: number) => {
    if (score >= 8) return "bg-green-500"
    if (score >= 6) return "bg-yellow-500"
    return "bg-red-500"
  }

  const getScoreLabel = (score: number) => {
    if (score >= 8) return "Excellent Match"
    if (score >= 6) return "Good Match"
    return "Fair Match"
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-blue-500" />
          AI Evaluation
        </CardTitle>
      </CardHeader>
      <CardContent>
        {score && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Match Score</span>
              <Badge className={getScoreColor(score)}>{score.toFixed(1)}/10</Badge>
            </div>
            <Progress value={score * 10} className="h-2" />
            <p className="text-sm text-muted-foreground mt-1">{getScoreLabel(score)}</p>
          </div>
        )}

        {evaluation && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm leading-relaxed">{evaluation}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
