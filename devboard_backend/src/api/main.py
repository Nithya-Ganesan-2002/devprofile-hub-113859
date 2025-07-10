from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import (
    auth_router, profile_router, project_router, tag_router, like_router, public_router
)

app = FastAPI(
    title="DevBoard API",
    description="API backend for DevBoard: User/project showcase, profiles, tags, likes, public API.",
    version="0.1.0",
    openapi_tags=[
        {"name": "Auth", "description": "User registration and login"},
        {"name": "Profile", "description": "Profile creation and editing"},
        {"name": "Project", "description": "Project upload, browsing"},
        {"name": "Tags", "description": "Project tags, tag cloud"},
        {"name": "Likes", "description": "Like/unlike projects"},
        {"name": "Public", "description": "Public profile/project APIs"},
    ],
)

# Allow any origin in dev (set restrictive CORS in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"], summary="Health Check", description="Base endpoint: confirms the API is live.")
def health_check():
    """Health check endpoint for the API."""
    return {"message": "Healthy"}

# Register all feature routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(project_router)
app.include_router(tag_router)
app.include_router(like_router)
app.include_router(public_router)
