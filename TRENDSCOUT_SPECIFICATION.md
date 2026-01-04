# TRENDSCOUT CORE ENGINE - TECHNICAL SPECIFICATION

## 🎯 PROJECT OVERVIEW

**Product Name:** TrendScout
**Description:** Daily trend discovery engine that sends coffee shops (and other businesses) the top 3 viral trends every morning at 7 AM via SMS/app with AI-generated business ideas.

**Business Model:**
- $100/month subscription
- Target: 1,000 clients (20 per state × 50 states)
- Revenue Goal: $100,000 MRR

**Core Value Proposition:**
Every morning at 7 AM, business owners receive:
1. Top 3 trending items in their vertical (e.g., "Lavender Oat Milk Latte")
2. AI-generated implementation guide (recipe, pricing, ROI projection)
3. Marketing templates (Instagram captions, etc.)

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                    TRENDSCOUT PIPELINE                      │
│                                                             │
│  1. DATA COLLECTION (Every 2-6 hours)                      │
│     ├─ TikTok (Apify API)                                  │
│     ├─ Instagram (Apify API)                               │
│     ├─ Google Trends (pytrends)                            │
│     ├─ Reddit (PRAW)                                       │
│     └─ YouTube (YouTube Data API)                          │
│                                                             │
│  2. FILTERING & NORMALIZATION                              │
│     ├─ Remove duplicates                                   │
│     ├─ Filter by vertical (coffee/restaurant/etc)          │
│     └─ Normalize data format                               │
│                                                             │
│  3. AI ANALYSIS (Claude API)                               │
│     ├─ Extract food/product items                          │
│     ├─ Sentiment analysis                                  │
│     ├─ Category classification                             │
│     └─ Quality scoring                                     │
│                                                             │
│  4. TREND SCORING (UTS Algorithm)                          │
│     ├─ Velocity (growth rate)                              │
│     ├─ Momentum (sustained interest)                       │
│     ├─ Engagement (likes, comments, shares)                │
│     ├─ Cross-platform presence                             │
│     └─ Geographic spread                                   │
│                                                             │
│  5. TOP 3 SELECTION                                        │
│     └─ Highest UTS scores                                  │
│                                                             │
│  6. BUSINESS IDEAS GENERATION (Claude API)                 │
│     ├─ Recipe/implementation guide                         │
│     ├─ Pricing recommendation                              │
│     ├─ ROI projection                                      │
│     └─ Marketing templates                                 │
│                                                             │
│  7. DELIVERY (7 AM daily)                                  │
│     ├─ SMS via Twilio                                      │
│     └─ App notification                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 PROJECT STRUCTURE

```
trendscout-core/
│
├── config/
│   ├── __init__.py
│   ├── settings.py              # All configuration (API keys, etc.)
│   └── verticals.py              # Vertical-specific configs
│
├── data_collectors/
│   ├── __init__.py
│   ├── base_collector.py        # Abstract base class
│   ├── tiktok_collector.py      # Apify TikTok scraper
│   ├── instagram_collector.py   # Apify Instagram scraper
│   ├── google_trends_collector.py  # pytrends
│   ├── reddit_collector.py      # PRAW
│   └── youtube_collector.py     # YouTube Data API
│
├── analyzers/
│   ├── __init__.py
│   ├── data_filter.py           # Filter & normalize data
│   ├── ai_analyzer.py           # Claude API analysis
│   └── trend_scorer.py          # UTS scoring algorithm
│
├── generators/
│   ├── __init__.py
│   └── idea_generator.py        # AI business ideas generation
│
├── database/
│   ├── __init__.py
│   ├── models.py                # SQLAlchemy models
│   └── db.py                    # Database connection
│
├── scheduler/
│   ├── __init__.py
│   └── daily_job.py             # Cron job for 7 AM execution
│
├── utils/
│   ├── __init__.py
│   └── helpers.py               # Utility functions
│
├── tests/
│   └── test_pipeline.py
│
├── main.py                      # Main pipeline orchestrator
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment variables
├── README.md                    # Setup instructions
└── docker-compose.yml           # Optional: Docker setup
```

