# Config and secrets

## Contents

- [Settings object](#settings-object)
- [Secrets](#secrets)
- [Entry points and environments](#entry-points-and-environments)

## Settings object

Load all configuration through `pydantic-settings`, in one `Settings` class in `config.py`, which sits at the package root beside `cli.py`.

- Use nested settings classes for groups such as database, auth and observability, each with its own `env_prefix`.
- Type secrets as `SecretStr` or `Secret[...]`, so a repr or a log line prints a mask.
- Give the settings model `ConfigDict(frozen=True, extra='forbid')` where the project does. A typo in a variable name then fails at boot.
- Use `field_validator` and `SettingsConfigDict`. The v1 inner `Config` class is gone.
- Build the settings once, in the composition root, and pass them down. A module that calls `Settings()` at import time makes every test read the real environment.
- Resolve a value in a fixed order: environment variable, then config file, then built-in default. Both overrides are optional so a zero-config run works.
- A constant in code beats a setting nobody changes. Add a setting when someone needs to change it.
- Choose a model or provider through a setting, never a literal in the code. Swapping a model is then a configuration edit.
- Production fails at boot when a required value is missing. Never fall back to a localhost URL, a test key or a local key provider. A failed key-management call also stops the boot.
- The migration tool reads the database URL from this object too.

## Secrets

- Keep secrets out of source, image layers, build args, console responses, agent context, artifacts and logs. Give each process only the secrets it needs.
- Commit a `.env.example` that names required and optional variables with no real values. Keep real `.env*` files ignored, and have a hook refuse to commit any other `.env*` file.
- Run secret scanning on every commit from the first commit, with `detect-private-key` plus the scanner the project chose. A repo that adds a scanner later has already leaked.
- Mint a separate token for production. Do not reuse a local developer credential.
- Never print a token or cookie. When you check that a variable is set, check presence only.
- Do not expose a service publicly as a convenience workaround. Bind to loopback locally and ask before opening any ingress.
- A write token never carries a prefix that a bundler inlines into client code, such as `NEXT_PUBLIC_` or `VITE_`.
- Encrypt personal data at rest with authenticated encryption that binds tenant, owner and field into the associated data. Record the field and purpose of each decryption, never the value.
- Behaviour flags that exist for a simulator or a test never take effect in production. Refuse them at boot.

## Entry points and environments

- Run the API from the factory: `uvicorn package.app:create_app --factory`. `create_app(settings=None)` builds the settings when none are passed, so a test passes its own.
- Declaring `[tool.fastapi] entrypoint` is acceptable for the framework's own CLI. The owner's repos start the server through the factory, so do that in a project that has no preference.
- Do not log the settings object whole. Log the keys that are set.
