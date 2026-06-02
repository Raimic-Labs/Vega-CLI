"""
tools/file_writer.py — File writing utilities for Vega CLI
Handles safe file creation, directory management, and batch project writes.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────
#  Core helpers
# ─────────────────────────────────────────────

def write_file(
    path:      str,
    content:   str,
    overwrite: bool = True,
    encoding:  str  = "utf-8",
) -> Path:
    """
    Write *content* to *path*, creating parent directories as needed.

    Args:
        path:      Absolute or relative file path.
        content:   Text content to write.
        overwrite: If False, raises FileExistsError when file already exists.
        encoding:  Text encoding (default utf-8).

    Returns:
        Resolved Path of the written file.

    Raises:
        FileExistsError: If overwrite=False and the file already exists.
        OSError:         On any filesystem error.
    """
    p = Path(path).resolve()

    if not overwrite and p.exists():
        raise FileExistsError(f"File already exists: {p}")

    p.parent.mkdir(parents=True, exist_ok=True)

    p.write_text(content, encoding=encoding)
    return p


def write_project(
    base_dir:  str,
    files:     dict[str, str],
    overwrite: bool = True,
    encoding:  str  = "utf-8",
) -> list[Path]:
    """
    Write an entire project (dict of relative-path → content) to *base_dir*.

    Args:
        base_dir:  Root directory for the project (created if missing).
        files:     Mapping of relative file path → file content.
        overwrite: If False, skips files that already exist.
        encoding:  Text encoding.

    Returns:
        List of Paths of all written files.

    Raises:
        OSError: On any filesystem error.
    """
    base = Path(base_dir).resolve()
    base.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for rel_path, content in files.items():
        dest = base / rel_path
        try:
            written.append(
                write_file(str(dest), content, overwrite=overwrite, encoding=encoding)
            )
        except FileExistsError:
            continue   # skip when overwrite=False

    return written


def read_file(path: str, encoding: str = "utf-8") -> str:
    """
    Read and return the text contents of *path*.

    Args:
        path:     File path to read.
        encoding: Text encoding.

    Returns:
        File contents as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError:           On any other read error.
    """
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    return p.read_text(encoding=encoding, errors="replace")


def ensure_dir(path: str) -> Path:
    """
    Create *path* (and any parents) if it doesn't already exist.

    Args:
        path: Directory path to ensure.

    Returns:
        Resolved Path.
    """
    p = Path(path).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_filename(name: str) -> str:
    """
    Sanitise *name* so it can be used safely as a file or directory name.
    Replaces spaces and special characters with underscores.

    Args:
        name: Raw name string.

    Returns:
        Sanitised filename string.
    """
    import re
    # Keep alphanumerics, dots, hyphens, underscores
    clean = re.sub(r"[^\w.\-]", "_", name)
    # Collapse multiple underscores
    clean = re.sub(r"_+", "_", clean)
    return clean.strip("_")


def list_files(
    directory:  str,
    extensions: Optional[list[str]] = None,
    recursive:  bool = True,
) -> list[Path]:
    """
    List files in *directory*, optionally filtered by extension.

    Args:
        directory:  Directory path to search.
        extensions: List of extensions to include, e.g. ['.py', '.md'].
                    If None, all files are returned.
        recursive:  If True, walk subdirectories.

    Returns:
        Sorted list of Path objects.
    """
    base    = Path(directory)
    pattern = "**/*" if recursive else "*"
    files   = [p for p in base.glob(pattern) if p.is_file()]

    if extensions:
        exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
        files = [p for p in files if p.suffix.lower() in exts]

    return sorted(files)


def delete_file(path: str, missing_ok: bool = True) -> bool:
    """
    Delete a single file.

    Args:
        path:       File path to delete.
        missing_ok: If True, silently succeed when file doesn't exist.

    Returns:
        True if deleted, False if missing and missing_ok=True.

    Raises:
        FileNotFoundError: If missing and missing_ok=False.
    """
    p = Path(path)
    if not p.exists():
        if missing_ok:
            return False
        raise FileNotFoundError(f"Cannot delete — file not found: {p}")
    p.unlink()
    return True


def copy_file(src: str, dst: str, overwrite: bool = True) -> Path:
    """
    Copy *src* to *dst*, creating parent directories as needed.

    Args:
        src:       Source file path.
        dst:       Destination file path.
        overwrite: If False, raises FileExistsError when dst exists.

    Returns:
        Resolved destination Path.
    """
    s = Path(src)
    d = Path(dst).resolve()

    if not overwrite and d.exists():
        raise FileExistsError(f"Destination already exists: {d}")

    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(s), str(d))
    return d


def file_size_str(path: str) -> str:
    """Return a human-readable file size string for *path*."""
    size = Path(path).stat().st_size
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def count_lines(path: str, encoding: str = "utf-8") -> int:
    """Return the number of lines in a text file."""
    try:
        return sum(1 for _ in Path(path).open(encoding=encoding, errors="replace"))
    except OSError:
        return 0
