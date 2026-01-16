import asyncio
import flet as ft
from src.ui.utils import show_snack


class BatchLinkDialog:
    def __init__(self, page: ft.Page, manager, on_success_callback):
        self.page = page
        self.manager = manager
        self.on_success = on_success_callback

    async def show(self):
        try:
            groups = self.manager.get_grouped_versions()
        except Exception as ex:
            await show_snack(
                self.page, f"Error scanning versions: {ex}", ft.Colors.ERROR
            )
            return

        # Filter for unlinked apps (no active version and no existing link)
        unlinked_apps = []
        for app_name in sorted(groups.keys()):
            data = groups[app_name]
            if data["active_version"] is None and data["link_name"] is None:
                versions = data["versions"]
                if versions:
                    # Sort versions descending (newest first)
                    sorted_versions = sorted(versions, reverse=True)
                    unlinked_apps.append((app_name, sorted_versions))

        if not unlinked_apps:
            await show_snack(
                self.page, "All apps are already linked! \U0001f389", ft.Colors.GREEN
            )
            return

        # UI Components storage
        batch_controls = {}

        dialog_content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            height=400,
            width=500,
        )

        for app_name, versions in unlinked_apps:
            # Default to newest version
            default_version = versions[0]

            chk = ft.Checkbox(value=True)

            options = [ft.dropdown.Option(v) for v in versions]

            dd = ft.Dropdown(
                options=options,
                value=default_version,
                width=200,
                text_size=12,
                content_padding=5,
                height=35,
            )

            batch_controls[app_name] = {"checkbox": chk, "dropdown": dd}

            row = ft.Row(
                controls=[
                    ft.Row(
                        [chk, ft.Text(app_name, weight=ft.FontWeight.BOLD)], spacing=5
                    ),
                    dd,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            dialog_content.controls.append(row)

        def close_dialog(e=None):
            self.page.dialog.open = False
            self.page.update()

        async def execute_batch(e):
            close_dialog()
            success_count = 0
            fail_count = 0

            await show_snack(self.page, "Processing batch links...", ft.Colors.BLUE)

            for app_name, controls in batch_controls.items():
                if controls["checkbox"].value:
                    version = controls["dropdown"].value
                    try:
                        await asyncio.sleep(0.01)
                        self.manager.create_link(app_name, version, force=True)
                        success_count += 1
                    except Exception as ex:
                        print(f"Failed to link {app_name}: {ex}")
                        fail_count += 1

            if fail_count > 0:
                await show_snack(
                    self.page,
                    f"Linked {success_count} apps. Failed: {fail_count}",
                    ft.Colors.ORANGE,
                )
            else:
                await show_snack(
                    self.page,
                    f"Successfully linked {success_count} apps!",
                    ft.Colors.GREEN,
                )

            if self.on_success:
                await self.on_success()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Batch Link ({len(unlinked_apps)} found)"),
            content=dialog_content,
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton(
                    "Link Selected",
                    on_click=execute_batch,
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
