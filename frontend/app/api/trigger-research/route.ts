import { NextRequest, NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import path from 'path'

const execAsync = promisify(exec)

export async function POST(request: NextRequest) {
  try {
    // Get the project root (go up from frontend/app/api)
    const projectRoot = path.join(process.cwd(), '../..')
    const scriptPath = path.join(projectRoot, 'backend', 'agent', 'research_agent.py')
    
    console.log('🔍 Triggering research agent...')
    console.log('Script path:', scriptPath)
    
    // Check if we're in a server environment that can run Python
    // For Vercel, we'll use GitHub Actions API instead
    const isVercel = process.env.VERCEL === '1'
    
    // Try GitHub Actions first (works for both Vercel and local)
    const githubToken = process.env.GITHUB_TOKEN || process.env.NEXT_PUBLIC_GITHUB_TOKEN
    const repo = process.env.GITHUB_REPO || 'AlexTo8319/ukraine-event-intelligence'
    
    if (githubToken) {
      try {
        console.log('Triggering GitHub Actions workflow...')
        const response = await fetch(
          `https://api.github.com/repos/${repo}/actions/workflows/daily-research.yml/dispatches`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${githubToken}`,
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
          // Fall through to try direct execution if GitHub fails
        } else {
          return NextResponse.json({
            success: true,
            message: 'Research agent triggered via GitHub Actions. Events will update in 2-3 minutes.',
            method: 'github-actions',
          })
        }
      } catch (error: any) {
        console.error('Error triggering GitHub Actions:', error)
        // Fall through to try direct execution
      }
    }
    
    // Fallback: Try direct execution (local development only)
    if (!isVercel) {
      // Local development: run Python script directly
      try {
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
        return NextResponse.json(
          { 
            error: 'Failed to run research agent', 
            details: error.message,
            suggestion: 'Make sure Python dependencies are installed: pip install -r backend/requirements.txt'
          },
          { status: 500 }
        )
      }
    }
  } catch (error: any) {
    console.error('Unexpected error:', error)
    return NextResponse.json(
      { error: 'Unexpected error', details: error.message },
      { status: 500 }
    )
  }
}

// Allow GET for status check
export async function GET() {
  return NextResponse.json({
    status: 'ready',
    message: 'Research trigger endpoint is available',
  })
}

