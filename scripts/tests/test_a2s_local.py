"""Tests for the anything-to-skill local source (walk, pass-through, docling chain)."""

import argparse
import importlib.util
import json
import os
import shutil
import sys
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2] / 'skills' / 'anything-to-skill' / 'scripts'
)
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from anything_to_skill import cli  # noqa: E402
from anything_to_skill.core.models import RunSummary, Unit  # noqa: E402
from anything_to_skill.core.workspace import Ctx, Workspace  # noqa: E402
from anything_to_skill.sources.local import (  # noqa: E402
    convert as convert_module,
    run as run_module,
)
from anything_to_skill.sources.local.walk import walk  # noqa: E402

DOCS = Path(__file__).parent / 'fixtures' / 'anything_to_skill' / 'local' / 'docs'
PDF = DOCS / 'book.pdf'
PASSTHROUGH_DONE = 4  # README.md, guide/setup.md, guide/config.rst, notes.txt
SKIPPED = 2  # empty.txt, binary.txt
TWO = 2
MAX_ATTEMPTS = 4


def _rel(paths: list[Path]) -> list[str]:
    return [p.relative_to(DOCS.resolve()).as_posix() for p in paths]


def _args(*, convert: bool = False) -> argparse.Namespace:
    return argparse.Namespace(convert=convert)


@pytest.fixture
def ctx(tmp_path: Path) -> Iterator[Ctx]:
    ws = Workspace.create('t', tmp_path / '.cc-arsenal' / 'a2s')
    with ws.open_store() as store:
        yield Ctx.open(ws, store)


def _seed(ctx: Ctx, path: Path) -> int:
    return ctx.store.add_unit('local', str(path.resolve()), kind='seed', priority=100)


def _files(ctx: Ctx) -> dict[str, Unit]:
    return {Path(u.meta['path']).name: u for u in ctx.store.units('local', kind='file')}


class TestWalk:
    def test_ignores_hidden_binary_and_dependency_dirs(self) -> None:
        assert _rel(walk(DOCS)) == [
            'README.md',
            'binary.txt',
            'book.pdf',
            'empty.txt',
            'guide/config.rst',
            'guide/setup.md',
            'notes.txt',
        ]

    def test_single_file(self) -> None:
        assert walk(DOCS / 'notes.txt') == [(DOCS / 'notes.txt').resolve()]
        assert walk(DOCS / 'data.json') == []

    def test_missing_path(self, tmp_path: Path) -> None:
        assert walk(tmp_path / 'nope') == []

    def test_symlinks_are_not_followed(self, tmp_path: Path) -> None:
        outside = tmp_path / 'outside'
        outside.mkdir()
        (outside / 'secret.md').write_text('secret')
        root = tmp_path / 'root'
        root.mkdir()
        (root / 'ok.md').write_text('ok')
        (root / 'link.md').symlink_to(outside / 'secret.md')
        (root / 'linkdir').symlink_to(outside, target_is_directory=True)
        assert _rel_to(walk(root), root) == ['ok.md']


def _rel_to(paths: list[Path], root: Path) -> list[str]:
    return [p.relative_to(root.resolve()).as_posix() for p in paths]


class TestOutline:
    def test_skips_fenced_code_and_deep_headings(self) -> None:
        md = '# A\n```\n# not\n```\n## B\n### C\n#Nope\n'
        assert convert_module.outline(md) == ['A', 'B']
        assert convert_module.outline(md, max_level=3) == ['A', 'B', 'C']

    def test_limit(self) -> None:
        assert convert_module.outline('# a\n# b\n# c\n', limit=2) == ['a', 'b']


