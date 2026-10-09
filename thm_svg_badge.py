#!/usr/bin/env python3
"""Generate TryHackMe profile badges as SVG and PNG, plus the profile avatar."""

import argparse
import asyncio
import base64
import json
import sys
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import urlencode

from playwright.async_api import async_playwright
from pyfiglet import figlet_format
from termcolor import colored


PROFILE_ENDPOINT = "https://tryhackme.com/api/v2/public-profile"


def paint(message, color, attrs=None):
    """Apply terminal colors, keeping all decoration in one place."""
    return colored(message, color, attrs=attrs or [])


def print_banner():
    """Show the project banner and author credit."""
    try:
        banner = figlet_format("THM SVG BADGE", font="slant")
    except Exception:
        banner = "THM SVG BADGE\n"

    print(paint(banner, "red", ["bold"]))
    print(paint("Made By Aryan Giri | giriaryan694-a11y", "cyan", ["bold"]))
    print(paint("TryHackMe profile badge generator\n", "yellow"))


def text(value):
    """Escape dynamic text so it is safe inside SVG/XML."""
    return escape(str(value), quote=True)


def format_number(value, default=0):
    """Format numeric profile fields with thousands separators when possible."""
    if value is None:
        value = default
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError, OverflowError):
        return str(value)


async def fetch_profile_and_avatar(username):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                viewport={"width": 1280, "height": 900}
            )
            page = await context.new_page()

            # Visit the main site first, then request the JSON endpoint in the
            # same browser context, matching the original script's behavior.
            await page.goto(
                "https://tryhackme.com/",
                wait_until="domcontentloaded",
                timeout=60000,
            )

            profile_url = f"{PROFILE_ENDPOINT}?{urlencode({'username': username})}"
            response = await page.goto(
                profile_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            if response is None:
                raise RuntimeError("The profile request did not return a response.")

            body = await response.text()
            if not response.ok:
                raise RuntimeError(
                    f"Profile request failed with HTTP {response.status}:\n"
                    f"{body[:300]}"
                )

            try:
                payload = json.loads(body)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "The endpoint did not return JSON. It may have returned a "
                    "block page or challenge instead."
                ) from exc

            if (
                not isinstance(payload, dict)
                or payload.get("status") != "success"
                or not isinstance(payload.get("data"), dict)
            ):
                raise RuntimeError(f"Unexpected API response: {str(payload)[:300]}")

            profile = payload["data"]
            avatar_data_uri = ""
            avatar_url = profile.get("avatar")

            # Embed the avatar into the SVG so the badge does not depend on a
            # remote image at viewing time.
            if avatar_url:
                avatar_response = await context.request.get(
                    avatar_url,
                    timeout=30000,
                )
                if avatar_response.ok:
                    content_type = (
                        avatar_response.headers.get("content-type", "")
                        .split(";")[0]
                        .strip()
                        .lower()
                    )
                    allowed_types = {
                        "image/png",
                        "image/jpeg",
                        "image/webp",
                        "image/gif",
                    }

                    if content_type in allowed_types:
                        raw_image = await avatar_response.body()
                        encoded_image = base64.b64encode(raw_image).decode("ascii")
                        avatar_data_uri = f"data:{content_type};base64,{encoded_image}"

            return profile, avatar_data_uri
        finally:
            await browser.close()


