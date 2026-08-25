from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import health, transactions, workflows, metrics, audit_logs, customers, demo, razorpay

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Autonomous Revenue Recovery Agent Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(transactions.router, prefix=settings.API_V1_STR, tags=["Transactions"])
app.include_router(workflows.router, prefix=settings.API_V1_STR, tags=["Recovery Workflows"])
app.include_router(metrics.router, prefix=settings.API_V1_STR, tags=["Recovery Metrics"])
app.include_router(audit_logs.router, prefix=settings.API_V1_STR, tags=["Audit Logs"])
app.include_router(customers.router, prefix=settings.API_V1_STR, tags=["Customers"])
app.include_router(demo.router, prefix=settings.API_V1_STR, tags=["Interactive Demo Studio"])
app.include_router(razorpay.router, prefix=settings.API_V1_STR, tags=["Razorpay Integration"])

@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "Welcome to RecoverAI API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
