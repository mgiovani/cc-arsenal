---
name: db-migrate
description: Creates, checks the status of, and validates database migrations by auto-detecting the project's migration framework (Alembic, Prisma, Knex, Django, Rails/ActiveRecord, Flyway, Atlas, TypeORM, Sequelize, SQLx, golang-migrate, Liquibase) from marker files, then driving that framework's own CLI. Use when the user wants to create a new migration, check pending vs. applied migration status, or validate a migration for a missing rollback script, a missing foreign-key index, or a destructive operation like DROP TABLE / TRUNCATE / DELETE FROM. Trigger phrases include "create a migration", "check migration status", "any pending migrations", "validate this migration", "does this migration have a rollback". Not for designing the schema change itself or writing ORM model code (use implement-feature), this skill only manages migration files and framework tooling once the schema change is already decided.
metadata:
  author: mgiovani
  version: 2.0.0
argument-hint: '[create|status|validate] [--name migration_name] [--dry-run]'
allowed-tools:
- Bash
- Read
- Write
- Edit
- Grep
- Glob
- AskUserQuestion
---

# DB Migrate

Create, check the status of, and validate database migrations across any framework. Auto-detects the migration tool from project marker files and drives its native CLI: this skill never invents a migration command.

## Ground rules

- **Detect before acting.** Scan for marker files (Phase 1) before running anything.
- **Never invent commands.** Only run commands from the detection table in [references/framework-commands.md](references/framework-commands.md) or found in the project's own docs/scripts.
- **Flag destructive operations and never auto-fix them.** `DROP TABLE`, `DROP COLUMN`, `TRUNCATE`, `DELETE FROM` get a warning and require the user's explicit go-ahead: this skill reports, it does not silently rewrite or apply a migration containing one.
- **Report only what a command actually produced.** File paths, migration names, and status output in the final summary must come from `ls`/`cat`/the framework CLI's own output, never guessed or reconstructed from memory.

## Workflow

### Phase 1: Detect framework

```bash
ls alembic.ini prisma/schema.prisma knexfile.* flyway.conf flyway.toml \
   db/migrate/ manage.py atlas.hcl typeorm.config.* ormconfig.* \
   liquibase.properties 2>/dev/null
```

Also check `package.json` (`knex`, `db-migrate`, `sequelize`, `typeorm`), `pyproject.toml`/`requirements.txt` (`alembic`, `sqlalchemy`), and `Gemfile` (`activerecord`) for framework dependencies when no marker file is conclusive.

If multiple frameworks are detected (e.g. a monorepo with both a Python and a Node service), ask the user which one they mean. If none is detected, ask the user to name it: don't guess a command for a framework you can't confirm.

Full detection table and per-framework commands: [references/framework-commands.md](references/framework-commands.md), load it once the framework is identified, before running any create/status/rollback command.

### Phase 2: Parse the request

Determine the operation from `$ARGUMENTS` or the user's phrasing:

- `create` (default if unspecified): make a new migration file
- `status`: show pending vs. applied migrations
- `validate`: check rollback coverage, naming convention, index coverage, destructive ops

If `--name <name>` is given, use it. Otherwise ask for a short, descriptive name before creating the file: don't invent one.
`--dry-run` shows what would be created/run without executing it.

### Phase 3: Execute

#### create

1. Check naming conventions in existing migrations (`Glob migrations/`, `db/migrate/`) and match the project's pattern.
2. Run the framework-native create command from the reference table (use `--autogenerate` / schema-diff mode where the framework supports it, e.g. Alembic, Prisma).
3. Read the generated file back and show it to the user: don't just report that a command succeeded.
4. Remind the user to review the diff, add a rollback/down script if it wasn't auto-generated, and add indexes for any new foreign keys.

#### status

Run the framework's status command and show applied migrations (with timestamps), pending migrations, and the current schema version, copied from that command's real output.

#### validate

Check the target migration file(s) for:
1. **Rollback exists**: every `up`/forward change has a matching `down`/reverse (warn if missing).
2. **Naming convention**: matches the pattern already used in the migrations directory.
3. **Foreign-key indexes**: `grep -iE "REFERENCES|foreign_key|FK_"` and confirm a corresponding `CREATE INDEX` exists.
4. **Destructive operations**: `grep -iE "DROP TABLE|DROP COLUMN|TRUNCATE|DELETE FROM"`, flag every hit by line.
5. **Mixed data + schema changes**: warn if one file both alters structure and mutates rows; these usually deploy and roll back better as two files.

### Phase 4: Report

Summarize using only what Phases 1–3 actually produced:
- File path(s) touched
- Migration name and timestamp
- Warnings found (destructive ops with line numbers, missing rollback, missing index): omit the section entirely if there were none, don't write "no issues found" as a guess
- Next step commands (apply / rollback), taken verbatim from the detection table for the detected framework

## Notes

- Review auto-generated migrations before applying: autogenerate can include unintended changes (e.g. Alembic missing custom types).
- Prisma dev migrations use a shadow database: confirm `DATABASE_URL` isn't pointed at production before running `prisma migrate dev`.
- Prefer transactional DDL where the database supports it, for atomicity. MySQL auto-commits DDL: flag this to the user when detected instead of assuming a transaction wraps it.

## Worked examples

**1. Create, framework auto-detected (Alembic)**
```
$ ls alembic.ini → found
Framework: Alembic
$ alembic revision --autogenerate -m "add_users_email_index"
  Generating migrations/versions/a1b2c3_add_users_email_index.py ... done

Created: migrations/versions/a1b2c3_add_users_email_index.py
  upgrade(): op.create_index('ix_users_email', 'users', ['email'])
  downgrade(): op.drop_index('ix_users_email', table_name='users')

No warnings — rollback present, no destructive ops.
Next: `alembic upgrade head` to apply, `alembic downgrade -1` to roll back.
```

**2. Status check (Prisma)**
```
$ npx prisma migrate status
3 migrations found, 1 pending: 20260710120000_add_orders_table

Applied: 20260601090000_init, 20260615140000_add_users_table
Pending: 20260710120000_add_orders_table
Next: `npx prisma migrate deploy` to apply the pending migration.
```

**3. Validate, destructive op found (Knex)**
```
$ grep -iE "DROP TABLE|DROP COLUMN|TRUNCATE|DELETE FROM" migrations/20260716_cleanup.js
12: knex.schema.dropTable('legacy_sessions')

WARNING: destructive operation at line 12 (dropTable).
Rollback (down()) is present but only recreates an empty table — dropped data is not recoverable from this migration alone.
This needs your explicit confirmation before it's treated as ready to apply.
```

**4. No framework detected**
```
$ ls alembic.ini prisma/schema.prisma knexfile.* ... → none found
$ grep -l "knex\|sequelize\|typeorm" package.json → no match

I couldn't detect a migration framework from marker files or dependencies.
Which one are you using, or is this a brand-new project without one yet?
```

**5. Two frameworks detected in a monorepo**
```
$ ls alembic.ini → found (api/)
$ ls prisma/schema.prisma → found (web/)

Both api/alembic.ini (Alembic) and web/prisma/schema.prisma (Prisma) are present.
Which service's migration do you want — api (Alembic) or web (Prisma)?
```