class TestPassthrough:
    def test_folder_seed_expands_and_ingests(self, ctx: Ctx) -> None:
        seed = _seed(ctx, DOCS)
        summary = run_module.run(ctx, _args())
        assert (summary.done, summary.skipped, summary.needs_convert) == (
            PASSTHROUGH_DONE,
            SKIPPED,
            1,
        )
        assert summary.failed == 0
        assert ctx.store.get(seed).status == 'skipped'

        files = _files(ctx)
        readme = files['README.md']
        assert readme.status == 'done'
        assert readme.title == 'Handbook'
        assert readme.hint == {
            'path': 'README.md',
            'headings': ['Handbook', 'Install', 'Usage'],
        }
        assert readme.depth == 0
        assert '```sh' in ctx.store.read_markdown(readme.id)

        setup = files['setup.md']
        assert setup.hint['path'] == 'guide/setup.md'
        assert setup.depth == 1
        assert files['config.rst'].title == 'config'
        assert files['book.pdf'].status == 'needs_convert'
        assert files['empty.txt'].status == files['binary.txt'].status == 'skipped'
        assert files['binary.txt'].error == 'binary content'
        assert ctx.store.token_total('local') > 0

    def test_rerun_is_a_noop(self, ctx: Ctx) -> None:
        _seed(ctx, DOCS)
        run_module.run(ctx, _args())
        again = run_module.run(ctx, _args())
        assert (again.done, again.skipped, again.failed) == (0, 0, 0)
        assert again.needs_convert == 1

    def test_single_file_seed_does_not_collide_with_its_unit(self, ctx: Ctx) -> None:
        _seed(ctx, DOCS / 'notes.txt')
        summary = run_module.run(ctx, _args())
        assert summary.done == 1
        (unit,) = ctx.store.units('local', kind='file')
        assert unit.hint['path'] == 'notes.txt'
        assert ctx.store.read_markdown(unit.id) == 'plain notes\n'

    def test_file_that_became_a_symlink_is_skipped(
        self, ctx: Ctx, tmp_path: Path
    ) -> None:
        folder = tmp_path / 'docs'
        folder.mkdir()
        target = folder / 'a.md'
        target.write_text('# A\n\nbody\n')
        outside = tmp_path / 'secret.md'
        outside.write_text('# Secret\n')
        _seed(ctx, folder)
        run_module._expand(ctx, ctx.store.claim('local')[0], RunSummary())  # noqa: SLF001
        target.unlink()
        target.symlink_to(outside)
        summary = run_module.run(ctx, _args())
        assert (summary.done, summary.skipped) == (0, 1)
        assert not list((ctx.store.root / 'md').glob('*.md'))

    def test_seed_without_supported_files_is_skipped(
        self, ctx: Ctx, tmp_path: Path
    ) -> None:
        empty = tmp_path / 'empty'
        empty.mkdir()
        seed = _seed(ctx, empty)
        summary = run_module.run(ctx, _args())
        assert summary.skipped == 1
        assert 'no supported files' in summary.errors[0]
        assert ctx.store.get(seed).status == 'skipped'

    def test_max_pages_caps_file_units(self, ctx: Ctx) -> None:
        _seed(ctx, DOCS)
        ctx.max_pages = TWO
        summary = run_module.run(ctx, _args())
        assert summary.done + summary.skipped + summary.needs_convert == TWO

    def test_invisible_unicode_is_stripped(self, ctx: Ctx, tmp_path: Path) -> None:
        note = tmp_path / 'a.md'
        note.write_text('# Title\n\nhi\u200b there\U000e0041\n')
        _seed(ctx, note)
        run_module.run(ctx, _args())
        (unit,) = ctx.store.units('local', kind='file')
        assert ctx.store.read_markdown(unit.id) == '# Title\n\nhi there\n'

    def test_unreadable_file_fails_without_crashing(
        self, ctx: Ctx, tmp_path: Path
    ) -> None:
        note = tmp_path / 'gone.md'
        note.write_text('# x')
        _seed(ctx, note)
        ctx.store.add_unit(
            'local',
            'file:///nowhere/lost.md',
            kind='file',
            meta={'path': str(tmp_path / 'lost.md')},
        )
        summary = run_module.run(ctx, _args())
        assert (summary.done, summary.failed) == (1, 1)
        assert 'lost.md' in summary.errors[0]


