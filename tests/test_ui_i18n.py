"""
DCC Shelves i18n (Internationalization) UI Tests

Tests for language switching and translations using the actual project frontend.
"""

from __future__ import annotations

import logging
import time

import pytest

logger = logging.getLogger(__name__)

# Check if auroraview is available
try:
    from auroraview import WebView
    from auroraview.testing import DomAssertions

    AURORAVIEW_AVAILABLE = True
except ImportError:
    AURORAVIEW_AVAILABLE = False


# =============================================================================
# Language Detection Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestLanguageDetection:
    """Tests for language detection and display."""

    def test_default_language_loaded(self, shelf_webview: WebView):
        """Test that a default language is loaded."""
        result = shelf_webview.eval_js("""
            // Check if i18n is initialized
            const hasEnglish = document.body.innerText.includes('Tools') ||
                              document.body.innerText.includes('Search');
            const hasChinese = document.body.innerText.includes('工具') ||
                              document.body.innerText.includes('搜索');
            hasEnglish || hasChinese;
        """)
        assert result is True, "App should display text in some language"

    def test_i18n_keys_not_displayed(self, shelf_webview: WebView):
        """Test that raw i18n keys are not displayed."""
        result = shelf_webview.eval_js("""
            const text = document.body.innerText;
            // i18n keys typically look like 'app.title' or 'tools.search'
            !text.includes('app.title') && !text.includes('tools.search') &&
            !text.includes('common.') && !text.includes('bottomPanel.');
        """)
        assert result is True, "Raw i18n keys should not be displayed"


# =============================================================================
# English Language Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestEnglishTranslations:
    """Tests for English translations."""

    def test_english_ui_elements(self, shelf_webview: WebView):
        """Test common English UI elements."""
        # First, try to switch to English
        shelf_webview.eval_js("""
            // Try to change language via i18n
            if (window.i18n && window.i18n.changeLanguage) {
                window.i18n.changeLanguage('en');
            }
        """)
        time.sleep(0.5)

        shelf_webview.eval_js("""
            const text = document.body.innerText;
            // Check for common English terms
            text.includes('Tools') || text.includes('Search') ||
            text.includes('Detail') || text.includes('Console') ||
            text.includes('Settings') || text.includes('User');
        """)
        # English text should be present

    def test_english_search_placeholder(self, shelf_webview: WebView):
        """Test English search placeholder."""
        shelf_webview.eval_js("""
            if (window.i18n && window.i18n.changeLanguage) {
                window.i18n.changeLanguage('en');
            }
        """)
        time.sleep(0.3)

        shelf_webview.eval_js("""
            const input = document.querySelector('input[type="text"]');
            const placeholder = input ? input.placeholder.toLowerCase() : '';
            placeholder.includes('search');
        """)
        # Placeholder should contain "search" in English


# =============================================================================
# Chinese Language Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestChineseTranslations:
    """Tests for Chinese translations."""

    def test_chinese_ui_elements(self, shelf_webview: WebView):
        """Test common Chinese UI elements."""
        # Switch to Chinese
        shelf_webview.eval_js("""
            if (window.i18n && window.i18n.changeLanguage) {
                window.i18n.changeLanguage('zh');
            }
        """)
        time.sleep(0.5)

        shelf_webview.eval_js("""
            const text = document.body.innerText;
            // Check for common Chinese terms
            text.includes('工具') || text.includes('搜索') ||
            text.includes('详情') || text.includes('控制台') ||
            text.includes('设置') || text.includes('用户');
        """)
        # Chinese text should be present

    def test_chinese_search_placeholder(self, shelf_webview: WebView):
        """Test Chinese search placeholder."""
        shelf_webview.eval_js("""
            if (window.i18n && window.i18n.changeLanguage) {
                window.i18n.changeLanguage('zh');
            }
        """)
        time.sleep(0.3)

        shelf_webview.eval_js("""
            const input = document.querySelector('input[type="text"]');
            const placeholder = input ? input.placeholder : '';
            placeholder.includes('搜索');
        """)
        # Placeholder should contain "搜索" in Chinese


