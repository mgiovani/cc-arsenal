import importlib
import re
import shutil
import subprocess
import sys
from functools import cache
from pathlib import Path
from typing import Any

IMAGES = {'.png', '.jpg', '.jpeg'}
MIN_CHARS = 20
PDFTOTEXT_TIMEOUT_S = 300

_IMAGE_PLACEHOLDER = re.compile(r'<!--\s*image\s*-->')
_HEADING = re.compile(r'^(#{1,6})\s+(.+?)\s*#*\s*$')
_FENCE = re.compile(r'^\s*(```|~~~)')


class ConversionError(RuntimeError):
    pass


def outline(markdown: str, max_level: int = 2, limit: int = 40) -> list[str]:
    """Heading texts down to max_level, skipping fenced code; the chapter breadcrumb hint."""
    out: list[str] = []
    in_fence = False
    for line in markdown.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and (m := _HEADING.match(line)) and len(m[1]) <= max_level:
            out.append(m[2])
            if len(out) == limit:
                break
    return out


def _steps(path: Path) -> list[str]:
    ext = path.suffix.lower()
    if ext == '.pdf':
        return ['standard', 'accurate', 'ocr', 'pypdfium2', 'pdftotext']
    if ext in IMAGES:
        return ['ocr']
    return ['default']


def _thin(markdown: str) -> bool:
    """Scanned pages export as bare image placeholders, which should escalate to OCR."""
    return len(_IMAGE_PLACEHOLDER.sub('', markdown).strip()) < MIN_CHARS


def _docling_module(name: str) -> Any:
    return importlib.import_module(f'docling.{name}')


@cache
def _docling(step: str, image: bool) -> Any:
    """A cached converter per step, so a batch of PDFs loads each model set once."""
    dc = _docling_module('document_converter')
    if step == 'default':
        return dc.DocumentConverter()

    po = _docling_module('datamodel.pipeline_options')
    input_format = _docling_module('datamodel.base_models').InputFormat
    opts = po.PdfPipelineOptions(do_ocr=step == 'ocr', do_table_structure=True)
    opts.table_structure_options.mode = (
        po.TableFormerMode.ACCURATE if step == 'accurate' else po.TableFormerMode.FAST
    )
    if step == 'accurate':
        opts.do_code_enrichment = True
        opts.do_formula_enrichment = True
        if sys.platform == 'darwin':
            accel = _docling_module('datamodel.accelerator_options')
            opts.accelerator_options = accel.AcceleratorOptions(device='mps')
    if step == 'ocr':
        opts.ocr_options = (
            po.OcrMacOptions() if sys.platform == 'darwin' else po.RapidOcrOptions()
        )
    if image:
        option = dc.ImageFormatOption(pipeline_options=opts)
        return dc.DocumentConverter(format_options={input_format.IMAGE: option})
    extra = {}
    if step == 'pypdfium2':
        extra['backend'] = _docling_module(
            'backend.pypdfium2_backend'
        ).PyPdfiumDocumentBackend
    option = dc.PdfFormatOption(pipeline_options=opts, **extra)
    return dc.DocumentConverter(format_options={input_format.PDF: option})


def _pdftotext(path: Path) -> str:
    exe = shutil.which('pdftotext')
    if not exe:
        raise RuntimeError('pdftotext is not installed')
    done = subprocess.run(
        [exe, '-layout', str(path), '-'],
        capture_output=True,
        encoding='utf-8',
        errors='replace',
        check=True,
        timeout=PDFTOTEXT_TIMEOUT_S,
    )
    return done.stdout


def convert(path: Path) -> tuple[str, str | None]:
    """(markdown, title) via docling with the fallback chain; imports docling lazily.

    PDFs escalate standard -> accurate -> OCR -> pypdfium2 backend -> pdftotext. A step
    that raises or yields next to no text moves on to the next one. pdftotext output is
    plain layout text, not markdown, and is the last resort.
    """
    errors: list[str] = []
    docling_missing = False
    for step in _steps(path):
        if docling_missing and step != 'pdftotext':
            continue
        try:
            if step == 'pdftotext':
                markdown = _pdftotext(path)
            else:
                result = _docling(step, path.suffix.lower() in IMAGES).convert(str(path))
                markdown = result.document.export_to_markdown()
        except ImportError as exc:
            docling_missing = docling_missing or (exc.name or '').startswith('docling')
            errors.append(f'{step}: {exc}')
            continue
        except Exception as exc:  # noqa: BLE001
            errors.append(f'{step}: {type(exc).__name__}: {exc}')
            continue
        if _thin(markdown):
            errors.append(f'{step}: no text extracted')
            continue
        title = next(iter(outline(markdown)), None)
        return markdown, title
    raise ConversionError('; '.join(errors))
