# DB Migrate: Framework Detection & Commands

This reference is loaded when `db-migrate` needs framework-specific commands.

## Detection Table

| Marker File | Framework | Create Command | Status Command | Apply Command |
|-------------|-----------|---------------|----------------|---------------|
| `alembic.ini` | Alembic (Python) | `alembic revision --autogenerate -m "<name>"` | `alembic current` | `alembic upgrade head` |
| `prisma/schema.prisma` | Prisma (Node.js) | `npx prisma migrate dev --name <name>` | `npx prisma migrate status` | `npx prisma migrate deploy` |
| `knexfile.*` | Knex (Node.js) | `npx knex migrate:make <name>` | `npx knex migrate:status` | `npx knex migrate:latest` |
| `flyway.conf` or `flyway.toml` | Flyway | Create `sql/V{timestamp}__<name>.sql` manually | `flyway info` | `flyway migrate` |
| `db/migrate/` (Ruby) | Rails/ActiveRecord | `rails generate migration <Name>` | `rails db:migrate:status` | `rails db:migrate` |
| `manage.py` + `*/migrations/` | Django | `python manage.py makemigrations [app]` | `python manage.py showmigrations` | `python manage.py migrate` |
| `atlas.hcl` | Atlas | `atlas migrate diff --env local` | `atlas migrate status` | `atlas migrate apply` |
| `typeorm.config.*` or `ormconfig.*` | TypeORM | `npx typeorm migration:generate -n <name>` | `npx typeorm migration:show` | `npx typeorm migration:run` |
| `sequelize-cli` in `package.json` | Sequelize | `npx sequelize-cli migration:generate --name <name>` | `npx sequelize-cli db:migrate:status` | `npx sequelize-cli db:migrate` |
| `Cargo.toml` + `sqlx` dep | SQLx (Rust) | `sqlx migrate add <name>` | `sqlx migrate info` | `sqlx migrate run` |
| `go.mod` + `migrate` dep | golang-migrate | `migrate create -ext sql -dir db/migrations <name>` | `migrate version` | `migrate up` |
| `liquibase.properties` | Liquibase | Create `changelog/<name>.xml` manually | `liquibase status` | `liquibase update` |

## Rollback Commands

| Framework | Rollback Command |
|-----------|-----------------|
| Alembic | `alembic downgrade -1` |
| Prisma | `npx prisma migrate reset` (full) or manual SQL |
| Knex | `npx knex migrate:rollback` |
| Flyway | `flyway undo` (Teams only) or manual SQL |
| Rails | `rails db:rollback` |
| Django | `python manage.py migrate <app> <migration_name>` |
| Atlas | `atlas migrate down` |
| TypeORM | `npx typeorm migration:revert` |
| Sequelize | `npx sequelize-cli db:migrate:undo` |
| SQLx | `sqlx migrate revert` |

## Per-Framework Best Practices

### Alembic (Python)
- Use `--autogenerate` to detect schema changes from SQLAlchemy models
- Always review auto-generated migrations: autogenerate may miss some changes (e.g., custom types)
- Use `alembic revision` (without autogenerate) for data migrations
- Keep `env.py` updated with all model imports for accurate autogenerate
- File naming: `<timestamp>_<slug>.py` (auto-generated)

### Prisma (Node.js)
- `prisma migrate dev` uses a shadow database to detect drift: never point to production
- `prisma migrate deploy` is for production (no shadow DB needed)
- Do not edit generated SQL files after running dev migration: use `prisma migrate resolve` instead
- For data migrations, use a separate migration with raw SQL via `$executeRaw`
- Reset caution: `prisma migrate reset` drops and re-creates the database

### Knex (Node.js)
- Always write both `up` and `down` functions in migration files
- Use `knex.schema.createTableIfNotExists` for idempotency
- File naming: `<timestamp>_<description>.js`
- Use `knex.raw()` for DDL not covered by the schema builder

### Flyway
- SQL file naming convention: `V{version}__{description}.sql` (double underscore)
- Use `R__` prefix for repeatable migrations (views, stored procedures)
- Commercial Flyway Teams required for undo migrations; open source is forward-only
- Use placeholders `${placeholder}` for environment-specific values

### Rails ActiveRecord
- Never edit existing migrations: create new ones to correct mistakes
- `db/schema.rb` is the source of truth; keep it committed
- Use `change` method when possible (Rails infers rollback); use `up`/`down` for complex migrations
- Data migrations should be separate from schema migrations; consider `data_migrate` gem

### Django
- Run `makemigrations` locally, commit migration files to version control
- Never delete migration files: use `squashmigrations` to consolidate if needed
- Use `RunPython` for data migrations with a `reverse_code` argument for rollback
- Use `--check` flag in CI: `python manage.py migrate --check` to verify no unapplied migrations

### Atlas
- Schema-as-code approach: define target schema in HCL, Atlas generates the migration
- `atlas migrate lint` catches migration issues before applying
- Supports versioned migrations and declarative migrations (pick one per project)
- Integrates with Terraform for infrastructure-as-code workflows

### TypeORM
- Use `synchronize: false` in production: never auto-sync schema
- Keep entity files and migrations in sync
- Use `MigrationInterface` with `up` and `down` methods
- `migration:generate` compares current entities to database, creates diff

### SQLx (Rust)
- Migration files are plain SQL with `-- +migrate Up` / `-- +migrate Down` markers
- Use `sqlx migrate run` in deployment, `sqlx migrate revert` for rollback
- Compile-time query checking requires `sqlx prepare` to generate query metadata

## Naming Conventions

| Style | Example | Used By |
|-------|---------|---------|
| Timestamp + description | `20240315120000_add_user_email.sql` | Flyway, golang-migrate, SQLx |
| Auto-incremented version | `0001_add_user_email.py` | Alembic (default), Django |
| CamelCase description | `AddUserEmail` | Rails, TypeORM |
| Timestamp + CamelCase | `1710504000000-AddUserEmail.ts` | TypeORM default |

## Common Pitfalls

1. **Missing DOWN migration**: Always write rollback scripts; production incidents require quick rollback
2. **Non-transactional DDL**: Some DB engines (MySQL) auto-commit DDL; wrap in explicit transactions where supported
3. **Large table migrations**: `ALTER TABLE` on large tables can lock; use `ADD COLUMN ... DEFAULT NULL` then backfill
4. **Index creation**: Use `CREATE INDEX CONCURRENTLY` (Postgres) to avoid table locks
5. **Enum types**: Adding enum values is forward-only in some DBs; plan carefully
6. **Running in CI without a DB**: Use Docker service containers or test databases in CI pipelines
