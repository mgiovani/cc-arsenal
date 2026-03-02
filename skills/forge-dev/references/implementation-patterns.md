# Implementation Patterns

Common SaaS coding patterns for authentication, CRUD operations, payment integration, and more. These are reference patterns — always adapt to match your project's existing conventions.

## Authentication Patterns

### JWT Authentication (Node.js/TypeScript)

```typescript
// API route with auth guard — Next.js App Router
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const session = await getServerSession(authOptions);

  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Proceed with authenticated request
  const userId = session.user.id;
  // ...
}
```

```typescript
// Protected page component — Next.js Server Component
import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";

export default async function ProtectedPage() {
  const session = await getServerSession();

  if (!session) {
    redirect("/login");
  }

  return <div>Protected content for {session.user.email}</div>;
}
```

### JWT Authentication (Python/FastAPI)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(
    token: str = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# Usage in endpoint
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

## CRUD Patterns

### REST API Endpoint (Next.js/TypeScript with Prisma)

```typescript
// GET list with filtering and pagination
export async function GET(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get("page") ?? "1");
  const limit = parseInt(searchParams.get("limit") ?? "20");
  const skip = (page - 1) * limit;

  const [items, total] = await Promise.all([
    prisma.project.findMany({
      where: { userId: session.user.id },
      orderBy: { updatedAt: "desc" },
      skip,
      take: limit,
    }),
    prisma.project.count({ where: { userId: session.user.id } }),
  ]);

  return NextResponse.json({
    items,
    pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
  });
}

// POST create with validation
import { z } from "zod";

const createProjectSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
});

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await request.json();
  const result = createProjectSchema.safeParse(body);

  if (!result.success) {
    return NextResponse.json(
      { error: "Invalid input", details: result.error.flatten() },
      { status: 400 }
    );
  }

  const project = await prisma.project.create({
    data: { ...result.data, userId: session.user.id },
  });

  return NextResponse.json(project, { status: 201 });
}
```

### REST API Endpoint (Python/FastAPI with SQLAlchemy)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    name: str
    description: str | None = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skip = (page - 1) * limit
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Project.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return projects

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = Project(**project_data.model_dump(), user_id=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
```

### Form with Validation (React/TypeScript)

```typescript
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";

const schema = z.object({
  name: z.string().min(1, "Name is required").max(100, "Name too long"),
  description: z.string().max(500, "Description too long").optional(),
});

type FormData = z.infer<typeof schema>;

export function CreateProjectForm({ onSuccess }: { onSuccess: () => void }) {
  const [serverError, setServerError] = useState<string | null>(null);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setServerError(null);
    try {
      const response = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const error = await response.json();
        setServerError(error.error ?? "Something went wrong");
        return;
      }

      onSuccess();
    } catch {
      setServerError("Network error. Please try again.");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label htmlFor="name">Name</label>
        <input id="name" {...register("name")} />
        {errors.name && <p className="error">{errors.name.message}</p>}
      </div>

      {serverError && <p className="error">{serverError}</p>}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Creating..." : "Create Project"}
      </button>
    </form>
  );
}
```

## Database Patterns

### Prisma Schema Addition

```prisma
// Adding a new model
model Project {
  id          String   @id @default(cuid())
  name        String
  description String?
  userId      String
  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@index([userId])
}
```

### SQLAlchemy Model

```python
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="projects")
```

## Payment Integration Patterns (Stripe)

### Create Checkout Session

```typescript
// API route: POST /api/billing/checkout
import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { priceId } = await request.json();

  const checkoutSession = await stripe.checkout.sessions.create({
    mode: "subscription",
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${process.env.NEXT_PUBLIC_APP_URL}/billing/success`,
    cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/billing`,
    customer_email: session.user.email!,
    metadata: { userId: session.user.id },
  });

  return NextResponse.json({ url: checkoutSession.url });
}
```

### Webhook Handler

```typescript
// API route: POST /api/billing/webhook
import { headers } from "next/headers";

