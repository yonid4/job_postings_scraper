import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { TrendingUp, Users, MessageSquare, Calendar, Award, Target } from "lucide-react"
import type { AnalyticsData } from "@/app/tracker/page"

interface AnalyticsCardsProps {
  analytics: AnalyticsData | null
  isLoading: boolean
}

export function AnalyticsCards({ analytics, isLoading }: AnalyticsCardsProps) {
  if (isLoading) {
    return <AnalyticsCardsSkeleton />
  }

  if (!analytics) {
    return null
  }

  const cards = [
    {
      title: "Total Jobs",
      value: analytics.total_jobs_tracked,
      icon: Target,
      color: "text-blue-600",
      bgColor: "bg-blue-50",
    },
    {
      title: "Applications",
      value: analytics.applications_submitted,
      icon: Users,
      color: "text-green-600",
      bgColor: "bg-green-50",
    },
    {
      title: "Response Rate",
      value: `${analytics.response_rate.toFixed(1)}%`,
      icon: TrendingUp,
      color: "text-purple-600",
      bgColor: "bg-purple-50",
    },
    {
      title: "Responses",
      value: analytics.responses_received,
      icon: MessageSquare,
      color: "text-amber-600",
      bgColor: "bg-amber-50",
    },
    {
      title: "Interviews",
      value: analytics.interviews_scheduled,
      icon: Calendar,
      color: "text-indigo-600",
      bgColor: "bg-indigo-50",
    },
    {
      title: "Offers",
      value: analytics.offers_received,
      icon: Award,
      color: "text-emerald-600",
      bgColor: "bg-emerald-50",
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card, index) => (
        <Card key={index} className="hover:shadow-md transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold">{card.value}</p>
                <p className="text-sm text-muted-foreground">{card.title}</p>
              </div>
              <div className={`p-2 rounded-full ${card.bgColor}`}>
                <card.icon className={`h-4 w-4 ${card.color}`} />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function AnalyticsCardsSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {Array.from({ length: 6 }).map((_, index) => (
        <Card key={index}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <Skeleton className="h-8 w-12" />
                <Skeleton className="h-4 w-16" />
              </div>
              <Skeleton className="h-8 w-8 rounded-full" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
