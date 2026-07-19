# Full .env.example Output Format

Load this when generating or syncing `.env.example` (Phase 4) and you want the complete
section-header/comment style, not just the shape.

```bash
# =============================================================================
# Database
# =============================================================================
DATABASE_URL=postgresql://user:password@localhost:5432/app_development
DB_HOST=localhost
DB_PORT=5432

# =============================================================================
# Authentication
# =============================================================================
# Generate with: openssl rand -hex 32
JWT_SECRET=your_jwt_secret_here
NEXTAUTH_SECRET=your_nextauth_secret_here

# =============================================================================
# Stripe (https://dashboard.stripe.com/apikeys)
# =============================================================================
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# =============================================================================
# App Config
# =============================================================================
NODE_ENV=development
PORT=3000
BASE_URL=http://localhost:3000
```

Rules:
- Never include real values from `.env` — only placeholders.
- Preserve existing comments and groupings in `.env.example` when updating.
- When updating, only add missing variables; do not reorder existing ones.
- Add a source-URL comment above keys tied to a third-party dashboard (e.g. Stripe, SendGrid)
  when the source is obvious from the variable name.
