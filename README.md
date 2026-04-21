# 🤖 Agentic AI Price Intelligence System

Find the best price for any product across the internet using a 7-agent AI pipeline powered by Groq (Llama3) + SerpAPI.

## Project Structure

```
price_ai/
├── agents/
│   ├── planner_agent.py        # LLM-powered dynamic planning
│   ├── search_agent.py         # SerpAPI multi-query search
│   ├── product_agent.py        # Real scraping (JSON-LD, meta, selectors)
│   ├── collection_agent.py     # Aggregation + deduplication
│   ├── trust_agent.py          # Granular trust scoring (0-10)
│   ├── decision_agent.py       # LLM-powered weighted ranking
│   └── recommendation_agent.py # LLM natural language explanation
├── core/
│   ├── orchestrator.py         # Pipeline coordinator + self-correction
│   └── llm.py                  # Groq API helper with retry
├── app.py                      # Streamlit UI
├── config.py                   # API keys + trusted domains
├── requirements.txt
└── .env                        # Your API keys (never commit this!)
```

## Setup

### Step 1: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Add your API keys
Edit `.env` file:
```
SERP_API_KEY=your_serpapi_key_here
GROQ_API_KEY=your_groq_api_key_here
```

Get keys from:
- SerpAPI: https://serpapi.com (free 100 searches/month)
- Groq: https://console.groq.com (free, fast Llama3)

### Step 3: Run
```bash
streamlit run app.py
```

## How It Works

```
User Input (product name OR link)
        ↓
🧠 Planner Agent    → LLM understands query, creates dynamic plan
        ↓
🔍 Search Agent     → 3 targeted SerpAPI queries
        ↓
🕷️ Product Agent    → Extracts price/rating via JSON-LD + scraping
        ↓
📦 Collection Agent → Aggregates, deduplicates (NO fake data)
        ↓
🛡️ Trust Agent      → Scores each source 0-10
        ↓
⚖️ Decision Agent   → LLM ranks by price + trust + rating
        ↓
💬 Recommend Agent  → LLM explains why this is the best deal
        ↓
🖥️ Streamlit UI     → Beautiful results display
```

## Key Improvements Over Original System

| Feature | Old System | New System |
|---|---|---|
| LLM/AI | ❌ None | ✅ Groq Llama3 |
| Planning | ❌ Hardcoded | ✅ Dynamic LLM |
| Trust Score | ❌ Binary (0/1) | ✅ Granular (0-10) |
| Decision | ❌ Simple sort | ✅ LLM weighted |
| Recommendation | ❌ First item | ✅ LLM explanation |
| Fake ratings | ❌ random() used | ✅ None — honest data |
| Self-correction | ❌ No | ✅ Retry on failure |
