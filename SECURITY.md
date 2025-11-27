# Security Guide

## Overview

This document outlines the security measures implemented to protect API keys and sensitive information in the Event Intelligence Platform.

## Security Architecture

### Backend (Python Research Agent)

**Protected Information:**
- Tavily API Key
- OpenAI API Key
- Supabase Service Role Key (full database access)

**Protection Methods:**
1. **Environment Variables**: All sensitive keys are loaded from `.env` file
2. **Git Ignore**: `.env` file is excluded from version control
3. **No Hardcoding**: Keys are never hardcoded in source files
4. **Server-Side Only**: Backend code never runs in the browser

**Implementation:**
```python
# ✅ CORRECT - Using environment variables
api_key = os.getenv("TAVILY_API_KEY")

# ❌ WRONG - Never do this
api_key = "hardcoded_key_12345"
```

### Frontend (Next.js Dashboard)

**Protected Information:**
- OpenAI API Key (NEVER exposed to frontend)
- Tavily API Key (NEVER exposed to frontend)
- Supabase Service Role Key (NEVER exposed to frontend)

**Exposed Information (Safe):**
- Supabase Anon Key (read-only, public)
- Supabase URL (public endpoint)

**Protection Methods:**
1. **Environment Variable Prefix**: Only `NEXT_PUBLIC_*` variables are exposed to browser
2. **Direct Database Access**: Frontend queries Supabase directly (no backend proxy needed)
3. **Row Level Security (RLS)**: Supabase RLS policies restrict access
4. **No API Key Exposure**: Sensitive keys are never included in frontend code

**Implementation:**
```typescript
// ✅ CORRECT - Only public variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL

// ❌ WRONG - This would expose the key
const openaiKey = process.env.OPENAI_API_KEY  // Never do this!
```

### GitHub Actions

**Protected Information:**
- All API keys stored as GitHub Secrets

**Protection Methods:**
1. **GitHub Secrets**: Encrypted storage in repository settings
2. **No Logging**: Secrets are never logged or printed
3. **Workflow Isolation**: Secrets only available during workflow execution
4. **Access Control**: Only repository admins can view/modify secrets

**Setup:**
1. Go to: Repository → Settings → Secrets and variables → Actions
2. Add secrets:
   - `TAVILY_API_KEY`
   - `OPENAI_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

## Supabase Row Level Security (RLS)

### Why RLS is Important

RLS ensures that even if someone gets the Anon Key, they can only access data according to your policies.

### Required RLS Policy

Run this SQL in your Supabase SQL Editor:

```sql
-- Enable RLS on events table
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Create policy: Allow public read access to events
CREATE POLICY "Allow public read access to events"
ON events
FOR SELECT
TO anon, authenticated
USING (true);

-- Note: Only service role (backend) can INSERT/UPDATE
-- This is enforced by default since we don't grant INSERT/UPDATE to anon
```

### Testing RLS

1. **Test Public Access (Should Work):**
   ```typescript
   // Frontend code - uses anon key
   const { data } = await supabase.from('events').select('*')
   ```

2. **Test Write Access (Should Fail with Anon Key):**
   ```typescript
   // This should fail - anon key cannot insert
   await supabase.from('events').insert({...})
   ```

## Environment Variable Checklist

### Local Development

- [ ] `.env` file exists in project root
- [ ] `.env` is in `.gitignore`
- [ ] All required variables are set
- [ ] No keys are committed to git

### Production (GitHub Actions)

- [ ] All secrets are set in GitHub Secrets
- [ ] Secret names match workflow file exactly
- [ ] Secrets are not logged in workflow output
- [ ] Service account has minimal required permissions

### Frontend Deployment

- [ ] Only `NEXT_PUBLIC_*` variables are set
- [ ] No sensitive keys in frontend environment
- [ ] Supabase RLS policies are configured
- [ ] Anon key has read-only access

## Best Practices

### ✅ DO

- Use environment variables for all secrets
- Keep `.env` files out of version control
- Use different keys for development/production
- Rotate keys periodically
- Use Supabase RLS to restrict access
- Monitor API usage for anomalies

### ❌ DON'T

- Commit `.env` files to git
- Hardcode API keys in source files
- Expose service role keys to frontend
- Share keys in chat/email
- Use production keys in development
- Log API keys in console output

## Incident Response

If an API key is compromised:

1. **Immediately revoke** the key in the provider dashboard
2. **Generate a new key** and update all environments
3. **Review access logs** for unauthorized usage
4. **Update GitHub Secrets** if applicable
5. **Notify team members** to update their `.env` files

## Key Rotation Schedule

Recommended rotation frequency:
- **Tavily API Key**: Every 90 days
- **OpenAI API Key**: Every 90 days
- **Supabase Keys**: Every 180 days (or when team members leave)

## Additional Resources

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

