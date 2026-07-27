---
name: nanobanana
description: "Generates and edits images by calling Google's Nano Banana / Gemini image generation API (requires a GEMINI_API_KEY), a real, billed API call. This skill is explicit-invocation only: use it only when the user names it or the Gemini path directly (\"nanobanana\", \"nano banana\", \"gemini image generation\", \"GEMINI_API_KEY\", \"use nanobanana to …\") or wants to integrate the Nano Banana / Gemini image API into their own codebase. For any implicit or general image-generation request (\"generate an image\", \"create a logo/hero/mascot\"), the default generator is codex-imagegen, not this skill. Not a design/mockup critique tool (use review-design) and not a browser-driven screenshot flow (use agent-browser)."
metadata:
  author: mgiovani
  version: 1.1.0
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# Nanobanana: Nano Banana Image Generation

Generate and edit images using Google's Nano Banana (Gemini image generation API). This skill handles direct image generation, iterative editing, and expert guidance for integrating the API into codebases.

**Core differentiator**: A prompt enhancement system that analyzes user intent and project context to craft optimized prompts before calling the API.

This is the explicit Gemini/Nano Banana path (named directly by the user): for a generic "generate an image" request with no engine named, codex-imagegen is the default generator instead.

---

## Phase 0: Environment Check

Before anything else, verify the environment is ready.

**1. Check API key:**
```bash
echo "${GEMINI_API_KEY:0:10}..."  # Show first 10 chars only (security)
```

If `GEMINI_API_KEY` is empty or unset:
- Read `references/integration-guide.md` (the setup section)
- Present setup instructions to the user
- **Stop here** until the key is configured

**2. Check `uv` is available:**
```bash
uv --version 2>&1
```

If `uv` is not installed, direct the user to https://docs.astral.sh/uv/getting-started/installation/ and stop. `uv` handles dependency installation automatically via PEP 723 inline metadata: no manual `pip install` needed.

---

## Phase 1: Understand Intent & Detect Mode

### Mine the conversation for:
- **Subject/scene**: What is the image of?
- **Purpose**: What is it for? (hero image, icon, mockup, blog post, etc.)
- **Style**: Photorealistic, illustration, minimalist, etc.
- **Technical requirements**: Aspect ratio, resolution, specific dimensions
- **Mood/atmosphere**: Energetic, calm, professional, playful, etc.

### Detect Mode

**Expert Integration Mode**: if the user wants to integrate Nano Banana into their codebase (e.g., "how do I add image generation to my app", "show me the API", "I'm building a feature that generates images"):
- Read `references/integration-guide.md`
- Provide SDK examples, authentication patterns, and production best practices
- **Skip to guidance, do not call the API**

**Generation Mode**: if the user wants an image generated now:
- Continue to Phase 2

### Analyze Project Context (Generation Mode Only)

If invoked within a project directory, gather context to improve prompts:

```bash
# Identify project type
ls package.json pyproject.toml README.md 2>/dev/null | head -5
```

```bash
# Find project description
head -20 README.md 2>/dev/null || head -20 pyproject.toml 2>/dev/null
```

```bash
# Find existing images (identify style conventions)
find . -name "*.png" -o -name "*.jpg" -o -name "*.svg" 2>/dev/null | grep -v node_modules | head -10
```

```bash
# Find color schemes (Tailwind, CSS variables, theme files)
grep -r "primary\|brand\|#[0-9a-fA-F]\{6\}" --include="*.css" --include="*.ts" --include="*.json" -l 2>/dev/null | head -5
```

Use this context to make the generated image fit the project's visual language.

### Classify Request Type

Choose the most fitting category:
- `photorealistic`: scenes, portraits, product photos, landscapes
- `stylized`: illustrations, art, cartoon, concept art
- `text-heavy`: posters, banners, infographics with text
- `product-marketing`: commercial product shots
- `ui-mockup`: app screens, website designs, wireframes
- `diagram`: technical illustrations, flowcharts, architecture
- `minimalist`: abstract, logos, icon concepts

### Ask Only for Missing Info

Only ask for information the conversation did not already provide. If the user said "a minimalist logo for my SaaS app", you already know: subject (logo), style (minimalist), purpose (SaaS branding). Don't ask for things you already know.

---

## Phase 2: Enhance Prompt

Read the relevant section from `references/prompt-engineering.md` based on the request category.

### Enhancement Process

Apply category-specific enhancements:

| Category | Add to Prompt |
|---|---|
| `photorealistic` | Camera angle, lens type, lighting setup, depth of field, atmosphere |
| `stylized` | Art style, quality level, shading approach, color palette reference |
| `text-heavy` | Exact text in quotes, font style, weight, color, placement |
| `product-marketing` | Studio lighting setup, surface material, background type |
| `ui-mockup` | Device frame, design language, project colors if known |
| `diagram` | Diagram type, color coding scheme, label style, clean lines |
| `minimalist` | Background color (exact), element positioning, size proportions |

Incorporate any project context found in Phase 1 (brand colors, design system, domain).

### Present Enhanced Prompt for Approval: Scale to Intent

Two paths, chosen by what the user actually asked for:

