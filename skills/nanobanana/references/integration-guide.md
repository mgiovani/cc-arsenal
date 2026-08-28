# Nano Banana integration guide

> SDK examples, API setup, authentication patterns, and best practices for integrating Nano Banana into codebases.

## API key setup

### Get your key
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click **Create API key** (or use an existing Gemini key)
3. The same key works for all Nano Banana models

### Set environment variable

**Linux/macOS:**
```bash
export GEMINI_API_KEY="your-key-here"

# Add to shell profile for persistence:
echo 'export GEMINI_API_KEY="your-key-here"' >> ~/.zshrc
# or
echo 'export GEMINI_API_KEY="your-key-here"' >> ~/.bashrc
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY = "your-key-here"
# For persistence:
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your-key-here", "User")
```

**Docker:**
```dockerfile
ENV GEMINI_API_KEY=your-key-here
# Or pass at runtime:
docker run -e GEMINI_API_KEY=your-key-here myapp
```

**Vercel/Netlify:**
Add `GEMINI_API_KEY` in the project's environment variables settings in the dashboard.

### Verify setup
```bash
python -c "
from google import genai
import os
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
print('Setup OK')
"
```

---

## Python SDK examples

### Install
```bash
uv add google-genai
```

For standalone scripts, use PEP 723 inline metadata instead: `uv run` handles installation automatically with no separate install step:
```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["google-genai>=1.0.0"]
# ///
```
```bash
uv run my_script.py  # deps installed automatically in isolated env
```

### Basic text-to-Image
```python
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents="A photorealistic red apple on a white background, studio lighting",
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_generation_config=types.ImageGenerationConfig(
            aspect_ratio="1:1",
            image_size="IMAGE_SIZE_2048",
        ),
    ),
)

# Extract image from response
for part in response.candidates[0].content.parts:
    if part.inline_data:
        with open("output.png", "wb") as f:
            f.write(part.inline_data.data)
        print("Image saved to output.png")
    elif part.text:
        print("Model says:", part.text)
```

### Image editing mode
```python
import os
from pathlib import Path
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Load existing image
image_bytes = Path("existing-image.png").read_bytes()

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        types.Content(role="user", parts=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            types.Part.from_text(text="Change the background to a forest scene"),
        ])
    ],
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
    ),
)

for part in response.candidates[0].content.parts:
    if part.inline_data:
        Path("edited-image.png").write_bytes(part.inline_data.data)
```

### Multi-Turn conversation (Iterative editing)
```python
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Use a chat session for iterative editing
chat = client.chats.create(
    model="gemini-3.1-flash-image-preview",
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
    ),
)

# First generation
response = chat.send_message("A minimalist logo with the letter A")
# Extract and save image...

# Refine in the same session
response = chat.send_message("Make it more bold and add a blue color scheme")
# Extract updated image...
```

### With reference images (Style transfer)
```python
import os
from pathlib import Path
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

style_image = Path("style-reference.png").read_bytes()

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        types.Content(role="user", parts=[
            types.Part.from_bytes(data=style_image, mime_type="image/png"),
            types.Part.from_text(text="Generate a hero image for a tech startup website in this same style"),
        ])
    ],
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_generation_config=types.ImageGenerationConfig(
            aspect_ratio="16:9",
            image_size="IMAGE_SIZE_2048",
        ),
    ),
)
```

---

## JavaScript/TypeScript SDK examples

### Install
```bash
npm install @google/genai
# or
bun add @google/genai
```

### Basic text-to-Image
```typescript
import { GoogleGenAI } from "@google/genai";
import fs from "fs";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

const response = await ai.models.generateContent({
  model: "gemini-3.1-flash-image-preview",
  contents: "A photorealistic red apple on a white background",
  config: {
    responseModalities: ["TEXT", "IMAGE"],
    imageGenerationConfig: {
      aspectRatio: "1:1",
      imageSize: "IMAGE_SIZE_2048",
    },
  },
});

for (const part of response.candidates?.[0]?.content?.parts ?? []) {
  if (part.inlineData) {
    const imageData = Buffer.from(part.inlineData.data!, "base64");
    fs.writeFileSync("output.png", imageData);
    console.log("Image saved to output.png");
  } else if (part.text) {
    console.log("Model says:", part.text);
  }
}
```

