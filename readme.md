
# 📊 GitHub Language Stats API  
### 🚀 FastAPI + MongoDB Atlas + GitHub API

A production-ready backend API that analyzes GitHub repository languages, computes total usage, stores historical snapshots, and serves publicly accessible endpoints. Built with FastAPI, MongoDB Atlas, and deployed on Render.

---

## 🌟 Overview

This backend project:

- Fetches all repositories of a GitHub user  
- Aggregates language usage across all repos  
- Computes bytes + percentage usage  
- Caches results for 24 hours using MongoDB  
- Stores full historical snapshots over time  
- Exposes clean API endpoints with Pydantic models  
- Runs asynchronously using FastAPI + httpx  
- Fully deployed online and globally accessible  

Perfect for:

- Developer dashboards  
- Portfolio projects  
- GitHub analytics tools  
- Resume enhancement  
- Learning full backend engineering  

---

## 🧠 Tech Stack

| Layer | Technology |
|------|------------|
| Backend Framework | **FastAPI** |
| HTTP Client | **httpx (async)** |
| Database | **MongoDB Atlas** |
| Driver | **Motor (async)** |
| Deployment | **Render** |
| Config | **python-dotenv** |
| Data Models | **Pydantic** |

---

## 🗂 Project Structure

```
github-stats/
│── app/
│   ├── main.py
│   ├── github_api.py
│   ├── stats_service.py
│   ├── database.py
│   ├── models.py
│── requirements.txt
│── .env
│── .gitignore
│── README.md
```

---

# 🌐 Live Demo

> Frontend Coming Soon .....

### 🚀 **Base URL**
```
https://githubstats-gqcp.onrender.com/
```

### 📘 **Swagger Docs**
```
https://githubstats-gqcp.onrender.com/docs
```
### Embed in Your README

```html
<img src="https://githubstats-gqcp.onrender.com/card/stats?username=YOUR_GITHUB_USERNAME" />
```

Example:
```html
<img src="https://githubstats-gqcp.onrender.com/card/stats?username=itsdevansh5" />
```

---

# 📡 API Documentation

## 1️⃣ `GET /`
### Health check route  
Returns API status.

**Example:**
```json
{"message": "GitHub Stats API is running!"}
```

---

## 2️⃣ `GET /stats/{username}`
Fetches latest GitHub language statistics.

### ✨ Features:
- Fetches repositories  
- Aggregates all language data  
- Computes percentages  
- Saves snapshot  
- Uses 24-hour caching  

### Example:
```
/stats/itsdevansh5
```

**Response:**
```json
{
  "username": "itsdevansh5",
  "cached": false,
  "total_bytes": {
    "Python": 63697231,
    "C++": 224954,
    "HTML": 246905
  },
  "percentages": {
    "Python": 93.13,
    "C++": 0.33,
    "HTML": 0.36
  }
}
```

If cached:
```json
{
  "cached": true,
  ...
}
```

---

## 3️⃣ `GET /history/{username}`
Returns all historical snapshots of the user.

**Example:**
```json
{
  "username": "itsdevansh5",
  "history": [
    {
      "fetched_at": "2025-12-10T12:34:11",
      "total_bytes": { ... },
      "percentages": { ... }
    },
    {
      "fetched_at": "2025-12-11T12:34:11",
      "total_bytes": { ... },
      "percentages": { ... }
    }
  ]
}
```

## 3️⃣ `GET /card`

Generates a dynamic **SVG GitHub stats card** for a user.

**Query Params:**
- `username` — GitHub username (required)

**Example:**
```html
<img src="https://githubstats-gqcp.onrender.com/card?username=itsdevansh5" />
```
<img width="1920" height="1080" alt="Screenshot (23)" src="https://github.com/user-attachments/assets/980db523-2754-4d15-9b39-745a81bb337c" />

---


# 🧮 How Percentages Are Calculated

GitHub returns byte counts:

```
Python → 63697231
C++    → 224954
HTML   → 246905
```

Percentage formula:

```
percent = (bytes_of_lang / sum(all_bytes)) × 100
```

Rounded to 2 decimals.

---

# 🔐 Environment Variables

Your `.env` should contain:

```
MONGO_URL="mongodb+srv://<user>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority"
GITHUB_TOKEN="ghp_your_github_token_here"
```

⚠️ **Never commit `.env` to GitHub.**  
Add this to `.gitignore`:

```
.env
```

---

# 🚀 Deployment (Render)

### 1️⃣ Push code to GitHub  
### 2️⃣ Go to Render → New Web Service  
### 3️⃣ Choose your repo  
### 4️⃣ Set settings:

**Build Command**
```
pip install -r requirements.txt
```

**Start Command**
```
uvicorn app.main:app --host=0.0.0.0 --port=$PORT
```

### 5️⃣ Add Environment Variables:
```
MONGO_URL=your_url_here
GITHUB_TOKEN=your_token_here
PYTHON_VERSION=3.11
```

### 6️⃣ Deploy 🎉

---

# 📝 To-Do / Future Improvements

- Add user authentication  
- Add rate-limiting per IP  
- Add frontend dashboard  
- Add export to CSV / JSON  
- Add charts (Pie, Bar, Trends)  
- Add caching with Redis  
- Make it a full SaaS product  

---

# 🎉 Author

Made with ❤️ by Devansh  
A backend + cloud enthusiast building real-world projects.

---

# ⭐ Enjoy using the GitHub Stats API!
