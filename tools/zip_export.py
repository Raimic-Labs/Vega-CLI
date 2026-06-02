"""
tools/zip_export.py — ZIP export utility for Vega CLI
Creates distributable ZIP archives of generated projects.
"""

from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────
#  Default ignore patterns
# ─────────────────────────────────────────────

DEFAULT_IGNORE: set[str] = {
    # Python
    "__pycache__", "*.pyc", "*.pyo", ".pytest_cache",
    "*.egg-info", "dist", "build", ".eggs",
    # Virtual envs
    "venv", ".venv", "env", ".env",
    # Node
    "node_modules", ".npm",
    # VCS
    ".git", ".svn", ".hg",
    # IDE
    ".idea", ".vscode", "*.swp", "*.swo",
    # OS
    ".DS_Store", "Thumbs.db", "desktop.ini",
    # Vega
    "*.zip",
}


def _should_ignore(path: Path, patterns: set[str]) -> bool:
    """Return True if *path* matches any ignore pattern."""
    import fnmatch
    name = path.name
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


# ─────────────────────────────────────────────
#  Core API
# ─────────────────────────────────────────────

def zip_project(
    source_dir:   str | Path,
    output_path:  Optional[str | Path] = None,
    ignore:       Optional[set[str]]   = None,
    compression:  int = zipfile.ZIP_DEFLATED,
) -> Path:
    """
    Create a ZIP archive of *source_dir*.

    Args:
        source_dir:  Directory to archive (must exist).
        output_path: Destination .zip path. Auto-generated if None
                     (placed next to source_dir with a timestamp suffix).
        ignore:      Set of glob patterns to exclude.
                     Defaults to DEFAULT_IGNORE.
        compression: zipfile compression type (default DEFLATED).

    Returns:
        Path to the created .zip file.

    Raises:
        FileNotFoundError: If source_dir does not exist.
        OSError:           On any filesystem error.
    """
    src  = Path(source_dir).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Source directory not found: {src}")

    ignore_set = ignore if ignore is not None else DEFAULT_IGNORE

    if output_path is None:
        ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = src.parent / f"{src.name}_{ts}.zip"

    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out, "w", compression=compression) as zf:
        for file_path in sorted(src.rglob("*")):
            # Skip ignored paths (check each component)
            skip = False
            for part in file_path.relative_to(src).parts:
                if _should_ignore(Path(part), ignore_set):
                    skip = True
                    break
            if skip:
                continue

            if file_path.is_file():
                arcname = file_path.relative_to(src)
                zf.write(file_path, arcname)

    return out


def zip_files(
    files:       dict[str, str],
    output_path: str | Path,
    compression: int = zipfile.ZIP_DEFLATED,
) -> Path:
    """
    Create a ZIP archive directly from an in-memory dict of path → content.

    Useful for zipping generated files without writing them to disk first.

    Args:
        files:       Dict mapping relative archive paths to file content strings.
        output_path: Destination .zip file path.
        compression: zipfile compression type.

    Returns:
        Path to the created .zip file.
    """
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out, "w", compression=compression) as zf:
        for rel_path, content in files.items():
            zf.writestr(rel_path, content.encode("utf-8"))

    return out


def unzip(
    zip_path:   str | Path,
    output_dir: str | Path,
    overwrite:  bool = True,
) -> Path:
    """
    Extract a ZIP archive to *output_dir*.

    Args:
        zip_path:   Path to the .zip file.
        output_dir: Destination directory (created if missing).
        overwrite:  If False, skips files that already exist.

    Returns:
        Resolved output directory Path.

    Raises:
        FileNotFoundError: If zip_path does not exist.
        zipfile.BadZipFile: If the file is not a valid ZIP.
    """
    src = Path(zip_path)
    if not src.exists():
        raise FileNotFoundError(f"ZIP file not found: {src}")

    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(src, "r") as zf:
        for member in zf.infolist():
            dest = out / member.filename
            if not overwrite and dest.exists():
                continue
            zf.extract(member, out)

    return out


def zip_info(zip_path: str | Path) -> dict:
    """
    Return metadata about a ZIP archive.

    Args:
        zip_path: Path to the .zip file.

    Returns:
        Dict with: file_count, total_size_bytes, total_compressed_bytes,
                   compression_ratio, files (list of names).
    """
    src = Path(zip_path)
    if not src.exists():
        raise FileNotFoundError(f"ZIP not found: {src}")

    with zipfile.ZipFile(src, "r") as zf:
        infos = zf.infolist()
        total_size       = sum(i.file_size       for i in infos)
        total_compressed = sum(i.compress_size   for i in infos)
        ratio = (
            round((1 - total_compressed / total_size) * 100, 1)
            if total_size > 0 else 0.0
        )
        return {
            "file_count":             len(infos),
            "total_size_bytes":       total_size,
            "total_compressed_bytes": total_compressed,
            "compression_ratio":      f"{ratio}%",
            "archive_size_bytes":     src.stat().st_size,
            "files":                  [i.filename for i in infos],
        }
