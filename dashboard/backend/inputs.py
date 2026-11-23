"""Scan inputs from a file upload or a pasted snippet, written under targets/uploads/<uuid4>/.

Framework-free: the HTTP layer maps InputRejected to a status code. Nothing here runs a scan.
"""

from __future__ import annotations

import re
import shutil
import stat
import tempfile
import uuid
import zipfile
import zlib
from pathlib import Path
from typing import BinaryIO

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_UNZIP_BYTES = 100 * 1024 * 1024
MAX_ZIP_MEMBERS = 5000
MAX_SNIPPET_BYTES = 200 * 1024
CHUNK = 1024 * 1024
MAX_NAME_CHARS = 120

SNIPPET_EXTENSIONS = {
    "python": "py", "javascript": "js", "typescript": "ts", "java": "java", "go": "go",
    "ruby": "rb", "php": "php", "sql": "sql", "yaml": "yaml", "json": "json", "env": "env",
    "other": "txt",
}

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_DRIVE = re.compile(r"^[A-Za-z]:")


class InputRejected(Exception):
    """A client-side problem with the input; `status` is the HTTP status to return."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def new_input_dir(targets_dir: Path) -> Path:
    dest = Path(targets_dir) / "uploads" / uuid.uuid4().hex
    dest.mkdir(parents=True)
    return dest


def write_snippet(code: str, language: str, targets_dir: Path) -> Path:
    """Write a pasted snippet to snippet.<ext> in a fresh input directory and return that directory."""
    if not code.strip():
        raise InputRejected(422, "code must not be empty")
    if len(code.encode("utf-8")) > MAX_SNIPPET_BYTES:
        raise InputRejected(413, f"code exceeds the {MAX_SNIPPET_BYTES // 1024} KB limit")
    ext = SNIPPET_EXTENSIONS.get(language.strip().lower())
    if ext is None:
        raise InputRejected(422, f"unknown language {language!r}; expected one of: "
                                 f"{', '.join(SNIPPET_EXTENSIONS)}")
    dest = new_input_dir(targets_dir)
    (dest / f"snippet.{ext}").write_bytes(code.encode("utf-8"))
    return dest


def store_upload(filename: str | None, source: BinaryIO, targets_dir: Path) -> Path:
    """Store one uploaded file, or extract a .zip, into a fresh input directory and return it."""
    name = safe_basename(filename)
    with tempfile.SpooledTemporaryFile(max_size=CHUNK) as spool:
        copy_capped(source, spool, MAX_UPLOAD_BYTES, f"upload exceeds the "
                    f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit")
        if spool.tell() == 0:
            raise InputRejected(400, "upload is empty")
        spool.seek(0)
        dest = new_input_dir(targets_dir)
        try:
            if name.lower().endswith(".zip"):
                extract_zip(spool, dest)
            else:
                with open(dest / name, "wb") as out:
                    shutil.copyfileobj(spool, out)
        except BaseException:
            shutil.rmtree(dest, ignore_errors=True)
            raise
    return dest


def safe_basename(filename: str | None) -> str:
    """Reduce a client-supplied name to a plain basename made of [A-Za-z0-9._-]."""
    base = (filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    name = _UNSAFE_CHARS.sub("_", base)[:MAX_NAME_CHARS]
    if not name.strip("."):
        return "upload"
    return name


def copy_capped(source: BinaryIO, out: BinaryIO, cap: int, message: str) -> None:
    total = 0
    while chunk := source.read(CHUNK):
        total += len(chunk)
        if total > cap:
            raise InputRejected(413, message)
        out.write(chunk)


def extract_zip(fileobj: BinaryIO, dest: Path) -> None:
    """Extract a zip into dest. Every member is validated before anything is written."""
    root = dest.resolve()
    try:
        archive = zipfile.ZipFile(fileobj)
    except zipfile.BadZipFile:
        raise InputRejected(400, "upload is not a valid zip archive")
    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_ZIP_MEMBERS:
            raise InputRejected(413, f"zip has {len(infos)} members; the limit is {MAX_ZIP_MEMBERS}")
        if sum(info.file_size for info in infos) > MAX_UNZIP_BYTES:
            raise InputRejected(413, f"zip uncompresses to more than "
                                     f"{MAX_UNZIP_BYTES // (1024 * 1024)} MB")
        plan = [(info, member_path(info, root)) for info in infos]
        written = 0
        try:
            for info, target in plan:
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as src, open(target, "wb") as out:
                    while chunk := src.read(CHUNK):
                        written += len(chunk)
                        if written > MAX_UNZIP_BYTES:
                            raise InputRejected(413, f"zip uncompresses to more than "
                                                     f"{MAX_UNZIP_BYTES // (1024 * 1024)} MB")
                        out.write(chunk)
        except (zipfile.BadZipFile, RuntimeError, NotImplementedError, zlib.error):
            raise InputRejected(400, "zip member could not be read (corrupt or encrypted)")


def member_path(info: zipfile.ZipInfo, root: Path) -> Path:
    """Resolve a zip member inside root, or reject it (absolute, traversal, symlink, device)."""
    name = info.filename
    if stat.S_ISLNK(info.external_attr >> 16):
        raise InputRejected(400, f"zip member {name!r} is a symlink; symlinks are not allowed")
    if "\x00" in name or name.startswith(("/", "\\")) or _DRIVE.match(name):
        raise InputRejected(400, f"zip member {name!r} has an absolute path")
    if any(part == ".." for part in re.split(r"[\\/]+", name)):
        raise InputRejected(400, f"zip member {name!r} escapes the upload directory")
    target = (root / name).resolve()
    if not target.is_relative_to(root) or target == root:
        raise InputRejected(400, f"zip member {name!r} escapes the upload directory")
    return target
