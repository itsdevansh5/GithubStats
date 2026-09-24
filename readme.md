# GitHub Language Stats API

### FastAPI + Redis + MongoDB Atlas + GitHub API

A backend API that analyzes GitHub repository language usage, computes language usage percentages, stores historical snapshots, caches recent results, and serves dynamically generated SVG statistics cards.

Built with FastAPI, Redis, MongoDB Atlas, GitHub API, async `httpx`, Docker, and GitHub Actions.

## Overview

This project is designed as a practical backend engineering project with emphasis on API design, asynchronous programming, bounded concurrency, caching, database usage, resource lifecycle management, testing, Docker, and CI.

### Features

- Fetches repositories belonging to a GitHub user
- Handles GitHub `Link`-header pagination
- Skips forked and archived repositories
- Fetches repository language statistics concurrently
- Uses `asyncio.Semaphore` to bound concurrent GitHub requests
- Aggregates language byte counts across repositories
- Computes language usage percentages
- Caches the latest computed result in Redis for 24 hours
- Stores historical snapshots in MongoDB
- Validates GitHub usernames at the API boundary
- Generates dynamic SVG GitHub language-statistics cards
- Escapes dynamic values before inserting them into SVG/XML
- Uses Pydantic models and Pydantic Settings
- Uses long-lived HTTPX, Redis, and MongoDB clients managed by FastAPI lifespan
- Handles timeouts, GitHub rate limits, transient 5xx failures, and invalid responses
- Uses bounded retries with exponential backoff for transient GitHub server errors
- Includes automated tests with pytest, pytest-asyncio, and respx
- Builds as a Docker image
- Runs automated CI through GitHub Actions
- Deployed on Render

---

## Architecture Snapshot

```text
                         Client
                           |
                           v
                    +-------------+
                    |   FastAPI   |
                    |    Routes   |
                    +------+------+
                           |
                    Pydantic validation
                           |
                           v
                    +-------------+
                    | Stats       |
                    | Service     |
                    +------+------+ 
                           |
                +----------+----------+
                |                     |
                v                     v
          Redis cache            GitHub API
            24h TTL                  |
                |             +-------+-------+
                |             |               |
                |        pagination     language calls
                |                             |
                |                         Semaphore(5)
                |                             |
                |                             v
                |                       Aggregation
                |                             |
                |              +--------------+--------------+
                |              |                             |
                |              v                             v
                |         Redis SET                     MongoDB
                |          + TTL                        history
                |              |                             |
                +--------------+-----------------------------+
                               |
                               v
                           Response

SVG endpoint
    |
    +--> SVG generator
           |
           +--> XML-escape dynamic values
```

### Resource lifecycle

FastAPI lifespan owns the long-lived external clients:

```text
Application startup
        |
        +-- create HTTPX client
        +-- create Redis client
        +-- create MongoDB client
        |
        v
     app.state
        |
        v
  request handling
        |
        v
Application shutdown
        |
        +-- close HTTPX
        +-- close Redis
        +-- close MongoDB
```

This avoids creating a new HTTP client for every GitHub request and gives external resources a clear lifecycle owner.

### Configuration flow

```text
.env / OS environment
          |
          v
   Pydantic Settings
          |
          v
       Settings
```

Secrets are supplied through the environment and are not baked into the Docker image.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Backend Framework | FastAPI |
| HTTP Client | httpx (async) |
| Database | MongoDB Atlas |
| Database Driver | Motor |
| Cache | Redis Cloud / redis-py (async) |
| Validation / Models | Pydantic |
| Configuration | Pydantic Settings |
| Concurrency | asyncio + Semaphore + gather |
| Output | SVG |
| Testing | pytest + pytest-asyncio + respx |
| Containerization | Docker |
| CI | GitHub Actions |
| Deployment | Render |

---

## Project Structure

