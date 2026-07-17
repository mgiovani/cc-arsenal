# Detection Patterns

Codebase detection commands for each diagram type.

## ORM Detection (ER Diagrams)

### Python ORMs

```bash
# SQLAlchemy
find . -name "*models.py" -exec grep -l "Base\|Column\|relationship" {} \; | head -10

# Django
find . -name "models.py" -exec grep -l "models.Model" {} \; | head -10

# Tortoise ORM
find . -name "*.py" -exec grep -l "tortoise.models" {} \; | head -10
```

### JavaScript/TypeScript ORMs

```bash
# Prisma
find . -name "schema.prisma"

# TypeORM
find . -name "*.entity.ts" -o -name "*entity.js" | head -10

# Sequelize
find . -name "*.model.js" -o -name "*.model.ts" | head -10
```

## Architecture Detection

```bash
# Find services
find . -name "*service*.ts" -o -name "*service*.py" -o -name "*service*.js" | head -15

# Find API routes
find . -name "*router*.ts" -o -name "*routes*.py" -o -name "*controller*.js" | head -15

# Find configs
find . -name "*.config.js" -o -name "*.config.ts" -o -name "config.py" | head -10
```

## Deployment Detection

```bash
# Docker
find . -name "Dockerfile" -o -name "docker-compose.yml" -o -name "docker-compose.yaml"

# Kubernetes
find . -name "*.k8s.yaml" -o -name "*.k8s.yml" -o -name "*deployment.yaml"

# CI/CD
find . -name ".github/workflows/*.yml" -o -name ".gitlab-ci.yml" -o -name "Jenkinsfile"
```

## Security Detection

```bash
# Authentication patterns
grep -r "authenticate\|authorization\|jwt\|oauth" --include="*.py" --include="*.ts" . | head -15

# Security middleware
grep -r "middleware\|cors\|csrf\|helmet" --include="*.py" --include="*.ts" --include="*.js" . | head -15

# Encryption
grep -r "encrypt\|decrypt\|hash\|bcrypt\|argon" --include="*.py" --include="*.ts" . | head -10
```
