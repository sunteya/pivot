import os
import re
import shutil
from pathlib import Path

import subprocess
import platform

# Import from local config
# Note: when running this file directly as script, imports might fail without sys.path hack
# but we will run it via 'uv run python -m src.manager' or similar.
try:
    from src.config import VERSIONS_DIR, PERSISTS_DIR
except ImportError:
    # Fallback for direct execution testing
    from config import VERSIONS_DIR, PERSISTS_DIR


class VersionManager:
    def __init__(self):
        self.versions_dir = VERSIONS_DIR
        self.persists_dir = PERSISTS_DIR

    def scan_versions(self) -> list[str]:
        """Returns sorted list of directory names in Versions/."""
        if not self.versions_dir.exists():
            return []
        return sorted([d.name for d in self.versions_dir.iterdir() if d.is_dir()])

    def scan_persisted(self) -> list[str]:
        """Returns list of names in Persists/ (symlinks or dirs)."""
        if not self.persists_dir.exists():
            return []
        return [d.name for d in self.persists_dir.iterdir()]

    def resolve_link_target(self, link_path: Path) -> Path | None:
        """
        Resolves the target of a symlink or junction.
        Returns absolute Path to target if successful, else None.
        """
        try:
            if link_path.is_symlink():
                target = link_path.readlink()
                if not target.is_absolute():
                    target = link_path.parent / target
                return target.resolve()

            # Python 3.10+ readlink supports junctions
            if link_path.exists():
                try:
                    target = link_path.readlink()
                    if not target.is_absolute():
                        target = link_path.parent / target
                    return target.resolve()
                except OSError:
                    pass
            return None
        except OSError:
            return None

    def get_grouped_versions(self) -> dict[str, dict]:
        """
        Returns a dictionary grouping versions by app name.
        Structure:
        {
            "AppName": {
                "versions": ["v1", "v2"],
                "active_version": "v1" | None,  # The folder name that is currently linked
                "link_name": "AppName" | None   # The name of the link in Persists
            }
        }
        """
        groups = {}
        version_to_link = {}
        extracted_root_to_link_name = {}

        # Track which Persists items are actually managed versions
        managed_links = set()

        # 1. Analyze Persists to establish Naming Priority
        if self.persists_dir.exists():
            for link_path in self.persists_dir.iterdir():
                target = self.resolve_link_target(link_path)
                if target:
                    # Check if target is inside Versions
                    # resolve() returns absolute path.
                    # We need to check if it's relative to self.versions_dir
                    try:
                        # Ensure both are resolved to avoid symlink/casing mismatches in parents
                        # But self.versions_dir might not be fully resolved if Config doesn't do it.
                        # target is already resolved() in resolve_link_target.

                        # Use resolve() on versions_dir to be safe
                        versions_root = self.versions_dir.resolve()

                        # Handle Windows Long Path prefix (\\?\) mismatch
                        # target might have it, versions_root might not
                        target_str = str(target)
                        root_str = str(versions_root)

                        if target_str.startswith("\\\\?\\"):
                            target_str = target_str[4:]
                            target = Path(target_str)

                        if root_str.startswith("\\\\?\\"):
                            root_str = root_str[4:]
                            versions_root = Path(root_str)

                        relative_target = target.relative_to(versions_root)
                        # It is a version!
                        folder_name = relative_target.parts[
                            0
                        ]  # Get the top-level folder name

                        link_name = link_path.name
                        version_to_link[folder_name] = link_name

                        managed_links.add(link_name)

                        # Establish mapping: RootName -> LinkName
                        root = self.extract_app_name(folder_name)
                        # We prefer the link name as the group name
                        extracted_root_to_link_name[root] = link_name

                    except ValueError:
                        # Target is not in Versions dir, ignore
                        pass

        # 2. Group all available versions
        for folder_name in self.scan_versions():
            root = self.extract_app_name(folder_name)

            # Determine Group Name: Use Link Name if available for this root, else Root Name
            group_name = extracted_root_to_link_name.get(root, root)

            if group_name not in groups:
                groups[group_name] = {
                    "versions": [],
                    "active_version": None,
                    "link_name": None,
                }
            groups[group_name]["versions"].append(folder_name)

            # Check if this specific version is the active one
            if folder_name in version_to_link:
                groups[group_name]["active_version"] = folder_name
                groups[group_name]["link_name"] = version_to_link[folder_name]

        # 3. Add unmanaged/external Persists items
        if self.persists_dir.exists():
            for link_path in self.persists_dir.iterdir():
                if link_path.name not in managed_links:
                    # This is either a regular directory or a link pointing elsewhere
                    # We add it as a group with no versions
                    group_name = link_path.name

                    if group_name not in groups:
                        groups[group_name] = {
                            "versions": [],
                            "active_version": None,
                            "link_name": group_name,
                        }
                    else:
                        # Ensure link_name is set if it wasn't
                        if groups[group_name]["link_name"] is None:
                            groups[group_name]["link_name"] = group_name

        return groups

    def get_unlinked_versions(self) -> list[tuple[str, str]]:
        """
        Returns a list of (App Name, Original Folder Name) for items
        that do not exist in Persists.
        """
        all_versions = self.scan_versions()
        persisted = set(self.scan_persisted())

        unlinked = []
        for folder_name in all_versions:
            app_name = self.extract_app_name(folder_name)
            # logic: if a link/folder with 'app_name' exists in Persists,
            # we consider it "linked" (managed).
            if app_name not in persisted:
                unlinked.append((app_name, folder_name))

        return unlinked

    def create_link(self, app_name: str, folder_name: str, force: bool = False) -> None:
        """
        Creates a symlink (or junction on Windows): Persists/app_name -> Versions/folder_name
        """
        src = self.versions_dir / folder_name
        dst = self.persists_dir / app_name

        if dst.exists() or dst.is_symlink():
            if force:
                if dst.is_symlink() or dst.is_file():
                    dst.unlink()
                else:
                    # Directory or Junction
                    try:
                        dst.rmdir()  # Works for Junctions and empty dirs
                    except OSError:
                        shutil.rmtree(dst)  # Non-empty directory
            else:
                raise FileExistsError(f"Target {dst} already exists.")

        # Create Symlink
        # target_is_directory=True is crucial for Windows
        try:
            os.symlink(src, dst, target_is_directory=True)
        except OSError as e:
            # Check for Windows Privilege Error (1314)
            if e.winerror == 1314 and platform.system() == "Windows":
                # Fallback to Junction
                self._create_junction(src, dst)
            else:
                raise

    def _create_junction(self, src: Path, dst: Path) -> None:
        """
        Creates a Windows Directory Junction using mklink /J.
        Does not require Admin privileges.
        """
        # mklink /J Link Target
        cmd = ["cmd", "/c", "mklink", "/J", str(dst), str(src)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise OSError(f"Failed to create junction: {result.stderr}")

    @staticmethod
    def extract_app_name(folder_name: str) -> str:
        """
        Heuristic to extract clean app name from versioned folder name.
        Strategies:
        1. Find version patterns (digits, vX.X, x86/64).
        2. Split at the first occurrence of such pattern.
        3. Clean trailing separators.
        """
        name = folder_name

        # Regex explanation:
        # We look for the *start* of the version/arch info.
        # delimiters: [-_ .] or end of previous word
        # patterns:
        #  - v\d : v1.2
        #  - \d+\.\d+ : 1.2, 5.40.2
        #  - x86, x64, win32, win64, portable
        #  - \d{3,} : 243, 20231118 (dates or build numbers)

        # We generally want to split BEFORE these matches, consuming the separator.

        # Specific match for arch/platform keywords that usually signal end of name
        # case insensitive
        platform_pattern = r"(?i)[-_. ](x86|x64|win\d+|portable|beta|rc\d+)"

        # Match version numbers: separator + digit + dot/end
        # e.g. "-1.0", " 2.0"
        version_pattern = r"(?i)[-_. ]v?\d+(\.|_|\d|x|b|a|$)"

        # Match just a number block at the end if strict (like FanControl_243)
        # separator + digit+
        tail_number_pattern = r"[-_. ]\d+$"

        # Special case: FastCopy5.8.1 (No separator)
        # Look for transition from Letter to Number, BUT strictly if the number
        # looks like a version (has a dot, or is 'v'+digit, or is long).
        # We don't want to split "Proxmark3GUI" at '3'.

        # Look for: Letter -> (Digit + Dot) OR (Digit + v) OR (Digit{2,})
        # FastCopy5.8 -> 'y' followed by '5.' -> match
        # SE4011 -> 'E' followed by '4011' -> match
        # Proxmark3GUI -> 'k' followed by '3G' -> NO match
        embedded_version_pattern = r"(?<=[a-zA-Z])(?=v?\d+(\.|_|\d))"

        # 1. Try to find platform indicators (often most reliable separators)
        # We want the earliest match

        matches = []

        for pat in [platform_pattern, version_pattern, tail_number_pattern]:
            m = re.search(pat, name)
            if m:
                matches.append(m.start())

        # If we have "LetterNumber" split, add that index
        m_embed = re.search(embedded_version_pattern, name)
        if m_embed:
            matches.append(m_embed.start())

        if matches:
            # Cut at the earliest match
            cutoff = min(matches)
            # If cutoff is 0 (starts with version?), that's weird, but handle it.
            if cutoff > 0:
                name = name[:cutoff]

        # Clean trailing separators
        name = name.rstrip("-_ .")

        return name


if __name__ == "__main__":
    # Test block
    test_folders = [
        "AIMP-5.40.2655",
        "MPC-HC.2.5.3.x64",
        "copyq-7.1.0",
        "Bandizip-7.40",
        "OrcaSlicer_Windows_V2.3.1_portable",
        "cursor-0.46.9",
        "ChameleonUltraGUI 1.1.2",
        "Proxmark3GUI V0.2.8-win64-rrg_other-v4.16717",
        "imFile-1.1.2-win",
        "Everything-1.4.1.1026.x64",
        "PrusaSlicer 2.6.0",
        "mkvtoolnix-64-bit-82.0",
        "ExplorerTabUtility-1.3.0",
        "Q-Dir-11.82",
        "mpv-x86_64-v3-20250404-git-0757185",
        "FanControl_243",
        "RemoteBaiduDisk-20231118",
        "openscad-2021.01",
        "FastCopy5.8.1_x64",
        "RemoteThunder-2025-04-20",
        "renamer-7.7",
        "Geek-Uninstaller-1.5.2.165",
        "SE4011",
        "spacesniffer_2_0_5_18_x64",
        "ImageGlass_9.1.8.723_x64",
        "ShareX-18.0.1-portable",
        "tinyMediaManager-family-5.1.5",
        "LocalSend-1.15.4-windows-x86-64",
        "TrafficMonitor_V1.85.1_x64",
        "tinyMediaManager-person-5",
        "MPC-BE.1.7.0.x64",
        "VSCodium-win32-x64-1.95.3.24321",
        "upscayl-2.11.5-win",
    ]

    vm = VersionManager()
    print(f"{'ORIGINAL':<50} | {'EXTRACTED':<30}")
    print("-" * 85)
    for f in test_folders:
        extracted = vm.extract_app_name(f)
        print(f"{f:<50} | {extracted:<30}")