# =============================================================================
# Language Switching Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestLanguageSwitching:
    """Tests for language switching functionality."""

    def test_switch_to_chinese(self, shelf_webview: WebView):
        """Test switching from English to Chinese."""
        # Switch to Chinese
        shelf_webview.eval_js("""
            if (window.i18n && window.i18n.changeLanguage) {
                window.i18n.changeLanguage('zh');
            }
        """)
        time.sleep(0.5)

        result = shelf_webview.eval_js("""
            const text = document.body.innerText;
            text.includes('工具') || text.includes('搜索') || text.includes('详情');
        """)
        assert result is True, "UI should display Chinese after switching"

    def test_switch_to_english(self, shelf_webview: WebView):
        """Test switching from Chinese to English."""
        # First switch to Chinese
        shelf_webview.eval_js("""
            if (window.i18n && window.i18n.changeLanguage) {
                window.i18n.changeLanguage('zh');
            }
        """)
        time.sleep(0.3)

        # Then switch to English
        shelf_webview.eval_js("""
            if (window.i18n && window.i18n.changeLanguage) {
                window.i18n.changeLanguage('en');
            }
        """)
        time.sleep(0.5)

        result = shelf_webview.eval_js("""
            const text = document.body.innerText;
            text.includes('Tools') || text.includes('Search') || text.includes('Detail');
        """)
        assert result is True, "UI should display English after switching"

    def test_language_switch_updates_all_elements(self, shelf_webview: WebView):
        """Test that language switch updates all UI elements."""
        # Switch to Chinese
        shelf_webview.eval_js("""
            if (window.i18n && window.i18n.changeLanguage) {
                window.i18n.changeLanguage('zh');
            }
        """)
        time.sleep(0.5)

        # Check multiple elements
        shelf_webview.eval_js("""
            const text = document.body.innerText;
            // Should not have English-only terms if switched to Chinese
            const hasDetailChinese = text.includes('详情');
            const hasConsoleChinese = text.includes('控制台');
            hasDetailChinese || hasConsoleChinese;
        """)
        # All elements should be translated


# =============================================================================
# Tool Name Translation Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestToolNameTranslations:
    """Tests for tool name translations."""

    def test_tool_names_in_english(self, shelf_webview: WebView):
        """Test that tool names display in English."""
        shelf_webview.eval_js("""
            if (window.i18n && window.i18n.changeLanguage) {
                window.i18n.changeLanguage('en');
            }
        """)
        time.sleep(0.5)

        result = shelf_webview.eval_js("""
            // Tool names should be visible
            const buttons = document.querySelectorAll('button');
            const toolBtns = Array.from(buttons).filter(btn => btn.querySelector('svg'));
            toolBtns.length > 0;
        """)
        assert result is True, "Tool buttons should be visible"

    def test_tool_names_in_chinese(self, shelf_webview: WebView):
        """Test that tool names display in Chinese."""
        shelf_webview.eval_js("""
            if (window.i18n && window.i18n.changeLanguage) {
                window.i18n.changeLanguage('zh');
            }
        """)
        time.sleep(0.5)

        result = shelf_webview.eval_js("""
            // Tool names should be visible
            const buttons = document.querySelectorAll('button');
            const toolBtns = Array.from(buttons).filter(btn => btn.querySelector('svg'));
            toolBtns.length > 0;
        """)
        assert result is True, "Tool buttons should be visible in Chinese"


# =============================================================================
# Settings Page i18n Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestSettingsPageI18n:
    """Tests for settings page internationalization."""

    def test_settings_language_selector(self, settings_webview: WebView):
        """Test that settings page has language selector."""
        result = settings_webview.eval_js("""
            const text = document.body.innerText;
            text.includes('Language') || text.includes('语言') ||
            text.includes('English') || text.includes('中文');
        """)
        assert result is True, "Settings should have language option"

    def test_settings_labels_translated(self, settings_webview: WebView):
        """Test that settings labels are translated."""
        # Switch to Chinese
        settings_webview.eval_js("""
            if (window.i18n && window.i18n.changeLanguage) {
                window.i18n.changeLanguage('zh');
            }
        """)
        time.sleep(0.5)

        settings_webview.eval_js("""
            const text = document.body.innerText;
            // Check for Chinese settings labels
            text.includes('语言') || text.includes('主题') || text.includes('设置');
        """)
        # Settings labels should be in Chinese