```text
GithubStats/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── exceptions.py
│   ├── github_api.py
│   ├── github_service.py
│   ├── models.py
│   ├── redis_caching.py
│   ├── stats_service.py
│   └── svg_generator.py
│
├── tests/
│   ├── test_business_rules.py
│   ├── test_github_api.py
│   ├── test_redis.py
│   ├── test_routing.py
│   └── test_svg_and_xml_escape.py
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .dockerignore
├── .gitignore
├── Dockerfile
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

# Live Demo

### Base URL

https://githubstats-gqcp.onrender.com/

### Swagger / OpenAPI

https://githubstats-gqcp.onrender.com/docs

### Embed the SVG card

```html
<img src="https://githubstats-gqcp.onrender.com/card/stats/YOUR_GITHUB_USERNAME" />
```

Example:

```html
<img src="https://githubstats-gqcp.onrender.com/card/stats/itsdevansh5" />
```

---

# API Documentation

## `GET /`

Health/status endpoint.

Example response:

```json
{
  "message": "GitHub Stats API Running"
}
```

---

## `GET /stats/{username}`

Fetches the latest GitHub language statistics.

Example:

```text
/stats/itsdevansh5
```

### Request flow

```text
GET /stats/{username}
        |
        v
   Redis GET
        |
   +----+----+
   |         |
  HIT       MISS
   |         |
   v         v
Return    GitHub API
cached        |
result        v
          Fetch repos
              |
              v
        Follow pagination
              |
              v
       Filter repositories
       (forked / archived)
              |
              v
       Fetch languages
       concurrently
              |
              v
       Aggregate bytes
              |
              v
       Calculate percentages
              |
        +-----+------+
        |            |
        v            v
      Redis       MongoDB
       cache       history
        |            |
        +-----+------+
              |
              v
           Response
```

### Example response

```json
{
  "username": "itsdevansh5",
  "cached": false,
  "language_aggregate": {
    "Python": 63697231,
    "C++": 224954,
    "HTML": 246905
  },
  "percentages": {
    "Python": 93.13,
    "C++": 0.33,
    "HTML": 0.36
  },
  "total_repos": 10,
  "fetched_at": "2026-09-24T12:34:11+00:00",
  "total_bytes": 64329090
}
```

When Redis contains a valid cached result:

```json
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

---

## `GET /history/{username}`

Returns historical language-statistics snapshots stored in MongoDB.

Example:

```text
/history/itsdevansh5
```

The history endpoint sorts snapshots by `fetched_at`.

Example:

```json
{
  "username": "itsdevansh5",
  "history": [
    {
      "fetched_at": "2026-08-10T12:34:11+00:00",
      "percentages": {
        "Python": 93.13,
        "C++": 0.33,
        "HTML": 0.36
      }
    },
    {
      "fetched_at": "2026-08-11T12:34:11+00:00",
      "percentages": {
        "Python": 92.80,
        "C++": 0.50,
        "HTML": 0.40
      }
    }
  ]
}
```

---

## `GET /card/stats/{username}`

Generates a dynamic SVG GitHub language-statistics card.

Example:

```text
/card/stats/itsdevansh5
```

Embed it in a GitHub README:

```html
<img src="https://githubstats-gqcp.onrender.com/card/stats/itsdevansh5" />
```

The endpoint returns:

```text
Content-Type: image/svg+xml
```

so browsers and GitHub-compatible clients can render the response as an SVG image.

---

# Asynchronous GitHub Fetching

Repository language data is fetched using a shared `httpx.AsyncClient`.

Sequential fetching would look conceptually like:

```text
Repo 1 -> wait -> Repo 2 -> wait -> Repo 3 -> wait
```

Instead, repository language requests are coordinated using:

```python
asyncio.gather(...)
```

A semaphore limits how many GitHub requests can be active simultaneously.

Current limit:

```python
MAX_CONCURRENT_GITHUB_REQUESTS = 5
```

Conceptually:

```text
Many repository tasks
        |
        v
  asyncio.gather()
        |
        v
   Semaphore(5)
        |
        v
Maximum 5 active GitHub requests
        |
        v
As one finishes, another can enter
```

This provides concurrency without creating an uncontrolled burst of requests.

Expected repository-level HTTP and validation failures can be isolated so that one problematic repository does not necessarily fail the entire aggregation.

---

# GitHub Pagination

