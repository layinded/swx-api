# 🚀 SwX-API

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-🚀-brightgreen)
![License](https://img.shields.io/github/license/layinded/swx-api)
![Docker Ready](https://img.shields.io/badge/Docker-Ready-blue)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-success)
![Made with ❤️](https://img.shields.io/badge/Made_with-%E2%9D%A4-red)

**SwX-API** is a Laravel-style, API-first **FastAPI** framework designed for speed, scalability, and maintainability. With a modular architecture, robust authentication (OAuth2, JWT, and social login), and production-grade tooling, it offers everything you need to kickstart your backend project.

> Built with ❤️ for developers who value flexibility and structure.

---

## ✨ Features

- ⚡ **FastAPI** backend with modular folder structure (`core/`, `app/`)
- 🗃️ **SQLModel** ORM with **PostgreSQL** support
- 🔄 **Alembic** migrations with auto-generation
- 🔐 **OAuth2 + JWT** authentication with refresh tokens
- 👥 **Social login** support (Google, Facebook)
- 🛡️ **Role-Based Access Control (RBAC)** & superuser support
- 🌍 **i18n** with language preference detection
- 🧠 **Dynamic model loading** & multilingual data seeding
- 🛠️ **CLI Tool**: `swx` for scaffolding and automation  
  _(e.g., `swx make:resource`, `swx migrate`)_
- 📚 **MkDocs** auto-generated API docs from Python docstrings
- 🧪 Pre-configured **logging**, **linting**, **formatting**, and **testing**
- 🐳 **Docker-ready** with `docker-compose.yml`
- ⚙️ Optional integration with **Traefik**, **Sentry**, and **GitHub Actions**
- 🚀 **CI/CD**-friendly with production-grade deployment tools

---

## 📁 Project Structure

```bash
swx_api/
├── app/                # User-defined application logic (routes, services)
├── core/               # Core framework logic (auth, db, utils, etc.)
├── docs/               # MkDocs documentation
├── alembic/            # Alembic migrations
├── scripts/            # CLI scripts
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Base Compose config
└── ...

```
### 🛠️ Installation

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional)
- PostgreSQL

### 📦 Clone the Repository

```bash
git clone https://github.com/yourusername/swx-api.git
cd swx-api
```

### 🐍 Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 📥 Install Dependencies

```bash
pip install -r requirements.txt
```

### ⚙️ Configure Environment Variables

Create a `.env` file in the project root with the following content:

```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/swx_db
JWT_SECRET_KEY=your_jwt_secret
```

> Replace `user`, `password`, and `swx_db` with your actual PostgreSQL credentials and database name.

### 🔄 Run Database Migrations

```bash
swx migrate
```

### 🚀 Start the Development Server

```bash
uvicorn main:app --reload
```

---

### 🐳 Run with Docker (Optional)

If you prefer using Docker:

```bash
docker-compose up --build
```

> This will spin up the app along with PostgreSQL using the provided `docker-compose.yml`.

---

## Deployment

Deployment docs: [deployment.md](./deployment.md).

## Development

General development docs: [development.md](./development.md).

This includes using Docker Compose, custom local domains, `.env` configurations, etc.

