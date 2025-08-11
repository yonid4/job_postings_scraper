import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { HelpCircle, Search, Lightbulb, Info, Zap, Globe, Shield, Rocket } from "lucide-react"

export function SearchSidebar() {
  return (
    <div className="space-y-6">
      {/* How to Use */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <HelpCircle className="h-4 w-4" />
            How to Use
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-5 h-5 bg-primary text-primary-foreground rounded-full text-xs flex items-center justify-center">
                1
              </span>
              <span>Select a job website (currently LinkedIn)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-5 h-5 bg-primary text-primary-foreground rounded-full text-xs flex items-center justify-center">
                2
              </span>
              <span>Enter your job title or keywords</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-5 h-5 bg-primary text-primary-foreground rounded-full text-xs flex items-center justify-center">
                3
              </span>
              <span>Configure your search filters (optional)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-5 h-5 bg-primary text-primary-foreground rounded-full text-xs flex items-center justify-center">
                4
              </span>
              <span>Set your qualification threshold</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-5 h-5 bg-primary text-primary-foreground rounded-full text-xs flex items-center justify-center">
                5
              </span>
              <span>Click "Analyze Jobs"</span>
            </li>
          </ol>

          <Alert className="mt-4">
            <Lightbulb className="h-4 w-4" />
            <AlertDescription className="text-sm">
              <strong>Pro Tip:</strong> Use the filters to narrow down your search by location, experience level, job
              type, and work arrangement. The qualification threshold determines which jobs are shown in your results.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* Search Examples */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Search className="h-4 w-4" />
            Search Examples
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium text-sm mb-2">Job Title Examples</h4>
            <p className="text-xs text-muted-foreground mb-2">Try these popular job titles:</p>
            <div className="space-y-1">
              <Badge variant="outline" className="text-xs">
                Software Engineer
              </Badge>
              <br />
              <Badge variant="outline" className="text-xs">
                Data Scientist
              </Badge>
              <br />
              <Badge variant="outline" className="text-xs">
                Product Manager
              </Badge>
              <br />
              <Badge variant="outline" className="text-xs">
                Python Developer
              </Badge>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-sm mb-2">Skill Keywords</h4>
            <p className="text-xs text-muted-foreground mb-2">Add specific skills:</p>
            <div className="space-y-1">
              <Badge variant="outline" className="text-xs">
                React, AWS, Docker
              </Badge>
              <br />
              <Badge variant="outline" className="text-xs">
                Machine Learning, Python
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Search Optimization Features */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Rocket className="h-4 w-4" />
            Search Optimization
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Zap className="h-4 w-4 text-green-600" />
              <h4 className="font-medium text-sm text-green-700">Fast API Mode</h4>
            </div>
            <p className="text-xs text-muted-foreground">
              For basic searches (keywords + location only), we use a fast API-only approach that completes in 2-5
              seconds with minimal resource usage.
            </p>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-2">
              <Globe className="h-4 w-4 text-amber-600" />
              <h4 className="font-medium text-sm text-amber-700">WebDriver Mode</h4>
            </div>
            <p className="text-xs text-muted-foreground">
              For advanced searches with filters (date, experience, job type, etc.), we use WebDriver for precise
              filtering, taking 10-30 seconds.
            </p>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-2">
              <Shield className="h-4 w-4 text-blue-600" />
              <h4 className="font-medium text-sm text-blue-700">CAPTCHA Handling</h4>
            </div>
            <p className="text-xs text-muted-foreground">
              If LinkedIn requires verification, we'll pause and guide you through solving the challenge, then continue
              automatically.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Analysis Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Info className="h-4 w-4" />
            Analysis Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Ready to analyze jobs</p>
        </CardContent>
      </Card>
    </div>
  )
}
