"use client"

import { motion } from "framer-motion"
import { Search, TrendingUp, Clock, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import Link from "next/link"

export function EmptySearchHistory() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex items-center justify-center min-h-[400px]"
    >
      <Card className="max-w-md w-full text-center border-0 bg-white/80 backdrop-blur-sm shadow-lg">
        <CardContent className="p-8 space-y-6">
          {/* Icon */}
          <div className="mx-auto w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <Clock className="h-10 w-10 text-white" />
          </div>

          {/* Title and Description */}
          <div className="space-y-2">
            <h3 className="text-xl font-semibold text-gray-900">No Search History Yet</h3>
            <p className="text-gray-600 text-sm leading-relaxed">
              Start searching for jobs to see your search history and analytics here. We'll track your searches to help
              you find patterns and improve your job hunt.
            </p>
          </div>

          {/* Features List */}
          <div className="space-y-3 text-left">
            <div className="flex items-center gap-3 text-sm text-gray-600">
              <div className="p-1 bg-blue-100 rounded">
                <Search className="h-3 w-3 text-blue-600" />
              </div>
              <span>Track all your job searches</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-600">
              <div className="p-1 bg-green-100 rounded">
                <TrendingUp className="h-3 w-3 text-green-600" />
              </div>
              <span>Analyze search patterns and success rates</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-600">
              <div className="p-1 bg-purple-100 rounded">
                <Clock className="h-3 w-3 text-purple-600" />
              </div>
              <span>Easily repeat successful searches</span>
            </div>
          </div>

          {/* Call to Action */}
          <div className="pt-4">
            <Link href="/search">
              <Button className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white">
                Start Your First Search
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>

          {/* Additional Help */}
          <div className="text-xs text-gray-500">
            Need help getting started?{" "}
            <Link href="/help" className="text-blue-600 hover:underline">
              View our search guide
            </Link>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
