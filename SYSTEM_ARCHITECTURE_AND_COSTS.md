# 🏗️ System Architecture & Cost Analysis
## Automated Urban Planning Event Intelligence Platform

---

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [Data Flow](#data-flow)
4. [Token Usage Analysis](#token-usage-analysis)
5. [Cost Breakdown](#cost-breakdown)
6. [Monthly Cost Estimates](#monthly-cost-estimates)
7. [Optimization Strategies](#optimization-strategies)

---

## 🎯 System Overview

This is an **automated event intelligence platform** that:
- **Searches** the web for urban planning, housing, and recovery events in Ukraine
- **Extracts** structured event data using AI
- **Stores** events in a PostgreSQL database (Supabase)
- **Displays** events on a Next.js dashboard (Vercel)
- **Runs automatically** daily via GitHub Actions

---

## 🏛️ Architecture Components

### 1. **Frontend (Next.js + React + TypeScript)**
- **Location**: `frontend/`
- **Hosting**: Vercel
- **Purpose**: Dashboard to display events
- **Features**:
  - Real-time event display
  - Category filtering (Legislation, Housing, Recovery, General)
  - Date filtering (today onwards, with past events toggle)
  - "Run Research Now" button to trigger manual research
  - Auto-refresh every 30 seconds after triggering research

### 2. **Backend Research Agent (Python)**
- **Location**: `backend/agent/`
- **Components**:
  - **SearchAgent** (`search.py`): Uses Tavily API for web search
  - **LLMProcessor** (`llm_processor.py`): Uses OpenAI GPT-4o-mini to extract events
  - **ResearchAgent** (`research_agent.py`): Orchestrates the workflow
- **Hosting**: GitHub Actions (runs on Ubuntu VMs)

### 3. **Database (PostgreSQL via Supabase)**
- **Location**: Supabase Cloud
- **Schema**: `events` table with 12 columns
- **Features**:
  - Row Level Security (RLS) enabled
  - Public read access, service role write access
  - Automatic timestamps (created_at, updated_at)

### 4. **Automation (GitHub Actions)**
- **Location**: `.github/workflows/daily-research.yml`
- **Schedule**: Daily at 2:00 AM UTC
- **Manual Trigger**: Via "Run Research Now" button
- **Runtime**: ~3-5 minutes per execution

---

## 🔄 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER TRIGGERS RESEARCH                    │
│  (via "Run Research Now" button or daily schedule)          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              GITHUB ACTIONS WORKFLOW STARTS                   │
│  - Checks out code                                           │
│  - Sets up Python 3.11                                       │
│  - Installs dependencies                                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              RESEARCH AGENT EXECUTION                        │
│                                                              │
│  Step 1: Generate Search Queries                            │
│  ──────────────────────────────────────                     │
│  • 28 search queries (7 per category × 4 categories)        │
│  • Mix of Ukrainian and English keywords                     │
│  • Focus: Planning, Recovery, Housing, Governance            │
│                                                              │
│  Step 2: Execute Web Searches (Tavily API)                  │
│  ──────────────────────────────────────                     │
│  • 28 queries × 10 results each = ~280 results              │
│  • Deduplication by URL → ~100-150 unique URLs               │
│                                                              │
│  Step 3: Process with LLM (OpenAI GPT-4o-mini)             │
│  ──────────────────────────────────────                     │
│  • Batch processing: 20 results per LLM call                 │
│  • ~5-8 LLM API calls per run                                │
│  • Extracts: title, date, time, organizer, URL, etc.       │
│                                                              │
│  Step 4: Validate & Filter Events                           │
│  ──────────────────────────────────────                     │
│  • Date validation (next 4 weeks only)                      │
│  • Category assignment                                      │
│  • Quality filtering (min title length, valid URLs)          │
│                                                              │
│  Step 5: Save to Database (Supabase)                        │
│  ──────────────────────────────────────                     │
│  • Upsert events (update if exists, insert if new)          │
│  • Uses service role key for write access                   │
│  • ~10-30 events saved per run (typical)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              DATABASE UPDATED                                │
│  • New events inserted                                       │
│  • Existing events updated (if info changed)                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND AUTO-REFRESHES                         │
│  • Dashboard polls database every 30 seconds                │
│  • New events appear automatically                           │
│  • User sees updated event list                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Token Usage Analysis

### **1. Tavily API (Web Search)**

**Usage per run:**
- **Search queries**: 28 queries
- **Results per query**: 10 results
- **Total API calls**: 28 calls
- **Search depth**: "advanced" (more comprehensive, costs more)

**Pricing (as of 2024):**
- **Free tier**: 1,000 credits/month (no credit card required)
- **Basic search**: 1 credit per query
- **Advanced search**: 2 credits per query
- **Current setup**: Basic search (1 credit per query)
- **Credits per run**: 28 queries × 1 credit = **28 credits per run**
- **Monthly usage**: 28 × 30 = **840 credits/month** (within free tier!)

**Note**: Tavily pricing can vary. Check current pricing at: https://tavily.com/pricing

### **2. OpenAI API (GPT-4o-mini)**

**Usage per run:**
- **Model**: `gpt-4o-mini` (cost-efficient)
- **LLM calls**: ~5-8 calls (batches of 20 search results)
- **Input tokens per call**: ~3,000-5,000 tokens
- **Output tokens per call**: ~500-1,500 tokens

**Token calculation:**
- **System prompt**: ~800 tokens (fixed)
- **User prompt**: ~3,000-5,000 tokens (20 search results × ~150-250 tokens each)
- **Total input per call**: ~3,800-5,800 tokens
- **Total output per call**: ~500-1,500 tokens

**Pricing (as of 2024):**
- **GPT-4o-mini input**: $0.15 per 1M tokens
- **GPT-4o-mini output**: $0.60 per 1M tokens

**Cost per LLM call:**
- Input: (4,000 tokens / 1,000,000) × $0.15 = **$0.0006**
- Output: (1,000 tokens / 1,000,000) × $0.60 = **$0.0006**
- **Total per call**: **$0.0012**

**Cost per run (7 LLM calls):**
- 7 calls × $0.0012 = **$0.0084 per run**

### **3. Supabase (Database)**

**Usage per run:**
- **Reads**: Minimal (checking for duplicates)
- **Writes**: ~10-30 event upserts
- **Storage**: ~1-5 KB per event

**Pricing (as of 2024):**
- **Free tier**: 
  - 500 MB database storage
  - 2 GB bandwidth
  - 50,000 monthly active users
  - Unlimited API requests
- **Paid tier**: Starts at $25/month (Pro plan)

**Cost per run**: **$0** (within free tier limits)

### **4. Vercel (Frontend Hosting)**

**Usage:**
- **Static site generation** (Next.js)
- **API routes** (trigger-research endpoint)
- **Bandwidth**: Minimal (dashboard page loads)

**Pricing (as of 2024):**
- **Free tier (Hobby)**:
  - Unlimited personal projects
  - 100 GB bandwidth/month
  - Serverless functions: 100 GB-hours/month
- **Paid tier**: Starts at $20/month (Pro plan)

**Cost per run**: **$0** (within free tier limits)

### **5. GitHub Actions**

**Usage per run:**
- **Runtime**: ~3-5 minutes
- **VM**: Ubuntu latest (2-core, 7 GB RAM)
- **Actions**: Checkout, Python setup, pip install, script execution

**Pricing (as of 2024):**
- **Free tier**: 
  - 2,000 minutes/month for private repos
  - Unlimited minutes for public repos
- **Paid tier**: $0.008 per minute (after free tier)

**Cost per run**: **$0** (if public repo or within free tier)

---

## 💰 Cost Breakdown

### **Per Run (Single Execution)**

| Service | Usage | Cost per Run |
|---------|-------|--------------|
| **Tavily API** | 28 search queries (basic depth) | **$0** (free tier) |
| **OpenAI API** | ~7 LLM calls | **$0.0084** |
| **Supabase** | ~20 event upserts | **$0** (free tier) |
| **Vercel** | Dashboard hosting | **$0** (free tier) |
| **GitHub Actions** | ~4 minutes runtime | **$0** (free tier) |
| **TOTAL PER RUN** | | **~$0.0084** |

### **Daily Execution (30 days/month)**

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| **Tavily API** | 840 credits/month (28 × 30) | **$0** (free tier - 1,000 credits) |
| **OpenAI API** | ~7 calls × 30 days = 210 calls | **$0.25** |
| **Supabase** | ~600 event upserts | **$0** (free tier) |
| **Vercel** | Dashboard hosting | **$0** (free tier) |
| **GitHub Actions** | ~120 minutes/month | **$0** (free tier) |
| **TOTAL MONTHLY** | | **~$0.25** |

### **With Manual Triggers (Additional Costs)**

If users click "Run Research Now" **5 times per day** (150 times/month):
- **Tavily**: 150 × 28 credits = 4,200 credits (exceeds free tier)
  - Free tier covers: 1,000 credits
  - Remaining: 3,200 credits would need paid plan
  - **Recommendation**: Limit to ~5-6 manual triggers/month to stay free
- **OpenAI**: 150 × $0.0084 = **$1.26/month**
- **Total additional**: **~$1.26/month** (if staying within free tier)

**Combined (Daily + 5 Manual Triggers/Month):**
- **Total monthly cost**: **~$1.51/month** (staying within free tiers)

---

## 📈 Monthly Cost Estimates

### **Scenario 1: Minimal Usage (Daily Only)**
- **Runs**: 30 per month (1 per day)
- **Tavily**: $0 (840 credits/month, within 1,000 free tier)
- **OpenAI**: $0.25
- **Other services**: $0 (free tier)
- **TOTAL**: **~$0.25/month** ✅

### **Scenario 2: Moderate Usage (Daily + 5 Manual Triggers/Month)**
- **Runs**: 35 per month (30 daily + 5 manual)
- **Tavily**: $0 (980 credits/month, within 1,000 free tier)
- **OpenAI**: $0.29
- **Other services**: $0 (free tier)
- **TOTAL**: **~$0.29/month** ✅

### **Scenario 3: Weekly Schedule (Maximum Buffer)**
- **Runs**: 4 per month (1 per week)
- **Tavily**: $0 (112 credits/month, within 1,000 free tier)
- **OpenAI**: $0.03
- **Other services**: $0 (free tier)
- **TOTAL**: **~$0.03/month** ✅
- **Manual trigger capacity**: ~31 extra triggers/month!

---

## 🎯 Optimization Strategies

### **1. Reduce Tavily API Costs (Biggest Cost Driver)**

**Current**: 28 queries per run = $5.60 per run

**Optimization Options:**

#### **Option A: Reduce Query Count**
- **Current**: 28 queries (7 per category × 4 categories)
- **Optimized**: 14 queries (3-4 per category)
- **Savings**: 50% reduction = **$84/month** (daily only)

#### **Option B: Use Basic Search Depth**
- **Current**: "advanced" depth (more expensive)
- **Optimized**: "basic" depth (cheaper)
- **Savings**: ~50% reduction = **$84/month** (daily only)

#### **Option C: Reduce Results per Query**
- **Current**: 10 results per query
- **Optimized**: 5 results per query
- **Savings**: Minimal (pricing is per query, not per result)

#### **Option D: Smart Query Selection**
- **Current**: All 28 queries run every time
- **Optimized**: Rotate queries (14 per day, different set each day)
- **Savings**: 50% reduction = **$84/month** (daily only)

**Recommended**: Combine Option A + Option B = **~$84/month** (daily only)

### **2. Optimize OpenAI API Usage**

**Current**: ~7 LLM calls per run = $0.0084 per run

**Optimization Options:**

#### **Option A: Increase Batch Size**
- **Current**: 20 results per batch
- **Optimized**: 30-40 results per batch
- **Savings**: ~30% reduction = **$0.06/month** (daily only)
- **Risk**: May hit token limits or reduce quality

#### **Option B: Use GPT-3.5-turbo (if available)**
- **Current**: GPT-4o-mini
- **Optimized**: GPT-3.5-turbo (cheaper)
- **Savings**: ~50% reduction = **$0.13/month** (daily only)
- **Risk**: May reduce extraction quality

**Recommended**: Keep GPT-4o-mini (cost is already minimal)

### **3. Reduce Execution Frequency**

**Current**: Daily execution

**Optimization Options:**

#### **Option A: Every 2 Days**
- **Savings**: 50% reduction = **$84/month**

#### **Option B: Weekly**
- **Savings**: 86% reduction = **$144/month**

**Recommended**: Keep daily (ensures fresh data)

### **4. Cache and Deduplication**

**Current**: Full search every time

**Optimization Options:**
- **Cache search results** for 24 hours
- **Skip searches** for queries that haven't changed
- **Savings**: Variable (depends on overlap)

---

## 📋 Summary

### **Current System Costs (Daily Only) - OPTIMIZED ✅**
- **Tavily API**: $0/month (840 credits/month, within 1,000 free tier)
- **OpenAI API**: $0.25/month (100% of total cost)
- **Other services**: $0/month (free tier)
- **TOTAL**: **~$0.25/month** 🎉

### **Key Insights**
1. **Tavily API is now FREE** (using basic search depth, within free tier)
2. **OpenAI costs are minimal** ($0.25/month)
3. **All other services are free** (within free tier limits)
4. **Manual triggers are limited** (~5-6/month to stay within free tier)

### **Optimizations Applied ✅**
1. ✅ **Changed search depth**: Advanced → Basic (2 credits → 1 credit per query)
2. ✅ **Result**: 1,680 credits/month → 840 credits/month
3. ✅ **Savings**: $168/month → $0/month (100% cost reduction!)

### **Optimized Monthly Cost**
- **Daily only**: **~$0.25/month** ✅ (Tavily free, only OpenAI costs)
- **Daily + 5 manual/month**: **~$0.29/month** ✅ (stays within free tier)
- **Weekly schedule**: **~$0.03/month** ✅ (maximum buffer for manual triggers)

---

## 🔧 Implementation Notes

### **To Implement Optimizations:**

1. **Reduce queries** in `backend/agent/search.py`:
   ```python
   # Reduce from 7 to 3-4 queries per category
   planning_keywords = planning_keywords[:4]  # Keep first 4
   ```

2. **Change search depth** in `backend/agent/search.py`:
   ```python
   response = self.client.search(
       query=query,
       search_depth="basic",  # Changed from "advanced"
       max_results=max_results,
   )
   ```

3. **Monitor costs**:
   - Set up billing alerts in Tavily dashboard
   - Track OpenAI usage in OpenAI dashboard
   - Review GitHub Actions minutes usage

---

## 📞 Support & Resources

- **Tavily Pricing**: https://tavily.com/pricing
- **OpenAI Pricing**: https://openai.com/pricing
- **Supabase Pricing**: https://supabase.com/pricing
- **Vercel Pricing**: https://vercel.com/pricing
- **GitHub Actions Pricing**: https://github.com/pricing

---

**Last Updated**: November 2024
**System Version**: 1.0

