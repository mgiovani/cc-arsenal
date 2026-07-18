---
name: i18n-check
description: i18n completeness checker — detects the project's i18n framework (next-intl,
  i18next, react-intl, vue-i18n, Django gettext, Rails I18n), diffs every locale file
  against the default locale for missing keys, untranslated values (identical to the
  source string), and orphan keys, then scans changed files (or the whole codebase)
  for hardcoded user-facing strings that bypass the i18n layer. Reports gaps grouped
  by locale and can scaffold the missing keys. Use when the user mentions i18n,
  translations, locale files, missing translation keys, or reports a localization bug
  like "the pt-BR label is untranslated" or "translations are out of sync". Also reach
  for it proactively after a PR touches locale/translation files or adds new UI copy,
  to catch missing keys before they ship. Not for writing the actual translated text
  (this only reports what's missing/wrong, a human or translation service fills it in)
  and not for scaffolding a brand-new locale from zero (that's a bigger one-time setup,
  not a completeness check).
metadata:
  author: mgiovani
  version: 1.0.1
disable-model-invocation: false
argument-hint: "[locale] [--scaffold]"
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, Task
---

# i18n Check

Finds the three ways translations silently rot: a key added to the default locale but
never copied to the others (missing), a key copied but never translated (still reads
identical to the source), and a key left behind in one locale after being renamed or
removed from the default (orphan). Also catches new UI copy that was hardcoded instead
of routed through the i18n layer in the first place — the most common way a translation
key never gets created.

## Step 1: Detect the framework

Look for these signals, in order, and stop at the first match:

| Signal | Framework | Locale file layout |
|---|---|---|
| `package.json` has `next-intl`; `i18n.ts`/`i18n/request.ts` | next-intl | `messages/<locale>.json`, nested |
| `package.json` has `i18next`/`react-i18next` | i18next | `public/locales/<lang>/<ns>.json` or `src/locales/<lang>.json`, nested |
| `package.json` has `react-intl` | react-intl | `lang/<locale>.json`, flat, or inline `defineMessages` (no files) |
| `package.json` has `vue-i18n` | vue-i18n | `src/locales/<lang>.json`/`.yaml`, or `<i18n>` SFC blocks |
| `manage.py` + `locale/<lang>/LC_MESSAGES/*.po` | Django gettext | `.po` catalogs, source strings live in code |
| `Gemfile` + `config/locales/*.yml` | Rails I18n | YAML keyed by locale at the top level |

If two signals match (e.g. a monorepo with a Rails API and a Vue frontend), run this
skill once per app, not once for the whole repo — their locale files don't overlap.

Read `references/frameworks.md` for the exact default-locale detection and the
flatten/diff one-liner for whichever framework you found. Every framework's diff
reduces to the same three sets (missing / untranslated / orphan) even though the file
format differs.

## Step 2: Diff every locale against the default

For each non-default locale file, flatten both it and the default locale to `key ->
value` pairs and compute:

- **Missing**: key exists in the default locale, absent here.
- **Untranslated**: key exists in both, and the value is byte-identical to the default
  locale's value.
- **Orphan**: key exists here, absent from the default locale (usually a rename or
  deletion that didn't propagate).

**Do not filter out short or single-word identical matches.** The bug class this skill
exists for is exactly that: a one-word label like "Developer" left untranslated because
it looked like it might legitimately be the same in both languages. Report every
identical match and let a human judge which ones are real bugs — a "smart" filter that
suppresses single words or short strings will suppress the real bugs along with the
noise. If you want to make the noise easier to scan, put clearly-fine matches (numbers,
URLs, brand names you can identify from context) in a separate "likely fine" bucket in
the report — do not drop them.

## Step 3: Scan for hardcoded strings

Default scope is the diff against the base branch (`git diff --name-only <base>...HEAD`,
or `git diff --name-only HEAD` for uncommitted work) — new UI copy is what actually
ships broken, and scanning the whole codebase on every check is slow and mostly re-finds
the same pre-existing debt. If the user explicitly asks for a full-codebase sweep, do
that instead. In an environment with subagent/Task support, spawn one per top-level
directory to keep the main context clean on a large repo; otherwise run the same grep
patterns directory-by-directory in a single sequential pass — the result is identical,
just slower on very large repos.

Read `references/hardcoded-strings.md` for the per-ecosystem patterns (JSX text nodes,
Vue templates, Django templates, Rails views) and their exclusions (code identifiers,
`console.log`/`alert` calls, strings already wrapped in the project's translate
function).

## Step 4: Report by locale

```
## pt-BR (messages/pt-BR.json, default: messages/en.json)

Missing (2):
  - sidebar.developer
  - settings.billing.title

Untranslated — identical to en (1):
  - sidebar.developer = "Developer"

Orphan — not in en (1):
  - sidebar.legacyLabel

## Hardcoded strings (bypass i18n) — 1 finding in changed files
  - src/components/Sidebar.tsx:42  <span>Developer</span>  (not wrapped in t()/useTranslations)
```

If a locale has zero findings across all three categories, say so in one line instead
of printing an empty section — don't pad the report.

## Step 5: Scaffold missing keys (only if asked)

If the user wants the missing keys filled in rather than just reported, insert each
missing key into the target locale file at the correct nested path with the value
copied verbatim from the default locale — never invent a translation. This makes the
new key show up as "untranslated" the next time this skill runs, which is the correct
and honest state until a human or translation service actually translates it. For
gettext, add the `msgid`/`msgstr ""` pair (empty `msgstr` is the standard gettext
convention for untranslated). Preserve the file's existing key ordering and formatting
style — read a few existing entries first and match indentation/quote style before
writing.

## Notes

- A locale file that's missing entirely (e.g. `de.json` never created) is not a
  key-level diff — flag it once as "locale file not found" and stop for that locale.
- Pluralized keys (`item_one` / `item_other`, ICU `{count, plural, ...}`) count as one
  logical key for the missing/orphan check; don't flag a plural form as orphan just
  because the default locale collapses plural forms differently.
- react-intl and other setups that keep source strings inline in code (`defineMessages`,
  `<FormattedMessage defaultMessage="...">`) have no default-locale file to diff against
  for missing/untranslated — for those, Step 3's hardcoded-string scan is the primary
  check, and Step 2 only runs on the non-default locale files that do exist.
