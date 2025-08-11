import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Rocket, User, Cog, Search } from "lucide-react"

export function QuickStartGuide() {
  const steps = [
    {
      icon: <User className="h-4 w-4" />,
      title: "Complete Your Profile",
      description: "Set up your experience, education, and skills to get accurate matches.",
      action: {
        text: "Set Up Profile",
        href: "/profile",
      },
    },
    {
      icon: <Cog className="h-4 w-4" />,
      title: "Configure Settings",
      description: "Add your Gemini API key for full functionality.",
      action: {
        text: "Configure Settings",
        href: "/settings",
      },
    },
    {
      icon: <Search className="h-4 w-4" />,
      title: "Start Job Search",
      description: "Paste LinkedIn search URLs to analyze multiple jobs at once.",
      action: {
        text: "Start Search",
        href: "/search",
      },
    },
  ]

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg font-medium">
          <Rocket className="h-5 w-5 text-blue-500" />
          Quick Start
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div key={index} className="space-y-2">
              <h3 className="font-medium">{step.title}</h3>
              <p className="text-sm text-muted-foreground">{step.description}</p>
              <Button variant={index === 0 ? "default" : "outline"} size="sm" className="mt-1" asChild>
                <a href={step.action.href}>
                  {step.icon}
                  <span className="ml-2">{step.action.text}</span>
                </a>
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
