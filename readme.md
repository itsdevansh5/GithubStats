# 📊 GitHub Language Stats API

### 🚀 FastAPI + Redis + MongoDB Atlas + GitHub API

A backend API that analyzes GitHub repository languages, computes
language usage percentages, stores historical snapshots, caches recent results, and serves a dynamically generated SVG stats card.

Built with **FastAPI, MongoDB Atlas, GitHub API, and async httpx**, and
deployed on Render.

------------------------------------------------------------------------

## 🌟 Overview

This backend project:

-   Fetches repositories belonging to a GitHub user
-   Skips forked and archived repositories
-   Fetches language statistics for repositories concurrently with
    **bounded concurrency**
-   Aggregates language byte counts across repositories
-   Computes language usage percentages
-   Caches the latest result for 24 hours using Redis
-   Stores historical snapshots in MongoDB
-   Validates GitHub usernames at the API boundary
-   Generates dynamic SVG GitHub stats cards
-   Escapes dynamic values before inserting them into SVG/XML
-   Exposes API endpoints with Pydantic models
-   Uses asynchronous FastAPI + httpx + Motor
-   Uses Pydantic Settings for typed environment configuration
-   Uses long-lived HTTPX, Redis, and MongoDB clients managed by FastAPI lifespan
-   Is deployed on Render

The project is being developed as a practical backend engineering
project, with emphasis on API design, asynchronous programming,
concurrency, caching, database usage, and production-oriented code
structure.

------------------------------------------------------------------------

------------------------------------------------------------------------

## 📌 Current Architecture Snapshot

``` text
FastAPI
  │
  ├── Pydantic validation
  │
  ├── Stats Service
  │      │
  │      ├── Redis cache-aside (24h TTL)
  │      │
  │      └── GitHub API
  │             │
  │             ├── Link-header pagination
  │             └── bounded concurrency
  │
  ├── MongoDB history
  │
  └── SVG generator
         └── XML-escape dynamic values

FastAPI lifespan owns:
  ├── HTTPX client
  ├── Redis client
  └── MongoDB client

Configuration:
  .env / OS environment
          ↓
  Pydantic Settings
          ↓
       Settings
```

## 🧠 Tech Stack

  Layer                      Technology
  -------------------------- ----------------------------------
  Backend Framework          **FastAPI**
  HTTP Client                **httpx (async)**
  Database                   **MongoDB Atlas**
  Database Driver            **Motor (async)**
  Cache                       **Redis Cloud / redis-py (async)**
  Deployment                 **Render**
  Configuration              **Pydantic Settings**
  Data Validation / Models   **Pydantic**
  Concurrency                **asyncio + Semaphore + gather**
  Output Format              **SVG**

------------------------------------------------------------------------

## 🗂 Project Structure

``` text
github-stats/
│── app/
│   ├── main.py
│   ├── github_api.py
│   ├── github_service.py
│   ├── stats_service.py
│   ├── database.py
│   ├── models.py
│   ├── svg_generator.py
│
│── requirements.txt
│── .env
│── .gitignore
│── README.md
```

> The exact structure may evolve as the project is further
> productionized.

------------------------------------------------------------------------

# 🌐 Live Demo

### 🚀 Base URL

``` text
https://githubstats-gqcp.onrender.com/
```

### 📘 Swagger Docs

``` text
https://githubstats-gqcp.onrender.com/docs
```

### Embed the SVG card in your GitHub README

``` html
<img src="https://githubstats-gqcp.onrender.com/card/stats/YOUR_GITHUB_USERNAME" />
```

Example:

``` html
<img src="https://githubstats-gqcp.onrender.com/card/stats/itsdevansh5" />
```

------------------------------------------------------------------------

# 📡 API Documentation

## 1️⃣ `GET /`

### Health check route

Returns API status.

**Example:**

``` json
{
  "message": "GitHub Stats API is running!"
}
```

------------------------------------------------------------------------

## 2️⃣ `GET /stats/{username}`

Fetches the latest GitHub language statistics.

### ✨ Features

-   Validates the GitHub username format
-   Fetches repositories
-   Skips forked and archived repositories
-   Fetches repository language data concurrently
-   Uses bounded concurrency to avoid excessive simultaneous GitHub
    requests
