# Competitive Keyword Analysis

A full-stack application for analyzing Google Ads across multiple domains. Extract ad text via OCR, identify keyphrases, and visualize clusters of related keywords.

## Features

- **Multi-domain search** - Analyze ads from multiple competitors simultaneously
- **OCR text extraction** - Extract headlines, descriptions, and sitelinks from ad preview images using color-based segmentation
- **Keyphrase extraction** - Identify key phrases using YAKE algorithm with per-segment analysis
- **Unified clustering** - Group all keyphrases from all domains together using sentence embeddings + Agglomerative Clustering
- **Language detection** - Filter ads by detected language
- **Country filtering** - Search ads by geographic location

## Architecture

```
├── apps/
│   ├── api/                    # FastAPI backend (Python)
│   │   ├── app/
│   │   │   ├── api/            # API endpoints
│   │   │   │   ├── ads.py      # Main ads search endpoints
│   │   │   │   ├── health.py   # Health check
│   │   │   │   └── router.py   # Router aggregation
│   │   │   ├── core/
│   │   │   │   └── config.py   # Settings (env vars, API keys)
│   │   │   ├── schemas/
│   │   │   │   └── ads.py      # Pydantic request/response models
│   │   │   ├── services/
│   │   │   │   ├── dataforseo.py       # DataForSEO API client
│   │   │   │   ├── ad_scraper.py       # OCR text extraction
│   │   │   │   ├── keyword_extractor.py # YAKE keyphrase extraction
│   │   │   │   ├── phrase_clustering.py # Sentence embeddings + clustering
│   │   │   │   └── language_detector.py # Language detection
│   │   │   └── main.py         # FastAPI app entrypoint
│   │   └── requirements.txt
│   └── web/                    # React frontend (TypeScript)
│       ├── src/
│       │   ├── components/     # UI components
│       │   │   ├── SearchForm/       # Domain input, filters
│       │   │   ├── DomainTagInput/   # Multi-domain tag input
│       │   │   ├── AdCard/           # Individual ad display
│       │   │   ├── AdResults/        # Results container + tabs
│       │   │   ├── ClusterView/      # Keyphrase cluster visualization
│       │   │   ├── Tabs/             # Tab navigation
│       │   │   └── ErrorMessage/     # Error display
│       │   ├── hooks/          # Custom React hooks
│       │   │   ├── useAdsSearch.ts   # Search state management
│       │   │   ├── useLocations.ts   # Country list fetching
│       │   │   └── useLanguages.ts   # Language list fetching
│       │   ├── services/
│       │   │   └── api.ts      # Backend API client
│       │   ├── types/
│       │   │   └── ads.ts      # TypeScript interfaces
│       │   ├── App.tsx         # Main app component
│       │   └── main.tsx        # React entrypoint
│       └── package.json
```

## How It Works

### Data Flow

1. **User enters domains** → Frontend sends POST to `/ads/domains/with-text`
2. **Backend fetches ad metadata** → Calls DataForSEO API for each domain (in parallel)
3. **OCR extracts text** → Downloads preview images, uses color-based segmentation to extract:
   - Blue text → Headlines and sitelinks
   - Gray text → Descriptions (URLs filtered out)
4. **Keyphrase extraction** → YAKE extracts 1-5 phrases per ad, processing headline/description/sitelinks separately to avoid cross-boundary phrases
5. **Unified clustering** → All keyphrases from ALL domains are clustered together using:
   - Sentence embeddings (`all-MiniLM-L6-v2`)
   - Agglomerative clustering with cosine distance
   - Post-merge by dominant keyword
6. **Response** → Ads + unified clustering data returned to frontend

### Key Services

| Service | Purpose |
|---------|---------|
| `dataforseo.py` | Fetches ad metadata from DataForSEO SERP Google Ads Search API |
| `ad_scraper.py` | Downloads images, applies color masks, runs Tesseract OCR |
| `keyword_extractor.py` | Cleans text, extracts keyphrases using YAKE |
| `phrase_clustering.py` | Embeds phrases, clusters with AgglomerativeClustering |
| `language_detector.py` | Detects language using `langdetect` library |

## Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **Tesseract OCR** - `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Linux)
- **DataForSEO API credentials**

## Setup

### Backend

```bash
cd apps/api

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cat > .env << EOF
DATAFORSEO_LOGIN=your_login
DATAFORSEO_PASSWORD=your_password
EOF

# Run server
uvicorn app.main:app --reload --port 8000
```

API available at:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

### Frontend

```bash
cd apps/web

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend available at http://localhost:5173

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ads/domains/with-text` | POST | Search multiple domains, extract text, cluster keyphrases |
| `/ads/domain/with-text` | POST | Search single domain (legacy) |
| `/ads/locations` | GET | Get available countries |
| `/ads/languages` | GET | Get supported languages |
| `/health` | GET | Health check |

### Example Request

```bash
curl -X POST http://localhost:8000/ads/domains/with-text \
  -H "Content-Type: application/json" \
  -d '{
    "domains": ["theliven.com", "betterhelp.com"],
    "location_code": 2840,
    "depth": 10
  }'
```

## Tech Stack

### Backend
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [httpx](https://www.python-httpx.org/) - Async HTTP client
- [pytesseract](https://github.com/madmaze/pytesseract) - OCR
- [YAKE](https://github.com/LIAAD/yake) - Keyphrase extraction
- [sentence-transformers](https://www.sbert.net/) - Text embeddings
- [scikit-learn](https://scikit-learn.org/) - Clustering
- [langdetect](https://github.com/Mimino666/langdetect) - Language detection

### Frontend
- [React 19](https://react.dev/) - UI library
- [TypeScript](https://www.typescriptlang.org/) - Type safety
- [Vite](https://vitejs.dev/) - Build tool

## License

MIT
