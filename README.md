# Contacts API Project

**FastAPI-based REST API** for managing personal contacts with user authentication, role-based access, Redis caching, avatar upload via Cloudinary, and email-based password reset.

---

## Features

- User registration & JWT authentication
- Email verification
- Password reset via email
- Avatar upload to Cloudinary
- Role-based access (`user` / `admin`)
- Redis caching for performance
- Dockerized (PostgreSQL, Redis, Mailhog)
- Automatically generated docs with Sphinx
- 79%+ test coverage (pytest, pytest-cov)

---

## Tech Stack

- **FastAPI**
- **PostgreSQL**
- **Redis**
- **SQLAlchemy**
- **Pydantic**
- **Docker & Docker Compose**
- **Cloudinary**
- **Mailhog (email testing)**
- **pytest + pytest-cov**

---

## How to Run

### 1. Clone the repository

```bash
git clone https://github.com/jod563/goit-pythonweb-hw-12.git
cd goit-pythonweb-hw-12
```

### 2. Create `.env` from example

```bash
cp .env.example .env
```

Fill in your secrets in `.env`.

---

### 3. Build & Run via Docker Compose

```bash
docker-compose up --build
```

App will be available at `http://localhost:8000`

MailHog UI → `http://localhost:8025`

---

## Run Tests

```bash
docker-compose exec web pytest --cov=app --cov-report=term-missing
```

---

## API Docs

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---