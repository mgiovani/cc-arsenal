# Errors and boundaries

## Contents

- [Validate at the boundary](#validate-at-the-boundary)
- [Never lose data silently](#never-lose-data-silently)
- [Domain exceptions](#domain-exceptions)
- [Handling and logging](#handling-and-logging)
- [Time, retries and configuration](#time-retries-and-configuration)

## Validate at the boundary

A trust boundary is any place data enters from outside the process: file paths, names, request bodies, query strings, uploads, subprocess output, environment variables, tokens.

Validate once at the boundary, then let the rest of the code trust the declared types. Without that, malformed data leaks into core logic.

- Where a wrong type must be rejected, use strict parsing. A lenient parser coerces a numeric string into an int and hides the mistake.
- For a path built from input, resolve both paths to absolute form and check the target stays under the base directory (`os.path.commonpath` in Python). Reject the escape with an error.
- Anchor whole-string patterns. In Python use `re.fullmatch`, because `$` also matches before a trailing newline.
- A parser is not a validator. Check what it returns.
- A validator returns a plain bool. A result dict is always truthy, so `if validate(x)` would accept every input.
- A JSON endpoint must survive a literal `null` body and answer 400 for a missing required field, not crash.
- Guard boundary math: check for zero before dividing and for empty before indexing `[0]`.
- Verify a signed token before trusting its identity, and compare signatures in constant time.
- Pass request values to SQL as bound parameters, never by string formatting.

## Never lose data silently

Prefer exclusive create, explicit refusal and a named error over a check-then-write. Two actors can both pass the check.

- Create with an exclusive flag (`open(..., 'x')`, `O_EXCL`) or one atomic statement (`INSERT ... ON CONFLICT`, a single `UPDATE ... RETURNING`). Do not catch a duplicate-key error and retry.
- Write files by writing a temp file and replacing the target, so a crash leaves the old content.
- An importer that skips bad rows quietly loses data. Reject the input, or process the good rows and report the skipped count and reasons.
- Missing, unpriced and failed data never appear as a measured zero. Show "unknown", not 0.
- An unknown error code goes to an explicit unknown branch. A `map[code] ?? 'fallback'` default sends it down the wrong path.

## Domain exceptions

A domain exception carries the facts a caller needs to act, and its message names the fix.

- Name the class for the condition, with an `Error` suffix in Python (`EscalationNotFoundError`, not `BadError`).
- The constructor takes the ids and values and builds the message from them. It also stores them as attributes so callers do not parse the text.
- The message says what to do: `provision web: port 8080 is taken; pick another port in the config` beats `provision failed`.
- Keep one exceptions module per context. Subclass the closest built-in (`ValueError` for refused input, `RuntimeError` for failed operations).
- Re-export driver exceptions under domain names in one module, so the driver is imported in one place.
- Use `raise ... from None` only when hiding the cause is deliberate.
- Never show a client an internal id, stack trace or raw error string. Map the exception to a public response at the edge.

## Handling and logging

- No empty catch, no `except: pass`, no catch that only logs and swallows. Handle the error or re-raise it.
- A narrow named exception with a `pass` body is a deliberate recovery and is fine. A broad `except Exception` is not.
- Handle an error at the layer that can act on it. Lower layers raise.
- Log a failure once, at the boundary, never in every layer it passes through.
- Log levels: `WARNING` for an absorbed anomaly (a retry, a degradation, a 5xx returned). `ERROR` for a failure that needs action. A 4xx is never `ERROR`. `INFO` marks a business or lifecycle event. `DEBUG` stays off in production.
- Keep log messages static and put ids in structured fields. Never log secrets, tokens or personal data. A log is not an audit trail.
- An error message names the real cause and the thing involved. "Parse failed" for a 1-byte file is a lie: say what the file was expected to be.
- Isolate failures per unit of work, but keep the run's exit status failing, so a crash cannot look clean.
- A gate's pass or fail is its own exit code and nothing else.

## Time, retries and configuration

- Every outbound HTTP call and database query gets an explicit timeout.
- Retry only transient failures, with a bound. Every agent or retry loop has a hard maximum.
- Release resources on every path, errors included: `finally`, context managers, effect cleanups.
- Malformed configuration is a hard error with a distinct exit code: unknown keys, bad regexes and a selector that matches nothing.
- Production fails fast when a required setting is missing. It never falls back to a dev or localhost endpoint or test credentials.
- Never disable TLS certificate verification on a production path.
