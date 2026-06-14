#!/usr/bin/env python3
"""Ask CodeKit to process source files and verify generated output changed.

By default this uses CodeKit's AppleScript `process file at path` command. The
older pulse method is still available as a fallback: add one newline, wait a
moment, then restore the original file bytes.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


DEFAULT_BATCH_SIZE = 4
DEFAULT_HOLD_SECONDS = 6.0
DEFAULT_WAIT_SECONDS = 7.0
EXCLUDED_DIRS = {".git", ".translation-cache", "assets", "en"}
CODEKIT_APP = Path("/Applications/CodeKit.app")


def path_is_partial(path: Path) -> bool:
    return path.name.startswith("_")


def path_is_excluded(path: Path, include_partials: bool) -> bool:
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return True
    if not include_partials and path_is_partial(path):
        return True
    return False


def discover_kit_files(root: Path, include_partials: bool) -> List[Path]:
    files = []
    for path in root.rglob("*.kit"):
        if path_is_excluded(path.relative_to(root), include_partials):
            continue
        files.append(path)
    return sorted(files)


def expand_paths(paths: Iterable[str], root: Path, include_partials: bool) -> List[Path]:
    expanded: List[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_absolute():
            path = root / path
        if path.is_dir():
            expanded.extend(discover_kit_files(path, include_partials))
        elif path.suffix == ".kit":
            expanded.append(path)
        else:
            raise ValueError(f"Not a .kit file or directory: {raw_path}")
    return sorted(dict.fromkeys(path.resolve() for path in expanded))


def generated_html_path(path: Path) -> Path:
    return path.with_suffix(".html")


def mtime(path: Path) -> Optional[float]:
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return None


def pulsed_text(original: str) -> str:
    newline = "\r\n" if "\r\n" in original else "\n"
    pulsed = original + newline
    if pulsed == original:
        pulsed = original + "\n"
    return pulsed


def write_pulse(path: Path) -> Tuple[str, str]:
    original = path.read_text(encoding="utf-8")
    pulsed = pulsed_text(original)
    path.write_text(pulsed, encoding="utf-8")
    return original, pulsed


def restore_pulse(path: Path, original: str, pulsed: str) -> Tuple[bool, str]:
    current = path.read_text(encoding="utf-8")
    if current != pulsed:
        return False, "changed while pulsed; left current file untouched"

    path.write_text(original, encoding="utf-8")
    return True, "restored"


def chunks(items: List[Path], size: int) -> Iterable[List[Path]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def applescript_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def applescript_available() -> bool:
    return CODEKIT_APP.exists() and shutil.which("osascript") is not None


def process_file_with_codekit(path: Path) -> Tuple[bool, str]:
    script = f'tell application "CodeKit" to process file at path "{applescript_string(str(path))}"'
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0:
        return False, output or f"osascript exited with {result.returncode}"
    if output and output != "0":
        return False, f"CodeKit returned {output}"
    return True, "queued"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        help="Specific .kit files or directories to pulse. Defaults to all page .kit files.",
    )
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--hold", type=float, default=DEFAULT_HOLD_SECONDS, help="Seconds before restoring each file.")
    parser.add_argument("--wait", type=float, default=DEFAULT_WAIT_SECONDS, help="Seconds to wait after each batch.")
    parser.add_argument(
        "--method",
        choices=("auto", "applescript", "pulse"),
        default="auto",
        help="How to ask CodeKit to rebuild. Auto prefers CodeKit AppleScript and falls back to pulse.",
    )
    parser.add_argument("--include-partials", action="store_true", help="Also pulse underscore partials.")
    parser.add_argument("--no-verify", action="store_true", help="Do not check generated .html mtimes.")
    parser.add_argument("--dry-run", action="store_true", help="List files without pulsing them.")
    args = parser.parse_args()

    if args.batch_size < 1:
        raise SystemExit("--batch-size must be at least 1")
    if args.hold < 0:
        raise SystemExit("--hold must be 0 or greater")
    if args.wait < 0:
        raise SystemExit("--wait must be 0 or greater")

    root = Path(".").resolve()
    files = (
        expand_paths(args.paths, root, args.include_partials)
        if args.paths
        else discover_kit_files(root, args.include_partials)
    )

    if not files:
        print("No .kit files found.")
        return 0

    method = args.method
    if method == "auto":
        method = "applescript" if applescript_available() else "pulse"
    if method == "applescript" and not applescript_available():
        print("CodeKit AppleScript support is not available; falling back to pulse.")
        method = "pulse"

    print(f"CodeKit wake plan: {len(files)} .kit file(s), batch size {args.batch_size}, method {method}.")
    for path in files:
        print(f"- {path.relative_to(root)}")

    if args.dry_run:
        return 0

    before = {path: mtime(generated_html_path(path)) for path in files}
    warnings: List[str] = []

    for batch_number, batch in enumerate(chunks(files, args.batch_size), start=1):
        if method == "applescript":
            print(f"Processing batch {batch_number} with CodeKit: {len(batch)} file(s)...", flush=True)
            for path in batch:
                ok, message = process_file_with_codekit(path)
                if not ok:
                    warnings.append(f"{path.relative_to(root)}: {message}")
        else:
            print(f"Pulsing batch {batch_number}: {len(batch)} file(s)...", flush=True)
            pulsed_files: List[Tuple[Path, str, str]] = []
            for path in batch:
                original, pulsed = write_pulse(path)
                pulsed_files.append((path, original, pulsed))
            if args.hold:
                print(f"Holding pulse for {args.hold:g}s...", flush=True)
                time.sleep(args.hold)
            for path, original, pulsed in pulsed_files:
                ok, message = restore_pulse(path, original, pulsed)
                if not ok:
                    warnings.append(f"{path.relative_to(root)}: {message}")
        if args.wait:
            print(f"Waiting {args.wait:g}s for CodeKit...", flush=True)
            time.sleep(args.wait)

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")

    if args.no_verify:
        return 0

    updated: List[Path] = []
    stale: List[Path] = []
    missing: List[Path] = []

    for path in files:
        generated = generated_html_path(path)
        after = mtime(generated)
        if after is None:
            missing.append(path)
        elif before[path] is None or after > before[path]:
            updated.append(path)
        else:
            stale.append(path)

    print(f"Generated HTML updated: {len(updated)}")
    print(f"Generated HTML unchanged: {len(stale)}")
    if missing:
        print(f"Generated HTML missing: {len(missing)}")

    if stale:
        print("CodeKit may not be running or did not process every page:")
        for path in stale[:12]:
            print(f"- {generated_html_path(path).relative_to(root)}")
        if len(stale) > 12:
            print(f"...and {len(stale) - 12} more.")
        return 2

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except ValueError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
