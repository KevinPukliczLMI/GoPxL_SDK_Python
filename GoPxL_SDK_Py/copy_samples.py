"""Copy bundled sample scripts to a local folder."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def _bundled_samples_dir() -> Path:
    return Path(__file__).resolve().parent / "samples"


def copy_samples(destination: Path) -> Path:
    source = _bundled_samples_dir()
    if not source.is_dir():
        raise FileNotFoundError(
            f"Bundled samples not found at {source}. "
            "Reinstall with: pip install git+https://github.com/kevinpuklicz/GoPxL_SDK_Python.git"
        )
    destination = destination.resolve()
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Copy GoPxL SDK sample scripts to a local folder.",
    )
    parser.add_argument(
        "destination",
        nargs="?",
        default="samples",
        help="Output folder (default: ./samples)",
    )
    args = parser.parse_args(argv)
    try:
        dest = copy_samples(Path(args.destination))
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Samples copied to {dest}")
    print(f"  cd {dest}")
    print("  python discover.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())