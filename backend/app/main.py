from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import products, customers, orders
from app.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (Alembic handles migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="IMS — Inventory & Order Management System",
    version="1.0.0",
    description="Production-ready REST API for managing products, customers, and orders.",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened per-environment via env var in prod
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(customers.router, prefix="/customers", tags=["Customers"])
app.include_router(orders.router, tags=["Orders"])


@app.get("/", tags=["System"])
async def root():
    from fastapi.responses import HTMLResponse
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>IMS API — Management Portal</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: #151b2c;
            --accent-color: #f59e0b;
            --accent-hover: #d97706;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border-color: #1e293b;
            --success-color: #10b981;
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            overflow-x: hidden;
        }
        .container {
            max-width: 650px;
            width: 100%;
            padding: 40px 20px;
            text-align: center;
        }
        .logo-container {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 72px;
            height: 72px;
            background: linear-gradient(135deg, var(--accent-color), #f97316);
            border-radius: 20px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(245, 158, 11, 0.3);
            font-size: 28px;
            font-weight: 800;
            color: #000;
        }
        h1 {
            font-size: 32px;
            font-weight: 700;
            margin: 0 0 12px 0;
            letter-spacing: -0.025em;
            background: linear-gradient(to right, #ffffff, #cbd5e1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        p.subtitle {
            font-size: 16px;
            color: var(--text-secondary);
            margin: 0 0 40px 0;
            line-height: 1.6;
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background-color: rgba(16, 185, 129, 0.1);
            color: var(--success-color);
            padding: 8px 16px;
            border-radius: 9999px;
            font-size: 14px;
            font-weight: 600;
            border: 1px solid rgba(16, 185, 129, 0.2);
            margin-bottom: 32px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            background-color: var(--success-color);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 40px;
        }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            text-align: left;
            transition: all 0.2s ease;
        }
        .card:hover {
            transform: translateY(-2px);
            border-color: #334155;
            box-shadow: 0 10px 20px -10px rgba(0, 0, 0, 0.5);
        }
        .card-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }
        .card-value {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
        }
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, var(--accent-color), #f97316);
            color: #0f172a;
            font-weight: 600;
            font-size: 15px;
            padding: 14px 28px;
            border-radius: 12px;
            text-decoration: none;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
        }
        .btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(245, 158, 11, 0.35);
        }
        footer {
            margin-top: 48px;
            font-size: 13px;
            color: #475569;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo-container">IMS</div>
        <h1>Inventory & Order Management Portal</h1>
        <p class="subtitle">Welcome to the core REST API backend for IMS. Access management services, monitor stock levels, and coordinate operations.</p>
        
        <div>
            <div class="status-badge">
                <span class="status-dot"></span>
                API System Operational
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <div class="card-title">Version</div>
                <div class="card-value">v1.0.0</div>
            </div>
            <div class="card">
                <div class="card-title">Environment</div>
                <div class="card-value">Production</div>
            </div>
        </div>
        
        <a href="/docs" class="btn">Explore API Documentation</a>
        
        <footer>
            &copy; 2026 IMS Warehouse Operations. All Rights Reserved.
        </footer>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@app.get("/health", tags=["System"])
async def health_check() -> dict:
    return {"status": "ok", "service": "ims-backend"}
