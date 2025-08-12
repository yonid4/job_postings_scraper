"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Search, Clock, Download } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { SearchHistoryCard } from "@/components/search-history/search-history-card"
import { DeleteSearchModal } from "@/components/search-history/delete-search-modal"
import { EmptySearchHistory } from "@/components/search-history/empty-search-history"
import { BaseLayout } from "@/components/base-layout"

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

interface SearchStats {
  totalSearches: number
  totalResults: number
  avgResultsPerSearch: number
  mostSearchedLocation: string
  mostSearchedRole: string
  successRate: number
}

export default function SearchHistoryPage() {
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([])
  const [filteredHistory, setFilteredHistory] = useState<SearchHistoryItem[]>([])
  const [searchStats, setSearchStats] = useState<SearchStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [sortBy, setSortBy] = useState<string>("date-desc")
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [selectedSearchId, setSelectedSearchId] = useState<string | null>(null)

  // Mock data - replace with actual API calls
  useEffect(() => {
    const loadSearchHistory = async () => {
      setIsLoading(true)

      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000))

      const mockHistory: SearchHistoryItem[] = [
        {
          id: "1",
          query: "Senior Frontend Developer",
          location: "San Francisco, CA",
          jobType: "Full-time",
          salaryRange: "$120k - $180k",
          datePosted: "Last 7 days",
          resultsCount: 247,
          searchDate: "2024-01-15T10:30:00Z",
          status: "completed",
          tags: ["React", "TypeScript", "Remote"],
        },
        {
          id: "2",
          query: "Product Manager",
          location: "New York, NY",
          jobType: "Full-time",
          salaryRange: "$100k - $150k",
          datePosted: "Last 24 hours",
          resultsCount: 89,
          searchDate: "2024-01-14T15:45:00Z",
          status: "completed",
          tags: ["SaaS", "B2B", "Growth"],
        },
        {
          id: "3",
          query: "Data Scientist",
          location: "Remote",
          jobType: "Contract",
          salaryRange: "$80k - $120k",
          datePosted: "Last 3 days",
          resultsCount: 156,
          searchDate: "2024-01-13T09:15:00Z",
          status: "completed",
          tags: ["Python", "ML", "AI"],
        },
        {
          id: "4",
          query: "UX Designer",
          location: "Austin, TX",
          jobType: "Full-time",
          salaryRange: "$70k - $110k",
          datePosted: "Last 7 days",
          resultsCount: 0,
          searchDate: "2024-01-12T14:20:00Z",
          status: "failed",
          tags: ["Design Systems", "Figma"],
        },
        {
          id: "5",
          query: "DevOps Engineer",
          location: "Seattle, WA",
          jobType: "Full-time",
          salaryRange: "$110k - $160k",
          datePosted: "Last 24 hours",
          resultsCount: 203,
          searchDate: "2024-01-11T11:00:00Z",
          status: "completed",
          tags: ["AWS", "Kubernetes", "Docker"],
        },
      ]

      const mockStats: SearchStats = {
        totalSearches: 5,
        totalResults: 695,
        avgResultsPerSearch: 139,
        mostSearchedLocation: "San Francisco, CA",
        mostSearchedRole: "Frontend Developer",
        successRate: 80,
      }

      setSearchHistory(mockHistory)
      setSearchStats(mockStats)
      setIsLoading(false)
    }

    loadSearchHistory()
  }, [])

  // Filter and sort search history
  useEffect(() => {
    let filtered = searchHistory

    // Apply search term filter
    if (searchTerm) {
      filtered = filtered.filter(
        (item) =>
          item.query.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.tags.some((tag) => tag.toLowerCase().includes(searchTerm.toLowerCase())),
      )
    }

    // Apply status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter((item) => item.status === statusFilter)
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "date-desc":
          return new Date(b.searchDate).getTime() - new Date(a.searchDate).getTime()
        case "date-asc":
          return new Date(a.searchDate).getTime() - new Date(b.searchDate).getTime()
        case "results-desc":
          return b.resultsCount - a.resultsCount
        case "results-asc":
          return a.resultsCount - b.resultsCount
        default:
          return 0
      }
    })

    setFilteredHistory(filtered)
  }, [searchHistory, searchTerm, statusFilter, sortBy])

  const handleDeleteSearch = (searchId: string) => {
    setSelectedSearchId(searchId)
    setDeleteModalOpen(true)
  }

  const confirmDeleteSearch = () => {
    if (selectedSearchId) {
      setSearchHistory((prev) => prev.filter((item) => item.id !== selectedSearchId))
      setDeleteModalOpen(false)
      setSelectedSearchId(null)
    }
  }

  const handleRepeatSearch = (searchId: string) => {
    const search = searchHistory.find((item) => item.id === searchId)
    if (search) {
      // Navigate to search page with pre-filled parameters
      const searchParams = new URLSearchParams({
        query: search.query,
        location: search.location,
        jobType: search.jobType,
        salaryRange: search.salaryRange,
        datePosted: search.datePosted,
      })
      window.location.href = `/search?${searchParams.toString()}`
    }
  }

  const handleExportHistory = () => {
    const dataStr = JSON.stringify(searchHistory, null, 2)
    const dataUri = "data:application/json;charset=utf-8," + encodeURIComponent(dataStr)

    const exportFileDefaultName = `search-history-${new Date().toISOString().split("T")[0]}.json`

    const linkElement = document.createElement("a")
    linkElement.setAttribute("href", dataUri)
    linkElement.setAttribute("download", exportFileDefaultName)
    linkElement.click()
  }

  if (isLoading) {
    return (
      <BaseLayout title="Search History & Analytics" showSidebar={true}>
        <div className="w-[calc(100vw-16rem)] -ml-6 md:-ml-10 px-6 md:px-10">
          <div className="space-y-6">
          {/* Header Skeleton */}
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-96" />
          </div>

          {/* Stats Cards Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <Card key={i}>
                <CardHeader className="pb-2">
                  <Skeleton className="h-4 w-24" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16 mb-2" />
                  <Skeleton className="h-3 w-32" />
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Search History Skeleton */}
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <Card key={i}>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="flex justify-between items-start">
                      <div className="space-y-2">
                        <Skeleton className="h-6 w-48" />
                        <Skeleton className="h-4 w-32" />
                      </div>
                      <Skeleton className="h-8 w-24" />
                    </div>
                    <div className="flex gap-2">
                      <Skeleton className="h-6 w-16" />
                      <Skeleton className="h-6 w-20" />
                      <Skeleton className="h-6 w-18" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </BaseLayout>
    )
  }

  return (
    <BaseLayout title="Search History & Analytics" showSidebar={true}>
      <div className="w-[calc(100vw-16rem)] -ml-6 md:-ml-10 px-6 md:px-10">
        <div className="space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-2"
        >
          <div className="flex items-center gap-3">
            <Clock className="h-6 w-6 text-blue-600" />
            <p className="text-gray-600">Track your job search progress and analyze your search patterns</p>
          </div>
        </motion.div>

        {/* Statistics Cards */}
        {searchStats && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium opacity-90">Total Searches</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{searchStats.totalSearches}</div>
                <p className="text-xs opacity-75">All time searches</p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-green-500 to-green-600 text-white">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium opacity-90">Total Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{searchStats.totalResults.toLocaleString()}</div>
                <p className="text-xs opacity-75">Jobs found</p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-purple-500 to-purple-600 text-white">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium opacity-90">Avg Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{searchStats.avgResultsPerSearch}</div>
                <p className="text-xs opacity-75">Per search</p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-orange-500 to-orange-600 text-white">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium opacity-90">Success Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{searchStats.successRate}%</div>
                <p className="text-xs opacity-75">Successful searches</p>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Search and Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="flex flex-col sm:flex-row gap-4 items-center justify-between"
        >
          <div className="flex flex-1 gap-4 w-full sm:w-auto">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Search history..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>

            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="date-desc">Newest First</SelectItem>
                <SelectItem value="date-asc">Oldest First</SelectItem>
                <SelectItem value="results-desc">Most Results</SelectItem>
                <SelectItem value="results-asc">Least Results</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button onClick={handleExportHistory} variant="outline" className="flex items-center gap-2 bg-transparent">
            <Download className="h-4 w-4" />
            Export History
          </Button>
        </motion.div>

        {/* Search History List */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="space-y-4"
        >
          {filteredHistory.length === 0 ? (
            <EmptySearchHistory />
          ) : (
            filteredHistory.map((search, index) => (
              <motion.div
                key={search.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <SearchHistoryCard
                  search={search}
                  onDelete={() => handleDeleteSearch(search.id)}
                  onRepeat={() => handleRepeatSearch(search.id)}
                />
              </motion.div>
            ))
          )}
        </motion.div>

        {/* Delete Confirmation Modal */}
        <DeleteSearchModal
          isOpen={deleteModalOpen}
          onClose={() => setDeleteModalOpen(false)}
          onConfirm={confirmDeleteSearch}
          searchQuery={searchHistory.find((s) => s.id === selectedSearchId)?.query || ""}
        />
        </div>
      </div>
    </BaseLayout>
  )
}
