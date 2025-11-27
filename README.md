# Automated Urban Planning Event Intelligence Platform (Ukraine Focus)

An autonomous research agent that identifies, filters, and catalogues professional events related to Urban Planning, Post-War Recovery, and Housing Policy in Ukraine.

## Features

- **Automated Daily Research**: Runs daily via GitHub Actions to scan the web for upcoming events
- **Intelligent Filtering**: Uses LLM to filter out noise and extract structured data
- **Multi-language Support**: Searches in Ukrainian and English
- **Interactive Dashboard**: Clean web interface to view and manage events
- **Duplicate Prevention**: Smart upsert logic prevents duplicate entries

## Project Structure

```
├── backend/              # Python research agent
│   ├── agent/           # Core research logic
│   ├── database/        # Database utilities
│   └── requirements.txt
├── frontend/            # Next.js dashboard
│   ├── app/            # Next.js app directory
│   ├── components/     # React components
│   └── package.json
├── .github/
│   └── workflows/      # GitHub Actions for scheduling
├── .env.example        # Environment variables template
└── README.md
```

## Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required variables:
- `TAVILY_API_KEY`: Your Tavily API key for web search
- `OPENAI_API_KEY`: Your OpenAI API key for LLM processing
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase service role key

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Database Setup

Run the SQL migration in Supabase SQL editor (see `backend/database/schema.sql`)

### 5. GitHub Actions

The workflow is configured in `.github/workflows/daily-research.yml`. Ensure your repository secrets are set:
- `TAVILY_API_KEY`
- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`

## Usage

### Verify Setup

Before running, verify your setup:

```bash
cd backend
python verify_setup.py
```

### Manual Run

```bash
cd backend
python -m agent.research_agent
```

### Automated Run

The GitHub Actions workflow runs daily at 2:00 AM UTC. You can also trigger it manually from the Actions tab.

### View Dashboard

```bash
cd frontend
npm run dev
```

Then open http://localhost:3000 in your browser.

## Technology Stack

- **Backend**: Python 3.11+
- **Search API**: Tavily
- **LLM**: OpenAI GPT-4
- **Database**: Supabase (PostgreSQL)
- **Frontend**: Next.js 14 (App Router)
- **Scheduling**: GitHub Actions

## Security

All API keys are stored as environment variables and GitHub secrets. Never commit `.env` files or expose API keys in client-side code.

**Important Security Notes:**
- Backend uses service role key (full access) - never expose to frontend
- Frontend uses anon key (read-only) - safe to expose
- Supabase Row Level Security (RLS) policies restrict access
- See `SECURITY.md` for detailed security documentation

## Documentation

- **SETUP.md**: Detailed setup instructions
- **SECURITY.md**: Security best practices and configuration
- **backend/database/schema.sql**: Database schema
- **backend/database/rls_policy.sql**: Row Level Security policies

