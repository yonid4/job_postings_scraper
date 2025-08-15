import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // URL of your Railway-deployed scraping service
    const SCRAPING_SERVICE_URL = process.env.SCRAPING_SERVICE_URL || 'http://localhost:8000'
    
    const response = await fetch(`${SCRAPING_SERVICE_URL}/api/jobs/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      // Add timeout for scraping operations
      signal: AbortSignal.timeout(60000) // 60 seconds
    })
    
    if (!response.ok) {
      throw new Error(`Scraping service error: ${response.status}`)
    }
    
    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Scraping service unavailable. Please try again later.',
        requires_manual_intervention: true
      },
      { status: 500 }
    )
  }
}