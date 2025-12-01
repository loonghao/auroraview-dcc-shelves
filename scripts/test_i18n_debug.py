#!/usr/bin/env python
"""i18n automated testing using Playwright.

This script provides real automated testing for i18n functionality:
- Headless browser automation
- Real DOM interaction and verification
- JavaScript execution with return values
- Language switching tests
- Translation verification

Usage:
    just test-i18n          # Run all i18n tests
    just test-i18n-zh       # Test switching to Chinese
    just test-i18n-en       # Test switching to English

Requirements:
    pip install playwright
    playwright install chromium
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

try:
    from playwright.sync_api import sync_playwright, Page
except ImportError:
    print("❌ Playwright not installed. Run:")
    print("   pip install playwright")
    print("   playwright install chromium")
    sys.exit(1)


class I18nTester:
    """i18n tester using Playwright for real browser automation."""

    def __init__(self, page: Page):
        self.page = page
        self.passed = 0
        self.failed = 0

    def _log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        if passed:
            self.passed += 1
            print(f"  ✅ {test_name}")
        else:
            self.failed += 1
            print(f"  ❌ {test_name}")
        if details:
            print(f"      {details}")

    def get_i18n_state(self) -> dict[str, Any]:
        """Get current i18n state from the page."""
        return self.page.evaluate("""() => {
            if (typeof i18next === 'undefined') {
                return { error: 'i18next not found' };
            }
            return {
                language: i18next.language,
                resolvedLanguage: i18next.resolvedLanguage,
                languages: i18next.languages,
                isInitialized: i18next.isInitialized,
                cached: localStorage.getItem('i18nextLng')
            };
        }""")

    def get_translations(self, keys: list[str]) -> dict[str, str]:
        """Get translation values for specified keys."""
        return self.page.evaluate("""(keys) => {
            if (typeof i18next === 'undefined') {
                return { error: 'i18next not found' };
            }
            const result = {};
            for (const key of keys) {
                result[key] = i18next.t(key);
            }
            return result;
        }""", keys)

    def switch_language(self, lang: str) -> dict[str, Any]:
        """Switch to specified language and return new state."""
        return self.page.evaluate("""async (lang) => {
            await i18next.changeLanguage(lang);
            localStorage.setItem('i18nextLng', lang);
            // Wait for React to re-render
            await new Promise(r => setTimeout(r, 200));
            return {
                language: i18next.language,
                resolvedLanguage: i18next.resolvedLanguage,
                cached: localStorage.getItem('i18nextLng')
            };
        }""", lang)

    def test_i18n_initialized(self) -> bool:
        """Test: i18n is properly initialized."""
        print("\n" + "=" * 50)
        print("TEST: i18n Initialization")
        print("=" * 50)

        state = self.get_i18n_state()

        if "error" in state:
            self._log_result("i18next available", False, state["error"])
            return False

        self._log_result("i18next available", True)
        self._log_result(
            "i18next initialized",
            state.get("isInitialized", False),
            f"isInitialized={state.get('isInitialized')}"
        )
        self._log_result(
            "Language detected",
            state.get("language") is not None,
            f"language={state.get('language')}"
        )

        print(f"\n  📊 Current State:")
        print(f"      Language: {state.get('language')}")
        print(f"      Resolved: {state.get('resolvedLanguage')}")
        print(f"      Cached: {state.get('cached')}")
        print(f"      Languages: {state.get('languages')}")

        return state.get("isInitialized", False)

    def test_translations_loaded(self) -> bool:
        """Test: Translations are properly loaded."""
        print("\n" + "=" * 50)
        print("TEST: Translation Loading")
        print("=" * 50)

        test_keys = [
            "app.title",
            "tools.allTools",
            "tools.searchPlaceholder",
            "console.title",
            "common.save",
            "common.cancel",
        ]

        translations = self.get_translations(test_keys)

        if "error" in translations:
            self._log_result("Get translations", False, translations["error"])
            return False

        all_valid = True
        for key in test_keys:
            value = translations.get(key, "")
            # Translation is valid if it's not the key itself (fallback)
            is_valid = value and value != key
            self._log_result(f"'{key}'", is_valid, f"= '{value}'")
            if not is_valid:
                all_valid = False

        return all_valid

    def test_language_switch(self, target_lang: str) -> bool:
        """Test: Language switching works correctly."""
        print("\n" + "=" * 50)
        print(f"TEST: Switch to '{target_lang}'")
        print("=" * 50)

        # Get initial state
        initial_state = self.get_i18n_state()
        initial_lang = initial_state.get("language", "unknown")
        print(f"  📍 Initial language: {initial_lang}")

        # Switch language
        new_state = self.switch_language(target_lang)
        new_lang = new_state.get("language", "unknown")

        # Verify switch
        switched = new_lang == target_lang
        self._log_result(
            f"Language changed to '{target_lang}'",
            switched,
            f"language={new_lang}"
        )

        # Verify localStorage
        cached = new_state.get("cached")
        cached_correct = cached == target_lang
        self._log_result(
            "localStorage updated",
            cached_correct,
            f"cached={cached}"
        )

        # Wait for UI update and verify DOM
        self.page.wait_for_timeout(300)

        # Check expected translations based on language
        if target_lang == "zh":
            expected = {
                "app.title": "DCC 工具架",
                "tools.allTools": "所有工具",
            }
        else:  # en
            expected = {
                "app.title": "DCC Shelves",
                "tools.allTools": "All Tools",
            }

        translations = self.get_translations(list(expected.keys()))
        for key, expected_value in expected.items():
            actual = translations.get(key, "")
            matches = actual == expected_value
            self._log_result(
                f"'{key}' = '{expected_value}'",
                matches,
                f"actual='{actual}'"
            )

        return switched and cached_correct

    def test_dom_content(self, expected_lang: str = None) -> bool:
        """Test: DOM content reflects current language."""
        print("\n" + "=" * 50)
        print("TEST: DOM Content Verification")
        print("=" * 50)

        if expected_lang is None:
            state = self.get_i18n_state()
            expected_lang = state.get("language", "en")

        print(f"  📍 Expected language: {expected_lang}")

        # Define expected content
        if expected_lang == "zh":
            expected_placeholder = "搜索工具..."
            expected_all_tools = "所有工具"
        else:
            expected_placeholder = "Search tools..."
            expected_all_tools = "All Tools"

        # Check search placeholder
        search_input = self.page.locator("input[type='text']").first
        if search_input.count() > 0:
            placeholder = search_input.get_attribute("placeholder")
            self._log_result(
                f"Search placeholder",
                placeholder == expected_placeholder,
                f"expected='{expected_placeholder}', actual='{placeholder}'"
            )
        else:
            self._log_result("Search input found", False)

        # Check "All" tab text (using more flexible selector)
        all_tab = self.page.locator("button").filter(has_text=expected_all_tools).first
        if all_tab.count() > 0:
            self._log_result(f"'{expected_all_tools}' button visible", True)
        else:
            self._log_result(
                f"'{expected_all_tools}' button visible",
                False,
                "Button not found"
            )

        return True

    def test_language_switcher_ui(self) -> bool:
        """Test: Language switcher UI works."""
        print("\n" + "=" * 50)
        print("TEST: Language Switcher UI")
        print("=" * 50)

        # Find the language switcher button (contains flag emoji and language code)
        # Look for button with "EN" or "中" text
        lang_button = self.page.locator("button").filter(has_text="EN").first
        if lang_button.count() == 0:
            lang_button = self.page.locator("button").filter(has_text="中").first

        if lang_button.count() == 0:
            self._log_result("Language button found", False, "Could not find EN or 中 button")
            return False

        self._log_result("Language button found", True)

        # Click to open dropdown
        lang_button.click()
        self.page.wait_for_timeout(300)

        # Check if dropdown appeared (look for language options with native names)
        zh_option = self.page.locator("button").filter(has_text="中文")
        en_option = self.page.locator("button").filter(has_text="English")

        has_zh = zh_option.count() > 0
        has_en = en_option.count() > 0

        self._log_result("Chinese option visible", has_zh)
        self._log_result("English option visible", has_en)

        if has_zh and has_en:
            # Click Chinese to test switch
            zh_option.click()
            self.page.wait_for_timeout(500)

            # Verify switch happened
            state = self.get_i18n_state()
            switched = state.get("language") == "zh"
            self._log_result("Switch via UI works", switched, f"language={state.get('language')}")

            # Verify UI updated - button should now show 中
            new_button = self.page.locator("button").filter(has_text="中").first
            ui_updated = new_button.count() > 0
            self._log_result("UI updated after switch", ui_updated)

            return switched and ui_updated

        return has_zh and has_en

    def run_all_tests(self) -> tuple[int, int]:
        """Run all i18n tests."""
        print("\n" + "=" * 60)
        print("🧪 i18n Automated Test Suite")
        print("=" * 60)

        self.test_i18n_initialized()
        self.test_translations_loaded()
        self.test_dom_content()
        self.test_language_switcher_ui()

        # Switch back to English and verify
        self.test_language_switch("en")
        self.test_dom_content("en")

        # Switch to Chinese and verify
        self.test_language_switch("zh")
        self.test_dom_content("zh")

        return self.passed, self.failed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="i18n Automated Testing with Playwright"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:5173",
        help="URL to test (default: http://localhost:5173)"
    )
    parser.add_argument(
        "--switch-to",
        default=None,
        help="Test switching to specified language (e.g., 'zh' or 'en')"
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run in headed mode (show browser)"
    )
    parser.add_argument(
        "--slow-mo",
        type=int,
        default=0,
        help="Slow down operations by specified milliseconds"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("🚀 i18n Automated Test Tool - Playwright")
    print("=" * 60)
    print(f"URL: {args.url}")
    print(f"Mode: {'Headed' if args.headed else 'Headless'}")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(
            headless=not args.headed,
            slow_mo=args.slow_mo
        )

        # Create context with locale preference
        context = browser.new_context(
            viewport={"width": 420, "height": 700},
            locale="en-US"  # Start with English
        )

        page = context.new_page()

        # Navigate to the app
        print(f"\n📂 Loading {args.url}...")
        try:
            page.goto(args.url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            print("\n💡 Make sure the dev server is running:")
            print("   npm run dev")
            browser.close()
            sys.exit(1)

        print("✅ Page loaded")

        # Wait for React to render
        page.wait_for_timeout(1000)

        # Create tester
        tester = I18nTester(page)

        # Run tests
        if args.switch_to:
            tester.test_i18n_initialized()
            tester.test_language_switch(args.switch_to)
            tester.test_dom_content(args.switch_to)
        else:
            tester.run_all_tests()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        print(f"  ✅ Passed: {tester.passed}")
        print(f"  ❌ Failed: {tester.failed}")
        print(f"  📈 Total:  {tester.passed + tester.failed}")

        if tester.failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {tester.failed} test(s) failed")

        # Keep browser open in headed mode
        if args.headed:
            print("\n⏸️  Browser open. Press Enter to close...")
            input()

        browser.close()

        # Exit with error if tests failed
        sys.exit(1 if tester.failed > 0 else 0)


if __name__ == "__main__":
    main()

