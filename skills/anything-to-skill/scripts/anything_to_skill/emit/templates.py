from pathlib import Path
from string import Template

TEMPLATES_DIR = Path(__file__).resolve().parents[3] / 'assets' / 'templates'


def render(template: str, /, **values: str) -> str:
    """string.Template substitution of assets/templates/<template>; a missing value raises KeyError."""
    return Template((TEMPLATES_DIR / template).read_text(encoding='utf-8')).substitute(
        values
    )
