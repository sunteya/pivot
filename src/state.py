from typing import Callable


class AppState:
    def __init__(self):
        # selected_versions: {app_name: version_folder}
        self.selected_versions: dict[str, str] = {}
        self._listeners: list[Callable] = []

    def get_selected(self, app_name: str) -> str | None:
        return self.selected_versions.get(app_name)

    def toggle(self, app_name: str, version: str):
        if self.selected_versions.get(app_name) == version:
            self.deselect(app_name)
        else:
            self.selected_versions[app_name] = version
            self._notify()

    def select(self, app_name: str, version: str):
        """Force select a specific version (idempotent)"""
        if self.selected_versions.get(app_name) != version:
            self.selected_versions[app_name] = version
            self._notify()

    def deselect(self, app_name: str):
        if app_name in self.selected_versions:
            del self.selected_versions[app_name]
            self._notify()

    def clear_all(self):
        self.selected_versions.clear()
        self._notify()

    def add_listener(self, callback: Callable):
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self):
        for callback in self._listeners:
            callback()