**Full review block**: use for final/production assets: explicit "final", "production-ready", "for the website/app", hero images, logos, or anything incorporating brand/project context from Phase 1. Getting these wrong costs real API spend and rework, so confirm before spending it:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 PROMPT REVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORIGINAL: [user's original prompt]

ENHANCED: [improved prompt with additions]

CHANGES:
  + [what was added]
  + [why it was added]

MODEL:    [Selected model name]
ASPECT:   [e.g., 16:9]
RESOLUTION: [e.g., 2K]
EST. COST: ~$[estimate]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proceed with enhanced prompt? (yes / modify / use original)
```

If the user wants modifications, update the enhanced prompt and show the review block again before proceeding.

**One-line summary**: use for drafts/exploration: "quick draft", "just try something", "rough concept", "let's iterate", or any low-stakes/throwaway request. State the enhanced prompt, model, and aspect ratio in one line and proceed straight to Phase 4, don't make the user click through ceremony for a $0.02 draft image.

When intent is ambiguous, default to the full review block on the *first* generation in a session; once the user has approved the pattern once, later iterations in the same session can use the one-line summary.

---

## Phase 3: Select Model & Parameters

**Default**: Nano Banana 2 (`gemini-3.1-flash-image-preview`) at 2K resolution.

> Model IDs and prices below are point-in-time. If the script returns `INVALID_MODEL`, don't guess a replacement: check https://ai.google.dev/pricing for current model IDs first.

See `references/model-guide.md` for full details. Quick reference:

| Use Case | Model | Resolution |
|---|---|---|
| Quick drafts / iteration | `gemini-2.5-flash-image` | 512 or 1K |
| **Most production assets (DEFAULT)** | `gemini-3.1-flash-image-preview` | 2K |
| Text-heavy images | `gemini-3-pro-image-preview` | 2K–4K |
| Print / high-DPI | `gemini-3-pro-image-preview` | 4K |

**Aspect ratio defaults by use case:**
- Hero/banner: `16:9`
- Profile/avatar: `1:1`
- Stories/mobile: `9:16`
- Portrait/pin: `2:3`
- Standard web: `4:3`

Always present the model and resolution choice to the user as part of the Phase 2 review block and allow them to override.

---

## Phase 4: Generate Image

Determine the output path (default to `./generated-image.png` if not specified, or a contextually appropriate name like `./hero-image.png` or `./logo-concept.png`).

### Text-to-Image
```bash
uv run "$(dirname "$0")/scripts/generate.py" \
  --prompt "ENHANCED_PROMPT_HERE" \
  --model "MODEL_ID_HERE" \
  --aspect-ratio "ASPECT_RATIO_HERE" \
  --resolution "RESOLUTION_HERE" \
  --output "OUTPUT_PATH_HERE"
```

### Image Editing (when user provides an existing image)
```bash
uv run "$(dirname "$0")/scripts/generate.py" \
  --prompt "EDIT_INSTRUCTION_HERE" \
  --input-image "INPUT_IMAGE_PATH_HERE" \
  --model "MODEL_ID_HERE" \
  --aspect-ratio "ASPECT_RATIO_HERE" \
  --resolution "RESOLUTION_HERE" \
  --output "OUTPUT_PATH_HERE"
```

### Parse the JSON Output

The script outputs a JSON object. Parse and handle each case:

**Success:**
```json
{"status": "success", "output_path": "/abs/path/image.png", "model_used": "...", "text_response": "...", "size_bytes": 245760}
```
→ Report the file path. Use `Read` on image files if the platform supports inline display.

**Error cases:**

| `error_code` | Meaning | Action |
|---|---|---|
| `CONTENT_POLICY` | Prompt blocked by safety filters | Suggest rephrasing; remove sensitive elements |
| `RATE_LIMIT` | API quota exceeded | Wait before retrying; suggest lower-cost model |
| `AUTH_ERROR` | Invalid or missing API key | Direct user to `references/integration-guide.md` setup section |
| `NO_IMAGE_GENERATED` | Model returned no image | Try rephrasing prompt; try different model |
| `DEPENDENCY_ERROR` | `google-genai` not installed | Ensure `uv` is available; `uv run` handles deps automatically via PEP 723 metadata |
| `FILE_NOT_FOUND` | Input image path invalid | Verify the path and re-run |
| `INVALID_MODEL` | `--model` value not recognized | Check https://ai.google.dev/pricing for current model IDs, don't fabricate one |
| `TIMEOUT` | Request took too long | Retry, or drop to a lower resolution |
| `API_ERROR` | Unclassified API failure | Report the raw error message to the user; don't retry silently more than the script already does |

---

## Phase 5: Iterate (Optional)

After a successful generation, offer iteration options based on user feedback:

**Minor tweaks** (color, brightness, small compositional changes):
→ Use **image editing mode**: pass the previous output as `--input-image`

**Major changes** (completely different subject, style change):
→ Modify the enhanced prompt and **regenerate** from scratch

**Rapid exploration** (testing multiple concepts):
→ Use `gemini-2.5-flash-image` at `512` resolution for all iterations
→ Identify the winning concept, then regenerate with `gemini-3.1-flash-image-preview` at `2K`

**For iterative editing sessions**, keep track of the prompt evolution so the user can revert to a previous version if needed.

---

## Expert Integration Mode

When the user wants to add image generation to their codebase:

1. Read `references/integration-guide.md`
2. Identify the user's tech stack (Python, JavaScript/TypeScript, REST API needed)
3. Provide the relevant SDK example from the guide
4. Tailor the example to their project structure:
   - Python FastAPI/Flask → show as an endpoint
   - Next.js → show as an API route
   - Plain script → show standalone function
5. Highlight critical production concerns from the guide:
   - Never expose API key in frontend
   - Implement rate limiting per user
   - Cache by prompt hash
   - Handle 429 with exponential backoff
6. Suggest environment variable setup appropriate for their project type

---

## Reference Files

- `references/prompt-engineering.md`: Photography terms, style guides, sparse→rich examples by category
- `references/model-guide.md`: Model comparison, pricing, rate limits, resolution options
- `references/integration-guide.md`: SDK examples (Python/JS/REST), setup, production best practices
- `scripts/generate.py`: Core API caller with retry logic and JSON output
- `scripts/requirements.txt`: `google-genai>=1.0.0`
