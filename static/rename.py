import os
from pathlib import Path


def rename_mp4_to_screen(static_dir: Path) -> None:
    """Rename every .mp4 file in the static folder to Screen.mp4."""
    mp4_files = sorted(static_dir.glob("*.mp4"), key=lambda p: p.name.lower())

    # Remove any previously generated Screen.mp4 so a later rename doesn't fail
    target = static_dir / "Screen.mp4"
    if target.exists():
        target.unlink()

    # Rename the first .mp4 file to Screen.mp4
    if mp4_files:
        source = mp4_files[0]
        source.rename(target)

    # If there are more .mp4 files, delete them to keep only the screen video
    for extra in mp4_files[1:]:
        extra.unlink()


if __name__ == "__main__":
    rename_mp4_to_screen(Path(__file__).resolve().parent)
