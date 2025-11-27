# Setup Guide

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Supabase account (free tier works)
- Tavily API key (get from https://tavily.com)
- OpenAI API key (get from https://platform.openai.com)

## Step-by-Step Setup

### 1. Clone and Navigate

```bash
cd "Cursor AI event search"
```

### 2. Set Up Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
TAVILY_API_KEY=your_actual_tavily_key
OPENAI_API_KEY=your_actual_openai_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

**Important Security Notes:**
- Never commit `.env` to git (it's in `.gitignore`)
- Use Supabase **Service Role Key** for backend (has admin access)
- Use Supabase **Anon Key** for frontend (public, read-only access)
- Keep API keys secure and rotate them periodically

### 3. Set Up Supabase Database

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy and paste the contents of `backend/database/schema.sql`
4. Run the SQL to create the `events` table

### 4. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

If you prefer using a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Test the Research Agent (Optional)

```bash
# Make sure you're in the backend directory
python -m agent.research_agent
```

This will run a full research cycle and populate your database.

### 6. Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

### 7. Run the Frontend

```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### 8. Set Up GitHub Actions (for Automated Daily Runs)

1. Push your code to a GitHub repository
2. Go to repository Settings → Secrets and variables → Actions
3. Add the following secrets:
   - `TAVILY_API_KEY`
   - `OPENAI_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

4. The workflow (`.github/workflows/daily-research.yml`) will automatically run daily at 2:00 AM UTC
5. You can also trigger it manually from the Actions tab

## Security Best Practices

### Backend (Python)
- All API keys are loaded from environment variables
- Never hardcode keys in source files
- Use `.env` file for local development (not committed to git)

### Frontend (Next.js)
- Only public environment variables (prefixed with `NEXT_PUBLIC_`) are exposed
- Sensitive keys (OpenAI, Tavily) are **never** exposed to the browser
- Frontend only uses Supabase Anon Key (read-only access)

### GitHub Actions
- All secrets are stored in GitHub Secrets (encrypted)
- Secrets are only available during workflow execution
- Never log or expose secrets in workflow output

## Troubleshooting

### Database Connection Issues
- Verify your Supabase URL and keys are correct
- Check that the `events` table was created successfully
- Ensure your Supabase project is active

### API Key Issues
- Verify keys are correctly set in `.env`
- Check API key quotas/limits
- Ensure keys have proper permissions

### Frontend Not Loading Events
- Check browser console for errors
- Verify `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are set
- Ensure Row Level Security (RLS) policies allow read access in Supabase

### Research Agent Errors
- Check that all API keys are valid
- Verify internet connectivity
- Review error messages in the console output

## Next Steps

1. Run the research agent manually to populate initial data
2. Set up GitHub Actions for automated daily runs
3. Customize the frontend styling if needed
4. Add additional filters or features as required

