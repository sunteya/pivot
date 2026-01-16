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

    def create_link(self, app_name: str, folder_name: str) -> None:
        """
        Creates a symlink (or junction on Windows): Persists/app_name -> Versions/folder_name
        """
        src = self.versions_dir / folder_name
        dst = self.persists_dir / app_name

        if dst.exists():
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
        version_pattern = r"(?i)[-_. ]v?\d+(\.|_|\d|x|b|a)"

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
