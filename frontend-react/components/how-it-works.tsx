import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Lightbulb, Link, CheckCircle, User } from "lucide-react"

export function HowItWorks() {
  const steps = [
    {
      icon: <User className="h-5 w-5" />,
      title: "Set Your Profile",
      description: "Define your experience, education, and skills",
    },
    {
      icon: <Link className="h-5 w-5" />,
      title: "Add Job URLs",
      description: "Paste LinkedIn search URLs or individual job links",
    },
    {
      icon: <Lightbulb className="h-5 w-5" />,
      title: "AI Analysis",
      description: "AI analyzes each job against your profile",
    },
    {
      icon: <CheckCircle className="h-5 w-5" />,
      title: "Get Results",
      description: "Review qualification scores and manage results",
    },
  ]

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg font-medium">
          <Lightbulb className="h-5 w-5 text-amber-500" />
          How It Works
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-4">
          {steps.map((step, index) => (
            <div key={index} className="flex flex-col items-center text-center">
              <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
                {step.icon}
              </div>
              <h3 className="mb-1 font-medium">
                {index + 1}. {step.title}
              </h3>
              <p className="text-sm text-muted-foreground">{step.description}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