---

## 🔧 TECHNOLOGY STACK

### **Language:**
- Python 3.11+

### **Data Collection:**
- `apify-client` - TikTok & Instagram scraping
- `pytrends` - Google Trends (unofficial API)
- `praw` - Reddit API
- `google-api-python-client` - YouTube Data API

### **AI/Analysis:**
- `anthropic` - Claude API for analysis & idea generation
- `openai` (optional backup)

### **Database:**
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL driver (or SQLite for MVP)

### **Scheduling:**
- `apscheduler` - Job scheduling

### **HTTP/Async:**
- `httpx` - Async HTTP client
- `asyncio` - Async operations

### **Environment:**
- `python-dotenv` - Environment variables
- `pydantic` - Data validation

---

## 📦 REQUIREMENTS.TXT

```txt
# Data Collection
apify-client==1.7.1
pytrends==4.9.2
praw==7.7.1
google-api-python-client==2.108.0

# AI
anthropic==0.18.1
openai==1.12.0

# Database
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1

# Async & HTTP
httpx==0.26.0
aiohttp==3.9.1

# Utilities
python-dotenv==1.0.1
pydantic==2.5.3
pydantic-settings==2.1.0

# Scheduling
apscheduler==3.10.4

# SMS (for future)
twilio==8.11.1

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
```

---

## 🔑 ENVIRONMENT VARIABLES (.env)

```bash
# API Keys
APIFY_API_KEY=your_apify_key_here
ANTHROPIC_API_KEY=your_claude_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_key_here  # Optional backup

# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=TrendScout/1.0

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/trendscout
# Or for SQLite: DATABASE_URL=sqlite:///./trendscout.db

# General Settings
VERTICAL=coffee  # Options: coffee, restaurant, barbershop, etc.
DEBUG=True
LOG_LEVEL=INFO
```

---

## 💾 DATABASE MODELS

### **Trend Model:**
```python
class Trend:
    id: int (PK)
    trend_name: str          # "Lavender Oat Milk Latte"
    category: str            # "coffee_drink", "pastry", etc.
    vertical: str            # "coffee", "restaurant"
    
    # Scores
    uts_score: float         # 0-100
    velocity_score: float
    momentum_score: float
    engagement_score: float
    
    # Metadata
    first_seen: datetime
    last_updated: datetime
    status: str              # "rising", "peak", "declining"
    
    # AI Analysis
    description: str
    sentiment: str           # "positive", "negative", "neutral"
    ai_confidence: float     # 0-1
```

### **Post Model:**
```python
class Post:
    id: int (PK)
    platform: str            # "tiktok", "instagram", "google_trends", etc.
    post_id: str             # Platform-specific ID
    content: str             # Post text/description
    url: str
    
    # Metrics
    views: int
    likes: int
    comments: int
    shares: int
    
    # Timestamps
    posted_at: datetime
    collected_at: datetime
    
    # Relations
    trend_id: int (FK to Trend)
```

### **BusinessIdea Model:**
```python
class BusinessIdea:
    id: int (PK)
    trend_id: int (FK)
    vertical: str
    
    # Implementation Guide
    recipe_instructions: str  # For coffee: actual recipe
    ingredients: list[str]
    equipment_needed: list[str]
    
    # Business Metrics
    suggested_price: float
    cost_estimate: float
    margin_percent: float
    roi_projection: str       # "$6,880/month"
    
    # Marketing
    marketing_caption: str
    hashtags: list[str]
    
    # Generated
    generated_at: datetime
```

---

## 🔄 CORE PIPELINE LOGIC

### **main.py - Pipeline Orchestrator**