def make_svg(profile, avatar_data_uri):
    username = text(profile.get("username") or "TryHackMe user")
    level = text(profile.get("level") if profile.get("level") is not None else "—")
    points = text(format_number(profile.get("totalPoints", 0)))
    rooms = text(format_number(profile.get("completedRoomsNumber", 0)))
    badges = text(format_number(profile.get("badgesNumber", 0)))
    rank = text(format_number(profile.get("rank", 0)))

    top_percentage = profile.get("topPercentage")
    top = text(f"{top_percentage}%" if top_percentage is not None else "—")

    avatar_href = text(avatar_data_uri)
    if avatar_data_uri:
        avatar_markup = f"""
          <image x="37" y="40" width="108" height="108"
                 preserveAspectRatio="xMidYMid slice"
                 href="{avatar_href}" xlink:href="{avatar_href}"
                 clip-path="url(#avatarClip)"/>
        """
    else:
        avatar_markup = """
          <circle cx="91" cy="94" r="54" fill="#292929"/>
          <text x="91" y="101" text-anchor="middle" fill="#ffffff"
                font-family="Arial, sans-serif" font-size="24"
                font-weight="bold">THM</text>
        """

    template = Template("""\
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="760" height="190" viewBox="0 0 760 190" role="img"
     aria-label="TryHackMe badge for $username">
  <defs>
    <clipPath id="avatarClip">
      <circle cx="91" cy="94" r="54"/>
    </clipPath>
  </defs>

  <rect x="1" y="1" width="758" height="188" rx="8"
        fill="#151515" stroke="#444444" stroke-width="2"/>
  <rect x="1" y="1" width="8" height="188" rx="4" fill="#c92332"/>

  <text x="25" y="27" fill="#c92332" font-family="Arial, sans-serif"
        font-size="13" font-weight="bold" letter-spacing="1.5">TRYHACKME</text>

  <circle cx="91" cy="94" r="56" fill="#c92332"/>
  $avatar

  <text x="170" y="68" fill="#ffffff" font-family="Arial, sans-serif"
        font-size="24" font-weight="bold">$username</text>
  <text x="171" y="94" fill="#bbbbbb" font-family="Arial, sans-serif"
        font-size="14">LEVEL $level</text>

  <path d="M170 111H735" stroke="#444444" stroke-width="1"/>

  <g font-family="Arial, sans-serif">
    <text x="171" y="143" fill="#ffffff" font-size="17"
          font-weight="bold">$points</text>
    <text x="171" y="162" fill="#999999" font-size="10"
          letter-spacing="0.7">POINTS</text>

    <text x="284" y="143" fill="#ffffff" font-size="17"
          font-weight="bold">#$rank</text>
    <text x="284" y="162" fill="#999999" font-size="10"
          letter-spacing="0.7">GLOBAL RANK</text>

    <text x="415" y="143" fill="#ffffff" font-size="17"
          font-weight="bold">$rooms</text>
    <text x="415" y="162" fill="#999999" font-size="10"
          letter-spacing="0.7">ROOMS</text>

    <text x="515" y="143" fill="#ffffff" font-size="17"
          font-weight="bold">$badges</text>
    <text x="515" y="162" fill="#999999" font-size="10"
          letter-spacing="0.7">BADGES</text>

    <text x="635" y="143" fill="#ffffff" font-size="17"
          font-weight="bold">TOP $top</text>
    <text x="635" y="162" fill="#999999" font-size="10"
          letter-spacing="0.7">PERCENTILE</text>
  </g>
</svg>
""")

    return template.substitute(
        username=username,
        level=level,
        points=points,
        rank=rank,
        rooms=rooms,
        badges=badges,
        top=top,
        avatar=avatar_markup,
    )


async def render_svg_to_png(svg, png_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(
                viewport={"width": 760, "height": 240},
                device_scale_factor=2,
            )
            await page.set_content(
                f"""<!doctype html>
                <html>
                  <head>
                    <style>
                      html, body {{ margin: 0; padding: 0; width: 760px; height: 240px; }}
                    </style>
                  </head>
                  <body>{svg}</body>
                </html>""",
                wait_until="load",
            )
            await page.locator("svg").screenshot(path=str(png_path))
        finally:
            await browser.close()


def ask_username():
    while True:
        username = input(paint("TryHackMe username: ", "yellow", ["bold"])).strip()
        if username:
            return username
        print(paint("Username cannot be blank. Try again.\n", "red"))


async def main():
    parser = argparse.ArgumentParser(
        description="Create a TryHackMe SVG badge, PNG badge, and profile image."
    )
    parser.add_argument(
        "-u",
        "--username",
        help="TryHackMe public username (prompted if omitted).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="thm_badge.svg",
        help="SVG filename (default: thm_badge.svg).",
    )
    parser.add_argument(
        "-d",
        "--output-dir",
        default=None,
        help="Directory for generated files (prompted if omitted; blank uses current directory).",
    )
    args = parser.parse_args()

    print_banner()

    try:
        username = (args.username or "").strip() or ask_username()

        if args.output_dir is None:
            output_dir_text = input(
                paint("Output directory [Enter = current directory]: ", "yellow", ["bold"])
            ).strip()
        else:
            output_dir_text = args.output_dir.strip()

        output_dir = Path(output_dir_text).expanduser() if output_dir_text else Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        output_name = (args.output or "thm_badge.svg").strip() or "thm_badge.svg"
        svg_path = output_dir / output_name
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        png_path = svg_path.with_suffix(".png")

        print(paint(f"\n[+] Fetching TryHackMe profile: {username}", "cyan", ["bold"]))
        profile, avatar_data_uri = await fetch_profile_and_avatar(username)
        svg = make_svg(profile, avatar_data_uri)

        svg_path.write_text(svg, encoding="utf-8")
        await render_svg_to_png(svg, png_path)

        if avatar_data_uri.startswith("data:image/") and "," in avatar_data_uri:
            header, encoded = avatar_data_uri.split(",", 1)
            mime_type = header.split(";", 1)[0].removeprefix("data:")
            extension = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp",
                "image/gif": ".gif",
            }.get(mime_type, ".img")

            photo_path = svg_path.parent / f"profile_pic{extension}"
            photo_path.write_bytes(base64.b64decode(encoded))
            print(paint(f"[+] Saved profile photo: {photo_path}", "green"))
        else:
            print(paint("[!] No supported profile photo was available to save.", "yellow"))

        print(paint(f"[+] Saved SVG: {svg_path}", "green", ["bold"]))
        print(paint(f"[+] Saved PNG: {png_path}", "green", ["bold"]))
        print(paint("\nDone. Happy hacking! 🎯", "cyan", ["bold"]))

    except KeyboardInterrupt:
        print(paint("\n[!] Cancelled by user.", "yellow"), file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(paint(f"\n[ERROR] {exc}", "red", ["bold"]), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    asyncio.run(main())
