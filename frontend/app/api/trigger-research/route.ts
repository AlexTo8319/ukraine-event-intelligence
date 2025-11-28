import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    console.log('🔍 Triggering research agent...')
    
    // Check if we're in a server environment that can run Python
    // For Vercel, we'll use GitHub Actions API instead
    const isVercel = process.env.VERCEL === '1'
    
    // Try GitHub Actions first (works for both Vercel and local)
    const githubToken = process.env.GITHUB_TOKEN
    const repo = process.env.GITHUB_REPO || 'AlexTo8319/ukraine-event-intelligence'
    const workflowFile = 'daily-research.yml'
    
    if (githubToken) {
      try {
        console.log('Triggering GitHub Actions workflow...')
        const response = await fetch(
          `https://api.github.com/repos/${repo}/actions/workflows/${workflowFile}/dispatches`,
          {
            method: 'POST',
            headers: {
              'Authorization': `token ${githubToken}`,
              'Accept': 'application/vnd.github.v3+json',
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              ref: 'main',
            }),
          }
        )
        
        if (!response.ok) {
          const errorText = await response.text()
          console.error('GitHub API error:', response.status, errorText)
          
          // Return error response
          return NextResponse.json({
            success: false,
            error: 'Failed to trigger GitHub Actions workflow',
            details: errorText.substring(0, 200),
            status: response.status,
          }, { status: response.status })
        }
        
        return NextResponse.json({
          success: true,
          message: 'Research agent triggered via GitHub Actions. Events will update in 2-3 minutes.',
          method: 'github-actions',
        })
      } catch (error: any) {
        console.error('Error triggering GitHub Actions:', error)
        return NextResponse.json({
          success: false,
          error: 'Failed to trigger research',
          details: error.message || String(error),
        }, { status: 500 })
      }
    } else {
      // No GitHub token available
      if (isVercel) {
        return NextResponse.json({
          success: false,
          error: 'GITHUB_TOKEN not configured',
          message: 'Please add GITHUB_TOKEN to Vercel environment variables to enable manual research triggers.',
        }, { status: 503 })
      }
      
      // Local development: Try direct execution
      try {
        const { exec } = await import('child_process')
        const { promisify } = await import('util')
        const execAsync = promisify(exec)
        const path = await import('path')
        
        const projectRoot = path.join(process.cwd(), '../..')
        
        const { stdout, stderr } = await execAsync(
          `cd "${projectRoot}/backend" && python3 -m agent.research_agent`,
          {
            timeout: 300000, // 5 minutes timeout
            maxBuffer: 10 * 1024 * 1024, // 10MB buffer
          }
        )
        
        console.log('Research agent output:', stdout)
        if (stderr) {
          console.error('Research agent stderr:', stderr)
        }
        
        return NextResponse.json({
          success: true,
          message: 'Research agent completed successfully!',
          method: 'direct',
          output: stdout.substring(0, 500), // First 500 chars of output
        })
      } catch (error: any) {
        console.error('Error running research agent:', error)
        return NextResponse.json({
          success: false,
          error: 'Failed to run research agent',
          details: error.message || String(error),
          suggestion: 'Make sure Python dependencies are installed: pip install -r backend/requirements.txt'
        }, { status: 500 })
      }
    }
  } catch (error: any) {
    console.error('Unexpected error:', error)
    return NextResponse.json({
      success: false,
      error: 'Unexpected error',
      details: error.message || String(error),
    }, { status: 500 })
  }
}

// Allow GET for status check
export async function GET() {
  return NextResponse.json({
    status: 'ready',
    message: 'Research trigger endpoint is available',
  })
}
