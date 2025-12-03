'use client'

import { useEffect, useState } from 'react'
import { supabase, Event } from '@/lib/supabase'
import './globals.css'

// Date formatting helper
const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch {
    return dateString
  }
}

export default function Home() {
  const [events, setEvents] = useState<Event[]>([])
  const [filteredEvents, setFilteredEvents] = useState<Event[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [showPastEvents, setShowPastEvents] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [debugInfo, setDebugInfo] = useState<string[]>([])
  const [isRunningResearch, setIsRunningResearch] = useState(false)
  const [researchStatus, setResearchStatus] = useState<string | null>(null)
  const [apiCredits, setApiCredits] = useState<{tavily: {used: number, remaining: number} | null, openai: {used: number} | null}>({tavily: null, openai: null})

  const addDebug = (message: string) => {
    if (typeof window !== 'undefined') {
      console.log(`[DEBUG] ${message}`)
    }
    setDebugInfo(prev => [...prev.slice(-4), `${new Date().toLocaleTimeString()}: ${message}`])
  }

  useEffect(() => {
    loadEvents(showPastEvents)
    loadApiCredits()
  }, [showPastEvents])

  useEffect(() => {
    let filtered = events

    // Filter by category only - date filtering is now done server-side
    if (selectedCategory) {
      filtered = filtered.filter(e => e.category === selectedCategory)
    }

    setFilteredEvents(filtered)
  }, [selectedCategory, events])

  const loadEvents = async (includePastEvents: boolean = false) => {
    try {
      setLoading(true)
      setError(null)
      addDebug('Starting to load events...')
      
      // Check Supabase client
      if (!supabase) {
        throw new Error('Supabase client not initialized')
      }
      addDebug('Supabase client initialized')
      
      // Get today's date in YYYY-MM-DD format for server-side filtering
      const today = new Date()
      const todayStr = today.toISOString().split('T')[0] // e.g., "2025-12-03"
      
      addDebug(`Making query to Supabase (today: ${todayStr}, includePast: ${includePastEvents})...`)
      
      // Build query with optional date filter
      let query = supabase
        .from('events')
        .select('*')
      
      // Only filter by date if NOT showing past events (server-side filtering)
      if (!includePastEvents) {
        query = query.gte('event_date', todayStr)
      }
      
      const { data, error: fetchError } = await query
        .order('event_date', { ascending: true })
        .limit(200)

      if (fetchError) {
        addDebug(`Supabase error: ${fetchError.message}`)
        console.error('Full Supabase error:', fetchError)
        throw new Error(`Database error: ${fetchError.message} (Code: ${fetchError.code || 'unknown'})`)
      }

      addDebug(`Query successful! Received ${data?.length || 0} events`)
      console.log('Events data:', data)
      
      if (!data || data.length === 0) {
        addDebug('No events found in database')
      } else {
        addDebug(`Setting ${data.length} events in state`)
      }
      
      setEvents(data || [])
      setFilteredEvents(data || [])
      addDebug('Events loaded successfully!')
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to load events'
      addDebug(`ERROR: ${errorMsg}`)
      console.error('Full error object:', err)
      setError(errorMsg)
    } finally {
      setLoading(false)
      addDebug('Loading complete')
    }
  }

  const loadApiCredits = async () => {
    try {
      const response = await fetch('/api/credits')
      if (response.ok) {
        const data = await response.json()
        setApiCredits(data)
      }
    } catch (err) {
      console.error('Failed to load API credits:', err)
      // Don't show error to user, just log it
    }
  }

  const triggerResearch = async () => {
    try {
      setIsRunningResearch(true)
      setResearchStatus('Triggering research agent...')
      
      const response = await fetch('/api/trigger-research', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      // Check if response is ok and has content
      if (!response.ok) {
        let errorData
        try {
          errorData = await response.json()
        } catch {
          errorData = { error: `HTTP ${response.status}: ${response.statusText}` }
        }
        throw new Error(errorData.error || errorData.message || 'Failed to trigger research')
      }
      
      // Parse JSON response
      let data
      try {
        const text = await response.text()
        if (!text) {
          throw new Error('Empty response from server')
        }
        data = JSON.parse(text)
      } catch (parseError: any) {
        console.error('JSON parse error:', parseError)
        throw new Error('Invalid response from server. Please check the console for details.')
      }
      
      if (data.success === false) {
        throw new Error(data.error || data.message || 'Research trigger failed')
      }
      
      const message = data.message || 'Research agent triggered successfully!'
      setResearchStatus(message)
      
      // If GitHub Actions was triggered, poll for new events
      if (data.method === 'github-actions') {
        // Keep status visible for longer
        // Start polling for new events after 30 seconds
        setTimeout(() => {
          setResearchStatus('Research in progress... Checking for new events...')
          
          // Poll every 30 seconds for up to 5 minutes
          let pollCount = 0
          const maxPolls = 10 // 10 polls * 30 seconds = 5 minutes
          
          const pollInterval = setInterval(() => {
            pollCount++
            loadEvents()
            loadApiCredits() // Refresh credits after each poll
            
            if (pollCount >= maxPolls) {
              clearInterval(pollInterval)
              setResearchStatus('Research completed! Check the events below.')
              setTimeout(() => setResearchStatus(null), 10000)
            } else {
              setResearchStatus(`Research in progress... Checking for new events... (${pollCount}/${maxPolls})`)
            }
          }, 30000) // Poll every 30 seconds
        }, 30000) // Wait 30 seconds before first poll
      } else {
        // Direct execution - refresh immediately
        setTimeout(() => {
          loadEvents()
          setResearchStatus('Research completed! Events updated.')
          setTimeout(() => setResearchStatus(null), 10000)
        }, 2000)
      }
      
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to trigger research'
      setResearchStatus(`Error: ${errorMsg}`)
      console.error('Research trigger error:', err)
    } finally {
      setIsRunningResearch(false)
      // Clear error status message after 15 seconds
      if (researchStatus && researchStatus.startsWith('Error:')) {
        setTimeout(() => setResearchStatus(null), 15000)
      }
    }
  }

  const categories = ['Legislation', 'Housing', 'Recovery', 'General'] as const
  
  // Calculate stats with current date
  const getStats = () => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    
    return {
      total: events.length,
      upcoming: events.filter(e => {
        const eventDate = new Date(e.event_date + 'T00:00:00')
        eventDate.setHours(0, 0, 0, 0)
        return eventDate >= today
      }).length,
      online: events.filter(e => e.is_online).length,
    }
  }
  
  const stats = getStats()

  const getBadgeClass = (category: string) => {
    return `badge badge-${category.toLowerCase()}`
  }

  const formatTime = (timeString: string | null) => {
    if (!timeString) return '—'
    try {
      // Handle HH:MM format
      const [hours, minutes] = timeString.split(':')
      const hour = parseInt(hours, 10)
      const minute = parseInt(minutes, 10)
      const date = new Date()
      date.setHours(hour, minute, 0, 0)
      return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })
    } catch {
      return timeString
    }
  }

  return (
    <div>
      <header className="header">
        <div className="container">
          <h1>Urban Planning Event Intelligence</h1>
          <p>Ukraine Focus - Automated Research Platform</p>
        </div>
      </header>

      <main className="container">
        {error && (
          <div className="error">
            <strong>Error:</strong> {error}
            <details style={{ marginTop: '10px', fontSize: '0.9em' }}>
              <summary style={{ cursor: 'pointer' }}>Debug Info</summary>
              <pre style={{ marginTop: '10px', padding: '10px', background: '#f5f5f5', overflow: 'auto', maxHeight: '200px' }}>
                {debugInfo.join('\n')}
              </pre>
            </details>
          </div>
        )}
        
        {process.env.NODE_ENV === 'development' && debugInfo.length > 0 && (
          <div style={{ marginBottom: '1rem', padding: '10px', background: '#e3f2fd', borderRadius: '4px', fontSize: '0.85em' }}>
            <strong>Debug Log:</strong>
            <pre style={{ marginTop: '5px', maxHeight: '100px', overflow: 'auto' }}>
              {debugInfo.slice(-5).join('\n')}
            </pre>
          </div>
        )}

        <div className="stats">
          <div className="stat-card">
            <h3>Total Events</h3>
            <p>{stats.total}</p>
          </div>
          <div className="stat-card">
            <h3>Upcoming</h3>
            <p>{stats.upcoming}</p>
          </div>
          <div className="stat-card">
            <h3>Online Events</h3>
            <p>{stats.online}</p>
          </div>
          {apiCredits.tavily && (
            <div className="stat-card" style={{ 
              backgroundColor: apiCredits.tavily.remaining < 200 ? '#fff3cd' : '#e3f2fd',
              border: `1px solid ${apiCredits.tavily.remaining < 200 ? '#ffc107' : '#90caf9'}`
            }}>
              <h3>API Credits</h3>
              <p style={{ fontSize: '0.9em', margin: 0 }}>
                Tavily: {apiCredits.tavily.remaining}/{apiCredits.tavily.freeTierLimit || 1000}
                {apiCredits.tavily.remaining < 200 && (
                  <span style={{ color: '#d32f2f', fontWeight: 'bold', marginLeft: '8px' }}>⚠️ Low</span>
                )}
              </p>
              {apiCredits.tavily.estimatedPerRun && (
                <p style={{ fontSize: '0.75em', color: '#666', margin: '4px 0 0 0' }}>
                  ~{apiCredits.tavily.estimatedPerRun} per run
                </p>
              )}
            </div>
          )}
        </div>

        <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div className="filters" style={{ flex: 1 }}>
            <button
              className={`filter-button ${selectedCategory === null ? 'active' : ''}`}
              onClick={() => setSelectedCategory(null)}
            >
              All Events
            </button>
            {categories.map(cat => (
              <button
                key={cat}
                className={`filter-button ${selectedCategory === cat ? 'active' : ''}`}
                onClick={() => setSelectedCategory(cat)}
              >
                {cat}
              </button>
            ))}
            <button
              className={`filter-button ${showPastEvents ? 'active' : ''}`}
              onClick={() => setShowPastEvents(!showPastEvents)}
              style={{ marginLeft: '1rem' }}
            >
              {showPastEvents ? 'Hide Past Events' : 'Show Past Events'}
            </button>
          </div>
          <button
            onClick={triggerResearch}
            disabled={isRunningResearch}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: isRunningResearch ? '#ccc' : '#0066cc',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: isRunningResearch ? 'not-allowed' : 'pointer',
              fontSize: '1rem',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'background-color 0.2s',
            }}
            onMouseEnter={(e) => {
              if (!isRunningResearch) {
                e.currentTarget.style.backgroundColor = '#0052a3'
              }
            }}
            onMouseLeave={(e) => {
              if (!isRunningResearch) {
                e.currentTarget.style.backgroundColor = '#0066cc'
              }
            }}
          >
            {isRunningResearch ? (
              <>
                <span>⏳</span>
                <span>Running Research...</span>
              </>
            ) : (
              <>
                <span>🔍</span>
                <span>Run Research Now</span>
              </>
            )}
          </button>
        </div>
        
        {researchStatus && (
          <div style={{
            padding: '1rem',
            marginBottom: '1rem',
            backgroundColor: researchStatus.startsWith('Error') ? '#fee' : '#e3f2fd',
            border: `1px solid ${researchStatus.startsWith('Error') ? '#fcc' : '#90caf9'}`,
            borderRadius: '6px',
            color: researchStatus.startsWith('Error') ? '#c00' : '#1565c0',
            fontSize: '0.95rem',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}>
            {researchStatus.startsWith('Error') ? '❌' : '⏳'}
            <span>{researchStatus}</span>
            {!researchStatus.startsWith('Error') && (
              <span style={{ fontSize: '0.85em', opacity: 0.8, marginLeft: 'auto' }}>
                (This may take 2-3 minutes)
              </span>
            )}
          </div>
        )}

        {loading ? (
          <div className="loading">Loading events...</div>
        ) : filteredEvents.length === 0 ? (
          <div className="loading">No events found. The research agent will populate events daily.</div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Date & Time</th>
                  <th>Event Title</th>
                  <th>Organizer</th>
                  <th>Target Audience</th>
                  <th>Category</th>
                  <th>Description</th>
                  <th>Register</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map(event => (
                  <tr key={event.id}>
                    <td>
                      <div>{formatDate(event.event_date)}</div>
                      {event.event_time && (
                        <div style={{ fontSize: '0.9em', color: '#666', marginTop: '4px' }}>
                          {formatTime(event.event_time)}
                        </div>
                      )}
                    </td>
                    <td>
                      <strong>{event.event_title}</strong>
                      {event.is_online && <span className="online-badge">Online</span>}
                    </td>
                    <td>{event.organizer || '—'}</td>
                    <td>{event.target_audience || '—'}</td>
                    <td>
                      <span className={getBadgeClass(event.category)}>
                        {event.category}
                      </span>
                    </td>
                    <td style={{ maxWidth: '300px' }}>{event.summary || '—'}</td>
                    <td>
                      <a 
                        href={event.registration_url || event.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{ 
                          color: '#0066cc', 
                          textDecoration: 'none',
                          fontWeight: '500'
                        }}
                      >
                        Register →
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  )
}

