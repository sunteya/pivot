import flet as ft
import subprocess
import platform
from pathlib import Path


async def show_snack(page: ft.Page, message: str, color: str | None = None):
    snack = ft.SnackBar(ft.Text(message), bgcolor=color)
    page.overlay.append(snack)
    snack.open = True
    page.update()


def reveal_in_explorer(path: Path):
    """
    Opens the file explorer and selects the specified path.
    If path is a directory, it opens the parent and selects the directory.
    """
    try:
        if platform.system() == "Windows":
            # Windows: explorer /select,"path"
            subprocess.Popen(["explorer", "/select,", str(path)])
        elif platform.system() == "Darwin":
            # macOS: open -R path
            subprocess.Popen(["open", "-R", str(path)])
        else:
            # Linux/Other: just open the parent directory
            subprocess.Popen(["xdg-open", str(path.parent)])
    except Exception as e:
        print(f"Failed to reveal path {path}: {e}")
