import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // URL of your Render-deployed scraping service
    const SCRAPING_SERVICE_URL = process.env.SCRAPING_SERVICE_URL || 'http://localhost:8000'
    
    console.log(`🔗 Attempting to connect to scraping service: ${SCRAPING_SERVICE_URL}/api/jobs/search`)
    console.log('📋 Request payload:', JSON.stringify(body, null, 2))
    
    const response = await fetch(`${SCRAPING_SERVICE_URL}/api/jobs/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      // Add timeout for scraping operations
      signal: AbortSignal.timeout(60000) // 60 seconds
    })
    
    console.log(`📊 Response status: ${response.status} ${response.statusText}`)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error(`❌ Scraping service error: ${response.status} - ${errorText}`)
      throw new Error(`Scraping service error: ${response.status} - ${errorText}`)
    }
    
    const data = await response.json()
    console.log(`✅ Response data: success=${data.success}, jobs=${data.jobs_count || 0}`)
    
    if (!data.success) {
      console.log(`⚠️  Backend returned failure: ${data.error}`)
    }
    
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('API Error:', error)
    
    // Provide more specific error messages based on the error type
    let errorMessage = 'Unknown error occurred'
    let requiresIntervention = false
    
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        errorMessage = 'Request timed out. The scraping service took too long to respond.'
      } else if (error.message.includes('fetch')) {
        errorMessage = `Connection error: Cannot reach scraping service at ${process.env.SCRAPING_SERVICE_URL || 'http://localhost:8000'}`
      } else if (error.message.includes('Scraping service error')) {
        errorMessage = `Scraping service returned an error: ${error.message}`
        // Only set requires_manual_intervention for actual scraping issues, not connection issues
        requiresIntervention = true
      } else {
        errorMessage = error.message
      }
    }
    
    return NextResponse.json(
      { 
        success: false, 
        error: errorMessage,
        ...(requiresIntervention && { requires_manual_intervention: true })
      },
      { status: 500 }
    )
  }
}