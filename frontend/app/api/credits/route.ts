import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // For Tavily, we'll track usage manually since they don't provide a credits API
    // We'll estimate based on search queries (14 queries * 10 results = ~140 credits per run)
    // Free tier: 1,000 credits/month
    
    // For OpenAI, we could track usage, but for now we'll just show estimated costs
    // gpt-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
    
    // Since we can't get real-time credits from Tavily API, we'll return estimated usage
    // This would need to be tracked in a database or file
    const tavilyCredits = {
      used: 0, // This should be tracked in a database/file
      remaining: 1000, // Free tier limit
      estimatedPerRun: 140, // 14 queries * 10 results
    }
    
    const openaiUsage = {
      estimatedPerRun: 0.05, // Estimated $0.05 per research run
    }
    
    return NextResponse.json({
      tavily: {
        used: tavilyCredits.used,
        remaining: tavilyCredits.remaining,
        estimatedPerRun: tavilyCredits.estimatedPerRun,
        freeTierLimit: 1000,
      },
      openai: {
        estimatedPerRun: openaiUsage.estimatedPerRun,
      },
    })
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to fetch credits' },
      { status: 500 }
    )
  }
}


