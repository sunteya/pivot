import flet as ft

from state import AppState
from ui.components import AppCard
from ui.utils import show_snack, reveal_in_explorer


class VersionGrid(ft.Column):
    def __init__(self, page: ft.Page, manager, app_state: AppState):
        self.app_page = page
        self.manager = manager
        self.app_state = app_state

        self.grid = ft.ResponsiveRow(spacing=10, run_spacing=10)

        super().__init__(
            controls=[ft.Container(content=self.grid, padding=20)],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
        )

        # Re-render when selection changes
        self.app_state.add_listener(self.update_grid_ui)

    async def on_link_version(self, app_name: str, folder_name: str):
        """Direct link action from a specific row (bypasses batch)"""
        try:
            self.manager.create_link(app_name, folder_name, force=True)

            # If this app was selected for batch, deselect it since it's now handled
            self.app_state.deselect(app_name)

            await show_snack(
                self.app_page, f"Linked {app_name} -> {folder_name}", ft.Colors.GREEN
            )
            await self.refresh_data()

        except Exception as ex:
            await show_snack(
                self.app_page, f"Failed to link {app_name}: {ex}", ft.Colors.ERROR
            )

    async def on_open_folder(self, app_name: str):
        """Opens the Persists folder for the given app."""
        if not hasattr(self, "groups") or app_name not in self.groups:
            return

        data = self.groups[app_name]
        link_name = data.get("link_name")

        if link_name:
            # Open Persists/link_name
            target = self.manager.persists_dir / link_name
            reveal_in_explorer(target)
        else:
            # Should not happen since button is hidden if unlinked, but fallback just in case
            pass

    async def refresh_data(self):
        """Full data reload from disk"""
        try:
            self.groups = self.manager.get_grouped_versions()
        except Exception as ex:
            self.groups = {}
            await show_snack(
                self.app_page, f"Error scanning versions: {ex}", ft.Colors.ERROR
            )

        self.update_grid_ui()

    def update_grid_ui(self):
        """Re-renders UI based on current data (self.groups) and selection state"""
        self.grid.controls.clear()

        if not hasattr(self, "groups") or not self.groups:
            # Just empty or not loaded yet
            pass
        else:
            sorted_apps = sorted(self.groups.keys())

            for app_name in sorted_apps:
                data = self.groups[app_name]
                card = AppCard(
                    app_name=app_name,
                    versions=data["versions"],
                    active_version=data["active_version"],
                    link_name=data.get("link_name"),
                    app_state=self.app_state,
                    on_link_version=self.on_link_version,
                    on_open_folder=self.on_open_folder,
                )
                self.grid.controls.append(card)

        self.update()