-   Aggregates language byte counts
-   Computes percentages
-   Uses 24-hour caching
-   Stores historical snapshots in MongoDB

### Example

``` text
/stats/itsdevansh5
```

### Response

``` json
{
  "username": "itsdevansh5",
  "cached": false,
  "percentages": {
    "Python": 93.13,
    "C++": 0.33,
    "HTML": 0.36
  }
}
```

If a cached result is available:

``` json
{
  "username": "itsdevansh5",
  "cached": true,
  "percentages": {
    "Python": 93.13,
    "C++": 0.33,
    "HTML": 0.36
  }
}
```

------------------------------------------------------------------------

## 3️⃣ `GET /history/{username}`

Returns historical language-statistics snapshots for a user.

### Example

``` text
/history/itsdevansh5
```

### Response

``` json
{
  "username": "itsdevansh5",
  "history": [
    {
      "fetched_at": "2026-08-10T12:34:11",
      "percentages": {
        "Python": 93.13,
        "C++": 0.33,
        "HTML": 0.36
      }
    },
    {
      "fetched_at": "2026-08-11T12:34:11",
      "percentages": {
        "Python": 92.80,
        "C++": 0.50,
        "HTML": 0.40
      }
    }
  ]
}
```

------------------------------------------------------------------------

## 4️⃣ `GET /card/stats/{username}`

Generates a dynamic **SVG GitHub language-stats card**.

The username is now a **path parameter**, making the API consistent with
the other username-based endpoints.

### Example

``` text
/card/stats/itsdevansh5
```

### Embed in GitHub README

``` html
<img src="https://githubstats-gqcp.onrender.com/card/stats/itsdevansh5" />
```

The endpoint returns:

``` text
Content-Type: image/svg+xml
```

so browsers and GitHub-compatible clients can render the response as an
SVG image.

------------------------------------------------------------------------

# ⚡ Asynchronous GitHub Fetching

Repository language data is fetched using `httpx.AsyncClient`.

Instead of waiting for every repository request sequentially:

``` text
Repo 1 → wait → Repo 2 → wait → Repo 3 → wait
```

the service creates coroutine objects for valid repositories and
coordinates them with:

``` python
asyncio.gather(...)
```

A semaphore limits the number of GitHub requests that can be active
simultaneously.

The current concurrency limit is:

``` python
MAX_CONCURRENT_GITHUB_REQUESTS = 5
```

Conceptually:

``` text
Many repository coroutines
          ↓
    asyncio.gather()
          ↓
    Semaphore(5)
          ↓
Maximum 5 active GitHub requests
          ↓
As one finishes, another can enter
```

This provides concurrency without creating an uncontrolled burst of
requests against the GitHub API.

Expected repository-level HTTP/validation failures are handled
independently so that one problematic repository does not fail the
entire statistics calculation.

------------------------------------------------------------------------

# 🔐 Username Validation

GitHub usernames are validated at the API boundary before GitHub is
contacted.

The validation checks that the supplied username follows the expected
GitHub username format.

This prevents obviously invalid input from unnecessarily reaching the
GitHub API.

Validation and resource existence are treated separately:

``` text
Invalid username format
        ↓
API validation error

Valid format
        ↓
GitHub API request
        ↓
User exists / does not exist
```

The same username validation rule is intended to be reused across:

``` text
/stats/{username}
/history/{username}
/card/stats/{username}
```

------------------------------------------------------------------------

# 🛡️ SVG Output Safety

The SVG card is generated dynamically from data returned by the
application and GitHub.

Dynamic values such as:

-   GitHub username
-   GitHub language names

are escaped before being inserted into the SVG/XML markup.

For example:

``` text
&
```

is represented safely inside XML as:

``` text
&amp;
```

and:

``` text
<
```

becomes:

``` text
&lt;
```

This ensures dynamic data is interpreted as **text/data rather than
SVG/XML markup**.

The SVG markup itself is not escaped; only dynamic values inserted into
that markup are escaped.

------------------------------------------------------------------------

# 🧮 How Percentages Are Calculated

GitHub returns byte counts for each language.

Example:

