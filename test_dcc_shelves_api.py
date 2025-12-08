"""Test DCC Shelves API binding with actual app code."""

import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from pathlib import Path

from auroraview import WebView
from auroraview.utils import get_auroraview_entry_url

DIST_DIR = Path(__file__).parent / "dist"


def main():
    webview = WebView(
        title="DCC Shelves - API Test",
        width=500,
        height=700,
        debug=True,
        context_menu=True,
        asset_root=str(DIST_DIR),
    )

    child_windows = {}

    class DesktopShelfAPI:
        """Test API class."""

        def get_config(self):
            logger.info("get_config called")
            return {"shelves": [], "currentHost": "desktop", "banner": {"title": "DCC Shelves", "subtitle": "API Test"}}

        def launch_tool(self, button_id=""):
            logger.info(f"launch_tool called: {button_id}")
            return {"success": True, "buttonId": button_id}

        def get_tool_path(self, button_id=""):
            return {"buttonId": button_id, "path": ""}

        def get_user_tools(self):
            return {"success": True, "tools": []}

        def save_user_tool(self, **kwargs):
            return {"success": True}

        def delete_user_tool(self, id=""):
            return {"success": True}

        def export_user_tools(self):
            return {"success": True, "config": "{}"}

        def import_user_tools(self, config="", merge=True):
            return {"success": True, "count": 0}

        def close_main_window(self):
            logger.info("close_main_window called")
            return {"success": True}

        def create_window(self, label="", url="", title="Window", width=500, height=600):
            """Create a new native window."""
            logger.info(f">>> create_window called: label={label}, url={url}, title={title}")

            if not label:
                return {"success": False, "message": "No label provided", "label": ""}

            if label in child_windows:
                logger.info(f"Window '{label}' already exists")
                return {"success": True, "message": "Window already exists", "label": label}

            try:
                # Resolve URL
                if url.startswith("http://") or url.startswith("https://"):
                    load_url = url
                else:
                    entry_file = url.lstrip("/")
                    load_url = get_auroraview_entry_url(entry_file)

                logger.info(f"Creating child window with URL: {load_url}")

                child = WebView(
                    title=title,
                    width=width,
                    height=height,
                    debug=True,
                    context_menu=True,
                    asset_root=str(DIST_DIR),
                )
                child.load_url(load_url)
                child_windows[label] = child
                child.show(wait=False)

                logger.info(f"Child window '{label}' created successfully!")
                return {"success": True, "message": "Window created", "label": label}
            except Exception as e:
                logger.error(f"Failed to create window: {e}")
                return {"success": False, "message": str(e), "label": label}

        def close_window(self, label=""):
            logger.info(f"close_window called: {label}")
            if label in child_windows:
                try:
                    child_windows[label].close()
                    del child_windows[label]
                    return {"success": True}
                except Exception as e:
                    return {"success": False, "message": str(e)}
            return {"success": False, "message": "Window not found"}

    # Create and bind API
    api = DesktopShelfAPI()
    webview.bind_api(api)
    logger.info("API bound successfully")

    # Load the actual app
    auroraview_url = get_auroraview_entry_url("index.html")
    logger.info(f"Loading: {auroraview_url}")
    webview.load_url(auroraview_url)

    logger.info("Starting webview...")
    webview.show_blocking()

    # Cleanup
    for label, child in list(child_windows.items()):
        try:
            child.close()
        except:
            pass


if __name__ == "__main__":
    main()
