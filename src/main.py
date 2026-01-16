import flet as ft
from src.manager import VersionManager


def show_snack(page, message, color=None):
    snack = ft.SnackBar(ft.Text(message), bgcolor=color)
    page.overlay.append(snack)
    snack.open = True
    page.update()


def main(page: ft.Page):
    page.title = "Pivot"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 800
    page.window.height = 600

    # Initialize Manager
    # In a larger app, this might be a singleton or injected dependency
    manager = VersionManager()

    # UI Components
    versions_list = ft.ListView(expand=1, spacing=10, padding=20)

    def refresh_list():
        versions_list.controls.clear()

        try:
            unlinked = manager.get_unlinked_versions()
        except Exception as ex:
            show_snack(page, f"Error scanning versions: {ex}", ft.Colors.ERROR)
            return

        if not unlinked:
            show_snack(page, "All versions are linked! 🎉", ft.Colors.GREEN)
        else:
            for app_name, folder_name in unlinked:
                # Create a ListTile for each unlinked version
                item = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.FOLDER, color=ft.Colors.BLUE_GREY),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        app_name, weight=ft.FontWeight.BOLD, size=16
                                    ),
                                    ft.Text(folder_name, size=12, color=ft.Colors.GREY),
                                ],
                                expand=True,
                                spacing=2,
                            ),
                            ft.FilledButton(
                                "Link",
                                icon=ft.Icons.LINK,
                                on_click=handle_link_click,
                                data={"app": app_name, "folder": folder_name},
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=10,
                    border=ft.Border(
                        top=ft.BorderSide(1, ft.Colors.GREY_400),
                        bottom=ft.BorderSide(1, ft.Colors.GREY_400),
                        left=ft.BorderSide(1, ft.Colors.GREY_400),
                        right=ft.BorderSide(1, ft.Colors.GREY_400),
                    ),
                    border_radius=8,
                    bgcolor=ft.Colors.WHITE,
                )
                versions_list.controls.append(item)

        page.update()

    def handle_link_click(e):
        app_name = e.control.data["app"]
        folder_name = e.control.data["folder"]

        try:
            manager.create_link(app_name, folder_name)

            show_snack(page, f"Linked {app_name} successfully!")

            # Refresh to show updated state
            refresh_list()

        except Exception as ex:
            show_snack(page, f"Failed to link {app_name}: {ex}", ft.Colors.ERROR)

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

    page.add(header, ft.Divider(height=1, thickness=1), versions_list)

    # Initial Load
    refresh_list()


if __name__ == "__main__":
    ft.run(main)
