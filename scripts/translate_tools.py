#!/usr/bin/env python
"""Auto-translate tool names and descriptions for i18n support.

Uses free translation APIs with local caching to avoid repeated requests.
Supports multiple translation backends:
- Lingva (Google Translate proxy, no API key needed)
- MyMemory (1000 requests/day free)
- LibreTranslate (self-hosted option)

Usage:
    python scripts/translate_tools.py [config.yaml]
    python scripts/translate_tools.py --dry-run  # Preview without saving
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import requests
import yaml

# Cache file for translations
CACHE_FILE = Path(__file__).parent / "translation_cache.json"

# Translation API endpoints (free options)
APIS = {
    "lingva": "https://lingva.ml/api/v1/{source}/{target}/{text}",
    "mymemory": "https://api.mymemory.translated.net/get?q={text}&langpair={source}|{target}",
}


def load_cache() -> dict[str, str]:
    """Load translation cache from file."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict[str, str]) -> None:
    """Save translation cache to file."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def translate_text(
    text: str,
    source: str = "en",
    target: str = "zh",
    api: str = "mymemory",
) -> str:
    """Translate text using free translation API.

    Args:
        text: Text to translate
        source: Source language code
        target: Target language code
        api: API to use (lingva, mymemory)

    Returns:
        Translated text
    """
    if not text or not text.strip():
        return text

    # Check cache first
    cache = load_cache()
    cache_key = f"{source}:{target}:{text}"
    if cache_key in cache:
        return cache[cache_key]

    try:
        if api == "mymemory":
            url = APIS["mymemory"].format(text=text, source=source, target=target)
            response = requests.get(url, timeout=10)
            if response.ok:
                data = response.json()
                translation = data.get("responseData", {}).get("translatedText", text)
                if translation and translation != text:
                    cache[cache_key] = translation
                    save_cache(cache)
                    return translation

        elif api == "lingva":
            # URL encode the text
            import urllib.parse
            encoded_text = urllib.parse.quote(text)
            url = APIS["lingva"].format(source=source, target=target, text=encoded_text)
            response = requests.get(url, timeout=10)
            if response.ok:
                data = response.json()
                translation = data.get("translation", text)
                if translation and translation != text:
                    cache[cache_key] = translation
                    save_cache(cache)
                    return translation

    except Exception as e:
        print(f"  ⚠️  Translation failed for '{text[:30]}...': {e}")

    return text


def translate_yaml_config(
    config_path: Path,
    target_lang: str = "zh",
    dry_run: bool = False,
) -> dict[str, int]:
    """Add translations to YAML config file.

    Args:
        config_path: Path to YAML config file
        target_lang: Target language code (default: zh)
        dry_run: If True, don't save changes

    Returns:
        Stats dict with counts of translated items
    """
    print(f"\n📂 Loading {config_path}...")

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    stats = {"shelves": 0, "buttons": 0, "descriptions": 0, "skipped": 0}
    name_key = f"name_{target_lang}"
    desc_key = f"description_{target_lang}"

    for shelf in config.get("shelves", []):
        shelf_name = shelf.get("name", "")

        # Translate shelf name
        if name_key not in shelf and shelf_name:
            print(f"\n📁 Shelf: {shelf_name}")
            translation = translate_text(shelf_name, target=target_lang)
            if translation != shelf_name:
                shelf[name_key] = translation
                print(f"   → {translation}")
                stats["shelves"] += 1
            time.sleep(0.5)  # Rate limiting
        else:
            stats["skipped"] += 1

        # Translate buttons
        for button in shelf.get("buttons", []):
            btn_name = button.get("name", "")
            btn_desc = button.get("description", "")

            # Translate button name
            if name_key not in button and btn_name:
                translation = translate_text(btn_name, target=target_lang)
                if translation != btn_name:
                    button[name_key] = translation
                    print(f"   🔧 {btn_name} → {translation}")
                    stats["buttons"] += 1
                time.sleep(0.3)

            # Translate description
            if desc_key not in button and btn_desc:
                translation = translate_text(btn_desc, target=target_lang)
                if translation != btn_desc:
                    button[desc_key] = translation
                    stats["descriptions"] += 1
                time.sleep(0.3)

    # Save updated config
    if not dry_run:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print(f"\n✅ Saved to {config_path}")
    else:
        print("\n🔍 Dry run - no changes saved")

    return stats


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Auto-translate tool configurations")
    parser.add_argument(
        "config",
        nargs="?",
        default="examples/shelf_config.yaml",
        help="Path to YAML config file",
    )
    parser.add_argument(
        "--target",
        "-t",
        default="zh",
        help="Target language code (default: zh)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Preview changes without saving",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return

    print("=" * 60)
    print("🌐 Tool Translation Script")
    print("=" * 60)
    print(f"Config: {config_path}")
    print(f"Target: {args.target}")
    print(f"Mode:   {'Dry run' if args.dry_run else 'Live'}")

    stats = translate_yaml_config(config_path, args.target, args.dry_run)

    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"  Shelves translated:     {stats['shelves']}")
    print(f"  Buttons translated:     {stats['buttons']}")
    print(f"  Descriptions translated: {stats['descriptions']}")
    print(f"  Already translated:     {stats['skipped']}")


if __name__ == "__main__":
    main()

