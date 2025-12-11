# Check if Rust code has been recompiled - Copy and paste into Maya Script Editor

import logging
import os
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("RUST COMPILATION CHECK")
logger.info("=" * 60)

# Check auroraview module location
import auroraview

module_path = auroraview.__file__
logger.info(f"AuroraView module: {module_path}")

# Get the directory containing the compiled .pyd/.so files
module_dir = os.path.dirname(module_path)
logger.info(f"Module directory: {module_dir}")

# Find all .pyd or .so files (compiled Rust extensions)
compiled_files = []
for filename in os.listdir(module_dir):
    if filename.endswith(".pyd") or filename.endswith(".so"):
        filepath = os.path.join(module_dir, filename)
        compiled_files.append(filepath)

if not compiled_files:
    logger.warning("WARNING: No compiled Rust files found!")
    logger.warning("This might be a pure Python installation")
else:
    logger.info(f"\nFound {len(compiled_files)} compiled Rust file(s):")

    for filepath in compiled_files:
        # Get file modification time
        mtime = os.path.getmtime(filepath)
        mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

        # Get file size
        size = os.path.getsize(filepath)
        size_mb = size / (1024 * 1024)

        # Calculate age
        age_seconds = time.time() - mtime
        age_minutes = age_seconds / 60
        age_hours = age_minutes / 60

        logger.info(f"\n  File: {os.path.basename(filepath)}")
        logger.info(f"  Modified: {mtime_str}")
        logger.info(f"  Size: {size_mb:.2f} MB")

        if age_hours < 1:
            logger.info(f"  Age: {age_minutes:.1f} minutes (RECENT)")
        elif age_hours < 24:
            logger.info(f"  Age: {age_hours:.1f} hours")
        else:
            age_days = age_hours / 24
            logger.info(f"  Age: {age_days:.1f} days (OLD)")

logger.info("\n" + "=" * 60)
logger.info("INTERPRETATION")
logger.info("=" * 60)

if compiled_files:
    newest_file = max(compiled_files, key=os.path.getmtime)
    newest_mtime = os.path.getmtime(newest_file)
    age_hours = (time.time() - newest_mtime) / 3600

    if age_hours < 1:
        logger.info("OK: Rust code was compiled recently (< 1 hour ago)")
        logger.info("The fixes should be active.")
    else:
        logger.warning(f"WARNING: Rust code was compiled {age_hours:.1f} hours ago")
        logger.warning("You may need to recompile:")
        logger.warning("  cd C:\\Users\\hallo\\Documents\\augment-projects\\dcc_webview")
        logger.warning("  maturin develop --release")
        logger.warning("Then restart Maya to load the new code.")
else:
    logger.error("ERROR: No compiled Rust files found!")
    logger.error("AuroraView may not be properly installed.")

logger.info("\n" + "=" * 60)