``` text
Python → 63697231
C++    → 224954
HTML   → 246905
```

The service aggregates the byte counts across all valid repositories.

The percentage formula is:

``` text
percent = (bytes_of_language / total_language_bytes) × 100
```

The resulting percentages are rounded to two decimal places.

The raw byte counts are used internally for aggregation and percentage
calculation; the API response focuses on the calculated percentages.

------------------------------------------------------------------------

# 🗄️ Caching and Historical Data

The current architecture deliberately gives Redis and MongoDB different
responsibilities.

### Redis: latest computed result

Redis is the disposable cache for the latest statistics.

Cache key convention:

``` text
gh:langpct:<username>
```

Example:

``` text
gh:langpct:itsdevansh5
```

The key naming convention is only for organization; Redis does not assign
special meaning to the colon-separated parts.

The cache uses a **24-hour TTL**.

``` text
Request
   ↓
Redis GET
   ↓
Fresh cached result?
 ┌──────┴──────┐
YES           NO
 │             │
 ▼             ▼
Return       GitHub API
cached          ↓
result       Calculate
                ↓
          Redis SET + TTL
                ↓
          MongoDB history
```

### MongoDB: historical snapshots

MongoDB stores durable historical results so previous calculations are
retained rather than overwritten.

``` text
Redis
  │
  └── latest / temporary
          │
          │ TTL
          ▼
       expires

MongoDB
  │
  └── historical snapshots
          │
          └── retained
```

The previous MongoDB `stats` collection is no longer required for the latest
cache because Redis now owns that responsibility. MongoDB remains responsible
for persistent history.

### Redis serialization

Redis stores the cached result as JSON text:

``` text
Python dict
    │
    │ json.dumps()
    ▼
JSON string
    │
    ▼
Redis
```

On retrieval:

``` text
Redis
  │
  ▼
JSON string
  │
  │ json.loads()
  ▼
Python dict
```

Python `datetime` values are converted to ISO 8601 strings before JSON
serialization.

---

# 🧱 Current Architecture

``` text
                         ┌─────────────────────┐
                         │       Client        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │       Routes        │
                         └──────────┬──────────┘
                                    │
                         username validation
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Stats Service     │
                         └──────┬────────┬─────┘
                                │        │
                         Redis GET        │
                                │        │
                         ┌──────▼───┐     │
                         │  Redis   │     │
                         │  24h TTL │     │
                         └──────┬───┘     │
                                │         │
                           HIT ─┘         │ MISS
                             │            ▼
                             │    ┌─────────────────┐
                             │    │ GitHub REST API │
                             │    └────────┬────────┘
                             │             │
                             │      repositories
                             │             │
                             │      pagination
                             │             │
                             │      language calls
                             │             │
                             │      Semaphore(5)
                             │             │
                             │             ▼
                             │    ┌─────────────────┐
                             │    │ Aggregate +     │
                             │    │ percentages     │
                             │    └───────┬─────────┘
                             │            │
                             │       ┌────┴─────┐
                             │       ▼          ▼
                             │    Redis SET   MongoDB
                             │    + 24h TTL   history
                             │       │          │
                             └───────┬┴──────────┘
                                     ▼
                                  Response
```

## Resource lifecycle

Long-lived external clients are created once during FastAPI startup and
closed during application shutdown:

``` text
Application startup
        │
        ├── create HTTPX client
        ├── create Redis client
        └── create MongoDB client
                │
                ▼
             app.state
                │
                ▼
          request handling
                │
                ▼
Application shutdown
        │
        ├── close HTTPX
        ├── close Redis
        └── close MongoDB
```

This avoids creating a new HTTP client for every GitHub request and gives
external resources a clear lifecycle owner.

---

# 🧠 Cache-Aside and Cache Stampede

The current strategy is **cache-aside**: the application explicitly reads
from Redis, computes the value on a miss, and then populates Redis.

A cache stampede is not simply "many new users." It happens when many
requests miss the **same cache key** at approximately the same time:

``` text
50 requests
     │
     ▼
same Redis key
     │
     ▼
   MISS
     │
     ├──► GitHub
     ├──► GitHub
     ├──► GitHub
     ├──► ...
     └──► GitHub
```