```python
"""
Main pipeline execution flow
"""

async def run_pipeline(vertical: str = "coffee") -> list[dict]:
    """
    Execute complete TrendScout pipeline
    
    Args:
        vertical: Business type (coffee, restaurant, etc.)
        
    Returns:
        List of top 3 trends with business ideas
    """
    
    # 1. COLLECT DATA
    collectors = [
        TikTokCollector(),
        InstagramCollector(),
        GoogleTrendsCollector(),
        RedditCollector(),
        YouTubeCollector()
    ]
    
    raw_data = []
    for collector in collectors:
        data = await collector.collect(vertical=vertical)
        raw_data.extend(data)
    
    # 2. FILTER & NORMALIZE
    filtered_data = DataFilter.filter_and_normalize(
        raw_data, 
        vertical=vertical
    )
    
    # 3. AI ANALYSIS
    analyzed_trends = await AIAnalyzer.analyze_batch(filtered_data)
    
    # 4. SCORE TRENDS (UTS Algorithm)
    scored_trends = TrendScorer.score_trends(analyzed_trends)
    
    # 5. SELECT TOP 3
    top_3 = sorted(scored_trends, key=lambda x: x['uts_score'], reverse=True)[:3]
    
    # 6. GENERATE BUSINESS IDEAS
    final_trends = []
    for trend in top_3:
        idea = await IdeaGenerator.generate(trend, vertical=vertical)
        final_trends.append({
            'trend': trend,
            'business_idea': idea
        })
    
    return final_trends
```

---

## 🤖 AI ANALYZER (Claude API)

### **Prompt Template for Trend Analysis:**

```python
ANALYSIS_PROMPT = """
Analyze this social media post to extract food/beverage trends.

POST DATA:
Platform: {platform}
Content: {content}
Engagement: {likes} likes, {comments} comments, {shares} shares
Posted: {posted_at}

TASKS:
1. Identify the main food/beverage item mentioned
2. Categorize it (drink, pastry, main dish, snack, etc.)
3. Assess sentiment (positive/negative/neutral)
4. Rate viral potential (0-10)
5. Determine if applicable to coffee shops/restaurants

Respond in JSON format:
{{
  "item_name": "...",
  "category": "...",
  "sentiment": "positive|negative|neutral",
  "viral_potential": 0-10,
  "restaurant_applicable": true|false,
  "reasoning": "..."
}}
"""
```

### **Prompt Template for Business Idea Generation:**

```python
IDEA_GENERATION_PROMPT = """
Generate a complete business implementation guide for this trend.

TREND: {trend_name}
CATEGORY: {category}
VIRAL METRICS:
- TikTok: {tiktok_views} views
- Instagram: {instagram_likes} likes
- UTS Score: {uts_score}/100

TARGET BUSINESS: Coffee shop

CREATE:
1. Recipe/Implementation:
   - Exact ingredients with quantities
   - Step-by-step preparation
   - Equipment needed
   - Prep time

2. Pricing Strategy:
   - Suggested retail price
   - Cost of goods sold (estimate)
   - Profit margin %

3. ROI Projection:
   - Expected daily sales
   - Monthly revenue projection
   - Time to profitability

4. Marketing:
   - Instagram caption (50 words max)
   - 5 relevant hashtags
   - Best posting time

Respond in JSON format:
{{
  "recipe": {{
    "ingredients": [...],
    "instructions": [...],
    "equipment": [...],
    "prep_time_minutes": 0
  }},
  "pricing": {{
    "suggested_price": 0.00,
    "cogs": 0.00,
    "margin_percent": 0.00
  }},
  "roi": {{
    "daily_sales_estimate": 0,
    "monthly_revenue": 0,
    "roi_summary": "..."
  }},
  "marketing": {{
    "caption": "...",
    "hashtags": [...],
    "best_time": "..."
  }}
}}
"""
```

---

## 📊 UTS SCORING ALGORITHM

### **Formula:**

```python
def calculate_uts_score(trend_data: dict) -> float:
    """
    Universal Trend Score (UTS)
    
    UTS = (V × M × E × G × P) / (T × C)
    
    Where:
    V = Velocity (growth rate)
    M = Momentum (sustained interest over 5 days)
    E = Engagement quality
    G = Geographic spread
    P = Platform diversity
    T = Time decay
    C = Competition
    
    Returns: Score from 0-100
    """
    
    # Calculate each component
    V = calculate_velocity(trend_data['metrics'])
    M = calculate_momentum(trend_data['historical_data'])
    E = calculate_engagement(trend_data['metrics'])
    G = calculate_geographic(trend_data['locations'])
    P = calculate_platform_diversity(trend_data['platforms'])
    T = calculate_time_decay(trend_data['age_hours'])
    C = calculate_competition(trend_data['similar_count'])
    
    # Apply formula
    uts_raw = (V * M * E * G * P) / (T * C)
    
    # Normalize to 0-100
    uts_normalized = normalize_score(uts_raw, 0, 100)
    
    return uts_normalized
```

