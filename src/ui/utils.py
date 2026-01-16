import flet as ft


async def show_snack(page: ft.Page, message: str, color: str = None):
    snack = ft.SnackBar(ft.Text(message), bgcolor=color)
    page.overlay.append(snack)
    snack.open = True
    page.update()
