#!/bin/sh
# Launcher for img2base64_md.py (macOS). UNTESTED: the maintainer has no Mac.
#
# Example: use it from a Finder Quick Action (Automator) with a "Run Shell Script"
# action set to "Pass input: as arguments", then call this file with "$@".
exec python3 "$(dirname "$0")/../img2base64_md.py" "$@"
