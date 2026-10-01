# OpenAI Images API

**What it gives you:** image generation and editing (inpainting, multi-image composition) with GPT Image models.
**Used by:** `image-gen`
**Access:** API key (`OPENAI_API_KEY`).
**Cost:** pay per image. At 1024×1024 with `gpt-image-2`: ~$0.006 (low), ~$0.053 (medium), ~$0.211 (high). Landscape 1536×1024 is slightly cheaper. Batch API: half price.
**Setup time:** ~5 minutes

## 1. Get a key

1. <https://platform.openai.com/api-keys> → Create new secret key. A project key with a budget is best for agents.
2. Add a payment method / credits (Billing).
3. Keys file: `OPENAI_API_KEY=...` (`kit.py open`).

New organisations **may need API Organization Verification** before GPT Image models work (Settings → Organization → General). If the first call returns a verification error, that's why.

## 2. Connect

Nothing else: the skill's `scripts/img.py` calls `POST /v1/images/generations` and `POST /v1/images/edits` directly. There is no official OpenAI image MCP server.

For the terminal, link the CLI once: `ln -s "$(pwd)/skills/image-gen/scripts/img.py" ~/.local/bin/img`.

## 3. Check

```bash
python3 skills/connect/scripts/kit.py doctor --live       # OPENAI_API_KEY · accepted
python3 skills/image-gen/scripts/img.py "a red circle on white" -q low -s 1024x1024 -o test.png
```

## Models

| Model | Notes |
|---|---|
| `gpt-image-2` | the kit's default; OpenAI now lists it as an earlier model |
| `gpt-image-2.5-flare` | recommended for new work, fast; adds `xhigh` and `max` quality; transparent backgrounds work (tested) |
| `gpt-image-2.5-sunburst` | recommended for editing |

Same per-token prices. Switch with `--model` or `IMG_MODEL=...`; test on a draft first.

## Safety

- Set a monthly budget on the project the key belongs to.
- Draft at `-q low`, render finals at `-q high` — quality is a ~35× price difference.

## Gotchas

- **Transparent backgrounds:** `gpt-image-2` returned HTTP 400 "not supported for this model" in a test on 2026-10-01, although the API reference lists it as a preview. `gpt-image-2.5-flare` produced a real transparent PNG in the same test: `--model gpt-image-2.5-flare --background transparent -f png`.
- Sizes: edges in multiples of 16, up to 3840 px, aspect ratio up to 3:1; above 2560×1440 is experimental. Complex prompts can take up to 2 minutes.
- The lowest usage tier is limited to ~5 images a minute; parallel batches will hit 429s.
- Masks need an alpha channel and the same size as the input image.
- Responses are base64 only (`b64_json`); the script writes the files.

## Links

- Guide: <https://developers.openai.com/api/docs/guides/image-generation>
- Model: <https://developers.openai.com/api/docs/models/gpt-image-2> · Pricing: <https://developers.openai.com/api/docs/pricing>

*Checked 2026-10-01.*
