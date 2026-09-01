# Nano Banana Model Guide

> Reference for model selection, resolution options, pricing, and rate limits.

## Model Comparison

| Model | ID | Speed | Quality | Price/Image | Best For |
|---|---|---|---|---|---|
| Nano Banana | `gemini-2.5-flash-image` | Fast | Good | ~$0.039 | Quick drafts, iteration |
| Nano Banana 2 | `gemini-3.1-flash-image-preview` | Medium | Great | ~$0.045 to $0.151 | Most production assets |
| Nano Banana Pro | `gemini-3-pro-image-preview` | Slow | Excellent | ~$0.134 to $0.240 | Text-heavy, print, final assets |

### Nano Banana (`gemini-2.5-flash-image`)
- **Strengths**: Lowest latency, cheapest, good for rapid iteration
- **Best for**: Quick concept validation, bulk generation, thumbnails, icons
- **Limitations**: Lower quality ceiling, weaker text rendering, basic detail

### Nano Banana 2 (`gemini-3.1-flash-image-preview`): DEFAULT
- **Strengths**: Best balance of quality and cost, supports extended aspect ratios
- **Best for**: Web hero images, social media posts, blog graphics, app screenshots
- **Limitations**: Not as fast as NB, not as detailed as NB Pro for complex scenes

### Nano Banana Pro (`gemini-3-pro-image-preview`)
- **Strengths**: Highest quality, superior text rendering, finest detail, best for print
- **Best for**: Text-heavy images (posters, banners, infographics), branding, print materials, high-DPI
- **Limitations**: Slowest, most expensive: reserve for final production assets

## Resolution Options

| Resolution | Pixels | Use Cases |
|---|---|---|
| `512` | ~512px | Icons, favicons, quick previews, thumbnails |
| `1K` | ~1024px | Social media thumbnails, web graphics, small illustrations |
| `2K` | ~2048px | Web hero images, blog posts, standard production assets |
| `4K` | ~4096px | Print materials, high-DPI displays, zoom-in-ready assets |

**Notes:**
- Higher resolutions cost more and take longer
- For iteration, use 512 or 1K to test concept, then upscale winning prompt to 2K+
- 4K recommended with Pro model for best quality

## Aspect Ratios

### Standard (All Models)
| Ratio | Common Use |
|---|---|
| `1:1` | Social media posts (Instagram), profile pictures, app icons |
| `16:9` | Widescreen hero images, YouTube thumbnails, presentations |
| `9:16` | Instagram/TikTok stories, mobile wallpapers |
| `4:3` | Blog post images, presentations, traditional print |
| `3:4` | Portrait photos, Pinterest pins, book covers |
| `2:3` | Portrait photography, posters |
| `3:2` | Landscape photography, wide web banners |
| `4:5` | Instagram feed posts (optimal crop) |

### Extended (Nano Banana 2 Only)
- Ultra-wide panoramics and non-standard ratios
- Useful for website backgrounds and email headers

## Pricing Estimates

| Model | 512 | 1K | 2K | 4K |
|---|---|---|---|---|
| Nano Banana | ~$0.020 | ~$0.039 | n/a | n/a |
| Nano Banana 2 | ~$0.025 | ~$0.045 | ~$0.090 | ~$0.151 |
| Nano Banana Pro | ~$0.067 | ~$0.100 | ~$0.134 | ~$0.240 |

> Prices are approximate. Check https://ai.google.dev/pricing for current rates.

## Rate Limits

| Tier | Requests/Minute | Requests/Day |
|---|---|---|
| Free | 10 | 1,000 |
| Pay-as-you-go | 60–120 | Unlimited |
| Enterprise | Custom | Custom |

**Handling Rate Limits:**
- The `generate.py` script automatically retries on 429 errors with exponential backoff (3 attempts)
- For bulk generation, add delays between requests or use lower-cost models
- Free tier is sufficient for personal projects and exploration

## Model Selection Decision Tree

```
Need text in the image?
  → YES: Use Nano Banana Pro (gemini-3-pro-image-preview)

Need print quality or 4K?
  → YES: Use Nano Banana Pro

Just testing/iterating?
  → YES: Use Nano Banana (gemini-2.5-flash-image) at 512px

Most other cases:
  → Use Nano Banana 2 (gemini-3.1-flash-image-preview) at 2K [DEFAULT]
```