export async function POST(request: Request) {
  const body = await request.text();
  const signature = headers().get("stripe-signature")!;

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch {
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object as Stripe.CheckoutSession;
      const userId = session.metadata?.userId;
      if (userId) {
        await prisma.user.update({
          where: { id: userId },
          data: { subscriptionStatus: "active", stripeCustomerId: session.customer as string },
        });
      }
      break;
    }
    case "customer.subscription.deleted": {
      // Handle cancellation
      break;
    }
  }

  return NextResponse.json({ received: true });
}
```

## Error Handling Patterns

### Centralized Error Response (Next.js)

```typescript
// lib/api-response.ts
export function errorResponse(message: string, status: number, details?: unknown) {
  return NextResponse.json({ error: message, details }, { status });
}

export function successResponse(data: unknown, status = 200) {
  return NextResponse.json(data, { status });
}

// Usage in API route
try {
  const data = await someOperation();
  return successResponse(data);
} catch (error) {
  if (error instanceof PrismaClientKnownRequestError && error.code === "P2002") {
    return errorResponse("A record with this value already exists", 409);
  }
  console.error("Unexpected error:", error);
  return errorResponse("Internal server error", 500);
}
```

### FastAPI Error Handling

```python
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

@router.post("/")
async def create_item(data: ItemCreate, db: Session = Depends(get_db)):
    try:
        item = Item(**data.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Item already exists")
    except Exception as e:
        db.rollback()
        logger.error("Failed to create item", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Testing Patterns

### API Route Test (Vitest/TypeScript)

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GET, POST } from "@/app/api/projects/route";

// Mock auth
vi.mock("next-auth", () => ({
  getServerSession: vi.fn(),
}));

// Mock database
vi.mock("@/lib/prisma", () => ({
  prisma: {
    project: {
      findMany: vi.fn(),
      create: vi.fn(),
    },
  },
}));

describe("GET /api/projects", () => {
  beforeEach(() => {
    vi.mocked(getServerSession).mockResolvedValue({ user: { id: "user-1" } });
  });

  it("returns projects for authenticated user", async () => {
    const mockProjects = [{ id: "1", name: "Test Project" }];
    vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects);

    const request = new Request("http://localhost/api/projects");
    const response = await GET(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.items).toEqual(mockProjects);
  });

  it("returns 401 for unauthenticated request", async () => {
    vi.mocked(getServerSession).mockResolvedValue(null);

    const request = new Request("http://localhost/api/projects");
    const response = await GET(request);

    expect(response.status).toBe(401);
  });
});
```

### FastAPI Test (pytest)

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

@pytest.fixture
def authenticated_client(client: TestClient, test_user: User):
    # Override auth dependency
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield client
    app.dependency_overrides.clear()

def test_list_projects_authenticated(authenticated_client, db_session, test_user):
    # Create test data
    project = Project(name="Test Project", user_id=test_user.id)
    db_session.add(project)
    db_session.commit()

    response = authenticated_client.get("/projects/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Project"

def test_list_projects_unauthenticated(client: TestClient):
    response = client.get("/projects/")
    assert response.status_code == 401
```

## File Organization Patterns

### Next.js App Router Structure

```
src/
  app/
    (auth)/           # Route group — pages for logged-out users
      login/page.tsx
      register/page.tsx
    (dashboard)/      # Route group — pages for logged-in users
      dashboard/page.tsx
      projects/
        page.tsx      # List view
        [id]/page.tsx # Detail view
    api/
      projects/
        route.ts      # GET list, POST create
        [id]/
          route.ts    # GET one, PUT update, DELETE
  components/
    ui/               # Reusable base components (Button, Input, Card)
    projects/         # Feature-specific components
      ProjectCard.tsx
      CreateProjectForm.tsx
  lib/
    prisma.ts         # Prisma client singleton
    auth.ts           # NextAuth configuration
    utils.ts          # Shared utilities
```

### FastAPI Project Structure

```
src/
  api/
    v1/
      auth.py         # Auth endpoints
      projects.py     # Project endpoints
      users.py        # User endpoints
  models/
    project.py        # SQLAlchemy models
    user.py
  schemas/
    project.py        # Pydantic request/response schemas
    user.py
  services/
    email.py          # Email sending service
    storage.py        # File storage service
  core/
    config.py         # App configuration
    database.py       # Database session management
    security.py       # JWT utilities
  tests/
    test_projects.py
    test_auth.py
    conftest.py       # Shared fixtures
```
