"""Tests for the anything-to-skill YouTube source; yt-dlp, whisper, ffmpeg are faked."""

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2] / 'skills' / 'anything-to-skill' / 'scripts'
)
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from anything_to_skill import sources  # noqa: E402
from anything_to_skill.core.models import RunSummary  # noqa: E402
from anything_to_skill.core.workspace import Ctx, Workspace  # noqa: E402
from anything_to_skill.laya import brain  # noqa: E402
from anything_to_skill.sources.youtube import (  # noqa: E402
    asr,
    captions,
    frames,
    funnel,
    listing,
    run as yt_run,
    vtt,
)
from anything_to_skill.sources.youtube.listing import YtDlpError  # noqa: E402

FIXTURES = Path(__file__).parent / 'fixtures' / 'anything_to_skill' / 'youtube'
PLAYLIST = 'https://www.youtube.com/playlist?list=PLdemo'
VIDEO_A = 'https://www.youtube.com/watch?v=aaaaaaaaaaa'
VIDEO_C = 'https://www.youtube.com/watch?v=ccccccccccc'
THREE = 3
TWO = 2
CAP = 5
LAST_FRAME = 66


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text('utf-8')


class FakeYtDlp:
    """Stands in for subprocess.run inside listing.py, keyed on yt-dlp's arguments."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.list_json = fixture('playlist_flat.json')
        self.info_json = fixture('video_info.json')
        self.vtt: str | None = fixture('manual.vtt')
        self.stderr = ''
        self.fail_stderr: str | None = None
        self.subs_stderr: str | None = None
        # per-video answers, keyed by the 11-character video id at the end of the URL
        self.infos: dict[str, str] = {}
        self.vtts: dict[str, str] = {}
        self.info_stderr: str | None = None
        self.info_429_once = False
        self.list_fail: dict[str, str] = {}

    def __call__(self, cmd: list[str], **_kw: object) -> subprocess.CompletedProcess:
        args = cmd[3:] if cmd[1] == '-m' else cmd[1:]
        self.calls.append(args)
        if self.fail_stderr:
            return subprocess.CompletedProcess(cmd, 1, '', self.fail_stderr)
        out = ''
        vid = re.search(r'([\w-]{11})$', args[-1])
        video = vid.group(1) if vid else ''
        if '--flat-playlist' in args:
            for tab, stderr in self.list_fail.items():
                if args[-1].endswith(tab):
                    return subprocess.CompletedProcess(cmd, 1, '', stderr)
            out = self.list_json
        elif '-J' in args:
            if self.info_429_once:
                self.info_429_once = False
                return subprocess.CompletedProcess(cmd, 1, '', 'HTTP Error 429')
            if self.info_stderr:
                return subprocess.CompletedProcess(cmd, 1, '', self.info_stderr)
            out = self.infos.get(video, self.info_json)
        elif '--write-subs' in args:
            if self.subs_stderr:
                return subprocess.CompletedProcess(cmd, 1, '', self.subs_stderr)
            text = self.vtts.get(video, self.vtt)
            if text is not None:
                target = Path(
                    args[args.index('-o') + 1].replace('%(id)s.%(ext)s', 'x.en.vtt')
                )
                target.write_text(text, 'utf-8')
        elif '-f' in args and args[args.index('-o') + 1].endswith('audio.%(ext)s'):
            Path(args[args.index('-o') + 1].replace('%(ext)s', 'm4a')).write_bytes(b'x')
        return subprocess.CompletedProcess(cmd, 0, out, self.stderr)


@pytest.fixture
def ytdlp(monkeypatch: pytest.MonkeyPatch) -> FakeYtDlp:
    fake = FakeYtDlp()
    monkeypatch.setattr(listing.subprocess, 'run', fake)
    monkeypatch.setattr(listing, '_command', lambda: ['yt-dlp'])
    return fake


@pytest.fixture
def ctx(tmp_path: Path) -> Iterator[Ctx]:
    ws = Workspace.create('demo', tmp_path)
    store = ws.open_store()
    store.set_meta('goal', 'postgres index performance')
    yield Ctx.open(ws, store)
    store.close()


def args(**over: object) -> argparse.Namespace:
    base = {
        'asr': False,
        'asr_model': None,
        'frames': False,
        'max_videos': None,
        'brain': 'rules',
        'rank_meta': None,
        'rank_transcripts': None,
    }
    return argparse.Namespace(**{**base, **over})


def seed(ctx: Ctx, uri: str = PLAYLIST) -> int:
    return ctx.store.add_unit('youtube', uri, kind='seed', priority=100.0)


# routing / parser


def test_detect_routes_youtube_urls() -> None:
    assert sources.route('https://youtu.be/aaaaaaaaaaa') == ('youtube', 10)
    assert sources.route('https://example.com/watch?v=1') == ('web', 1)


def test_add_args_declares_the_shim_flags() -> None:
    parser = argparse.ArgumentParser()
    yt_run.add_args(parser)
    parsed = parser.parse_args(['--asr', '--frames', '--max-videos', '3'])
    assert (parsed.asr, parsed.frames, parsed.max_videos) == (True, True, 3)
    assert (parsed.rank_meta, parsed.rank_transcripts) == (None, None)
    sized = parser.parse_args(['--rank-meta', '20', '--rank-transcripts', '0'])
    assert (sized.rank_meta, sized.rank_transcripts) == (20, 0)


# vtt


def test_parse_manual_vtt_strips_tags_and_entities() -> None:
    cues = vtt.parse_vtt(fixture('manual.vtt'))
    assert cues == [
        (1.0, 'Welcome to the talk & thanks.'),
        (4.5, 'Today: indexes.'),
        (66.0, 'A B-tree keeps keys sorted.'),
    ]


def test_parse_auto_vtt_removes_rolling_duplicates() -> None:
    cues = vtt.parse_vtt(fixture('auto_rolling.vtt'))
    assert [t for _, t in cues] == ['so today we talk', 'about indexes', 'and B-trees']
    assert [round(s) for s, _ in cues] == [0, 4, 6]


def test_parse_vtt_empty_input() -> None:
    assert vtt.parse_vtt('WEBVTT\n\n') == []


CHAPTERS = [
    {'start_time': 0.0, 'title': 'Intro'},
    {'start_time': 65.0, 'title': 'B-trees'},
]


def test_chapters_become_headings_with_anchors() -> None:
    cues = vtt.parse_vtt(fixture('manual.vtt'))
    md = vtt.to_markdown(cues, CHAPTERS, 'Talk')
    assert md.startswith('# Talk\n\n## Intro [00:00]\n\n[00:01] Welcome')
    assert '## B-trees [01:05]\n\n[01:06] A B-tree keeps keys sorted.' in md
    assert md.index('## Intro') < md.index('## B-trees')


def test_paragraph_never_straddles_a_chapter() -> None:
    cues = [(60.0, 'before'), (66.0, 'after')]
    md = vtt.to_markdown(cues, CHAPTERS, 'T')
    assert '[01:00] before\n\n## B-trees [01:05]\n\n[01:06] after' in md


def test_no_chapters_means_no_sections_and_hour_anchors() -> None:
    md = vtt.to_markdown([(0.0, 'a'), (3700.0, 'b')], [], 'T')
    assert '## ' not in md.replace('# T', '')
    assert '[1:01:40] b' in md


def test_frames_land_after_their_paragraph() -> None:
    cues = [(0.0, 'one'), (40.0, 'two')]
    md = vtt.to_markdown(cues, [], 'T', {41.0: 'assets/frames/a-00041.png'})
    assert md.rstrip().endswith('![frame at 00:41](assets/frames/a-00041.png)')
    assert md.index('[00:40] two') < md.index('![frame')


# listing


def test_list_videos_dedupes_and_builds_watch_urls(ytdlp: FakeYtDlp) -> None:
    videos = listing.list_videos(PLAYLIST)
    assert [v['url'] for v in videos] == [
        VIDEO_A,
        'https://www.youtube.com/watch?v=bbbbbbbbbbb',
        VIDEO_C,
    ]
    assert '--flat-playlist' in ytdlp.calls[0]


def test_channel_root_lists_the_videos_tab_and_flattens_tabs(ytdlp: FakeYtDlp) -> None:
    ytdlp.list_json = fixture('channel_tabs.json')
    videos = listing.list_videos('https://www.youtube.com/@demo')
    assert ytdlp.calls[0][-1] == 'https://www.youtube.com/@demo/videos'
    assert len(videos) == TWO


CHANNEL = 'https://www.youtube.com/@demo'


def tab_calls(ytdlp: FakeYtDlp) -> list[str]:
    return [c[-1].rsplit('/', 1)[-1] for c in ytdlp.calls if '--flat-playlist' in c]


def test_channel_root_lists_videos_streams_and_shorts(ytdlp: FakeYtDlp) -> None:
    listing.list_videos(CHANNEL)
    assert tab_calls(ytdlp) == ['videos', 'streams', 'shorts']


@pytest.mark.usefixtures('ytdlp')
def test_channel_tabs_are_merged_without_duplicates() -> None:
    assert len(listing.list_videos(CHANNEL)) == THREE  # the fake answers every tab alike


def test_a_channel_without_a_streams_tab_still_lists_the_rest(ytdlp: FakeYtDlp) -> None:
    ytdlp.list_fail['streams'] = 'ERROR: This channel does not have a streams tab'
    assert len(listing.list_videos(CHANNEL)) == THREE
    assert tab_calls(ytdlp) == ['videos', 'streams', 'shorts']


def test_a_throttled_tab_is_not_a_silent_partial_listing(ytdlp: FakeYtDlp) -> None:
    ytdlp.list_fail['shorts'] = 'ERROR: HTTP Error 429: Too Many Requests'
    with pytest.raises(YtDlpError, match='429'):
        listing.list_videos(CHANNEL)


def test_a_channel_where_no_tab_lists_raises(ytdlp: FakeYtDlp) -> None:
    ytdlp.fail_stderr = 'ERROR: This channel does not exist'
    with pytest.raises(YtDlpError, match='does not exist'):
        listing.list_videos(CHANNEL)


def test_an_explicit_tab_or_playlist_url_is_listed_alone(ytdlp: FakeYtDlp) -> None:
    listing.list_videos(f'{CHANNEL}/shorts')
    listing.list_videos(PLAYLIST)
    assert len(ytdlp.calls) == TWO


def test_listing_and_metadata_calls_pause_between_requests(ytdlp: FakeYtDlp) -> None:
    listing.list_videos(PLAYLIST)
    listing.video_info(VIDEO_A)
    assert all('--sleep-requests' in call for call in ytdlp.calls)


def test_single_video_listing_returns_itself(ytdlp: FakeYtDlp) -> None:
    ytdlp.list_json = fixture('video_info.json')
    assert [v['url'] for v in listing.list_videos(VIDEO_A)] == [VIDEO_A]


@pytest.mark.usefixtures('ytdlp')
def test_video_info_keeps_only_useful_keys() -> None:
    info = listing.video_info(VIDEO_A)
    assert 'formats' not in info
    assert info['chapters'][1]['title'] == 'B-trees'
    assert info['upload_date'] == '20260101'


@pytest.mark.parametrize(
    ('stderr', 'needle', 'permanent'),
    [
        (
            'ERROR: n challenge solving failed: no JavaScript runtime',
            'install deno',
            False,
        ),
        ('WARNING: PO Token missing\nERROR: x', 'PO token', False),
        ("ERROR: Sign in to confirm you're not a bot", 'bot', False),
        ('ERROR: [youtube] abc: Private video. Sign in', 'Private video', True),
    ],
)
def test_error_messages_are_actionable(
    ytdlp: FakeYtDlp, stderr: str, needle: str, permanent: bool
) -> None:
    ytdlp.fail_stderr = stderr
    with pytest.raises(YtDlpError, match=needle) as exc:
        listing.video_info(VIDEO_A)
    assert exc.value.permanent is permanent


def test_missing_yt_dlp_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(listing.importlib.util, 'find_spec', lambda _n: None)
    monkeypatch.setattr(listing.shutil, 'which', lambda _n: None)
    with pytest.raises(YtDlpError, match='not installed'):
        listing.ytdlp(['-J'], VIDEO_A)


# captions


def test_fetch_captions_returns_vtt_path(ytdlp: FakeYtDlp, tmp_path: Path) -> None:
    path = captions.fetch_captions(VIDEO_A, tmp_path)
    assert path is not None
    assert path.suffix == '.vtt'
    flags = ytdlp.calls[0]
    assert '--write-subs' in flags
    assert '--write-auto-subs' in flags


def test_regional_language_tag_is_reduced_to_the_track_key(
    ytdlp: FakeYtDlp, tmp_path: Path
) -> None:
    captions.fetch_captions(VIDEO_A, tmp_path, 'en-US')
    flags = ytdlp.calls[0]
    assert flags[flags.index('--sub-langs') + 1] == 'en'


def test_uploader_language_never_reaches_yt_dlp_as_a_regex(
    ytdlp: FakeYtDlp, tmp_path: Path
) -> None:
    captions.fetch_captions(VIDEO_A, tmp_path, '.*')
    flags = ytdlp.calls[0]
    assert flags[flags.index('--sub-langs') + 1] == 'en'


def test_url_follows_a_double_dash_so_it_cannot_be_an_option(
    ytdlp: FakeYtDlp, tmp_path: Path
) -> None:
    captions.fetch_captions('--exec=id', tmp_path)
    assert ytdlp.calls[0][-2:] == ['--', '--exec=id']


def test_fetch_captions_none_without_tracks(ytdlp: FakeYtDlp, tmp_path: Path) -> None:
    ytdlp.vtt = None
    assert captions.fetch_captions(VIDEO_A, tmp_path) is None


def test_throttled_subtitle_request_is_not_mistaken_for_no_captions(
    ytdlp: FakeYtDlp, tmp_path: Path
) -> None:
    ytdlp.vtt = None
    ytdlp.stderr = 'WARNING: Unable to download video subtitles: HTTP Error 429'
    with pytest.raises(YtDlpError, match='429'):
        captions.fetch_captions(VIDEO_A, tmp_path)


def test_captions_request_pauses_between_subtitle_downloads(
    ytdlp: FakeYtDlp, tmp_path: Path
) -> None:
    captions.fetch_captions(VIDEO_A, tmp_path)
    call = ytdlp.calls[0]
    assert call[call.index('--sleep-subtitles') + 1] == captions.SLEEP_S
    assert '--sleep-requests' in call


def test_nonzero_subtitle_429_is_a_captions_throttle(
    ytdlp: FakeYtDlp, tmp_path: Path
) -> None:
    ytdlp.subs_stderr = (
        "ERROR: Unable to download video subtitles for 'en': HTTP Error 429"
    )
    with pytest.raises(captions.CaptionsThrottledError) as caught:
        captions.fetch_captions(VIDEO_A, tmp_path)
    assert caught.value.throttled


# run: seeds, captions, needs_asr


@pytest.mark.usefixtures('ytdlp')
def test_seed_expands_filters_by_goal_and_caps(ctx: Ctx) -> None:
    seed_id = seed(ctx)
    summary = yt_run.run(ctx, args(max_videos=1))
    videos = ctx.store.units('youtube', kind='video')
    assert [v.uri for v in videos] == [VIDEO_A]  # cat video filtered, cap of 1 applied
    assert ctx.store.get(seed_id).status == 'skipped'
    assert summary.done == 1


@pytest.mark.usefixtures('ytdlp')
def test_laya_brain_picks_the_ranked_video_and_shows_it_in_status(
    ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Ranker:
        def __init__(self, _goal: str) -> None: ...

        def score(
            self, entries: list[dict], _hits: list[int]
        ) -> tuple[list[float | None], list[bool]]:
            scores = [0.9 if 'planner' in e['title'] else 0.1 for e in entries]
            return list(scores), [True] * len(entries)

    monkeypatch.setattr(brain, 'LayaVideoRanker', Ranker)
    seed_id = seed(ctx)
    yt_run.run(ctx, args(max_videos=1, brain='laya', rank_meta=0, rank_transcripts=0))
    assert [v.uri for v in ctx.store.units('youtube', kind='video')] == [VIDEO_C]
    record = ctx.store.all_meta()['youtube.ranking'][PLAYLIST]
    assert record['chosen'][0]['id'] == 'ccccccccccc'
    assert {r['id'] for r in record['skipped']} == {'aaaaaaaaaaa', 'bbbbbbbbbbb'}
    assert ctx.store.get(seed_id).status == 'skipped'


def test_goal_ending_in_a_period_still_matches_its_last_word() -> None:
    entries = [
        {'title': 'Query performance', 'url': 'u1'},
        {'title': 'Cooking pasta', 'url': 'u2'},
    ]
    picked = yt_run.select(entries, 'Learn performance.', 5)
    assert [e['url'] for e, _ in picked] == ['u1']


def test_near_duplicate_picks_keep_the_longer_and_take_the_next_candidate() -> None:
    entries = [
        {'title': 'Attention explained #shorts', 'url': 'short', 'duration': 60},
        {'title': 'Attention explained in depth', 'url': 'long', 'duration': 1800},
        {'title': 'Attention: the math of attention', 'url': 'other', 'duration': 900},
    ]
    picked = yt_run.select(entries, 'attention', 2)
    assert [e['url'] for e, _ in picked] == ['long', 'other']


def test_dedupe_pushes_losers_behind_and_keeps_distinct_titles() -> None:
    entries = [
        {'title': 'Rust ownership explained'},
        {'title': 'Rust ownership explained again'},
        {'title': 'Cargo workspaces'},
    ]
    assert yt_run.dedupe(entries, [0, 1, 2]) == [0, 2, 1]
    assert yt_run.dedupe(entries[:1] + entries[2:], [0, 1]) == [0, 1]


def test_a_short_on_the_topic_of_a_long_video_is_a_duplicate() -> None:
    short = {'title': 'Rust ownership #shorts', 'duration': 45}
    long = {
        'title': 'Rust ownership, borrowing and lifetimes in one hour',
        'duration': 3600,
    }
    assert yt_run.near_duplicates(short, long)
    assert not yt_run.near_duplicates({**short, 'duration': 600}, long)


@pytest.mark.usefixtures('ytdlp')
def test_no_goal_match_falls_back_to_first_videos(ctx: Ctx) -> None:
    ctx.goal = 'gardening'
    seed(ctx)
    yt_run.run(ctx, args(max_videos=2))
    assert len(ctx.store.units('youtube', kind='video')) == TWO


def test_captioned_video_becomes_markdown_with_chapters(
    ctx: Ctx, ytdlp: FakeYtDlp
) -> None:
    seed(ctx, VIDEO_A)
    ytdlp.list_json = fixture('video_info.json')
    summary = yt_run.run(ctx, args())
    unit = ctx.store.get_by_uri('https://youtu.be/aaaaaaaaaaa')
    assert unit is not None
    assert unit.status == 'done'
    assert (summary.done, summary.needs_asr) == (1, 0)
    md = ctx.store.read_markdown(unit.id)
    assert '## B-trees [01:05]' in md
    assert unit.title == 'Postgres index deep dive'
    assert unit.hint == {'path': ['Demo Channel'], 'headings': ['Intro', 'B-trees']}
    assert unit.meta['text_from'] == 'captions'
    assert unit.meta['description'].startswith('0:00 Intro')


def test_video_without_captions_is_needs_asr(ctx: Ctx, ytdlp: FakeYtDlp) -> None:
    ytdlp.vtt = None
    seed(ctx, VIDEO_A)
    ytdlp.list_json = fixture('video_info.json')
    summary = yt_run.run(ctx, args())
    assert ctx.store.get_by_uri('https://youtu.be/aaaaaaaaaaa').status == 'needs_asr'  # type: ignore[union-attr]
    assert (summary.done, summary.needs_asr) == (0, 1)


def test_transient_failure_retries_and_surfaces_deno_error(
    ctx: Ctx, ytdlp: FakeYtDlp
) -> None:
    ctx.store.add_unit('youtube', VIDEO_A, kind='video')
    ytdlp.fail_stderr = 'ERROR: no JavaScript runtime found'
    summary = yt_run.run(ctx, args())
    unit = ctx.store.get_by_uri(VIDEO_A)
    assert unit is not None
    assert unit.status == 'pending'
    assert unit.next_at > unit.updated - 1
    assert 'deno' in summary.errors[0]


def test_private_video_is_skipped_not_retried(ctx: Ctx, ytdlp: FakeYtDlp) -> None:
    ctx.store.add_unit('youtube', VIDEO_A, kind='video')
    ytdlp.fail_stderr = 'ERROR: Private video'
    summary = yt_run.run(ctx, args())
    assert ctx.store.get_by_uri(VIDEO_A).status == 'skipped'  # type: ignore[union-attr]
    assert summary.skipped == 1


def test_listing_failure_marks_the_seed_failed(ctx: Ctx, ytdlp: FakeYtDlp) -> None:
    seed_id = seed(ctx)
    ytdlp.fail_stderr = "ERROR: Sign in to confirm you're not a bot"
    summary = yt_run.run(ctx, args())
    assert ctx.store.get(seed_id).status == 'failed'
    assert summary.failed == 1
    assert 'bot' in summary.errors[0]


def _two_videos(ctx: Ctx) -> None:
    for uri in (VIDEO_A, VIDEO_C):
        ctx.store.add_unit('youtube', uri, kind='video')


@pytest.mark.usefixtures('ytdlp')
def test_max_pages_limits_a_run(ctx: Ctx) -> None:
    _two_videos(ctx)
    ctx.max_pages = 1
    summary = yt_run.run(ctx, args())
    assert summary.done == 1
    assert len(ctx.store.units('youtube', 'pending')) == 1


@pytest.mark.usefixtures('ytdlp')
def test_resumed_run_counts_stored_videos_against_max_pages(ctx: Ctx) -> None:
    _two_videos(ctx)
    ctx.max_pages = 1
    assert yt_run.run(ctx, args()).done == 1
    assert yt_run.run(ctx, args()).done == 0
    assert len(ctx.store.units('youtube', 'done')) == 1
    assert len(ctx.store.units('youtube', 'pending')) == 1


@pytest.mark.usefixtures('ytdlp')
def test_max_pages_also_caps_the_videos_kept_from_a_listing(
    ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Ranker:
        def __init__(self, _goal: str) -> None: ...

        def score(
            self, entries: list[dict], _hits: list[int]
        ) -> tuple[list[float | None], list[bool]]:
            return [0.5] * len(entries), [True] * len(entries)

    monkeypatch.setattr(brain, 'LayaVideoRanker', Ranker)
    seed(ctx)
    ctx.max_pages = 1
    yt_run.run(ctx, args(max_videos=2, brain='laya'))
    assert len(ctx.store.units('youtube', kind='video')) == 1
    assert ctx.store.all_meta()['youtube.ranking'][PLAYLIST]['cap'] == 1


# ASR


def fake_whisper(monkeypatch: pytest.MonkeyPatch, cues: list[tuple[float, str]]) -> list:
    seen: list = []

    def transcribe(audio: Path, model: str | None = None) -> list[tuple[float, str]]:
        seen.append((audio.name, model))
        return cues

    monkeypatch.setattr(yt_run.asr, 'transcribe', transcribe)
    return seen


@pytest.mark.usefixtures('ytdlp')
def test_asr_pass_transcribes_needs_asr_units(
    ctx: Ctx,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uid = ctx.store.add_unit('youtube', VIDEO_A, kind='video')
    ctx.store.mark(uid, 'needs_asr')
    seen = fake_whisper(monkeypatch, [(0.0, 'hello'), (70.0, 'btrees')])
    summary = yt_run.run(ctx, args(asr=True, asr_model='tiny'))
    unit = ctx.store.get(uid)
    assert unit.status == 'done'
    assert unit.meta['text_from'] == 'asr'
    assert seen == [('audio.m4a', 'tiny')]
    assert '## B-trees [01:05]' in ctx.store.read_markdown(uid)
    assert (summary.done, summary.needs_asr) == (1, 0)


def test_asr_pass_ignores_pending_units(
    ctx: Ctx, ytdlp: FakeYtDlp, monkeypatch: pytest.MonkeyPatch
) -> None:
    uid = ctx.store.add_unit('youtube', VIDEO_A, kind='video')
    fake_whisper(monkeypatch, [(0.0, 'x')])
    yt_run.run(ctx, args(asr=True))
    assert ctx.store.get(uid).status == 'pending'
    assert ytdlp.calls == []


def test_missing_whisper_backend_stops_and_keeps_unit(
    ctx: Ctx, ytdlp: FakeYtDlp, monkeypatch: pytest.MonkeyPatch
) -> None:
    uids = [ctx.store.add_unit('youtube', u, kind='video') for u in (VIDEO_A, VIDEO_C)]
    for uid in uids:
        ctx.store.mark(uid, 'needs_asr')

    def boom(_audio: Path, _model: str | None = None) -> list:
        raise ImportError('mlx_whisper')

    monkeypatch.setattr(yt_run.asr, 'transcribe', boom)
    summary = yt_run.run(ctx, args(asr=True))
    assert summary.needs_asr == TWO
    assert 'transcribe.py' in summary.errors[0]
    assert len(ytdlp.calls) == TWO  # one info+audio pair, then it stops


def _needs_asr(ctx: Ctx) -> int:
    uid = ctx.store.add_unit('youtube', VIDEO_A, kind='video')
    ctx.store.mark(uid, 'needs_asr')
    return uid


@pytest.mark.usefixtures('ytdlp')
def test_asr_runtime_error_is_recorded_and_retried_not_fatal(
    ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    uid = _needs_asr(ctx)

    def boom(_audio: Path, _model: str | None = None) -> list:
        raise RuntimeError('model download failed')

    monkeypatch.setattr(yt_run.asr, 'transcribe', boom)
    summary = yt_run.run(ctx, args(asr=True))
    unit = ctx.store.get(uid)
    assert unit.status == 'needs_asr'
    assert unit.attempts >= 1
    assert unit.error is not None
    assert 'RuntimeError: model download failed' in unit.error
    assert 'transcription failed' in summary.errors[0]


@pytest.mark.usefixtures('ytdlp')
def test_silent_video_is_skipped_by_asr(
    ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    uid = _needs_asr(ctx)
    fake_whisper(monkeypatch, [])
    summary = yt_run.run(ctx, args(asr=True))
    assert ctx.store.get(uid).status == 'skipped'
    assert summary.skipped == 1


def test_asr_download_failures_skip_permanent_and_retry_transient(
    ctx: Ctx, ytdlp: FakeYtDlp
) -> None:
    uid = _needs_asr(ctx)
    ytdlp.fail_stderr = 'ERROR: Private video'
    assert yt_run.run(ctx, args(asr=True)).skipped == 1
    assert ctx.store.get(uid).status == 'skipped'
    uid = ctx.store.add_unit('youtube', VIDEO_C, kind='video')
    ctx.store.mark(uid, 'needs_asr')
    ytdlp.fail_stderr = 'ERROR: no JavaScript runtime found'
    yt_run.run(ctx, args(asr=True))
    assert ctx.store.get(uid).status == 'needs_asr'
    assert ctx.store.get(uid).attempts >= 1


def test_asr_audio_403_is_logged_as_a_throttle_and_retried(
    ctx: Ctx, ytdlp: FakeYtDlp
) -> None:
    uid = _needs_asr(ctx)
    ytdlp.fail_stderr = 'ERROR: unable to download video data: HTTP Error 403: Forbidden'
    yt_run.run(ctx, args(asr=True))
    (event,) = throttle_events(ctx)
    assert (event['host'], event['event'], event['status']) == ('youtube.com', '403', 403)
    assert ctx.store.get(uid).status == 'needs_asr'


def test_asr_picks_mlx_only_on_apple_silicon(monkeypatch: pytest.MonkeyPatch) -> None:
    class Faster:
        def __init__(self, name: str, **_kw: object) -> None:
            self.name = name

        def transcribe(self, _path: str, **_kw: object) -> tuple[list, None]:
            seg = type('S', (), {'start': 2.0, 'text': ' hi '})()
            return [seg, type('S', (), {'start': 3.0, 'text': ' '})()], None

    fake = type(sys)('faster_whisper')
    fake.WhisperModel = Faster  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, 'faster_whisper', fake)
    monkeypatch.setattr(asr.platform, 'machine', lambda: 'x86_64')
    assert asr.transcribe(Path('a.m4a')) == [(2.0, 'hi')]

    mlx = type(sys)('mlx_whisper')
    mlx.transcribe = lambda _p, **_kw: {  # type: ignore[attr-defined]
        'segments': [{'start': 1, 'text': ' yo '}]
    }
    monkeypatch.setitem(sys.modules, 'mlx_whisper', mlx)
    monkeypatch.setattr(asr.sys, 'platform', 'darwin')
    monkeypatch.setattr(asr.platform, 'machine', lambda: 'arm64')
    assert asr.transcribe(Path('a.m4a')) == [(1.0, 'yo')]


# frames


def test_frame_timestamps_chapters_first_then_cue_phrases_spaced() -> None:
    cues = [(30.0, 'as you can see here'), (33.0, 'this slide shows'), (100.0, 'plain')]
    stamps = frames.frame_timestamps(CHAPTERS, cues)
    assert stamps == [1.0, 31.0, 66.0]  # 34.0 is within the gap of 31.0


def test_frame_timestamps_respect_cap() -> None:
    chapters = [{'start_time': i * 60.0} for i in range(30)]
    assert len(frames.frame_timestamps(chapters, [], cap=CAP)) == CAP


class Hash(int):
    """Stands in for an imagehash value: subtraction is the hamming distance."""

    def __sub__(self, other: int) -> int:
        return bin(int(self) ^ int(other)).count('1')


def test_dedupe_drops_near_duplicates(tmp_path: Path) -> None:
    paths = []
    for name in ('a-00001.png', 'a-00031.png', 'a-00066.png'):
        (tmp_path / name).write_bytes(b'x')
        paths.append(tmp_path / name)
    hashes = {
        'a-00001.png': Hash(0b0000),
        'a-00031.png': Hash(0b0001),
        'a-00066.png': Hash(0xFFFF),
    }
    kept = frames.dedupe(paths, lambda p: hashes[p.name])
    assert [p.name for p in kept] == ['a-00001.png', 'a-00066.png']
    assert not (tmp_path / 'a-00031.png').exists()
    assert frames.seconds_of(kept[1]) == LAST_FRAME


@pytest.mark.usefixtures('ytdlp')
def test_extract_frames_runs_ffmpeg_per_timestamp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ffmpeg_calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kw: object) -> subprocess.CompletedProcess:
        if cmd[0] == 'ffmpeg':
            ffmpeg_calls.append(cmd)
            Path(cmd[-1]).write_bytes(b'png')
            return subprocess.CompletedProcess(cmd, 0)
        Path(cmd[cmd.index('-o') + 1].replace('%(ext)s', 'mp4')).write_bytes(b'v')
        return subprocess.CompletedProcess(cmd, 0, '', '')

    monkeypatch.setattr(frames.subprocess, 'run', fake_run)
    monkeypatch.setattr(listing.subprocess, 'run', fake_run)
    monkeypatch.setattr(frames.shutil, 'which', lambda _n: '/usr/bin/ffmpeg')
    monkeypatch.setattr(frames.importlib.util, 'find_spec', lambda _n: object())
    monkeypatch.setattr(frames, 'dedupe', lambda paths: paths)
    out = frames.extract_frames(VIDEO_A, [1.0, 66.0], tmp_path / 'f', prefix='vid')
    assert [p.name for p in out] == ['vid-00001.png', 'vid-00066.png']
    assert len(ffmpeg_calls) == TWO


@pytest.mark.usefixtures('ytdlp')
def test_a_hung_ffmpeg_skips_that_timestamp_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(cmd: list[str], **kw: object) -> subprocess.CompletedProcess:
        if cmd[0] == 'ffmpeg':
            assert kw['timeout'] == frames.FFMPEG_TIMEOUT_S
            if '-ss' in cmd and cmd[cmd.index('-ss') + 1] == '1.0':
                raise subprocess.TimeoutExpired(cmd, frames.FFMPEG_TIMEOUT_S)
            Path(cmd[-1]).write_bytes(b'png')
            return subprocess.CompletedProcess(cmd, 0)
        Path(cmd[cmd.index('-o') + 1].replace('%(ext)s', 'mp4')).write_bytes(b'v')
        return subprocess.CompletedProcess(cmd, 0, '', '')

    monkeypatch.setattr(frames.subprocess, 'run', fake_run)
    monkeypatch.setattr(listing.subprocess, 'run', fake_run)
    monkeypatch.setattr(frames.shutil, 'which', lambda _n: '/usr/bin/ffmpeg')
    monkeypatch.setattr(frames.importlib.util, 'find_spec', lambda _n: object())
    monkeypatch.setattr(frames, 'dedupe', lambda paths: paths)
    out = frames.extract_frames(VIDEO_A, [1.0, 66.0], tmp_path / 'f', prefix='vid')
    assert [p.name for p in out] == ['vid-00066.png']


def test_frames_need_ffmpeg(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(frames.shutil, 'which', lambda _n: None)
    with pytest.raises(YtDlpError, match='ffmpeg'):
        frames.extract_frames(VIDEO_A, [1.0], tmp_path)


@pytest.mark.usefixtures('ytdlp')
def test_run_with_frames_references_stills_in_markdown(
    ctx: Ctx,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx.store.add_unit('youtube', VIDEO_A, kind='video')
    monkeypatch.setattr(
        yt_run.frames,
        'extract_frames',
        lambda _url, stamps, out, prefix: [
            out / f'{prefix}-{int(s):05d}.png' for s in stamps
        ],
    )
    summary = yt_run.run(ctx, args(frames=True))
    unit = ctx.store.get_by_uri(VIDEO_A)
    assert unit is not None
    assert (
        '![frame at 00:01](assets/frames/aaaaaaaaaaa-00001.png)'
        in ctx.store.read_markdown(unit.id)
    )
    assert unit.meta['frames']['66.0'] == 'assets/frames/aaaaaaaaaaa-00066.png'
    assert summary.done == 1


@pytest.mark.usefixtures('ytdlp')
def test_frame_failure_keeps_the_transcript(
    ctx: Ctx,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx.store.add_unit('youtube', VIDEO_A, kind='video')

    def no_ffmpeg(*_a: object, **_k: object) -> list:
        raise YtDlpError('ffmpeg is required for --frames but was not found on PATH')

    monkeypatch.setattr(yt_run.frames, 'extract_frames', no_ffmpeg)
    summary = yt_run.run(ctx, args(frames=True))
    assert ctx.store.get_by_uri(VIDEO_A).status == 'done'  # type: ignore[union-attr]
    assert 'ffmpeg' in summary.errors[0]


@pytest.mark.parametrize(
    'script', ['ingest_youtube.py', 'transcribe.py', 'youtube_brain.py']
)
def test_every_youtube_entry_point_declares_the_frames_dependencies(script: str) -> None:
    header = (SCRIPTS_DIR / script).read_text('utf-8').split('# ///')[1]
    assert '"pillow"' in header
    assert '"imagehash"' in header


@pytest.mark.usefixtures('ytdlp')
def test_summary_json_round_trips(ctx: Ctx) -> None:
    seed(ctx)
    data = json.loads(yt_run.run(ctx, args()).to_json())
    assert data['done'] == TWO


# 429 handling


def throttle_events(ctx: Ctx) -> list[dict]:
    return ctx.store.throttle_events()


def test_subtitle_429_is_logged_as_a_throttle_event(ctx: Ctx, ytdlp: FakeYtDlp) -> None:
    ctx.store.add_unit('youtube', VIDEO_A, kind='video')
    ytdlp.subs_stderr = (
        "ERROR: Unable to download video subtitles for 'en': HTTP Error 429"
    )
    yt_run.run(ctx, args())
    (event,) = throttle_events(ctx)
    assert (event['host'], event['event'], event['status']) == ('youtube.com', '429', 429)
    assert event['wait'] > 0


def test_exit_zero_subtitle_429_is_logged_too(ctx: Ctx, ytdlp: FakeYtDlp) -> None:
    ctx.store.add_unit('youtube', VIDEO_A, kind='video')
    ytdlp.vtt = None
    ytdlp.stderr = 'WARNING: Unable to download video subtitles: HTTP Error 429'
    yt_run.run(ctx, args())
    assert [e['event'] for e in throttle_events(ctx)] == ['429']


def test_listing_429_is_logged(ctx: Ctx, ytdlp: FakeYtDlp) -> None:
    seed(ctx)
    ytdlp.fail_stderr = 'ERROR: HTTP Error 429: Too Many Requests'
    yt_run.run(ctx, args())
    assert [e['event'] for e in throttle_events(ctx)] == ['429']


def test_other_failures_are_not_logged_as_throttles(ctx: Ctx, ytdlp: FakeYtDlp) -> None:
    ctx.store.add_unit('youtube', VIDEO_A, kind='video')
    ytdlp.fail_stderr = 'ERROR: no JavaScript runtime found'
    yt_run.run(ctx, args())
    assert throttle_events(ctx) == []


def test_second_consecutive_subtitle_429_hands_the_video_to_asr(
    ctx: Ctx, ytdlp: FakeYtDlp, monkeypatch: pytest.MonkeyPatch
) -> None:
    uid = ctx.store.add_unit('youtube', VIDEO_A, kind='video')
    ytdlp.subs_stderr = (
        "ERROR: Unable to download video subtitles for 'en': HTTP Error 429"
    )
    first = yt_run.run(ctx, args())
    assert ctx.store.get(uid).status == 'pending'
    assert first.needs_asr == 0
    ctx.store.requeue('pending')  # skip the backoff wait, keep the recorded error
    second = yt_run.run(ctx, args())
    unit = ctx.store.get(uid)
    assert (unit.status, unit.attempts) == ('needs_asr', 0)
    assert second.needs_asr == 1
    assert second.failed == 0
    assert any('needs_asr' in e for e in second.errors)
    assert len(throttle_events(ctx)) == TWO
    fake_whisper(monkeypatch, [(0.0, 'hello')])
    yt_run.run(ctx, args(asr=True))
    assert ctx.store.get(uid).status == 'done'


def test_a_non_throttle_failure_resets_the_consecutive_count(
    ctx: Ctx, ytdlp: FakeYtDlp
) -> None:
    uid = ctx.store.add_unit('youtube', VIDEO_A, kind='video')
    ytdlp.subs_stderr = (
        "ERROR: Unable to download video subtitles for 'en': HTTP Error 429"
    )
    yt_run.run(ctx, args())
    ctx.store.requeue('pending')
    ytdlp.subs_stderr = None
    ytdlp.fail_stderr = 'ERROR: no JavaScript runtime found'
    yt_run.run(ctx, args())
    ctx.store.requeue('pending')
    ytdlp.fail_stderr = None
    ytdlp.subs_stderr = (
        "ERROR: Unable to download video subtitles for 'en': HTTP Error 429"
    )
    yt_run.run(ctx, args())
    assert ctx.store.get(uid).status == 'pending'


def test_rerun_during_backoff_says_how_many_units_wait_and_until_when(
    ctx: Ctx, ytdlp: FakeYtDlp, capsys: pytest.CaptureFixture[str]
) -> None:
    ctx.store.add_unit('youtube', VIDEO_A, kind='video')
    ytdlp.fail_stderr = 'ERROR: no JavaScript runtime found'
    yt_run.run(ctx, args())
    ytdlp.calls.clear()
    capsys.readouterr()
    summary = yt_run.run(ctx, args())
    assert ytdlp.calls == []
    assert summary.done == 0
    assert any('1 units waiting until' in e for e in summary.errors)
    assert '1 units waiting until' in capsys.readouterr().err


@pytest.mark.usefixtures('ytdlp')
def test_no_waiting_note_when_nothing_is_backing_off(ctx: Ctx) -> None:
    seed(ctx)
    assert not any('waiting' in e for e in yt_run.run(ctx, args()).errors)


# ranking funnel: stage 1 titles, stage 2 description and chapters, stage 3 captions

GOAL = 'backpropagation'
CLICKBAIT, HIDDEN, FILLER = 'aaaaaaaaaaa', 'bbbbbbbbbbb', 'ccccccccccc'
ONE_FIVE_TWO = '\n\n'.join(
    f'00:00:{i:02d}.000 --> 00:00:{i + 1:02d}.000\n{line}'
    for i, line in enumerate(
        ['welcome', 'today backpropagation', 'gradients flow back'], 1
    )
)
DEEP_LISTING = {
    '_type': 'playlist',
    'entries': [
        {'id': CLICKBAIT, 'title': 'Deep learning crash course'},
        {'id': HIDDEN, 'title': 'Episode 12'},
        {'id': FILLER, 'title': 'Cooking pasta'},
    ],
}


def info_for(video: str, description: str) -> str:
    return json.dumps(
        {'id': video, 'title': video, 'description': description, 'language': 'en'}
    )


class FunnelRanker:
    """Titles favour the clickbait; description and captions favour the hidden gem."""

    def __init__(self, _goal: str = GOAL) -> None:
        self.judged: list[str] = []

    def score(self, entries: list[dict], _hits: list[int]) -> tuple[list, list[bool]]:
        by_title = {'Deep learning crash course': 0.9, 'Episode 12': 0.3}
        return [by_title.get(e['title'], 0.1) for e in entries], [True] * len(entries)

    def judge(self, evidence: list[str]) -> list[float]:
        self.judged += evidence
        return [0.9 if GOAL in text else 0.1 for text in evidence]


@pytest.fixture
def deep(ytdlp: FakeYtDlp) -> FakeYtDlp:
    ytdlp.list_json = json.dumps(DEEP_LISTING)
    ytdlp.infos = {
        CLICKBAIT: info_for(CLICKBAIT, 'a general overview'),
        HIDDEN: info_for(HIDDEN, 'we derive backpropagation step by step'),
        FILLER: info_for(FILLER, 'pasta'),
    }
    ytdlp.vtts = {HIDDEN: ONE_FIVE_TWO}
    ytdlp.vtt = 'WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nsmalltalk about nothing'
    return ytdlp


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    slept: list[float] = []
    monkeypatch.setattr(funnel.time, 'sleep', slept.append)
    return slept


@pytest.fixture
def funnel_ranker(monkeypatch: pytest.MonkeyPatch) -> type[FunnelRanker]:
    monkeypatch.setattr(brain, 'LayaVideoRanker', FunnelRanker)
    return FunnelRanker


def expand(ctx: Ctx, **over: object) -> RunSummary:
    seed(ctx)
    summary = RunSummary()
    yt_run.expand_seeds(ctx, args(max_videos=1, brain='laya', **over), summary)
    return summary


def info_calls(ytdlp: FakeYtDlp) -> list[str]:
    return [c[-1] for c in ytdlp.calls if '-J' in c and '--flat-playlist' not in c]


def chosen_ids(ctx: Ctx) -> list[str]:
    return [v.meta['video_id'] for v in ctx.store.units('youtube', kind='video')]


@pytest.mark.usefixtures('funnel_ranker', 'sleeps')
def test_titles_alone_pick_the_clickbait(ctx: Ctx, deep: FakeYtDlp) -> None:
    ctx.goal = GOAL
    expand(ctx, rank_meta=0, rank_transcripts=0)
    assert chosen_ids(ctx) == [CLICKBAIT]
    assert not info_calls(deep)


@pytest.mark.usefixtures('funnel_ranker', 'sleeps', 'deep')
def test_description_and_captions_promote_the_video_the_title_hid(ctx: Ctx) -> None:
    ctx.goal = GOAL
    expand(ctx, rank_meta=3, rank_transcripts=2)
    assert chosen_ids(ctx) == [HIDDEN]
    record = ctx.store.all_meta()['youtube.ranking'][PLAYLIST]
    top = record['chosen'][0]
    assert (top['laya'], top['meta'], top['transcript']) == (0.3, 0.9, 0.9)
    assert record['funnel']['meta'] == {'asked': 3, 'scored': 3}
    assert record['funnel']['transcripts'] == {'asked': 2, 'scored': 2}
    assert 'throttled' not in record['funnel']
    clickbait = next(r for r in record['skipped'] if r['id'] == CLICKBAIT)
    assert clickbait['meta'] == pytest.approx(0.1)
    assert clickbait['transcript'] == pytest.approx(0.1)


@pytest.mark.usefixtures('funnel_ranker', 'sleeps')
def test_only_the_top_n_are_read_at_each_stage(ctx: Ctx, deep: FakeYtDlp) -> None:
    ctx.goal = GOAL
    expand(ctx, rank_meta=2, rank_transcripts=1)
    sub_calls = [c[-1] for c in deep.calls if '--write-subs' in c]
    assert len(info_calls(deep)) == TWO
    assert len(sub_calls) == 1


@pytest.mark.usefixtures('funnel_ranker', 'sleeps')
def test_chosen_video_is_ingested_from_the_funnels_download_and_the_rest_are_discarded(
    ctx: Ctx, deep: FakeYtDlp
) -> None:
    ctx.goal = GOAL
    seed(ctx)
    summary = yt_run.run(
        ctx, args(max_videos=1, brain='laya', rank_meta=3, rank_transcripts=2)
    )
    assert summary.done == 1
    (unit,) = ctx.store.units('youtube', kind='video')
    assert unit.meta['video_id'] == HIDDEN
    assert 'gradients flow back' in ctx.store.read_markdown(unit.id)
    downloads = info_calls(deep)
    downloads += [c[-1] for c in deep.calls if '--write-subs' in c]
    assert (
        sum(u.endswith(HIDDEN) for u in downloads) == TWO
    )  # once for info, once for captions
    assert not (ctx.ws.dir / yt_run.CACHE_DIR).exists()
    assert all(
        'smalltalk' not in ctx.store.read_markdown(u.id)
        for u in ctx.store.units('youtube', 'done')
    )


@pytest.mark.usefixtures('sleeps')
def test_ingest_reuses_cached_info_and_fetches_only_the_captions(
    ctx: Ctx, ytdlp: FakeYtDlp
) -> None:
    uid = ctx.store.add_unit(
        'youtube', VIDEO_A, kind='video', meta={'video_id': 'aaaaaaaaaaa'}
    )
    cache = ctx.ws.dir / yt_run.CACHE_DIR
    cache.mkdir()
    (cache / 'aaaaaaaaaaa.json').write_text(
        json.dumps({'info': json.loads(fixture('video_info.json')), 'vtt': None})
    )
    yt_run.run(ctx, args())
    assert ctx.store.get(uid).status == 'done'
    assert not info_calls(ytdlp)
    assert any('--write-subs' in c for c in ytdlp.calls)
    assert not (cache / 'aaaaaaaaaaa.json').exists()


@pytest.mark.usefixtures('sleeps')
def test_cached_no_captions_goes_straight_to_needs_asr(
    ctx: Ctx, ytdlp: FakeYtDlp
) -> None:
    uid = ctx.store.add_unit(
        'youtube', VIDEO_A, kind='video', meta={'video_id': 'aaaaaaaaaaa'}
    )
    cache = ctx.ws.dir / yt_run.CACHE_DIR
    cache.mkdir()
    (cache / 'aaaaaaaaaaa.json').write_text(
        json.dumps({'info': json.loads(fixture('video_info.json')), 'vtt': ''})
    )
    yt_run.run(ctx, args())
    assert ctx.store.get(uid).status == 'needs_asr'
    assert not ytdlp.calls


def test_a_hostile_video_id_never_becomes_a_cache_path(ctx: Ctx) -> None:
    assert yt_run.cache_path(ctx, '../../etc/passwd') is None
    assert yt_run.cache_path(ctx, None) is None
    assert yt_run.cache_path(ctx, 'aaaaaaaaaaa') is not None


@pytest.mark.usefixtures('funnel_ranker')
def test_a_throttled_caption_stage_keeps_the_metadata_ranking(
    ctx: Ctx, deep: FakeYtDlp, sleeps: list[float]
) -> None:
    ctx.goal = GOAL
    deep.subs_stderr = (
        "ERROR: Unable to download video subtitles for 'en': HTTP Error 429"
    )
    summary = expand(ctx, rank_meta=3, rank_transcripts=2)
    assert chosen_ids(ctx) == [HIDDEN]  # stage 2 alone already finds it
    record = ctx.store.all_meta()['youtube.ranking'][PLAYLIST]
    assert record['funnel']['throttled'] == 'transcripts'
    assert record['funnel']['transcripts']['scored'] == 0
    assert record['chosen'][0]['transcript'] is None
    assert funnel.BACKOFF_S in sleeps
    events = throttle_events(ctx)
    assert {(e['host'], e['event']) for e in events} == {('youtube.com', '429')}
    assert len(events) == TWO  # the first try and the retry after the back-off
    assert any('stage transcripts throttled' in e for e in summary.errors)


@pytest.mark.usefixtures('funnel_ranker')
def test_a_throttled_metadata_stage_falls_back_to_the_title_ranking(
    ctx: Ctx, deep: FakeYtDlp, sleeps: list[float]
) -> None:
    ctx.goal = GOAL
    deep.info_stderr = 'HTTP Error 429'
    expand(ctx, rank_meta=3, rank_transcripts=0)
    assert chosen_ids(ctx) == [CLICKBAIT]
    record = ctx.store.all_meta()['youtube.ranking'][PLAYLIST]
    assert record['funnel']['throttled'] == 'meta'
    assert funnel.BACKOFF_S in sleeps


@pytest.mark.usefixtures('funnel_ranker')
def test_one_throttle_is_waited_out_and_the_stage_completes(
    ctx: Ctx, deep: FakeYtDlp, sleeps: list[float]
) -> None:
    ctx.goal = GOAL
    deep.info_429_once = True
    expand(ctx, rank_meta=3, rank_transcripts=0)
    record = ctx.store.all_meta()['youtube.ranking'][PLAYLIST]
    assert record['funnel']['meta']['scored'] == THREE
    assert 'throttled' not in record['funnel']
    assert funnel.BACKOFF_S in sleeps
    assert len(throttle_events(ctx)) == 1


@pytest.mark.usefixtures('funnel_ranker', 'deep')
def test_every_yt_dlp_call_of_a_stage_follows_a_pause(
    ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx.goal = GOAL
    seen: list[str] = []
    fake = listing.subprocess.run

    def spy(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        seen.append('call')
        return fake(cmd, **kw)

    monkeypatch.setattr(funnel.time, 'sleep', lambda _s: seen.append('sleep'))
    monkeypatch.setattr(listing.subprocess, 'run', spy)
    expand(ctx, rank_meta=3, rank_transcripts=0)
    stages = seen[seen.index('sleep') :]
    assert stages == ['sleep', 'call'] * (len(stages) // 2)
    assert len(stages) == 2 * THREE


@pytest.mark.usefixtures('sleeps', 'deep')
def test_a_model_failure_in_a_later_stage_keeps_the_title_ranking(
    ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Broken(FunnelRanker):
        def judge(self, evidence: list[str]) -> list[float]:
            raise RuntimeError(f'model gone for {len(evidence)} texts')

    monkeypatch.setattr(brain, 'LayaVideoRanker', Broken)
    ctx.goal = GOAL
    expand(ctx, rank_meta=3, rank_transcripts=2)
    assert chosen_ids(ctx) == [CLICKBAIT]
    record = ctx.store.all_meta()['youtube.ranking'][PLAYLIST]
    assert any('model gone' in e for e in record['funnel']['errors'])


@pytest.mark.usefixtures('funnel_ranker')
def test_a_video_without_captions_gets_no_transcript_score(
    ctx: Ctx, deep: FakeYtDlp, sleeps: list[float]
) -> None:
    ctx.goal = GOAL
    deep.vtts = {}
    deep.vtt = None
    expand(ctx, rank_meta=3, rank_transcripts=3)
    record = ctx.store.all_meta()['youtube.ranking'][PLAYLIST]
    assert all(r['transcript'] is None for r in record['chosen'] + record['skipped'])
    assert record['funnel']['transcripts']['scored'] == 0
    assert 'throttled' not in record['funnel']
    assert sleeps


@pytest.mark.parametrize(
    ('effort', 'given', 'expected'),
    [
        ('quick', {}, (15, 6)),
        ('standard', {}, (30, 12)),
        ('complete', {}, (60, 24)),
        ('standard', {'rank_meta': 20, 'rank_transcripts': 8}, (20, 8)),
        ('standard', {'rank_meta': 0}, (0, 12)),
    ],
)
def test_funnel_sizes_follow_effort_unless_flagged(
    ctx: Ctx, effort: str, given: dict, expected: tuple[int, int]
) -> None:
    ctx.effort = effort
    assert yt_run.funnel_sizes(ctx, args(**given)) == expected


def test_stage_scores_blend_by_weight_and_unjudged_stays_neutral() -> None:
    entries = [{'title': 'x', 'url': 'u'}]
    fun = funnel.Funnel(FunnelRanker(), lambda _t: 0, lambda _e, _w: None, print)
    ev = fun.get(entries[0])
    ev.meta, ev.text = 0.8, 0.2
    _, laya, _ = yt_run.blend(entries, 'zzz', [0.5], fun)
    assert laya[0] == pytest.approx((1 * 0.5 + 2 * 0.8 + 3 * 0.2) / 6)
    _, neutral, _ = yt_run.blend(entries, 'zzz', [None], None)
    assert neutral[0] == yt_run.UNJUDGED_LAYA


# keywords, description text and transcript excerpts


def test_acronyms_and_plurals_in_the_goal_match_titles() -> None:
    hits = yt_run.keyword_hits(
        [
            {'title': 'Never Trust An LLM'},
            {'title': 'Your codebase is NOT ready for AI'},
            {'title': 'Air quality'},
            {'title': 'Cooking'},
        ],
        'AI fundamentals: machine learning and LLMs',
    )
    assert hits == [1, 1, 0, 0]


def test_keywords_also_match_the_description_chapters_and_tags() -> None:
    entry = {
        'title': 'Episode 12',
        'description': 'backpropagation',
        'chapters': [{'title': 'gradient descent'}],
        'tags': ['optimizers'],
    }
    goal = 'gradient descent optimizers backpropagation'
    assert yt_run.keyword_hits([entry], goal) == [4]


def test_description_text_drops_links_and_caps_its_length() -> None:
    info = {
        'description': 'Learn X https://sponsor.example/x ' + 'word ' * 500,
        'chapters': [{'title': f'c{i}'} for i in range(30)],
        'tags': ['a', 'b'],
    }
    text = funnel.describe('T', info)
    assert 'sponsor' not in text
    assert text.startswith('Video title: T\nDescription: Learn X word')
    assert len(text.splitlines()[1]) <= funnel.DESCRIPTION_CHARS + len('Description: ')
    assert text.count('c') <= funnel.CHAPTERS_SHOWN + 3
    assert text.endswith('Tags: a, b')
    assert funnel.describe('T', {}) == 'Video title: T'


def cues(count: int, words: int = 12) -> list[tuple[float, str]]:
    return [
        (float(i * 10), ' '.join(f'w{i}x{j}' for j in range(words))) for i in range(count)
    ]


def test_windows_cover_start_middle_and_the_chapter_that_mentions_the_goal() -> None:
    transcript = cues(200)
    chapters = [
        {'start_time': 0, 'title': 'Intro'},
        {'start_time': 1500, 'title': 'Backpropagation explained'},
    ]
    out = funnel.windows(transcript, chapters, lambda t: int('backprop' in t.lower()))
    assert len(out) == THREE
    assert out[0].startswith('w0x0 ')
    assert out[1].startswith('w100x0 ')
    assert out[2].startswith('w150x0 ')
    assert all(len(w) <= funnel.WINDOW_CHARS + 100 for w in out)


def test_windows_without_a_matching_chapter_use_the_three_quarter_mark() -> None:
    out = funnel.windows(cues(200), [{'start_time': 0, 'title': 'Intro'}], lambda _t: 0)
    assert out[2].startswith('w150x0 ')


def test_a_short_transcript_is_one_window_and_none_is_none() -> None:
    assert len(funnel.windows(cues(3), [], lambda _t: 0)) == 1
    assert funnel.windows([], [], lambda _t: 0) == []
