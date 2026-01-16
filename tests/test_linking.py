import shutil
from src.manager import VersionManager
from src.config import PERSISTS_DIR, VERSIONS_DIR


def test_linking():
    # Setup
    vm = VersionManager()

    # Ensure clean state for test
    test_app = "TestApp"
    test_folder = "TestApp-1.0.0"

    # Create fake version
    (VERSIONS_DIR / test_folder).mkdir(exist_ok=True)

    # Ensure no existing link
    link_path = PERSISTS_DIR / test_app
    if link_path.exists():
        if link_path.is_symlink():
            link_path.unlink()
        else:
            shutil.rmtree(link_path)

    print(f"Testing linking {test_folder} -> {test_app}...")

    # Execute
    vm.create_link(test_app, test_folder)

    # Verify
    if link_path.exists():
        print(f"SUCCESS: Link created at {link_path}")

        # Check if it's a symlink or junction (both are reparse points)
        # Note: is_symlink() might be False for junctions on some python versions
        is_sym = link_path.is_symlink()
        print(f"       is_symlink(): {is_sym}")

        # For validation, we just want to ensure it resolves to the right place
        resolved = link_path.resolve()
        expected = (VERSIONS_DIR / test_folder).resolve()

        print(f"       Resolves to: {resolved}")

        if resolved == expected:
            print("       Target path matches exactly.")
        else:
            print(f"       WARNING: Target {resolved} != {expected}")
    else:
        print("FAILURE: Link path does not exist.")

    # Cleanup
    link_path.unlink()
    (VERSIONS_DIR / test_folder).rmdir()


if __name__ == "__main__":
    test_linking()
