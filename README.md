# img2base64-md

Copy an image to the clipboard as a Markdown image tag with the image embedded as a Base64 data URI:

```
![file name without extension](data:image/png;base64,iVBORw0KGgo...)
```

Paste it into a Markdown editor that supports data URIs (for example Typora) to embed the image without a separate file.

## Platform support

| Platform | Status |
|---|---|
| Windows 10/11 | Supported and tested |
| macOS | Included on a best-effort basis (`pbcopy`), **untested**: the maintainer has no Mac. Feedback is welcome. |
| Linux | Not supported (exits with code `4`) |

## Requirements

- Python 3.8 or later. No third-party packages.

## Usage

```
python img2base64_md.py [-q] [--max-mb N] <image-path>
```

| Option | Description |
|---|---|
| `-q`, `--quiet` | No sounds or dialogs. Messages are still written to stderr. |
| `--max-mb N` | Warn when the file is larger than `N` MB (default: 5). The text is still copied. |

Only the first path is used. Extra arguments are ignored.

On success the tool plays a short sound. Errors are shown in a dialog on Windows. Warnings (large files, formats such as HEIC that many editors cannot display) are reported after the text has been copied.

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 2 | Missing or invalid argument |
| 3 | File not found or unreadable |
| 4 | Clipboard failure or unsupported platform |

### MIME types

The MIME type is chosen from the file extension (case-insensitive) using a fixed table: `png`, `jpg`/`jpeg`, `gif`, `webp`, `bmp`, `svg`, `ico`, `avif`, `heic`. Any other extension falls back to `image/png`. The content of the file is not inspected.

The alt text is the file name without its extension, normalized to NFC, with `[` and `]` escaped.

## Windows: launching from an image viewer

Two launchers are provided. Both forward the image path to the script and pass on its exit code.

| Launcher | Console window | Use it for |
|---|---|---|
| [`launchers/img2base64-md.vbs`](launchers/img2base64-md.vbs) | None | Image viewers and other GUI programs (recommended) |
| [`launchers/img2base64-md.cmd`](launchers/img2base64-md.cmd) | A black window flashes briefly when started from a GUI program | Terminals, or tools that need a plain batch file |

The `.cmd` file flashes a window because `cmd.exe` itself opens a console before the batch file runs, even though the script is then started with `pythonw`.

Register the `.vbs` file as an external program in your image viewer:

- Program: `wscript.exe`
- Arguments: `"<full path to launchers\img2base64-md.vbs>" "<current image path>"`

The placeholder that stands for the current file differs for each viewer. Check your viewer's documentation.

Verified by the maintainer with IrfanView: the `.vbs` launcher works without any console window. The `.cmd` launcher also works but flashes a black window briefly.

## macOS (untested)

[`launchers/img2base64-md.sh`](launchers/img2base64-md.sh) calls `python3` on the script. Make sure it is executable (`chmod +x`). One possible setup is a Finder Quick Action (Automator) with a "Run Shell Script" action that passes its input as arguments. None of this has been tested on a Mac.

## Development

```
python -m unittest discover -s tests -v
```

The tests cover the OS-independent logic and use mocks for the clipboard and notifications. Clipboard behavior itself is checked manually on Windows.
