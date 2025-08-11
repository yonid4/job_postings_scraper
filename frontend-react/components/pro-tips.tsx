import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Lightbulb } from "lucide-react"

export function ProTips() {
  const tips = [
    {
      title: "Use Search URLs",
      description: "Paste LinkedIn search URLs to analyze multiple jobs at once instead of individual job links.",
    },
    {
      title: "Keep Profile Updated",
      description: "Regularly update your skills and experience to get more accurate qualification scores.",
    },
    {
      title: "Save to Sheets",
      description: "Use the dashboard to keep track of qualified jobs and your application decisions.",
    },
  ]

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg font-medium">
          <Lightbulb className="h-5 w-5 text-amber-500" />
          Pro Tips
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-6 md:grid-cols-3">
          {tips.map((tip, index) => (
            <div key={index} className="flex gap-3">
              <Lightbulb className="h-5 w-5 shrink-0 text-amber-500" />
              <div>
                <h3 className="font-medium">{tip.title}</h3>
                <p className="text-sm text-muted-foreground">{tip.description}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
