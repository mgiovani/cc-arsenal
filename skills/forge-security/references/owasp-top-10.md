# OWASP Top 10 2021 — Detailed Reference

Detailed reference for the OWASP Top 10 2021 categories, with specific patterns to look for during a security audit, code examples of vulnerabilities, and recommended fixes. Use this alongside the forge-security SKILL.md.

---

## A01: Broken Access Control

**Risk**: Ranked #1 because 94% of applications tested had some form of broken access control.

### What it means
Users can act outside their intended permissions: access other users' data, modify other users' accounts, access admin functions, or access data without authentication.

### Vulnerable patterns to look for

**IDOR (Insecure Direct Object Reference)**:
```python
# VULNERABLE: uses user-supplied ID without ownership check
@app.get("/orders/{order_id}")
def get_order(order_id: int, current_user: User = Depends(auth)):
    return db.query(Order).filter(Order.id == order_id).first()

# SECURE: verify ownership
@app.get("/orders/{order_id}")
def get_order(order_id: int, current_user: User = Depends(auth)):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id  # ownership check
    ).first()
    if not order:
        raise HTTPException(status_code=404)
    return order
```

**Missing auth on sensitive endpoints**:
- Admin routes without role guards
- API endpoints that check auth on GET but not POST/PUT/DELETE
- Routes added without copying the auth middleware

**Mass assignment**:
```javascript
// VULNERABLE: accepts all fields including is_admin
const user = await User.update(req.params.id, req.body);

// SECURE: whitelist allowed fields
const { name, email } = req.body;
const user = await User.update(req.params.id, { name, email });
```

---

## A02: Cryptographic Failures

**Risk**: Data exposed at rest or in transit due to weak or missing encryption.

### Vulnerable patterns to look for

**Weak password hashing**:
```python
# VULNERABLE
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()
password_hash = hashlib.sha256(password.encode()).hexdigest()  # still weak for passwords

# SECURE
import bcrypt
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
```

**Hardcoded secrets**:
```python
# VULNERABLE
SECRET_KEY = "my-super-secret-key-12345"
API_KEY = "sk-prod-abc123def456"

# SECURE
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set")
```

**Sensitive data in URLs or logs**:
```python
# VULNERABLE — tokens appear in server logs
redirect_url = f"/reset?token={reset_token}"
logger.info(f"User {user.email} logged in with password {password}")

# SECURE
redirect_url = f"/reset"  # token in POST body or httpOnly cookie
logger.info("User logged in", user_id=user.id)
```

---

## A03: Injection

**Risk**: Attacker injects malicious commands that are executed by the interpreter.

### SQL Injection

```python
# VULNERABLE
query = f"SELECT * FROM users WHERE email = '{email}'"
db.execute(query)

# SECURE — parameterized query
query = "SELECT * FROM users WHERE email = %s"
db.execute(query, (email,))

# SECURE — ORM
User.query.filter_by(email=email).first()
```

### Command Injection

```python
# VULNERABLE
import subprocess
filename = request.form.get("filename")
subprocess.run(f"convert {filename} output.png", shell=True)

# SECURE
subprocess.run(["convert", filename, "output.png"])  # no shell=True, no interpolation
```

### NoSQL Injection (MongoDB)

```javascript
// VULNERABLE — user can pass {"$gt": ""} to bypass
const user = await User.findOne({ email: req.body.email });

// SECURE — validate type and sanitize
const email = String(req.body.email);
if (!isValidEmail(email)) throw new Error("Invalid email");
const user = await User.findOne({ email });
```

### Template Injection

```python
# VULNERABLE — user controls template content
from jinja2 import Template
template = Template(user_input)  # allows {{ config }} or {{ ''.__class__.__mro__[1]... }}

# SECURE — render user data into a fixed template
template = Template("Hello, {{ name }}!")
template.render(name=user_input)
```

---

## A04: Insecure Design

**Risk**: Design flaws that cannot be fixed by correct implementation alone.

### Patterns to look for

**No rate limiting on authentication**:
- Login endpoint allows unlimited attempts
- Password reset allows generating unlimited tokens
- Registration allows creating accounts from the same IP without throttling

**Insecure password reset**:
```python
# VULNERABLE — predictable token
token = str(user.id) + str(int(time.time()))

# VULNERABLE — token never expires
user.reset_token = generate_token()
user.save()  # no expiry set

# SECURE
token = secrets.token_urlsafe(32)
expiry = datetime.utcnow() + timedelta(hours=1)
user.reset_token = hash_token(token)  # store hashed
user.reset_token_expiry = expiry
user.save()
```

**Missing business logic validation**:
```python
# VULNERABLE — negative quantity possible
order.quantity = request.data["quantity"]  # could be -1

# SECURE
quantity = int(request.data["quantity"])
if quantity < 1 or quantity > MAX_ORDER_QUANTITY:
    raise ValidationError("Invalid quantity")
```

---

## A05: Security Misconfiguration

**Risk**: Insecure default configurations, incomplete setups, or open cloud storage.

### Patterns to look for

