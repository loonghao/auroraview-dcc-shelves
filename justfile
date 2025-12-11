# AuroraView DCC Shelves - Just Commands
# A universal tool shelf system for all DCC applications

# Set shell to PowerShell on Windows
set shell := ["powershell", "-NoLogo", "-Command"]

# Default recipe: show all available commands
default:
    @just --list

# ============================================
# Development Commands
# ============================================

# Start frontend development server
dev:
    npm run dev

# Build frontend for production
build:
    npm run build

# Preview production build
preview:
    npm run preview

# Install all dependencies (Python + Node.js)
install:
    uv sync --all-extras
    npm install

# Run linting checks
lint:
    uvx nox -s lint

# Format code
format:
    uvx nox -s format

# Run tests
test:
    uvx nox -s pytest

# Run tests with coverage
coverage:
    uvx nox -s coverage

# ============================================
# DCC Launch Commands (Windows)
# ============================================

# Common DCC installation paths (Windows)
# These can be overridden via environment variables

MAYA_PATH := env_var_or_default("MAYA_PATH", "C:/Program Files/Autodesk/Maya2024/bin/maya.exe")
HOUDINI_PATH := env_var_or_default("HOUDINI_PATH", "C:/Program Files/Side Effects Software/Houdini 20.5/bin/houdini.exe")
BLENDER_PATH := env_var_or_default("BLENDER_PATH", "C:/Program Files/Blender Foundation/Blender 4.2/blender.exe")
NUKE_PATH := env_var_or_default("NUKE_PATH", "C:/Program Files/Nuke15.1v1/Nuke15.1.exe")
CINEMA4D_PATH := env_var_or_default("CINEMA4D_PATH", "C:/Program Files/Maxon Cinema 4D 2024/Cinema 4D.exe")
UNREAL_PATH := env_var_or_default("UNREAL_PATH", "C:/Program Files/Epic Games/UE_5.4/Engine/Binaries/Win64/UnrealEditor.exe")
RESOLVE_PATH := env_var_or_default("RESOLVE_PATH", "C:/Program Files/Blackmagic Design/DaVinci Resolve/Resolve.exe")
SUBSTANCE_PAINTER_PATH := env_var_or_default("SUBSTANCE_PAINTER_PATH", "C:/Program Files/Adobe/Adobe Substance 3D Painter/Adobe Substance 3D Painter.exe")
SUBSTANCE_DESIGNER_PATH := env_var_or_default("SUBSTANCE_DESIGNER_PATH", "C:/Program Files/Adobe/Adobe Substance 3D Designer/Adobe Substance 3D Designer.exe")
ZBRUSH_PATH := env_var_or_default("ZBRUSH_PATH", "C:/Program Files/Maxon ZBrush 2024/ZBrush.exe")
MAX_PATH := env_var_or_default("MAX_PATH", "C:/Program Files/Autodesk/3ds Max 2024/3dsmax.exe")
MOTIONBUILDER_PATH := env_var_or_default("MOTIONBUILDER_PATH", "C:/Program Files/Autodesk/MotionBuilder 2024/bin/motionbuilder.exe")
MARI_PATH := env_var_or_default("MARI_PATH", "C:/Program Files/Mari7.0v1/Bundle/bin/Mari7.0v1.exe")
KATANA_PATH := env_var_or_default("KATANA_PATH", "C:/Program Files/Katana7.0v1/bin/katana.exe")

# Launch Maya
maya:
    @Write-Host "Launching Maya..."
    @Start-Process "{{MAYA_PATH}}"

# Launch Houdini
houdini:
    @Write-Host "Launching Houdini..."
    @Start-Process "{{HOUDINI_PATH}}"

# Launch Blender
blender:
    @Write-Host "Launching Blender..."
    @Start-Process "{{BLENDER_PATH}}"

# Launch Nuke
nuke:
    @Write-Host "Launching Nuke..."
    @Start-Process "{{NUKE_PATH}}"

# Launch Cinema 4D
cinema4d:
    @Write-Host "Launching Cinema 4D..."
    @Start-Process "{{CINEMA4D_PATH}}"

# Launch Unreal Engine
unreal:
    @Write-Host "Launching Unreal Engine..."
    @Start-Process "{{UNREAL_PATH}}"

# Launch DaVinci Resolve
resolve:
    @Write-Host "Launching DaVinci Resolve..."
    @Start-Process "{{RESOLVE_PATH}}"

# Launch Substance Painter
substance-painter:
    @Write-Host "Launching Substance Painter..."
    @Start-Process "{{SUBSTANCE_PAINTER_PATH}}"

# Launch Substance Designer
substance-designer:
    @Write-Host "Launching Substance Designer..."
    @Start-Process "{{SUBSTANCE_DESIGNER_PATH}}"

# Launch ZBrush
zbrush:
    @Write-Host "Launching ZBrush..."
    @Start-Process "{{ZBRUSH_PATH}}"

# Launch 3ds Max
max:
    @Write-Host "Launching 3ds Max..."
    @Start-Process "{{MAX_PATH}}"

# Launch MotionBuilder
motionbuilder:
    @Write-Host "Launching MotionBuilder..."
    @Start-Process "{{MOTIONBUILDER_PATH}}"

# Launch Mari
mari:
    @Write-Host "Launching Mari..."
    @Start-Process "{{MARI_PATH}}"

