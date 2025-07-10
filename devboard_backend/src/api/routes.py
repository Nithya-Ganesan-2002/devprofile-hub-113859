"""All main routers/endpoints for user auth, profile, project, tags, likes, and public profile."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from .models import (
    UserCreate, UserLogin, UserOut,
    ProfileCreate, ProfileUpdate, ProfileOut,
    ProjectCreate, ProjectOut,
    TagSchema, Token
)
from .auth_utils import (
    register_user, authenticate_user,
    get_current_user, create_access_token
)

# Routers
auth_router = APIRouter(prefix="/auth", tags=["Auth"])
profile_router = APIRouter(prefix="/profile", tags=["Profile"])
project_router = APIRouter(prefix="/project", tags=["Project"])
tag_router = APIRouter(prefix="/tags", tags=["Tags"])
like_router = APIRouter(prefix="/like", tags=["Likes"])
public_router = APIRouter(prefix="/public", tags=["Public"])

# In-memory stores (replace with DB for prod)
profile_store = {}      # {user_id: {display_name, bio, avatar_url}}
project_store = {}      # {project_id: {...}}
tag_store = {}          # {tag: tag_id}
like_store = set()      # set of (user_id, project_id)
project_id_counter = 1
tag_id_counter = 1

# ---------- Auth Endpoints ----------

# PUBLIC_INTERFACE
@auth_router.post("/register", response_model=UserOut, summary="Register a new user")
def register(user: UserCreate):
    """Register user and return minimal user info."""
    user_dict = register_user(user.email, user.password)
    return UserOut(id=user_dict["id"], email=user_dict["email"])


# PUBLIC_INTERFACE
@auth_router.post("/login", response_model=Token, summary="Log in user and get JWT")
def login(user: UserLogin):
    """Authenticate and return JWT access token."""
    u = authenticate_user(user.email, user.password)
    if not u:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    token = create_access_token({"sub": u["email"], "user_id": u["id"]})
    return Token(access_token=token)


# ---------- Profile Endpoints ----------

# PUBLIC_INTERFACE
@profile_router.post("/", response_model=ProfileOut, summary="Create user profile")
def create_profile(profile: ProfileCreate, current_user: UserOut = Depends(get_current_user)):
    """Create profile for current user. One per-user."""
    if current_user.id in profile_store:
        raise HTTPException(status_code=400, detail="Profile already exists for user.")
    entry = {**profile.dict(), "user_id": current_user.id, "projects": []}
    profile_store[current_user.id] = entry
    return ProfileOut(**entry)


# PUBLIC_INTERFACE
@profile_router.get("/", response_model=ProfileOut, summary="Get current user's profile")
def get_my_profile(current_user: UserOut = Depends(get_current_user)):
    """Retrieve your own profile (must be logged in)."""
    entry = profile_store.get(current_user.id)
    if not entry:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return ProfileOut(**entry)


# PUBLIC_INTERFACE
@profile_router.put("/", response_model=ProfileOut, summary="Update current user's profile")
def update_my_profile(update: ProfileUpdate, current_user: UserOut = Depends(get_current_user)):
    """Edit profile. Fields not set are unchanged."""
    entry = profile_store.get(current_user.id)
    if not entry:
        raise HTTPException(status_code=404, detail="Profile not found.")
    entry.update({k: v for k, v in update.dict().items() if v is not None})
    profile_store[current_user.id] = entry
    return ProfileOut(**entry)


# ---------- Project Endpoints ----------

# PUBLIC_INTERFACE
@project_router.post("/", response_model=ProjectOut, summary="Upload/project add", tags=["Project"])
def upload_project(project: ProjectCreate, current_user: UserOut = Depends(get_current_user)):
    """Upload a new project for user, create tags if needed, link to profile."""
    global project_id_counter, tag_id_counter

    # Create tags
    project_tags = []
    for tag_name in (project.tags or []):
        tag_name = tag_name.lower().strip()
        if tag_name not in tag_store:
            tag_store[tag_name] = tag_id_counter
            project_tags.append({"id": tag_id_counter, "name": tag_name})
            tag_id_counter += 1
        else:
            project_tags.append({"id": tag_store[tag_name], "name": tag_name})

    project_id = project_id_counter
    now = datetime.utcnow()
    project_entry = {
        "id": project_id,
        "user_id": current_user.id,
        "title": project.title,
        "description": project.description,
        "repo_url": project.repo_url,
        "preview_img_url": project.preview_img_url,
        "tags": project_tags,
        "created_at": now,
        "like_count": 0,
    }
    project_store[project_id] = project_entry
    project_id_counter += 1

    # Link project to profile projects list
    if current_user.id in profile_store:
        profile_store[current_user.id]["projects"].append(project_id)

    return ProjectOut(**project_entry)


# PUBLIC_INTERFACE
@project_router.get("/", response_model=List[ProjectOut], summary="List all projects with optional tag filter")
def list_projects(tag: Optional[str] = Query(None), search: Optional[str] = Query(None)):
    """List all projects (optionally filter by tag or search string)."""
    results = list(project_store.values())
    if tag:
        tag_ = tag.lower().strip()
        results = [p for p in results if any(t["name"] == tag_ for t in p["tags"])]
    if search:
        s = search.lower()
        results = [p for p in results if s in p["title"].lower() or s in p["description"].lower()]
    return [ProjectOut(**p) for p in results]


# PUBLIC_INTERFACE
@project_router.get("/{project_id}", response_model=ProjectOut, summary="Get specific project")
def get_project(project_id: int):
    """Get project by project ID."""
    p = project_store.get(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")
    return ProjectOut(**p)


# ---------- Tag Endpoints ----------

# PUBLIC_INTERFACE
@tag_router.get("/", response_model=List[TagSchema], summary="List all tags")
def list_tags():
    """Return all tags (tag cloud, etc)."""
    return [TagSchema(id=tid, name=name) for name, tid in tag_store.items()]


# ---------- Like Endpoints ----------

# PUBLIC_INTERFACE
@like_router.post("/{project_id}", status_code=204, summary="Like a project")
def like_project(project_id: int, current_user: UserOut = Depends(get_current_user)):
    """Like a project if not already liked."""
    key = (current_user.id, project_id)
    if (project_id not in project_store or key in like_store):
        return
    like_store.add(key)
    project_store[project_id]["like_count"] += 1

# PUBLIC_INTERFACE
@like_router.delete("/{project_id}", status_code=204, summary="Unlike a project")
def unlike_project(project_id: int, current_user: UserOut = Depends(get_current_user)):
    """Remove like from project."""
    key = (current_user.id, project_id)
    if key in like_store:
        like_store.remove(key)
        if project_id in project_store and project_store[project_id]["like_count"] > 0:
            project_store[project_id]["like_count"] -= 1

# ---------- Public Profile Endpoints ----------

# PUBLIC_INTERFACE
@public_router.get("/profile/{user_id}", response_model=ProfileOut, summary="Get public profile data for user")
def get_public_profile(user_id: int):
    """Return public profile data for a user (including their projects)."""
    entry = profile_store.get(user_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return ProfileOut(**entry)


# PUBLIC_INTERFACE
@public_router.get("/profile/{user_id}/projects", response_model=List[ProjectOut], summary="Get all projects for a user's public profile")
def get_user_projects(user_id: int):
    """Return public projects for a profile/user."""
    entry = profile_store.get(user_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return [ProjectOut(**project_store[pid]) for pid in entry["projects"] if pid in project_store]