GitHub repository responses can span multiple pages.

The service follows GitHub's `Link` response header and continues fetching pages until there is no `rel="next"` URL.

Conceptually:

```text
GET page 1
   |
   +--> Link: next
            |
            v
        GET page 2
            |
            +--> Link: next
                     |
                     v
                 GET page 3
                     |
                     v
                  complete
```

This avoids assuming that a single API response contains every repository.

---

# Retry and Error Handling

The GitHub integration distinguishes between different failure categories, including:

- request timeouts
- invalid external responses
- GitHub rate limiting
- transient GitHub server errors

Transient 5xx failures use bounded retries with exponential backoff rather than retrying indefinitely.

Low-level GitHub/application exceptions are separated from FastAPI's HTTP responses. The route layer converts relevant application failures into appropriate HTTP responses.

---

# Username Validation

GitHub usernames are validated at the API boundary before GitHub is contacted.

The validation checks that the supplied username follows the expected GitHub username format.

Validation and resource existence are treated separately:

```text
Invalid username format
        |
        v
Validation error

Valid format
        |
        v
GitHub API request
        |
        v
User exists / does not exist
```

The same validation model is reused across:

```text
/stats/{username}
/history/{username}
/card/stats/{username}
```

---

# SVG Output Safety

The SVG card contains dynamic values such as:

- GitHub username
- GitHub language names
- calculated percentages

Dynamic values are XML-escaped before being inserted into the SVG/XML markup.

For example:

```text
&
```

becomes:

```text
&amp;
```

and:

```text
<
```

becomes:

```text
&lt;
```

This ensures dynamic data is interpreted as text/data rather than SVG/XML markup.

The static SVG markup itself is not escaped; only dynamic values inserted into that markup are escaped.

---

# Percentage Calculation

GitHub returns language byte counts.

For example:

```text
Python -> 63697231
C++    -> 224954
HTML   -> 246905
```

The service aggregates byte counts across all valid repositories.

The percentage formula is:

```text
percentage = (language_bytes / total_language_bytes) * 100
```

The resulting percentages are rounded to two decimal places.

Raw byte counts are retained in the computed data for aggregation and metadata, while percentages provide the main language-distribution view.

---

# Caching and Historical Data

Redis and MongoDB deliberately have different responsibilities.

## Redis: latest computed result

Redis is the disposable cache for the latest statistics.

Cache key convention:

```text
gh:langpct:<username>
```

Example:

```text
gh:langpct:itsdevansh5
```

The colon-separated naming convention is only for organization; Redis does not assign special meaning to those parts.

The cache uses a 24-hour TTL.

### Cache-aside flow

```text
Request
   |
   v
Redis GET
   |
   v
Cached result?
 +-----+-----+
 |           |
YES          NO
 |           |
 v           v
Return     GitHub API
cached        |
result        v
          Calculate
              |
              v
        Redis SET + TTL
              |
              v
        MongoDB history
```

## MongoDB: historical snapshots

MongoDB stores durable historical results so previous calculations are retained rather than overwritten.

The separation is:

```text
Redis
  |
  +-- latest / temporary
          |
          +-- 24h TTL
          +-- expires

MongoDB
  |
  +-- historical snapshots
          |
          +-- retained
```

MongoDB therefore acts as the durable history store rather than the current cache.

---

# Redis Serialization

Redis values are serialized as JSON.

```text
Python dict
    |
    | json.dumps()
    v
JSON string
    |
    v
Redis
```

On retrieval:

```text
Redis
  |
  v
JSON string
  |
  | json.loads()
  v
Python dict
```

Datetime values are converted to ISO 8601 strings before JSON serialization.

---

# Cache Stampede

The current strategy is cache-aside.

A cache stampede can occur when many requests miss the same cache key at approximately the same time:

```text
50 requests
     |
     v
same Redis key
     |
     v
   MISS
     |
     +--> GitHub
     +--> GitHub
     +--> GitHub
     +--> ...
     +--> GitHub
```

This can duplicate expensive GitHub work and increase the chance of rate limiting.

