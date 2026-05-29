#!/usr/bin/env python3
"""Download Python wheel packages with dependencies for offline installation."""

import argparse
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# (platform, arch) -> pip platform tag
PLATFORM_TAG_MAP: dict[tuple[str, str], str] = {
    ("windows", "amd64"): "win_amd64",
    ("windows", "arm64"): "win_arm64",
    ("linux", "amd64"): "manylinux2014_x86_64",
    ("linux", "arm64"): "manylinux2014_aarch64",
    ("macos", "amd64"): "macosx_10_9_x86_64",
    ("macos", "arm64"): "macosx_11_0_arm64",
}

# Friendly platform labels for archive naming
PLATFORM_LABEL: dict[tuple[str, str], str] = {
    ("windows", "amd64"): "win64",
    ("windows", "arm64"): "win-arm64",
    ("linux", "amd64"): "linux-x86_64",
    ("linux", "arm64"): "linux-aarch64",
    ("macos", "amd64"): "macos-x86_64",
    ("macos", "arm64"): "macos-arm64",
}


def resolve_platform_tag(platform: str, arch: str) -> str:
    """Map platform + arch to a pip-compatible platform tag."""
    key = (platform.lower(), arch.lower())
    tag = PLATFORM_TAG_MAP.get(key)
    if tag:
        return tag
    # Fallback: construct directly (e.g., "linux_riscv64")
    return f"{platform.lower()}_{arch.lower()}"


def resolve_label(platform: str, arch: str) -> str:
    """Get a short human-readable label for the target."""
    key = (platform.lower(), arch.lower())
    return PLATFORM_LABEL.get(key, f"{platform.lower()}-{arch.lower()}")


def download_wheels(
    package_spec: str,
    platform_tag: str,
    python_version: str,
    dest_dir: Path,
) -> int:
    """Run pip download and return the number of .whl files downloaded."""
    cmd = [
        sys.executable, "-m", "pip", "download",
        package_spec,
        "--dest", str(dest_dir),
        "--only-binary", ":all:",
        "--platform", platform_tag,
        "--python-version", python_version,
        "--implementation", "cp",
    ]

    print(f"[pip] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    whl_files = list(dest_dir.glob("*.whl"))
    print(f"\nDownloaded {len(whl_files)} wheel(s):")
    for f in sorted(whl_files):
        print(f"  {f.name}")

    return len(whl_files)


def create_zip(whl_dir: Path, output_path: Path) -> int:
    """Package all .whl files in whl_dir into a zip at output_path."""
    whl_files = sorted(whl_dir.glob("*.whl"))
    if not whl_files:
        print("No .whl files to package.", file=sys.stderr)
        return 0

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for whl in whl_files:
            zf.write(whl, whl.name)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\nPackaged {len(whl_files)} wheel(s) → {output_path} ({size_mb:.1f} MB)")
    return len(whl_files)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Python wheel packages and dependencies for offline install",
    )
    parser.add_argument(
        "package",
        help="Package name (e.g., 'requests', 'numpy')",
    )
    parser.add_argument(
        "--platform", "-p",
        default="windows",
        choices=["windows", "linux", "macos"],
        help="Target platform (default: windows)",
    )
    parser.add_argument(
        "--arch", "-a",
        default="amd64",
        choices=["amd64", "arm64"],
        help="Target architecture (default: amd64)",
    )
    parser.add_argument(
        "--python-version", "-py",
        default="3.11",
        help="Target Python version (default: 3.11)",
    )
    parser.add_argument(
        "--version", "-v",
        default=None,
        help="Package version (default: latest)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output zip path (default: <package>-<platform>-py<ver>.zip in CWD)",
    )
    parser.add_argument(
        "--extra-index-url",
        default=None,
        help="Extra PyPI index URL (e.g., internal mirror)",
    )

    args = parser.parse_args()

    platform_tag = resolve_platform_tag(args.platform, args.arch)
    label = resolve_label(args.platform, args.arch)

    pkg_spec = f"{args.package}=={args.version}" if args.version else args.package

    output = args.output or f"{args.package}-{label}-py{args.python_version}.zip"
    output_path = Path(output).resolve()

    # Extra index URL handling
    if args.extra_index_url:
        os.environ.setdefault("PIP_EXTRA_INDEX_URL", args.extra_index_url)

    with tempfile.TemporaryDirectory() as tmpdir:
        wheel_dir = Path(tmpdir) / "wheels"
        wheel_dir.mkdir()

        print(f"Target: {pkg_spec}  platform={platform_tag}  python={args.python_version}\n")
        download_wheels(pkg_spec, platform_tag, args.python_version, wheel_dir)
        create_zip(wheel_dir, output_path)

    print("\nOffline install instructions:")
    print(f"  1. Copy {output_path.name} to the offline machine")
    print(f"  2. Extract: unzip {output_path.name}")
    print(f"  3. Install: pip install --no-index --find-links=. {args.package}")


if __name__ == "__main__":
    main()
