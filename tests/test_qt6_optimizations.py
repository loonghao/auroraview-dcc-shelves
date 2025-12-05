"""Test Qt6 optimizations are applied correctly.

This script verifies that Qt6-specific optimizations are properly
applied to dialogs in Houdini and Substance Painter.

Usage:
    # In Houdini
    python test_qt6_optimizations.py

    # In Substance Painter
    python test_qt6_optimizations.py
"""

import logging
import sys

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_qt6_dialog_optimizations():
    """Test that Qt6 dialog optimizations are applied correctly."""
    print("\n" + "=" * 60)
    print("Qt6 Dialog Optimizations Test")
    print("=" * 60)

    try:
        from qtpy.QtCore import Qt
        from qtpy.QtWidgets import QApplication, QDialog

        # Import diagnostics and optimization function
        sys.path.insert(0, "C:/Users/hallo/Documents/augment-projects/dcc_webview/python")
        from auroraview.integration.qt._compat import (
            apply_qt6_dialog_optimizations,
            get_qt_info,
            is_qt6,
        )
        from auroraview.integration.qt.diagnostics import diagnose_dialog, print_diagnostics
    except ImportError as e:
        print(f"ERROR: Failed to import required modules: {e}")
        return False

    # Create QApplication if needed
    app = QApplication.instance()
    if not app:
        app = QApplication([])

    # Get Qt info
    binding, version = get_qt_info()
    print(f"\nQt Environment: {binding} (Qt {version})")
    print(f"Is Qt6: {is_qt6()}")

    if not is_qt6():
        print("\nWARNING: Not running on Qt6, test may not be relevant")

    # Test 1: Dialog without optimizations
    print("\n" + "-" * 60)
    print("Test 1: Dialog WITHOUT optimizations")
    print("-" * 60)

    dialog1 = QDialog()
    dialog1.setWindowTitle("Test Dialog (No Optimizations)")
    diag1 = diagnose_dialog(dialog1)
    print_diagnostics(diag1, "Before Optimizations")

    # Test 2: Dialog with optimizations
    print("\n" + "-" * 60)
    print("Test 2: Dialog WITH optimizations")
    print("-" * 60)

    dialog2 = QDialog()
    dialog2.setWindowTitle("Test Dialog (With Optimizations)")

    # Apply optimizations
    success = apply_qt6_dialog_optimizations(dialog2)
    print(f"\nOptimizations applied: {success}")

    diag2 = diagnose_dialog(dialog2)
    print_diagnostics(diag2, "After Optimizations")

    # Verify optimizations
    print("\n" + "-" * 60)
    print("Verification")
    print("-" * 60)

    if is_qt6():
        expected_attrs = {
            "WA_OpaquePaintEvent": True,
            "WA_TranslucentBackground": False,
            "WA_NoSystemBackground": False,
            "WA_NativeWindow": True,
            "WA_InputMethodEnabled": True,
        }

        all_correct = True
        for attr_name, expected_value in expected_attrs.items():
            actual_value = diag2["attributes"].get(attr_name)
            status = "✓" if actual_value == expected_value else "✗"
            print(f"{status} {attr_name}: {actual_value} (expected: {expected_value})")

            if actual_value != expected_value:
                all_correct = False

        if all_correct:
            print("\n✅ All Qt6 optimizations applied correctly!")
            return True
        else:
            print("\n❌ Some Qt6 optimizations are missing!")
            return False
    else:
        print("Skipping verification (not Qt6)")
        return True


def test_houdini_adapter():
    """Test Houdini adapter dialog configuration."""
    print("\n" + "=" * 60)
    print("Houdini Adapter Test")
    print("=" * 60)

    try:
        from qtpy.QtWidgets import QApplication, QDialog

        sys.path.insert(0, "C:/github/auroraview-dcc-shelves/src")
        from auroraview_dcc_shelves.apps.houdini import HoudiniAdapter

        sys.path.insert(0, "C:/Users/hallo/Documents/augment-projects/dcc_webview/python")
        from auroraview.integration.qt.diagnostics import diagnose_dialog, print_diagnostics
    except ImportError as e:
        print(f"ERROR: Failed to import: {e}")
        return False

    # Create QApplication if needed
    app = QApplication.instance()
    if not app:
        app = QApplication([])

    # Create adapter and dialog
    adapter = HoudiniAdapter()
    dialog = QDialog()

    # Configure dialog using adapter
    adapter.configure_dialog(dialog)

    # Diagnose
    diag = diagnose_dialog(dialog)
    print_diagnostics(diag, "Houdini Dialog Configuration")

    # Check for issues
    if diag["issues"]:
        print("\n❌ Issues found!")
        return False
    elif diag["warnings"]:
        print("\n⚠️  Warnings found (may be acceptable)")
        return True
    else:
        print("\n✅ No issues found!")
        return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AuroraView Qt6 Optimizations Test Suite")
    print("=" * 60)

    # Run tests
    test1_passed = test_qt6_dialog_optimizations()
    test2_passed = test_houdini_adapter()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Qt6 Dialog Optimizations: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Houdini Adapter: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print("=" * 60 + "\n")

    sys.exit(0 if (test1_passed and test2_passed) else 1)

