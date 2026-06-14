# IMS — Inventory & Order Management System

A production-ready full-stack application for managing products, customers, and orders.

**Stack:** Python · FastAPI · PostgreSQL · React · Vite · Docker

---

## Quick Start (Docker Compose)

```bash
# 1. Clone and enter the project
git clone <your-repo-url> ims && cd ims

# 2. Create your .env file
cp .env.example .env
# Edit .env with a strong POSTGRES_PASSWORD

# 3. Build and start all services
docker compose up --build

# Services:
# Frontend  →  http://localhost:3000
# Backend   →  http://localhost:8000
# API Docs  →  http://localhost:8000/docs
```

---

## Local Development (without Docker)

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# Set environment variables
set DATABASE_URL=postgresql+asyncpg://ims_user:password@localhost:5432/ims_db

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

# For local dev (uses Vite proxy to localhost:8000)
npm run dev
# → http://localhost:3000
```

---

## Environment Variables

| Variable | Service | Description |
|---|---|---|
| `POSTGRES_DB` | Docker Compose | Database name |
| `POSTGRES_USER` | Docker Compose | DB username |
| `POSTGRES_PASSWORD` | Docker Compose | DB password |
| `DATABASE_URL` | Backend | Full asyncpg connection string |
| `VITE_API_BASE_URL` | Frontend build | Backend URL for production build |

---

## API Reference

### Products
| Method | Path | Description |
|---|---|---|
| `GET` | `/products` | List all products |
| `POST` | `/products` | Create product |
| `GET` | `/products/{id}` | Get by ID |
| `PUT` | `/products/{id}` | Update |
| `DELETE` | `/products/{id}` | Delete |

### Customers
| Method | Path | Description |
|---|---|---|
| `GET` | `/customers` | List all |
| `POST` | `/customers` | Create |
| `GET` | `/customers/{id}` | Get by ID |
| `DELETE` | `/customers/{id}` | Delete |

### Orders
| Method | Path | Description |
|---|---|---|
| `GET` | `/orders` | List all |
| `POST` | `/orders` | Create (deducts stock) |
| `GET` | `/orders/{id}` | Get with items |
| `DELETE` | `/orders/{id}` | Cancel (restores stock if pending) |

### Dashboard
| Method | Path | Description |
|---|---|---|
| `GET` | `/dashboard/summary` | Totals + low stock products |

Full interactive docs at `/docs` (Swagger UI).

---

## Business Rules

- **SKU must be unique** — `409 Conflict` if duplicate
- **Email must be unique** — `409 Conflict` if duplicate
- **Stock check before order** — `400 Bad Request` with clear message per out-of-stock product
- **Atomic order creation** — stock deducted in a single DB transaction
- **Unit price snapshot** — price at order time, not current price
- **Cancel pending order** — restores stock atomically
- **Low stock threshold** — products with `quantity < 10` (configurable in `backend/app/constants.py`)

---

## Deployment

### Backend → Render

1. Create a new **Web Service** on [Render](https://render.com)
2. Connect your GitHub repository
3. Set **Root Directory** to `backend`
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables:
   - `DATABASE_URL` → your Render PostgreSQL connection string

### Frontend → Vercel

1. Import repository on [Vercel](https://vercel.com)
2. Set **Root Directory** to `frontend`
3. Add environment variable:
   - `VITE_API_BASE_URL` → your live Render backend URL (e.g. `https://ims-api.onrender.com`)
4. Vercel auto-detects Vite — no extra config needed

Add `frontend/vercel.json` for SPA routing:
```json
{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
```

### Docker Hub (for submission)

```bash
docker build -t naushadia/ims-backend:latest ./backend
docker push naushadia/ims-backend:latest
```

---

## Project Structure

```
ims/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, CORS, routers
│   │   ├── database.py      # Async SQLAlchemy engine
│   │   ├── constants.py     # LOW_STOCK_THRESHOLD
│   │   ├── exceptions.py    # Global error handlers
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic v2 schemas
│   │   ├── services/        # All business logic
│   │   └── routers/         # Thin HTTP handlers
│   ├── alembic/             # DB migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # Axios helpers per entity
│   │   ├── components/      # Sidebar, Header, Drawer, StatusBadge
│   │   ├── hooks/           # useProducts, useCustomers, useOrders
│   │   └── pages/           # Dashboard, Products, Customers, Orders, OrderDetail
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── .env.example
```

---

## Design System

**Warm Utility** theme — IBM Plex Sans (UI), Fraunces (KPI numbers only), IBM Plex Mono (codes/IDs). Plain CSS custom properties, no Tailwind. Status as colored text only — no pill badges.
