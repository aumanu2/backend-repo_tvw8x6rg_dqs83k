"""
Database Schemas for the SaaS demo

Each Pydantic model represents a MongoDB collection. Collection name is the
lowercase of the class name.

- User -> "user"
- BlogPost -> "blogpost"
- ContactMessage -> "contactmessage"
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    """Users collection schema"""
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="Hashed password")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    role: str = Field("user", description="user | admin")
    is_active: bool = Field(True, description="Whether user is active")

class BlogPost(BaseModel):
    """Blog posts collection schema"""
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    author_name: str
    cover_image: Optional[str] = None
    tags: List[str] = []
    status: str = Field("published", description="draft | published")
    published_at: Optional[datetime] = None

class ContactMessage(BaseModel):
    """Contact messages collection schema"""
    name: str
    email: EmailStr
    company: Optional[str] = None
    message: str
    status: str = Field("new", description="new | read | archived")