This can duplicate expensive GitHub work and increase the chance of rate
limits or server overload.

A future solution could use a Redis lock/single-flight mechanism so only one
request refreshes a missing hot key while other requests wait for the result.

This is intentionally deferred until there is a demonstrated need.

---

# 🔐 Environment Variables

Create a local `.env` file containing your secrets:

``` text
MONGO_URL="mongodb+srv://<user>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority"
GITHUB_TOKEN="your_github_token_here"
```

**Never commit `.env` to GitHub.**

Add:

``` text
.env
```

to `.gitignore`.

------------------------------------------------------------------------

# 🚀 Deployment (Render)

### 1️⃣ Push the project to GitHub

### 2️⃣ Create a Render Web Service

Connect the GitHub repository to Render.

### 3️⃣ Configure the build command

``` bash
pip install -r requirements.txt
```

### 4️⃣ Configure the start command

``` bash
uvicorn app.main:app --host=0.0.0.0 --port=$PORT
```

### 5️⃣ Configure environment variables

``` text
MONGO_URL=your_mongodb_connection_string
GITHUB_TOKEN=your_github_token
PYTHON_VERSION=3.11
```

### 6️⃣ Deploy

Render starts the FastAPI application and exposes the API publicly.

------------------------------------------------------------------------

# 📝 To-Do / Future Improvements

-   [ ] Make HTTP timeout configuration explicit
-   [ ] Add automated tests with pytest + pytest-asyncio + respx
-   [ ] Add rate limiting per IP
-   [ ] Improve GitHub API error handling
-   [ ] Improve cache stampede/concurrent-cache handling
-   [ ] Add frontend dashboard
-   [ ] Add export to CSV / JSON
-   [ ] Add charts and historical trends
-   [x] Add Redis for distributed caching
-   [ ] Add authentication if the project becomes a public SaaS
-   [ ] Improve SVG card design and customization

------------------------------------------------------------------------

# 🧪 Testing Roadmap

The next major credibility milestone is automated testing.

Planned stack:

- **pytest**
- **pytest-asyncio**
- **respx** for mocking HTTPX/GitHub calls

Priority coverage:

``` text
┌──────────────────────────────────────────┐
│              Test Coverage               │
├──────────────────────────────────────────┤
│ Pagination termination                   │
│ Bounded concurrency                      │
│ Partial repository failure               │
│ GitHub rate-limit detection              │
│ SVG/XML escaping                         │
│ Redis cache hit                          │
│ Redis cache miss + population            │
└──────────────────────────────────────────┘
```

GitHub requests should be mocked in tests so the test suite does not depend
on GitHub availability or consume real API rate limits.

---

# 🔁 CI Roadmap

After the local test suite is established, GitHub Actions will run on pull
requests:

``` text
Pull Request
     │
     ▼
GitHub Actions
     │
     ├──► Lint
     │
     ├──► Type-check
     │
     └──► Pytest
              │
          ┌───┴───┐
          ▼       ▼
         PASS    FAIL
```

The goal is to prevent regressions from being merged when formatting,
typing, or behavior checks fail.

---

# 🐳 Docker Roadmap

The planned local development environment will use Docker Compose:

``` text
              docker compose up
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
     ┌────────┐  ┌─────────┐  ┌─────────┐
     │ FastAPI│  │ MongoDB │  │  Redis  │
     │  app   │  │         │  │         │
     └────────┘  └─────────┘  └─────────┘
          │           ▲           ▲
          └───────────┴───────────┘
```

The objective is a reproducible one-command local environment containing
the application and its local infrastructure dependencies.

---

# 🎯 Engineering Concepts Demonstrated

This project is intentionally being developed around practical backend
concepts:

-   REST API design
-   FastAPI routing
-   Pydantic validation and response models
-   Async/await
-   Python coroutines
-   `asyncio.gather`
-   Bounded concurrency with semaphores
-   Async HTTP clients
-   HTTP connection pooling
-   HTTP error handling
-   MongoDB persistence
-   Cache-aside style caching
-   Historical data storage
-   XML/SVG output generation
-   Context-aware output escaping
-   Environment-based configuration
-   Cloud deployment
-   Git-based incremental refactoring
