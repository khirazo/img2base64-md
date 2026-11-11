#!/usr/bin/env python3
"""Copy an image to the clipboard as a Markdown image tag with a Base64 data URI.

Usage:
    python img2base64_md.py [--quiet] [--max-mb N] <image-path>

The clipboard receives:
    ![file name without extension](data:image/png;base64,....)

Platform support:
    Windows 10/11  supported and tested.
    macOS          best effort (pbcopy), UNTESTED.
    other          not supported (exit code 4).

Setting it up from an image viewer (Windows): register launchers/img2base64-md.cmd
as an external application and pass the viewer's "current file path" token as the
only argument. The token differs per viewer (check its documentation), and the
path should be passed in double quotes.

Exit codes:
    0  success
    2  missing or invalid argument
    3  file not found or unreadable
    4  clipboard failure or unsupported platform

Standard library only. Python 3.8 or later.
"""
from __future__ import annotations

import argparse
import base64
import os
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import List, Optional

EXIT_OK = 0
EXIT_BAD_ARGS = 2
EXIT_FILE = 3
EXIT_CLIPBOARD = 4

DEFAULT_MAX_MB = 5.0
DEFAULT_MIME = "image/png"

# Fixed map on purpose: the stdlib "mimetypes" module depends on OS settings.
MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".avif": "image/avif",
    ".heic": "image/heic",
}

# Formats that most Markdown editors cannot render. Copied anyway, with a warning.
POORLY_SUPPORTED = {".heic"}


class ClipboardError(Exception):
    """Raised when the text cannot be placed on the clipboard."""


# --------------------------------------------------------------------------
# Pure functions (no OS dependency)
# --------------------------------------------------------------------------


def guess_mime(path: Path) -> str:
    """Return the MIME type for the file extension, defaulting to image/png."""
    return MIME_TYPES.get(path.suffix.lower(), DEFAULT_MIME)


def escape_alt(text: str) -> str:
    """Escape square brackets so the alt text cannot break the Markdown syntax."""
    return text.replace("[", "\\[").replace("]", "\\]")


def build_markdown(path: Path) -> str:
    """Read the image and return ``![alt](data:mime;base64,...)`` on one line."""
    data = path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    alt = escape_alt(unicodedata.normalize("NFC", path.stem))
    return "![{}](data:{};base64,{})".format(alt, guess_mime(path), encoded)


# --------------------------------------------------------------------------
# OS-specific code
# --------------------------------------------------------------------------


def _copy_windows(text: str) -> None:
    # clip.exe detects UTF-16 LE from the content. Do not prepend a BOM: it would be
    # copied to the clipboard as a literal U+FEFF character.
    payload = text.encode("utf-16-le")
    try:
        result = subprocess.run(
            ["clip.exe"],
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except OSError as exc:
        raise ClipboardError("could not run clip.exe: {}".format(exc))
    if result.returncode != 0:
        raise ClipboardError("clip.exe exited with code {}".format(result.returncode))


def _copy_macos(text: str) -> None:
    # UNTESTED: no Mac was available to the maintainer.
    env = dict(os.environ, LC_ALL="en_US.UTF-8")
    try:
        result = subprocess.run(
            ["pbcopy"],
            input=text.encode("utf-8"),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise ClipboardError("could not run pbcopy: {}".format(exc))
    if result.returncode != 0:
        raise ClipboardError("pbcopy exited with code {}".format(result.returncode))


def copy_to_clipboard(text: str) -> None:
    """Place ``text`` on the system clipboard. Raise ClipboardError on failure."""
    if sys.platform == "win32":
        _copy_windows(text)
    elif sys.platform == "darwin":
        _copy_macos(text)
    else:
        raise ClipboardError("unsupported platform: {}".format(sys.platform))


def _eprint(message: str) -> None:
    # sys.stderr is None when started with pythonw.exe.
    stream = sys.stderr
    if stream is None:
        return
    try:
        stream.write(message + "\n")
        stream.flush()
    except (OSError, ValueError):
        pass


def notify(kind: str, message: str, quiet: bool = False) -> None:
    """Report a result. ``kind`` is "ok", "warn" or "error". Best effort only.

    The message always goes to stderr. Sounds and dialogs are skipped when ``quiet``.
    """
    _eprint(message)
    if quiet:
        return
    try:
        if sys.platform == "win32":
            import winsound

            if kind == "error":
                import ctypes

                ctypes.windll.user32.MessageBoxW(0, message, "img2base64-md", 0x10)
            elif kind == "warn":
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            else:
                winsound.MessageBeep(winsound.MB_OK)
        elif sys.platform == "darwin":
            # UNTESTED
            if kind == "error":
                script = 'display alert "img2base64-md" message {}'.format(
                    '"' + message.replace("\\", "\\\\").replace('"', '\\"') + '"'
                )
                subprocess.Popen(["osascript", "-e", script])
            else:
                sound = "Basso" if kind == "warn" else "Pop"
                subprocess.Popen(["afplay", "/System/Library/Sounds/{}.aiff".format(sound)])
    except Exception:  # notification must never change the exit code
        pass


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="img2base64_md",
        description="Copy an image to the clipboard as a Markdown Base64 image tag.",
    )
    parser.add_argument("path", nargs="?", help="path to the image file")
    parser.add_argument("-q", "--quiet", action="store_true", help="no sounds or dialogs")
    parser.add_argument(
        "--max-mb",
        type=float,
        default=DEFAULT_MAX_MB,
        help="warn when the file is larger than this many MB (default: %(default)s)",
    )
    # Extra positional arguments are ignored on purpose.
    args, _unknown = parser.parse_known_args(argv)
    return args


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = parse_args(argv)
    except SystemExit as exc:  # argparse exits with 2 on invalid options, 0 on --help
        return exc.code if isinstance(exc.code, int) else EXIT_BAD_ARGS

    quiet = args.quiet
    if not args.path:
        notify("error", "No image path given. Usage: img2base64_md.py <image-path>", quiet)
        return EXIT_BAD_ARGS

    path = Path(args.path)
    try:
        if not path.is_file():
            notify("error", "File not found: {}".format(path), quiet)
            return EXIT_FILE
        size = path.stat().st_size
        markdown = build_markdown(path)
    except OSError as exc:
        notify("error", "Cannot read {}: {}".format(path, exc), quiet)
        return EXIT_FILE

    try:
        copy_to_clipboard(markdown)
    except ClipboardError as exc:
        notify("error", "Clipboard error: {}".format(exc), quiet)
        return EXIT_CLIPBOARD

    suffix = path.suffix.lower()
    warnings = []
    if size > args.max_mb * 1024 * 1024:
        warnings.append(
            "{:.1f} MB exceeds {:g} MB; the Base64 text is about 1.33x larger.".format(
                size / (1024 * 1024), args.max_mb
            )
        )
    if suffix in POORLY_SUPPORTED:
        warnings.append("{} images are not displayed by many Markdown editors.".format(suffix))

    if warnings:
        notify("warn", "Copied, but: " + " ".join(warnings), quiet)
    else:
        notify("ok", "Copied {} ({} characters).".format(path.name, len(markdown)), quiet)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
