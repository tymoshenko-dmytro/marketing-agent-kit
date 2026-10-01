#!/usr/bin/env python3
"""
img — CLI for OpenAI image generation (gpt-image-2). Stdlib only.

Usage:
  img.py "a watercolor cat"                        # generate (subcommand inferred)
  img.py generate "a watercolor cat" -o cat.png
  img.py edit "make it nighttime" -i photo.png -o out.png
  img.py edit "fill the masked area with sky" -i photo.png -m mask.png -o out.png

API key: $OPENAI_API_KEY, or OPENAI_API_KEY=... in ~/.config/marketing-agent-kit/.env
(see connections/openai-images-api.md).

Tip: alias it for the terminal —  ln -s "$(pwd)/img.py" ~/.local/bin/img
"""
from __future__ import annotations

import argparse
import base64
import datetime
import json
import mimetypes
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
import uuid

API_BASE = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_QUALITY = "high"
DEFAULT_SIZE = "auto"
DEFAULT_FORMAT = "png"
ENV_FILE = pathlib.Path(os.path.expanduser(
    os.environ.get("MARKETING_KIT_ENV", "~/.config/marketing-agent-kit/.env")))
TIMEOUT_SECONDS = 600


def load_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            k, _, v = line.strip().partition("=")
            v = re.split(r"(?:^|\s)#", v.strip(), maxsplit=1)[0].strip().strip('"').strip("'")   # same rule as kit.py
            if k.strip() == "OPENAI_API_KEY" and v:
                return v
    sys.exit(
        "error: no OpenAI API key found.\n"
        f"  set $OPENAI_API_KEY, or add OPENAI_API_KEY=... to {ENV_FILE} (chmod 600).\n"
        "  Setup: connections/openai-images-api.md"
    )


def default_output(fmt: str) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"img-{ts}.{fmt}"


def build_multipart(fields, files):
    boundary = uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        if value is None:
            continue
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        body += str(value).encode() + b"\r\n"
    for name, path in files:
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        body += f"--{boundary}\r\n".encode()
        body += (
            f'Content-Disposition: form-data; name="{name}"; '
            f'filename="{path.name}"\r\n'
        ).encode()
        body += f"Content-Type: {mime}\r\n\r\n".encode()
        body += path.read_bytes() + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def http_post(url, headers, data):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        sys.exit(f"error: HTTP {e.code} from OpenAI:\n{body}")
    except urllib.error.URLError as e:
        sys.exit(f"error: network: {e.reason}")


def save_images(data, output, count):
    base = pathlib.Path(output)
    base.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, item in enumerate(data):
        if count == 1:
            path = base
        else:
            path = base.with_stem(f"{base.stem}-{i + 1}")
        b64 = item.get("b64_json")
        if not b64:
            sys.exit(f"error: response item {i} has no b64_json: {item}")
        path.write_bytes(base64.b64decode(b64))
        paths.append(str(path))
    return paths


def common_payload(args):
    p = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "n": args.count,
        "output_format": args.format,
    }
    if args.background:
        p["background"] = args.background
    if args.moderation:
        p["moderation"] = args.moderation
    if args.compression is not None and args.format in ("jpeg", "webp"):
        p["output_compression"] = args.compression
    return p


def cmd_generate(args, key):
    payload = common_payload(args)
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    print(
        f"→ generate ({args.quality}, {args.size}, {args.format}, n={args.count}) …",
        file=sys.stderr,
    )
    resp = http_post(
        f"{API_BASE}/images/generations", headers, json.dumps(payload).encode()
    )
    output = args.output or default_output(args.format)
    for p in save_images(resp["data"], output, args.count):
        print(p)


def cmd_edit(args, key):
    images = [pathlib.Path(p) for p in args.images]
    for p in images:
        if not p.exists():
            sys.exit(f"error: image not found: {p}")
    mask_path = pathlib.Path(args.mask) if args.mask else None
    if mask_path and not mask_path.exists():
        sys.exit(f"error: mask not found: {mask_path}")

    fields = {k: v for k, v in common_payload(args).items() if k != "prompt"}
    fields["prompt"] = args.prompt
    fields["n"] = str(args.count)
    if "output_compression" in fields:
        fields["output_compression"] = str(fields["output_compression"])

    files = []
    if len(images) == 1:
        files.append(("image", images[0]))
    else:
        for p in images:
            files.append(("image[]", p))
    if mask_path:
        files.append(("mask", mask_path))

    body, content_type = build_multipart(fields, files)
    headers = {"Authorization": f"Bearer {key}", "Content-Type": content_type}
    print(
        f"→ edit {len(images)} image(s) ({args.quality}, {args.size}) …",
        file=sys.stderr,
    )
    resp = http_post(f"{API_BASE}/images/edits", headers, body)
    output = args.output or default_output(args.format)
    for p in save_images(resp["data"], output, args.count):
        print(p)


def add_common(p):
    p.add_argument("-o", "--output", help="output path (default: img-<timestamp>.<format>)")
    p.add_argument(
        "-s", "--size", default=DEFAULT_SIZE,
        help="auto | 1024x1024 | 1536x1024 | 1024x1536 | ... (default: auto)",
    )
    p.add_argument(
        "-q", "--quality", default=DEFAULT_QUALITY,
        choices=["low", "medium", "high", "auto", "xhigh", "max"],
        help=f"low | medium | high | auto; xhigh | max on GPT Image 2.5 models (default: {DEFAULT_QUALITY})",
    )
    p.add_argument(
        "-f", "--format", default=DEFAULT_FORMAT,
        choices=["png", "jpeg", "webp"],
        help=f"png | jpeg | webp (default: {DEFAULT_FORMAT})",
    )
    p.add_argument("-n", "--count", type=int, default=1, help="number of images")
    p.add_argument("--background", choices=["opaque", "transparent", "auto"],
                   help="background mode; transparent: GPT Image 2.5 models only, png/webp")
    p.add_argument("--compression", type=int, help="0-100 for jpeg/webp")
    p.add_argument("--moderation", choices=["low", "auto"], help="moderation strictness")
    p.add_argument("--model", default=os.environ.get("IMG_MODEL", DEFAULT_MODEL),
                   help=f"model (default: $IMG_MODEL or {DEFAULT_MODEL})")


def main():
    argv = sys.argv[1:]
    if argv and argv[0] not in ("generate", "edit", "-h", "--help"):
        argv = ["generate"] + argv

    parser = argparse.ArgumentParser(
        prog="img.py",
        description="OpenAI image generation CLI (gpt-image-2).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="generate image from a text prompt")
    g.add_argument("prompt", help="text prompt")
    add_common(g)

    e = sub.add_parser("edit", help="edit one or more images with a prompt")
    e.add_argument("prompt", help="text prompt describing the edit")
    e.add_argument(
        "-i", "--image", action="append", required=True, dest="images",
        metavar="PATH", help="input image (repeat -i for multiple)",
    )
    e.add_argument("-m", "--mask", help="mask PNG (alpha channel = area to edit)")
    add_common(e)

    args = parser.parse_args(argv)
    key = load_api_key()
    if args.cmd == "generate":
        cmd_generate(args, key)
    else:
        cmd_edit(args, key)


if __name__ == "__main__":
    main()