### Next.js API route
```typescript
// app/api/generate-image/route.ts
import { GoogleGenAI } from "@google/genai";
import { NextRequest, NextResponse } from "next/server";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY! });

export async function POST(request: NextRequest) {
  const { prompt, aspectRatio = "16:9" } = await request.json();

  if (!prompt) {
    return NextResponse.json({ error: "Prompt is required" }, { status: 400 });
  }

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3.1-flash-image-preview",
      contents: prompt,
      config: {
        responseModalities: ["TEXT", "IMAGE"],
        imageGenerationConfig: { aspectRatio },
      },
    });

    for (const part of response.candidates?.[0]?.content?.parts ?? []) {
      if (part.inlineData) {
        return NextResponse.json({
          imageBase64: part.inlineData.data,
          mimeType: part.inlineData.mimeType,
        });
      }
    }

    return NextResponse.json({ error: "No image generated" }, { status: 500 });
  } catch (error: any) {
    if (error.status === 429) {
      return NextResponse.json({ error: "Rate limit exceeded" }, { status: 429 });
    }
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
```

---

## REST/cURL examples

```bash
# Text-to-image via REST API
curl -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [{"text": "A red apple on a white background"}]
    }],
    "generationConfig": {
      "responseModalities": ["TEXT", "IMAGE"],
      "imageGenerationConfig": {
        "aspectRatio": "1:1",
        "imageSize": "IMAGE_SIZE_2048"
      }
    }
  }'
```

---

## Error handling patterns

```python
import time
from google.api_core import exceptions

def generate_with_retry(client, prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=prompt,
                config=...,
            )
        except exceptions.ResourceExhausted:
            # 429 rate limit
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt * 2)
                continue
            raise
        except exceptions.InvalidArgument as e:
            # 400 bad request — often content policy
            if "safety" in str(e).lower():
                raise ValueError("Content blocked by safety policy") from e
            raise
        except exceptions.PermissionDenied:
            # 403 invalid API key
            raise ValueError("Invalid API key") from None
```

---

## Production best practices

### Rate limiting
- Implement token bucket or sliding window rate limiting in your application
- Cache generated images aggressively (same prompt + params = same image)
- Use a queue for bulk generation to avoid burst 429s

### Cost optimization
- Generate at low resolution (512/1K) for iteration, upscale with Pro only for finals
- Cache images by prompt hash, avoid regenerating identical prompts
- Use Nano Banana (flash) for automated/bulk tasks, Pro only for client-facing finals

### Security
- Never expose your API key in frontend JavaScript, always route through a backend API
- Validate and sanitize user prompts before sending to the API
- Implement your own content moderation layer for user-generated prompts
- Rate limit per user, not just globally

### Storage
- Store generated images in object storage (S3, GCS, Cloudflare R2) not on disk
- Use a CDN for serving generated images to end users
- Consider storing the prompt + parameters alongside the image for reproducibility

### Error handling
- Always handle 429 (rate limit) with exponential backoff
- Surface content policy blocks clearly to users with actionable guidance
- Log failed generations with prompt (sanitized) for debugging
- Implement a fallback strategy (e.g., stock images) for API outages

### Environment variables
```bash
# .env.example
GEMINI_API_KEY=           # Required: Your Google AI Studio API key
GEMINI_DEFAULT_MODEL=gemini-3.1-flash-image-preview  # Optional: Override default model
GEMINI_MAX_RETRIES=3      # Optional: Number of retry attempts
GEMINI_TIMEOUT=60         # Optional: Request timeout in seconds
```
