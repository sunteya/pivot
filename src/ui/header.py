import flet as ft
from typing import Callable


def create_header(manager, on_batch_click: Callable):
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Pivot", size=30, weight=ft.FontWeight.BOLD),
                        ft.Chip(
                            label=ft.Text(
                                "Dev Mode"
                                if "dummy" in str(manager.versions_dir)
                                else "Prod"
                            ),
                            color=ft.Colors.BLUE_200,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.ElevatedButton(
                    "Batch Link",
                    icon=ft.Icons.LIBRARY_ADD_CHECK,
                    on_click=on_batch_click,
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=20,
        bgcolor=ft.Colors.GREY_100,
    )
