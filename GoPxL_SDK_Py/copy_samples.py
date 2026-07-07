"""Copy bundled sample scripts to a local folder."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def bundled_samples_dir() -> Path:
    source = Path(__file__).resolve().parent / "samples"
    if not source.is_dir():
        raise FileNotFoundError(
            f"Bundled samples not found at {source}. "
            "Reinstall: pip install git+https://github.com/kevinpuklicz/GoPxL_SDK_Python.git"
        )
    return source


def copy_samples(destination: Path) -> Path:
    source = bundled_samples_dir().resolve()
    destination = destination.resolve()
    if destination == source:
        raise ValueError(
            f"Destination is the bundled samples folder ({source}). "
            "Run from another directory, for example: cd .. && python -m gopxl_sdk"
        )
    if source in destination.parents:
        raise ValueError(
            f"Destination {destination} is inside bundled samples ({source}). "
            "Choose a folder outside the SDK install path."
        )
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Copy GoPxL SDK sample scripts to a local folder.")
    parser.add_argument(
        "destination",
        nargs="?",
        default="./samples",
        help="Output folder (default: ./samples)",
    )
    args = parser.parse_args(argv)
    try:
        dest = copy_samples(Path(args.destination))
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Samples copied to {dest}")
    print(f"  cd {dest}")
    print("  python discover.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())