from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from app.routers import auth, languages, documentation, linguistic, export
from app.database import init_neo4j, close_neo4j
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up Lexiconnect API...")
    init_neo4j()
    yield
    # Shutdown
    print("Shutting down Lexiconnect API...")
    close_neo4j()


app = FastAPI(
    title="Lexiconnect API",
    description="IGT-first, graph-native tool for endangered/minority language documentation and research",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(languages.router, prefix="/api/v1/languages", tags=["languages"])
app.include_router(documentation.router, prefix="/api/v1/docs", tags=["documentation"])
app.include_router(
    linguistic.router, prefix="/api/v1/linguistic", tags=["linguistic-data"]
)
app.include_router(export.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to Lexiconnect API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "lexiconnect-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
    )
