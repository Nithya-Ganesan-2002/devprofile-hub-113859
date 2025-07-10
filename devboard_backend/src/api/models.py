"""Data models and Pydantic schemas for DevBoard backend (users, profiles, projects, tags, likes)."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

# ---------------------------
# User & Profile Schemas
# ---------------------------

# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """Schema for registering a new user."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password")

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, description="User's password")

# PUBLIC_INTERFACE
class UserOut(BaseModel):
    """Public info for a user."""
    id: int
    email: EmailStr

# PUBLIC_INTERFACE
class ProfileBase(BaseModel):
    """Base details for a profile."""
    display_name: str = Field(..., max_length=50, description="Display name")
    bio: Optional[str] = Field(None, max_length=300, description="User bio/about")
    avatar_url: Optional[str] = Field(None, description="Link to avatar/profile picture")

# PUBLIC_INTERFACE
class ProfileCreate(ProfileBase):
    """Profile creation schema."""
    pass

# PUBLIC_INTERFACE
class ProfileUpdate(BaseModel):
    """Editable fields for profile update (partial)."""
    display_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]

# PUBLIC_INTERFACE
class ProfileOut(ProfileBase):
    """Profile as returned to client."""
    user_id: int
    projects: Optional[List[int]] = []  # Will list project IDs

# ---------------------------
# Project & Tag Schemas
# ---------------------------

# PUBLIC_INTERFACE
class TagSchema(BaseModel):
    """Schema for a project tag."""
    id: int
    name: str

# PUBLIC_INTERFACE
class TagCreate(BaseModel):
    """Schema to create a new tag."""
    name: str = Field(..., max_length=30, description="Tag name")

# PUBLIC_INTERFACE
class ProjectBase(BaseModel):
    """Shared fields for a project."""
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=1000)
    repo_url: Optional[str] = Field(None, description="URL to code repository (e.g., GitHub)")
    preview_img_url: Optional[str] = Field(None, description="Preview image URL")

# PUBLIC_INTERFACE
class ProjectCreate(ProjectBase):
    """Schema when uploading a new project."""
    tags: Optional[List[str]] = Field(default_factory=list, description="List of tag names (to create/link)")

# PUBLIC_INTERFACE
class ProjectUpdate(BaseModel):
    """Editable fields for project update."""
    title: Optional[str]
    description: Optional[str]
    repo_url: Optional[str]
    preview_img_url: Optional[str]
    tags: Optional[List[str]]

# PUBLIC_INTERFACE
class ProjectOut(ProjectBase):
    """Project as returned to frontend."""
    id: int
    user_id: int
    tags: List[TagSchema]
    created_at: datetime
    like_count: int

# ---------------------------
# Like System
# ---------------------------

# PUBLIC_INTERFACE
class LikeOut(BaseModel):
    """Like data for a project."""
    project_id: int
    user_id: int

# ---------------------------
# Auth Token
# ---------------------------

# PUBLIC_INTERFACE
class Token(BaseModel):
    """Auth response token."""
    access_token: str
    token_type: str = "bearer"

# PUBLIC_INTERFACE
class TokenData(BaseModel):
    """Token data for internal use."""
    user_id: Optional[int] = None
