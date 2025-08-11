import type React from "react"
import { Suspense } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { BaseLayout } from "@/components/base-layout"
import { HowItWorks } from "@/components/how-it-works"
import { ProTips } from "@/components/pro-tips"
import { QuickStartGuide } from "@/components/quick-start-guide"
import { SystemStatus } from "@/components/system-status"
import { BarChart3, Cog, GraduationCap, Search } from "lucide-react"

export default function DashboardPage() {
  return (
    <BaseLayout title="Dashboard">
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-muted-foreground">Intelligent job matching powered by AI</p>
        </div>
        <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 text-sm px-3 py-1">
          v3.0.0
        </Badge>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <QuickStatCard
          icon={<GraduationCap className="h-6 w-6" />}
          title="Profile"
          description="Manage your qualifications"
          href="/profile"
          buttonText="View Profile"
        />
        <QuickStatCard
          icon={<Search className="h-6 w-6" />}
          title="Job Search"
          description="Analyze job opportunities"
          href="/search"
          buttonText="Start Search"
        />
        <QuickStatCard
          icon={<BarChart3 className="h-6 w-6" />}
          title="Results"
          description="View analysis results"
          href="/results"
          buttonText="View Results"
        />
        <QuickStatCard
          icon={<Cog className="h-6 w-6" />}
          title="Settings"
          description="Configure system"
          href="/settings"
          buttonText="Settings"
        />
      </div>

      <div className="mt-8">
        <HowItWorks />
      </div>

      <div className="grid gap-6 md:grid-cols-2 mt-8">
        <QuickStartGuide />
        <Suspense fallback={<SystemStatusSkeleton />}>
          <SystemStatus />
        </Suspense>
      </div>

      <div className="mt-8">
        <ProTips />
      </div>
    </BaseLayout>
  )
}

function QuickStatCard({
  icon,
  title,
  description,
  href,
  buttonText,
}: {
  icon: React.ReactNode
  title: string
  description: string
  href: string
  buttonText: string
}) {
  return (
    <Card className="overflow-hidden transition-all hover:shadow-md">
      <CardHeader className="pb-2">
        <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-2">
          {icon}
        </div>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardFooter className="pt-2">
        <Button variant="outline" size="sm" className="w-full bg-transparent" asChild>
          <a href={href}>{buttonText}</a>
        </Button>
      </CardFooter>
    </Card>
  )
}

function SystemStatusSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Skeleton className="h-5 w-5 rounded-full" />
          <Skeleton className="h-6 w-32" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 mb-4">
          <Skeleton className="h-4 w-4 rounded-full" />
          <Skeleton className="h-4 w-40" />
        </div>
        <Skeleton className="h-4 w-32 mb-4" />
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center gap-2">
              <Skeleton className="h-4 w-4 rounded-full" />
              <Skeleton className="h-4 w-full" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
