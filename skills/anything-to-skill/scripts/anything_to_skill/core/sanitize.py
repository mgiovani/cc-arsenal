import re
from typing import Any

# ponytail: ZWJ/ZWNJ are stripped too, which drops emoji joins and Indic/Persian
# shaping; acceptable for a docs corpus, split the set if that ever matters.
_RANGES = (
    (0x00AD, 0x00AD),  # soft hyphen
    (0x034F, 0x034F),  # combining grapheme joiner
    (0x061C, 0x061C),  # Arabic letter mark (bidi)
    (0x115F, 0x1160),  # Hangul choseong/jungseong fillers
    (0x17B4, 0x17B5),  # Khmer inherent vowels
    (0x180B, 0x180F),  # Mongolian variation selectors and vowel separator
    (0x200B, 0x200F),  # zero-width space/joiners, LRM/RLM
    (0x2028, 0x202E),  # line/paragraph separators, bidi embeddings and overrides
    (0x2060, 0x206F),  # word joiner, invisible operators, isolates, deprecated controls
    (0x3164, 0x3164),  # Hangul filler
    (0xFE00, 0xFE0F),  # variation selectors
    (0xFEFF, 0xFEFF),  # BOM / zero-width no-break space
    (0xFFA0, 0xFFA0),  # halfwidth Hangul filler
    (0xFFF9, 0xFFFB),  # interlinear annotation controls
    (0x1BCA0, 0x1BCA3),  # shorthand format controls
    (0x13430, 0x1345F),  # Egyptian hieroglyph format controls
    (0x1D173, 0x1D17A),  # musical format controls
    (0xE0000, 0xE0FFF),  # Unicode tag block and variation selectors supplement
)
_INVISIBLE = re.compile('[' + ''.join(f'{chr(a)}-{chr(b)}' for a, b in _RANGES) + ']')


def strip_invisible(text: str) -> str:
    """Remove zero-width, bidi-control and Unicode tag characters (hidden-text vectors)."""
    return _INVISIBLE.sub('', text)


def find_invisible(text: str) -> list[tuple[int, int]]:
    """Return (offset, codepoint) for each invisible character, for scanners."""
    return [(m.start(), ord(m.group())) for m in _INVISIBLE.finditer(text)]


def clean(value: Any) -> Any:
    """strip_invisible over every string in a title/hint/meta value; titles also lose newlines."""
    if isinstance(value, str):
        return ' '.join(strip_invisible(value).split())
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    return value
