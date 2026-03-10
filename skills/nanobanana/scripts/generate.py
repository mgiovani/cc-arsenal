#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "google-genai>=1.0.0",
# ]
# ///
"""
Nano Banana Image Generator
Calls the Google Gemini image generation API and saves the result to disk.
Outputs structured JSON to stdout for programmatic parsing by AI agents.

Usage:
    uv run generate.py --prompt "A red apple" --output ./apple.png
    uv run generate.py --prompt "Make it blue" \
        --input-image ./apple.png --output ./blue-apple.png
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

VALID_MODELS = {
    'nano-banana': 'gemini-2.5-flash-image',
    'nano-banana-2': 'gemini-3.1-flash-image-preview',
    'nano-banana-pro': 'gemini-3-pro-image-preview',
    # Also accept raw model IDs
    'gemini-2.5-flash-image': 'gemini-2.5-flash-image',
    'gemini-3.1-flash-image-preview': 'gemini-3.1-flash-image-preview',
    'gemini-3-pro-image-preview': 'gemini-3-pro-image-preview',
}

DEFAULT_MODEL = 'gemini-3.1-flash-image-preview'

VALID_ASPECT_RATIOS = [
    '1:1',
    '2:3',
    '3:2',
    '4:3',
    '3:4',
    '4:5',
    '5:4',
    '9:16',
    '16:9',
]

VALID_RESOLUTIONS = ['512', '1K', '2K', '4K']

RESOLUTION_MAP = {
    '512': 'IMAGE_SIZE_512',
    '1K': 'IMAGE_SIZE_1024',
    '2K': 'IMAGE_SIZE_2048',
    '4K': 'IMAGE_SIZE_4096',
}


def output_json(data: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(data) + '\n')
    sys.stdout.flush()


def output_error(message: str, error_code: str = 'UNKNOWN_ERROR') -> None:
    output_json({'status': 'error', 'error_message': message, 'error_code': error_code})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Generate or edit images using Nano Banana (Gemini image generation)'
    )
    parser.add_argument(
        '--prompt', required=True, help='Text prompt describing the image to generate'
    )
    parser.add_argument(
        '--model',
        default=DEFAULT_MODEL,
        help=f'Model to use. Options: {", ".join(VALID_MODELS)}. Default: {DEFAULT_MODEL}',
    )
    parser.add_argument(
        '--aspect-ratio',
        default='1:1',
        choices=VALID_ASPECT_RATIOS,
        help='Aspect ratio of the generated image. Default: 1:1',
    )
    parser.add_argument(
        '--resolution',
        default='2K',
        choices=VALID_RESOLUTIONS,
        help='Resolution of the generated image. Default: 2K',
    )
    parser.add_argument(
        '--output', required=True, help='Output file path for the generated image (PNG)'
    )
    parser.add_argument(
        '--input-image',
        default=None,
        help='Path to an existing image for editing mode (optional)',
    )
    parser.add_argument(
        '--thinking',
        action='store_true',
        help='Enable extended thinking/reasoning mode (slower, higher quality)',
    )
    return parser.parse_args()


def validate_environment() -> str:
    """Check GEMINI_API_KEY is set and return it."""
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()
    if not api_key:
        output_error(
            'GEMINI_API_KEY environment variable is not set. '
            'Get a key at https://aistudio.google.com/apikey and set: '
            "export GEMINI_API_KEY='your-key-here'",
            'AUTH_ERROR',
        )
        sys.exit(1)
    return api_key


def resolve_model(model_arg: str) -> str:
    """Resolve friendly model name to actual model ID."""
    resolved = VALID_MODELS.get(model_arg)
    if not resolved:
        output_error(
            f"Unknown model: '{model_arg}'. Valid options: {', '.join(VALID_MODELS)}",
            'INVALID_MODEL',
        )
        sys.exit(1)
    return resolved


def load_input_image(image_path: str) -> tuple[bytes, str]:
    """Load an input image for editing mode. Returns (image_bytes, mime_type)."""
    path = Path(image_path)
    if not path.exists():
        output_error(f'Input image not found: {image_path}', 'FILE_NOT_FOUND')
        sys.exit(1)

    mime_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
    }
    mime_type = mime_map.get(path.suffix.lower(), 'image/png')
    return path.read_bytes(), mime_type


def build_contents(prompt: str, input_image_path: str | None) -> list[types.Content]:
    """Build the contents list for the API call."""
    parts: list[types.Part] = []

    if input_image_path:
        image_bytes, mime_type = load_input_image(input_image_path)
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

    parts.append(types.Part.from_text(text=prompt))
    return [types.Content(role='user', parts=parts)]


def build_config(
    aspect_ratio: str, resolution: str, thinking: bool
) -> types.GenerateContentConfig:
    """Build the GenerateContentConfig for the API call."""
    image_size = RESOLUTION_MAP.get(resolution, 'IMAGE_SIZE_2048')
    image_config = types.ImageConfig(
        aspect_ratio=aspect_ratio,
        image_size=image_size,
    )
    config_kwargs: dict[str, Any] = {
        'response_modalities': ['TEXT', 'IMAGE'],
        'image_config': image_config,
    }
    if thinking:
        config_kwargs['thinking_config'] = types.ThinkingConfig(thinking_budget=8192)

    return types.GenerateContentConfig(**config_kwargs)


def call_api_with_retry(
    client: genai.Client,
    model_id: str,
    contents: list[types.Content],
    config: types.GenerateContentConfig,
    max_retries: int = 3,
) -> object:
    """Call the API with exponential backoff for rate limit errors."""
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model_id,
                contents=contents,
                config=config,
            )
        except Exception as e:  # noqa: BLE001
            error_str = str(e).lower()
            last_error = e

            if '429' in str(e) or 'rate' in error_str or 'quota' in error_str:
                if attempt < max_retries - 1:
                    time.sleep((2**attempt) * 2)  # 2s, 4s, 8s
                    continue
                output_error(
                    f'Rate limit exceeded after {max_retries} attempts. '
                    'Wait a moment before trying again or upgrade your API plan.',
                    'RATE_LIMIT',
                )
                sys.exit(1)

            elif '400' in str(e) and any(
                w in error_str for w in ('safety', 'policy', 'blocked')
            ):
                output_error(
                    'Image generation was blocked by content policy. '
                    'Try rephrasing the prompt to remove potentially sensitive content.',
                    'CONTENT_POLICY',
                )
                sys.exit(1)

            elif (
                '401' in str(e)
                or '403' in str(e)
                or any(w in error_str for w in ('api key', 'authentication'))
            ):
                output_error(
                    f'Authentication failed: {e}. '
                    'Verify your GEMINI_API_KEY is valid at https://aistudio.google.com/apikey',
                    'AUTH_ERROR',
                )
                sys.exit(1)

            elif 'timeout' in error_str:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                output_error(
                    'Request timed out. Try again or use a lower resolution.', 'TIMEOUT'
                )
                sys.exit(1)

            else:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                output_error(f'API call failed: {e}', 'API_ERROR')
                sys.exit(1)

    output_error(f'All {max_retries} attempts failed: {last_error}', 'API_ERROR')
    sys.exit(1)


def extract_image_and_text(response: object) -> tuple[bytes | None, str]:
    """Extract image bytes and any text from the API response."""
    image_bytes = None
    text_parts: list[str] = []

    if not response.candidates:
        return None, ''

    for candidate in response.candidates:
        if not candidate.content or not candidate.content.parts:
            continue
        for part in candidate.content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                raw = part.inline_data.data
                # Some SDK versions return base64 strings
                image_bytes = base64.b64decode(raw) if isinstance(raw, str) else raw
            elif hasattr(part, 'text') and part.text:
                text_parts.append(part.text)

    return image_bytes, ' '.join(text_parts)


def save_image(image_bytes: bytes, output_path: str) -> Path:
    """Save image bytes to disk, creating parent directories as needed."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image_bytes)
    return path


def main() -> None:
    args = parse_args()
    api_key = validate_environment()
    model_id = resolve_model(args.model)

    client = genai.Client(api_key=api_key)
    contents = build_contents(args.prompt, args.input_image)
    config = build_config(args.aspect_ratio, args.resolution, args.thinking)
    response = call_api_with_retry(client, model_id, contents, config)
    image_bytes, text_response = extract_image_and_text(response)

    if image_bytes is None:
        block_reason = ''
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            block_reason = str(response.prompt_feedback)
        msg = (
            'No image was generated. The model may have blocked the request. '
            f'{block_reason}'
        )
        output_error(msg.strip(), 'NO_IMAGE_GENERATED')
        sys.exit(1)

    saved_path = save_image(image_bytes, args.output)
    output_json(
        {
            'status': 'success',
            'output_path': str(saved_path.resolve()),
            'model_used': model_id,
            'text_response': text_response,
            'size_bytes': len(image_bytes),
            'aspect_ratio': args.aspect_ratio,
            'resolution': args.resolution,
        }
    )


if __name__ == '__main__':
    main()
