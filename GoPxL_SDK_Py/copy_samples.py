"""Copy bundled sample scripts to a local folder."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from importlib import resources
from pathlib import Path
from typing import Iterator

GITHUB_REPO = "https://github.com/kevinpuklicz/GoPxL_SDK_Python.git"
GITHUB_SAMPLES_SUBPATH = Path("GoPxL_SDK_Py") / "samples"


def _local_samples_dir() -> Path | None:
    local = Path(__file__).resolve().parent / "samples"
    return local if local.is_dir() else None


def _iter_packaged_samples() -> Iterator[tuple[Path, bytes]]:
    root = resources.files("gopxl_sdk") / "samples"
    for item in root.rglob("*.py"):
        rel = item.relative_to(root)
        yield Path(rel), item.read_bytes()


def _copy_tree(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )


def _guard_destination(source: Path, destination: Path) -> None:
    if destination == source:
        raise ValueError(
            f"Destination is the bundled samples folder ({source}). "
            "Run from another directory, for example: cd .. && python -m gopxl"
        )
    if source in destination.parents:
        raise ValueError(
            f"Destination {destination} is inside bundled samples ({source}). "
            "Choose a folder outside the SDK install path."
        )


def copy_samples_from_github(destination: Path) -> Path:
    destination = destination.resolve()
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0

    with tempfile.TemporaryDirectory(prefix="gopxl_samples_") as tmp:
        repo_dir = Path(tmp) / "GoPxL_SDK_Python"
        result = subprocess.run(
            ["git", "clone", "--depth", "1", GITHUB_REPO, str(repo_dir)],
            capture_output=True,
            text=True,
            creationflags=creationflags,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "git clone failed").strip()
            raise FileNotFoundError(
                f"Could not clone samples from GitHub ({GITHUB_REPO}).\n{detail}"
            )

        source = (repo_dir / GITHUB_SAMPLES_SUBPATH).resolve()
        if not source.is_dir():
            raise FileNotFoundError(
                f"Samples folder not found in cloned repo at {GITHUB_SAMPLES_SUBPATH.as_posix()}"
            )

        _copy_tree(source, destination)

    return destination


def copy_samples(destination: Path, *, from_github: bool = False) -> Path:
    destination = destination.resolve()

    if from_github:
        return copy_samples_from_github(destination)

    local = _local_samples_dir()
    if local is not None:
        source = local.resolve()
        _guard_destination(source, destination)
        _copy_tree(source, destination)
        return destination

    destination.mkdir(parents=True, exist_ok=True)
    try:
        files = list(_iter_packaged_samples())
    except (FileNotFoundError, ModuleNotFoundError, TypeError) as exc:
        raise FileNotFoundError(
            "Bundled samples not found. Try: python -m gopxl --from-github"
        ) from exc
    if not files:
        raise FileNotFoundError(
            "Bundled samples not found in package data. Try: python -m gopxl --from-github"
        )
    for rel, data in files:
        out = destination / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Copy GoPxL SDK sample scripts to a local folder.")
    parser.add_argument(
        "destination",
        nargs="?",
        default="./samples",
        help="Output folder (default: ./samples)",
    )
    parser.add_argument(
        "--from-github",
        action="store_true",
        help="Clone the GitHub repo (default branch, depth 1) and copy GoPxL_SDK_Py/samples",
    )
    args = parser.parse_args(argv)
    try:
        dest = copy_samples(Path(args.destination), from_github=args.from_github)
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Samples copied to {dest}")
    print(f"  cd {dest}")
    print("  python discover.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())