# Project Summary

## What Was Built

A complete **Automated Urban Planning Event Intelligence Platform** that autonomously researches, filters, and displays professional events related to Ukraine's urban planning, post-war recovery, and housing policy.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Actions                       │
│              (Daily Scheduled Trigger)                   │
└────────────────────┬──────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Python Research Agent                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Search Agent │→ │ LLM Processor│→ │ DB Client    │ │
│  │  (Tavily)    │  │  (OpenAI)    │  │ (Supabase)   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────┬──────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Supabase PostgreSQL                        │
│                  (Events Table)                         │
└────────────────────┬──────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            Next.js Frontend Dashboard                   │
│         (Interactive Event Display)                     │
└─────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Backend Research Agent (`backend/`)

**Search Agent** (`agent/search.py`)
- Generates 30+ search queries in Ukrainian and English
- Uses Tavily API for advanced web search
- Covers 4 keyword clusters: Planning, Recovery, Housing, Governance
- Filters results for next 4 weeks timeframe

**LLM Processor** (`agent/llm_processor.py`)
- Uses OpenAI GPT-4o-mini for intelligent extraction
- Filters out noise (student projects, protests, irrelevant events)
- Extracts structured data: title, date, organizer, URL, category, online status, summary
- Validates events meet criteria (professional, Ukraine-related, upcoming)

**Research Agent** (`agent/research_agent.py`)
- Orchestrates the complete workflow
- Handles batching and error management
- Provides execution statistics
- Upserts events to prevent duplicates

**Database Client** (`database/client.py`)
- Supabase integration
- Smart upsert logic (URL-based duplicate prevention)
- Query methods for retrieving events

### 2. Frontend Dashboard (`frontend/`)

**Next.js 14 App Router**
- Modern React with TypeScript
- Server-side rendering for performance
- Responsive design with clean UI

**Features:**
- Event table with sorting by date
- Category filtering (Legislation, Housing, Recovery, General)
- Statistics dashboard (total, upcoming, online events)
- Direct links to event pages
- Online event badges
- Mobile-responsive layout

### 3. Automation (`.github/workflows/`)

**GitHub Actions Workflow**
- Scheduled daily at 2:00 AM UTC
- Manual trigger option
- Automated dependency installation
- Secure secret management
- Error logging

### 4. Security

**Multi-Layer Protection:**
- Environment variables for all secrets
- `.env` files excluded from git
- Frontend only exposes public Supabase keys
- Backend uses service role key (never exposed)
- Row Level Security (RLS) policies in Supabase
- GitHub Secrets for CI/CD

## Data Flow

1. **Trigger**: GitHub Actions runs daily (or manual trigger)
2. **Search**: Agent generates queries and searches web via Tavily
3. **Extract**: LLM processes results and extracts structured event data
4. **Filter**: Invalid events are removed (past dates, non-professional, etc.)
5. **Store**: Valid events are upserted to Supabase (duplicates prevented)
6. **Display**: Frontend queries Supabase and displays events to users

## Search Strategy

The agent searches for events using 4 keyword groups:

**Group A - Planning:**
- урбаністика, урбан-планування, просторове планування
- public space, green infrastructure, urban planning

**Group B - Recovery:**
- відбудова України, відновлення громад, стійке відновлення
- resilient cities, sustainable urban development, post-war recovery

**Group C - Housing:**
- житлова політика, доступне житло, архітектура
- housing policy, affordable housing, energy efficiency

**Group D - Governance:**
- розвиток спроможності, децентралізація, місцеве самоврядування
- capacity building, municipal governance, digital governance

## Event Schema

Each event contains:
- `event_title`: String
- `event_date`: ISO Date (YYYY-MM-DD)
- `organizer`: String (optional)
- `url`: String (unique identifier)
- `category`: Enum (Legislation, Housing, Recovery, General)
- `is_online`: Boolean
- `summary`: String (English summary of relevance)

## Technology Choices

**Why Tavily?**
- Advanced search API optimized for research
- Better results than basic web scraping
- Handles Ukrainian language content well

**Why OpenAI GPT-4o-mini?**
- Cost-effective for batch processing
- Excellent at structured data extraction
- Good multilingual support

**Why Supabase?**
- PostgreSQL with built-in API
- Easy Row Level Security
- Free tier suitable for this use case
- Direct frontend integration

**Why Next.js?**
- Modern React framework
- Server-side rendering
- Easy deployment
- TypeScript support

## File Structure

```
├── backend/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── models.py          # Event data models
│   │   ├── search.py          # Tavily search integration
│   │   ├── llm_processor.py   # OpenAI extraction logic
│   │   └── research_agent.py  # Main orchestrator
│   ├── database/
│   │   ├── __init__.py
│   │   ├── client.py          # Supabase client
│   │   ├── schema.sql         # Database schema
│   │   └── rls_policy.sql     # Security policies
│   ├── requirements.txt
│   └── verify_setup.py        # Setup verification
├── frontend/
│   ├── app/
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Main dashboard
│   │   └── globals.css        # Styling
│   ├── lib/
│   │   └── supabase.ts        # Supabase client
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
├── .github/
│   └── workflows/
│       └── daily-research.yml  # Automation
├── .env.example                # Environment template
├── .gitignore
├── README.md                   # Main documentation
├── SETUP.md                    # Setup guide
├── SECURITY.md                 # Security guide
└── PROJECT_SUMMARY.md          # This file
```

## Next Steps for Deployment

1. **Get API Keys:**
   - Sign up for Tavily API
   - Get OpenAI API key
   - Create Supabase project

2. **Set Up Database:**
   - Run `backend/database/schema.sql` in Supabase
   - Run `backend/database/rls_policy.sql` for security

3. **Configure Environment:**
   - Copy `.env.example` to `.env`
   - Fill in all API keys

4. **Test Locally:**
   - Run `python backend/verify_setup.py`
   - Run `python -m backend.agent.research_agent`
   - Start frontend: `cd frontend && npm run dev`

5. **Deploy:**
   - Push to GitHub
   - Set GitHub Secrets
   - Deploy frontend (Vercel/Netlify)
   - Workflow will run automatically

## Maintenance

- **Daily**: Automated research runs via GitHub Actions
- **Weekly**: Review event quality and adjust LLM prompts if needed
- **Monthly**: Rotate API keys, review costs
- **Quarterly**: Update keyword lists based on trends

## Cost Estimates

- **Tavily API**: ~$0.01-0.05 per search query (30 queries/day = $0.30-1.50/day)
- **OpenAI API**: ~$0.01-0.03 per batch (1 batch/day = $0.01-0.03/day)
- **Supabase**: Free tier (up to 500MB database, 2GB bandwidth)
- **GitHub Actions**: Free tier (2000 minutes/month)

**Total**: ~$10-50/month depending on usage

## Success Metrics

- Number of events discovered per day
- Event quality (relevance to target audience)
- Duplicate prevention rate
- Dashboard usage statistics

