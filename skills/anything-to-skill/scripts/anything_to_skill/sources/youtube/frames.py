import importlib.util
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from anything_to_skill.sources.youtube.listing import YtDlpError, ytdlp

_CUE_PHRASE = re.compile(
    r'as you can see|this slide|on (?:the )?screen|this diagram|the diagram|'
    r'this code|the code here|look at this|here we have',
    re.IGNORECASE,
)
MIN_GAP_S = 10
MAX_FRAMES = 24
FFMPEG_TIMEOUT_S = 60
PHASH_DISTANCE = 5
_STEM = re.compile(r'-(\d+)$')


def frame_timestamps(
    chapters: list[dict],
    cues: list[tuple[float, str]],
    cap: int = MAX_FRAMES,
) -> list[float]:
    """Chapter starts first (they mark topic changes), then cue phrases, spaced apart."""
    wanted = [c['start_time'] + 1 for c in chapters]
    wanted += [at + 1 for at, line in cues if _CUE_PHRASE.search(line)]
    picked: list[float] = []
    for ts in wanted:
        if len(picked) < cap and all(abs(ts - p) >= MIN_GAP_S for p in picked):
            picked.append(ts)
    return sorted(picked)


def seconds_of(path: Path) -> int:
    """Frames are named <prefix>-<seconds>.png; this reads the timestamp back."""
    return int(_STEM.search(path.stem).group(1))  # type: ignore[union-attr]


def _phash(path: Path) -> Any:
    import imagehash  # noqa: PLC0415  # pyright: ignore[reportMissingImports]
    from PIL import Image  # noqa: PLC0415  # pyright: ignore[reportMissingImports]

    with Image.open(path) as img:
        return imagehash.phash(img)


def dedupe(paths: list[Path], hash_fn: Callable[[Path], Any] = _phash) -> list[Path]:
    """Drop stills whose perceptual hash is within PHASH_DISTANCE of one already kept."""
    kept: list[tuple[Path, object]] = []
    for path in paths:
        digest = hash_fn(path)
        if any(digest - other <= PHASH_DISTANCE for _, other in kept):
            path.unlink()
        else:
            kept.append((path, digest))
    return [p for p, _ in kept]


def extract_frames(
    url: str, timestamps: list[float], out_dir: Path, prefix: str = 'frame'
) -> list[Path]:
    """Low-res download plus ffmpeg stills at timestamps, near-duplicates removed by pHash."""
    if not shutil.which('ffmpeg'):
        raise YtDlpError('ffmpeg is required for --frames but was not found on PATH')
    if not (importlib.util.find_spec('imagehash') and importlib.util.find_spec('PIL')):
        raise YtDlpError(
            '--frames needs pillow and imagehash: run through ingest_youtube.py'
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    stills: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        ytdlp(
            [
                '--no-playlist',
                '-f',
                'bv[height<=480]/b[height<=480]/w',
                '-o',
                str(Path(tmp) / 'video.%(ext)s'),
            ],
            url,
            timeout=1800,
        )
        video = next(Path(tmp).glob('video.*'))
        for ts in sorted(timestamps):
            still = out_dir / f'{prefix}-{int(ts):05d}.png'
            try:
                done = subprocess.run(
                    [
                        'ffmpeg',
                        '-loglevel',
                        'error',
                        '-y',
                        '-ss',
                        str(ts),
                        '-i',
                        str(video),
                        '-frames:v',
                        '1',
                        str(still),
                    ],
                    capture_output=True,
                    check=False,
                    timeout=FFMPEG_TIMEOUT_S,
                )
            except subprocess.TimeoutExpired:  # a corrupt download can hang ffmpeg
                continue
            if done.returncode == 0 and still.exists():
                stills.append(still)
    return dedupe(stills)
