# Secure Coding Patterns for SaaS Applications

Reference guide of secure coding patterns for common SaaS operations. Each entry shows the insecure approach, the secure approach, and the rationale.

---

## 1. Password Handling

### Storage
```python
# NEVER store passwords as plaintext or with fast hashes (MD5, SHA-1, SHA-256)
# ALWAYS use adaptive hashing: bcrypt, argon2, or scrypt

import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds is the 2024 recommended minimum
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
```

### Validation
```python
def validate_password_strength(password: str) -> list[str]:
    errors = []
    if len(password) < 12:
        errors.append("Password must be at least 12 characters")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain an uppercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain a number")
    # Prefer length over complexity rules — NIST SP 800-63B guidelines
    return errors
```

---

## 2. Token Generation

```python
import secrets

# Secure random token for password reset, email confirmation, API keys
def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)

# For numeric codes (e.g., 2FA)
def generate_otp(digits: int = 6) -> str:
    return str(secrets.randbelow(10 ** digits)).zfill(digits)

# NEVER use:
# random.random(), random.randint(), str(uuid.uuid4()) for security tokens
# time.time() or user.id-based tokens
```

---

## 3. JWT Handling

```python
import jwt
from datetime import datetime, timedelta

# Token creation
def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=15),  # short-lived
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# Token verification — always specify algorithm
def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"],  # NEVER omit this — prevents "alg: none" attack
            options={"require": ["exp", "sub", "type"]}  # require critical claims
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")
```

---

## 4. Input Validation

```python
from pydantic import BaseModel, EmailStr, constr, validator
import re

class UserCreateRequest(BaseModel):
    email: EmailStr                              # validates email format
    password: constr(min_length=12, max_length=128)
    name: constr(min_length=1, max_length=100, strip_whitespace=True)
    role: str

    @validator("role")
    def validate_role(cls, v):
        allowed = {"user", "editor"}             # NEVER trust client-supplied role
        if v not in allowed:
            raise ValueError(f"role must be one of: {allowed}")
        return v

    @validator("name")
    def validate_name_content(cls, v):
        if re.search(r"[<>\"'&]", v):            # prevent basic HTML injection
            raise ValueError("Name contains invalid characters")
        return v
```

---

## 5. SQL Injection Prevention

```python
# ALWAYS use parameterized queries

# SQLAlchemy ORM — safe by default
users = session.query(User).filter(User.email == email).all()

# SQLAlchemy Core with text() — use bindparams
from sqlalchemy import text
result = session.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email}
)

# Raw psycopg2 — use %s placeholders
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# NEVER do:
query = f"SELECT * FROM users WHERE email = '{email}'"  # SQL injection!
query = "SELECT * FROM users WHERE email = '" + email + "'"  # SQL injection!
```

---

## 6. Authorization Middleware

```python
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if not token:
            raise AuthError("Authentication required", 401)
        payload = verify_token(token)
        request.current_user_id = int(payload["sub"])
        return f(*args, **kwargs)
    return decorated

def require_resource_ownership(resource_model, id_param="id"):
    """Verify the current user owns the requested resource."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            resource_id = kwargs.get(id_param)
            resource = resource_model.query.get_or_404(resource_id)
            if resource.user_id != request.current_user_id:
                raise AuthError("Access denied", 403)
            request.resource = resource
            return f(*args, **kwargs)
        return decorated
    return decorator

# Usage
@app.get("/orders/<id>")
@require_auth
@require_resource_ownership(Order)
def get_order(id: int):
    return request.resource.to_dict()
```

---

## 7. Rate Limiting

```python
from functools import wraps
import time

# Simple in-memory rate limiter (use Redis in production for distributed systems)
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._store = {}  # key -> [(timestamp, ...)]

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        requests = self._store.get(key, [])
        requests = [t for t in requests if t > window_start]
        if len(requests) >= self.max_requests:
            return False
        requests.append(now)
        self._store[key] = requests
        return True

login_limiter = RateLimiter(max_requests=5, window_seconds=300)  # 5 attempts per 5 min

@app.post("/login")
def login():
    ip = request.remote_addr
    if not login_limiter.is_allowed(ip):
        return {"error": "Too many login attempts. Try again later."}, 429
    # ... proceed with authentication
```

---

## 8. Secrets Management

```python
import os
from typing import Optional

class Config:
    """Load and validate required secrets from environment."""

    def __init__(self):
        self.secret_key = self._require("SECRET_KEY")
        self.database_url = self._require("DATABASE_URL")
        self.stripe_secret = self._require("STRIPE_SECRET_KEY")
        self.smtp_password = self._require("SMTP_PASSWORD")
        # Optional with defaults
        self.debug = os.environ.get("DEBUG", "false").lower() == "true"

    def _require(self, name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise EnvironmentError(
                f"Required environment variable {name!r} is not set. "
                f"See .env.example for required variables."
            )
        return value

config = Config()  # fail fast at startup if secrets are missing
```

---

## 9. Secure HTTP Headers

```python
# Apply security headers to all responses

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'nonce-{nonce}'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.example.com"
    ),
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()"
}

@app.after_request
def apply_security_headers(response):
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response
```

---

## 10. File Upload Security

```python
import magic  # python-magic for true MIME detection
import os

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

def validate_upload(file) -> None:
    # 1. Check file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE_BYTES:
        raise ValidationError("File too large")

    # 2. Check actual MIME type (not just extension or Content-Type header)
    header_bytes = file.read(2048)
    file.seek(0)
    mime = magic.from_buffer(header_bytes, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise ValidationError(f"File type not allowed: {mime}")

    # 3. Sanitize filename — never use user-supplied filename directly
    # Generate a UUID-based filename instead
    ext = {"image/jpeg": ".jpg", "image/png": ".png", ...}.get(mime, "")
    return f"{uuid.uuid4()}{ext}"
```

---

## 11. Sensitive Data Filtering in Logs

```python
import re
import structlog

SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "api_key", "credit_card"}
SENSITIVE_PATTERN = re.compile(
    r"\b(password|token|secret|api_key|card_number)\s*[=:]\s*\S+",
    re.IGNORECASE
)

def sanitize_log_data(data: dict) -> dict:
    """Remove sensitive values from log context."""
    result = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = sanitize_log_data(value)
        else:
            result[key] = value
    return result

logger = structlog.get_logger().bind(
    service="api",
    environment=os.environ.get("ENV", "development")
)

# Log authentication events
def log_auth_event(event: str, user_id: int, ip: str, success: bool):
    logger.info(
        event,
        user_id=user_id,
        ip=ip,
        success=success
        # Never log: password, token, session_id
    )
```

---

## 12. SSRF Prevention

```python
import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"https"}
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "metadata.google.internal"}
BLOCKED_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),       # Private
    ipaddress.ip_network("172.16.0.0/12"),     # Private
    ipaddress.ip_network("192.168.0.0/16"),    # Private
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local (AWS metadata)
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
]

def validate_external_url(url: str) -> str:
    """Validate that a URL is safe to fetch from server-side."""
    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValidationError("Only HTTPS URLs are allowed")

    hostname = parsed.hostname
    if not hostname:
        raise ValidationError("Invalid URL")

    if hostname.lower() in BLOCKED_HOSTS:
        raise ValidationError("URL not allowed")

    try:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
        for network in BLOCKED_IP_RANGES:
            if ip in network:
                raise ValidationError("URL resolves to a private/internal address")
    except socket.gaierror:
        raise ValidationError("Could not resolve hostname")

    return url
```
