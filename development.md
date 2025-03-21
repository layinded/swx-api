# Development Guide

This document outlines how to set up and contribute to the SwX API project during development.

## 🧱 Prerequisites

- Python 3.10+
- `uv` or `pip` + `virtualenv`
- Docker & Docker Compose
- PostgreSQL

## 📁 Setup

```bash
cp .env.example .env
uv venv
uv pip install -r requirements.txt
```

### 📂 Create Alembic Migrations

```bash
swx db revision -m "your migration message"
swx db migrate
```

### 🔁 Run Locally

```bash
uvicorn swx_api.main:app --reload
```

### 🔍 Lint / Format / Type Check

```bash
swx format      # Run ruff formatter & pre-commit
swx lint        # Run ruff, mypy, pre-commit checks
```

## 🧪 Testing

```bash
pytest
```

## 📜 CLI Commands

```bash
swx --help
swx db migrate
swx make:resource blog
swx tinker
```

## 🔄 Hot Reloading

- Enabled in development using `--reload`
- All changes are automatically reflected without restarting the app
