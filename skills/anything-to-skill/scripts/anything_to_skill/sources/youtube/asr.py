import platform
import sys
from pathlib import Path

from anything_to_skill.sources.youtube.listing import YtDlpError, ytdlp

MLX_MODEL = 'mlx-community/whisper-small-mlx'
FASTER_MODEL = 'small'


def fetch_audio(url: str, workdir: Path) -> Path:
    ytdlp(
        [
            '--no-playlist',
            '-f',
            'bestaudio/best',
            '-o',
            str(workdir / 'audio.%(ext)s'),
        ],
        url,
        timeout=1800,
    )
    found = sorted(workdir.glob('audio.*'))
    if not found:
        raise YtDlpError('yt-dlp produced no audio file')
    return found[0]


def transcribe(audio: Path, model: str | None = None) -> list[tuple[float, str]]:
    """(start_seconds, text) segments via mlx-whisper on Apple silicon, else faster-whisper."""
    if sys.platform == 'darwin' and platform.machine() == 'arm64':
        import mlx_whisper  # noqa: PLC0415  # pyright: ignore[reportMissingImports]

        result = mlx_whisper.transcribe(str(audio), path_or_hf_repo=model or MLX_MODEL)
        pairs = [(float(s['start']), s['text']) for s in result['segments']]
    else:
        import faster_whisper  # noqa: PLC0415  # pyright: ignore[reportMissingImports]

        whisper = faster_whisper.WhisperModel(model or FASTER_MODEL, compute_type='int8')
        segments, _ = whisper.transcribe(str(audio), vad_filter=True)
        pairs = [(float(s.start), s.text) for s in segments]
    return [(start, text.strip()) for start, text in pairs if text.strip()]