# Launch Katana
katana:
    @Write-Host "Launching Katana..."
    @Start-Process "{{KATANA_PATH}}"

# ============================================
# Demo & Examples
# ============================================

# Run the shelf demo with AuroraView
demo:
    uv run python -c "from auroraview_dcc_shelves import ShelfApp, load_config; config = load_config('examples/shelf_config.yaml'); app = ShelfApp(config); app.show()"

# Run the shelf demo with debug mode enabled
demo-debug:
    uv run python -c "from auroraview_dcc_shelves import ShelfApp, load_config; config = load_config('examples/shelf_config.yaml'); app = ShelfApp(config); app.show(debug=True)"

# Show example configuration
show-config:
    @Get-Content examples/shelf_config.yaml

# Open dist/index.html in default browser for testing
preview-html:
    Start-Process "file:///C:/github/auroraview-dcc-shelves/dist/index.html"

# ============================================
# Tool Translation Commands
# ============================================

# Translate tool names/descriptions in YAML config (default: examples/shelf_config.yaml)
translate-tools config="examples/shelf_config.yaml":
    python scripts/translate_tools.py "{{config}}"

# Preview translations without saving (dry run)
translate-tools-preview config="examples/shelf_config.yaml":
    python scripts/translate_tools.py "{{config}}" --dry-run

# Clear translation cache
translate-clear-cache:
    Remove-Item -Path scripts/translation_cache.json -ErrorAction SilentlyContinue
    Write-Host "Translation cache cleared"

# ============================================
# Pre-commit & Linting
# ============================================

# Install pre-commit hooks
pre-commit-install:
    uvx pre-commit install

# Run pre-commit on all files
pre-commit-all:
    uvx pre-commit run --all-files

# Run ruff check and fix
ruff-fix:
    uv run ruff check --fix src tests
    uv run ruff format src tests

# CI lint check (no auto-fix)
ci-lint:
    uv run ruff check src tests
    uv run ruff format --check src tests

# ============================================
# DCC Package Build Commands
# ============================================

# Build distribution package for all DCCs
build-dcc-packages:
    @Write-Host "Building DCC distribution packages..."
    @just build
    @just _build-maya-package
    @just _build-houdini-package
    @just _build-nuke-package
    @Write-Host "[OK] All DCC packages built in dist/dcc/"

# Build Maya package
_build-maya-package:
    @Write-Host "Building Maya package..."
    @New-Item -ItemType Directory -Force -Path "dist/dcc/maya" | Out-Null
    @Copy-Item -Recurse -Force "src/auroraview_dcc_shelves" "dist/dcc/maya/"
    @Copy-Item -Recurse -Force "dist/assets" "dist/dcc/maya/" -ErrorAction SilentlyContinue
    @Copy-Item -Force "dist/index.html" "dist/dcc/maya/" -ErrorAction SilentlyContinue
    @Copy-Item -Force "examples/maya/*.py" "dist/dcc/maya/" -ErrorAction SilentlyContinue
    @Write-Host "[OK] Maya package: dist/dcc/maya/"

# Build Houdini package
_build-houdini-package:
    @Write-Host "Building Houdini package..."
    @New-Item -ItemType Directory -Force -Path "dist/dcc/houdini" | Out-Null
    @Copy-Item -Recurse -Force "src/auroraview_dcc_shelves" "dist/dcc/houdini/"
    @Copy-Item -Recurse -Force "dist/assets" "dist/dcc/houdini/" -ErrorAction SilentlyContinue
    @Copy-Item -Force "dist/index.html" "dist/dcc/houdini/" -ErrorAction SilentlyContinue
    @Copy-Item -Force "examples/houdini/*.py" "dist/dcc/houdini/" -ErrorAction SilentlyContinue
    @Write-Host "[OK] Houdini package: dist/dcc/houdini/"

# Build Nuke package
_build-nuke-package:
    @Write-Host "Building Nuke package..."
    @New-Item -ItemType Directory -Force -Path "dist/dcc/nuke" | Out-Null
    @Copy-Item -Recurse -Force "src/auroraview_dcc_shelves" "dist/dcc/nuke/"
    @Copy-Item -Recurse -Force "dist/assets" "dist/dcc/nuke/" -ErrorAction SilentlyContinue
    @Copy-Item -Force "dist/index.html" "dist/dcc/nuke/" -ErrorAction SilentlyContinue
    @Copy-Item -Force "examples/nuke/*.py" "dist/dcc/nuke/" -ErrorAction SilentlyContinue
    @Write-Host "[OK] Nuke package: dist/dcc/nuke/"

# Build package for specific DCC
build-dcc dcc:
    @Write-Host "Building {{dcc}} package..."
    @just build
    @just _build-{{dcc}}-package

# Clean DCC packages
clean-dcc-packages:
    @Remove-Item -Recurse -Force "dist/dcc" -ErrorAction SilentlyContinue
    @Write-Host "[OK] DCC packages cleaned"

# ============================================
# CI Commands
# ============================================

# CI install dependencies
ci-install:
    uv sync --extra dev
    npm install

# CI build (frontend + Python)
ci-build:
    npm run build
    uv build

# CI test
ci-test:
    uv run pytest tests/ --tb=short -v -m "not slow"

# Full CI pipeline
ci: ci-install ci-lint ci-build ci-test
    @Write-Host "[OK] CI pipeline completed"