### **Component Calculations:**

```python
def calculate_velocity(metrics: dict) -> float:
    """
    Velocity = (current_value - previous_value) / time_period
    Normalized to 0-100
    """
    current = metrics['current_views']
    previous = metrics['views_6h_ago']
    velocity = (current - previous) / 6  # per hour
    return normalize(velocity, 0, 100)

def calculate_momentum(historical: list) -> float:
    """
    Momentum = average growth over last 5 days
    Higher if acceleration is positive
    """
    growth_rates = []
    for i in range(1, len(historical)):
        rate = (historical[i] - historical[i-1]) / historical[i-1]
        growth_rates.append(rate)
    
    avg_growth = sum(growth_rates) / len(growth_rates)
    return normalize(avg_growth * 100, 0, 100)

def calculate_engagement(metrics: dict) -> float:
    """
    Engagement = (comments×3 + shares×5 + saves×7) / views × 100
    """
    engagement = (
        metrics['comments'] * 3 +
        metrics['shares'] * 5 +
        metrics.get('saves', 0) * 7
    ) / metrics['views'] * 100
    
    return min(engagement, 100)  # Cap at 100
```

---

## 📅 SCHEDULER (7 AM Daily)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

# Run pipeline every day at 7:00 AM
scheduler.add_job(
    run_pipeline,
    trigger=CronTrigger(hour=7, minute=0),
    id='daily_trend_discovery',
    name='Daily Trend Discovery',
    replace_existing=True
)

scheduler.start()
```

---

## 🔌 DATA COLLECTOR IMPLEMENTATIONS

### **TikTok Collector (Apify):**

```python
from apify_client import ApifyClient

class TikTokCollector:
    def __init__(self):
        self.client = ApifyClient(os.getenv('APIFY_API_KEY'))
    
    async def collect(self, vertical: str) -> list[dict]:
        """
        Collect TikTok posts for given vertical
        """
        # Get keywords for vertical
        keywords = get_vertical_keywords(vertical)  # e.g., ["coffee", "latte", "espresso"]
        
        results = []
        for keyword in keywords:
            # Run Apify actor
            run = self.client.actor("bebity/tiktok-scraper").call(
                run_input={
                    "hashtags": [f"#{keyword}"],
                    "resultsPerPage": 50,
                    "maxProfilesPerQuery": 1
                }
            )
            
            # Get results
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append({
                    'platform': 'tiktok',
                    'post_id': item['id'],
                    'content': item['text'],
                    'url': item['webVideoUrl'],
                    'views': item['playCount'],
                    'likes': item['diggCount'],
                    'comments': item['commentCount'],
                    'shares': item['shareCount'],
                    'posted_at': item['createTime']
                })
        
        return results
```

### **Google Trends Collector:**

```python
from pytrends.request import TrendReq

class GoogleTrendsCollector:
    def __init__(self):
        self.pytrends = TrendReq(hl='en-US', tz=360)
    
    async def collect(self, vertical: str) -> list[dict]:
        """
        Collect Google Trends data
        """
        keywords = get_vertical_keywords(vertical)
        
        # Build payload
        self.pytrends.build_payload(
            keywords,
            cat=0,
            timeframe='now 7-d',
            geo='US'
        )
        
        # Get interest over time
        interest_df = self.pytrends.interest_over_time()
        
        # Get rising searches
        rising_df = self.pytrends.trending_searches(pn='united_states')
        
        results = []
        for keyword in keywords:
            if keyword in interest_df.columns:
                interest_score = interest_df[keyword].iloc[-1]
                
                results.append({
                    'platform': 'google_trends',
                    'post_id': f"gt_{keyword}",
                    'content': keyword,
                    'interest_score': interest_score,
                    'is_breakout': interest_score > 80
                })
        
        return results
