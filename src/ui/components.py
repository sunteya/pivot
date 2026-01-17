import flet as ft

from state import AppState


class VersionRow(ft.Container):
    def __init__(
        self,
        app_name: str,
        version: str,
        is_active: bool,
        is_selected: bool,
        on_toggle_select,
        on_link_click,
    ):
        super().__init__()
        self.app_name = app_name
        self.version = version
        self.is_active = is_active
        self.is_selected = is_selected

        # Interaction logic
        self.on_click = on_toggle_select if not is_active else None
        self.border_radius = 4
        self.padding = ft.Padding(left=5, top=5, right=5, bottom=5)
        self.height = 40

        # Styling based on state
        if is_active:
            self.bgcolor = None  # Transparent for active
        elif is_selected:
            self.bgcolor = ft.Colors.BLUE_50
        else:
            self.bgcolor = None

        self.content = self._build_content(on_link_click)

    def _build_content(self, on_link_click):
        # Left Indicator
        if self.is_active:
            # Simple checkmark for active version (neutral color, no circle)
            left_icon = ft.Icon(ft.Icons.CHECK, size=16, color=ft.Colors.GREY_400)
        elif self.is_selected:
            left_icon = ft.Icon(
                ft.Icons.RADIO_BUTTON_CHECKED, size=16, color=ft.Colors.BLUE
            )
        else:
            left_icon = ft.Icon(
                ft.Icons.RADIO_BUTTON_UNCHECKED, size=16, color=ft.Colors.GREY_400
            )

        # Right Action/Status
        right_content: ft.Control
        if self.is_active:
            right_content = ft.Row(
                controls=[
                    ft.Text(
                        "Active",
                        size=12,
                        color=ft.Colors.GREEN,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                spacing=5,
            )
        else:
            # Unlinked version
            # Show link button. Clicking this should link IMMEDIATELY.
            right_content = ft.IconButton(
                icon=ft.Icons.LINK,
                tooltip="Link immediately",
                on_click=on_link_click,
                data=self.version,
                icon_size=18,
                icon_color=ft.Colors.GREY_500,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=4),
                ),
            )

        return ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        left_icon,
                        ft.Text(
                            self.version,
                            size=14,
                            color=ft.Colors.BLACK
                            if (self.is_active or self.is_selected)
                            else ft.Colors.GREY_700,
                            weight=ft.FontWeight.NORMAL,
                        ),
                    ],
                    spacing=10,
                ),
                right_content,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )


class AppCard(ft.Container):
    def __init__(
        self,
        app_name: str,
        versions: list[str],
        active_version: str | None,
        link_name: str | None,
        app_state: AppState,
        on_link_version,
        on_open_folder=None,
    ):
        super().__init__()
        self.app_name = app_name
        self.versions = versions
        self.active_version = active_version
        self.link_name = link_name
        self.app_state = app_state
        self.on_link_version = on_link_version
        self.on_open_folder = on_open_folder

        self.padding = 10
        self.border = ft.Border.all(1, ft.Colors.GREY_300)
        self.border_radius = 8
        self.bgcolor = ft.Colors.WHITE
        self.col = {"xs": 12, "md": 6, "xl": 4}

        self.content = self._build_content()

    async def _handle_link_click(self, e):
        version = e.control.data
        if self.on_link_version:
            await self.on_link_version(self.app_name, version)

    async def _handle_folder_click(self, e):
        if self.on_open_folder:
            await self.on_open_folder(self.app_name)

    def _build_content(self):
        # Header Parts
        header_left = ft.Row(
            controls=[
                ft.Icon(ft.Icons.APPS, size=16, color=ft.Colors.BLUE),
                ft.Text(self.app_name, size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(
                        f"{len(self.versions)} versions", size=10, color=ft.Colors.GREY
                    ),
                    padding=ft.Padding(left=5, top=0, right=0, bottom=0),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Header Right (Folder Icon if linked)
        header_right = ft.Container()  # Empty by default
        if self.link_name:
            header_right = ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.FOLDER_OPEN,
                    tooltip="Open installation folder",
                    on_click=self._handle_folder_click,
                    icon_size=18,
                    icon_color=ft.Colors.GREY_600,
                    style=ft.ButtonStyle(padding=0),
                    width=24,
                    height=24,
                ),
                margin=ft.margin.only(right=4),
            )

        # Combine Header
        header = ft.Container(
            content=ft.Row(
                controls=[header_left, header_right],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=30,  # Fixed height to ensure consistency with or without button
        )

        rows: list[ft.Control] = []

        # Sort versions descending
        sorted_versions = sorted(self.versions, reverse=True)

        if not self.versions:
            # Empty state
            rows.append(
                ft.Container(
                    content=ft.Text(
                        "No versions available", italic=True, color=ft.Colors.GREY_500
                    ),
                    padding=10,
                    alignment=ft.Alignment(0, 0),
                )
            )
        else:
            for v in sorted_versions:
                is_active = v == self.active_version
                is_selected = self.app_state.get_selected(self.app_name) == v

                rows.append(
                    VersionRow(
                        app_name=self.app_name,
                        version=v,
                        is_active=is_active,
                        is_selected=is_selected,
                        on_toggle_select=lambda e, v=v: self.app_state.toggle(
                            self.app_name, v
                        ),
                        on_link_click=self._handle_link_click,
                    )
                )

        return ft.Column(
            controls=[
                header,
                ft.Divider(height=5, thickness=1),
                ft.Column(controls=rows, spacing=0),
            ],
            spacing=5,
        )
