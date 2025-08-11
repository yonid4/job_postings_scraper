"use client"

import { motion } from "framer-motion"
import {
  Calendar,
  MapPin,
  Briefcase,
  DollarSign,
  Search,
  RefreshCw,
  Trash2,
  ExternalLink,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { formatDistanceToNow } from "date-fns"

interface SearchHistoryItem {
  id: string
  query: string
  location: string
  jobType: string
  salaryRange: string
  datePosted: string
  resultsCount: number
  searchDate: string
  status: "completed" | "in-progress" | "failed"
  tags: string[]
}

interface SearchHistoryCardProps {
  search: SearchHistoryItem
  onDelete: () => void
  onRepeat: () => void
}

export function SearchHistoryCard({ search, onDelete, onRepeat }: SearchHistoryCardProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "failed":
        return <XCircle className="h-4 w-4 text-red-600" />
      case "in-progress":
        return <AlertCircle className="h-4 w-4 text-yellow-600" />
      default:
        return null
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800 border-green-200"
      case "failed":
        return "bg-red-100 text-red-800 border-red-200"
      case "in-progress":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  return (
    <motion.div whileHover={{ y: -2 }} transition={{ duration: 0.2 }}>
      <Card className="hover:shadow-lg transition-all duration-200 border-0 bg-white/80 backdrop-blur-sm">
        <CardContent className="p-6">
          <div className="space-y-4">
            {/* Header */}
            <div className="flex items-start justify-between">
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <Search className="h-5 w-5 text-blue-600" />
                    {search.query}
                  </h3>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {formatDistanceToNow(new Date(search.searchDate), { addSuffix: true })}
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      {search.location}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Badge className={`${getStatusColor(search.status)} flex items-center gap-1`}>
                  {getStatusIcon(search.status)}
                  {search.status}
                </Badge>
                <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                  {search.resultsCount} results
                </Badge>
              </div>
            </div>

            {/* Search Details */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 py-3 border-t border-gray-100">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Briefcase className="h-4 w-4" />
                <span>{search.jobType}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <DollarSign className="h-4 w-4" />
                <span>{search.salaryRange}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Calendar className="h-4 w-4" />
                <span>{search.datePosted}</span>
              </div>
            </div>

            {/* Tags */}
            {search.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {search.tags.map((tag, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-gray-100">
              <div className="flex items-center gap-2">
                <Button
                  onClick={onRepeat}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2 hover:bg-blue-50 hover:border-blue-200 bg-transparent"
                >
                  <RefreshCw className="h-4 w-4" />
                  Repeat Search
                </Button>
                <Button variant="outline" size="sm" className="flex items-center gap-2 hover:bg-gray-50 bg-transparent">
                  <ExternalLink className="h-4 w-4" />
                  View Results
                </Button>
              </div>

              <Button
                onClick={onDelete}
                variant="ghost"
                size="sm"
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
