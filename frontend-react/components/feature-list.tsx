import { CheckCircle } from "lucide-react"

export function FeatureList() {
  const features = [
    "LinkedIn job extraction",
    "AI qualification analysis",
    "Google Sheets integration",
    "Custom rule-based analysis",
  ]

  return (
    <ul className="space-y-2">
      {features.map((feature, index) => (
        <li key={index} className="flex items-center gap-2 text-sm">
          <CheckCircle className="h-4 w-4 text-green-500" />
          <span>{feature}</span>
        </li>
      ))}
    </ul>
  )
}
