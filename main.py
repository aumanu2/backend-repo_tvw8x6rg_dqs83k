import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from database import db, create_document, get_documents
from schemas import User, BlogPost, ContactMessage

app = FastAPI(title="SaaS Starter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "SaaS API running"}

# --- Auth (simple email link demo placeholders; storing users) ---
class RegisterPayload(BaseModel):
    name: str
    email: EmailStr
    password: str

@app.post("/api/auth/register")
def register_user(payload: RegisterPayload):
    # very basic: store hashed password string placeholder (no real hashing here)
    # In production use passlib/bcrypt. Keeping dependencies minimal per template.
    existing = get_documents("user", {"email": payload.email.lower()}, limit=1)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(name=payload.name, email=payload.email.lower(), password_hash=f"sha256:{payload.password}")
    user_id = create_document("user", user)
    return {"id": user_id, "name": user.name, "email": user.email}

class LoginPayload(BaseModel):
    email: EmailStr
    password: str

@app.post("/api/auth/login")
def login_user(payload: LoginPayload):
    user_docs = get_documents("user", {"email": payload.email.lower()}, limit=1)
    if not user_docs:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = user_docs[0]
    if user.get("password_hash") != f"sha256:{payload.password}":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # return a fake token for demo purposes
    return {"token": "demo-token", "user": {"name": user.get("name"), "email": user.get("email")}}

# --- Pricing (static) ---
@app.get("/api/pricing")
def get_pricing():
    return {
        "currency": "USD",
        "plans": [
            {"name": "Starter", "price": 0, "period": "mo", "features": ["Up to 3 projects", "Community support", "Basic analytics"]},
            {"name": "Pro", "price": 19, "period": "mo", "features": ["Unlimited projects", "Priority support", "Advanced analytics"]},
            {"name": "Business", "price": 49, "period": "mo", "features": ["Team workspaces", "SSO (SAML)", "Custom reports"]}
        ]
    }

# --- Blog ---
@app.get("/api/blog", response_model=List[dict])
def list_posts():
    posts = get_documents("blogpost", {"status": "published"})
    # map to light-weight
    mapped = []
    for p in posts:
        mapped.append({
            "id": str(p.get("_id")),
            "title": p.get("title"),
            "slug": p.get("slug"),
            "excerpt": p.get("excerpt"),
            "author_name": p.get("author_name"),
            "cover_image": p.get("cover_image"),
            "tags": p.get("tags", []),
            "published_at": p.get("published_at")
        })
    return mapped

class BlogCreatePayload(BaseModel):
    title: str
    content: str
    author_name: str
    tags: Optional[List[str]] = None

@app.post("/api/blog")
def create_post(payload: BlogCreatePayload):
    slug = payload.title.lower().strip().replace(" ", "-")
    post = BlogPost(
        title=payload.title,
        slug=slug,
        excerpt=(payload.content[:140] + "...") if len(payload.content) > 140 else payload.content,
        content=payload.content,
        author_name=payload.author_name,
        tags=payload.tags or [],
        status="published",
        published_at=datetime.utcnow()
    )
    post_id = create_document("blogpost", post)
    return {"id": post_id, "slug": slug}

# --- Contact ---
class ContactPayload(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    message: str

@app.post("/api/contact")
def submit_contact(payload: ContactPayload):
    entry = ContactMessage(name=payload.name, email=payload.email, company=payload.company, message=payload.message)
    contact_id = create_document("contactmessage", entry)
    return {"id": contact_id, "status": "received"}

# --- Health/test ---
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
