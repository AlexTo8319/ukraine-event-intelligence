'use client'

import { useEffect, useState } from 'react'
import { supabase, Event } from '@/lib/supabase'
// Date formatting helper
const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch {
    return dateString
  }
}
import './globals.css'

export default function Home() {
  const [events, setEvents] = useState<Event[]>([])
  const [filteredEvents, setFilteredEvents] = useState<Event[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [debugInfo, setDebugInfo] = useState<string[]>([])

  const addDebug = (message: string) => {
    if (typeof window !== 'undefined') {
      console.log(`[DEBUG] ${message}`)
    }
    setDebugInfo(prev => [...prev.slice(-4), `${new Date().toLocaleTimeString()}: ${message}`])
  }

  useEffect(() => {
    loadEvents()
  }, [])

  useEffect(() => {
    if (selectedCategory) {
      setFilteredEvents(events.filter(e => e.category === selectedCategory))
    } else {
      setFilteredEvents(events)
    }
  }, [selectedCategory, events])

  const loadEvents = async () => {
    try {
      setLoading(true)
      setError(null)
      addDebug('Starting to load events...')
      
      // Check Supabase client
      if (!supabase) {
        throw new Error('Supabase client not initialized')
      }
      addDebug('Supabase client initialized')
      
      addDebug('Making query to Supabase...')
      const { data, error: fetchError } = await supabase
        .from('events')
        .select('*')
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

  const categories = ['Legislation', 'Housing', 'Recovery', 'General'] as const
  const stats = {
    total: events.length,
    upcoming: events.filter(e => {
      const eventDate = new Date(e.event_date)
      return eventDate >= new Date()
    }).length,
    online: events.filter(e => e.is_online).length,
  }

  const getBadgeClass = (category: string) => {
    return `badge badge-${category.toLowerCase()}`
  }

  const formatDate = (dateString: string) => {
    try {
      return formatDate(dateString)
    } catch {
      return dateString
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
        </div>

        <div className="filters">
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
        </div>

        {loading ? (
          <div className="loading">Loading events...</div>
        ) : filteredEvents.length === 0 ? (
          <div className="loading">No events found. The research agent will populate events daily.</div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Event Title</th>
                  <th>Organizer</th>
                  <th>Category</th>
                  <th>Summary</th>
                  <th>Link</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map(event => (
                  <tr key={event.id}>
                    <td>{formatDate(event.event_date)}</td>
                    <td>
                      <strong>{event.event_title}</strong>
                      {event.is_online && <span className="online-badge">Online</span>}
                    </td>
                    <td>{event.organizer || 'N/A'}</td>
                    <td>
                      <span className={getBadgeClass(event.category)}>
                        {event.category}
                      </span>
                    </td>
                    <td>{event.summary || '—'}</td>
                    <td>
                      <a href={event.url} target="_blank" rel="noopener noreferrer">
                        View Event →
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