A Redis lock or single-flight mechanism could be introduced later so that only one request refreshes a missing hot key while other requests wait.

This is intentionally deferred until there is a demonstrated need.

---

# Environment Variables

Create a local `.env` file containing your secrets.

Example:

```env
MONGO_URL=mongodb+srv://<user>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
REDIS_URL=redis://<user>:<password>@<host>:<port>
GITHUB_TOKEN=your_github_token_here
```

Do not commit `.env` to GitHub.

The repository's `.gitignore` and `.dockerignore` exclude local environment files.

For Docker, environment variables are injected at runtime:

```bash
docker run --env-file .env -p 8000:8000 githubstats
```

Secrets are therefore not baked into the Docker image.

---

# Docker

The project includes a Dockerfile for reproducible application packaging.

## Build

```bash
docker build -t githubstats .
```

## Run

```bash
docker run --env-file .env   -p 8000:8000   --name githubstats-container   githubstats
```

Then open:

```text
http://localhost:8000/docs
```

### Container architecture

```text
Host / VM
    |
    v
Docker Engine
    |
    v
GithubStats container
    |
    +-- Python 3.12
    +-- FastAPI
    +-- Uvicorn
    +-- application dependencies
    |
    +-------> Redis Cloud
    |
    +-------> MongoDB Atlas
    |
    +-------> GitHub API
```

MongoDB Atlas and Redis Cloud remain external managed services; they are not packaged inside the application container.

The `Dockerfile` is committed to the repository because it is part of the application's reproducible build instructions.

---

# Testing

The project uses:

- `pytest`
- `pytest-asyncio`
- `respx`

The tests cover application behavior including:

- GitHub API interaction
- pagination
- retry behavior
- GitHub rate-limit handling
- persistent GitHub server failures
- Redis cache hits
- Redis cache misses and population
- routing
- history retrieval
- SVG generation
- XML escaping
- business rules

GitHub HTTP requests are mocked in tests so the suite does not depend on GitHub availability or consume real API rate limits.

Run the complete test suite:

```bash
pytest -v
```

Run with coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

---

# Continuous Integration

GitHub Actions is used for CI.

The workflow runs on pushes to the main branch and on pull requests.

The CI pipeline:

```text
Push / Pull Request
        |
        v
GitHub Actions
        |
        v
Ubuntu runner
        |
        +--> Checkout repository
        |
        +--> Set up Python
        |
        +--> Install dependencies
        |
        +--> Run pytest
        |
        +--> Build Docker image
```

The Docker build is performed after the test job succeeds.

CI therefore verifies both:

1. The application behavior passes the automated test suite.
2. The project can still be packaged into a Docker image.

The CI workflow is stored at:

```text
.github/workflows/ci.yml
```

---

# Deployment

The application is deployed on Render.

Production API:

https://githubstats-gqcp.onrender.com/

Swagger documentation:

https://githubstats-gqcp.onrender.com/docs

Production secrets are configured through the deployment platform rather than committed to the repository.

---

# Engineering Concepts Demonstrated

This project demonstrates practical backend engineering concepts:

- REST API design
- FastAPI routing
- Pydantic validation
- Pydantic Settings
- OpenAPI / Swagger
- async/await
- Python coroutines
- `asyncio.gather`
- bounded concurrency
- semaphores
- async HTTP clients
- HTTP connection pooling
- API pagination
- retries
- exponential backoff
- rate-limit handling
- external API integration
- Redis caching
- cache-aside architecture
- TTL
- MongoDB persistence
- historical data storage
- application lifecycle management
- resource cleanup
- environment-based configuration
- Docker
- GitHub Actions CI
- automated testing
- SVG generation
- XML escaping
- separation of concerns
- service-layer architecture

---

# Project Status

**Complete**

Current project milestones:

- FastAPI backend
- GitHub API integration
- Link-header pagination
- bounded asynchronous concurrency
- retry and error handling
- Redis cache-aside with 24-hour TTL
- MongoDB historical snapshots
- SVG statistics card
- XML escaping
- automated tests
- Docker containerization
- GitHub Actions CI
- Render deployment