```

---

## 🚀 GETTING STARTED (for Cursor)

### **Step 1: Setup Environment**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
```

### **Step 2: Get API Keys**

1. **Apify:** https://console.apify.com/account/integrations
2. **Anthropic (Claude):** https://console.anthropic.com/
3. **YouTube:** https://console.cloud.google.com/apis/credentials
4. **Reddit:** https://www.reddit.com/prefs/apps

### **Step 3: Run Pipeline**

```bash
# Test run
python main.py

# Or with specific vertical
python main.py --vertical=coffee
```

---

## 📝 CURSOR AI PROMPTS

### **Prompt 1: Generate Project Structure**

```
Create a Python project called "trendscout-core" with this exact structure:

trendscout-core/
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── verticals.py
├── data_collectors/
│   ├── __init__.py
│   ├── base_collector.py
│   ├── tiktok_collector.py
│   ├── instagram_collector.py
│   ├── google_trends_collector.py
│   ├── reddit_collector.py
│   └── youtube_collector.py
├── analyzers/
│   ├── __init__.py
│   ├── data_filter.py
│   ├── ai_analyzer.py
│   └── trend_scorer.py
├── generators/
│   ├── __init__.py
│   └── idea_generator.py
├── database/
│   ├── __init__.py
│   ├── models.py
│   └── db.py
├── scheduler/
│   ├── __init__.py
│   └── daily_job.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
├── main.py
├── requirements.txt
├── .env.example
└── README.md

Initialize all __init__.py files and create the basic structure.
```

### **Prompt 2: Implement Main Pipeline**

```
In main.py, implement the TrendScout core pipeline with these requirements:

1. Create an async function `run_pipeline(vertical: str)` that:
   - Collects data from 5 sources (TikTok, Instagram, Google Trends, Reddit, YouTube)
   - Filters and normalizes the data
   - Uses Claude AI to analyze trends
   - Scores trends using UTS algorithm (Velocity × Momentum × Engagement × Geographic × Platform) / (Time Decay × Competition)
   - Selects top 3 trends
   - Generates business ideas with Claude AI

2. Include proper error handling and logging
3. Return structured data with trend details and business recommendations

Use Python 3.11+, async/await patterns, and type hints.
```

### **Prompt 3: Implement TikTok Collector**

```
In data_collectors/tiktok_collector.py, create a TikTokCollector class that:

1. Uses Apify's "bebity/tiktok-scraper" actor
2. Searches for hashtags based on vertical (coffee, restaurant, etc.)
3. Collects: post_id, content, url, views, likes, comments, shares, posted_at
4. Returns list of normalized dict objects
5. Handles API errors gracefully
6. Implements rate limiting

Use apify-client library and async operations.
```

### **Prompt 4: Implement AI Analyzer**

```
In analyzers/ai_analyzer.py, create an AIAnalyzer class that:

1. Uses Anthropic's Claude API (anthropic library)
2. Analyzes batches of social media posts
3. For each post, extracts:
   - Main food/beverage item name
   - Category (drink, pastry, main dish, etc.)
   - Sentiment (positive/negative/neutral)
   - Viral potential score (0-10)
   - Restaurant applicability (boolean)

4. Returns structured JSON responses
5. Includes retry logic for API failures
6. Batch processes up to 100 posts efficiently

Prompt template provided in spec above.
```

### **Prompt 5: Implement UTS Scoring**

```
In analyzers/trend_scorer.py, implement the UTS (Universal Trend Score) algorithm:

Formula: UTS = (V × M × E × G × P) / (T × C)

Where:
- V = Velocity: (current_views - views_6h_ago) / 6
- M = Momentum: Average growth rate over 5 days
- E = Engagement: (comments×3 + shares×5 + saves×7) / views × 100
- G = Geographic: log₂(countries + 1) / log₂(195)
- P = Platform diversity: platforms_count / 10 × 100
- T = Time decay: 1 + (age_hours / 24) × 0.1
- C = Competition: 1 + log₁₀(similar_content + 1)

Normalize final score to 0-100 range.
Include helper functions for each component.
```

