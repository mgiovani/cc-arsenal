# Hardcoded user-facing string patterns, by ecosystem

Goal: find text a user will see that never went through the project's translate
function. Grep for candidate patterns, then exclude lines that are already wrapped.

## React / Next (JSX, TSX)

```bash
rg -n '>[A-Z][a-zA-Z0-9 ,.!?\x27-]{2,}<' --type tsx --type jsx
rg -n '\b(placeholder|alt|title|aria-label)="[A-Z][a-zA-Z0-9 ]{2,}"' --type tsx --type jsx
```

Exclude a match if the same line (or the enclosing JSX expression) already contains
`t(`, `useTranslations(`, `<Trans`, `<FormattedMessage`, or `intl.formatMessage(`.
Also exclude lines that are clearly not user-facing: `className`, `data-testid`,
`key=`, `href=`, `src=`, `console.*`, code comments.

## Vue templates

```bash
rg -n '>[A-Z][a-zA-Z0-9 ,.!?\x27-]{2,}<' --type vue
rg -n '\b(placeholder|title|alt)="[A-Z][a-zA-Z0-9 ]{2,}"' --type vue
```

Exclude matches already using `{{ $t(...) }}` or `v-t="..."`.

## Django templates

```bash
rg -n '>[A-Z][a-zA-Z0-9 ,.!?\x27-]{2,}<' --glob '*.html'
```

Exclude text already inside `{% trans %}` / `{% blocktrans %}` / `{{ _('...') }}`
tags. A hardcoded string here is any literal English (or default-locale) sentence
sitting directly in the template markup.

## Rails views (ERB / HAML)

```bash
rg -n '>[A-Z][a-zA-Z0-9 ,.!?\x27-]{2,}<' --glob '*.erb'
rg -n '^\s*%[a-z]+\s+[A-Z][a-zA-Z0-9 ,.!?\x27-]{2,}$' --glob '*.haml'
```

Exclude lines already calling `t("...")` / `I18n.t(...)`.

## General false-positive filters (all ecosystems)

Drop a match if the "string" is actually:
- A code identifier, CSS class, or file path (no spaces, `camelCase`/`kebab-case`/`snake_case`).
- A URL, email address, or number.
- Inside a `<script>` block, a comment, or a test fixture file.
- A log/debug call (`console.log`, `logger.info`, `Rails.logger`) — not user-facing.

Do not filter based on string length or "looks like it could be intentional" — that
judgment call belongs to the human reading the report, not to the scan.
