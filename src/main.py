import sys
import asyncio
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import flet as ft

try:
    from src.manager import VersionManager
    from src.state import AppState
    from src.ui.toolbar import PivotToolbar
    from src.ui.version_grid import VersionGrid
    from src.ui.utils import show_snack
except ImportError:
    from manager import VersionManager
    from state import AppState
    from ui.toolbar import PivotToolbar
    from ui.version_grid import VersionGrid
    from ui.utils import show_snack


async def main(page: ft.Page):
    page.title = "Pivot"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1000
    page.window.height = 700
    page.padding = 0

    # Initialize Core Objects
    manager = VersionManager()
    app_state = AppState()

    # Center window
    await page.window.center()

    # -- Actions --

    async def execute_batch_link():
        """Iterate through selected versions and link them."""
        # Get snapshot of tasks to avoid modification issues during iteration
        tasks = list(app_state.selected_versions.items())

        if not tasks:
            return

        success_count = 0
        fail_count = 0

        await show_snack(page, "Processing batch links...", ft.Colors.BLUE)

        for app_name, version in tasks:
            try:
                # Small delay for UI responsiveness
                await asyncio.sleep(0.01)
                manager.create_link(app_name, version, force=True)
                success_count += 1
            except Exception as ex:
                print(f"Failed to link {app_name}: {ex}")
                fail_count += 1

        # Clear selection after processing
        app_state.clear_all()

        # Refresh Data
        await versions_grid.refresh_data()

        if fail_count > 0:
            await show_snack(
                page, f"Linked {success_count}. Failed: {fail_count}", ft.Colors.ORANGE
            )
        else:
            await show_snack(
                page, f"Successfully linked {success_count} apps!", ft.Colors.GREEN
            )

    def select_latest_available():
        """Selects the newest version for all apps where the newest is not currently active."""
        if not hasattr(versions_grid, "groups"):
            return

        for app_name, data in versions_grid.groups.items():
            versions = data["versions"]
            if not versions:
                continue

            # Get newest (sort descending)
            newest = sorted(versions, reverse=True)[0]

            # Select if the newest is NOT the currently active one
            if data["active_version"] != newest:
                app_state.select(app_name, newest)

    # -- Components --

    versions_grid = VersionGrid(page, manager, app_state)

    toolbar = PivotToolbar(
        page,
        app_state,
        on_link_action=execute_batch_link,
        on_select_latest=select_latest_available,
    )

    # -- Layout --

    layout = ft.Column(
        controls=[toolbar, ft.Divider(height=1, thickness=1), versions_grid],
        spacing=0,
        expand=True,
    )

    page.add(layout)

    # Initial Load
    await versions_grid.refresh_data()


if __name__ == "__main__":
    ft.run(main)
