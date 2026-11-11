"""Unit tests for img2base64_md (OS-independent parts)."""
import base64
import sys
import tempfile
import unittest
import unicodedata
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import img2base64_md as app  # noqa: E402

PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360f8cfc0f01f0005000201a5f645400000000049454e44ae426082"
)


class GuessMimeTest(unittest.TestCase):
    def test_known_extensions(self):
        cases = {
            "a.png": "image/png",
            "a.jpg": "image/jpeg",
            "a.jpeg": "image/jpeg",
            "a.gif": "image/gif",
            "a.webp": "image/webp",
            "a.bmp": "image/bmp",
            "a.svg": "image/svg+xml",
            "a.ico": "image/x-icon",
            "a.avif": "image/avif",
            "a.heic": "image/heic",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(app.guess_mime(Path(name)), expected)

    def test_case_insensitive(self):
        self.assertEqual(app.guess_mime(Path("PHOTO.JPG")), "image/jpeg")
        self.assertEqual(app.guess_mime(Path("x.PnG")), "image/png")

    def test_unknown_extension_falls_back_to_png(self):
        self.assertEqual(app.guess_mime(Path("a.xyz")), "image/png")
        self.assertEqual(app.guess_mime(Path("noext")), "image/png")


class EscapeAltTest(unittest.TestCase):
    def test_brackets_escaped(self):
        self.assertEqual(app.escape_alt("a[1]"), "a\\[1\\]")

    def test_parentheses_untouched(self):
        self.assertEqual(app.escape_alt("a(1)"), "a(1)")


class BuildMarkdownTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def _write(self, name, data=PNG_BYTES):
        path = self.dir / name
        path.write_bytes(data)
        return path

    def test_round_trip(self):
        path = self._write("sample.png")
        text = app.build_markdown(path)
        prefix = "![sample](data:image/png;base64,"
        self.assertTrue(text.startswith(prefix))
        self.assertTrue(text.endswith(")"))
        self.assertEqual(base64.b64decode(text[len(prefix):-1]), PNG_BYTES)

    def test_single_line_no_trailing_newline(self):
        path = self._write("big.png", b"\x00" * 10000)
        text = app.build_markdown(path)
        self.assertNotIn("\n", text)
        self.assertNotIn("\r", text)

    def test_japanese_space_and_brackets_in_name(self):
        path = self._write("画像 テスト[1].jpg")
        text = app.build_markdown(path)
        self.assertTrue(text.startswith("![画像 テスト\\[1\\]](data:image/jpeg;base64,"))

    def test_alt_is_nfc(self):
        nfd_name = unicodedata.normalize("NFD", "ガイド") + ".png"
        path = self._write(nfd_name)
        text = app.build_markdown(path)
        self.assertTrue(text.startswith("![ガイド]("))
        self.assertIn(unicodedata.normalize("NFC", "ガイド"), text[:10])


class MainTest(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(app, "notify")
        self.notify = patcher.start()
        self.addCleanup(patcher.stop)
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def _png(self, name="a.png", data=PNG_BYTES):
        path = self.dir / name
        path.write_bytes(data)
        return str(path)

    def test_no_args_returns_2(self):
        self.assertEqual(app.main([]), app.EXIT_BAD_ARGS)

    def test_missing_file_returns_3(self):
        self.assertEqual(app.main([str(self.dir / "nope.png")]), app.EXIT_FILE)

    def test_directory_returns_3(self):
        self.assertEqual(app.main([str(self.dir)]), app.EXIT_FILE)

    def test_success_copies_markdown(self):
        path = self._png()
        with mock.patch.object(app, "copy_to_clipboard") as copy:
            self.assertEqual(app.main([path]), app.EXIT_OK)
        copy.assert_called_once()
        self.assertTrue(copy.call_args[0][0].startswith("![a](data:image/png;base64,"))
        self.assertEqual(self.notify.call_args[0][0], "ok")

    def test_extra_arguments_ignored(self):
        path = self._png()
        with mock.patch.object(app, "copy_to_clipboard") as copy:
            self.assertEqual(app.main([path, "other.png"]), app.EXIT_OK)
        copy.assert_called_once()

    def test_clipboard_failure_returns_4(self):
        path = self._png()
        with mock.patch.object(app, "copy_to_clipboard", side_effect=app.ClipboardError("x")):
            self.assertEqual(app.main([path]), app.EXIT_CLIPBOARD)
        self.assertEqual(self.notify.call_args[0][0], "error")

    def test_large_file_warns_but_copies(self):
        path = self._png("big.png", b"\x00" * (2 * 1024 * 1024))
        with mock.patch.object(app, "copy_to_clipboard") as copy:
            self.assertEqual(app.main(["--max-mb", "1", path]), app.EXIT_OK)
        copy.assert_called_once()
        self.assertEqual(self.notify.call_args[0][0], "warn")

    def test_heic_warns_but_copies(self):
        path = self._png("photo.heic")
        with mock.patch.object(app, "copy_to_clipboard") as copy:
            self.assertEqual(app.main([path]), app.EXIT_OK)
        copy.assert_called_once()
        self.assertEqual(self.notify.call_args[0][0], "warn")

    def test_quiet_is_passed_to_notify(self):
        path = self._png()
        with mock.patch.object(app, "copy_to_clipboard"):
            app.main(["-q", path])
        self.assertTrue(self.notify.call_args[0][2])


class CopyToClipboardTest(unittest.TestCase):
    def test_unsupported_platform_raises(self):
        with mock.patch.object(sys, "platform", "linux"):
            with self.assertRaises(app.ClipboardError) as ctx:
                app.copy_to_clipboard("x")
        self.assertIn("unsupported platform", str(ctx.exception))

    def test_unsupported_platform_main_returns_4(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.png"
            path.write_bytes(PNG_BYTES)
            with mock.patch.object(sys, "platform", "linux"), mock.patch.object(app, "notify"):
                self.assertEqual(app.main([str(path)]), app.EXIT_CLIPBOARD)

    def test_macos_uses_pbcopy_with_utf8(self):
        completed = mock.Mock(returncode=0)
        with mock.patch.object(sys, "platform", "darwin"), mock.patch.object(
            app.subprocess, "run", return_value=completed
        ) as run:
            app.copy_to_clipboard("日本語")
        self.assertEqual(run.call_args[0][0], ["pbcopy"])
        self.assertEqual(run.call_args[1]["input"], "日本語".encode("utf-8"))
        self.assertEqual(run.call_args[1]["env"]["LC_ALL"], "en_US.UTF-8")

    def test_command_failure_raises(self):
        completed = mock.Mock(returncode=1)
        with mock.patch.object(sys, "platform", "darwin"), mock.patch.object(
            app.subprocess, "run", return_value=completed
        ):
            with self.assertRaises(app.ClipboardError):
                app.copy_to_clipboard("x")


if __name__ == "__main__":
    unittest.main()
