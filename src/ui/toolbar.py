import flet as ft

from state import AppState


class PivotToolbar(ft.Container):
    def __init__(
        self, page: ft.Page, app_state: AppState, on_link_action, on_select_latest
    ):
        super().__init__()
        self.app_page = page
        self.app_state = app_state
        self.on_link_action = on_link_action
        self.on_select_latest = on_select_latest

        self.padding = 10
        self.bgcolor = ft.Colors.WHITE
        self.border = ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_300))

        # Subscribe to state changes
        self.app_state.add_listener(self.update_toolbar)

        self.content = self._build_content()

    async def _handle_link_action(self, e):
        if self.on_link_action:
            await self.on_link_action()

    def _build_content(self):
        count = len(self.app_state.selected_versions)

        return ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Pivot", size=24, weight=ft.FontWeight.BOLD),
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.TextButton(
                                    "Select Latest",
                                    icon=ft.Icons.AUTO_MODE,
                                    on_click=lambda _: self.on_select_latest(),
                                    style=ft.ButtonStyle(color=ft.Colors.BLUE),
                                ),
                                ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                                ft.TextButton(
                                    "Clear",
                                    icon=ft.Icons.CLEAR_ALL,
                                    on_click=lambda _: self.app_state.clear_all(),
                                    disabled=count == 0,
                                    style=ft.ButtonStyle(color=ft.Colors.GREY),
                                ),
                            ],
                            spacing=5,
                        ),
                        ft.Container(width=20),
                        ft.FilledButton(
                            f"Link Selected ({count})",
                            icon=ft.Icons.LINK,
                            on_click=self._handle_link_action,
                            disabled=count == 0,
                            style=ft.ButtonStyle(
                                bgcolor={
                                    ft.ControlState.DEFAULT: ft.Colors.BLUE,
                                    ft.ControlState.DISABLED: ft.Colors.GREY_200,
                                },
                                color={
                                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                    ft.ControlState.DISABLED: ft.Colors.GREY_500,
                                },
                            ),
                            width=180,
                        ),
                    ],
                    spacing=0,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def update_toolbar(self):
        self.content = self._build_content()
        self.update()