### **Prompt 6: Implement Business Idea Generator**

```
In generators/idea_generator.py, create an IdeaGenerator class that:

1. Uses Claude API to generate complete business implementation guides
2. For a given trend, produces:
   - Recipe/implementation (ingredients, instructions, equipment, time)
   - Pricing strategy (retail price, COGS, margin)
   - ROI projection (daily sales, monthly revenue)
   - Marketing templates (Instagram caption, hashtags, best posting time)

3. Returns structured JSON matching BusinessIdea model
4. Specific to vertical (coffee shop, restaurant, etc.)

Use the prompt template from spec above.
```

### **Prompt 7: Setup Database Models**

```
In database/models.py, create SQLAlchemy models for:

1. Trend:
   - id, trend_name, category, vertical
   - uts_score, velocity_score, momentum_score, engagement_score
   - first_seen, last_updated, status
   - description, sentiment, ai_confidence

2. Post:
   - id, platform, post_id, content, url
   - views, likes, comments, shares
   - posted_at, collected_at, trend_id (FK)

3. BusinessIdea:
   - id, trend_id (FK), vertical
   - recipe_instructions, ingredients, equipment_needed
   - suggested_price, cost_estimate, margin_percent, roi_projection
   - marketing_caption, hashtags
   - generated_at

Include proper relationships and indexes.
```

---

## ✅ TESTING CHECKLIST

After Cursor builds the code, test in this order:

1. ✅ **Environment Setup**
   - All dependencies install without errors
   - .env file configured with API keys

2. ✅ **Individual Collectors**
   - Test each collector separately
   - Verify data format matches spec

3. ✅ **AI Analyzer**
   - Test with sample post
   - Verify JSON response format

4. ✅ **Scoring Algorithm**
   - Test with mock data
   - Verify scores are 0-100

5. ✅ **Full Pipeline**
   - Run `python main.py`
   - Should return 3 trends with ideas
   - Time: ~2-5 minutes

6. ✅ **Scheduler**
   - Test cron job setup
   - Verify runs at 7 AM

---

## 🎯 SUCCESS CRITERIA

Pipeline is successful when:

1. ✅ Collects 1000+ posts from all platforms
2. ✅ Filters down to 100-200 relevant posts
3. ✅ AI analyzes without errors
4. ✅ Returns exactly 3 trends
5. ✅ Each trend has complete business idea
6. ✅ UTS scores are logical (viral = 80-100)
7. ✅ Total execution time < 10 minutes
8. ✅ Can run daily at 7 AM automatically

---

## 📞 API COST ESTIMATES

**Daily Run (1000 clients):**
- Apify: $0.50/run × 1 = $0.50
- Claude API: $0.20 (analysis + generation)
- YouTube: FREE (within quota)
- Reddit: FREE
- Total: ~$0.70/day = $21/month

**Monthly (30 runs):**
- Total API costs: ~$21
- Per client cost: $0.021
- Margin: $100 - $0.021 = $99.98 (99.98%!)

---

## 🚀 NEXT STEPS AFTER CORE

Once core pipeline works:

1. **SMS Delivery** (Twilio integration)
2. **Web Dashboard** (View trends in browser)
3. **Multi-Vertical Support** (Coffee, Restaurant, Barbershop, etc.)
4. **User Management** (Accounts, subscriptions)
5. **Analytics** (Track which trends perform best)

---

## 📚 DOCUMENTATION LINKS

- Apify: https://docs.apify.com/
- Anthropic Claude: https://docs.anthropic.com/
- pytrends: https://pypi.org/project/pytrends/
- PRAW (Reddit): https://praw.readthedocs.io/
- YouTube API: https://developers.google.com/youtube/v3

---

**END OF SPECIFICATION**

This document contains everything Cursor AI needs to build TrendScout Core Engine.

Copy this entire file into Cursor and use the prompts above step-by-step!
