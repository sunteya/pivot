import sys
from pathlib import Path

# Ensure project root is in sys.path so 'from src.manager import ...' works
# even when flet runs this script directly from the src directory.
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import flet as ft

# Try importing from src package (Dev mode from root), otherwise fall back to local import (Packaged/Dev from src)
try:
    from src.manager import VersionManager
except ImportError:
    from manager import VersionManager


async def show_snack(page, message, color=None):
    snack = ft.SnackBar(ft.Text(message), bgcolor=color)
    page.overlay.append(snack)
    snack.open = True
    page.update()


async def main(page: ft.Page):
    page.title = "Pivot"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 800
    page.window.height = 600

    # Center window
    await page.window.center()

    # Initialize Manager
    manager = VersionManager()

    # UI Setup
    versions_grid = ft.ResponsiveRow(spacing=10, run_spacing=10)

    scroll_container = ft.Column(
        controls=[versions_grid],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=0,
    )

    async def handle_link_click(e):
        app_name = e.control.data["app"]
        folder_name = e.control.data["folder"]

        try:
            # force=True allows switching versions (overwriting existing link)
            manager.create_link(app_name, folder_name, force=True)

            await show_snack(
                page, f"Linked {app_name} -> {folder_name}", ft.Colors.GREEN
            )

            # Refresh to show updated state
            await refresh_list()

        except Exception as ex:
            await show_snack(page, f"Failed to link {app_name}: {ex}", ft.Colors.ERROR)

    async def refresh_list():
        versions_grid.controls.clear()

        try:
            groups = manager.get_grouped_versions()
        except Exception as ex:
            await show_snack(page, f"Error scanning versions: {ex}", ft.Colors.ERROR)
            return

        if not groups:
            await show_snack(page, "No versions found! 📂", ft.Colors.ORANGE)
        else:
            # Sort groups by app name
            sorted_apps = sorted(groups.keys())

            for app_name in sorted_apps:
                data = groups[app_name]
                versions = data["versions"]
                active_version = data["active_version"]

                # Sort versions descending (newest first)
                sorted_versions = sorted(versions, reverse=True)

                # Create rows for each version
                version_rows = []
                for v_folder in sorted_versions:
                    is_active = v_folder == active_version

                    # Row controls
                    row_controls = [
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE
                            if is_active
                            else ft.Icons.CIRCLE_OUTLINED,
                            color=ft.Colors.GREEN if is_active else ft.Colors.GREY_300,
                            size=16,
                        ),
                        ft.Text(
                            v_folder,
                            expand=True,
                            size=14,
                            color=ft.Colors.BLACK if is_active else ft.Colors.GREY_700,
                        ),
                    ]

                    # Action container
                    action_container = ft.Container(
                        width=80,
                        alignment=ft.Alignment(1.0, 0.0),
                    )

                    if is_active:
                        action_container.content = ft.Container(
                            content=ft.Text(
                                "Active",
                                color=ft.Colors.GREEN,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                            ),
                            padding=5,
                            border_radius=4,
                        )
                    else:
                        action_container.content = ft.IconButton(
                            icon=ft.Icons.LINK,
                            tooltip="Link this version",
                            on_click=handle_link_click,
                            data={"app": app_name, "folder": v_folder},
                            icon_size=18,
                            style=ft.ButtonStyle(
                                padding=5,
                                shape=ft.RoundedRectangleBorder(radius=4),
                            ),
                        )

                    row_controls.append(action_container)

                    version_rows.append(
                        ft.Container(
                            content=ft.Row(
                                controls=row_controls,
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=ft.Padding(left=5, top=2, right=0, bottom=2),
                            bgcolor=ft.Colors.GREEN_50 if is_active else None,
                            border_radius=4,
                            height=40,
                        )
                    )

                # Check if it's an unmanaged group (Persists only)
                if not versions:
                    # Add a special row for unmanaged version
                    link_name = data.get("link_name", app_name)

                    row_controls = [
                        ft.Icon(
                            ft.Icons.FOLDER_OPEN,
                            color=ft.Colors.ORANGE,
                            size=16,
                        ),
                        ft.Text(
                            f"Current: {link_name}",
                            expand=True,
                            size=14,
                            color=ft.Colors.ORANGE_900,
                            italic=True,
                        ),
                    ]

                    version_rows.append(
                        ft.Container(
                            content=ft.Row(
                                controls=row_controls,
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=ft.Padding(left=5, top=2, right=0, bottom=2),
                            bgcolor=ft.Colors.ORANGE_50,
                            border_radius=4,
                            height=40,
                        )
                    )

                # App Card
                card = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.APPS, size=16, color=ft.Colors.BLUE
                                    ),
                                    ft.Text(
                                        app_name, size=16, weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            f"{len(versions)} versions",
                                            size=10,
                                            color=ft.Colors.GREY,
                                        ),
                                        padding=ft.Padding(
                                            left=5, top=0, right=0, bottom=0
                                        ),
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Divider(height=5, thickness=1),
                            ft.Column(controls=version_rows, spacing=0),
                        ],
                        spacing=5,
                    ),
                    padding=10,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    bgcolor=ft.Colors.WHITE,
                    col={"xs": 12, "md": 6, "xl": 4},
                )
                versions_grid.controls.append(card)

        page.update()

    # Layout
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text("Pivot", size=30, weight=ft.FontWeight.BOLD),
                ft.Chip(
                    label=ft.Text(
                        "Dev Mode" if "dummy" in str(manager.versions_dir) else "Prod"
                    ),
                    color=ft.Colors.BLUE_200,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=20,
        bgcolor=ft.Colors.GREY_100,
    )

    page.add(header, ft.Divider(height=1, thickness=1), scroll_container)

    # Initial Load
    await refresh_list()


if __name__ == "__main__":
    ft.run(main)
