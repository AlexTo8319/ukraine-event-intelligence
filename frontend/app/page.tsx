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

  // Today's date (November 28, 2025)
  const today = new Date('2025-11-28')
  today.setHours(0, 0, 0, 0)

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
    let filtered = events

    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter(e => e.category === selectedCategory)
    }

    // Filter by date (show only today onwards unless showPastEvents is true)
    if (!showPastEvents) {
      filtered = filtered.filter(e => {
        const eventDate = new Date(e.event_date)
        eventDate.setHours(0, 0, 0, 0)
        return eventDate >= today
      })
    }

    setFilteredEvents(filtered)
  }, [selectedCategory, showPastEvents, events])

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
      eventDate.setHours(0, 0, 0, 0)
      return eventDate >= today
    }).length,
    online: events.filter(e => e.is_online).length,
  }

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
          <button
            className={`filter-button ${showPastEvents ? 'active' : ''}`}
            onClick={() => setShowPastEvents(!showPastEvents)}
            style={{ marginLeft: '1rem' }}
          >
            {showPastEvents ? 'Hide Past Events' : 'Show Past Events'}
          </button>
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

