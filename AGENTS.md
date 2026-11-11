# AGENTS.md

Instructions for AI coding agents working in this repository.

## Local overrides

**Before doing anything else, read `AGENTS.local.md` in the repository root if it exists.**
It holds environment-specific instructions (OS, shell, tool paths, personal preferences)
and is intentionally not committed (it is listed in `.gitignore`).
If `AGENTS.local.md` conflicts with this file, `AGENTS.local.md` wins for that machine only.
Never copy the contents of `AGENTS.local.md` into tracked files.

## Project overview

`img2base64-md` is a small command-line tool. It takes an image file path, builds a
Markdown image tag with the image embedded as a Base64 data URI, and copies it to the
system clipboard:

```
![file name without extension](data:image/png;base64,iVBORw0KGgo...)
```

It is meant to be launched from an image viewer's "open with external application"
feature (Windows) or from a Finder Quick Action / Shortcuts (macOS).

## Requirements and constraints

- Python 3.8 or later, **standard library only**. Do not add third-party dependencies.
- Platform support:
  - Windows 10/11: officially supported and tested.
  - macOS: included on a best-effort basis (`pbcopy`), but **unverified**: the maintainer has
    no Mac to test on. Do not claim it works; label it "untested" in docs and welcome
    feedback from Mac users.
  - Linux: not supported. No Linux clipboard code; on other platforms the script exits
    with code `4` and a clear "unsupported platform" message.
- Startup speed matters. Do not import heavy modules (`tkinter`, `PIL`, ...). Import
  OS-specific modules (`winsound`, `ctypes`) only on the matching OS.
- Never use `shell=True`. Pass `subprocess` arguments as a list.
- The tool only reads the input file. No network access, no writing to the input file.
- Do not use `mimetypes` for MIME detection. Use the fixed extension map so results do
  not depend on the OS. Unknown extensions fall back to `image/png`.
- Normalize the alt text (file name stem) to NFC and escape `[` and `]`.

## Layout

```
img2base64_md.py            # main script
launchers/img2base64-md.vbs # Windows launcher for GUI programs (no console window)
launchers/img2base64-md.cmd # Windows launcher for terminals (flashes a console from GUIs)
launchers/img2base64-md.sh  # macOS launcher (untested)
tests/test_img2base64_md.py # unit tests (clipboard and notifications are mocked)
README.md                   # usage and per-OS setup
```

Keep OS-independent logic (MIME lookup, Markdown building, alt-text escaping) in pure
functions so it can be unit tested without a clipboard. Keep OS-specific code (clipboard,
notifications) in separate functions.

Exit codes: `0` success, `2` missing/invalid argument, `3` file not found or unreadable,
`4` clipboard failure or unsupported platform.

Windows clipboard note: `clip.exe` must receive UTF-16 LE **without a BOM**. A BOM ends up
on the clipboard as a literal U+FEFF character.

## Commands

```
python -m unittest discover -s tests -v    # run tests
python img2base64_md.py <image-path>       # run manually
```

Use `python3` instead of `python` on macOS.

## Conventions

- All tracked files (code, comments, docs, commit messages, issue/PR text) are written
  in **English**. Japanese is allowed only in untracked files such as `AGENTS.local.md`
  and `work/`, and as test data in `tests/` (Japanese file names, NFC/NFD checks).
- Follow PEP 8. Keep functions small and type-annotated. Add comments only where intent is not
  obvious. Do not use syntax newer than Python 3.8 (no `match`, no `X | Y` type unions).
- Line endings are controlled by `.gitattributes`: `.cmd`/`.bat` use CRLF, `.sh` uses LF.
  Do not change them by hand.
- The `.sh` launcher must keep its executable bit:
  `git update-index --chmod=+x launchers/img2base64-md.sh`.
- Keep changes minimal and scoped to the request. Do not add features that were not asked for.

## Untracked directories

`work/` is git-ignored and holds drafts and design notes. Do not reference files in
`work/` from tracked files, and do not commit anything from it.