**Debug mode in production**:
```python
# VULNERABLE
app = Flask(__name__, debug=True)

# SECURE
debug = os.environ.get("DEBUG", "false").lower() == "true"
app = Flask(__name__, debug=debug)
```

**Missing security headers**:
```python
# SECURE — add these headers to all responses
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["Content-Security-Policy"] = "default-src 'self'"
response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
```

**Overly permissive CORS**:
```javascript
// VULNERABLE
app.use(cors({ origin: "*" }));

// SECURE
const allowedOrigins = process.env.ALLOWED_ORIGINS.split(",");
app.use(cors({ origin: allowedOrigins, credentials: true }));
```

**Verbose error messages**:
```python
# VULNERABLE — exposes internal details
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

# SECURE
@app.errorhandler(Exception)
def handle_error(e):
    logger.exception("Unhandled error")
    return jsonify({"error": "Internal server error"}), 500
```

---

## A06: Vulnerable & Outdated Components

**Risk**: Using components with known vulnerabilities.

### What to check

- Dependency files: `package.json`, `requirements.txt`, `Gemfile`, `go.mod`
- Lock files for exact versions used
- Whether critical packages (auth libraries, crypto, serialization) are recent
- Presence of packages with known CVE history in those versions

### Common high-risk packages to verify
- Authentication libraries (passport, PyJWT, devise)
- Serialization libraries (pickle, yaml.load, xmltodict)
- HTTP client libraries (requests, axios, node-fetch)
- Template engines

---

## A07: Identification & Authentication Failures

**Risk**: Weak authentication allows account takeover.

### Patterns to look for

**JWT without algorithm verification**:
```python
# VULNERABLE — "none" algorithm accepted
decoded = jwt.decode(token, options={"verify_signature": False})

# VULNERABLE — algorithm not specified
decoded = jwt.decode(token, SECRET_KEY)

# SECURE
decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

**No session invalidation on logout**:
```python
# VULNERABLE — only clears client-side cookie
@app.post("/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"status": "logged out"}

# SECURE — also invalidate server-side
@app.post("/logout")
def logout(response: Response, session_id: str = Cookie()):
    session_store.delete(session_id)  # server-side invalidation
    response.delete_cookie("session")
    return {"status": "logged out"}
```

---

## A08: Software & Data Integrity Failures

**Risk**: Unverified updates, insecure deserialization, or supply chain attacks.

### Patterns to look for

**Unsafe deserialization**:
```python
# VULNERABLE — pickle executes arbitrary code
import pickle
data = pickle.loads(request.body)

# VULNERABLE — yaml.load executes Python
import yaml
data = yaml.load(request.body)  # use yaml.safe_load

# SECURE
import yaml
data = yaml.safe_load(request.body)
```

**Webhooks without signature verification**:
```python
# VULNERABLE — accepts any POST to webhook endpoint
@app.post("/webhooks/payment")
def payment_webhook(data: dict):
    process_payment_event(data)

# SECURE — verify webhook signature
@app.post("/webhooks/payment")
def payment_webhook(request: Request, data: dict):
    signature = request.headers.get("X-Signature")
    expected = hmac.new(WEBHOOK_SECRET, request.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401)
    process_payment_event(data)
```

---

## A09: Security Logging & Monitoring Failures

**Risk**: Attacks go undetected due to insufficient logging.

### What should be logged

**Authentication events** (with timestamp, IP, user ID):
- Successful login
- Failed login (and after N failures, potential lockout)
- Logout
- Password change / reset
- MFA challenge result

**Authorization events**:
- Access denied (403)
- Attempt to access another user's resource

**High-value transactions**:
- Subscription changes
- Payment events
- Data export / bulk operations
- Admin actions

### What must NOT be logged
- Passwords (even hashed)
- Full credit card numbers
- Full tokens (log last 4 chars max)
- Full PII beyond what is necessary

---

## A10: Server-Side Request Forgery (SSRF)

**Risk**: Attacker causes server to make requests to unintended locations.

### Patterns to look for

**User-controlled URLs in server-side requests**:
```python
# VULNERABLE
@app.post("/fetch-url")
def fetch_url(url: str):
    response = requests.get(url)  # could be http://169.254.169.254/ (AWS metadata)
    return response.text

# SECURE — strict allowlist
ALLOWED_HOSTS = {"api.example.com", "cdn.example.com"}

@app.post("/fetch-url")
def fetch_url(url: str):
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_HOSTS:
        raise ValidationError("URL not allowed")
    if parsed.scheme not in ("https",):
        raise ValidationError("Only HTTPS allowed")
    response = requests.get(url, timeout=5)
    return response.text
```

**Webhook URL registration**:
```python
# VULNERABLE — user can register internal URLs as webhooks
webhook.url = request.data["url"]

# SECURE — validate webhook URLs against an allowlist or block internal ranges
def validate_webhook_url(url: str) -> bool:
    parsed = urlparse(url)
    ip = socket.gethostbyname(parsed.hostname)
    # Block private IP ranges
    addr = ipaddress.ip_address(ip)
    return not (addr.is_private or addr.is_loopback or addr.is_reserved)
```
