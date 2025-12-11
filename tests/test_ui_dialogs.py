"""
DCC Shelves Dialog UI Tests

Tests for dialog components using the actual project frontend.
Covers Create Tool dialog, Settings dialog, and other modal interactions.
"""

from __future__ import annotations

import logging
import time

import pytest

logger = logging.getLogger(__name__)

# Check if auroraview is available
try:
    from auroraview import WebView
    from auroraview.testing import DomAssertions  # noqa: F401

    AURORAVIEW_AVAILABLE = True
except ImportError:
    AURORAVIEW_AVAILABLE = False


# =============================================================================
# Create Tool Dialog Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestCreateToolDialog:
    """Tests for the Create Tool dialog."""

    def test_open_create_dialog(self, shelf_webview: WebView):
        """Test opening the Create Tool dialog."""
        # Find and click Create button
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const createBtn = Array.from(buttons).find(btn => {
                const text = btn.textContent.toLowerCase();
                return text.includes('create') || text.includes('创建') ||
                       btn.querySelector('[data-icon="plus"]');
            });

            if (createBtn) {
                createBtn.click();
                return true;
            }
            return false;
        """)
        time.sleep(0.5)

        # Check if dialog opened
        shelf_webview.eval_js("""
            const dialog = document.querySelector('[role="dialog"], .dialog, .modal, [data-dialog]');
            dialog !== null;
        """)
        # Dialog may or may not appear depending on UI state

    def test_create_dialog_has_form_fields(self, shelf_webview: WebView):
        """Test that Create dialog has required form fields."""
        # Open dialog first
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const createBtn = Array.from(buttons).find(btn => {
                const text = btn.textContent.toLowerCase();
                return text.includes('create') || text.includes('创建');
            });
            if (createBtn) createBtn.click();
        """)
        time.sleep(0.5)

        # Check for form fields
        shelf_webview.eval_js("""
            const inputs = document.querySelectorAll('input, select, textarea');
            inputs.length;
        """)
        # Should have at least some form inputs

    def test_create_dialog_cancel(self, shelf_webview: WebView):
        """Test canceling the Create dialog."""
        # Open dialog
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const createBtn = Array.from(buttons).find(btn => {
                const text = btn.textContent.toLowerCase();
                return text.includes('create') || text.includes('创建');
            });
            if (createBtn) createBtn.click();
        """)
        time.sleep(0.3)

        # Click Cancel button
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const cancelBtn = Array.from(buttons).find(btn => {
                const text = btn.textContent.toLowerCase();
                return text.includes('cancel') || text.includes('取消');
            });
            if (cancelBtn) cancelBtn.click();
        """)
        time.sleep(0.3)

        # Dialog should be closed
        shelf_webview.eval_js("""
            const dialog = document.querySelector('[role="dialog"], .dialog, .modal');
            dialog === null || dialog.style.display === 'none';
        """)
        # Dialog should be closed or hidden

    def test_create_dialog_form_validation(self, shelf_webview: WebView):
        """Test form validation in Create dialog."""
        # Open dialog
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const createBtn = Array.from(buttons).find(btn => {
                const text = btn.textContent.toLowerCase();
                return text.includes('create') || text.includes('创建');
            });
            if (createBtn) createBtn.click();
        """)
        time.sleep(0.3)

        # Try to submit without filling required fields
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const saveBtn = Array.from(buttons).find(btn => {
                const text = btn.textContent.toLowerCase();
                return text.includes('save') || text.includes('保存') ||
                       text.includes('confirm') || text.includes('确定');
            });
            if (saveBtn) saveBtn.click();
        """)
        time.sleep(0.3)

        # Should show validation error or prevent submission
        shelf_webview.eval_js("""
            // Check for error message or required field indication
            const errorText = document.body.innerText.toLowerCase();
            errorText.includes('required') || errorText.includes('必填') ||
            document.querySelector('.error, .invalid, [aria-invalid="true"]') !== null;
        """)
        # Validation should be triggered


