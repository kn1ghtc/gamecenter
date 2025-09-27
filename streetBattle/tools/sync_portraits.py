#!/usr/bin/env python3
"""Synchronise remote and fallback portraits for StreetBattle.

This utility refreshes ``assets/portrait_sources.json`` with up-to-date remote
artwork URLs sourced from the public SNK KOF XV and KOF XIV websites while also
provisioning deterministic procedural fallback palettes for all 43 characters.

It can optionally download the remote artwork into the local cache and invoke
``download_portraits.py`` to regenerate the procedural backups.
"""
from __future__ import annotations

import argparse
import colorsys
import json
import logging
import random
import re
import textwrap
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import requests

try:  # Local generator is reused for fallback production
    from . import download_portraits
except ImportError:  # pragma: no cover - module executed as script
    import download_portraits  # type: ignore

LOGGER = logging.getLogger("streetbattle.sync_portraits")

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
MANIFEST_PATH = ASSETS_DIR / "portrait_sources.json"
COMPREHENSIVE_PATH = ASSETS_DIR / "comprehensive_kof_characters.json"
PORTRAIT_DIR = ASSETS_DIR / "images" / "portraits"

HEADERS = {
    "User-Agent": "StreetBattlePortraitSync/1.0 (https://github.com/kn1ghtc)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
TIMEOUT = 20

PATTERNS = ["flames", "fan", "crescent", "star", "diagonal"]
REMOTE_LICENSE = "SNK official promotional artwork (for research preview only)"
REMOTE_NOTES = (
    "Remote artwork is downloaded on-demand from the official SNK websites."
    " For characters without official renders, StreetBattle falls back to the"
    " procedural portrait generator."
)


def canonical(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def hsv_to_hex(h: float, s: float, v: float) -> str:
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def generate_palette(identifier: str) -> Dict[str, str | List[str]]:
    rng = random.Random(identifier)
    base_hue = rng.random()
    palette: List[str] = []
    for idx in range(4):
        hue = (base_hue + 0.19 * idx + rng.uniform(-0.04, 0.04)) % 1.0
        saturation = 0.55 + rng.random() * 0.35
        value = 0.58 + rng.random() * 0.32
        palette.append(hsv_to_hex(hue, saturation, value))

    accent = palette[-1]
    secondary = palette[0]
    silhouette = palette[min(1, len(palette) - 1)]

    accent_h = (base_hue + 0.47) % 1.0
    emblem_color = hsv_to_hex(accent_h, 0.6 + 0.3 * rng.random(), 0.75 + 0.2 * rng.random())

    pattern = PATTERNS[rng.randrange(len(PATTERNS))]

    return {
        "palette": palette,
        "accent_color": accent,
        "secondary_color": secondary,
        "silhouette_color": silhouette,
        "emblem_color": emblem_color,
        "pattern": pattern,
        "emblem_size": 204 + rng.randrange(-20, 21),
    }


def fetch_kof15_mapping(session: requests.Session) -> Dict[str, Dict[str, str]]:
    url = "https://www.snk-corp.co.jp/us/games/kof-xv/characters/"
    LOGGER.debug("Fetching KOF XV roster page %s", url)
    resp = session.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    slugs: List[str] = []
    for chunk in resp.text.split("characters_")[1:]:
        slug = chunk.split(".php")[0]
        if slug and slug not in slugs:
            slugs.append(slug)

    mapping: Dict[str, Dict[str, str]] = {}
    for slug in slugs:
        detail = f"{url}characters_{slug}.php"
        try:
            page = session.get(detail, headers=HEADERS, timeout=TIMEOUT)
            page.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network
            LOGGER.warning("Failed to fetch %s: %s", detail, exc)
            continue
        title_match = re.search(r"<title>([^<]+)</title>", page.text)
        if not title_match:
            continue
        name = title_match.group(1).split("|")[0].strip()
        name = name.replace("B.JENET", "B. JENET").replace("KIM", "KIM KAPHWAN")

        webp_match = re.search(r"img/(character_[a-z0-9_\-]+\.webp)", page.text, flags=re.IGNORECASE)
        png_match = re.search(r"img/(character_[a-z0-9_\-]+\.png)", page.text, flags=re.IGNORECASE)
        img_path = (webp_match or png_match)
        if not img_path:
            LOGGER.debug("No portrait image found for %s", detail)
            continue
        img_url = f"{url}{img_path.group(0)}"

        mapping[canonical(name)] = {
            "display": name,
            "url": img_url,
            "source": "SNK Official — THE KING OF FIGHTERS XV",
        }
    return mapping


def fetch_kof14_mapping(session: requests.Session) -> Dict[str, Dict[str, str]]:
    index_url = "https://www.snk-corp.co.jp/us/games/kof-xiv/teams/"
    LOGGER.debug("Fetching KOF XIV team index %s", index_url)
    resp = session.get(index_url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()

    team_slugs = {
        match.lower()
        for match in re.findall(r"/us/games/kof-xiv/teams/([a-z0-9_-]+)\.php", resp.text, flags=re.IGNORECASE)
    }

    character_slugs: set[str] = set()
    for slug in sorted(team_slugs):
        team_url = f"{index_url}{slug}.php"
        try:
            page = session.get(team_url, headers=HEADERS, timeout=TIMEOUT)
            page.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover
            LOGGER.warning("Failed to fetch %s: %s", team_url, exc)
            continue
        slugs = re.findall(r"/us/games/kof-xiv/characters/([a-z0-9_-]+)\.php", page.text, flags=re.IGNORECASE)
        character_slugs.update(slug.lower() for slug in slugs)

    mapping: Dict[str, Dict[str, str]] = {}
    base_char_url = "https://www.snk-corp.co.jp/us/games/kof-xiv/characters/"
    for slug in sorted(character_slugs):
        detail_url = f"{base_char_url}{slug}.php"
        try:
            detail = session.get(detail_url, headers=HEADERS, timeout=TIMEOUT)
            detail.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover
            LOGGER.debug("Failed to fetch KOF XIV character page %s: %s", detail_url, exc)
            continue

        title_match = re.search(r"<title>([^<]+)</title>", detail.text)
        if not title_match:
            continue
        title = title_match.group(1)
        name = title.split("|")[0].strip()
        if not name:
            continue

        img_match = re.search(r"characters/img/(charaimg_[a-z0-9_\-]+\.(?:png|jpg))", detail.text, flags=re.IGNORECASE)
        if not img_match:
            continue
        img_rel = img_match.group(1)
        img_url = f"{base_char_url}img/{img_rel}"

        mapping[canonical(name)] = {
            "display": name,
            "url": img_url,
            "source": "SNK Official — THE KING OF FIGHTERS XIV",
        }
    return mapping


def load_roster() -> List[Dict[str, str]]:
    data = json.loads(COMPREHENSIVE_PATH.read_text(encoding="utf-8"))
    return data["characters"]


def build_manifest(session: requests.Session) -> Dict[str, Dict[str, object]]:
    roster = load_roster()
    kof15 = fetch_kof15_mapping(session)
    kof14 = fetch_kof14_mapping(session)

    manifest: Dict[str, Dict[str, object]] = {}
    for entry in roster:
        char_id = entry["id"]
        name = entry["name"]
        key = canonical(name)

        remote_meta: Optional[Dict[str, str]] = kof15.get(key) or kof14.get(key)
        palette_info = generate_palette(char_id)
        emblem_text = "".join(part[0] for part in name.split() if part)[:2].upper()

        manifest[char_id] = {
            "display_name": name,
            "urls": [remote_meta["url"]] if remote_meta else [],
            "remote_source": remote_meta["source"] if remote_meta else "",
            "license": REMOTE_LICENSE,
            "notes": REMOTE_NOTES if remote_meta else "Remote artwork unavailable; procedural fallback only.",
            "palette": palette_info["palette"],
            "accent_color": palette_info["accent_color"],
            "secondary_color": palette_info["secondary_color"],
            "silhouette_color": palette_info["silhouette_color"],
            "emblem_color": palette_info["emblem_color"],
            "emblem_text": emblem_text,
            "emblem_size": palette_info["emblem_size"],
            "pattern": palette_info["pattern"],
        }

    return manifest


def write_manifest(manifest: Dict[str, Dict[str, object]]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    LOGGER.info("Wrote portrait manifest to %s", MANIFEST_PATH)


def download_remote_assets(session: requests.Session, manifest: Dict[str, Dict[str, object]], overwrite: bool = False, limit: Optional[Iterable[str]] = None) -> None:
    PORTRAIT_DIR.mkdir(parents=True, exist_ok=True)
    targets = set(limit) if limit else None
    for char_id, spec in manifest.items():
        if targets and char_id not in targets:
            continue
        urls = spec.get("urls", [])
        if not urls:
            LOGGER.debug("Skipping %s — no remote URLs", char_id)
            continue
        destination = PORTRAIT_DIR / f"{char_id}_official.png"
        if destination.exists() and not overwrite:
            LOGGER.debug("%s already exists; skip", destination.name)
            continue
        for url in urls:
            try:
                LOGGER.info("Downloading %s from %s", char_id, url)
                resp = session.get(url, headers=HEADERS, timeout=TIMEOUT)
                resp.raise_for_status()
                destination.write_bytes(resp.content)
                break
            except requests.RequestException as exc:
                LOGGER.warning("Failed to download %s: %s", url, exc)
        else:
            LOGGER.error("All remote URLs failed for %s", char_id)


def generate_fallbacks(manifest: Dict[str, Dict[str, object]], overwrite: bool = False, limit: Optional[Iterable[str]] = None) -> None:
    PORTRAIT_DIR.mkdir(parents=True, exist_ok=True)
    targets = set(limit) if limit else None
    for char_id, spec in manifest.items():
        if targets and char_id not in targets:
            continue
        palette = spec.get("palette")
        if not palette:
            LOGGER.warning("%s missing palette specification; skipping fallback", char_id)
            continue
        portrait_path = PORTRAIT_DIR / f"{char_id}_fallback.png"
        if portrait_path.exists() and not overwrite:
            LOGGER.debug("%s already exists; skip", portrait_path.name)
            continue
        portrait_spec = {
            "palette": spec["palette"],
            "accent_color": spec["accent_color"],
            "secondary_color": spec["secondary_color"],
            "silhouette_color": spec["silhouette_color"],
            "emblem_text": spec.get("emblem_text", ""),
            "emblem_color": spec.get("emblem_color", spec["accent_color"]),
            "emblem_size": spec.get("emblem_size"),
            "pattern": spec.get("pattern", "diagonal"),
            "display_name": spec.get("display_name", char_id.replace("_", " ").title()),
        }
        download_portraits.generate_portrait(char_id, portrait_spec, portrait_path, overwrite=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronise StreetBattle portrait assets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              python tools/sync_portraits.py --write-manifest
              python tools/sync_portraits.py --download --generate-fallbacks
              python tools/sync_portraits.py --download --limit kyo_kusanagi iori_yagami
            """
        ),
    )
    parser.add_argument("--write-manifest", action="store_true", help="Regenerate portrait_sources.json")
    parser.add_argument("--download", action="store_true", help="Download remote portraits into the cache")
    parser.add_argument("--generate-fallbacks", action="store_true", help="Regenerate procedural fallback portraits")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files when downloading/generating")
    parser.add_argument("--limit", nargs="*", help="Restrict operations to specific character IDs")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


def main() -> None:  # pragma: no cover - CLI entry point
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(levelname)s] %(message)s",
        force=True,
    )

    session = requests.Session()
    manifest = build_manifest(session)

    if args.write_manifest or not MANIFEST_PATH.exists():
        write_manifest(manifest)
    else:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    if args.download:
        download_remote_assets(session, manifest, overwrite=args.overwrite, limit=args.limit)

    if args.generate_fallbacks:
        generate_fallbacks(manifest, overwrite=args.overwrite, limit=args.limit)


if __name__ == "__main__":  # pragma: no cover - script execution
    main()
