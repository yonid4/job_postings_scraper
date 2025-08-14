"use client"

import type React from "react"
import { Suspense } from "react"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { BaseLayout } from "@/components/base-layout"
import { HowItWorks } from "@/components/how-it-works"
import { ProTips } from "@/components/pro-tips"
import { QuickStartGuide } from "@/components/quick-start-guide"
import { SystemStatus } from "@/components/system-status"
import { BarChart3, Cog, GraduationCap, Search, ArrowRight, CheckCircle } from "lucide-react"
import { useAuth } from "@/hooks/use-auth"

export default function HomePage() {
  const { isAuthenticated } = useAuth()

  if (isAuthenticated) {
    return <AuthenticatedDashboard />
  }

  return <LandingPage />
}

function AuthenticatedDashboard() {
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

function LandingPage() {
  return (
    <BaseLayout title="" showSidebar={false}>
      <div className="max-w-6xl mx-auto px-6">
        {/* Hero Section */}
        <div className="text-center py-12 lg:py-20">
          <Badge variant="outline" className="mb-4 bg-emerald-50 text-emerald-700 border-emerald-200">
            AI-Powered Job Matching v3.0.0
          </Badge>
          <h1 className="text-4xl lg:text-6xl font-bold tracking-tight mb-6">
            Find Your Perfect Job with{" "}
            <span className="text-primary">AI Intelligence</span>
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            Automated job search and qualification screening platform that matches you 
            with opportunities based on your skills and experience.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button size="lg" asChild>
              <Link href="/auth/register">
                Get Started <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/auth/login">Sign In</Link>
            </Button>
          </div>
        </div>

        {/* Features Section */}
        <div className="grid gap-8 md:grid-cols-3 mb-16">
          <FeatureCard
            icon={<Search className="h-8 w-8" />}
            title="Smart Job Search"
            description="AI-powered search that finds jobs matching your qualifications and preferences"
            features={["LinkedIn integration", "Advanced filtering", "Real-time results"]}
          />
          <FeatureCard
            icon={<GraduationCap className="h-8 w-8" />}
            title="Qualification Analysis"
            description="Intelligent screening that evaluates your fit for each position"
            features={["Skills assessment", "Experience matching", "Personalized scoring"]}
          />
          <FeatureCard
            icon={<BarChart3 className="h-8 w-8" />}
            title="Application Tracking"
            description="Comprehensive dashboard to manage your job application pipeline"
            features={["Progress monitoring", "Application status", "Performance analytics"]}
          />
        </div>
      </div>

      <div className="bg-muted/30 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <HowItWorks />
        </div>
      </div>
    </BaseLayout>
  )
}

function FeatureCard({ 
  icon, 
  title, 
  description, 
  features 
}: { 
  icon: React.ReactNode
  title: string
  description: string
  features: string[]
}) {
  return (
    <Card className="text-center">
      <CardHeader>
        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-primary mx-auto mb-4">
          {icon}
        </div>
        <CardTitle className="text-xl">{title}</CardTitle>
        <CardDescription className="text-base">{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {features.map((feature, index) => (
            <li key={index} className="flex items-center text-sm text-muted-foreground">
              <CheckCircle className="h-4 w-4 text-primary mr-2 flex-shrink-0" />
              {feature}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
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