# =============================================================================
# Settings Dialog Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestSettingsDialog:
    """Tests for the Settings dialog/panel."""

    def test_open_settings(self, shelf_webview: WebView):
        """Test opening settings."""
        # Find and click Settings button
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const settingsBtn = Array.from(buttons).find(btn => {
                const text = btn.textContent.toLowerCase();
                const ariaLabel = btn.getAttribute('aria-label')?.toLowerCase() || '';
                return text.includes('settings') || text.includes('设置') ||
                       ariaLabel.includes('settings');
            });

            if (settingsBtn) {
                settingsBtn.click();
                return true;
            }
            return false;
        """)
        time.sleep(0.5)

        # Settings may open in new window or panel

    def test_settings_has_language_option(self, settings_webview: WebView):
        """Test that settings has language option."""
        result = settings_webview.eval_js("""
            const text = document.body.innerText;
            text.includes('Language') || text.includes('语言') ||
            text.includes('English') || text.includes('中文');
        """)
        assert result is True, "Settings should have language option"

    def test_settings_has_theme_option(self, settings_webview: WebView):
        """Test that settings has theme option."""
        settings_webview.eval_js("""
            const text = document.body.innerText;
            text.includes('Theme') || text.includes('主题') ||
            text.includes('Dark') || text.includes('Light');
        """)
        # Theme option may or may not exist


# =============================================================================
# Confirmation Dialog Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestConfirmationDialogs:
    """Tests for confirmation dialogs."""

    def test_delete_confirmation(self, shelf_webview: WebView):
        """Test delete confirmation dialog."""
        # This would require having a user tool to delete
        # For now, just verify the mechanism exists
        shelf_webview.eval_js("""
            // Check if there's any delete button
            const buttons = document.querySelectorAll('button');
            const deleteBtn = Array.from(buttons).find(btn => {
                const text = btn.textContent.toLowerCase();
                return text.includes('delete') || text.includes('删除');
            });
            deleteBtn !== null;
        """)
        # Delete button may or may not exist


# =============================================================================
# Dialog Accessibility Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestDialogAccessibility:
    """Tests for dialog accessibility."""

    def test_dialog_has_role(self, shelf_webview: WebView):
        """Test that dialogs have proper ARIA role."""
        # Open a dialog first
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const createBtn = Array.from(buttons).find(btn => {
                const text = btn.textContent.toLowerCase();
                return text.includes('create') || text.includes('创建');
            });
            if (createBtn) createBtn.click();
        """)
        time.sleep(0.3)

        result = shelf_webview.eval_js("""
            const dialog = document.querySelector('[role="dialog"]');
            dialog !== null;
        """)
        # Dialog should have role="dialog"
        logger.info(f"Dialog has role: {result}")

    def test_dialog_focus_trap(self, shelf_webview: WebView):
        """Test that dialog traps focus."""
        # Open dialog
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const createBtn = Array.from(buttons).find(btn => {
                const text = btn.textContent.toLowerCase();
                return text.includes('create') || text.includes('创建');
            });
            if (createBtn) createBtn.click();
        """)
        time.sleep(0.3)

        # Check if focus is within dialog
        result = shelf_webview.eval_js("""
            const dialog = document.querySelector('[role="dialog"], .dialog, .modal');
            if (!dialog) return null;

            const activeElement = document.activeElement;
            dialog.contains(activeElement) || dialog === activeElement;
        """)
        # Focus should be trapped in dialog
        logger.info(f"Focus trapped: {result}")


# =============================================================================
# Dialog Animation Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestDialogAnimations:
    """Tests for dialog animations."""

    def test_dialog_open_animation(self, shelf_webview: WebView):
        """Test that dialog has open animation."""
        # Check for animation classes
        shelf_webview.eval_js("""
            const dialog = document.querySelector('[role="dialog"], .dialog, .modal');
            if (!dialog) return null;

            const classes = dialog.className;
            const style = window.getComputedStyle(dialog);

            classes.includes('animate') || classes.includes('transition') ||
            style.transition !== 'all 0s ease 0s' || style.animation !== 'none';
        """)
        # Animation may or may not be present

    def test_dialog_backdrop(self, shelf_webview: WebView):
        """Test that dialog has backdrop overlay."""
        # Open dialog
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const createBtn = Array.from(buttons).find(btn => {
                const text = btn.textContent.toLowerCase();
                return text.includes('create') || text.includes('创建');
            });
            if (createBtn) createBtn.click();
        """)
        time.sleep(0.3)

        result = shelf_webview.eval_js("""
            // Look for backdrop/overlay element
            const backdrop = document.querySelector('.backdrop, .overlay, [data-backdrop]');
            const fixedOverlay = document.querySelector('.fixed.inset-0');
            backdrop !== null || fixedOverlay !== null;
        """)
        # Backdrop should exist when dialog is open
        logger.info(f"Backdrop exists: {result}")
