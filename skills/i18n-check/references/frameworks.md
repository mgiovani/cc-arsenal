# Per-framework detection and diffing

Every framework reduces to the same three sets (missing / untranslated / orphan).
What differs is where the default locale lives and how to flatten its file format into
`key -> value` pairs. Pick your framework below.

## next-intl

- **Default locale**: `defaultLocale` in `i18n/routing.ts` (or `middleware.ts` / a
  `next.config.js` matcher). Locale files usually at `messages/<locale>.json` or
  `src/messages/<locale>.json`, referenced from `i18n/request.ts`.
- **Format**: nested JSON.

```bash
python3 - <<'EOF'
import json

def flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        out.update(flatten(v, key)) if isinstance(v, dict) else out.update({key: v})
    return out

base = flatten(json.load(open("messages/en.json")))
target = flatten(json.load(open("messages/pt-BR.json")))
missing = sorted(set(base) - set(target))
orphan = sorted(set(target) - set(base))
untranslated = sorted(k for k in base if k in target and base[k] == target[k])
print("missing:", missing)
print("orphan:", orphan)
print("untranslated:", untranslated)
EOF
```

## i18next / react-i18next

- **Default locale**: `fallbackLng` in the `i18next.init(...)` config.
- **Format**: nested JSON, one file per `<lang>/<namespace>`. Run the same flatten
  script above once per namespace (e.g. `public/locales/en/common.json` vs
  `public/locales/pt-BR/common.json`), not once for the whole language.

## react-intl

- **Default locale**: wherever `defaultLocale` is passed to `IntlProvider`.
- **Format**: usually flat JSON already (`id -> message`), extracted via
  `babel-plugin-formatjs`/`formatjs extract` into `lang/<locale>.json`. If the project
  keeps messages inline (`defineMessages`, `<FormattedMessage defaultMessage="...">`)
  there is no default-locale file — skip Step 2 and rely on the hardcoded-string scan.
- Diff flat JSON with the same script above; flattening is a no-op since it's already
  flat.

## vue-i18n

- **Default locale**: `fallbackLocale` in the `createI18n({...})` config.
- **Format**: JSON or YAML at `src/locales/<lang>.json`/`.yaml`, or inline `<i18n
  locale="en">{...}</i18n>` custom blocks inside `.vue` SFCs.
- JSON: same flatten script as next-intl above.
- YAML: use `js-yaml` if it's already a project dependency (`node -e "..."`), otherwise
  fall back to `ruby -ryaml` (ships with Ruby, present on macOS and most CI images) —
  don't add a new dependency just to parse YAML for this check.

## Django gettext

- **Default locale**: source strings live directly in code (`_("...")`, `{% trans %}`,
  `{% blocktrans %}`) — there is no default-locale catalog file to diff against.
  `LANGUAGE_CODE` in `settings.py` only picks which translation to serve, not where the
  source text lives.
- **Format**: `locale/<lang>/LC_MESSAGES/django.po`, entries are `msgid` / `msgstr`
  pairs. Missing = empty `msgstr ""`. Untranslated = `msgstr` identical to `msgid`.
  Orphan = entries marked obsolete with a leading `#~`.

```bash
awk '
  /^msgid "/ { id = $0 }
  /^msgstr "/ {
    if ($0 == "msgstr \"\"" && id != "msgid \"\"") print "MISSING: " id
  }
' locale/pt-BR/LC_MESSAGES/django.po
```

For the untranslated check, pair up each `msgid`/`msgstr` and compare the quoted text
directly (strip the `msgid "`/`msgstr "` prefix and trailing `"`).

## Rails I18n

- **Default locale**: `config.i18n.default_locale` in `config/application.rb` (defaults
  to `en` if unset).
- **Format**: YAML with the locale as the single top-level key
  (`en: { sidebar: { developer: "Developer" } }`).

```bash
ruby -ryaml -e '
  base = YAML.load_file("config/locales/en.yml")["en"]
  target = YAML.load_file("config/locales/pt-BR.yml")["pt-BR"]

  def flatten(h, prefix = "")
    h.each_with_object({}) do |(k, v), out|
      key = prefix.empty? ? k.to_s : "#{prefix}.#{k}"
      v.is_a?(Hash) ? out.merge!(flatten(v, key)) : out[key] = v
    end
  end

  b, t = flatten(base), flatten(target)
  puts "missing: #{(b.keys - t.keys)}"
  puts "orphan: #{(t.keys - b.keys)}"
  puts "untranslated: #{b.keys.select { |k| t.key?(k) && b[k] == t[k] }}"
'
```
