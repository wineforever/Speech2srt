import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from speech2srt.config import load_settings


class ConfigTests(unittest.TestCase):
    def test_precedence_and_relative_output_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir, "custom.ini")
            config_path.write_text(
                "[paths]\noutput_dir = ini-output\n"
                "[asr]\nasr_engine = bcut\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"ASR_ENGINE": "jianying"}, clear=False):
                settings = load_settings(
                    str(config_path),
                    overrides={"output_dir": "cli-output"},
                )

            self.assertEqual(settings.asr_engine, "jianying")
            self.assertEqual(
                settings.output_dir,
                os.path.normpath(os.path.join(temp_dir, "cli-output")),
            )

    def test_missing_config_uses_safe_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = load_settings(os.path.join(temp_dir, "missing.ini"))

        self.assertEqual(settings.asr_engine, "bcut")
        self.assertIn("wav", settings.supported_formats)
        self.assertGreater(settings.subtitle_max_chars, 0)


if __name__ == "__main__":
    unittest.main()
