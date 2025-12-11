"""Qt style sheets (QSS) for DCC Shelves UI.

This module contains all QSS styles used by the ShelfApp for styling
Qt widgets with a flat, Apple-style design.
"""

from __future__ import annotations

# =============================================================================
# Flat Apple-style QSS
# Deep dark background matching WebView content to prevent white flash
# Uses the same gradient colors as frontend
# =============================================================================
FLAT_STYLE_QSS = """
/* Main dialog - dark background matching WebView content */
/* This prevents white flash during WebView initialization */
/* Ensure no margins or padding that could cause white borders */
QDialog {
    background-color: #0d0d0d;
    border: none;
    margin: 0;
    padding: 0;
}

/* Frame with transparent background */
QFrame {
    background-color: transparent;
    border: none;
    margin: 0;
    padding: 0;
}

/* Ensure QWidget containers have no borders */
QWidget {
    margin: 0;
    padding: 0;
}

/* Scrollbar - minimal Apple-style */
QScrollBar:vertical {
    background-color: transparent;
    width: 6px;
    margin: 4px 2px 4px 2px;
    border: none;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background-color: rgba(255, 255, 255, 0.12);
    min-height: 30px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background-color: rgba(255, 255, 255, 0.20);
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
    background: transparent;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}

/* Horizontal scrollbar */
QScrollBar:horizontal {
    background-color: transparent;
    height: 6px;
    margin: 2px 4px 2px 4px;
    border: none;
    border-radius: 3px;
}

QScrollBar::handle:horizontal {
    background-color: rgba(255, 255, 255, 0.12);
    min-width: 30px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal:hover {
    background-color: rgba(255, 255, 255, 0.20);
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
    background: transparent;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
}

/* Tooltip styling */
QToolTip {
    background-color: #2d2d44;
    color: #ffffff;
    border: 1px solid #3d3d5c;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* Size grip - subtle */
QSizeGrip {
    background-color: transparent;
    width: 16px;
    height: 16px;
}

/* Loading indicator */
QLabel#loadingLabel {
    color: rgba(255, 255, 255, 0.6);
    font-size: 14px;
    font-weight: 500;
}
"""

# =============================================================================
# Loading Indicator Style
# Used during deferred initialization
# =============================================================================
LOADING_STYLE_QSS = """
QDialog {
    background-color: #0d0d0d;
    border: none;
    margin: 0;
    padding: 0;
}
QWidget {
    margin: 0;
    padding: 0;
}
QLabel {
    color: rgba(255, 255, 255, 0.6);
    font-size: 14px;
    font-weight: 500;
}
"""