class TestConvertPhase:
    def test_converts_needs_convert_units_with_stub(
        self, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: list[str] = []

        def fake(path: Path) -> tuple[str, str | None]:
            seen.append(path.name)
            return '# Book Title\n\nbody\n\n## Chapter 1\n\ntext\n', 'Book Title'

        monkeypatch.setattr(run_module, 'convert', fake)
        _seed(ctx, PDF)
        summary = run_module.run(ctx, _args())
        assert summary.needs_convert == 1
        assert seen == []

        summary = run_module.run(ctx, _args(convert=True))
        assert seen == ['book.pdf']
        assert (summary.done, summary.needs_convert) == (1, 0)
        (unit,) = ctx.store.units('local', kind='file')
        assert unit.status == 'done'
        assert unit.title == 'Book Title'
        assert unit.hint['headings'] == ['Book Title', 'Chapter 1']

    def test_single_run_with_convert_flag_does_both_phases(
        self, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(run_module, 'convert', lambda _p: ('# T\n\nbody\n', 'T'))
        _seed(ctx, DOCS)
        summary = run_module.run(ctx, _args(convert=True))
        assert summary.done == PASSTHROUGH_DONE + 1
        assert summary.needs_convert == 0
        assert _files(ctx)['book.pdf'].title == 'T'

    def test_failed_conversion_stays_queued_for_retry(
        self, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def boom(_path: Path) -> tuple[str, str | None]:
            raise convert_module.ConversionError('standard: broken')

        monkeypatch.setattr(run_module, 'convert', boom)
        _seed(ctx, PDF)
        summary = run_module.run(ctx, _args(convert=True))
        assert (summary.done, summary.failed, summary.needs_convert) == (0, 0, 1)
        assert 'broken' in summary.errors[0]
        (unit,) = ctx.store.units('local', kind='file')
        assert unit.status == 'needs_convert'
        assert unit.error == 'standard: broken'
        assert unit.next_at > 0

    def test_exhausted_attempts_mark_failed(
        self, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def boom(_path: Path) -> tuple[str, str | None]:
            raise convert_module.ConversionError('nope')

        monkeypatch.setattr(run_module, 'convert', boom)
        _seed(ctx, PDF)
        summary = RunSummary()
        for _ in range(MAX_ATTEMPTS):
            summary = run_module.run(ctx, _args(convert=True))
            ctx.store._run('UPDATE unit SET next_at = 0')  # noqa: SLF001
        assert (summary.failed, summary.needs_convert) == (1, 0)
        assert ctx.store.units('local', kind='file')[0].status == 'failed'


class FakeConverter:
    def __init__(self, outcome: str | Exception) -> None:
        self.outcome = outcome

    def convert(self, _path: str) -> SimpleNamespace:
        if isinstance(self.outcome, Exception):
            raise self.outcome
        text = self.outcome
        return SimpleNamespace(document=SimpleNamespace(export_to_markdown=lambda: text))


def _fake_docling(
    monkeypatch: pytest.MonkeyPatch, outcomes: dict[str, str | Exception]
) -> list[str]:
    calls: list[str] = []

    def factory(step: str, image: bool) -> FakeConverter:  # noqa: ARG001
        calls.append(step)
        return FakeConverter(outcomes[step])

    monkeypatch.setattr(convert_module, '_docling', factory)
    return calls


class TestConvertChain:
    def test_first_good_step_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls = _fake_docling(monkeypatch, {'standard': '# Real Title\n\n' + 'x' * 40})
        markdown, title = convert_module.convert(PDF)
        assert calls == ['standard']
        assert title == 'Real Title'
        assert markdown.startswith('# Real')

    def test_thin_output_and_errors_escalate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = _fake_docling(
            monkeypatch,
            {
                'standard': '<!-- image -->\n<!-- image -->',
                'accurate': RuntimeError('oom'),
                'ocr': 'scanned text ' * 5,
            },
        )
        markdown, title = convert_module.convert(PDF)
        assert calls == ['standard', 'accurate', 'ocr']
        assert markdown.startswith('scanned text')
        assert title is None

    def test_all_steps_fail_reports_every_reason(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fake_docling(
            monkeypatch,
            {
                'standard': RuntimeError('a'),
                'accurate': RuntimeError('b'),
                'ocr': RuntimeError('c'),
                'pypdfium2': '',
            },
        )
        monkeypatch.setattr(
            convert_module,
            '_pdftotext',
            lambda _p: (_ for _ in ()).throw(RuntimeError('pdftotext is not installed')),
        )
        with pytest.raises(convert_module.ConversionError) as err:
            convert_module.convert(PDF)
        message = str(err.value)
        for part in (
            'standard: RuntimeError: a',
            'ocr: RuntimeError: c',
            'pypdfium2: no text',
            'pdftotext',
        ):
            assert part in message

    def test_missing_docling_goes_straight_to_pdftotext(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: list[str] = []

        def no_docling(step: str, image: bool) -> None:  # noqa: ARG001
            seen.append(step)
            raise ModuleNotFoundError("No module named 'docling'", name='docling')

        monkeypatch.setattr(convert_module, '_docling', no_docling)
        monkeypatch.setattr(convert_module, '_pdftotext', lambda _p: 'layout text ' * 4)
        markdown, _title = convert_module.convert(PDF)
        assert seen == ['standard']
        assert markdown.startswith('layout text')

    def test_non_pdf_uses_only_the_default_converter(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        calls = _fake_docling(monkeypatch, {'default': '# Deck\n\n' + 'slide ' * 10})
        assert convert_module.convert(tmp_path / 'deck.pptx')[1] == 'Deck'
        assert calls == ['default']

    def test_images_only_try_ocr(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        calls = _fake_docling(monkeypatch, {'ocr': RuntimeError('no engine')})
        with pytest.raises(convert_module.ConversionError, match='no engine'):
            convert_module.convert(tmp_path / 'scan.png')
        assert calls == ['ocr']


class TestShimEntryPoints:
    def test_run_source_ingests_and_prints_the_summary(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ws = Workspace.create('t', tmp_path / '.cc-arsenal' / 'a2s')
        with ws.open_store() as store:
            store.add_unit('local', str(DOCS.resolve()), kind='seed', priority=100)
        argv = ['--slug', 't', '--base', str(ws.dir.parent), '--max-pages', '2']
        assert cli.run_source('local', argv) == 0
        # --max-pages 2 covers the seed plus one file; unbounded, four files finish
        assert json.loads(capsys.readouterr().out)['done'] == 1

    def test_run_source_without_a_workspace_exits_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert cli.run_source('local', ['--slug', 'nope', '--base', str(tmp_path)]) == TWO
        assert capsys.readouterr().err.startswith('ingest-local:')

    def test_run_command_reports_a_missing_workspace_and_passes_the_rest(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ran = []
        assert (
            cli.run_command(
                'judge',
                ['--slug', 'nope', '--base', str(tmp_path)],
                lambda _p: None,
                lambda _ws, _a: ran.append(1) or 0,
            )
            == TWO
        )
        assert capsys.readouterr().err.startswith('judge:')
        assert not ran


@pytest.mark.skipif(shutil.which('pdftotext') is None, reason='pdftotext not installed')
def test_pdftotext_fallback_on_real_pdf() -> None:
    assert 'Hello from the fixture PDF' in convert_module._pdftotext(PDF)  # noqa: SLF001


@pytest.mark.skipif(
    importlib.util.find_spec('docling') is None or not os.environ.get('A2S_LIVE'),
    reason='needs docling and its model downloads; set A2S_LIVE=1 to run',
)
def test_real_docling_conversion() -> None:
    markdown, _title = convert_module.convert(PDF)
    assert 'Hello from the fixture PDF' in markdown
